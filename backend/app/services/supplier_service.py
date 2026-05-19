"""
ZimAgriTrust – Supplier Module Service
Handles supplier registration, products, orders, wallet, and analytics.
"""
from __future__ import annotations

import random
import string
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func as sa_func, desc, and_, extract
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole, UserStatus
from app.models.supplier import (
    SupplierProfile,
    SupplierDocument,
    SupplierProduct,
    SupplierOrder,
    SupplierOrderItem,
    SupplierStockHistory,
    SupplierWalletTransaction,
    SupplierBusinessType,
    SupplierVerificationStatus,
    SupplierProductType,
    SupplierProductStatus,
    SupplierOrderStatus,
    SupplierPaymentStatus,
    SupplierWalletTxnType,
)


PLATFORM_FEE_PERCENT = 0.03  # 3%
BOOST_FEE_INPUT = 5.0
BOOST_FEE_MACHINERY = 10.0
WITHDRAWAL_MIN = 50.0
WITHDRAWAL_FEE_PERCENT = 0.01
WITHDRAWAL_FEE_CAP = 10.0


def _generate_sku(prefix: str = "SP") -> str:
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}-{rand}"


def _generate_order_number() -> str:
    rand = "".join(random.choices(string.digits, k=8))
    return f"SO-{rand}"


# ============================================================================
# REGISTRATION
# ============================================================================

