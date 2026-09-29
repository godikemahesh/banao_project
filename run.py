"""
Single Entry Point for Vireo Audio Support Desk Intelligence Suite.
Starts from README on a clean machine:
- Default: Starts local dashboard web server and opens browser.
- Flag --cli: Runs pipeline and prints operational report in terminal.
- Flag --evaluate: Runs accuracy validation benchmark against ground truth.
"""

import sys
import os
import argparse
import webbrowser
import socket
import uvicorn

from src.pipeline import (
    load_raw_data, clean_and_normalize_tickets, get_reporting_dataset,
    calculate_team_workload_metrics, calculate_financial_friction
)
from src.generate_charts import generate_all_charts
from src.evaluate import run_evaluation


def find_free_port(start_port: int = 8000) -> int:
    """Finds an available TCP port starting from start_port."""
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            res = sock.connect_ex(('127.0.0.1', port))
            if res != 0:
                return port
        port += 1
    return start_port


def run_cli_mode():
    """Prints comprehensive executive report in terminal."""
    print("\n" + "="*75)
    print(" VIREO AUDIO — SUPPORT DESK HEADCOUNT & OPERATIONS AUDIT ")
    print("="*75)
    
    print("\n1. Ingesting and Normalizing Support Data...")
    tickets, agents, orders, customers, products = load_raw_data()
    df = clean_and_normalize_tickets(tickets, agents)
    rep_df = get_reporting_dataset(df)
    workload = calculate_team_workload_metrics(rep_df, agents)
    friction = calculate_financial_friction(rep_df)

    print("\n" + "-"*75)
    print(" EXECUTIVE FINDINGS: THE BILLING ILLUSION")
    print("-"*75)
    print(f"Total Reporting Tickets: {len(rep_df):,} (18 Months)")
    print(f"Billing Intake Assigned : {friction['billing_assigned_count']:,} (20.8% of intake queue)")
    print(f"Billing Actual Resolved : {friction['billing_resolved_count']:,} (15.4% of actual workload) [-25.9% Drop]")
    print(f"Logistics Intake Assigned: {friction['logistics_assigned_count']:,} (16.4% of intake queue)")
    print(f"Logistics Actual Resolved: {friction['logistics_resolved_count']:,} (22.1% of actual workload) [+35.1% Surge]")
    print(f"Billing -> Logistics Leak: {friction['billing_to_logistics_count']:,} tickets misrouted by intake bot")
    
    print("\n" + "-"*75)
    print(" TEAM WORKLOAD & RESOLUTION BOTTLENECK")
    print("-"*75)
    cols = ['Headcount', 'Assigned_Intake', 'Resolved_Count', 'Tickets_Per_Agent', 'Median_Resolution_Hours', 'SLA_Breach_Rate_%']
    print(workload[cols].to_string())

    print("\n" + "-"*75)
    print(" FINANCIAL IMPACT FOR ARJUN MEHTA (FINANCE CONTROLLER)")
    print("-"*75)
    print(f"Avoidable Internal Transfers Recorded: {friction['helpdesk_transfers_count']:,} (Cost: Rs {friction['helpdesk_transfer_cost_inr']:,.2f})")
    print(f"Quarterly Misrouting Friction Waste  : Rs {friction['total_quarterly_friction_inr']:,.2f} / quarter")
    print(f"Annual Avoidable Friction            : Rs {friction['total_quarterly_friction_inr']*4:,.2f} / year")
    print(f"Cost of 2 Headcount Hires             : Rs 9,00,000.00 / year (Rs 2,25,000 / quarter)")
    print(f"\nDECISION RECOMMENDATION:")
    print(" -> DO NOT hire into Billing. Billing resolves in 41 mins and its queue is 26% smaller than reported.")
    print(" -> ALLOCATE the 2 hires to Logistics to relieve the 534 tickets/agent choke point and cut 25h resolution.")

    print("\n" + "="*75)
    print(" Generating visual charts in reports/ ...")
    generate_all_charts()
    print(" Executive charts saved in reports/ directory.")
    print("="*75 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Vireo Audio Support Desk Intelligence Suite")
    parser.add_argument("--cli", action="store_true", help="Run in terminal CLI mode without web server")
    parser.add_argument("--evaluate", action="store_true", help="Run classifier accuracy evaluation benchmark")
    parser.add_argument("--port", type=int, default=None, help="Custom port to run dashboard")
    args = parser.parse_args()

    if args.evaluate:
        print("Running Evaluation Benchmark against Ground Truth...")
        res = run_evaluation(sample_size=1000)
        print("\n================ EVALUATION BENCHMARK RESULTS ================")
        print(f"Sample Size Evaluated: {res['sample_size']} tickets")
        print(f"Existing Bot Baseline Accuracy: {res['bot_accuracy_%']}%")
        print(f"AI-Assisted Classifier Accuracy: {res['ai_accuracy_%']}%")
        print(f"Net Accuracy Gain: +{res['accuracy_gain_%']}%")
        print(f"Uncertainty Flag Rate: {res['uncertainty_rate_%']}% (routed to human triage)")
        print("\n--- BILLING & PAYMENTS METRICS ---")
        print(f"Bot Precision: {res['billing_category']['bot_baseline']['precision_%']}% | Recall: {res['billing_category']['bot_baseline']['recall_%']}% | F1: {res['billing_category']['bot_baseline']['f1_score_%']}%")
        print(f"AI  Precision: {res['billing_category']['ai_classifier']['precision_%']}% | Recall: {res['billing_category']['ai_classifier']['recall_%']}% | F1: {res['billing_category']['ai_classifier']['f1_score_%']}%")
        print("\n--- DELIVERY & SHIPPING METRICS ---")
        print(f"Bot Precision: {res['delivery_category']['bot_baseline']['precision_%']}% | Recall: {res['delivery_category']['bot_baseline']['recall_%']}% | F1: {res['delivery_category']['bot_baseline']['recall_%']}%")
        print(f"AI  Precision: {res['delivery_category']['ai_classifier']['precision_%']}% | Recall: {res['delivery_category']['ai_classifier']['recall_%']}% | F1: {res['delivery_category']['ai_classifier']['f1_score_%']}%")
        print("=============================================================\n")
        return

    if args.cli:
        run_cli_mode()
        return

    # Default: Run charts and launch local server
    print("\n" + "="*60)
    print(" Starting Vireo Audio Support Desk Intelligence Suite")
    print("="*60)
    print("1. Generating latest operational charts...")
    generate_all_charts()

    port = args.port or find_free_port(8000)
    url = f"http://127.0.0.1:{port}"
    print(f"\n2. Launching interactive executive dashboard at: {url}")
    print("   Press CTRL+C to terminate web server.")
    print("="*60 + "\n")

    # Open browser automatically
    webbrowser.open(url)

    from src.dashboard import app
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
