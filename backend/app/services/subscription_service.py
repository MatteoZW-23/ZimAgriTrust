from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from app.models.subscription import (
    BillingHistory,
    Subscription,
    SubscriptionBenefit,
    SubscriptionDowngrade,
    SubscriptionFeature,
    SubscriptionPlanModel,
    SubscriptionRenewal,
    SubscriptionUpgrade,
)
from app.models.supplier import SupplierProfile
from app.models.transaction import Order, OrderStatus
from app.models.user import User, UserRole


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"
    PAST_DUE = "EXPIRED"
    TRIAL = "PENDING"


class BillingCycle(str, enum.Enum):
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"
    YEARLY = "ANNUAL"


@dataclass(frozen=True)
class PlanDefinition:
    role: str
    code: str
    name: str
    monthly_price: float
    platform_fee_percent: float
    visibility_weight: int
    sort_order: int
    features: tuple[str, ...]
    benefits: tuple[str, ...]

    @property
    def annual_price(self) -> float:
        return round(self.monthly_price * 12, 2)


PLAN_DEFINITIONS: tuple[PlanDefinition, ...] = (
    PlanDefinition("farmer", "free", "Free", 0, 3, 100, 1, (
        "Marketplace Access", "Listings", "Orders", "Wallet", "Withdrawals",
        "Escrow", "Ratings", "Trust Score",
    ), ("Earn before paying", "Core marketplace access")),
    PlanDefinition("farmer", "pro", "Pro", 3, 2, 200, 2, (
        "Featured Listings", "Verified Pro Badge", "Priority Search Ranking",
        "Market Insights", "Demand Reports", "Higher Visibility", "Priority Support",
    ), ("Lower fees", "Higher listing visibility", "Better business insights")),
    PlanDefinition("farmer", "enterprise", "Enterprise", 20, 1, 300, 3, (
        "Enterprise Badge", "Multi User Access", "Farm Team Accounts",
        "Advanced Analytics", "Contract Farming Tools", "Export Reports", "Dedicated Support",
    ), ("Lowest farmer fees", "Enterprise trust signals", "Team growth tools")),
    PlanDefinition("buyer", "free", "Free", 0, 3, 100, 1, (
        "Browse Marketplace", "Offers", "Orders", "Escrow", "Ratings",
    ), ("Buy before paying", "Core procurement access")),
    PlanDefinition("buyer", "pro", "Pro", 5, 2, 200, 2, (
        "Verified Buyer Badge", "Price Alerts", "Saved Searches", "Priority Matching",
        "Market Intelligence", "Advanced Filters", "Priority Support",
    ), ("Lower fees", "Smarter sourcing", "Better matching")),
    PlanDefinition("buyer", "enterprise", "Enterprise", 30, 1, 300, 3, (
        "Enterprise Buyer Badge", "Team Accounts", "Procurement Dashboard",
        "Contract Management", "Bulk Requests", "Advanced Analytics", "API Access",
        "Dedicated Support",
    ), ("Lowest buyer fees", "Procurement controls", "Team buying workflows")),
    PlanDefinition("supplier", "basic", "Basic", 10, 8, 100, 1, (
        "Product Listings", "Inventory Management", "Orders",
    ), ("Supplier storefront", "Inventory sales tools")),
    PlanDefinition("supplier", "pro", "Pro", 25, 5, 200, 2, (
        "Promotions", "Priority Listings", "Analytics", "Inventory Insights", "Pro Badge",
    ), ("Lower supplier fees", "Priority product visibility", "Inventory insights")),
    PlanDefinition("supplier", "enterprise", "Enterprise", 50, 3, 300, 3, (
        "Enterprise Badge", "Unlimited Products", "Team Accounts", "API Access",
        "Advanced Analytics", "Dedicated Support",
    ), ("Lowest supplier fees", "Unlimited scale", "API and team operations")),
)

