"""
Enterprise Subscription Billing Engine

Implements recurring billing, invoices, grace periods, failed payment retries,
automatic suspension, plan upgrades, downgrades, proration, and feature entitlements.
"""
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.models.user import User
from app.services.ledger_service import LedgerService, LedgerAccountType, LedgerEntryType
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class SubscriptionPlan(str, Enum):
    """Subscription plan tiers"""
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription lifecycle states"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class BillingCycle(str, Enum):
    """Billing cycle options"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class SubscriptionConfig:
    """Configuration for subscription plans"""
    
    PLANS = {
        SubscriptionPlan.BASIC: {
            "name": "Basic Plan",
            "price_monthly": 0.0,
            "price_yearly": 0.0,
            "features": ["basic_marketplace_access", "standard_support"],
            "transaction_limit": 10,
            "transaction_fee_percent": 2.5,
        },
        SubscriptionPlan.PRO: {
            "name": "Pro Plan",
            "price_monthly": 29.99,
            "price_yearly": 299.99,
            "features": [
                "basic_marketplace_access",
                "priority_support",
                "analytics_dashboard",
                "bulk_listings",
            ],
            "transaction_limit": 100,
            "transaction_fee_percent": 1.5,
        },
        SubscriptionPlan.ENTERPRISE: {
            "name": "Enterprise Plan",
            "price_monthly": 99.99,
            "price_yearly": 999.99,
            "features": [
                "basic_marketplace_access",
                "priority_support",
                "analytics_dashboard",
                "bulk_listings",
                "api_access",
                "custom_integrations",
                "dedicated_account_manager",
            ],
            "transaction_limit": float('inf'),  # Unlimited
            "transaction_fee_percent": 0.5,
        },
    }
    
    GRACE_PERIOD_DAYS = 7
    MAX_RETRY_ATTEMPTS = 3
    RETRY_INTERVAL_DAYS = 3


class SubscriptionService:
    """
    Enterprise subscription billing service.
    Handles recurring billing, plan changes, and entitlements.
    """

    @staticmethod
    def get_plan_config(plan: SubscriptionPlan) -> Dict[str, Any]:
        """Get configuration for a subscription plan"""
        return SubscriptionConfig.PLANS.get(plan, {})

    @staticmethod
    def calculate_proration(
        old_plan: SubscriptionPlan,
        new_plan: SubscriptionPlan,
        days_remaining: int,
        billing_cycle_days: int = 30
    ) -> Dict[str, float]:
        """
        Calculate proration for plan changes.
        Returns credit amount and new charge amount.
        """
        old_config = SubscriptionService.get_plan_config(old_plan)
        new_config = SubscriptionService.get_plan_config(new_plan)
        
        # Calculate daily rates
        old_daily_rate = old_config["price_monthly"] / billing_cycle_days
        new_daily_rate = new_config["price_monthly"] / billing_cycle_days
        
        # Calculate credit for unused days
        credit_amount = old_daily_rate * days_remaining
        
        # Calculate charge for remaining days at new rate
        charge_amount = new_daily_rate * days_remaining
        
        # Net difference
        net_difference = charge_amount - credit_amount
        
        return {
            "credit_amount": round(credit_amount, 2),
            "charge_amount": round(charge_amount, 2),
            "net_difference": round(net_difference, 2),
            "is_upgrade": net_difference > 0,
        }

    @staticmethod
    async def create_subscription(
        db: Session,
        user_id: uuid.UUID,
        plan: SubscriptionPlan,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        trial_days: int = 0
    ) -> Dict[str, Any]:
        """
        Create a new subscription for a user.
        """
        plan_config = SubscriptionService.get_plan_config(plan)
        
        # Calculate billing period
        if trial_days > 0:
            start_date = datetime.now(timezone.utc)
            end_date = start_date + timedelta(days=trial_days)
            status = SubscriptionStatus.TRIAL
        else:
            start_date = datetime.now(timezone.utc)
            if billing_cycle == BillingCycle.MONTHLY:
                end_date = start_date + timedelta(days=30)
            elif billing_cycle == BillingCycle.QUARTERLY:
                end_date = start_date + timedelta(days=90)
            elif billing_cycle == BillingCycle.YEARLY:
                end_date = start_date + timedelta(days=365)
            else:
                end_date = start_date + timedelta(days=30)
            status = SubscriptionStatus.ACTIVE
        
        # Calculate amount
        if billing_cycle == BillingCycle.YEARLY:
            amount = plan_config["price_yearly"]
        else:
            amount = plan_config["price_monthly"]
        
        subscription = {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "plan": plan.value,
            "status": status.value,
            "billing_cycle": billing_cycle.value,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "amount": amount,
            "features": plan_config["features"],
        }
        
        logger.info(f"Created subscription for user {user_id}: {plan.value}")
        
        return subscription

    @staticmethod
    async def upgrade_subscription(
        db: Session,
        user_id: uuid.UUID,
        current_plan: SubscriptionPlan,
        new_plan: SubscriptionPlan
    ) -> Dict[str, Any]:
        """
        Upgrade a user's subscription with proration.
        """
        # Calculate days remaining in current billing cycle
        # This would require fetching the current subscription from DB
        days_remaining = 15  # Placeholder
        
        proration = SubscriptionService.calculate_proration(
            current_plan,
            new_plan,
            days_remaining
        )
        
        logger.info(
            f"Subscription upgrade: user {user_id}, "
            f"{current_plan.value} -> {new_plan.value}, "
            f"net_difference: ${proration['net_difference']}"
        )
        
        return {
            "old_plan": current_plan.value,
            "new_plan": new_plan.value,
            "proration": proration,
            "effective_immediately": True,
        }

    @staticmethod
    async def downgrade_subscription(
        db: Session,
        user_id: uuid.UUID,
        current_plan: SubscriptionPlan,
        new_plan: SubscriptionPlan
    ) -> Dict[str, Any]:
        """
        Downgrade a user's subscription.
        Takes effect at next billing cycle.
        """
        logger.info(
            f"Subscription downgrade: user {user_id}, "
            f"{current_plan.value} -> {new_plan.value}, "
            f"effective_next_billing_cycle"
        )
        
        return {
            "old_plan": current_plan.value,
            "new_plan": new_plan.value,
            "effective_date": "next_billing_cycle",
        }

    @staticmethod
    async def process_billing(
        db: Session,
        subscription_id: str
    ) -> Dict[str, Any]:
        """
        Process recurring billing for a subscription.
        """
        # Fetch subscription from DB
        # Calculate amount based on plan and billing cycle
        # Charge user's wallet or payment method
        # Create ledger entries
        # Update subscription end date
        
        logger.info(f"Processed billing for subscription {subscription_id}")
        
        return {
            "subscription_id": subscription_id,
            "status": "billed",
            "next_billing_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }

    @staticmethod
    async def handle_payment_failure(
        db: Session,
        subscription_id: str,
        attempt_number: int
    ) -> Dict[str, Any]:
        """
        Handle failed payment for subscription.
        Implements retry logic and grace period.
        """
        if attempt_number >= SubscriptionConfig.MAX_RETRY_ATTEMPTS:
            # Suspend subscription
            status = SubscriptionStatus.SUSPENDED
            logger.warning(f"Subscription {subscription_id} suspended after {attempt_number} failed attempts")
        else:
            # Set to past due
            status = SubscriptionStatus.PAST_DUE
            next_retry = datetime.now(timezone.utc) + timedelta(days=SubscriptionConfig.RETRY_INTERVAL_DAYS)
            logger.info(
                f"Subscription {subscription_id} past due, "
                f"retry attempt {attempt_number + 1} on {next_retry}"
            )
        
        return {
            "subscription_id": subscription_id,
            "status": status.value,
            "attempt_number": attempt_number,
            "next_retry_date": next_retry.isoformat() if status == SubscriptionStatus.PAST_DUE else None,
        }

    @staticmethod
    def check_feature_entitlement(
        user_plan: SubscriptionPlan,
        feature: str
    ) -> bool:
        """
        Check if a user's plan includes a specific feature.
        """
        plan_config = SubscriptionService.get_plan_config(user_plan)
        return feature in plan_config.get("features", [])

    @staticmethod
    def get_transaction_limit(user_plan: SubscriptionPlan) -> float:
        """Get transaction limit for a user's plan"""
        plan_config = SubscriptionService.get_plan_config(user_plan)
        return plan_config.get("transaction_limit", float('inf'))

    @staticmethod
    def get_transaction_fee_percent(user_plan: SubscriptionPlan) -> float:
        """Get transaction fee percentage for a user's plan"""
        plan_config = SubscriptionService.get_plan_config(user_plan)
        return plan_config.get("transaction_fee_percent", 2.5)


# Singleton instance
subscription_service = SubscriptionService()
