import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.subscription import SubscriptionPlanModel
from app.models.supplier import SupplierProfile
from app.models.user import User, UserRole
from app.services.subscription_service import BillingCycle, SubscriptionService
from app.services.notification_service import NotificationService

router = APIRouter()
admin_router = APIRouter()


class SubscriptionChangeRequest(BaseModel):
    plan_code: str = Field(min_length=3, max_length=20)
    billing_cycle: str = Field(default=BillingCycle.MONTHLY.value, max_length=20)


class PlanUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=80)
    monthly_price: Optional[float] = Field(default=None, ge=0)
    annual_price: Optional[float] = Field(default=None, ge=0)
    platform_fee_percent: Optional[float] = Field(default=None, ge=0, le=100)
    visibility_weight: Optional[int] = Field(default=None, ge=0, le=1000)
    is_active: Optional[bool] = None


class PlanCreateRequest(BaseModel):
    role: str = Field(min_length=3, max_length=20)
    code: str = Field(min_length=3, max_length=20)
    name: str = Field(min_length=1, max_length=80)
    monthly_price: float = Field(ge=0)
    annual_price: float = Field(ge=0)
    platform_fee_percent: float = Field(ge=0, le=100)
    visibility_weight: int = Field(default=100, ge=0, le=1000)


def _owner(db: Session, user: User) -> tuple[Optional[User], Optional[SupplierProfile]]:
    if user.role == UserRole.SUPPLIER:
        supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == user.id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier profile not found")
        return None, supplier
    SubscriptionService.normalize_role(user.role)
    return user, None


@router.get("/plans")
def list_plans(role: str = Query("buyer", pattern="^(farmer|buyer|supplier)$"), db: Session = Depends(get_db)):
    plans = SubscriptionService.get_plans(db, role)
    return [SubscriptionService.serialize_plan(plan) for plan in plans if plan.is_active]


@router.get("/me")
def current_subscription(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user, supplier = _owner(db, current_user)
    subscription = SubscriptionService.get_current_subscription(db, user=user, supplier=supplier)
    payload = SubscriptionService.serialize_subscription(db, subscription)
    payload["badges"] = SubscriptionService.get_badges(db, user=user, supplier=supplier)
    payload["savings"] = SubscriptionService.savings_dashboard(db, user=user, supplier=supplier)
    return payload


@router.post("/upgrade")
def upgrade_subscription(
    payload: SubscriptionChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user, supplier = _owner(db, current_user)
    result = SubscriptionService.change_plan(
        db,
        payload.plan_code,
        payload.billing_cycle,
        user=user,
        supplier=supplier,
        activate_paid=True,
    )
    target_user = current_user if current_user else None
    if target_user:
        import asyncio
        try:
            asyncio.run(NotificationService.dispatch_event(
                db,
                target_user,
                "subscription_upgraded",
                priority="informational",
                PLAN=payload.plan_code.upper(),
            ))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.create_task(NotificationService.dispatch_event(
                db,
                target_user,
                "subscription_upgraded",
                priority="informational",
                PLAN=payload.plan_code.upper(),
            ))
    return result


@router.post("/cancel")
def cancel_subscription(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user, supplier = _owner(db, current_user)
    result = SubscriptionService.cancel_subscription(db, user=user, supplier=supplier)
    import asyncio
    try:
        asyncio.run(NotificationService.dispatch_event(
            db,
            current_user,
            "subscription_cancelled",
            priority="informational",
        ))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.create_task(NotificationService.dispatch_event(
            db,
            current_user,
            "subscription_cancelled",
            priority="informational",
        ))
    return result


@router.get("/savings")
def subscription_savings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user, supplier = _owner(db, current_user)
    return SubscriptionService.savings_dashboard(db, user=user, supplier=supplier)


@router.get("/quote")
def fee_quote(
    amount: float = Query(..., ge=0),
    role: str = Query(..., pattern="^(farmer|buyer|supplier)$"),
    plan_code: str = Query(..., min_length=3, max_length=20),
):
    return SubscriptionService.calculate_fee(amount, role, plan_code)


@admin_router.get("/subscribers")
def admin_subscribers(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
        UserRole.SYSTEM_ADMIN,
        UserRole.FINANCE_ADMIN,
        UserRole.REGIONAL_ADMIN,
    )),
):
    return SubscriptionService.admin_subscribers(db)


@admin_router.get("/analytics")
def admin_subscription_analytics(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
        UserRole.SYSTEM_ADMIN,
        UserRole.FINANCE_ADMIN,
        UserRole.REGIONAL_ADMIN,
    )),
):
    return SubscriptionService.analytics(db)


@admin_router.post("/plans")
def create_plan(
    payload: PlanCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN)),
):
    role = SubscriptionService.normalize_role(payload.role)
    existing = db.query(SubscriptionPlanModel).filter(
        SubscriptionPlanModel.role == role,
        SubscriptionPlanModel.code == payload.code.lower(),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Plan already exists")
    plan = SubscriptionPlanModel(
        role=role,
        code=payload.code.lower(),
        name=payload.name,
        monthly_price=payload.monthly_price,
        annual_price=payload.annual_price,
        platform_fee_percent=payload.platform_fee_percent,
        visibility_weight=payload.visibility_weight,
        is_active=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return SubscriptionService.serialize_plan(plan)


@admin_router.patch("/plans/{plan_id}")
def update_plan(
    plan_id: uuid.UUID,
    payload: PlanUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN)),
):
    plan = db.query(SubscriptionPlanModel).filter(SubscriptionPlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return SubscriptionService.serialize_plan(plan)


@admin_router.post("/plans/{plan_id}/enable")
def enable_plan(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN)),
):
    return _set_plan_enabled(db, plan_id, True)


@admin_router.post("/plans/{plan_id}/disable")
def disable_plan(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN)),
):
    return _set_plan_enabled(db, plan_id, False)


def _set_plan_enabled(db: Session, plan_id: uuid.UUID, enabled: bool):
    plan = db.query(SubscriptionPlanModel).filter(SubscriptionPlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.is_active = enabled
    db.commit()
    db.refresh(plan)
    return SubscriptionService.serialize_plan(plan)
