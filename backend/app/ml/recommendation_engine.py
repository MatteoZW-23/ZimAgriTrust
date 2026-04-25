from typing import List, Dict
from datetime import datetime


class RecommendationEngine:
    """
    Agri-Link Recommendation Engine.
    Combines live DB demand signals with agronomic suitability rules
    to suggest crops and buyers — no trained weights required.
    """

    def __init__(self):
        self.architecture = "Rule-based Collaborative-Content Recommender (Live DB)"

    # ── Crop suitability table (soil type → suitable crops) ───────────────────
    _SOIL_CROPS: Dict[str, List[str]] = {
        "Sandy Loam":   ["Maize", "Sunflower Seeds", "Groundnuts", "Sweet Potatoes"],
        "Clay":         ["Wheat", "Sugar Beans", "Soybeans", "Sorghum"],
        "Loam":         ["Tobacco", "Maize", "Soybeans", "Vegetables"],
        "Sandy":        ["Groundnuts", "Sunflower Seeds", "Sorghum", "Cassava"],
        "Silty Loam":   ["Wheat", "Maize", "Sugar Beans", "Vegetables"],
    }

    # ── Base profit index by crop ─────────────────────────────────────────────
    _PROFIT_INDEX: Dict[str, str] = {
        "Tobacco":        "Very High",
        "Soybeans":       "High",
        "Sunflower Seeds":"High",
        "Wheat":          "High",
        "Maize":          "Medium",
        "Sugar Beans":    "Medium",
        "Groundnuts":     "Medium",
        "Sorghum":        "Low",
        "Sweet Potatoes": "Low",
        "Cassava":        "Low",
        "Vegetables":     "Medium",
    }

    def recommend_for_farmer(self, farmer_profile: Dict, db=None) -> List[Dict]:
        """
        Suggests crops based on soil type and live demand signals from the DB.
        Falls back to agronomic rules when DB is unavailable.
        """
        soil_type = farmer_profile.get("soil_type", "Sandy Loam")
        suitable = self._SOIL_CROPS.get(soil_type, self._SOIL_CROPS["Sandy Loam"])

        # Pull live demand ratios if DB is available
        demand_map: Dict[str, float] = {}
        if db is not None:
            try:
                from sqlalchemy import func
                from app.models.listing import Listing, Offer, ListingStatus
                rows = (
                    db.query(
                        Listing.product_type,
                        func.count(Offer.id).label("offers"),
                        func.count(Listing.id).label("listings"),
                    )
                    .outerjoin(Offer, Offer.listing_id == Listing.id)
                    .filter(Listing.status == ListingStatus.ACTIVE)
                    .group_by(Listing.product_type)
                    .all()
                )
                for r in rows:
                    demand_map[r.product_type] = r.offers / max(r.listings, 1)
            except Exception:
                pass

        results = []
        for crop in suitable:
            demand_ratio = demand_map.get(crop, 0.0)
            # Suitability: base 70 + up to 20 from demand signal
            suitability = min(99, 70 + int(demand_ratio * 10))
            supply_note = (
                "High buyer demand — good time to sell"
                if demand_ratio > 2
                else "Stable demand — consistent market"
                if demand_ratio > 0.5
                else f"Well-suited for {soil_type} soil"
            )
            results.append({
                "crop": crop,
                "suitability": suitability,
                "profit_index": self._PROFIT_INDEX.get(crop, "Medium"),
                "reason": supply_note,
                "demand_ratio": round(demand_ratio, 2),
                "type": "CROP_SELECTION",
            })

        # Sort by suitability descending
        results.sort(key=lambda x: x["suitability"], reverse=True)
        return results[:5]

    def recommend_listings_for_buyer(self, buyer_id, history: List[Dict], db=None) -> List[Dict]:
        """
        Returns active listings that match the buyer's past purchase history.
        Falls back to top-demand listings when no history is available.
        """
        if db is None:
            return []

        try:
            from app.models.listing import Listing, ListingStatus
            from app.models.transaction import Order

            # Determine crops the buyer has purchased before
            past_crops: List[str] = [h.get("product_type") for h in history if h.get("product_type")]
            if not past_crops:
                # No history — return top 5 active listings by recency
                listings = (
                    db.query(Listing)
                    .filter(Listing.status == ListingStatus.ACTIVE)
                    .order_by(Listing.created_at.desc())
                    .limit(5)
                    .all()
                )
            else:
                listings = (
                    db.query(Listing)
                    .filter(
                        Listing.status == ListingStatus.ACTIVE,
                        Listing.product_type.in_(past_crops),
                    )
                    .order_by(Listing.created_at.desc())
                    .limit(5)
                    .all()
                )

            return [
                {
                    "listing_id": str(l.id),
                    "product": l.product_type,
                    "price_per_unit": l.price_per_unit,
                    "quantity": l.quantity,
                    "location": l.location_province,
                    "match_score": 0.95 if l.product_type in past_crops else 0.70,
                    "reason": (
                        "Matches your purchase history"
                        if l.product_type in past_crops
                        else "Popular listing in your region"
                    ),
                }
                for l in listings
            ]
        except Exception:
            return []


# Global instance
recommender = RecommendationEngine()
