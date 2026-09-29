# Vireo Audio — Customer Support Desk Intelligence & Headcount Optimization Suite

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)

An operational analytics pipeline, AI-assisted ticket auto-categorization engine, and executive dashboard developed for **Vireo Audio (Task 1 V2 Technical Assessment)**.

---

## 🚀 Quick Start (Clean Machine in 60 Seconds)

### 1. Prerequisites
- Python 3.10+ installed.

### 2. Clone & Install Dependencies
```bash
git clone <your-repo-url>
cd banao_project
pip install -r requirements.txt
```

### 3. Launch the Suite (Single Command)
```bash
python run.py
```
> **What this does:**
> 1. Ingests all 11,641 support tickets and roster data.
> 2. Automatically cleans and normalizes the UTC/IST timezone offset on 2,379 legacy tickets.
> 3. Generates executive charts in the `reports/` folder.
> 4. Launches the interactive dashboard at **`http://127.0.0.1:8000`** and opens your default browser.

---

## 🖥️ Alternative Run Modes

### Terminal CLI Report (No Web Server)
```bash
python run.py --cli
```
*Prints the full operational audit, team workload comparison, and financial friction metrics directly to the console.*

### Run Verification & Accuracy Benchmark
```bash
python run.py --evaluate
```
*Evaluates the AI classifier against 1,000 ground-truth tickets, generating Precision, Recall, F1 scores, and confusion metrics.*

---

## 📊 The Core Business Finding: The "Billing Illusion"

```
+---------------------------------------------------------------------------------------+
|                                 THE "BILLING ILLUSION"                                |
|                                                                                       |
|   Priya's Assumption (Intake Volume):                                                 |
|   - Billing: 2,425 tickets (20.8%)   ==> "Add 2 hires to Billing"                     |
|   - Logistics: 1,905 tickets (16.4%)                                                  |
|                                                                                       |
|   Operational Reality (Resolved Tickets):                                             |
|   - Billing Resolved: 1,798 tickets (15.4%)  [-25.9% Drop!]                           |
|   - Logistics Resolved: 2,574 tickets (22.1%) [+35.1% Surge!]                        |
|                                                                                       |
|   The Cause:                                                                          |
|   - 696+ tickets assigned to Billing were actually LOGISTICS issues misclassified      |
|     by the keyword chatbot ("paid 5 days ago, where is my order?").                   |
|   - Billing agents spent time reading and bouncing them to Logistics.                 |
+---------------------------------------------------------------------------------------+
```

### The Strategic Recommendation:
1. **Allocate the 2 hires to Logistics (NOT Billing):** Logistics has 5 agents resolving 515 tickets/agent with a median resolution time of **25.1 hours** (vs 41 minutes for Billing) and the highest SLA breach rate in the company (16.4%).
2. **Deploy the AI Classifier at Intake:** Eliminates over 1,200 avoidable internal transfers (Rs 305/transfer) and associated SLA penalty credits (Rs 350/breach), saving **Rs 1,22,295 per quarter (~Rs 4.89 Lakh per year)**.

---

## 📁 Repository Structure

```
├── data/                                 # Normalized CSV datasets & support policy
│   ├── tickets.csv                       # 11,780 support tickets (18 months)
│   ├── agents.csv                        # Roster of 44 support agents
│   ├── orders.csv                        # Reference order logs
│   ├── customers.csv                     # Customer profiles & Care+ flags
│   ├── products.csv                      # SKUs, warranty, unit costs
│   ├── email_thread.txt                  # Pre-engagement stakeholder correspondence
│   ├── readme.txt                        # Column documentation
│   └── support_policy.png                # Support Operating Policy v3.2
├── src/                                  # Modular source code
│   ├── config.py                         # SLA parameters, costs, and directory constants
│   ├── pipeline.py                       # Data cleaning, timezone normalization, metrics
│   ├── classifier.py                     # AI ticket classifier (Hybrid: Semantic + LLM)
│   ├── evaluate.py                       # Precision/Recall/F1 benchmark against ground truth
│   ├── dashboard.py                      # FastAPI REST API backend
│   └── generate_charts.py                # Publication-grade chart generation
├── static/                               # Dashboard UI assets
│   ├── index.html                        # Modern executive interface
│   ├── app.js                            # Interactive Chart.js and sandbox logic
│   └── style.css                         # Sleek, card-based CSS styling
├── reports/                              # Output charts and evaluation results
│   ├── monthly_breakdown_by_category.png
│   ├── monthly_breakdown_by_team_assigned_vs_resolved.png
│   ├── resolution_time_and_sla_breaches.png
│   ├── quarterly_friction_costs.png
│   ├── evaluation_accuracy_comparison.png
│   └── evaluation_results.json
├── memo_priya_raman.md                   # Deliverable 4: 1-Page non-technical executive memo
├── video_script.md                       # Deliverable 5: 3-Minute screen recording walkthrough script
├── submission-form.md                    # Deliverable 6: Completed assessment submission form
├── run.py                                # Single execution entry point
├── requirements.txt                      # Lightweight dependencies
└── README.md                             # Repository guide & instructions
```

---

## 🧪 Accuracy Benchmark & Verification (Deliverable 3)

We validated the AI Classifier on a stratified benchmark of 1,000 tickets audited against human agent closing notes, resolving actions, and refund codes:

| Category / Metric | Existing Intake Bot | AI-Assisted Classifier | Operational Change |
| :--- | :---: | :---: | :--- |
| **Overall Desk Accuracy** | 70.8% | **80.0%** | **+9.2% Accuracy Gain** |
| **Billing Precision** | 49.78% | **79.02%** | **+29.24% Precision** (eliminates phantom queue) |
| **Billing F1-Score** | 63.87% | **83.39%** | **+19.52% F1** |
| **Delivery Recall** | 42.41% | **75.23%** | **+32.82% Recall** (catches missed deliveries) |
| **Delivery F1-Score** | 57.20% | **80.60%** | **+23.40% F1** |
| **Uncertainty Flag Rate** | 0.0% | **8.7%** | Routed safely to human triage |

---

## 🛠️ Key Technical Decisions & Data Traps Handled

1. **The Legacy Freshdesk Missing Transfers (3,913 Tickets):**
   Freshdesk did not track transfers. We preserved blanks (`NaN`) rather than imputing zero, preventing artificially deflated historical transfer rates.
2. **The UTC vs. IST Event Log Timezone Anomaly (2,379 Tickets):**
   Freshdesk event logs for `resolved_at` were exported in UTC while helpdesk `created_at` was in IST (UTC+5:30), creating negative durations (down to -5.4 hours). We added automatic `+5.5 hours` normalization to restore valid resolution durations.
3. **Agent Display Name Collisions:**
   Two agents share the same display name. All roster joins strictly rely on `agent_id`.
4. **Offline Clean Machine Compatibility:**
   The classification engine uses a high-performance, deterministic semantic scoring engine by default, requiring **$0 API spend** and zero credentials to run on any clean machine. An optional LLM adapter (OpenAI / Gemini) is toggled automatically if API keys are detected.

---

## 📄 Submission Deliverables Index

- [Executive Memo to Priya Raman](memo_priya_raman.md) (1-page non-technical strategy, ~5 min read)
- [3-Minute Screen Recording Walkthrough Script](video_script.md) (prompts, version diffs, discards)
- [Completed Submission Form](submission-form.md) (full disclosures, trade-offs, financial metrics)
