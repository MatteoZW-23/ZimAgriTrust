from decimal import Decimal
from app.core.constants import (
    DEFAULT_PLATFORM_FEE_RATE, 
    PREMIUM_FEE_RATE, 
    TRUST_THRESHOLD_PREMIUM
)

# National Currency Framework (Binary Economy)
# ZIG (Zimbabwe Gold) backed by gold reserves
ZIG_USD_RATE = 13.56  # 1 USD = 13.56 ZIG (Live Market Simulation)

# Financial Inclusion Thresholds (Rural Support)
SMALLHOLDER_WAIVER_THRESHOLD = 15.0  # Zero fees for transactions under $15
RURAL_DISCOUNT_RATE = 0.0075         # Half-price platform fee for remote rural districts

def convert_to_usd(amount: float, currency: str) -> float:
    """Converts local settlement (ZiG) back to USD base for global metrics."""
    if str(currency).upper() == "ZIG":
        return round(float(Decimal(str(amount)) / Decimal(str(ZIG_USD_RATE))), 2)
    return amount

def calculate_platform_fees(amount: float, user_trust_score: float = 0, is_rural: bool = False, currency: str = "USD") -> float:
    """
    Inclusion-Aware Platform Commission Policy
    Logic optimized for smallholder farmer support and dual-currency settlements.
    """
    # Normalize to USD for fee assessment (ensures thresholds work for ZiG)
    usd_val = convert_to_usd(amount, currency)
    
    # 1. Financial Inclusion: Zero fees for small survival-level trades
    if usd_val <= SMALLHOLDER_WAIVER_THRESHOLD:
        return 0.0
    
    # 2. Rural Logistics Offset: 50% discount for remote locations
    base_rate = DEFAULT_PLATFORM_FEE_RATE
    if user_trust_score >= TRUST_THRESHOLD_PREMIUM:
        base_rate = PREMIUM_FEE_RATE
    
    final_rate = RURAL_DISCOUNT_RATE if is_rural else base_rate
    
    return round(float(Decimal(str(amount)) * Decimal(str(final_rate))), 2)

def calculate_seller_settlement(amount: float, user_trust_score: float = 0, is_rural: bool = False, currency: str = "USD") -> tuple[float, float]:
    """
    Returns (platform_fee, seller_payout) in original currency
    """
    fee = calculate_platform_fees(amount, user_trust_score, is_rural, currency)
    return fee, round(amount - fee, 2)
