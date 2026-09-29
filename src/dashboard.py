"""
FastAPI Dashboard Backend for Vireo Audio Support Desk.
Provides REST APIs for:
- Executive Overview Metrics
- Monthly Volume by Category and Team (Assigned vs Resolved)
- Team Workload and Throughput
- Misrouting & Financial Friction Analysis
- Live AI Ticket Classification Sandbox
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.config import STATIC_DIR, REPORTS_DIR
from src.pipeline import (
    load_raw_data, clean_and_normalize_tickets, get_reporting_dataset,
    calculate_monthly_breakdown, calculate_team_workload_metrics,
    calculate_financial_friction
)
from src.classifier import classify_ticket, ClassificationResult

app = FastAPI(
    title="Vireo Audio Support Intelligence",
    description="Operational analytics and AI auto-categorization engine",
    version="2.0.0"
)

# Global cached data structures
_cached_data = {}


def get_cached_pipeline_data():
    if "df" not in _cached_data:
        tickets, agents, orders, customers, products = load_raw_data()
        df = clean_and_normalize_tickets(tickets, agents)
        rep_df = get_reporting_dataset(df)
        workload = calculate_team_workload_metrics(rep_df, agents)
        friction = calculate_financial_friction(rep_df)
        monthly = calculate_monthly_breakdown(rep_df)
        
        _cached_data["df"] = df
        _cached_data["rep_df"] = rep_df
        _cached_data["agents"] = agents
        _cached_data["workload"] = workload
        _cached_data["friction"] = friction
        _cached_data["monthly"] = monthly

    return _cached_data


class ClassifyRequest(BaseModel):
    message: str
    initial_category: Optional[str] = "Other"
    ticket_id: Optional[str] = "SANDBOX-001"


# API Endpoints
@app.get("/api/overview")
def get_overview_metrics():
    data = get_cached_pipeline_data()
    friction = data["friction"]
    workload = data["workload"]

    billing_assigned = int(friction["billing_assigned_count"])
    billing_resolved = int(friction["billing_resolved_count"])
    logistics_assigned = int(friction["logistics_assigned_count"])
    logistics_resolved = int(friction["logistics_resolved_count"])

    return {
        "total_tickets": int(friction["total_tickets"]),
        "billing_assigned": billing_assigned,
        "billing_resolved": billing_resolved,
        "billing_drop_pct": round((billing_resolved - billing_assigned) / billing_assigned * 100, 1),
        "logistics_assigned": logistics_assigned,
        "logistics_resolved": logistics_resolved,
        "logistics_surge_pct": round((logistics_resolved - logistics_assigned) / logistics_assigned * 100, 1),
        "billing_to_logistics_leak": int(friction["billing_to_logistics_count"]),
        "total_misrouted": int(friction["total_misrouted_count"]),
        "misrouted_pct": friction["misrouted_percentage"],
        "quarterly_friction_inr": friction["total_quarterly_friction_inr"],
        "quarterly_transfer_waste_inr": friction["quarterly_transfer_waste_inr"],
        "quarterly_sla_waste_inr": friction["quarterly_sla_waste_inr"]
    }


@app.get("/api/monthly-data")
def get_monthly_breakdown_data():
    data = get_cached_pipeline_data()
    monthly = data["monthly"]

    cat_df = monthly["category_assigned"]
    team_ass_df = monthly["team_assigned"]
    team_res_df = monthly["team_resolved"]

    months = cat_df.index.tolist()

    return {
        "months": months,
        "categories": {cat: cat_df[cat].tolist() for cat in cat_df.columns},
        "teams_assigned": {team: team_ass_df[team].tolist() for team in team_ass_df.columns},
        "teams_resolved": {team: team_res_df[team].tolist() for team in team_res_df.columns}
    }


@app.get("/api/team-workload")
def get_team_workload():
    data = get_cached_pipeline_data()
    workload = data["workload"]
    teams_list = []
    for team, row in workload.iterrows():
        teams_list.append({
            "team": team,
            "headcount": int(row["Headcount"]),
            "assigned_intake": int(row["Assigned_Intake"]),
            "assigned_share_pct": float(row["Assigned_Share_%"]),
            "resolved_count": int(row["Resolved_Count"]),
            "resolved_share_pct": float(row["Resolved_Share_%"]),
            "net_diff": int(row["Net_Volume_Diff"]),
            "tickets_per_agent": float(row["Tickets_Per_Agent"]),
            "median_resolution_hours": float(row["Median_Resolution_Hours"]),
            "mean_resolution_hours": float(row["Mean_Resolution_Hours"]),
            "sla_breaches": int(row["SLA_Breaches"]),
            "sla_breach_rate_pct": float(row["SLA_Breach_Rate_%"])
        })
    return {"teams": teams_list}


@app.get("/api/evaluation")
def get_evaluation_metrics():
    eval_file = REPORTS_DIR / "evaluation_results.json"
    if eval_file.exists():
        with open(eval_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "status": "pending",
        "message": "Run python -m src.evaluate to generate fresh evaluation benchmark."
    }


@app.get("/api/sites-and-channels")
def get_sites_and_channels():
    data = get_cached_pipeline_data()
    rep_df = data["rep_df"]
    
    site_counts = rep_df['site'].value_counts().to_dict()
    channel_counts = rep_df['channel'].value_counts().to_dict()
    
    return {
        "sites": site_counts,
        "channels": channel_counts
    }


@app.get("/api/memo")
def get_executive_memo():
    from src.config import BASE_DIR
    memo_path = BASE_DIR / "memo_priya_raman.md"
    if memo_path.exists():
        with open(memo_path, "r", encoding="utf-8") as f:
            return {"memo": f.read()}
    return {"memo": "Executive memo not found."}


@app.post("/api/classify")
def classify_endpoint(req: ClassifyRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Customer message cannot be empty")
    
    result = classify_ticket(
        message=req.message,
        initial_category=req.initial_category,
        ticket_id=req.ticket_id
    )
    return result.model_dump()


# Mount static directory for HTML/JS/CSS assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend assets not yet compiled.")
    return FileResponse(index_file)
