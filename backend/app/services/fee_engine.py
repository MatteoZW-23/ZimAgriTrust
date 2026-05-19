"""
Enterprise Platform Fee Calculation Engine

Implements percentage fees, fixed fees, capped fees, tiered fees,
subscription discounts, enterprise negotiated fees, tax calculation,
revenue splits, commission sharing for suppliers, affiliates, resellers.
"""
import uuid
import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum

from app.models.user import User

logger = logging.getLogger(__name__)


class FeeType(str, Enum):
    """Types of fees"""
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    CAPPED = "capped"
    TIERED = "tiered"
    SUBSCRIPTION_DISCOUNT = "subscription_discount"
    ENTERPRISE_NEGOTIATED = "enterprise_negotiated"


class CommissionType(str, Enum):
    """Types of commissions"""
    SUPPLIER = "supplier"
    AFFILIATE = "affiliate"
    RESELLER = "reseller"
    MARKETPLACE = "marketplace"
    AGENT_ONBOARDING = "agent_onboarding"
    AGENT_VOLUME = "agent_volume"
    AGENT_REFERRAL = "agent_referral"
    AGENT_VERIFICATION = "agent_verification"
    AGENT_DISPUTE_RESOLUTION = "agent_dispute_resolution"
    AGENT_ORDER_FULFILLMENT = "agent_order_fulfillment"
    AGENT_FIELD_SUPPORT = "agent_field_support"


