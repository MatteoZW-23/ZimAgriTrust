"""
ZimAgriTrust – Supplier Module API Endpoints
All supplier registration, product, order, wallet, analytics, public, and admin endpoints.
"""
from __future__ import annotations

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.supplier import SupplierProfile, SupplierVerificationStatus
from app.schemas.supplier import (
    SupplierApplicationCreate,
    SupplierDocumentsSubmit,
    SupplierProfileResponse,
    SupplierProfileUpdate,
    SupplierProductCreate,
    SupplierProductUpdate,
    SupplierProductResponse,
    SupplierStockUpdate,
    BulkPriceUpdate,
    BoostProductRequest,
    SupplierOrderResponse,
    OrderItemResponse,
    TrackingUpdate,
    OrderCancelRequest,
    PublicOrderCreate,
    SupplierWalletResponse,
    SupplierWithdrawalRequest,
    SupplierWalletTxnResponse,
    PublicSupplierResponse,
    AdminSupplierAction,
)
from app.services.supplier_service import (
    SupplierRegistrationService,
    SupplierProfileService,
    SupplierProductService,
    SupplierOrderService,
    SupplierWalletService,
    SupplierAnalyticsService,
    SupplierAdminService,
    SupplierPublicService,
)

router = APIRouter()
admin_router = APIRouter()
public_router = APIRouter()
logger = logging.getLogger(__name__)


# ── Helper: get current supplier profile ──────────────────────────────────────

def _get_supplier_profile(db: Session, user: User) -> SupplierProfile:
    return SupplierProfileService.get_profile(db, user.id)


def _get_admin_uuid(user: User) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(str(user.id))
    except (TypeError, ValueError, AttributeError):
        return None


# ============================================================================
# SUPPLIER REGISTRATION (6 endpoints)
# ============================================================================

