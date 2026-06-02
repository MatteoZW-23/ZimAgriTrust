"""
ZimAgriTrust – Supplier Module API Endpoints
All supplier registration, product, order, wallet, analytics, public, and admin endpoints.
"""
from __future__ import annotations

import uuid
import logging
from typing import Optional
from time import time

from fastapi import APIRouter, Depends, Query, Request, Response, HTTPException, UploadFile, File, Body
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
    CSVImportResponse,
    SupplierReviewCreate,
    SupplierReviewResponse,
    SupplierReviewUpdate,
    SupplierReviewListResponse,
    SupplierDiscountCreate,
    SupplierDiscountUpdate,
    SupplierDiscountResponse,
    DiscountValidationRequest,
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
    SupplierReviewService,
    SupplierSubscriptionService,
    SupplierLogisticsService,
    SupplierPayoutService,
    SupplierDiscountService,
)

router = APIRouter()
admin_router = APIRouter()
public_router = APIRouter()
logger = logging.getLogger(__name__)
_SUPPLIER_PUBLIC_CACHE: dict[str, tuple[float, object]] = {}


def _supplier_cache_get(key: str):
    rec = _SUPPLIER_PUBLIC_CACHE.get(key)
    if not rec:
        return None
    expires_at, payload = rec
    if time() >= expires_at:
        _SUPPLIER_PUBLIC_CACHE.pop(key, None)
        return None
    return payload


def _supplier_cache_set(key: str, payload: object, ttl_seconds: int):
    _SUPPLIER_PUBLIC_CACHE[key] = (time() + ttl_seconds, payload)


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


