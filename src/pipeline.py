"""
Data Processing and Operational Metrics Pipeline for Vireo Audio Support Desk.
Handles data loading, timezone normalization, joins, SLA calculations,
misrouting detection, and financial friction modeling.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from src.config import (
    TICKETS_FILE, AGENTS_FILE, ORDERS_FILE, CUSTOMERS_FILE, PRODUCTS_FILE,
    SLA_TARGET_HOURS, SLA_BREACH_PENALTY_INR, INTERNAL_TRANSFER_COST_INR,
    REPORTING_START, REPORTING_END
)


def load_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all 5 raw CSV datasets."""
    tickets = pd.read_csv(TICKETS_FILE)
    agents = pd.read_csv(AGENTS_FILE)
    orders = pd.read_csv(ORDERS_FILE)
    customers = pd.read_csv(CUSTOMERS_FILE)
    products = pd.read_csv(PRODUCTS_FILE)
    return tickets, agents, orders, customers, products


def clean_and_normalize_tickets(tickets: pd.DataFrame, agents: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw tickets:
    1. Parse datetime timestamps.
    2. Fix UTC vs IST timezone bug in legacy_fd resolved_at (+5.5 hours offset).
    3. Accurately join agents on agent_id (avoiding duplicate display names).
    4. Calculate first-response time, resolution time, and SLA breaches.
    5. Identify misrouted tickets and transfer costs.
    """
    df = tickets.copy()

    # Parse timestamps
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['first_response_at'] = pd.to_datetime(df['first_response_at'])
    df['resolved_at'] = pd.to_datetime(df['resolved_at'])

    # Timezone correction for legacy_fd resolved_at
    # Event logs were exported in UTC while created_at was in IST (UTC+5:30)
    is_legacy = df['source_system'] == 'legacy_fd'
    df['resolved_at_raw'] = df['resolved_at']
    df.loc[is_legacy & df['resolved_at'].notna(), 'resolved_at'] = (
        df.loc[is_legacy & df['resolved_at'].notna(), 'resolved_at'] + pd.Timedelta(hours=5.5)
    )

    # Join resolving agent information on agent_id
    agent_cols = ['agent_id', 'team', 'name', 'site', 'shift', 'tier']
    clean_agents = agents[agent_cols].drop_duplicates(subset=['agent_id'])
    df = df.merge(clean_agents, on='agent_id', how='left', suffixes=('', '_agent'))
    df.rename(columns={'team': 'resolving_team', 'name': 'agent_name'}, inplace=True)

    # Duration calculations (hours)
    df['frt_hours'] = (df['first_response_at'] - df['created_at']).dt.total_seconds() / 3600.0
    df['resolution_hours'] = (df['resolved_at'] - df['created_at']).dt.total_seconds() / 3600.0

    # Channel-specific SLA breach logic (Section 3 of Support Operating Policy)
    def is_breached(row):
        ch = str(row['channel']).lower().strip()
        frt = row['frt_hours']
        if pd.isna(frt):
            return False
        target = SLA_TARGET_HOURS.get(ch, 8.0)
        return frt > target

    df['sla_target_hours'] = df['channel'].str.lower().map(SLA_TARGET_HOURS)
    df['sla_breached'] = df.apply(is_breached, axis=1)
    df['sla_breach_penalty_inr'] = np.where(df['sla_breached'], SLA_BREACH_PENALTY_INR, 0.0)

    # Misrouting and Transfer Analysis
    # A ticket is misrouted if the team it was first assigned to != team that resolved it
    df['is_misrouted'] = (df['assigned_team'] != df['resolving_team']) & df['resolving_team'].notna()
    df['is_billing_to_logistics'] = (df['assigned_team'] == 'Billing') & (df['resolving_team'] == 'Logistics')

    # Transfer cost calculation (Helpdesk recorded transfers; legacy left blank)
    df['recorded_transfers'] = df['transfers']  # Keep NaN for legacy to avoid bias
    df['transfer_cost_inr'] = df['recorded_transfers'] * INTERNAL_TRANSFER_COST_INR

    # Add Calendar Helpers
    df['year_month'] = df['created_at'].dt.to_period('M').astype(str)
    df['quarter'] = df['created_at'].dt.to_period('Q').astype(str)

    return df


def get_reporting_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Filter tickets strictly within the 18-month reporting window (Jan 2025 - Jun 2026)."""
    mask = (df['created_at'] >= REPORTING_START) & (df['created_at'] <= REPORTING_END)
    return df[mask].copy()


def calculate_team_workload_metrics(df: pd.DataFrame, agents: pd.DataFrame) -> pd.DataFrame:
    """
    Computes comparative workload: Intake Assigned Volume vs Actual Resolved Volume
    and per-agent throughput.
    """
    agent_counts = agents.groupby('team')['agent_id'].nunique()
    
    assigned = df['assigned_team'].value_counts()
    resolved = df['resolving_team'].value_counts()
    sla_breaches = df.groupby('resolving_team')['sla_breached'].sum()
    median_res_time = df.groupby('resolving_team')['resolution_hours'].median()
    mean_res_time = df.groupby('resolving_team')['resolution_hours'].mean()

    summary = pd.DataFrame({
        'Headcount': agent_counts,
        'Assigned_Intake': assigned,
        'Assigned_Share_%': (assigned / len(df) * 100).round(2),
        'Resolved_Count': resolved,
        'Resolved_Share_%': (resolved / len(df) * 100).round(2),
        'Net_Volume_Diff': resolved - assigned,
        'Tickets_Per_Agent': (resolved / agent_counts).round(1),
        'Median_Resolution_Hours': median_res_time.round(2),
        'Mean_Resolution_Hours': mean_res_time.round(2),
        'SLA_Breaches': sla_breaches,
        'SLA_Breach_Rate_%': ((sla_breaches / resolved) * 100).round(2)
    })

    return summary.sort_values(by='Resolved_Count', ascending=False)


def calculate_monthly_breakdown(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Generates monthly volume tables by Category and by Team (both assigned & resolved)."""
    monthly_cat_assigned = pd.crosstab(df['year_month'], df['category'])
    monthly_team_assigned = pd.crosstab(df['year_month'], df['assigned_team'])
    monthly_team_resolved = pd.crosstab(df['year_month'], df['resolving_team'])

    return {
        'category_assigned': monthly_cat_assigned,
        'team_assigned': monthly_team_assigned,
        'team_resolved': monthly_team_resolved
    }


def calculate_financial_friction(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Quantifies the exact financial waste of misrouting, transfers, and SLA penalties.
    """
    # Filter helpdesk for reliable transfer counts
    hd = df[df['source_system'] == 'helpdesk']
    
    billing_to_log = df[df['is_billing_to_logistics']]
    all_misrouted = df[df['is_misrouted']]

    # Helpdesk direct transfers cost
    hd_transfers_total = hd['transfers'].sum()
    hd_transfer_cost_total = hd_transfers_total * INTERNAL_TRANSFER_COST_INR

    # Billing transfers in helpdesk
    hd_billing_transfers = hd[hd['assigned_team'] == 'Billing']['transfers'].sum()
    hd_billing_transfer_cost = hd_billing_transfers * INTERNAL_TRANSFER_COST_INR

    # SLA breach penalty
    total_sla_penalties = df['sla_breach_penalty_inr'].sum()
    misrouted_sla_penalties = all_misrouted['sla_breach_penalty_inr'].sum()

    # Quarterly averages in reporting period (6 quarters)
    quarters_count = df['quarter'].nunique()
    quarterly_misrouted_count = len(all_misrouted) / quarters_count
    quarterly_billing_to_log_count = len(billing_to_log) / quarters_count

    # Quarterly financial impact of misrouting
    # Rs 305 per transfer + Rs 350 for SLA breach
    quarterly_transfer_waste = (len(all_misrouted) * INTERNAL_TRANSFER_COST_INR) / quarters_count
    quarterly_sla_waste = misrouted_sla_penalties / quarters_count
    total_quarterly_friction = quarterly_transfer_waste + quarterly_sla_waste

    return {
        'total_tickets': len(df),
        'billing_assigned_count': (df['assigned_team'] == 'Billing').sum(),
        'billing_resolved_count': (df['resolving_team'] == 'Billing').sum(),
        'logistics_assigned_count': (df['assigned_team'] == 'Logistics').sum(),
        'logistics_resolved_count': (df['resolving_team'] == 'Logistics').sum(),
        'billing_to_logistics_count': len(billing_to_log),
        'total_misrouted_count': len(all_misrouted),
        'misrouted_percentage': round(len(all_misrouted) / len(df) * 100, 2),
        'helpdesk_transfers_count': int(hd_transfers_total),
        'helpdesk_transfer_cost_inr': round(hd_transfer_cost_total, 2),
        'total_sla_penalties_inr': round(total_sla_penalties, 2),
        'misrouted_sla_penalties_inr': round(misrouted_sla_penalties, 2),
        'quarterly_misrouted_count': round(quarterly_misrouted_count, 1),
        'quarterly_billing_to_log_count': round(quarterly_billing_to_log_count, 1),
        'quarterly_transfer_waste_inr': round(quarterly_transfer_waste, 2),
        'quarterly_sla_waste_inr': round(quarterly_sla_waste, 2),
        'total_quarterly_friction_inr': round(total_quarterly_friction, 2)
    }
