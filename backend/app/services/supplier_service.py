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
from sqlalchemy import func as sa_func, desc, and_, extract, String
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
    SupplierCSVImport,
    SupplierReview,
    SupplierDiscount,
    SupplierBusinessType,
    SupplierVerificationStatus,
    SupplierProductType,
    SupplierProductStatus,
    SupplierOrderStatus,
    SupplierPaymentStatus,
    SupplierWalletTxnType,
    can_transition_supplier_order_status,
)
from app.services.escrow_account_service import EscrowAccountService
from app.services.ledger_service import LedgerService
from app.services.wallet_service import WalletService


PLATFORM_FEE_PERCENT = 0.08
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
    def _require_operational_supplier(profile: SupplierProfile) -> None:
        if profile.verification_status != SupplierVerificationStatus.APPROVED:
            raise HTTPException(
                status_code=403,
                detail="Supplier must be approved before performing commerce operations",
            )

    @staticmethod
    def create_product(db: Session, supplier_id: uuid.UUID, data: dict) -> SupplierProduct:
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")
        SupplierProductService._require_operational_supplier(profile)
        required_fields = ["name", "price", "product_type"]
        missing = [field for field in required_fields if data.get(field) in (None, "")]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required product fields: {', '.join(missing)}",
            )
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

    @staticmethod
    def bulk_import_from_csv(db: Session, supplier_id: uuid.UUID, csv_data: str, file_name: str, file_size: int) -> dict:
        """
        Import products from CSV data.
        CSV format: product_type,name,description,price,quantity,unit_type,category,brand,manufacturer
        """
        import csv
        import io
        import json

        # Create import record
        import_record = SupplierCSVImport(
            supplier_id=supplier_id,
            file_name=file_name,
            file_size=file_size,
            status="processing",
        )
        db.add(import_record)
        db.commit()
        db.refresh(import_record)

        # Parse CSV
        f = io.StringIO(csv_data)
        reader = csv.DictReader(f)
        rows = list(reader)

        errors = []
        successful = 0
        created_products = []

        try:
            for idx, row in enumerate(rows, start=2):  # Start at 2 (header is row 1)
                try:
                    # Validate required fields
                    if not row.get("name") or not row.get("price") or not row.get("quantity"):
                        errors.append({
                            "row_number": idx,
                            "field": "required",
                            "error": "Missing required field (name, price, or quantity)",
                            "value": str(row)
                        })
                        continue

                    # Validate product type
                    product_type = row.get("product_type", "input").lower()
                    if product_type not in ["input", "machinery"]:
                        errors.append({
                            "row_number": idx,
                            "field": "product_type",
                            "error": "Invalid product type. Must be 'input' or 'machinery'",
                            "value": product_type
                        })
                        continue

                    # Create product
                    product = SupplierProduct(
                        supplier_id=supplier_id,
                        sku=_generate_sku(),
                        product_type=SupplierProductType(product_type),
                        name=row.get("name", "").strip(),
                        description=row.get("description", "").strip(),
                        price=float(row.get("price", 0)),
                        currency=(row.get("currency") or "USD").strip().upper(),
                        quantity_available=int(row.get("quantity", 0)),
                        unit_type=row.get("unit_type", "piece").strip(),
                        min_stock_level=int(row.get("min_stock_level", 5)),
                        brand=row.get("brand", "").strip(),
                        manufacturer=row.get("manufacturer", "").strip(),
                        status=SupplierProductStatus.DRAFT,
                    )

                    # Set category based on product type
                    if product_type == "input":
                        category = row.get("category", "").strip().lower()
                        if category:
                            try:
                                from app.models.supplier import InputCategory
                                product.input_category = InputCategory(category)
                            except ValueError:
                                errors.append({
                                    "row_number": idx,
                                    "field": "category",
                                    "error": f"Invalid input category: {category}",
                                    "value": category
                                })
                                continue
                    else:
                        category = row.get("category", "").strip().lower()
                        if category:
                            try:
                                from app.models.supplier import MachineryCategory
                                product.machinery_category = MachineryCategory(category)
                            except ValueError:
                                errors.append({
                                    "row_number": idx,
                                    "field": "category",
                                    "error": f"Invalid machinery category: {category}",
                                    "value": category
                                })
                                continue

                    # Set machinery-specific fields
                    if product_type == "machinery":
                        condition = row.get("condition", "new").strip().lower()
                        if condition in ["new", "used", "refurbished"]:
                            product.condition = condition
                        warranty = row.get("warranty_months")
                        if warranty:
                            try:
                                product.warranty_months = int(warranty)
                            except ValueError:
                                pass

                    db.add(product)
                    created_products.append(product)
                    successful += 1

                except Exception as e:
                    errors.append({
                        "row_number": idx,
                        "field": "general",
                        "error": str(e),
                        "value": str(row)
                    })

            # Commit all products
            if created_products:
                db.commit()

            # Update import record
            import_record.total_rows = len(rows)
            import_record.successful = successful
            import_record.failed = len(errors)
            import_record.errors = json.dumps(errors) if errors else None
            import_record.status = "completed" if not errors else "partial"
            import_record.completed_at = datetime.now(timezone.utc)
            db.commit()

            return {
                "import_id": str(import_record.id),
                "status": import_record.status,
                "total_rows": import_record.total_rows,
                "successful": import_record.successful,
                "failed": import_record.failed,
                "errors": errors,
                "created_at": import_record.created_at,
            }

        except Exception as e:
            # Rollback on error
            db.rollback()
            import_record.status = "failed"
            import_record.errors = json.dumps([{"error": str(e)}])
            import_record.completed_at = datetime.now(timezone.utc)
            db.commit()

            raise HTTPException(status_code=500, detail=f"CSV import failed: {str(e)}")


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
        for idx, item in enumerate(items_data, start=1):
            if not item.get("product_id"):
                raise HTTPException(status_code=400, detail=f"Item {idx} is missing product_id")
            if item.get("quantity") is None:
                raise HTTPException(status_code=400, detail=f"Item {idx} is missing quantity")
            if float(item["quantity"]) <= 0:
                raise HTTPException(status_code=400, detail=f"Item {idx} quantity must be greater than zero")

        # Group items by supplier
        try:
            product_ids = [uuid.UUID(str(i["product_id"])) for i in items_data]
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="One or more product_id values are not valid UUIDs")
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
            if p.quantity_available < int(item["quantity"]):
                raise HTTPException(status_code=400, detail=f"Insufficient stock for '{p.name}'")

        # Group by supplier to create separate orders per supplier
        supplier_groups: Dict[uuid.UUID, list] = {}
        for item in items_data:
            p = product_map[str(item["product_id"])]
            sg = supplier_groups.setdefault(p.supplier_id, [])
            sg.append({"product": p, "quantity": int(item["quantity"])})

        orders_created = []
        for supplier_id, group_items in supplier_groups.items():
            subtotal = sum(gi["product"].price * gi["quantity"] for gi in group_items)
            from app.services.subscription_service import SubscriptionService
            supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
            if not supplier:
                raise HTTPException(status_code=404, detail="Supplier not found")
            if supplier.verification_status != SupplierVerificationStatus.APPROVED:
                raise HTTPException(status_code=403, detail="Supplier is not approved for commerce")
            fee_quote = SubscriptionService.calculate_fee_for_owner(db, subtotal, supplier=supplier) if supplier else {
                "platform_fee": round(subtotal * PLATFORM_FEE_PERCENT, 2)
            }
            platform_fee = fee_quote["platform_fee"]
            total = round(subtotal, 2)

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

            success = WalletService.hold_escrow(
                db,
                user_id=buyer_id,
                amount=total,
                currency=order.currency,
                idempotency_key=f"supplier_order_hold:{order.id}",
            )
            if not success:
                db.rollback()
                raise HTTPException(status_code=400, detail="Insufficient wallet balance for supplier checkout")
            EscrowAccountService.mark_supplier_funded(db, order, total)
            orders_created.append(order)

        db.commit()

        if len(orders_created) == 1:
            db.refresh(orders_created[0])
            return orders_created[0]

        return orders_created[0]  # Return first order, caller can handle multiple

    @staticmethod
    def get_buyer_orders(db: Session, buyer_id: uuid.UUID) -> list[SupplierOrder]:
        """Get all supplier orders for a buyer/farmer."""
        return db.query(SupplierOrder).filter(SupplierOrder.buyer_id == buyer_id).order_by(SupplierOrder.created_at.desc()).all()

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
        if not can_transition_supplier_order_status(order.status, SupplierOrderStatus.CONFIRMED):
            raise HTTPException(status_code=400, detail="Invalid supplier order transition")
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
        if not can_transition_supplier_order_status(order.status, SupplierOrderStatus.SHIPPED):
            raise HTTPException(status_code=400, detail="Invalid supplier order transition")
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
        if not can_transition_supplier_order_status(order.status, SupplierOrderStatus.CANCELLED):
            raise HTTPException(status_code=400, detail="Invalid supplier order transition")

        order.status = SupplierOrderStatus.CANCELLED
        order.cancel_reason = reason

        # Restore stock - use joinedload to avoid N+1 query
        from sqlalchemy.orm import joinedload
        items = db.query(SupplierOrderItem).options(
            joinedload(SupplierOrderItem.product)
        ).filter(SupplierOrderItem.order_id == order_id).all()
        for item in items:
            product = item.product
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

        if order.payment_status == SupplierPaymentStatus.ESCROW:
            success = WalletService.refund_escrow(
                db,
                buyer_id=order.buyer_id,
                amount=order.total_amount,
                currency=order.currency,
                idempotency_key=f"supplier_order_refund:{order.id}",
            )
            if not success:
                db.rollback()
                raise HTTPException(status_code=500, detail="Supplier order refund failed")
            from app.models.escrow import EscrowStatus, EscrowTransactionType
            account = EscrowAccountService.get_or_create_for_supplier_order(db, order)
            if account.status != EscrowStatus.REFUNDED:
                account.status = EscrowStatus.REFUNDED
                account.refunded_at = datetime.now(timezone.utc)
                EscrowAccountService._record(
                    db,
                    account,
                    EscrowTransactionType.REFUND,
                    order.total_amount,
                    EscrowStatus.REFUNDED,
                    reference=f"supplier_escrow_refunded:{order.id}",
                )
            order.payment_status = SupplierPaymentStatus.REFUNDED

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
        if not can_transition_supplier_order_status(order.status, SupplierOrderStatus.DELIVERED):
            raise HTTPException(status_code=400, detail="Invalid supplier order transition")

        order.status = SupplierOrderStatus.DELIVERED
        order.delivered_at = datetime.now(timezone.utc)
        order.payment_status = SupplierPaymentStatus.PAID

        # Credit supplier wallet through immutable ledger escrow release.
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        net = round(order.total_amount - order.platform_fee, 2)
        success = WalletService.release_escrow(
            db,
            buyer_id=order.buyer_id,
            seller_id=profile.user_id,
            amount=order.total_amount,
            fee=order.platform_fee,
            currency=order.currency,
            idempotency_key=f"supplier_order_release:{order.id}",
        )
        if not success:
            db.rollback()
            raise HTTPException(status_code=500, detail="Supplier escrow settlement failed")

        profile.lifetime_earnings += net
        profile.total_sales += 1
        profile.total_revenue += order.total_amount

        txn = SupplierWalletTransaction(
            supplier_id=supplier_id,
            order_id=order.id,
            txn_type=SupplierWalletTxnType.SALE,
            amount=order.total_amount,
            fee=order.platform_fee,
            net_amount=net,
            description=f"Payment for order {order.order_number}",
        )
        db.add(txn)
        from app.models.escrow import EscrowStatus, EscrowTransactionType
        account = EscrowAccountService.get_or_create_for_supplier_order(db, order)
        if account.status != EscrowStatus.RELEASED:
            account.status = EscrowStatus.RELEASED
            account.released_at = datetime.now(timezone.utc)
            EscrowAccountService._record(
                db,
                account,
                EscrowTransactionType.RELEASE,
                order.total_amount,
                EscrowStatus.RELEASED,
                reference=f"supplier_escrow_released:{order.id}",
                metadata={"platform_fee": order.platform_fee, "supplier_payout": net},
            )
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
        available = LedgerService.get_balance(db, profile.user_id, "USD")
        pending = LedgerService.get_pending_balance(db, profile.user_id, "USD")
        return {
            "available_balance": available,
            "pending_balance": pending,
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
        if LedgerService.get_balance(db, profile.user_id, "USD") < amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        fee = min(round(amount * WITHDRAWAL_FEE_PERCENT, 2), WITHDRAWAL_FEE_CAP)
        net = round(amount - fee, 2)

        success = WalletService.withdraw(
            db,
            user_id=profile.user_id,
            amount=amount,
            currency="USD",
            idempotency_key=f"supplier_withdrawal:{supplier_id}:{uuid.uuid4()}",
        )
        if not success:
            db.rollback()
            raise HTTPException(status_code=500, detail="Withdrawal ledger entry failed")
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
            "available_balance": LedgerService.get_balance(db, profile.user_id, "USD"),
            "pending_balance": LedgerService.get_pending_balance(db, profile.user_id, "USD"),
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
        verification_status_text = sa_func.lower(SupplierProfile.verification_status.cast(String))
        return db.query(SupplierProfile).filter(
            verification_status_text == SupplierVerificationStatus.APPROVED.value,
            SupplierProfile.is_active == True,
        ).order_by(desc(SupplierProfile.rating)).offset(offset).limit(limit).all()

    @staticmethod
    def get_supplier_products(db: Session, supplier_id: uuid.UUID) -> list[SupplierProduct]:
        product_status_text = sa_func.lower(SupplierProduct.status.cast(String))
        return db.query(SupplierProduct).filter(
            SupplierProduct.supplier_id == supplier_id,
            product_status_text == SupplierProductStatus.ACTIVE.value,
        ).order_by(desc(SupplierProduct.is_boosted), desc(SupplierProduct.created_at)).all()

    @staticmethod
    def list_all_products(db: Session, category: Optional[str] = None, product_type: Optional[str] = None, search: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[SupplierProduct]:
        product_status_text = sa_func.lower(SupplierProduct.status.cast(String))
        verification_status_text = sa_func.lower(SupplierProfile.verification_status.cast(String))
        q = db.query(SupplierProduct).join(SupplierProfile).filter(
            product_status_text == SupplierProductStatus.ACTIVE.value,
            verification_status_text == SupplierVerificationStatus.APPROVED.value,
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
        product_status_text = sa_func.lower(SupplierProduct.status.cast(String))
        product = db.query(SupplierProduct).options(
            joinedload(SupplierProduct.supplier),
        ).filter(
            SupplierProduct.id == product_id,
            product_status_text == SupplierProductStatus.ACTIVE.value,
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


# ============================================================================
# SUPPLIER REVIEWS
# ============================================================================

class SupplierReviewService:

    @staticmethod
    def create_review(db: Session, buyer_id: uuid.UUID, supplier_id: uuid.UUID, data: dict) -> SupplierReview:
        """Create a review for a supplier after order completion."""
        # Validate order exists and belongs to buyer
        order = db.query(SupplierOrder).filter(
            SupplierOrder.id == uuid.UUID(data["order_id"]),
            SupplierOrder.buyer_id == buyer_id,
            SupplierOrder.supplier_id == supplier_id,
            SupplierOrder.status == SupplierOrderStatus.DELIVERED,
        ).first()
        
        if not order:
            raise HTTPException(status_code=400, detail="Order not found or not eligible for review")
        
        # Check if review already exists for this order
        existing = db.query(SupplierReview).filter(
            SupplierReview.order_id == uuid.UUID(data["order_id"]),
            SupplierReview.buyer_id == buyer_id,
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Review already exists for this order")
        
        # Create review
        review = SupplierReview(
            supplier_id=supplier_id,
            buyer_id=buyer_id,
            order_id=uuid.UUID(data["order_id"]),
            rating=data["rating"],
            comment=data.get("comment"),
        )
        
        db.add(review)
        db.commit()
        db.refresh(review)
        
        # Update supplier rating
        SupplierReviewService._update_supplier_rating(db, supplier_id)
        
        return review

    @staticmethod
    def get_reviews(db: Session, supplier_id: uuid.UUID, limit: int = 50, offset: int = 0) -> dict:
        """Get all reviews for a supplier with statistics."""
        reviews = db.query(SupplierReview).filter(
            SupplierReview.supplier_id == supplier_id,
            SupplierReview.is_hidden == False,
        ).order_by(desc(SupplierReview.created_at)).offset(offset).limit(limit).all()
        
        # Calculate statistics
        all_reviews = db.query(SupplierReview).filter(
            SupplierReview.supplier_id == supplier_id,
            SupplierReview.is_hidden == False,
        ).all()
        
        total = len(all_reviews)
        avg_rating = sum(r.rating for r in all_reviews) / total if total > 0 else 0.0
        
        # Rating distribution
        rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in all_reviews:
            rating_dist[r.rating] = rating_dist.get(r.rating, 0) + 1
        
        # Load buyer names
        buyer_ids = [r.buyer_id for r in reviews]
        buyers = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(buyer_ids)).all()}
        
        # Add buyer names to reviews
        for review in reviews:
            review.buyer_name = buyers.get(review.buyer_id, "Anonymous")
        
        return {
            "reviews": reviews,
            "total": total,
            "average_rating": round(avg_rating, 1),
            "rating_distribution": rating_dist,
        }

    @staticmethod
    def respond_to_review(db: Session, supplier_id: uuid.UUID, review_id: uuid.UUID, response: str) -> SupplierReview:
        """Supplier responds to a review."""
        review = db.query(SupplierReview).filter(
            SupplierReview.id == review_id,
            SupplierReview.supplier_id == supplier_id,
        ).first()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        review.supplier_response = response
        review.supplier_responseed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(review)
        
        return review

    @staticmethod
    def flag_review(db: Session, review_id: uuid.UUID, notes: Optional[str] = None) -> SupplierReview:
        """Flag a review for moderation."""
        review = db.query(SupplierReview).filter(SupplierReview.id == review_id).first()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        review.is_flagged = True
        review.moderation_notes = notes
        db.commit()
        db.refresh(review)
        
        return review

    @staticmethod
    def hide_review(db: Session, review_id: uuid.UUID, notes: Optional[str] = None) -> SupplierReview:
        """Hide a review (admin action)."""
        review = db.query(SupplierReview).filter(SupplierReview.id == review_id).first()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        review.is_hidden = True
        review.moderation_notes = notes
        db.commit()
        db.refresh(review)
        
        return review

    @staticmethod
    def _update_supplier_rating(db: Session, supplier_id: uuid.UUID):
        """Recalculate supplier rating based on all reviews."""
        reviews = db.query(SupplierReview).filter(
            SupplierReview.supplier_id == supplier_id,
            SupplierReview.is_hidden == False,
        ).all()
        
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
            if profile:
                profile.rating = round(avg_rating, 1)
                db.commit()


# ============================================================================
# SUPPLIER SUBSCRIPTION INTEGRATION
# ============================================================================

class SupplierSubscriptionService:

    @staticmethod
    def set_subscription(db: Session, supplier_id: uuid.UUID, plan: str, billing_cycle: str = "monthly") -> dict:
        from app.services.subscription_service import SubscriptionService

        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return SubscriptionService.change_plan(db, plan, billing_cycle, supplier=profile, activate_paid=True)

    @staticmethod
    def get_subscription(db: Session, supplier_id: uuid.UUID) -> dict:
        """Get a supplier's subscription details."""
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        from app.services.subscription_service import SubscriptionService

        subscription = SubscriptionService.get_current_subscription(db, supplier=profile)
        payload = SubscriptionService.serialize_subscription(db, subscription)
        payload.update({
            "subscription_plan": subscription.plan.code,
            "subscription_status": subscription.status.lower(),
            "subscription_start_date": subscription.current_period_start,
            "subscription_end_date": subscription.current_period_end,
            "is_expired": subscription.status == "EXPIRED",
            "features": payload["plan"]["features"],
            "price": payload["plan"]["monthly_price"],
            "savings": SubscriptionService.savings_dashboard(db, supplier=profile),
            "badges": SubscriptionService.get_badges(db, supplier=profile),
        })
        return payload

    @staticmethod
    def cancel_subscription(db: Session, supplier_id: uuid.UUID) -> dict:
        """Cancel a supplier's subscription."""
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        from app.services.subscription_service import SubscriptionService

        return SubscriptionService.cancel_subscription(db, supplier=profile)

    @staticmethod
    def check_feature_entitlement(db: Session, supplier_id: uuid.UUID, feature: str) -> bool:
        """Check if a supplier has access to a specific feature based on their subscription."""
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            return False
        
        from app.services.subscription_service import SubscriptionService

        subscription = SubscriptionService.get_current_subscription(db, supplier=profile)
        allowed = {item.feature_key for item in subscription.plan.features if item.is_enabled}
        allowed.update(item.label.lower().replace(" ", "_") for item in subscription.plan.features if item.is_enabled)
        return feature in allowed

    @staticmethod
    def check_transaction_limit(db: Session, supplier_id: uuid.UUID) -> dict:
        """Check if a supplier has reached their transaction limit."""
        profile = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
        if not profile:
            return {"has_limit": True, "remaining": 0, "limit": 0}
        
        return {"has_limit": False, "remaining": -1, "limit": -1, "used": 0}


# ============================================================================
# SUPPLIER LOGISTICS INTEGRATION
# ============================================================================

class SupplierLogisticsService:

    @staticmethod
    def create_delivery_record(db: Session, order_id: uuid.UUID) -> dict:
        """Create a logistics delivery record for a supplier order."""
        from app.models.logistics import OrderDelivery, DeliveryMethod, DeliveryStatus
        
        order = db.query(SupplierOrder).filter(SupplierOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if delivery record already exists
        if order.logistics_delivery_id:
            raise HTTPException(status_code=400, detail="Delivery record already exists")
        
        # Determine delivery method based on shipping method
        delivery_method = DeliveryMethod.THIRD_PARTY
        if order.shipping_method:
            if "buyer" in order.shipping_method.lower():
                delivery_method = DeliveryMethod.BUYER_COLLECTS
            elif "farmer" in order.shipping_method.lower() or "supplier" in order.shipping_method.lower():
                delivery_method = DeliveryMethod.FARMER_DELIVERS
        
        # Create delivery record
        delivery = OrderDelivery(
            order_id=str(order.id),  # Store as string to match logistics model
            delivery_method=delivery_method,
            status=DeliveryStatus.PENDING_PICKUP,
            pickup_address=None,  # Will be set when assigned
            delivery_address=order.delivery_address,
            delivery_phone=order.delivery_phone,
            recipient_name=None,  # Will be set from buyer profile
            scheduled_pickup_time=None,
            scheduled_delivery_time=None,
            pickup_confirmed_at=None,
            pickup_completed_at=None,
            delivery_in_progress_at=None,
            delivery_confirmed_at=None,
            agent_id=None,
            driver_id=None,
            tracking_number=order.tracking_number,
            delivery_proof_url=order.delivery_proof_url,
            gps_coordinates=None,
            notes=order.supplier_notes,
        )
        
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        
        # Link order to delivery
        order.logistics_delivery_id = delivery.id
        db.commit()
        
        return {
            "delivery_id": str(delivery.id),
            "status": delivery.status.value,
            "delivery_method": delivery.delivery_method.value,
        }

    @staticmethod
    def get_delivery_status(db: Session, order_id: uuid.UUID) -> dict:
        """Get the logistics delivery status for a supplier order."""
        from app.models.logistics import OrderDelivery
        
        order = db.query(SupplierOrder).filter(SupplierOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if not order.logistics_delivery_id:
            return {"status": "not_linked", "message": "Order not linked to logistics system"}
        
        delivery = db.query(OrderDelivery).filter(OrderDelivery.id == order.logistics_delivery_id).first()
        if not delivery:
            return {"status": "not_found", "message": "Delivery record not found"}
        
        return {
            "delivery_id": str(delivery.id),
            "status": delivery.status.value,
            "delivery_method": delivery.delivery_method.value,
            "tracking_number": delivery.tracking_number,
            "agent_id": str(delivery.agent_id) if delivery.agent_id else None,
            "driver_id": str(delivery.driver_id) if delivery.driver_id else None,
            "scheduled_pickup_time": delivery.scheduled_pickup_time,
            "scheduled_delivery_time": delivery.scheduled_delivery_time,
            "pickup_confirmed_at": delivery.pickup_confirmed_at,
            "pickup_completed_at": delivery.pickup_completed_at,
            "delivery_in_progress_at": delivery.delivery_in_progress_at,
            "delivery_confirmed_at": delivery.delivery_confirmed_at,
            "gps_coordinates": delivery.gps_coordinates,
        }

    @staticmethod
    def sync_order_status(db: Session, order_id: uuid.UUID) -> dict:
        """Sync supplier order status with logistics delivery status."""
        from app.models.logistics import OrderDelivery, DeliveryStatus
        
        order = db.query(SupplierOrder).filter(SupplierOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if not order.logistics_delivery_id:
            return {"status": "not_linked", "message": "Order not linked to logistics system"}
        
        delivery = db.query(OrderDelivery).filter(OrderDelivery.id == order.logistics_delivery_id).first()
        if not delivery:
            return {"status": "not_found", "message": "Delivery record not found"}
        
        # Map delivery status to order status
        status_mapping = {
            DeliveryStatus.PENDING_PICKUP: SupplierOrderStatus.NEW,
            DeliveryStatus.PICKUP_SCHEDULED: SupplierOrderStatus.CONFIRMED,
            DeliveryStatus.PICKUP_IN_PROGRESS: SupplierOrderStatus.PROCESSING,
            DeliveryStatus.PICKUP_COMPLETED: SupplierOrderStatus.PROCESSING,
            DeliveryStatus.IN_TRANSIT: SupplierOrderStatus.SHIPPED,
            DeliveryStatus.DELAYED: SupplierOrderStatus.PROCESSING,
            DeliveryStatus.ARRIVED: SupplierOrderStatus.SHIPPED,
            DeliveryStatus.DELIVERY_IN_PROGRESS: SupplierOrderStatus.SHIPPED,
            DeliveryStatus.DELIVERED: SupplierOrderStatus.DELIVERED,
            DeliveryStatus.CONFIRMED: SupplierOrderStatus.DELIVERED,
            DeliveryStatus.AUTO_CONFIRMED: SupplierOrderStatus.DELIVERED,
            DeliveryStatus.DISPUTED: SupplierOrderStatus.REFUNDED,
        }
        
        new_status = status_mapping.get(delivery.status, order.status)
        
        if new_status != order.status:
            order.status = new_status
            db.commit()
        
        return {
            "order_status": order.status.value,
            "delivery_status": delivery.status.value,
            "synced": new_status != order.status,
        }


# ============================================================================
# SUPPLIER PAYOUT PROCESSING
# ============================================================================

class SupplierPayoutService:

    @staticmethod
    def process_pending_payouts(db: Session) -> dict:
        """Process all pending withdrawal requests (cron job)."""
        pending_withdrawals = db.query(SupplierWalletTransaction).filter(
            SupplierWalletTransaction.txn_type == SupplierWalletTxnType.WITHDRAWAL,
            SupplierWalletTransaction.status == "pending",
        ).all()
        
        processed = 0
        failed = 0
        
        for withdrawal in pending_withdrawals:
            try:
                SupplierPayoutService._execute_payout(db, withdrawal)
                processed += 1
            except Exception as e:
                withdrawal.status = "failed"
                withdrawal.description = f"Payout failed: {str(e)}"
                db.commit()
                failed += 1
        
        return {
            "processed": processed,
            "failed": failed,
            "total": len(pending_withdrawals),
        }

    @staticmethod
    def _execute_payout(db: Session, withdrawal: SupplierWalletTransaction):
        """Execute a single payout (integrates with payment gateway)."""
        from app.core.config import settings

        if not settings.ENABLE_SUPPLIER_PAYOUT_PROCESSING:
            raise RuntimeError("Supplier payout provider is not configured")

        withdrawal.status = "processing"
        withdrawal.description = f"Payout submitted via {withdrawal.withdrawal_method}"
        withdrawal.reference = f"PAYOUT-{withdrawal.id[:8].upper()}"
        
        db.commit()

    @staticmethod
    def get_payout_history(db: Session, supplier_id: uuid.UUID, limit: int = 50, offset: int = 0) -> dict:
        """Get payout history for a supplier."""
        payouts = db.query(SupplierWalletTransaction).filter(
            SupplierWalletTransaction.supplier_id == supplier_id,
            SupplierWalletTransaction.txn_type == SupplierWalletTxnType.WITHDRAWAL,
        ).order_by(desc(SupplierWalletTransaction.created_at)).offset(offset).limit(limit).all()
        
        total = db.query(SupplierWalletTransaction).filter(
            SupplierWalletTransaction.supplier_id == supplier_id,
            SupplierWalletTransaction.txn_type == SupplierWalletTxnType.WITHDRAWAL,
        ).count()
        
        # Calculate totals
        total_withdrawn = sum(p.amount for p in payouts)
        total_fees = sum(p.fee for p in payouts)
        total_net = sum(p.net_amount for p in payouts)
        
        return {
            "payouts": [
                {
                    "id": str(p.id),
                    "amount": p.amount,
                    "fee": p.fee,
                    "net_amount": p.net_amount,
                    "method": p.withdrawal_method,
                    "status": p.status,
                    "reference": p.reference,
                    "description": p.description,
                    "created_at": p.created_at,
                }
                for p in payouts
            ],
            "total": total,
            "total_withdrawn": total_withdrawn,
            "total_fees": total_fees,
            "total_net": total_net,
        }

    @staticmethod
    def get_tax_report(db: Session, supplier_id: uuid.UUID, year: int, month: Optional[int] = None) -> dict:
        """Generate tax report for supplier earnings."""
        from datetime import datetime
        
        # Filter transactions by date range
        start_date = datetime(year, 1, 1) if month is None else datetime(year, month, 1)
        if month is None:
            end_date = datetime(year, 12, 31, 23, 59, 59)
        else:
            if month == 12:
                end_date = datetime(year, 12, 31, 23, 59, 59)
            else:
                end_date = datetime(year, month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
        
        # Get sales transactions
        sales = db.query(SupplierWalletTransaction).filter(
            SupplierWalletTransaction.supplier_id == supplier_id,
            SupplierWalletTransaction.txn_type == SupplierWalletTxnType.SALE,
            SupplierWalletTransaction.created_at >= start_date,
            SupplierWalletTransaction.created_at <= end_date,
        ).all()
        
        # Get withdrawal transactions
        withdrawals = db.query(SupplierWalletTransaction).filter(
            SupplierWalletTransaction.supplier_id == supplier_id,
            SupplierWalletTransaction.txn_type == SupplierWalletTxnType.WITHDRAWAL,
            SupplierWalletTransaction.created_at >= start_date,
            SupplierWalletTransaction.created_at <= end_date,
        ).all()
        
        # Get platform fees
        platform_fees = db.query(SupplierWalletTransaction).filter(
            SupplierWalletTransaction.supplier_id == supplier_id,
            SupplierWalletTransaction.txn_type == SupplierWalletTxnType.PLATFORM_FEE,
            SupplierWalletTransaction.created_at >= start_date,
            SupplierWalletTransaction.created_at <= end_date,
        ).all()
        
        # Calculate totals
        total_gross = sum(s.amount for s in sales)
        total_platform_fees = sum(f.amount for f in platform_fees)
        total_withdrawn = sum(w.net_amount for w in withdrawals if w.status == "completed")
        
        return {
            "period": f"{year}" if month is None else f"{year}-{month:02d}",
            "total_gross": total_gross,
            "total_platform_fees": total_platform_fees,
            "total_net": total_gross - total_platform_fees,
            "total_withdrawn": total_withdrawn,
            "taxable_income": total_gross - total_platform_fees,
            "transaction_count": len(sales),
            "withdrawal_count": len(withdrawals),
        }


# ============================================================================
# SUPPLIER DISCOUNT/PROMOTION MANAGEMENT
# ============================================================================

class SupplierDiscountService:

    @staticmethod
    def create_discount(db: Session, supplier_id: uuid.UUID, data: dict) -> SupplierDiscount:
        """Create a new discount/promotion code."""
        # Check if code already exists
        existing = db.query(SupplierDiscount).filter(
            SupplierDiscount.code == data["code"].upper()
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Discount code already exists")
        
        # Create discount
        discount = SupplierDiscount(
            supplier_id=supplier_id,
            code=data["code"].upper(),
            discount_type=data["discount_type"],
            discount_value=data["discount_value"],
            min_order_value=data.get("min_order_value"),
            max_discount_amount=data.get("max_discount_amount"),
            applicable_products=data.get("applicable_products"),
            applicable_categories=data.get("applicable_categories"),
            max_uses=data.get("max_uses"),
            max_uses_per_user=data.get("max_uses_per_user"),
            start_date=data["start_date"],
            end_date=data["end_date"],
            description=data.get("description"),
        )
        
        db.add(discount)
        db.commit()
        db.refresh(discount)
        
        return discount

    @staticmethod
    def list_discounts(db: Session, supplier_id: uuid.UUID, active_only: bool = False) -> list[SupplierDiscount]:
        """List all discounts for a supplier."""
        q = db.query(SupplierDiscount).filter(SupplierDiscount.supplier_id == supplier_id)
        
        if active_only:
            now = datetime.now(timezone.utc)
            q = q.filter(
                SupplierDiscount.is_active == True,
                SupplierDiscount.start_date <= now,
                SupplierDiscount.end_date >= now,
            )
        
        return q.order_by(desc(SupplierDiscount.created_at)).all()

    @staticmethod
    def get_discount(db: Session, discount_id: uuid.UUID, supplier_id: uuid.UUID) -> SupplierDiscount:
        """Get a specific discount."""
        discount = db.query(SupplierDiscount).filter(
            SupplierDiscount.id == discount_id,
            SupplierDiscount.supplier_id == supplier_id,
        ).first()
        
        if not discount:
            raise HTTPException(status_code=404, detail="Discount not found")
        
        return discount

    @staticmethod
    def update_discount(db: Session, discount_id: uuid.UUID, supplier_id: uuid.UUID, data: dict) -> SupplierDiscount:
        """Update a discount."""
        discount = db.query(SupplierDiscount).filter(
            SupplierDiscount.id == discount_id,
            SupplierDiscount.supplier_id == supplier_id,
        ).first()
        
        if not discount:
            raise HTTPException(status_code=404, detail="Discount not found")
        
        for key, val in data.items():
            if val is not None and hasattr(discount, key):
                setattr(discount, key, val)
        
        db.commit()
        db.refresh(discount)
        
        return discount

    @staticmethod
    def delete_discount(db: Session, discount_id: uuid.UUID, supplier_id: uuid.UUID) -> dict:
        """Delete a discount."""
        discount = db.query(SupplierDiscount).filter(
            SupplierDiscount.id == discount_id,
            SupplierDiscount.supplier_id == supplier_id,
        ).first()
        
        if not discount:
            raise HTTPException(status_code=404, detail="Discount not found")
        
        db.delete(discount)
        db.commit()
        
        return {"message": "Discount deleted"}

    @staticmethod
    def validate_discount(db: Session, code: str, order_total: float, product_ids: Optional[list] = None, user_id: Optional[uuid.UUID] = None) -> dict:
        """Validate a discount code and calculate discount amount."""
        discount = db.query(SupplierDiscount).filter(
            SupplierDiscount.code == code.upper(),
            SupplierDiscount.is_active == True,
        ).first()
        
        if not discount:
            return {"valid": False, "error": "Invalid discount code"}
        
        # Check validity period
        now = datetime.now(timezone.utc)
        if discount.start_date > now or discount.end_date < now:
            return {"valid": False, "error": "Discount code has expired"}
        
        # Check usage limits
        if discount.max_uses and discount.current_uses >= discount.max_uses:
            return {"valid": False, "error": "Discount code has reached maximum uses"}
        
        # Check minimum order value
        if discount.min_order_value and order_total < discount.min_order_value:
            return {"valid": False, "error": f"Minimum order value of ${discount.min_order_value} not met"}
        
        # Check product/category applicability
        if discount.applicable_products and product_ids:
            if not any(pid in discount.applicable_products for pid in product_ids):
                return {"valid": False, "error": "Discount not applicable to these products"}
        
        # Calculate discount amount
        discount_amount = 0.0
        if discount.discount_type == "percentage":
            discount_amount = order_total * (discount.discount_value / 100)
        elif discount.discount_type == "fixed_amount":
            discount_amount = discount.discount_value
        elif discount.discount_type == "buy_x_get_y":
            # Simplified: treat as percentage for now
            discount_amount = order_total * (discount.discount_value / 100)
        
        # Apply maximum discount limit
        if discount.max_discount_amount and discount_amount > discount.max_discount_amount:
            discount_amount = discount.max_discount_amount
        
        return {
            "valid": True,
            "discount_id": str(discount.id),
            "discount_type": discount.discount_type,
            "discount_amount": round(discount_amount, 2),
            "final_total": round(order_total - discount_amount, 2),
        }

    @staticmethod
    def apply_discount(db: Session, discount_id: uuid.UUID) -> SupplierDiscount:
        """Apply a discount (increment usage count)."""
        discount = db.query(SupplierDiscount).filter(SupplierDiscount.id == discount_id).first()
        
        if not discount:
            raise HTTPException(status_code=404, detail="Discount not found")
        
        discount.current_uses += 1
        db.commit()
        db.refresh(discount)
        
        return discount
