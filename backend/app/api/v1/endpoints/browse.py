"""
Unified browse endpoint: returns crops + inputs in a normalised shape so the
frontend can render a single grid with the toggle "Crops / Inputs / All".
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.input_marketplace import InputListing, InputListingStatus
from app.models.listing import Listing, ListingStatus

router = APIRouter()


@router.get("/search")
def unified_search(
    kind: str = Query("all", pattern="^(all|crops|inputs)$"),
    q: Optional[str] = None,
    province: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    category_id: Optional[int] = None,         # input-only
    brand: Optional[str] = None,                # input-only
    verified_only: bool = False,                # input-only
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Returns:
      {
        "results": [ { kind: "crop" | "input", ...normalised... }, ... ],
        "counts":  { "crops": N, "inputs": M }
      }
    """
    items: list[dict] = []
    counts = {"crops": 0, "inputs": 0}

    if kind in ("all", "crops"):
        cq = db.query(Listing).filter(Listing.status == ListingStatus.ACTIVE)
        if q:
            like = f"%{q}%"
            cq = cq.filter(Listing.product_type.ilike(like))
        if province:
            cq = cq.filter(Listing.province == province)
        if min_price is not None:
            cq = cq.filter(Listing.price_per_unit >= min_price)
        if max_price is not None:
            cq = cq.filter(Listing.price_per_unit <= max_price)
        crops = cq.order_by(Listing.created_at.desc()).offset(offset).limit(limit).all()
        counts["crops"] = len(crops)
        for l in crops:
            items.append({
                "kind": "crop",
                "id": str(l.id),
                "name": l.product_type,
                "brand": None,
                "price_per_unit": float(l.price_per_unit or 0),
                "currency": l.currency,
                "quantity": float(l.quantity or 0),
                "unit": getattr(l, "unit", "kg"),
                "location": getattr(l, "location", None),
                "province": l.province,
                "photos": getattr(l, "photos", None) or [],
                "verified": bool(getattr(l, "verified_at", None)),
                "expiry_date": None,
                "boosted": bool(getattr(l, "is_boosted", False)),
                "created_at": l.created_at,
            })

    if kind in ("all", "inputs"):
        iq = db.query(InputListing).filter(InputListing.status == InputListingStatus.ACTIVE)
        iq = iq.filter(
            (InputListing.expiry_date.is_(None)) | (InputListing.expiry_date > datetime.utcnow())
        )
        if q:
            like = f"%{q}%"
            iq = iq.filter(
                (InputListing.product_name.ilike(like)) | (InputListing.brand.ilike(like))
            )
        if province:
            iq = iq.filter(InputListing.province == province)
        if min_price is not None:
            iq = iq.filter(InputListing.price_per_unit >= min_price)
        if max_price is not None:
            iq = iq.filter(InputListing.price_per_unit <= max_price)
        if category_id:
            iq = iq.filter(InputListing.category_id == category_id)
        if brand:
            iq = iq.filter(InputListing.brand.ilike(brand))
        if verified_only:
            iq = iq.filter(InputListing.verified_at.isnot(None))

        inputs = (
            iq.order_by(InputListing.is_boosted.desc(), InputListing.created_at.desc())
            .offset(offset).limit(limit).all()
        )
        counts["inputs"] = len(inputs)
        for l in inputs:
            items.append({
                "kind": "input",
                "id": str(l.id),
                "name": l.product_name,
                "brand": l.brand,
                "price_per_unit": float(l.price_per_unit),
                "currency": l.currency,
                "quantity": float(l.quantity),
                "unit": l.unit,
                "location": l.location,
                "province": l.province,
                "photos": l.photos or [],
                "verified": l.verified_at is not None,
                "expiry_date": l.expiry_date,
                "category_id": l.category_id,
                "boosted": bool(l.is_boosted),
                "created_at": l.created_at,
            })

    items.sort(key=lambda x: (not x["boosted"], x["created_at"]), reverse=True)
    return {"results": items[:limit], "counts": counts}
