import uuid

import pytest
from fastapi import HTTPException

from app.models.supplier import (
    SupplierPaymentStatus,
    SupplierProduct,
    SupplierProductStatus,
    SupplierProductType,
    SupplierProfile,
    SupplierVerificationStatus,
)
from app.models.user import User, UserRole, UserStatus
from app.services.supplier_service import SupplierOrderService, SupplierProductService


def _create_supplier_with_product(db):
    user = User(
        full_name="Supplier User",
        phone_number=f"+26377{uuid.uuid4().int % 10000000:07d}",
        password_hash="hash",
        role=UserRole.SUPPLIER,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.flush()

    profile = SupplierProfile(
        user_id=user.id,
        business_name="Supplier Biz",
        verification_status=SupplierVerificationStatus.APPROVED,
    )
    db.add(profile)
    db.flush()

    product = SupplierProduct(
        supplier_id=profile.id,
        product_type=SupplierProductType.INPUT,
        name="Seed Pack",
        price=20.0,
        quantity_available=10,
        status=SupplierProductStatus.ACTIVE,
    )
    db.add(product)
    db.commit()
    return user, profile, product


def test_create_product_rejects_missing_required_fields(db):
    _, profile, _ = _create_supplier_with_product(db)

    with pytest.raises(HTTPException) as exc:
        SupplierProductService.create_product(
            db,
            profile.id,
            {"product_type": "input", "price": 10.0},
        )

    assert exc.value.status_code == 400
    assert "Missing required product fields" in str(exc.value.detail)


def test_supplier_order_rejects_invalid_product_uuid(db):
    buyer = User(
        full_name="Buyer User",
        phone_number=f"+26378{uuid.uuid4().int % 10000000:07d}",
        password_hash="hash",
        role=UserRole.BUYER,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(buyer)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        SupplierOrderService.create_order_from_buyer(
            db,
            buyer.id,
            {"items": [{"product_id": "not-a-uuid", "quantity": 1}]},
        )

    assert exc.value.status_code == 400
    assert "not valid UUIDs" in str(exc.value.detail)


def test_supplier_order_rejects_non_positive_quantity(db):
    buyer = User(
        full_name="Buyer Quantity",
        phone_number=f"+26371{uuid.uuid4().int % 10000000:07d}",
        password_hash="hash",
        role=UserRole.BUYER,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(buyer)
    db.flush()
    _, _, product = _create_supplier_with_product(db)

    with pytest.raises(HTTPException) as exc:
        SupplierOrderService.create_order_from_buyer(
            db,
            buyer.id,
            {"items": [{"product_id": str(product.id), "quantity": 0}]},
        )

    assert exc.value.status_code == 400
    assert "quantity must be greater than zero" in str(exc.value.detail)