BASELINE_PLAN = {"farmer": "free", "buyer": "free", "supplier": "basic"}
VERIFICATION_BADGE = {
    "farmer": "VERIFIED FARMER",
    "buyer": "VERIFIED BUYER",
    "supplier": "VERIFIED SUPPLIER",
}


def _norm(value: Any) -> str:
    raw = value.value if hasattr(value, "value") else str(value)
    return raw.strip().lower()


class SubscriptionService:
    @staticmethod
    def normalize_role(value: Any) -> str:
        role = _norm(value)
        if role not in {"farmer", "buyer", "supplier"}:
            raise HTTPException(status_code=400, detail="Subscriptions are only available for farmers, buyers, and suppliers")
        return role

    @staticmethod
    def default_plan_for_role(role: str) -> str:
        return BASELINE_PLAN[SubscriptionService.normalize_role(role)]

    @staticmethod
    def plan_matrix() -> list[dict[str, Any]]:
        return [
            {
                "role": p.role,
                "code": p.code,
                "name": p.name,
                "monthly_price": p.monthly_price,
                "annual_price": p.annual_price,
                "platform_fee_percent": p.platform_fee_percent,
                "visibility_weight": p.visibility_weight,
                "features": list(p.features),
                "benefits": list(p.benefits),
                "is_active": True,
            }
            for p in PLAN_DEFINITIONS
        ]

    @staticmethod
    def get_plan_definition(role: str, code: str) -> PlanDefinition:
        role = SubscriptionService.normalize_role(role)
        code = _norm(code)
        for plan in PLAN_DEFINITIONS:
            if plan.role == role and plan.code == code:
                return plan
        raise HTTPException(status_code=404, detail="Subscription plan not found")

    @staticmethod
    def get_plan_config(plan: SubscriptionPlan | str, role: str = "supplier") -> Any:
        definition = SubscriptionService.get_plan_definition(role, _norm(plan))
        return type("PlanConfig", (), {
            "name": definition.name,
            "price_monthly": definition.monthly_price,
            "price_annual": definition.annual_price,
            "transaction_fee_percent": definition.platform_fee_percent,
            "features": list(definition.features),
            "benefits": list(definition.benefits),
            "visibility_weight": definition.visibility_weight,
        })()

    @staticmethod
    def ensure_default_plans(db: Session, commit: bool = True) -> None:
        for definition in PLAN_DEFINITIONS:
            plan = db.query(SubscriptionPlanModel).filter(
                SubscriptionPlanModel.role == definition.role,
                SubscriptionPlanModel.code == definition.code,
            ).first()
            if not plan:
                plan = SubscriptionPlanModel(
                    role=definition.role,
                    code=definition.code,
                    name=definition.name,
                    monthly_price=definition.monthly_price,
                    annual_price=definition.annual_price,
                    platform_fee_percent=definition.platform_fee_percent,
                    visibility_weight=definition.visibility_weight,
                    sort_order=definition.sort_order,
                    is_active=True,
                )
                db.add(plan)
                db.flush()
            else:
                plan.name = definition.name
                plan.monthly_price = definition.monthly_price
                plan.annual_price = definition.annual_price
                plan.platform_fee_percent = definition.platform_fee_percent
                plan.visibility_weight = definition.visibility_weight
                plan.sort_order = definition.sort_order
                plan.is_active = True

            for label in definition.features:
                key = label.lower().replace(" ", "_").replace("-", "_")
                feat_stmt = insert(SubscriptionFeature).values(
                    plan_id=plan.id,
                    feature_key=key,
                    label=label,
                    is_enabled=True,
                )
                feat_stmt = feat_stmt.on_conflict_do_update(
                    constraint="uq_subscription_feature_plan_key",
                    set_={"label": label, "is_enabled": True},
                )
                db.execute(feat_stmt)

            for label in definition.benefits:
                key = label.lower().replace(" ", "_").replace("-", "_")
                ben_stmt = insert(SubscriptionBenefit).values(
                    plan_id=plan.id,
                    benefit_key=key,
                    label=label,
                    value={"text": label},
                )
                ben_stmt = ben_stmt.on_conflict_do_update(
                    constraint="uq_subscription_benefit_plan_key",
                    set_={"label": label, "value": {"text": label}},
                )
                db.execute(ben_stmt)
        if commit:
            db.commit()
        else:
            db.flush()

    @staticmethod
    def get_plans(db: Session, role: str) -> list[SubscriptionPlanModel]:
        role = SubscriptionService.normalize_role(role)
        SubscriptionService.ensure_default_plans(db)
        return (
            db.query(SubscriptionPlanModel)
            .options(selectinload(SubscriptionPlanModel.features), selectinload(SubscriptionPlanModel.benefits))
            .filter(SubscriptionPlanModel.role == role)
            .order_by(SubscriptionPlanModel.sort_order.asc())
            .all()
        )

    @staticmethod
    def _active_subscription_query(db: Session, role: str):
        return db.query(Subscription).options(selectinload(Subscription.plan)).filter(
            Subscription.role == role,
            Subscription.status == SubscriptionStatus.ACTIVE.value,
        )

    @staticmethod
    def get_current_subscription(
        db: Session,
        user: Optional[User] = None,
        supplier: Optional[SupplierProfile] = None,
        create_default: bool = True,
    ) -> Subscription:
        if supplier is not None:
            role = "supplier"
            subscription = SubscriptionService._active_subscription_query(db, role).filter(
                Subscription.supplier_id == supplier.id
            ).order_by(Subscription.created_at.desc()).first()
            owner_filter = {"supplier_id": supplier.id}
        elif user is not None:
            role = SubscriptionService.normalize_role(user.role)
            subscription = SubscriptionService._active_subscription_query(db, role).filter(
                Subscription.user_id == user.id
            ).order_by(Subscription.created_at.desc()).first()
            owner_filter = {"user_id": user.id}
        else:
            raise HTTPException(status_code=400, detail="Subscription owner is required")

        if subscription or not create_default:
            return subscription

        default_code = SubscriptionService.default_plan_for_role(role)
        plan = SubscriptionService._get_plan_model(db, role, default_code)
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            role=role,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE.value,
            billing_cycle=BillingCycle.MONTHLY.value,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            **owner_filter,
        )
        db.add(subscription)
        if supplier is not None:
            supplier.subscription_plan = default_code
            supplier.subscription_status = "active"
            supplier.subscription_start_date = now
            supplier.subscription_end_date = subscription.current_period_end
        elif user is not None and hasattr(user, "subscription_tier"):
            user.subscription_tier = SubscriptionService._legacy_user_tier(default_code)
            user.subscription_expires_at = subscription.current_period_end
        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def _legacy_user_tier(code: str):
        from app.models.user import SubscriptionTier

        if code == "enterprise":
            return SubscriptionTier.ENTERPRISE
        if code == "pro":
            return SubscriptionTier.PREMIUM
        return SubscriptionTier.BASIC

    @staticmethod
    def _get_plan_model(db: Session, role: str, code: str) -> SubscriptionPlanModel:
        role = SubscriptionService.normalize_role(role)
        code = _norm(code)
        SubscriptionService.ensure_default_plans(db, commit=False)
        plan = db.query(SubscriptionPlanModel).filter(
            SubscriptionPlanModel.role == role,
            SubscriptionPlanModel.code == code,
            SubscriptionPlanModel.is_active.is_(True),
        ).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Subscription plan not found or disabled")
        return plan

    @staticmethod
    def change_plan(
        db: Session,
        plan_code: str,
        billing_cycle: str = BillingCycle.MONTHLY.value,
        user: Optional[User] = None,
        supplier: Optional[SupplierProfile] = None,
        activate_paid: bool = False,
    ) -> dict[str, Any]:
        current = SubscriptionService.get_current_subscription(db, user=user, supplier=supplier)
        role = current.role
        target = SubscriptionService._get_plan_model(db, role, plan_code)
        cycle = _norm(billing_cycle).upper()
        if cycle == "YEARLY":
            cycle = BillingCycle.ANNUAL.value
        if cycle not in {BillingCycle.MONTHLY.value, BillingCycle.ANNUAL.value}:
            raise HTTPException(status_code=400, detail="Unsupported billing cycle")

        amount = target.annual_price if cycle == BillingCycle.ANNUAL.value else target.monthly_price
        free_or_active = amount <= 0 or activate_paid
        now = datetime.now(timezone.utc)

        if current.plan_id == target.id and current.status == SubscriptionStatus.ACTIVE.value:
            return SubscriptionService.serialize_subscription(db, current)

        current.status = SubscriptionStatus.CANCELLED.value
        current.cancelled_at = now

        next_subscription = Subscription(
            user_id=current.user_id,
            supplier_id=current.supplier_id,
            role=role,
            plan_id=target.id,
            status=SubscriptionStatus.ACTIVE.value if free_or_active else SubscriptionStatus.PENDING.value,
            billing_cycle=cycle,
            current_period_start=now if free_or_active else None,
            current_period_end=(now + timedelta(days=365 if cycle == BillingCycle.ANNUAL.value else 30)) if free_or_active else None,
        )
        db.add(next_subscription)
        db.flush()

        delta = max(0.0, amount - (current.plan.monthly_price if cycle == BillingCycle.MONTHLY.value else current.plan.annual_price))
        movement_cls = SubscriptionUpgrade if target.visibility_weight >= current.plan.visibility_weight else SubscriptionDowngrade
        db.add(movement_cls(
            subscription_id=next_subscription.id,
            from_plan_id=current.plan_id,
            to_plan_id=target.id,
            amount_delta=round(delta, 2),
        ))

        if amount > 0:
            db.add(BillingHistory(
                subscription_id=next_subscription.id,
                amount=amount,
                currency="USD",
                status="PAID" if free_or_active else "PENDING",
                paid_at=now if free_or_active else None,
            ))
            db.add(SubscriptionRenewal(
                subscription_id=next_subscription.id,
                due_at=now + timedelta(days=365 if cycle == BillingCycle.ANNUAL.value else 30),
                status="PENDING",
                amount=amount,
            ))

        if supplier is not None:
            supplier.subscription_plan = target.code
            supplier.subscription_status = "active" if free_or_active else "pending"
            supplier.subscription_start_date = now if free_or_active else None
            supplier.subscription_end_date = next_subscription.current_period_end
        elif user is not None:
            user.subscription_tier = SubscriptionService._legacy_user_tier(target.code)
            user.subscription_expires_at = next_subscription.current_period_end

        db.commit()
        db.refresh(next_subscription)
        return SubscriptionService.serialize_subscription(db, next_subscription)

    @staticmethod
    def activate_pending_subscription(db: Session, subscription_id: uuid.UUID, reference: str | None = None) -> Subscription:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        now = datetime.now(timezone.utc)
        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.current_period_start = now
        subscription.current_period_end = now + timedelta(days=365 if subscription.billing_cycle == BillingCycle.ANNUAL.value else 30)
        bill = db.query(BillingHistory).filter(BillingHistory.subscription_id == subscription.id).order_by(BillingHistory.created_at.desc()).first()
        if bill:
            bill.status = "PAID"
            bill.reference = reference or bill.reference
            bill.paid_at = now
        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def cancel_subscription(db: Session, user: Optional[User] = None, supplier: Optional[SupplierProfile] = None) -> dict[str, Any]:
        subscription = SubscriptionService.get_current_subscription(db, user=user, supplier=supplier)
        now = datetime.now(timezone.utc)
        subscription.status = SubscriptionStatus.CANCELLED.value
        subscription.cancelled_at = now
        role = subscription.role
        default_plan = SubscriptionService.default_plan_for_role(role)
        db.commit()
        return SubscriptionService.change_plan(db, default_plan, user=user, supplier=supplier, activate_paid=True)

    @staticmethod
    def get_fee_percent(
        db: Optional[Session] = None,
        user: Optional[User] = None,
        supplier: Optional[SupplierProfile] = None,
        role: Optional[str] = None,
        plan_code: Optional[str] = None,
    ) -> float:
        if plan_code and role:
            return SubscriptionService.get_plan_definition(role, plan_code).platform_fee_percent
        if db is not None and (user is not None or supplier is not None):
            subscription = SubscriptionService.get_current_subscription(db, user=user, supplier=supplier)
            return float(subscription.plan.platform_fee_percent)
        if role:
            return SubscriptionService.get_plan_definition(role, SubscriptionService.default_plan_for_role(role)).platform_fee_percent
        return 3.0

    @staticmethod
    def calculate_fee(amount: float, role: str, plan_code: str) -> dict[str, float]:
        definition = SubscriptionService.get_plan_definition(role, plan_code)
        fee = round(float(amount) * (definition.platform_fee_percent / 100), 2)
        baseline = SubscriptionService.get_plan_definition(role, BASELINE_PLAN[definition.role])
        baseline_fee = round(float(amount) * (baseline.platform_fee_percent / 100), 2)
        return {
            "fee_percent": definition.platform_fee_percent,
            "platform_fee": fee,
            "baseline_fee": baseline_fee,
            "savings": round(max(0.0, baseline_fee - fee), 2),
        }

    @staticmethod
    def calculate_fee_for_owner(
        db: Session,
        amount: float,
        user: Optional[User] = None,
        supplier: Optional[SupplierProfile] = None,
    ) -> dict[str, Any]:
        subscription = SubscriptionService.get_current_subscription(db, user=user, supplier=supplier)
        values = SubscriptionService.calculate_fee(amount, subscription.role, subscription.plan.code)
        values.update({
            "role": subscription.role,
            "plan_code": subscription.plan.code,
            "plan_name": subscription.plan.name,
            "visibility_weight": subscription.plan.visibility_weight,
        })
        return values

    @staticmethod
    def get_badges(db: Session, user: Optional[User] = None, supplier: Optional[SupplierProfile] = None) -> list[str]:
        subscription = SubscriptionService.get_current_subscription(db, user=user, supplier=supplier)
        badges: list[str] = []
        if subscription.plan.code == "pro":
            badges.append("PRO")
        if subscription.plan.code == "enterprise":
            badges.append("ENTERPRISE")
        if supplier is not None:
            if supplier.verification_status and _norm(supplier.verification_status) == "approved":
                badges.append(VERIFICATION_BADGE["supplier"])
        elif user is not None:
            if subscription.role == "farmer" and bool(getattr(user, "id_verified", False)):
                badges.append(VERIFICATION_BADGE["farmer"])
            if subscription.role == "buyer" and (bool(getattr(user, "id_verified", False)) or bool(getattr(user, "business_verified", False))):
                badges.append(VERIFICATION_BADGE["buyer"])
        return badges

    @staticmethod
    def visibility_weight(db: Session, user: Optional[User] = None, supplier: Optional[SupplierProfile] = None) -> int:
        subscription = SubscriptionService.get_current_subscription(db, user=user, supplier=supplier)
        return int(subscription.plan.visibility_weight)

    @staticmethod
    def has_feature(
        db: Session,
        feature_label: str,
        user: Optional[User] = None,
        supplier: Optional[SupplierProfile] = None,
    ) -> bool:
        subscription = SubscriptionService.get_current_subscription(db, user=user, supplier=supplier)
        enabled = {f.label.lower() for f in subscription.plan.features if getattr(f, "is_enabled", False)}
        return feature_label.lower() in enabled

    @staticmethod
    def savings_dashboard(db: Session, user: Optional[User] = None, supplier: Optional[SupplierProfile] = None) -> dict[str, Any]:
        subscription = SubscriptionService.get_current_subscription(db, user=user, supplier=supplier)
        if supplier is not None:
            amount_sum = float(sum(o.subtotal or 0 for o in supplier.orders)) if hasattr(supplier, "orders") else 0.0
            fee_paid = float(sum(o.platform_fee or 0 for o in supplier.orders)) if hasattr(supplier, "orders") else 0.0
        else:
            amount_sum = float(db.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
                Order.seller_id == user.id,
                Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED]),
            ).scalar() or 0.0)
            fee_paid = float(db.query(func.coalesce(func.sum(Order.platform_fee), 0)).filter(
                Order.seller_id == user.id,
                Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED]),
            ).scalar() or 0.0)

        baseline_percent = SubscriptionService.get_plan_definition(subscription.role, BASELINE_PLAN[subscription.role]).platform_fee_percent
        baseline_fee = round(amount_sum * (baseline_percent / 100), 2)
        return {
            "plan": subscription.plan.code,
            "role": subscription.role,
            "current_fee_percent": subscription.plan.platform_fee_percent,
            "baseline_fee_percent": baseline_percent,
            "total_fees_paid": round(fee_paid, 2),
            "estimated_without_plan": baseline_fee,
            "total_fees_saved": round(max(0.0, baseline_fee - fee_paid), 2),
            "current_plan_savings_percent": round(max(0.0, baseline_percent - subscription.plan.platform_fee_percent), 2),
        }

    @staticmethod
    def serialize_plan(plan: SubscriptionPlanModel) -> dict[str, Any]:
        return {
            "id": str(plan.id),
            "role": plan.role,
            "code": plan.code,
            "name": plan.name,
            "monthly_price": plan.monthly_price,
            "annual_price": plan.annual_price,
            "platform_fee_percent": plan.platform_fee_percent,
            "visibility_weight": plan.visibility_weight,
            "is_active": plan.is_active,
            "features": [f.label for f in plan.features if f.is_enabled],
            "benefits": [b.label for b in plan.benefits],
        }

    @staticmethod
    def serialize_subscription(db: Session, subscription: Subscription) -> dict[str, Any]:
        return {
            "id": str(subscription.id),
            "role": subscription.role,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "plan": SubscriptionService.serialize_plan(subscription.plan),
        }

    @staticmethod
    def admin_subscribers(db: Session) -> list[dict[str, Any]]:
        rows = (
            db.query(Subscription)
            .options(selectinload(Subscription.plan))
            .order_by(Subscription.created_at.desc())
            .limit(500)
            .all()
        )
        return [SubscriptionService.serialize_subscription(db, row) for row in rows]

    @staticmethod
    def analytics(db: Session) -> dict[str, Any]:
        SubscriptionService.ensure_default_plans(db)
        active = db.query(Subscription).filter(Subscription.status == SubscriptionStatus.ACTIVE.value).count()
        cancelled = db.query(Subscription).filter(Subscription.status == SubscriptionStatus.CANCELLED.value).count()
        total = db.query(Subscription).count() or 1
        revenue = float(db.query(func.coalesce(func.sum(BillingHistory.amount), 0)).filter(BillingHistory.status == "PAID").scalar() or 0.0)
        renewals_due = db.query(SubscriptionRenewal).filter(SubscriptionRenewal.status == "PENDING").count()
        popularity = (
            db.query(SubscriptionPlanModel.role, SubscriptionPlanModel.code, func.count(Subscription.id))
            .join(Subscription, Subscription.plan_id == SubscriptionPlanModel.id, isouter=True)
            .group_by(SubscriptionPlanModel.role, SubscriptionPlanModel.code, SubscriptionPlanModel.sort_order)
            .order_by(SubscriptionPlanModel.role.asc(), SubscriptionPlanModel.sort_order.asc())
            .all()
        )
        return {
            "subscriber_count": active,
            "subscription_revenue": round(revenue, 2),
            "churn_rate": round((cancelled / total) * 100, 2),
            "renewal_rate": round(((active - renewals_due) / max(active, 1)) * 100, 2),
            "renewals_due": renewals_due,
            "plan_popularity": [
                {"role": role, "plan": code, "count": count}
                for role, code, count in popularity
            ],
        }