@router.post("/register/apply", tags=["supplier-registration"])
def supplier_apply(data: SupplierApplicationCreate, db: Session = Depends(get_db)):
    """Submit a new supplier application (public, no auth required)."""
    try:
        return SupplierRegistrationService.apply(db, data.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supplier application error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit supplier application")


@router.post("/register/documents", tags=["supplier-registration"])
def supplier_upload_documents(
    data: SupplierDocumentsSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Upload supporting documents for supplier application."""
    try:
        profile = _get_supplier_profile(db, user)
        docs = [d.model_dump() for d in data.documents]
        return SupplierRegistrationService.upload_documents(db, profile.id, docs)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supplier document upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload documents")


@router.get("/application/status", tags=["supplier-registration"])
def supplier_application_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Check current application/verification status."""
    try:
        return SupplierRegistrationService.get_application_status(db, user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supplier application status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve application status")


@router.post("/login", tags=["supplier-registration"])
async def supplier_login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Supplier login via PIN (delegates to portal auth service)."""
    try:
        from app.services.portal_auth_service import login_with_pin
        body = await request.json()
        return await login_with_pin(
            db=db,
            request=request,
            response=response,
            phone_number=body["phone_number"],
            pin=body["password"],
            allowed_roles={UserRole.SUPPLIER},
            portal_name="supplier",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supplier login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Supplier login failed")


# ============================================================================
# SUPPLIER PROFILE (2 endpoints)
# ============================================================================

@router.get("/profile", response_model=SupplierProfileResponse, tags=["supplier-profile"])
def get_supplier_profile(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    try:
        return SupplierProfileService.get_profile(db, user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get supplier profile error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve supplier profile")


@router.put("/profile", response_model=SupplierProfileResponse, tags=["supplier-profile"])
def update_supplier_profile(
    data: SupplierProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    try:
        return SupplierProfileService.update_profile(db, user.id, data.model_dump(exclude_none=True))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update supplier profile error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update supplier profile")


# ============================================================================
# PRODUCT MANAGEMENT (10 endpoints)
# ============================================================================

@router.post("/products", tags=["supplier-products"])
def create_product(
    data: SupplierProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    product = SupplierProductService.create_product(db, profile.id, data.model_dump())
    return SupplierProductResponse.model_validate(product)


@router.get("/products", tags=["supplier-products"])
def list_products(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    products = SupplierProductService.list_products(db, profile.id, status)
    return [SupplierProductResponse.model_validate(p) for p in products]


@router.get("/products/{product_id}", tags=["supplier-products"])
def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    product = SupplierProductService.get_product(db, product_id, profile.id)
    return SupplierProductResponse.model_validate(product)


@router.put("/products/{product_id}", tags=["supplier-products"])
def update_product(
    product_id: uuid.UUID,
    data: SupplierProductUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    product = SupplierProductService.update_product(db, product_id, profile.id, data.model_dump(exclude_none=True))
    return SupplierProductResponse.model_validate(product)


@router.delete("/products/{product_id}", tags=["supplier-products"])
def delete_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    return SupplierProductService.delete_product(db, product_id, profile.id)


@router.post("/products/{product_id}/boost", tags=["supplier-products"])
def boost_product(
    product_id: uuid.UUID,
    data: BoostProductRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    product = SupplierProductService.boost_product(db, product_id, profile.id, data.duration_days)
    return SupplierProductResponse.model_validate(product)


@router.put("/products/{product_id}/stock", tags=["supplier-products"])
def update_stock(
    product_id: uuid.UUID,
    data: SupplierStockUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    product = SupplierProductService.update_stock(db, product_id, profile.id, data.quantity_available, data.notes)
    return SupplierProductResponse.model_validate(product)


@router.get("/inventory", tags=["supplier-products"])
def get_inventory(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    products = SupplierProductService.get_inventory(db, profile.id)
    return [SupplierProductResponse.model_validate(p) for p in products]


@router.get("/low-stock-alerts", tags=["supplier-products"])
def get_low_stock_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    products = SupplierProductService.get_low_stock_alerts(db, profile.id)
    return [SupplierProductResponse.model_validate(p) for p in products]


@router.post("/bulk-price-update", tags=["supplier-products"])
def bulk_price_update(
    data: BulkPriceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    return SupplierProductService.bulk_price_update(db, profile.id, data.updates)


# ============================================================================
# ORDER MANAGEMENT (8 endpoints)
# ============================================================================

@router.get("/orders", tags=["supplier-orders"])
def list_orders(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    orders = SupplierOrderService.list_orders(db, profile.id, status)
    results = []
    for o in orders:
        d = SupplierOrderResponse.model_validate(o)
        d.buyer_name = o.buyer.full_name if o.buyer else None
        results.append(d)
    return results


@router.get("/orders/{order_id}", tags=["supplier-orders"])
def get_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    order = SupplierOrderService.get_order(db, order_id, profile.id)
    resp = SupplierOrderResponse.model_validate(order)
    resp.buyer_name = order.buyer.full_name if order.buyer else None
    resp.buyer_phone = order.buyer.phone_number if order.buyer else None
    return resp


@router.put("/orders/{order_id}/confirm", tags=["supplier-orders"])
def confirm_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    order = SupplierOrderService.confirm_order(db, order_id, profile.id)
    return {"message": "Order confirmed", "order_id": str(order.id), "status": order.status.value}


@router.put("/orders/{order_id}/ship", tags=["supplier-orders"])
def ship_order(
    order_id: uuid.UUID,
    data: TrackingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    order = SupplierOrderService.ship_order(db, order_id, profile.id, data.tracking_number, data.shipping_method)
    return {"message": "Order shipped", "order_id": str(order.id), "tracking": order.tracking_number}


@router.put("/orders/{order_id}/cancel", tags=["supplier-orders"])
def cancel_order(
    order_id: uuid.UUID,
    data: OrderCancelRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    order = SupplierOrderService.cancel_order(db, order_id, profile.id, data.reason)
    return {"message": "Order cancelled", "order_id": str(order.id)}


@router.post("/orders/{order_id}/tracking", tags=["supplier-orders"])
def add_tracking(
    order_id: uuid.UUID,
    data: TrackingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    order = SupplierOrderService.add_tracking(db, order_id, profile.id, data.tracking_number, data.shipping_method)
    return {"message": "Tracking updated", "tracking_number": order.tracking_number}


@router.get("/orders/export", tags=["supplier-orders"])
def export_orders(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    orders = SupplierOrderService.list_orders(db, profile.id)
    rows = []
    for o in orders:
        rows.append({
            "order_number": o.order_number,
            "status": o.status.value,
            "total_amount": o.total_amount,
            "payment_status": o.payment_status.value,
            "created_at": str(o.created_at),
        })
    return {"orders": rows, "total": len(rows)}


@router.post("/orders/{order_id}/invoice", tags=["supplier-orders"])
def generate_invoice(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    order = SupplierOrderService.get_order(db, order_id, profile.id)
    return {
        "invoice": {
            "order_number": order.order_number,
            "supplier": profile.business_name,
            "buyer_name": order.buyer.full_name if order.buyer else "N/A",
            "items": [{"name": i.product_name, "qty": i.quantity, "unit_price": i.unit_price, "total": i.total_price} for i in order.items],
            "subtotal": order.subtotal,
            "tax": order.tax_amount,
            "shipping": order.shipping_cost,
            "platform_fee": order.platform_fee,
            "total": order.total_amount,
            "date": str(order.created_at),
        }
    }


# ============================================================================
# SUPPLIER WALLET (5 endpoints)
# ============================================================================

@router.get("/wallet", tags=["supplier-wallet"])
def get_wallet(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    return SupplierWalletService.get_wallet(db, profile.id)


@router.get("/wallet/transactions", tags=["supplier-wallet"])
def get_wallet_transactions(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    txns = SupplierWalletService.get_transactions(db, profile.id, limit)
    return [SupplierWalletTxnResponse.model_validate(t) for t in txns]


@router.post("/wallet/withdraw", tags=["supplier-wallet"])
def withdraw(
    data: SupplierWithdrawalRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    return SupplierWalletService.withdraw(db, profile.id, data.amount, data.method, data.account_details)


@router.get("/wallet/statement", tags=["supplier-wallet"])
def get_statement(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    txns = SupplierWalletService.get_statement(db, profile.id, month, year)
    return [SupplierWalletTxnResponse.model_validate(t) for t in txns]


@router.get("/earnings", tags=["supplier-wallet"])
def get_earnings(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    return SupplierWalletService.get_earnings(db, profile.id)


# ============================================================================
# SUPPLIER ANALYTICS (4 endpoints)
# ============================================================================

@router.get("/analytics/sales", tags=["supplier-analytics"])
def sales_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    return SupplierAnalyticsService.sales_analytics(db, profile.id)


@router.get("/analytics/bestsellers", tags=["supplier-analytics"])
def bestsellers(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    return SupplierAnalyticsService.bestsellers(db, profile.id)


@router.get("/analytics/inventory", tags=["supplier-analytics"])
def inventory_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    return SupplierAnalyticsService.inventory_analytics(db, profile.id)


@router.get("/reports", tags=["supplier-analytics"])
def reports(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    return SupplierAnalyticsService.reports(db, profile.id)


# ============================================================================
# PUBLIC ENDPOINTS – BUYER FACING (5 endpoints)
# ============================================================================

@public_router.get("/list", tags=["supplier-public"])
def public_list_suppliers(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    suppliers = SupplierPublicService.list_suppliers(db, limit, offset)
    return [PublicSupplierResponse.model_validate(s) for s in suppliers]


@public_router.get("/{supplier_id}/products", tags=["supplier-public"])
def public_supplier_products(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    products = SupplierPublicService.get_supplier_products(db, supplier_id)
    result = []
    for p in products:
        resp = SupplierProductResponse.model_validate(p)
        resp.supplier_name = p.supplier.business_name if p.supplier else None
        resp.supplier_rating = p.supplier.rating if p.supplier else None
        resp.supplier_verification = p.supplier.verification_status.value if p.supplier else None
        result.append(resp)
    return result


@public_router.get("/products", tags=["supplier-public"])
def public_list_products(
    category: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    products = SupplierPublicService.list_all_products(db, category, product_type, search, limit, offset)
    result = []
    for p in products:
        resp = SupplierProductResponse.model_validate(p)
        resp.supplier_name = p.supplier.business_name if p.supplier else None
        resp.supplier_rating = p.supplier.rating if p.supplier else None
        resp.supplier_verification = p.supplier.verification_status.value if p.supplier else None
        result.append(resp)
    return result


@public_router.get("/products/{product_id}", tags=["supplier-public"])
def public_product_detail(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    return SupplierPublicService.get_product_detail(db, product_id)


@public_router.post("/orders", tags=["supplier-public"])
def public_create_order(
    data: PublicOrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Buyer places an order for supplier products."""
    items = [{"product_id": str(i.product_id), "quantity": i.quantity} for i in data.items]
    order = SupplierOrderService.create_order_from_buyer(db, user.id, {
        "items": items,
        "delivery_address": data.delivery_address,
        "delivery_phone": data.delivery_phone,
        "shipping_method": data.shipping_method,
        "buyer_notes": data.buyer_notes,
        "promo_code": data.promo_code,
    })
    return {"message": "Order placed", "order_id": str(order.id), "order_number": order.order_number}


# ============================================================================
# ADMIN ENDPOINTS – SUPPLIER MANAGEMENT (7 endpoints)
# ============================================================================

@admin_router.get("/pending", tags=["admin-suppliers"])
def admin_pending_suppliers(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    suppliers = SupplierAdminService.get_pending(db)
    return [SupplierProfileResponse.model_validate(s) for s in suppliers]


@admin_router.get("/{supplier_id}", tags=["admin-suppliers"])
def admin_get_supplier(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return SupplierProfileResponse.model_validate(SupplierAdminService.get_supplier_detail(db, supplier_id))


@admin_router.post("/{supplier_id}/approve", tags=["admin-suppliers"])
def admin_approve_supplier(
    supplier_id: uuid.UUID,
    data: AdminSupplierAction,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return SupplierAdminService.approve(db, supplier_id, _get_admin_uuid(user), data.notes)


@admin_router.post("/{supplier_id}/reject", tags=["admin-suppliers"])
def admin_reject_supplier(
    supplier_id: uuid.UUID,
    data: AdminSupplierAction,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return SupplierAdminService.reject(db, supplier_id, _get_admin_uuid(user), data.notes)


@admin_router.post("/{supplier_id}/suspend", tags=["admin-suppliers"])
def admin_suspend_supplier(
    supplier_id: uuid.UUID,
    data: AdminSupplierAction,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return SupplierAdminService.suspend(db, supplier_id, _get_admin_uuid(user), data.notes)


@admin_router.get("/{supplier_id}/documents", tags=["admin-suppliers"])
def admin_get_documents(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    docs = SupplierAdminService.get_documents(db, supplier_id)
    return [{"id": str(d.id), "type": d.document_type, "url": d.document_url, "name": d.document_name, "verified": d.is_verified} for d in docs]


@admin_router.put("/categories", tags=["admin-suppliers"])
def admin_update_categories(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return {"message": "Categories managed via product enums", "categories": {
        "input": ["seeds", "fertilizer", "pesticides", "herbicides", "fungicides", "animal_feed"],
        "machinery": ["tractor", "sprayer", "irrigation", "tiller", "harvester", "tools"],
    }}