class AgentTier(str, Enum):
    """Agent performance tiers"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class FeeConfig:
    """Configuration for fee calculation"""
    
    # Default platform fee percentages (your revenue)
    DEFAULT_PLATFORM_FEE_PERCENT = 2.5
    DEFAULT_TRANSACTION_FEE_PERCENT = 1.5
    
    # Provider transaction costs (passed to users, NOT platform revenue)
    ECOCASH_TRANSACTION_COST_PERCENT = 1.5
    ONEMONEY_TRANSACTION_COST_PERCENT = 1.5
    ZIPIT_TRANSACTION_COST_PERCENT = 1.0
    BANK_TRANSFER_COST_PERCENT = 0.5
    WALLET_TRANSACTION_COST_PERCENT = 0.0  # Internal wallet transfers
    
    # Fixed fees
    FIXED_FEE_MIN = 0.50
    FIXED_FEE_MAX = 10.00
    
    # Fee caps
    MAX_FEE_PERCENT = 10.0
    MAX_FEE_AMOUNT = 100.00
    
    # Tiered fee thresholds
    TIER_1_THRESHOLD = 100.0  # Up to $100
    TIER_2_THRESHOLD = 500.0  # $100 - $500
    TIER_3_THRESHOLD = 1000.0  # $500 - $1000
    TIER_4_THRESHOLD = float('inf')  # Above $1000
    
    TIER_1_FEE_PERCENT = 3.0
    TIER_2_FEE_PERCENT = 2.5
    TIER_3_FEE_PERCENT = 2.0
    TIER_4_FEE_PERCENT = 1.5
    
    # Agent commission percentages (platform keeps majority)
    # All commissions capped at 10% of platform fee maximum
    AGENT_ONBOARDING_COMMISSION_PERCENT = 10.0  # % of platform fees from first 10 transactions (capped at 10%)
    AGENT_ONBOARDING_TRANSACTION_LIMIT = 10  # First N transactions count
    
    # Service-specific commissions (unlimited earning potential)
    # All commissions are calculated as % of platform fee, not total transaction amount
    # Maximum commission per service: 10% of platform fee
    AGENT_VERIFICATION_COMMISSION_PERCENT = 5.0  # % of platform fees from verified listings
    AGENT_DISPUTE_RESOLUTION_COMMISSION_PERCENT = 10.0  # % of platform fee from dispute resolution (at max)
    AGENT_ORDER_FULFILLMENT_COMMISSION_PERCENT = 3.0  # % of platform fee from order fulfillment
    AGENT_FIELD_SUPPORT_COMMISSION_PERCENT = 7.0  # % of platform fee from field support
    
    # Territory volume commission
    AGENT_VOLUME_COMMISSION_PERCENT = 0.5  # % of GMV from territory
    
    # Referral program
    AGENT_REFERRAL_BONUS = 50.0  # Fixed bonus for recruiting new agent
    AGENT_REFERRAL_COMMISSION_PERCENT = 5.0  # % of recruited agent's earnings
    
    # Agent performance multipliers
    AGENT_TIER_MULTIPLIERS = {
        AgentTier.BRONZE: 1.0,    # rating 3.0-3.9
        AgentTier.SILVER: 1.25,   # rating 4.0-4.4
        AgentTier.GOLD: 1.5,      # rating 4.5-4.7
        AgentTier.PLATINUM: 2.0,  # rating 4.8-5.0
    }
    
    # Agent task bonuses
    AGENT_SPEED_BONUS_PERCENT = 20.0  # +20% if completed within 24h
    AGENT_QUALITY_BONUS_PERCENT = 30.0  # +30% for zero disputes in territory
    
    # Agent rating criteria (what determines rating)
    RATING_MIN_TASKS_BRONZE = 10  # Minimum tasks to reach Bronze
    RATING_MIN_TASKS_SILVER = 25  # Minimum tasks to reach Silver
    RATING_MIN_TASKS_GOLD = 50  # Minimum tasks to reach Gold
    RATING_MIN_TASKS_PLATINUM = 100  # Minimum tasks to reach Platinum
    
    RATING_SUCCESS_RATE_BRONZE = 0.7  # 70% success rate
    RATING_SUCCESS_RATE_SILVER = 0.8  # 80% success rate
    RATING_SUCCESS_RATE_GOLD = 0.9  # 90% success rate
    RATING_SUCCESS_RATE_PLATINUM = 0.95  # 95% success rate


class FeeEngine:
    """
    Enterprise platform fee calculation engine.
    Supports complex fee structures and revenue splits.
    """

    @staticmethod
    def calculate_percentage_fee(
        amount: float,
        percentage: float,
        cap: Optional[float] = None
    ) -> float:
        """
        Calculate percentage-based fee with optional cap.
        """
        fee = amount * (percentage / 100)
        
        if cap:
            fee = min(fee, cap)
        
        return round(fee, 2)

    @staticmethod
    def calculate_fixed_fee(
        amount: float,
        fixed_fee: float,
        minimum: Optional[float] = None
    ) -> float:
        """
        Calculate fixed fee with minimum guarantee.
        """
        if minimum:
            return max(fixed_fee, minimum)
        return fixed_fee

    @staticmethod
    def calculate_tiered_fee(amount: float) -> float:
        """
        Calculate tiered fee based on amount.
        Higher amounts get lower percentage fees.
        """
        if amount <= FeeConfig.TIER_1_THRESHOLD:
            fee_percent = FeeConfig.TIER_1_FEE_PERCENT
        elif amount <= FeeConfig.TIER_2_THRESHOLD:
            fee_percent = FeeConfig.TIER_2_FEE_PERCENT
        elif amount <= FeeConfig.TIER_3_THRESHOLD:
            fee_percent = FeeConfig.TIER_3_FEE_PERCENT
        else:
            fee_percent = FeeConfig.TIER_4_FEE_PERCENT
        
        return FeeEngine.calculate_percentage_fee(amount, fee_percent)

    @staticmethod
    def calculate_capped_fee(
        amount: float,
        percentage: float,
        cap_amount: float
    ) -> float:
        """
        Calculate fee with percentage but capped at maximum amount.
        """
        fee = amount * (percentage / 100)
        return min(fee, cap_amount)

    @staticmethod
    def calculate_subscription_discount(
        base_fee: float,
        user_plan: str
    ) -> float:
        """
        Apply subscription-based discount to fee.
        """
        if user_plan == "pro":
            discount_percent = 20  # 20% discount
        elif user_plan == "enterprise":
            discount_percent = 40  # 40% discount
        else:
            discount_percent = 0  # No discount for basic
        
        discount = base_fee * (discount_percent / 100)
        return round(base_fee - discount, 2)

    @staticmethod
    def calculate_enterprise_fee(
        amount: float,
        negotiated_rate: float
    ) -> float:
        """
        Calculate fee using enterprise-negotiated rate.
        """
        return FeeEngine.calculate_percentage_fee(amount, negotiated_rate)

    @staticmethod
    def calculate_provider_transaction_cost(
        amount: float,
        provider: str = "ecocash"
    ) -> Dict[str, float]:
        """
        Calculate provider transaction cost (passed to user, NOT platform revenue).
        This is the fee charged by EcoCash, OneMoney, banks, etc.
        """
        provider_costs = {
            "ecocash": FeeConfig.ECOCASH_TRANSACTION_COST_PERCENT,
            "onemoney": FeeConfig.ONEMONEY_TRANSACTION_COST_PERCENT,
            "zipit": FeeConfig.ZIPIT_TRANSACTION_COST_PERCENT,
            "bank_transfer": FeeConfig.BANK_TRANSFER_COST_PERCENT,
            "wallet": FeeConfig.WALLET_TRANSACTION_COST_PERCENT,
        }
        
        cost_percent = provider_costs.get(provider, FeeConfig.ECOCASH_TRANSACTION_COST_PERCENT)
        cost = amount * (cost_percent / 100)
        
        return {
            "provider": provider,
            "cost_percent": cost_percent,
            "cost_amount": round(cost, 2),
        }

    @staticmethod
    def calculate_total_fee(
        amount: float,
        fee_config: Dict[str, Any] = None,
        provider: str = "ecocash"
    ) -> Dict[str, float]:
        """
        Calculate total fee with all applicable components.
        Separates platform revenue from provider transaction costs.
        """
        if fee_config is None:
            fee_config = {}
        
        # Calculate provider transaction cost (passed to user)
        provider_cost = FeeEngine.calculate_provider_transaction_cost(amount, provider)
        
        # Determine fee type for platform revenue
        fee_type = fee_config.get("type", FeeType.PERCENTAGE)
        
        if fee_type == FeeType.PERCENTAGE:
            percentage = fee_config.get("percentage", FeeConfig.DEFAULT_PLATFORM_FEE_PERCENT)
            cap = fee_config.get("cap")
            platform_fee = FeeEngine.calculate_percentage_fee(amount, percentage, cap)
        elif fee_type == FeeType.FIXED:
            fixed_fee = fee_config.get("fixed_fee", FeeConfig.FIXED_FEE_MIN)
            minimum = fee_config.get("minimum")
            platform_fee = FeeEngine.calculate_fixed_fee(amount, fixed_fee, minimum)
        elif fee_type == FeeType.CAPPED:
            percentage = fee_config.get("percentage", FeeConfig.DEFAULT_PLATFORM_FEE_PERCENT)
            cap = fee_config.get("cap", FeeConfig.MAX_FEE_AMOUNT)
            platform_fee = FeeEngine.calculate_capped_fee(amount, percentage, cap)
        elif fee_type == FeeType.TIERED:
            platform_fee = FeeEngine.calculate_tiered_fee(amount)
        elif fee_type == FeeType.SUBSCRIPTION_DISCOUNT:
            user_plan = fee_config.get("user_plan", "basic")
            base_fee = FeeEngine.calculate_percentage_fee(amount, FeeConfig.DEFAULT_PLATFORM_FEE_PERCENT)
            platform_fee = FeeEngine.calculate_subscription_discount(base_fee, user_plan)
        elif fee_type == FeeType.ENTERPRISE_NEGOTIATED:
            negotiated_rate = fee_config.get("negotiated_rate", FeeConfig.DEFAULT_PLATFORM_FEE_PERCENT)
            platform_fee = FeeEngine.calculate_enterprise_fee(amount, negotiated_rate)
        else:
            platform_fee = FeeEngine.calculate_percentage_fee(amount, FeeConfig.DEFAULT_PLATFORM_FEE_PERCENT)
        
        # Apply tax to platform fee only (not provider cost)
        tax_rate = fee_config.get("tax_rate", 0.0)
        tax = platform_fee * (tax_rate / 100)
        platform_fee_with_tax = platform_fee + tax
        
        # Total charge to user = amount + provider cost + platform fee + tax
        total_charge = amount + provider_cost["cost_amount"] + platform_fee_with_tax
        
        return {
            "amount": amount,
            "provider_cost": provider_cost["cost_amount"],
            "provider_cost_percent": provider_cost["cost_percent"],
            "platform_fee": platform_fee,
            "tax": round(tax, 2),
            "platform_fee_with_tax": round(platform_fee_with_tax, 2),
            "total_charge": round(total_charge, 2),
            "platform_revenue": round(platform_fee_with_tax, 2),  # Your actual profit
            "fee_percent": round((platform_fee / amount) * 100, 2) if amount > 0 else 0,
        }

    @staticmethod
    def calculate_commission(
        amount: float,
        commission_type: CommissionType,
        commission_rate: Optional[float] = None,
        agent_tier: Optional[AgentTier] = None
    ) -> Dict[str, float]:
        """
        Calculate commission for different stakeholder types.
        Includes performance multiplier for agents.
        """
        if commission_type in [CommissionType.AGENT_ONBOARDING, CommissionType.AGENT_VOLUME, CommissionType.AGENT_REFERRAL]:
            if commission_rate is None:
                if commission_type == CommissionType.AGENT_ONBOARDING:
                    commission_rate = FeeConfig.AGENT_ONBOARDING_COMMISSION_PERCENT
                elif commission_type == CommissionType.AGENT_VOLUME:
                    commission_rate = FeeConfig.AGENT_VOLUME_COMMISSION_PERCENT
                elif commission_type == CommissionType.AGENT_REFERRAL:
                    commission_rate = FeeConfig.AGENT_REFERRAL_COMMISSION_PERCENT
            
            # Apply performance multiplier for agents
            multiplier = 1.0
            if agent_tier:
                multiplier = FeeConfig.AGENT_TIER_MULTIPLIERS.get(agent_tier, 1.0)
            
            commission = amount * (commission_rate / 100) * multiplier
        else:
            if commission_rate is None:
                if commission_type == CommissionType.SUPPLIER:
                    commission_rate = FeeConfig.SUPPLIER_COMMISSION_PERCENT
                elif commission_type == CommissionType.AFFILIATE:
                    commission_rate = FeeConfig.AFFILIATE_COMMISSION_PERCENT
                elif commission_type == CommissionType.RESELLER:
                    commission_rate = FeeConfig.RESELLER_COMMISSION_PERCENT
            
            commission = amount * (commission_rate / 100)
        
        return {
            "commission_type": commission_type.value,
            "commission_rate": commission_rate if commission_rate else 0.0,
            "commission_amount": round(commission, 2),
            "multiplier": multiplier if agent_tier else 1.0,
        }

    @staticmethod
    def calculate_agent_onboarding_commission(
        platform_fee: float,
        transaction_count: int,
        agent_tier: AgentTier = AgentTier.BRONZE
    ) -> Dict[str, float]:
        """
        Calculate agent commission for onboarding new users.
        Agent gets 10% of platform fees from first 10 transactions.
        Capped at 10% maximum per platform requirement.
        Unlimited earning potential - no caps on total earnings, just per-transaction rate.
        """
        # No commission if no transactions
        if transaction_count == 0:
            return {
                "platform_fee": 0.0,
                "transaction_count": 0,
                "commission_percent": FeeConfig.AGENT_ONBOARDING_COMMISSION_PERCENT,
                "multiplier": 1.0,
                "commission_amount": 0.0,
            }
        
        multiplier = FeeConfig.AGENT_TIER_MULTIPLIERS.get(agent_tier, 1.0)
        commission = platform_fee * (FeeConfig.AGENT_ONBOARDING_COMMISSION_PERCENT / 100) * multiplier
        
        return {
            "platform_fee": platform_fee,
            "transaction_count": transaction_count,
            "commission_percent": FeeConfig.AGENT_ONBOARDING_COMMISSION_PERCENT,
            "multiplier": multiplier,
            "commission_amount": round(commission, 2),
        }

    @staticmethod
    def calculate_agent_verification_commission(
        platform_fees: list[float],
        agent_tier: AgentTier = AgentTier.BRONZE
    ) -> Dict[str, float]:
        """
        Calculate agent commission for listing verification.
        Agent gets 5% of platform fees from verified listings.
        Unlimited earning potential - more verifications = more earnings.
        """
        multiplier = FeeConfig.AGENT_TIER_MULTIPLIERS.get(agent_tier, 1.0)
        total_platform_fees = sum(platform_fees)
        commission = total_platform_fees * (FeeConfig.AGENT_VERIFICATION_COMMISSION_PERCENT / 100) * multiplier
        
        return {
            "total_platform_fees": total_platform_fees,
            "verification_count": len(platform_fees),
            "commission_percent": FeeConfig.AGENT_VERIFICATION_COMMISSION_PERCENT,
            "multiplier": multiplier,
            "commission_amount": round(commission, 2),
        }

    @staticmethod
    def calculate_agent_dispute_commission(
        dispute_amount: float,
        platform_fee_percent: float = 2.5,
        resolved_in_favor: bool = True,
        agent_tier: AgentTier = AgentTier.BRONZE
    ) -> Dict[str, float]:
        """
        Calculate agent commission for dispute resolution.
        Agent gets 10% of platform fee from dispute, not total dispute amount.
        Unlimited earning potential - higher value disputes = more platform fees = more earnings.
        """
        if not resolved_in_favor:
            return {
                "dispute_amount": dispute_amount,
                "platform_fee": 0.0,
                "resolved_in_favor": False,
                "commission_percent": FeeConfig.AGENT_DISPUTE_RESOLUTION_COMMISSION_PERCENT,
                "multiplier": 1.0,
                "commission_amount": 0.0,
            }
        
        # Calculate platform fee first
        platform_fee = dispute_amount * (platform_fee_percent / 100)
        
        # Agent commission is % of platform fee
        multiplier = FeeConfig.AGENT_TIER_MULTIPLIERS.get(agent_tier, 1.0)
        commission = platform_fee * (FeeConfig.AGENT_DISPUTE_RESOLUTION_COMMISSION_PERCENT / 100) * multiplier
        
        return {
            "dispute_amount": dispute_amount,
            "platform_fee": round(platform_fee, 2),
            "resolved_in_favor": True,
            "commission_percent": FeeConfig.AGENT_DISPUTE_RESOLUTION_COMMISSION_PERCENT,
            "multiplier": multiplier,
            "commission_amount": round(commission, 2),
        }

    @staticmethod
    def calculate_agent_fulfillment_commission(
        order_amount: float,
        platform_fee_percent: float = 2.5,
        agent_tier: AgentTier = AgentTier.BRONZE
    ) -> Dict[str, float]:
        """
        Calculate agent commission for order fulfillment.
        Agent gets 3% of platform fee from order, not total order amount.
        Unlimited earning potential - more orders = more platform fees = more earnings.
        """
        # Calculate platform fee first
        platform_fee = order_amount * (platform_fee_percent / 100)
        
        # Agent commission is % of platform fee
        multiplier = FeeConfig.AGENT_TIER_MULTIPLIERS.get(agent_tier, 1.0)
        commission = platform_fee * (FeeConfig.AGENT_ORDER_FULFILLMENT_COMMISSION_PERCENT / 100) * multiplier
        
        return {
            "order_amount": order_amount,
            "platform_fee": round(platform_fee, 2),
            "commission_percent": FeeConfig.AGENT_ORDER_FULFILLMENT_COMMISSION_PERCENT,
            "multiplier": multiplier,
            "commission_amount": round(commission, 2),
        }

    @staticmethod
    def calculate_agent_field_support_commission(
        order_amount: float,
        platform_fee_percent: float = 2.5,
        agent_tier: AgentTier = AgentTier.BRONZE
    ) -> Dict[str, float]:
        """
        Calculate agent commission for field support.
        Agent gets 7% of platform fee from supported order, not total order amount.
        Unlimited earning potential - more support = more platform fees = more earnings.
        """
        # Calculate platform fee first
        platform_fee = order_amount * (platform_fee_percent / 100)
        
        # Agent commission is % of platform fee
        multiplier = FeeConfig.AGENT_TIER_MULTIPLIERS.get(agent_tier, 1.0)
        commission = platform_fee * (FeeConfig.AGENT_FIELD_SUPPORT_COMMISSION_PERCENT / 100) * multiplier
        
        return {
            "order_amount": order_amount,
            "platform_fee": round(platform_fee, 2),
            "commission_percent": FeeConfig.AGENT_FIELD_SUPPORT_COMMISSION_PERCENT,
            "multiplier": multiplier,
            "commission_amount": round(commission, 2),
        }

    @staticmethod
    def calculate_agent_volume_commission(
        gmv: float,
        agent_tier: AgentTier = AgentTier.BRONZE
    ) -> Dict[str, float]:
        """
        Calculate agent commission based on transaction volume in their territory.
        """
        multiplier = FeeConfig.AGENT_TIER_MULTIPLIERS.get(agent_tier, 1.0)
        commission = gmv * (FeeConfig.AGENT_VOLUME_COMMISSION_PERCENT / 100) * multiplier
        
        return {
            "gmv": gmv,
            "commission_percent": FeeConfig.AGENT_VOLUME_COMMISSION_PERCENT,
            "multiplier": multiplier,
            "commission_amount": round(commission, 2),
        }

    @staticmethod
    def determine_agent_tier(rating: float) -> AgentTier:
        """
        Determine agent tier based on rating.
        """
        if rating >= 4.8:
            return AgentTier.PLATINUM
        elif rating >= 4.5:
            return AgentTier.GOLD
        elif rating >= 4.0:
            return AgentTier.SILVER
        else:
            return AgentTier.BRONZE

    @staticmethod
    def calculate_agent_rating(
        total_tasks: int,
        successful_tasks: int,
        avg_response_hours: float,
        dispute_count: int = 0
    ) -> Dict[str, Any]:
        """
        Calculate agent rating based on performance metrics.
        Rating is based on:
        - Success rate (completed vs total tasks)
        - Response time (faster = higher rating)
        - Dispute count (fewer = higher rating)
        - Task volume (more tasks = higher rating)
        """
        if total_tasks == 0:
            return {
                "rating": 3.0,
                "tier": AgentTier.BRONZE,
                "success_rate": 0.0,
                "response_score": 0.0,
                "dispute_penalty": 0.0,
                "volume_bonus": 0.0,
            }
        
        # Success rate (0-1)
        success_rate = successful_tasks / total_tasks
        
        # Response time score (0-1, faster = higher)
        # 0-12h = 1.0, 12-24h = 0.8, 24-48h = 0.6, 48h+ = 0.4
        if avg_response_hours <= 12:
            response_score = 1.0
        elif avg_response_hours <= 24:
            response_score = 0.8
        elif avg_response_hours <= 48:
            response_score = 0.6
        else:
            response_score = 0.4
        
        # Dispute penalty (0-0.5)
        dispute_penalty = min(dispute_count * 0.1, 0.5)
        
        # Volume bonus (0-0.5)
        if total_tasks >= 100:
            volume_bonus = 0.5
        elif total_tasks >= 50:
            volume_bonus = 0.3
        elif total_tasks >= 25:
            volume_bonus = 0.2
        elif total_tasks >= 10:
            volume_bonus = 0.1
        else:
            volume_bonus = 0.0
        
        # Calculate base rating (2.5-5.0)
        base_rating = 2.5 + (success_rate * 1.5) + (response_score * 0.5) + volume_bonus - dispute_penalty
        rating = min(max(base_rating, 3.0), 5.0)  # Clamp between 3.0 and 5.0
        
        tier = FeeEngine.determine_agent_tier(rating)
        
        return {
            "rating": round(rating, 2),
            "tier": tier,
            "success_rate": round(success_rate * 100, 1),
            "response_score": round(response_score * 100, 1),
            "dispute_penalty": round(dispute_penalty * 100, 1),
            "volume_bonus": round(volume_bonus * 100, 1),
        }

    @staticmethod
    def calculate_revenue_split(
        total_amount: float,
        splits: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate revenue split among multiple parties.
        Splits should be provided as percentages that sum to 100.
        """
        total_percentage = sum(splits.values())
        
        if abs(total_percentage - 100.0) > 0.01:
            raise ValueError(f"Splits must sum to 100%, got {total_percentage}%")
        
        result = {}
        for party, percentage in splits.items():
            amount = total_amount * (percentage / 100)
            result[party] = round(amount, 2)
        
        return result

    @staticmethod
    def calculate_seller_payout(
        sale_amount: float,
        platform_fee: float,
        provider_cost: float = 0.0,
        transport_fee: float = 0.0,
        insurance_fee: float = 0.0,
        commission: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate net payout to seller after all deductions.
        Provider costs are NOT deducted from seller - they're paid by buyer.
        """
        total_deductions = platform_fee + transport_fee + insurance_fee + commission
        net_payout = sale_amount - total_deductions
        
        return {
            "sale_amount": sale_amount,
            "provider_cost": provider_cost,  # Paid by buyer, not deducted from seller
            "platform_fee": platform_fee,
            "transport_fee": transport_fee,
            "insurance_fee": insurance_fee,
            "commission": commission,
            "total_deductions": round(total_deductions, 2),
            "net_payout": round(net_payout, 2),
        }

    @staticmethod
    def calculate_buyer_total(
        product_price: float,
        platform_fee: float,
        provider_cost: float = 0.0,
        transport_fee: float = 0.0,
        insurance_fee: float = 0.0,
        tax: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate total amount buyer pays including all fees and taxes.
        Buyer pays provider costs, platform fees, and taxes.
        """
        subtotal = product_price + provider_cost + platform_fee + transport_fee + insurance_fee
        total = subtotal + tax
        
        return {
            "product_price": product_price,
            "provider_cost": provider_cost,  # Provider transaction fee (EcoCash, etc.)
            "platform_fee": platform_fee,
            "transport_fee": transport_fee,
            "insurance_fee": insurance_fee,
            "subtotal": round(subtotal, 2),
            "tax": tax,
            "total": round(total, 2),
        }


# Singleton instance
fee_engine = FeeEngine()
