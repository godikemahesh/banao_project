"""
Executive Chart Generation Module.
Generates publication-quality charts for Priya Raman, Arjun Mehta, and the One-Page Memo:
1. Monthly volume by Category (18-month trend).
2. Monthly volume by Team: Intake Assigned vs Actually Resolved (The Billing Illusion).
3. The Billing-to-Logistics Leakage & Transfer Cost Trend.
4. Resolution Times & SLA Breach Rates across Teams.
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import numpy as np
from src.config import REPORTS_DIR
from src.pipeline import (
    load_raw_data, clean_and_normalize_tickets, get_reporting_dataset,
    calculate_monthly_breakdown, calculate_team_workload_metrics
)

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']


def generate_all_charts():
    tickets, agents, orders, customers, products = load_raw_data()
    df = clean_and_normalize_tickets(tickets, agents)
    rep_df = get_reporting_dataset(df)

    # 1. Monthly Breakdown by Category
    monthly_cat = pd.crosstab(rep_df['year_month'], rep_df['category'])
    fig, ax = plt.subplots(figsize=(14, 7))
    monthly_cat.plot(kind='line', ax=ax, marker='o', linewidth=2.2, markersize=5)
    ax.set_title("Vireo Audio: Monthly Ticket Volume by Category (Jan 2025 – Jun 2026)", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Month", fontsize=11, fontweight='bold')
    ax.set_ylabel("Ticket Volume", fontsize=11, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title="Category", bbox_to_anchor=(1.02, 1), loc='upper left', frameon=True)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "monthly_breakdown_by_category.png", dpi=200)
    plt.close()

    # 2. Monthly Assigned vs Resolved (The Billing Illusion vs Logistics Reality)
    monthly_assigned = pd.crosstab(rep_df['year_month'], rep_df['assigned_team'])
    monthly_resolved = pd.crosstab(rep_df['year_month'], rep_df['resolving_team'])

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)

    # Left: Billing
    months = monthly_assigned.index.tolist()
    x = np.arange(len(months))
    w = 0.38

    axes[0].bar(x - w/2, monthly_assigned['Billing'], width=w, label='Assigned Intake (Priya\'s View)', color='#93c5fd')
    axes[0].bar(x + w/2, monthly_resolved['Billing'], width=w, label='Actually Resolved (Workload)', color='#1d4ed8')
    axes[0].set_title("Billing Queue: Intake Illusion vs Actual Workload (-28%)", fontsize=12, fontweight='bold', pad=10)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(months, rotation=45, fontsize=9)
    axes[0].set_ylabel("Monthly Tickets", fontsize=11, fontweight='bold')
    axes[0].legend(frameon=True)

    # Right: Logistics
    axes[1].bar(x - w/2, monthly_assigned['Logistics'], width=w, label='Assigned Intake', color='#fca5a5')
    axes[1].bar(x + w/2, monthly_resolved['Logistics'], width=w, label='Actually Resolved (+40% Surge)', color='#b91c1c')
    axes[1].set_title("Logistics Queue: True Operational Choke Point (+40%)", fontsize=12, fontweight='bold', pad=10)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(months, rotation=45, fontsize=9)
    axes[1].legend(frameon=True)

    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "monthly_breakdown_by_team_assigned_vs_resolved.png", dpi=200)
    plt.close()

    # 3. Resolution Time & SLA Breaches
    team_metrics = calculate_team_workload_metrics(rep_df, agents)
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    teams = team_metrics.index.tolist()
    y_pos = np.arange(len(teams))

    # Median Resolution Time
    axes[0].barh(y_pos, team_metrics['Median_Resolution_Hours'], color='#6366f1')
    axes[0].set_yticks(y_pos)
    axes[0].set_yticklabels(teams, fontweight='bold')
    axes[0].set_xlabel("Median Resolution Time (Hours)", fontsize=11, fontweight='bold')
    axes[0].set_title("Median Resolution Time by Team (Logistics > 25 hrs)", fontsize=12, fontweight='bold', pad=10)
    for i, v in enumerate(team_metrics['Median_Resolution_Hours']):
        axes[0].text(v + 1.0, i, f"{v:.1f}h", va='center', fontweight='bold', fontsize=9)

    # SLA Breach Rate (%)
    axes[1].barh(y_pos, team_metrics['SLA_Breach_Rate_%'], color='#ef4444')
    axes[1].set_yticks(y_pos)
    axes[1].set_yticklabels(teams, fontweight='bold')
    axes[1].set_xlabel("SLA Breach Rate (%)", fontsize=11, fontweight='bold')
    axes[1].set_title("SLA Breach Rate by Team (Logistics Highest at 16.4%)", fontsize=12, fontweight='bold', pad=10)
    for i, v in enumerate(team_metrics['SLA_Breach_Rate_%']):
        axes[1].text(v + 0.5, i, f"{v:.1f}%", va='center', fontweight='bold', fontsize=9)

    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "resolution_time_and_sla_breaches.png", dpi=200)
    plt.close()

    # 4. Quarterly Financial Friction of Misrouted Tickets
    rep_df['quarter'] = rep_df['created_at'].dt.to_period('Q').astype(str)
    misrouted = rep_df[rep_df['is_misrouted']]
    q_transfer_cost = misrouted.groupby('quarter').size() * 305.0
    q_sla_cost = misrouted.groupby('quarter')['sla_breached'].sum() * 350.0

    quarters = q_transfer_cost.index.tolist()
    xq = np.arange(len(quarters))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(xq, q_transfer_cost, label='Avoidable Transfer Overhead (Rs 305/xfer)', color='#f59e0b', width=0.55)
    ax.bar(xq, q_sla_cost, bottom=q_transfer_cost, label='SLA Breach Penalty Credits (Rs 350/breach)', color='#dc2626', width=0.55)
    ax.set_title("Quarterly Financial Friction from Misrouted Tickets (INR)", fontsize=13, fontweight='bold', pad=12)
    ax.set_xticks(xq)
    ax.set_xticklabels(quarters, fontweight='bold')
    ax.set_ylabel("Cost in INR (Rs)", fontsize=11, fontweight='bold')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"Rs {int(y):,}"))
    ax.legend(frameon=True)

    for i in range(len(quarters)):
        tot = q_transfer_cost.iloc[i] + q_sla_cost.iloc[i]
        ax.text(i, tot + 2500, f"Rs {int(tot):,}", ha='center', fontweight='bold', fontsize=9)

    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "quarterly_friction_costs.png", dpi=200)
    plt.close()

    print("All executive charts successfully generated in reports/ directory.")


if __name__ == '__main__':
    generate_all_charts()