@router.post("/products/bulk-import", response_model=CSVImportResponse, tags=["supplier-products"])
async def bulk_import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """
    Bulk import products from CSV file.
    CSV format: product_type,name,description,price,quantity,unit_type,category,brand,manufacturer,min_stock_level,condition,warranty_months
    """
    try:
        profile = _get_supplier_profile(db, user)
        
        # Read file content
        content = await file.read()
        csv_data = content.decode('utf-8')
        
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Call service to import
        result = SupplierProductService.bulk_import_from_csv(
            db, 
            profile.id, 
            csv_data, 
            file.filename, 
            len(content)
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk import error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk import failed: {str(e)}")


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


@router.put("/orders/{order_id}/deliver", tags=["supplier-orders"])
def deliver_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    profile = _get_supplier_profile(db, user)
    order = SupplierOrderService.mark_delivered(db, order_id, profile.id)
    return {
        "message": "Order delivered and settlement released",
        "order_id": str(order.id),
        "status": order.status.value,
        "payment_status": order.payment_status.value,
    }


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
    from app.services.subscription_service import SubscriptionService
    enriched = []
    for supplier in sorted(
        suppliers,
        key=lambda item: (SubscriptionService.visibility_weight(db, supplier=item), item.rating, item.total_sales),
        reverse=True,
    ):
        response = PublicSupplierResponse.model_validate(supplier)
        response.subscription_plan = supplier.subscription_plan or "basic"
        response.badges = SubscriptionService.get_badges(db, supplier=supplier)
        response.visibility_weight = SubscriptionService.visibility_weight(db, supplier=supplier)
        enriched.append(response)
    return enriched


@public_router.get("/{supplier_id}/products", tags=["supplier-public"])
def public_supplier_products(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    products = SupplierPublicService.get_supplier_products(db, supplier_id)
    result = []
    for p in products:
        from app.services.subscription_service import SubscriptionService
        supplier = p.supplier
        resp = SupplierProductResponse.model_validate(p)
        resp.supplier_name = supplier.business_name if supplier else None
        resp.supplier_rating = supplier.rating if supplier else None
        resp.supplier_verification = supplier.verification_status.value if supplier else None
        resp.supplier_subscription_plan = supplier.subscription_plan if supplier else "basic"
        resp.supplier_badges = SubscriptionService.get_badges(db, supplier=supplier) if supplier else []
        resp.visibility_weight = SubscriptionService.visibility_weight(db, supplier=supplier) if supplier else 100
        result.append(resp)
    return sorted(result, key=lambda item: (item.visibility_weight, item.is_boosted, item.is_featured, item.created_at), reverse=True)


@public_router.get("/products", tags=["supplier-public"])
def public_list_products(
    category: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    cache_key = f"public_products:{category}:{product_type}:{search}:{limit}:{offset}"
    cached = _supplier_cache_get(cache_key)
    if cached is not None:
        return cached
    products = SupplierPublicService.list_all_products(db, category, product_type, search, limit, offset)
    result = []
    for p in products:
        from app.services.subscription_service import SubscriptionService
        supplier = p.supplier
        resp = SupplierProductResponse.model_validate(p)
        resp.supplier_name = supplier.business_name if supplier else None
        resp.supplier_rating = supplier.rating if supplier else None
        resp.supplier_verification = supplier.verification_status.value if supplier else None
        resp.supplier_subscription_plan = supplier.subscription_plan if supplier else "basic"
        resp.supplier_badges = SubscriptionService.get_badges(db, supplier=supplier) if supplier else []
        resp.visibility_weight = SubscriptionService.visibility_weight(db, supplier=supplier) if supplier else 100
        result.append(resp)
    payload = sorted(result, key=lambda item: (item.visibility_weight, item.is_boosted, item.is_featured, item.created_at), reverse=True)
    _supplier_cache_set(cache_key, payload, 90)
    return payload


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


@public_router.get("/orders", tags=["supplier-public"])
def public_get_my_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Buyer/farmer gets their supplier orders."""
    orders = SupplierOrderService.get_buyer_orders(db, user.id)
    return [SupplierOrderResponse.model_validate(o) for o in orders]


@public_router.post("/orders/{order_id}/confirm-receipt", tags=["supplier-public"])
def public_confirm_supplier_order_receipt(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Buyer confirms supplier order receipt and releases settlement if still pending."""
    order = SupplierOrderService.buyer_confirm_receipt(db, order_id, user.id)
    return {
        "message": "Receipt confirmed",
        "order_id": str(order.id),
        "status": order.status.value,
        "payment_status": order.payment_status.value,
    }


# ============================================================================
# SUPPLIER TRANSPORT (1 endpoint)
# ============================================================================

@router.post("/orders/{order_id}/transport", tags=["supplier-transport"])
def request_supplier_transport(
    order_id: uuid.UUID,
    pickup_address: str = Body(..., embed=True),
    pickup_latitude: Optional[float] = Body(None, embed=True),
    pickup_longitude: Optional[float] = Body(None, embed=True),
    pickup_contact_name: Optional[str] = Body(None, embed=True),
    pickup_contact_phone: Optional[str] = Body(None, embed=True),
    delivery_address: str = Body(..., embed=True),
    delivery_latitude: Optional[float] = Body(None, embed=True),
    delivery_longitude: Optional[float] = Body(None, embed=True),
    delivery_contact_name: Optional[str] = Body(None, embed=True),
    delivery_contact_phone: Optional[str] = Body(None, embed=True),
    cargo_weight_kg: float = Body(..., embed=True),
    cargo_volume_m3: Optional[float] = Body(None, embed=True),
    cargo_description: Optional[str] = Body(None, embed=True),
    preferred_vehicle_type: Optional[str] = Body("van", embed=True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Supplier requests platform transport for an order."""
    try:
        # Verify order belongs to supplier
        order = db.query(SupplierOrder).filter(
            SupplierOrder.id == order_id,
            SupplierOrder.supplier_id == user.id
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Import transport service
        from app.services.transport_rule_engine import TransportRuleEngine, TransportMode

        # Prepare transport data
        transport_data = {
            "distance_km": 0.0,
            "vehicle_type": preferred_vehicle_type or "van",
            "cargo_weight_kg": cargo_weight_kg,
        }

        # Apply transport rule
        rule_engine = TransportRuleEngine(db)
        result = rule_engine.apply_rules(
            order_id=order_id,
            requested_by="SUPPLIER",
            mode=TransportMode.PLATFORM_DELIVERY_SUPPLIER_REQUESTED,
            transport_request_data=transport_data,
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message or "Failed to process transport request")

        # Create transport request
        from app.models.transport import TransportRequest, TransportRequestStatus, TransportMode as DBTransportMode
        from app.models.transport import PaymentAllocation, AllocationType

        transport_request = TransportRequest(
            order_id=order_id,
            requested_by="SUPPLIER",
            mode=DBTransportMode.PLATFORM_DELIVERY_SUPPLIER_REQUESTED,
            pickup_address=pickup_address,
            pickup_latitude=pickup_latitude,
            pickup_longitude=pickup_longitude,
            pickup_contact_name=pickup_contact_name,
            pickup_contact_phone=pickup_contact_phone,
            delivery_address=delivery_address,
            delivery_latitude=delivery_latitude,
            delivery_longitude=delivery_longitude,
            delivery_contact_name=delivery_contact_name,
            delivery_contact_phone=delivery_contact_phone,
            cargo_weight_kg=cargo_weight_kg,
            cargo_volume_m3=cargo_volume_m3,
            cargo_description=cargo_description,
            preferred_vehicle_type=preferred_vehicle_type,
            status=TransportRequestStatus.PRICED,
            created_by=user.id,
        )
        db.add(transport_request)
        db.flush()

        # Create payment allocation
        for allocation in result.payment_allocations:
            payment_allocation = PaymentAllocation(
                order_id=order_id,
                transport_request_id=transport_request.id,
                allocation_type=AllocationType(allocation["allocation_type"]),
                payer=allocation["payer"],
                payee=allocation["payee"],
                amount=allocation["amount"],
                currency=allocation["currency"],
                payment_method=allocation["payment_method"],
            )
            db.add(payment_allocation)

        db.commit()

        return {
            "success": True,
            "transport_fee_payer": result.transport_fee_payer,
            "transport_fee": result.transport_fee,
            "driver_assignment": result.driver_assignment,
            "transport_request_id": str(transport_request.id),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supplier transport request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to request transport")


# ============================================================================
# SUPPLIER REVIEWS (5 endpoints)
# ============================================================================

@router.post("/reviews", response_model=SupplierReviewResponse, tags=["supplier-reviews"])
def create_review(
    data: SupplierReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Buyer creates a review for a supplier after order completion."""
    try:
        # Get supplier from order
        order = db.query(SupplierOrder).filter(SupplierOrder.id == data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        review = SupplierReviewService.create_review(db, user.id, order.supplier_id, data.model_dump())
        return SupplierReviewResponse.model_validate(review)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create review error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create review")


@router.get("/reviews/{supplier_id}", response_model=SupplierReviewListResponse, tags=["supplier-reviews"])
def get_supplier_reviews(
    supplier_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get all reviews for a supplier with statistics."""
    try:
        result = SupplierReviewService.get_reviews(db, supplier_id, limit, offset)
        return SupplierReviewListResponse(
            reviews=[SupplierReviewResponse.model_validate(r) for r in result["reviews"]],
            total=result["total"],
            average_rating=result["average_rating"],
            rating_distribution=result["rating_distribution"],
        )
    except Exception as e:
        logger.error(f"Get reviews error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reviews")


@router.put("/reviews/{review_id}/respond", response_model=SupplierReviewResponse, tags=["supplier-reviews"])
def respond_to_review(
    review_id: uuid.UUID,
    data: SupplierReviewUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Supplier responds to a review."""
    try:
        profile = _get_supplier_profile(db, user)
        review = SupplierReviewService.respond_to_review(db, profile.id, review_id, data.supplier_response)
        return SupplierReviewResponse.model_validate(review)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Respond to review error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to respond to review")


@router.post("/reviews/{review_id}/flag", response_model=SupplierReviewResponse, tags=["supplier-reviews"])
def flag_review(
    review_id: uuid.UUID,
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Admin flags a review for moderation."""
    try:
        review = SupplierReviewService.flag_review(db, review_id, notes)
        return SupplierReviewResponse.model_validate(review)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Flag review error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to flag review")


@router.post("/reviews/{review_id}/hide", response_model=SupplierReviewResponse, tags=["supplier-reviews"])
def hide_review(
    review_id: uuid.UUID,
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Admin hides a review."""
    try:
        review = SupplierReviewService.hide_review(db, review_id, notes)
        return SupplierReviewResponse.model_validate(review)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hide review error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to hide review")


# ============================================================================
# SUPPLIER SUBSCRIPTIONS (4 endpoints)
# ============================================================================

@router.get("/subscription", tags=["supplier-subscriptions"])
def get_subscription(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Get current supplier subscription details."""
    try:
        profile = _get_supplier_profile(db, user)
        return SupplierSubscriptionService.get_subscription(db, profile.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get subscription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription")


@router.post("/subscription", tags=["supplier-subscriptions"])
def set_subscription(
    supplier_id: uuid.UUID = Query(..., description="Supplier profile ID"),
    plan: str = Query(..., description="Subscription plan: basic, pro, enterprise"),
    billing_cycle: str = Query("monthly", description="Billing cycle: monthly, quarterly, yearly"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Admin sets a supplier's subscription plan."""
    try:
        return SupplierSubscriptionService.set_subscription(db, supplier_id, plan, billing_cycle)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set subscription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to set subscription")


@router.post("/subscription/upgrade", tags=["supplier-subscriptions"])
def upgrade_own_subscription(
    plan: str = Body(..., embed=True),
    billing_cycle: str = Body("monthly", embed=True),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    try:
        profile = _get_supplier_profile(db, user)
        return SupplierSubscriptionService.set_subscription(db, profile.id, plan, billing_cycle)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upgrade subscription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upgrade subscription")


@router.post("/subscription/cancel", tags=["supplier-subscriptions"])
def cancel_subscription(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Supplier cancels their subscription."""
    try:
        profile = _get_supplier_profile(db, user)
        return SupplierSubscriptionService.cancel_subscription(db, profile.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel subscription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.get("/subscription/feature-check/{feature}", tags=["supplier-subscriptions"])
def check_feature_entitlement(
    feature: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Check if supplier has access to a specific feature."""
    try:
        profile = _get_supplier_profile(db, user)
        has_access = SupplierSubscriptionService.check_feature_entitlement(db, profile.id, feature)
        return {"feature": feature, "has_access": has_access}
    except Exception as e:
        logger.error(f"Feature check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check feature entitlement")


# ============================================================================
# SUPPLIER LOGISTICS INTEGRATION (3 endpoints)
# ============================================================================

@router.post("/orders/{order_id}/logistics/create", tags=["supplier-logistics"])
def create_delivery_record(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Create a logistics delivery record for a supplier order."""
    try:
        profile = _get_supplier_profile(db, user)
        # Verify order belongs to supplier
        order = db.query(SupplierOrder).filter(
            SupplierOrder.id == order_id,
            SupplierOrder.supplier_id == profile.id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return SupplierLogisticsService.create_delivery_record(db, order_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create delivery record error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create delivery record")


@router.get("/orders/{order_id}/logistics/status", tags=["supplier-logistics"])
def get_delivery_status(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Get the logistics delivery status for a supplier order."""
    try:
        profile = _get_supplier_profile(db, user)
        # Verify order belongs to supplier
        order = db.query(SupplierOrder).filter(
            SupplierOrder.id == order_id,
            SupplierOrder.supplier_id == profile.id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return SupplierLogisticsService.get_delivery_status(db, order_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get delivery status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve delivery status")


@router.post("/orders/{order_id}/logistics/sync", tags=["supplier-logistics"])
def sync_order_status(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Sync supplier order status with logistics delivery status."""
    try:
        profile = _get_supplier_profile(db, user)
        # Verify order belongs to supplier
        order = db.query(SupplierOrder).filter(
            SupplierOrder.id == order_id,
            SupplierOrder.supplier_id == profile.id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return SupplierLogisticsService.sync_order_status(db, order_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync order status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to sync order status")


# ============================================================================
# SUPPLIER PAYOUT PROCESSING (3 endpoints)
# ============================================================================

@router.post("/wallet/payouts/process", tags=["supplier-payouts"])
def process_pending_payouts(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Process all pending withdrawal requests (admin/cron job)."""
    try:
        return SupplierPayoutService.process_pending_payouts(db)
    except Exception as e:
        logger.error(f"Process payouts error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process payouts")


@router.get("/wallet/payouts/history", tags=["supplier-payouts"])
def get_payout_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Get payout history for a supplier."""
    try:
        profile = _get_supplier_profile(db, user)
        return SupplierPayoutService.get_payout_history(db, profile.id, limit, offset)
    except Exception as e:
        logger.error(f"Get payout history error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payout history")


@router.get("/wallet/payouts/tax-report", tags=["supplier-payouts"])
def get_tax_report(
    year: int = Query(..., ge=2020, le=2030),
    month: Optional[int] = Query(None, ge=1, le=12),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Generate tax report for supplier earnings."""
    try:
        profile = _get_supplier_profile(db, user)
        return SupplierPayoutService.get_tax_report(db, profile.id, year, month)
    except Exception as e:
        logger.error(f"Get tax report error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate tax report")


# ============================================================================
# SUPPLIER DISCOUNTS/PROMOTIONS (6 endpoints)
# ============================================================================

@router.post("/discounts", response_model=SupplierDiscountResponse, tags=["supplier-discounts"])
def create_discount(
    data: SupplierDiscountCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Create a new discount/promotion code."""
    try:
        profile = _get_supplier_profile(db, user)
        discount = SupplierDiscountService.create_discount(db, profile.id, data.model_dump())
        return SupplierDiscountResponse.model_validate(discount)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create discount error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create discount")


@router.get("/discounts", tags=["supplier-discounts"])
def list_discounts(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """List all discounts for a supplier."""
    try:
        profile = _get_supplier_profile(db, user)
        discounts = SupplierDiscountService.list_discounts(db, profile.id, active_only)
        return [SupplierDiscountResponse.model_validate(d) for d in discounts]
    except Exception as e:
        logger.error(f"List discounts error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discounts")


@router.get("/discounts/{discount_id}", response_model=SupplierDiscountResponse, tags=["supplier-discounts"])
def get_discount(
    discount_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Get a specific discount."""
    try:
        profile = _get_supplier_profile(db, user)
        discount = SupplierDiscountService.get_discount(db, discount_id, profile.id)
        return SupplierDiscountResponse.model_validate(discount)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get discount error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discount")


@router.put("/discounts/{discount_id}", response_model=SupplierDiscountResponse, tags=["supplier-discounts"])
def update_discount(
    discount_id: uuid.UUID,
    data: SupplierDiscountUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Update a discount."""
    try:
        profile = _get_supplier_profile(db, user)
        discount = SupplierDiscountService.update_discount(db, discount_id, profile.id, data.model_dump(exclude_none=True))
        return SupplierDiscountResponse.model_validate(discount)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update discount error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update discount")


@router.delete("/discounts/{discount_id}", tags=["supplier-discounts"])
def delete_discount(
    discount_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPPLIER)),
):
    """Delete a discount."""
    try:
        profile = _get_supplier_profile(db, user)
        return SupplierDiscountService.delete_discount(db, discount_id, profile.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete discount error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete discount")


@public_router.post("/discounts/validate", tags=["supplier-discounts"])
def validate_discount(
    data: DiscountValidationRequest,
    db: Session = Depends(get_db),
):
    """Validate a discount code (public endpoint)."""
    try:
        return SupplierDiscountService.validate_discount(db, data.code, data.order_total, data.product_ids)
    except Exception as e:
        logger.error(f"Validate discount error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate discount")


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
