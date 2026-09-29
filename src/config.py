"""
Configuration settings, data paths, cost standards, and SLA parameters
for Vireo Audio Customer Support Operations Analysis.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
STATIC_DIR = BASE_DIR / "static"

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# File resolution helper: checks data/ first, then fallback to root with uuid prefix
def find_data_file(filename: str, fallback_patterns: list[str]) -> Path:
    std_path = DATA_DIR / filename
    if std_path.exists():
        return std_path
    
    # Check in BASE_DIR directly
    base_path = BASE_DIR / filename
    if base_path.exists():
        return base_path
        
    # Search by glob
    for pattern in fallback_patterns:
        matches = list(BASE_DIR.glob(pattern))
        if matches:
            return matches[0]
            
    raise FileNotFoundError(f"Could not locate data file for {filename}")

TICKETS_FILE = find_data_file("tickets.csv", ["*tickets.csv"])
AGENTS_FILE = find_data_file("agents.csv", ["*agents.csv"])
ORDERS_FILE = find_data_file("orders.csv", ["*orders.csv"])
CUSTOMERS_FILE = find_data_file("customers.csv", ["*customers.csv"])
PRODUCTS_FILE = find_data_file("products.csv", ["*products.csv"])

# Support Policy SLAs (First Response Time in hours)
# Section 3: chat 15m (0.25h), voice callback 2h, social 4h, email 8h
SLA_TARGET_HOURS = {
    "chat": 0.25,
    "voice": 2.0,
    "social": 4.0,
    "email": 8.0
}

# Policy Cost Standards (FY26 Planning Figures, Section 4 & 5)
SLA_BREACH_PENALTY_INR = 350.0       # Rs 350 store credit per breach
INTERNAL_TRANSFER_COST_INR = 305.0   # Rs 305 per transfer
AGENT_HOURLY_COST_INR = 165.0        # Rs 165 per agent-hour
AGENT_SHIFT_HOURS = 8.0              # 8 hours per shift
ANNUAL_COST_PER_2_HIRES_INR = 900000.0  # Rs 9 Lakh/year for 2 hires (Arjun Mehta)
QUARTERLY_COST_PER_2_HIRES_INR = 225000.0  # Rs 2.25 Lakh per quarter

# Channels fully loaded contact cost (INR)
CHANNEL_CONTACT_COST = {
    "chat": 210.0,
    "email": 260.0,
    "voice": 520.0,
    "social": 240.0,
    "blended": 290.0
}

# Official Support Categories (11 total)
CATEGORIES = [
    "Billing & Payments",
    "Delivery & Shipping",
    "Returns & Refunds",
    "Warranty & Repair",
    "Connectivity",
    "Charging & Battery",
    "App & Firmware",
    "Audio Quality",
    "Product Enquiry",
    "Account & Login",
    "Other"
]

# Reporting Window
REPORTING_START = "2025-01-01"
REPORTING_END = "2026-06-30 23:59:59"
