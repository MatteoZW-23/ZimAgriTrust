# Platform Configuration & Business Rules
# --------------------------------------------------
import os

# Transaction & Escrow Fees
DEFAULT_PLATFORM_FEE_RATE = 0.01   # 1.0% Standard
PREMIUM_FEE_RATE          = 0.005  # 0.5% for High Trust Farmers

# On-platform transport incentive — reduced goods fee when buyer uses a registered driver
ON_PLATFORM_TRANSPORT_FEE_RATE = 0.008  # 0.8% (saves 0.2% vs standard)

# Transport insurance (optional, buyer-elected)
TRANSPORT_INSURANCE_FEE_USD = 1.50   # Flat fee per transaction
TRANSPORT_INSURANCE_COVERAGE_RATE = 0.80  # Platform covers 80% of goods value on claim

# Risk & Governance Thresholds
RISK_THRESHOLD_SUSPEND  = 85.0
RISK_THRESHOLD_MODERATE = 60.0
TRUST_THRESHOLD_PREMIUM = 90.0

# Penalty Weightings (Policy Engine)
DISPUTE_PENALTY_WEIGHT          = 20.0
FAILED_DELIVERY_PENALTY_WEIGHT  = 30.0
SUCCESSFUL_TX_CREDIT_WEIGHT     = 5.0

# Market Standards (GMB/Zim-specific)
MAX_MAIZE_MOISTURE_CONTENT = 12.5   # GMB Moisture Grade A Standard
COLLATERAL_LENDING_LTV     = 0.70   # 70% Loan-to-Value for WHR Financing

# Currency Standards
ZIG_USD_BENCHMARK_RATE = float(os.environ.get("ZIG_USD_RATE", "0"))  # Set via environment variable
