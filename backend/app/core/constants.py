# Platform Configuration & Business Rules
# --------------------------------------------------

# Transaction & Escrow Fees
DEFAULT_PLATFORM_FEE_RATE = 0.015  # 1.5% Standard
PREMIUM_FEE_RATE = 0.01           # 1.0% for Verified High Trust Farmers

# Risk & Governance Thresholds
RISK_THRESHOLD_SUSPEND = 85.0
RISK_THRESHOLD_MODERATE = 60.0
TRUST_THRESHOLD_PREMIUM = 90.0

# Penalty Weightings (Policy Engine)
DISPUTE_PENALTY_WEIGHT = 20.0
FAILED_DELIVERY_PENALTY_WEIGHT = 30.0
SUCCESSFUL_TX_CREDIT_WEIGHT = 5.0

# Market Standards (GMB/Zim-specific)
MAX_MAIZE_MOISTURE_CONTENT = 12.5  # GMB Moisture Grade A Standard
COLLATERAL_LENDING_LTV = 0.70      # 70% Loan-to-Value for WHR Financing

# Currency Standards
ZIG_USD_BENCHMARK_RATE = 28.5      # Official simulated rate for demo
