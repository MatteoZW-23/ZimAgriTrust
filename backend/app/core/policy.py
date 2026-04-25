"""
AgriTrust Platform Policy Engine
Unified fee calculation covering:
  - Standard / premium / rural goods fee
  - On-platform transport incentive (reduced goods fee)
  - Optional transport insurance
  - Financial inclusion waiver for small trades
"""
from decimal import Decimal
from app.core.constants import (
    DEFAULT_PLATFORM_FEE_RATE,
    PREMIUM_FEE_RATE,
    ON_PLATFORM_TRANSPORT_FEE_RATE,
    TRANSPORT_INSURANCE_FEE_USD,
    TRUST_THRESHOLD_PREMIUM,
)

# National Currency Framework
ZIG_USD_RATE = 13.56  # 1 USD = 13.56 ZIG

# Financial Inclusion Thresholds
SMALLHOLDER_WAIVER_THRESHOLD = 15.0   # Zero fees for transactions under $15
RURAL_DISCOUNT_RATE          = 0.0075  # Half-price for remote rural districts


def convert_to_usd(amount: float, currency: str) -> float:
    if str(currency).upper() == "ZIG":
        return round(float(Decimal(str(amount)) / Decimal(str(ZIG_USD_RATE))), 2)
    return amount


def calculate_platform_fees(
    amount: float,
    user_trust_score: float = 0,
    is_rural: bool = False,
    currency: str = "USD",
    using_platform_transport: bool = False,
) -> float:
    """
    Inclusion-Aware Platform Commission Policy.

    Fee tiers (goods only, not transport):
      - ≤ $15:                    0%   (smallholder waiver)
      - Rural + any trust:        0.75%
      - Trust ≥ 90 (premium):     0.5%
      - On-platform transport:    0.8% (incentive discount)
      - Standard:                 1.0%
    """
    usd_val = convert_to_usd(amount, currency)

    # Financial inclusion waiver
    if usd_val <= SMALLHOLDER_WAIVER_THRESHOLD:
        return 0.0

    if is_rural:
        rate = RURAL_DISCOUNT_RATE
    elif user_trust_score >= TRUST_THRESHOLD_PREMIUM:
        rate = PREMIUM_FEE_RATE
    elif using_platform_transport:
        rate = ON_PLATFORM_TRANSPORT_FEE_RATE  # Incentive: 0.8% vs 1.0%
    else:
        rate = DEFAULT_PLATFORM_FEE_RATE

    return round(float(Decimal(str(amount)) * Decimal(str(rate))), 2)


def calculate_transport_insurance_fee(
    goods_value: float,
    currency: str = "USD",
    elected: bool = False,
) -> float:
    """
    Optional transport insurance fee.
    Flat $1.50 per transaction, regardless of goods value.
    Returns 0.0 if buyer did not elect insurance.
    """
    if not elected:
        return 0.0
    usd_val = convert_to_usd(goods_value, currency)
    if usd_val <= SMALLHOLDER_WAIVER_THRESHOLD:
        return 0.0
    return TRANSPORT_INSURANCE_FEE_USD


def calculate_seller_settlement(
    amount: float,
    user_trust_score: float = 0,
    is_rural: bool = False,
    currency: str = "USD",
    using_platform_transport: bool = False,
) -> tuple[float, float]:
    """Returns (platform_fee, seller_payout)."""
    fee = calculate_platform_fees(amount, user_trust_score, is_rural, currency, using_platform_transport)
    return fee, round(amount - fee, 2)


def calculate_full_order_breakdown(
    goods_amount: float,
    user_trust_score: float = 0,
    is_rural: bool = False,
    currency: str = "USD",
    using_platform_transport: bool = False,
    transport_fee: float = 0.0,
    transport_insurance_elected: bool = False,
) -> dict:
    """
    Full order cost breakdown for the payments preview endpoint.
    Returns every line item the buyer sees before confirming.
    """
    platform_fee = calculate_platform_fees(
        goods_amount, user_trust_score, is_rural, currency, using_platform_transport
    )
    insurance_fee = calculate_transport_insurance_fee(
        goods_amount, currency, transport_insurance_elected
    )
    seller_payout = round(goods_amount - platform_fee, 2)
    buyer_total   = round(goods_amount + transport_fee + insurance_fee, 2)

    savings = 0.0
    if using_platform_transport:
        standard_fee = calculate_platform_fees(goods_amount, user_trust_score, is_rural, currency, False)
        savings = round(standard_fee - platform_fee, 2)

    return {
        "goods_amount":              goods_amount,
        "platform_fee":              platform_fee,
        "platform_fee_rate":         f"{(platform_fee / goods_amount * 100):.1f}%" if goods_amount else "0%",
        "transport_fee":             transport_fee,
        "transport_insurance_fee":   insurance_fee,
        "insurance_elected":         transport_insurance_elected,
        "buyer_total":               buyer_total,
        "seller_payout":             seller_payout,
        "on_platform_transport_savings": savings,
        "currency":                  currency,
    }