class SupplierRegistrationService:

    @staticmethod
    def apply(db: Session, data: dict) -> dict:
        """Create a new supplier application. Creates User + SupplierProfile."""
        # Check phone uniqueness
        existing = db.query(User).filter(User.phone_number == data["phone"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="Phone number already registered")

        # Create user account
        password_hash = get_password_hash(data["password"])
        user = User(
            full_name=data["full_name"],
            phone_number=data["phone"],
            email=data.get("email"),
            password_hash=password_hash,
            ussd_pin_hash=password_hash,
            role=UserRole.SUPPLIER,
            status=UserStatus.PENDING_VERIFICATION,
            trust_score=60,
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Create supplier profile
        btype = None
        try:
            btype = SupplierBusinessType(data.get("business_type", ""))
        except ValueError:
            pass

        profile = SupplierProfile(
            user_id=user.id,
            business_name=data["business_name"],
            registration_number=data.get("registration_number"),
            tax_id=data.get("tax_id"),
            business_type=btype,
            years_in_operation=data.get("years_in_operation"),
            physical_address=data.get("physical_address"),
            contact_person=data.get("contact_person", data["full_name"]),
            phone=data["phone"],
            email=data.get("email"),
            product_categories=data.get("product_categories"),
            verification_status=SupplierVerificationStatus.PENDING,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return {
            "message": "Supplier application submitted successfully",
            "supplier_id": str(profile.id),
            "user_id": str(user.id),
            "status": profile.verification_status.value,
        }

    @staticmethod
    def upload_documents(db: Session, supplier_id: uuid.UUID, documents: list[dict]) -> dict:
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")

        for doc in documents:
            sd = SupplierDocument(
                supplier_id=supplier_id,
                document_type=doc["document_type"],
                document_url=doc["document_url"],
                document_name=doc.get("document_name"),
            )
            db.add(sd)

        if profile.verification_status == SupplierVerificationStatus.PENDING:
            profile.verification_status = SupplierVerificationStatus.UNDER_REVIEW
        db.commit()
        return {"message": f"{len(documents)} document(s) uploaded", "status": profile.verification_status.value}

    @staticmethod
    def get_application_status(db: Session, user_id: uuid.UUID) -> dict:
        profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="No supplier application found")
        doc_count = db.query(SupplierDocument).filter(SupplierDocument.supplier_id == profile.id).count()
        return {
            "supplier_id": str(profile.id),
            "business_name": profile.business_name,
            "verification_status": profile.verification_status.value,
            "verification_notes": profile.verification_notes,
            "submitted_documents": doc_count,
            "created_at": profile.created_at,
        }


# ============================================================================
# PROFILE
# ============================================================================

class SupplierProfileService:

    @staticmethod
    def get_profile(db: Session, user_id: uuid.UUID) -> SupplierProfile:
        profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier profile not found")
        return profile

    @staticmethod
    def update_profile(db: Session, user_id: uuid.UUID, data: dict) -> SupplierProfile:
        profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier profile not found")
        for key, val in data.items():
            if val is not None and hasattr(profile, key):
                setattr(profile, key, val)
        db.commit()
        db.refresh(profile)
        return profile


# ============================================================================
# PRODUCT MANAGEMENT
# ============================================================================

class SupplierProductService:

    @staticmethod
    def create_product(db: Session, supplier_id: uuid.UUID, data: dict) -> SupplierProduct:
        product = SupplierProduct(
            supplier_id=supplier_id,
            sku=_generate_sku(),
            product_type=SupplierProductType(data["product_type"]),
            name=data["name"],
            description=data.get("description"),
            price=data["price"],
            currency=data.get("currency", "USD"),
            quantity_available=data.get("quantity_available", 0),
            unit_type=data.get("unit_type", "piece"),
            min_stock_level=data.get("min_stock_level", 5),
            registration_number=data.get("registration_number"),
            manufacturer=data.get("manufacturer"),
            safety_data_sheet_url=data.get("safety_data_sheet_url"),
            delivery_included=data.get("delivery_included", False),
            manual_url=data.get("manual_url"),
            photo_urls=data.get("photo_urls"),
            status=SupplierProductStatus(data.get("status", "draft")),
        )
        # Set category fields
        if data.get("input_category"):
            from app.models.supplier import InputCategory
            try:
                product.input_category = InputCategory(data["input_category"])
            except ValueError:
                pass
        if data.get("machinery_category"):
            from app.models.supplier import MachineryCategory
            try:
                product.machinery_category = MachineryCategory(data["machinery_category"])
            except ValueError:
                pass
        if data.get("expiry_date"):
            product.expiry_date = data["expiry_date"]
        if data.get("condition"):
            from app.models.supplier import ProductCondition
            try:
                product.condition = ProductCondition(data["condition"])
            except ValueError:
                pass
        if data.get("warranty_months"):
            product.warranty_months = data["warranty_months"]

        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def list_products(db: Session, supplier_id: uuid.UUID, status_filter: Optional[str] = None) -> list[SupplierProduct]:
        q = db.query(SupplierProduct).filter(SupplierProduct.supplier_id == supplier_id)
        if status_filter:
            try:
                q = q.filter(SupplierProduct.status == SupplierProductStatus(status_filter))
            except ValueError:
                pass
        return q.order_by(desc(SupplierProduct.created_at)).all()

    @staticmethod
    def get_product(db: Session, product_id: uuid.UUID, supplier_id: Optional[uuid.UUID] = None) -> SupplierProduct:
        q = db.query(SupplierProduct).filter(SupplierProduct.id == product_id)
        if supplier_id:
            q = q.filter(SupplierProduct.supplier_id == supplier_id)
        product = q.first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    @staticmethod
    def update_product(db: Session, product_id: uuid.UUID, supplier_id: uuid.UUID, data: dict) -> SupplierProduct:
        product = db.query(SupplierProduct).filter(
            SupplierProduct.id == product_id,
            SupplierProduct.supplier_id == supplier_id,
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        for key, val in data.items():
            if val is not None and hasattr(product, key):
                setattr(product, key, val)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete_product(db: Session, product_id: uuid.UUID, supplier_id: uuid.UUID) -> dict:
        product = db.query(SupplierProduct).filter(
            SupplierProduct.id == product_id,
            SupplierProduct.supplier_id == supplier_id,
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        db.delete(product)
        db.commit()
        return {"message": "Product deleted"}

    @staticmethod
    def boost_product(db: Session, product_id: uuid.UUID, supplier_id: uuid.UUID, duration_days: int = 7) -> SupplierProduct:
        product = db.query(SupplierProduct).filter(
            SupplierProduct.id == product_id,
            SupplierProduct.supplier_id == supplier_id,
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        fee = BOOST_FEE_INPUT if product.product_type == SupplierProductType.INPUT else BOOST_FEE_MACHINERY
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if profile.available_balance < fee:
            raise HTTPException(status_code=400, detail=f"Insufficient balance. Boost fee is ${fee:.2f}")

        profile.available_balance -= fee
        product.is_boosted = True
        product.boost_fee = fee
        product.boosted_until = datetime.now(timezone.utc) + timedelta(days=duration_days)

        txn = SupplierWalletTransaction(
            supplier_id=supplier_id,
            txn_type=SupplierWalletTxnType.BOOST_FEE,
            amount=fee,
            fee=0,
            net_amount=-fee,
            description=f"Boost fee for product: {product.name}",
        )
        db.add(txn)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def update_stock(db: Session, product_id: uuid.UUID, supplier_id: uuid.UUID, new_qty: int, notes: Optional[str] = None) -> SupplierProduct:
        product = db.query(SupplierProduct).filter(
            SupplierProduct.id == product_id,
            SupplierProduct.supplier_id == supplier_id,
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        old_qty = product.quantity_available
        change = new_qty - old_qty
        product.quantity_available = new_qty
        if new_qty == 0:
            product.status = SupplierProductStatus.OUT_OF_STOCK
        elif product.status == SupplierProductStatus.OUT_OF_STOCK and new_qty > 0:
            product.status = SupplierProductStatus.ACTIVE

        history = SupplierStockHistory(
            product_id=product_id,
            change_type="restock" if change > 0 else "adjustment",
            quantity_change=change,
            quantity_before=old_qty,
            quantity_after=new_qty,
            notes=notes,
        )
        db.add(history)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_low_stock_alerts(db: Session, supplier_id: uuid.UUID) -> list[SupplierProduct]:
        return db.query(SupplierProduct).filter(
            SupplierProduct.supplier_id == supplier_id,
            SupplierProduct.quantity_available <= SupplierProduct.min_stock_level,
            SupplierProduct.status != SupplierProductStatus.DRAFT,
        ).all()

    @staticmethod
    def get_inventory(db: Session, supplier_id: uuid.UUID) -> list[SupplierProduct]:
        return db.query(SupplierProduct).filter(
            SupplierProduct.supplier_id == supplier_id,
        ).order_by(SupplierProduct.name).all()

    @staticmethod
    def bulk_price_update(db: Session, supplier_id: uuid.UUID, updates: list[dict]) -> dict:
        updated = 0
        for item in updates:
            pid = item.get("product_id")
            new_price = item.get("new_price")
            if not pid or new_price is None:
                continue
            product = db.query(SupplierProduct).filter(
                SupplierProduct.id == uuid.UUID(pid),
                SupplierProduct.supplier_id == supplier_id,
            ).first()
            if product:
                product.price = new_price
                updated += 1
        db.commit()
        return {"message": f"{updated} product(s) updated"}


# ============================================================================
# ORDER MANAGEMENT
# ============================================================================

class SupplierOrderService:

    @staticmethod
    def create_order_from_buyer(db: Session, buyer_id: uuid.UUID, data: dict) -> SupplierOrder:
        """Called when a buyer places an order for supplier products."""
        items_data = data.get("items", [])
        if not items_data:
            raise HTTPException(status_code=400, detail="No items in order")

        # Group items by supplier
        product_ids = [uuid.UUID(i["product_id"]) for i in items_data]
        products = db.query(SupplierProduct).filter(SupplierProduct.id.in_(product_ids)).all()
        product_map = {str(p.id): p for p in products}

        # Validate all products exist and have stock
        for item in items_data:
            pid = str(item["product_id"])
            p = product_map.get(pid)
            if not p:
                raise HTTPException(status_code=404, detail=f"Product {pid} not found")
            if p.status != SupplierProductStatus.ACTIVE:
                raise HTTPException(status_code=400, detail=f"Product '{p.name}' is not available")
            if p.quantity_available < item["quantity"]:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for '{p.name}'")

        # Group by supplier to create separate orders per supplier
        supplier_groups: Dict[uuid.UUID, list] = {}
        for item in items_data:
            p = product_map[str(item["product_id"])]
            sg = supplier_groups.setdefault(p.supplier_id, [])
            sg.append({"product": p, "quantity": item["quantity"]})

        orders_created = []
        for supplier_id, group_items in supplier_groups.items():
            subtotal = sum(gi["product"].price * gi["quantity"] for gi in group_items)
            platform_fee = round(subtotal * PLATFORM_FEE_PERCENT, 2)
            total = round(subtotal + platform_fee, 2)

            order = SupplierOrder(
                order_number=_generate_order_number(),
                supplier_id=supplier_id,
                buyer_id=buyer_id,
                subtotal=subtotal,
                platform_fee=platform_fee,
                total_amount=total,
                delivery_address=data.get("delivery_address"),
                delivery_phone=data.get("delivery_phone"),
                shipping_method=data.get("shipping_method"),
                buyer_notes=data.get("buyer_notes"),
                promo_code=data.get("promo_code"),
                status=SupplierOrderStatus.NEW,
                payment_status=SupplierPaymentStatus.ESCROW,
            )
            db.add(order)
            db.flush()

            for gi in group_items:
                p = gi["product"]
                qty = gi["quantity"]
                oi = SupplierOrderItem(
                    order_id=order.id,
                    product_id=p.id,
                    product_name=p.name,
                    quantity=qty,
                    unit_price=p.price,
                    total_price=round(p.price * qty, 2),
                )
                db.add(oi)

                # Deduct stock
                old_qty = p.quantity_available
                p.quantity_available = max(0, p.quantity_available - qty)
                if p.quantity_available == 0:
                    p.status = SupplierProductStatus.OUT_OF_STOCK
                p.order_count += qty

                sh = SupplierStockHistory(
                    product_id=p.id,
                    change_type="sale",
                    quantity_change=-qty,
                    quantity_before=old_qty,
                    quantity_after=p.quantity_available,
                    reference_id=str(order.id),
                )
                db.add(sh)

            orders_created.append(order)

        db.commit()

        if len(orders_created) == 1:
            db.refresh(orders_created[0])
            return orders_created[0]

        return orders_created[0]  # Return first order, caller can handle multiple

    @staticmethod
    def list_orders(db: Session, supplier_id: uuid.UUID, status_filter: Optional[str] = None) -> list[SupplierOrder]:
        q = db.query(SupplierOrder).filter(SupplierOrder.supplier_id == supplier_id)
        if status_filter:
            try:
                q = q.filter(SupplierOrder.status == SupplierOrderStatus(status_filter))
            except ValueError:
                pass
        return q.options(joinedload(SupplierOrder.items)).order_by(desc(SupplierOrder.created_at)).all()

    @staticmethod
    def get_order(db: Session, order_id: uuid.UUID, supplier_id: uuid.UUID) -> SupplierOrder:
        order = db.query(SupplierOrder).options(
            joinedload(SupplierOrder.items),
            joinedload(SupplierOrder.buyer),
        ).filter(
            SupplierOrder.id == order_id,
            SupplierOrder.supplier_id == supplier_id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    @staticmethod
    def confirm_order(db: Session, order_id: uuid.UUID, supplier_id: uuid.UUID) -> SupplierOrder:
        order = db.query(SupplierOrder).filter(
            SupplierOrder.id == order_id,
            SupplierOrder.supplier_id == supplier_id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status != SupplierOrderStatus.NEW:
            raise HTTPException(status_code=400, detail=f"Cannot confirm order in '{order.status.value}' status")
        order.status = SupplierOrderStatus.CONFIRMED
        order.confirmed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def ship_order(db: Session, order_id: uuid.UUID, supplier_id: uuid.UUID, tracking: Optional[str] = None, method: Optional[str] = None) -> SupplierOrder:
        order = db.query(SupplierOrder).filter(
            SupplierOrder.id == order_id,
            SupplierOrder.supplier_id == supplier_id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status not in (SupplierOrderStatus.CONFIRMED, SupplierOrderStatus.PROCESSING):
            raise HTTPException(status_code=400, detail=f"Cannot ship order in '{order.status.value}' status")
        order.status = SupplierOrderStatus.SHIPPED
        order.shipped_at = datetime.now(timezone.utc)
        if tracking:
            order.tracking_number = tracking
        if method:
            order.shipping_method = method
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def cancel_order(db: Session, order_id: uuid.UUID, supplier_id: uuid.UUID, reason: str) -> SupplierOrder:
        order = db.query(SupplierOrder).filter(
            SupplierOrder.id == order_id,
            SupplierOrder.supplier_id == supplier_id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status in (SupplierOrderStatus.DELIVERED, SupplierOrderStatus.CANCELLED):
            raise HTTPException(status_code=400, detail="Cannot cancel this order")

        order.status = SupplierOrderStatus.CANCELLED
        order.cancel_reason = reason

        # Restore stock
        items = db.query(SupplierOrderItem).filter(SupplierOrderItem.order_id == order_id).all()
        for item in items:
            product = db.query(SupplierProduct).filter(SupplierProduct.id == item.product_id).first()
            if product:
                old_qty = product.quantity_available
                product.quantity_available += item.quantity
                if product.status == SupplierProductStatus.OUT_OF_STOCK:
                    product.status = SupplierProductStatus.ACTIVE
                sh = SupplierStockHistory(
                    product_id=product.id,
                    change_type="adjustment",
                    quantity_change=item.quantity,
                    quantity_before=old_qty,
                    quantity_after=product.quantity_available,
                    reference_id=str(order.id),
                    notes=f"Cancelled order: {reason}",
                )
                db.add(sh)

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def add_tracking(db: Session, order_id: uuid.UUID, supplier_id: uuid.UUID, tracking_number: str, method: Optional[str] = None) -> SupplierOrder:
        order = db.query(SupplierOrder).filter(
            SupplierOrder.id == order_id,
            SupplierOrder.supplier_id == supplier_id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        order.tracking_number = tracking_number
        if method:
            order.shipping_method = method
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def mark_delivered(db: Session, order_id: uuid.UUID, supplier_id: uuid.UUID) -> SupplierOrder:
        """Release payment to supplier on delivery confirmation."""
        order = db.query(SupplierOrder).filter(
            SupplierOrder.id == order_id,
            SupplierOrder.supplier_id == supplier_id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status != SupplierOrderStatus.SHIPPED:
            raise HTTPException(status_code=400, detail="Order must be shipped before delivery")

        order.status = SupplierOrderStatus.DELIVERED
        order.delivered_at = datetime.now(timezone.utc)
        order.payment_status = SupplierPaymentStatus.PAID

        # Credit supplier wallet
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        net = order.subtotal  # platform fee already separated
        profile.available_balance += net
        profile.lifetime_earnings += net
        profile.total_sales += 1
        profile.total_revenue += order.total_amount

        txn = SupplierWalletTransaction(
            supplier_id=supplier_id,
            order_id=order.id,
            txn_type=SupplierWalletTxnType.SALE,
            amount=order.subtotal,
            fee=order.platform_fee,
            net_amount=net,
            description=f"Payment for order {order.order_number}",
        )
        db.add(txn)
        db.commit()
        db.refresh(order)
        return order


# ============================================================================
# WALLET
# ============================================================================

class SupplierWalletService:

    @staticmethod
    def get_wallet(db: Session, supplier_id: uuid.UUID) -> dict:
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return {
            "available_balance": profile.available_balance,
            "pending_balance": profile.pending_balance,
            "lifetime_earnings": profile.lifetime_earnings,
            "currency": "USD",
        }

    @staticmethod
    def get_transactions(db: Session, supplier_id: uuid.UUID, limit: int = 50) -> list[SupplierWalletTransaction]:
        return db.query(SupplierWalletTransaction).filter(
            SupplierWalletTransaction.supplier_id == supplier_id,
        ).order_by(desc(SupplierWalletTransaction.created_at)).limit(limit).all()

    @staticmethod
    def withdraw(db: Session, supplier_id: uuid.UUID, amount: float, method: str, account_details: Optional[str] = None) -> dict:
        if amount < WITHDRAWAL_MIN:
            raise HTTPException(status_code=400, detail=f"Minimum withdrawal is ${WITHDRAWAL_MIN}")

        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")
        if profile.available_balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        fee = min(round(amount * WITHDRAWAL_FEE_PERCENT, 2), WITHDRAWAL_FEE_CAP)
        net = round(amount - fee, 2)

        profile.available_balance -= amount
        txn = SupplierWalletTransaction(
            supplier_id=supplier_id,
            txn_type=SupplierWalletTxnType.WITHDRAWAL,
            amount=amount,
            fee=fee,
            net_amount=net,
            withdrawal_method=method,
            reference=account_details,
            status="pending",
            description=f"Withdrawal via {method}",
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)
        return {
            "message": "Withdrawal request submitted",
            "amount": amount,
            "fee": fee,
            "net_amount": net,
            "method": method,
            "status": "pending",
            "transaction_id": str(txn.id),
        }

    @staticmethod
    def get_earnings(db: Session, supplier_id: uuid.UUID) -> dict:
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")

        total_withdrawn = db.query(sa_func.coalesce(sa_func.sum(SupplierWalletTransaction.amount), 0)).filter(
            SupplierWalletTransaction.supplier_id == supplier_id,
            SupplierWalletTransaction.txn_type == SupplierWalletTxnType.WITHDRAWAL,
        ).scalar()

        return {
            "lifetime_earnings": profile.lifetime_earnings,
            "available_balance": profile.available_balance,
            "pending_balance": profile.pending_balance,
            "total_withdrawn": float(total_withdrawn),
            "total_sales": profile.total_sales,
            "total_revenue": profile.total_revenue,
        }

    @staticmethod
    def get_statement(db: Session, supplier_id: uuid.UUID, month: Optional[int] = None, year: Optional[int] = None) -> list[SupplierWalletTransaction]:
        q = db.query(SupplierWalletTransaction).filter(SupplierWalletTransaction.supplier_id == supplier_id)
        if month and year:
            q = q.filter(
                extract("month", SupplierWalletTransaction.created_at) == month,
                extract("year", SupplierWalletTransaction.created_at) == year,
            )
        return q.order_by(desc(SupplierWalletTransaction.created_at)).all()


# ============================================================================
# ANALYTICS
# ============================================================================

class SupplierAnalyticsService:

    @staticmethod
    def sales_analytics(db: Session, supplier_id: uuid.UUID) -> dict:
        orders = db.query(SupplierOrder).filter(
            SupplierOrder.supplier_id == supplier_id,
            SupplierOrder.status == SupplierOrderStatus.DELIVERED,
        ).all()

        total_revenue = sum(o.total_amount for o in orders)
        total_orders = len(orders)
        avg_order_value = round(total_revenue / total_orders, 2) if total_orders else 0

        # Revenue by month (last 12 months)
        revenue_by_month = []
        now = datetime.now(timezone.utc)
        for i in range(11, -1, -1):
            d = now - timedelta(days=30 * i)
            month_orders = [o for o in orders if o.delivered_at and o.delivered_at.month == d.month and o.delivered_at.year == d.year]
            revenue_by_month.append({
                "month": d.strftime("%Y-%m"),
                "revenue": sum(o.total_amount for o in month_orders),
                "orders": len(month_orders),
            })

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "avg_order_value": avg_order_value,
            "revenue_by_month": revenue_by_month,
        }

    @staticmethod
    def bestsellers(db: Session, supplier_id: uuid.UUID, limit: int = 10) -> list[dict]:
        results = db.query(
            SupplierOrderItem.product_id,
            SupplierOrderItem.product_name,
            sa_func.sum(SupplierOrderItem.quantity).label("total_sold"),
            sa_func.sum(SupplierOrderItem.total_price).label("total_revenue"),
        ).join(SupplierOrder).filter(
            SupplierOrder.supplier_id == supplier_id,
            SupplierOrder.status == SupplierOrderStatus.DELIVERED,
        ).group_by(
            SupplierOrderItem.product_id,
            SupplierOrderItem.product_name,
        ).order_by(desc("total_sold")).limit(limit).all()

        return [
            {
                "product_id": str(r.product_id),
                "product_name": r.product_name,
                "total_sold": int(r.total_sold),
                "total_revenue": float(r.total_revenue),
            }
            for r in results
        ]

    @staticmethod
    def inventory_analytics(db: Session, supplier_id: uuid.UUID) -> dict:
        products = db.query(SupplierProduct).filter(SupplierProduct.supplier_id == supplier_id).all()
        total = len(products)
        in_stock = sum(1 for p in products if p.quantity_available > p.min_stock_level)
        low = sum(1 for p in products if 0 < p.quantity_available <= p.min_stock_level)
        oos = sum(1 for p in products if p.quantity_available == 0)
        total_value = sum(p.price * p.quantity_available for p in products)
        return {
            "total_products": total,
            "in_stock": in_stock,
            "low_stock": low,
            "out_of_stock": oos,
            "total_value": round(total_value, 2),
        }

    @staticmethod
    def reports(db: Session, supplier_id: uuid.UUID) -> dict:
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        return {
            "business_name": profile.business_name if profile else "",
            "total_sales": profile.total_sales if profile else 0,
            "total_revenue": profile.total_revenue if profile else 0,
            "rating": profile.rating if profile else 0,
            "trust_score": profile.trust_score if profile else 0,
        }


# ============================================================================
# ADMIN – SUPPLIER MANAGEMENT
# ============================================================================

class SupplierAdminService:

    @staticmethod
    def get_pending(db: Session) -> list[SupplierProfile]:
        return db.query(SupplierProfile).filter(
            SupplierProfile.verification_status.in_([
                SupplierVerificationStatus.PENDING,
                SupplierVerificationStatus.UNDER_REVIEW,
            ])
        ).order_by(SupplierProfile.created_at).all()

    @staticmethod
    def get_supplier_detail(db: Session, supplier_id: uuid.UUID) -> SupplierProfile:
        profile = db.query(SupplierProfile).options(
            joinedload(SupplierProfile.documents),
            joinedload(SupplierProfile.user),
        ).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return profile

    @staticmethod
    def approve(db: Session, supplier_id: uuid.UUID, admin_id: uuid.UUID, notes: Optional[str] = None) -> dict:
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")

        profile.verification_status = SupplierVerificationStatus.APPROVED
        profile.verification_notes = notes
        profile.verified_by = admin_id
        profile.verified_at = datetime.now(timezone.utc)

        # Activate user account
        user = db.query(User).filter(User.id == profile.user_id).first()
        if user:
            user.status = UserStatus.ACTIVE
            user.trust_score = 60

        db.commit()
        return {"message": "Supplier approved", "supplier_id": str(supplier_id)}

    @staticmethod
    def reject(db: Session, supplier_id: uuid.UUID, admin_id: uuid.UUID, notes: Optional[str] = None) -> dict:
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")

        profile.verification_status = SupplierVerificationStatus.REJECTED
        profile.verification_notes = notes
        profile.verified_by = admin_id
        profile.verified_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": "Supplier rejected", "supplier_id": str(supplier_id)}

    @staticmethod
    def suspend(db: Session, supplier_id: uuid.UUID, admin_id: uuid.UUID, notes: Optional[str] = None) -> dict:
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")

        profile.verification_status = SupplierVerificationStatus.SUSPENDED
        profile.verification_notes = notes
        profile.is_active = False

        user = db.query(User).filter(User.id == profile.user_id).first()
        if user:
            user.is_suspended = True

        db.commit()
        return {"message": "Supplier suspended", "supplier_id": str(supplier_id)}

    @staticmethod
    def get_documents(db: Session, supplier_id: uuid.UUID) -> list[SupplierDocument]:
        return db.query(SupplierDocument).filter(SupplierDocument.supplier_id == supplier_id).all()


# ============================================================================
# PUBLIC – BUYER FACING
# ============================================================================

class SupplierPublicService:

    @staticmethod
    def list_suppliers(db: Session, limit: int = 50, offset: int = 0) -> list[SupplierProfile]:
        return db.query(SupplierProfile).filter(
            SupplierProfile.verification_status == SupplierVerificationStatus.APPROVED,
            SupplierProfile.is_active == True,
        ).order_by(desc(SupplierProfile.rating)).offset(offset).limit(limit).all()

    @staticmethod
    def get_supplier_products(db: Session, supplier_id: uuid.UUID) -> list[SupplierProduct]:
        return db.query(SupplierProduct).filter(
            SupplierProduct.supplier_id == supplier_id,
            SupplierProduct.status == SupplierProductStatus.ACTIVE,
        ).order_by(desc(SupplierProduct.is_boosted), desc(SupplierProduct.created_at)).all()

    @staticmethod
    def list_all_products(db: Session, category: Optional[str] = None, product_type: Optional[str] = None, search: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[SupplierProduct]:
        q = db.query(SupplierProduct).join(SupplierProfile).filter(
            SupplierProduct.status == SupplierProductStatus.ACTIVE,
            SupplierProfile.verification_status == SupplierVerificationStatus.APPROVED,
            SupplierProfile.is_active == True,
        )
        if product_type:
            try:
                q = q.filter(SupplierProduct.product_type == SupplierProductType(product_type))
            except ValueError:
                pass
        if category:
            q = q.filter(
                (SupplierProduct.input_category == category) | (SupplierProduct.machinery_category == category)
            )
        if search:
            q = q.filter(SupplierProduct.name.ilike(f"%{search}%"))

        return q.order_by(desc(SupplierProduct.is_boosted), desc(SupplierProduct.is_featured), desc(SupplierProduct.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def get_product_detail(db: Session, product_id: uuid.UUID) -> dict:
        product = db.query(SupplierProduct).options(
            joinedload(SupplierProduct.supplier),
        ).filter(
            SupplierProduct.id == product_id,
            SupplierProduct.status == SupplierProductStatus.ACTIVE,
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        product.view_count += 1
        db.commit()

        return {
            "product": product,
            "supplier": {
                "id": str(product.supplier.id),
                "business_name": product.supplier.business_name,
                "rating": product.supplier.rating,
                "trust_score": product.supplier.trust_score,
                "verification_status": product.supplier.verification_status.value,
                "logo_url": product.supplier.logo_url,
            },
        }
