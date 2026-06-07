from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from app.models.dispute import Dispute
from app.models.listing import Listing, ListingStatus, Offer
from app.models.user import User, UserRole
from app.services.price_service import get_price_prediction


class AIAssistantService:
    """Rule-based assistant and intelligence layer for role-specific guidance.

    This service deliberately works without an external LLM provider so the API is
    production-safe by default. A hosted model can later be added behind this
    boundary for richer language generation.
    """

    ASSISTANT_ROLES = {"farmer", "buyer", "supplier", "agent", "admin"}

    ROLE_PLAYBOOKS: Dict[str, Dict[str, List[str]]] = {
        "farmer": {
            "focus": ["listing quality", "price timing", "trust score", "escrow readiness"],
            "actions": [
                "Create listings with grade, harvest date, photos, and verified pickup location.",
                "Use market demand and price forecasts before accepting offers.",
                "Prefer escrow-funded orders before exposing full contact details.",
            ],
        },
        "buyer": {
            "focus": ["verified supply", "offer discipline", "delivery risk", "escrow protection"],
            "actions": [
                "Compare seller trust score, quality grade, unit price, and product handling needs before making an offer.",
                "Use counter-offers when price is outside the market range.",
                "Select platform logistics for high-value, perishable, live, or fragile agriculture goods.",
            ],
        },
        "supplier": {
            "focus": ["stock movement", "input demand", "subscription value", "fulfillment quality"],
            "actions": [
                "Keep active products in stock with clear categories and delivery terms.",
                "Promote inputs before planting windows and peak fertilizer demand.",
                "Use subscription insights to identify high-demand districts.",
            ],
        },
        "agent": {
            "focus": ["verification priority", "dispute evidence", "field support", "response time"],
            "actions": [
                "Prioritize urgent disputes, high-value listings, and expiring delivery windows.",
                "Capture objective evidence: photos, weights, grade notes, and signatures.",
                "Close assignments only after the buyer and seller outcome is recorded.",
            ],
        },
        "admin": {
            "focus": ["market liquidity", "fraud risk", "dispute load", "service health"],
            "actions": [
                "Monitor demand-to-supply gaps by agriculture product, sector, and province.",
                "Escalate users with low trust score and repeated disputes.",
                "Use audit logs and wallet reconciliation before manual financial actions.",
            ],
        },
    }

    @classmethod
    def normalize_assistant_role(cls, assistant_role: str) -> str:
        role = assistant_role.strip().lower().replace("_ai", "").replace("-ai", "")
        if role not in cls.ASSISTANT_ROLES:
            raise ValueError(f"Unsupported assistant role: {assistant_role}")
        return role

    @classmethod
    def answer(
        cls,
        db: Session,
        current_user: User,
        assistant_role: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        role = cls.normalize_assistant_role(assistant_role)
        product = cls._context_product(context)
        market = cls.market_intelligence(db, product=product, province=(context or {}).get("province"))
        recommendations = cls.recommendations(db, current_user, role, context=context)
        playbook = cls.ROLE_PLAYBOOKS[role]
        intent = cls._detect_intent(message)

        answer_parts = [
            f"{role.title()} AI guidance for {current_user.full_name}:",
            cls._intent_guidance(role, intent, market, recommendations),
        ]

        return {
            "assistant": f"{role}_ai",
            "mode": "deterministic_advisory",
            "intent": intent,
            "answer": " ".join(answer_parts),
            "focus_areas": playbook["focus"],
            "recommended_actions": recommendations["actions"],
            "market_context": market,
            "safety": {
                "human_review_required": role in {"admin", "agent"} or intent in {"dispute", "credit"},
                "not_financial_advice": intent == "credit",
                "model_provider": "rules_engine",
            },
        }

    @classmethod
    def recommendations(
        cls,
        db: Session,
        current_user: User,
        assistant_role: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        role = cls.normalize_assistant_role(assistant_role or cls._role_to_assistant(current_user.role))
        actions = list(cls.ROLE_PLAYBOOKS[role]["actions"])
        product = cls._context_product(context)

        if product:
            prediction = get_price_prediction(db, product, province=(context or {}).get("province"))
            actions.insert(0, f"For {product}, current forecast trend is {prediction.get('trend', 'STABLE')}.")

        if current_user.trust_score < 40:
            actions.insert(0, "Improve trust score before high-value transactions: complete verification and close pending orders cleanly.")
        if current_user.risk_score > 70:
            actions.insert(0, "Reduce risk flags before requesting premium services or credit.")

        return {
            "assistant": f"{role}_ai",
            "user_id": str(current_user.id),
            "trust_score": current_user.trust_score,
            "risk_score": current_user.risk_score,
            "actions": actions,
        }

    @classmethod
    def market_intelligence(
        cls,
        db: Session,
        product: Optional[str] = None,
        province: Optional[str] = None,
    ) -> Dict[str, Any]:
        listing_query = db.query(Listing).filter(Listing.status == ListingStatus.ACTIVE)
        offer_query = db.query(Offer).join(Listing)

        if product:
            listing_query = listing_query.filter(
                or_(
                    Listing.product_type.ilike(f"%{product}%"),
                    Listing.product_subtype.ilike(f"%{product}%"),
                    cast(Listing.sector, String).ilike(f"%{product}%"),
                    Listing.crop.ilike(f"%{product}%"),
                    Listing.crop_type.ilike(f"%{product}%"),
                )
            )
            offer_query = offer_query.filter(
                or_(
                    Listing.product_type.ilike(f"%{product}%"),
                    Listing.product_subtype.ilike(f"%{product}%"),
                    cast(Listing.sector, String).ilike(f"%{product}%"),
                    Listing.crop.ilike(f"%{product}%"),
                    Listing.crop_type.ilike(f"%{product}%"),
                )
            )
        if province:
            listing_query = listing_query.filter(Listing.location_province.ilike(f"%{province}%"))
            offer_query = offer_query.filter(Listing.location_province.ilike(f"%{province}%"))

        supply_quantity = listing_query.with_entities(func.sum(Listing.quantity)).scalar() or 0
        active_listing_count = listing_query.count()
        demand_quantity = offer_query.with_entities(func.sum(Offer.offered_quantity_kg)).scalar() or 0
        avg_price = listing_query.with_entities(func.avg(Listing.price_per_unit)).scalar() or 0

        demand_index = float(demand_quantity) / float(supply_quantity) * 10 if supply_quantity else 0.0
        status = "HIGH" if demand_index > 7 else "MODERATE" if demand_index > 3 else "LOW"
        if active_listing_count and not demand_quantity:
            status = "SUPPLY_HEAVY"

        return {
            "product": product or "all",
            "crop": product or "all",
            "province": province or "all",
            "active_listings": active_listing_count,
            "total_supply": round(float(supply_quantity), 2),
            "total_demand": round(float(demand_quantity), 2),
            "average_price": round(float(avg_price), 2),
            "demand_index": round(demand_index, 2),
            "status": status,
            "demand_signal": status,
            "trend": status,
            "recommendation": cls._market_recommendation(status),
        }

    @classmethod
    def price_and_demand_prediction(
        cls,
        db: Session,
        product: str,
        province: Optional[str] = None,
        days_ahead: int = 30,
    ) -> Dict[str, Any]:
        market = cls.market_intelligence(db, product=product, province=province)
        price = get_price_prediction(db, product, province=province, days_ahead=days_ahead)
        days = max(1, min(days_ahead, 90))
        demand_confidence = "medium" if market["active_listings"] >= 5 else "low"
        price_confidence = price.get("accuracy_rating", "low")

        return {
            "product": product,
            "crop": product,
            "province": province or "all",
            "days_ahead": days,
            "predicted_price": price.get("predicted_price") or price.get("forecast_30d"),
            "price_trend": price.get("trend", "STABLE"),
            "demand_signal": market["status"],
            "confidence": price_confidence if price_confidence != "low" else demand_confidence,
            "model_type": price.get("model_type", "market_history_weighted_forecast"),
            "training_status": price.get("training_status", "data_backed_not_ml_trained"),
            "data_source": price.get("data_source"),
            "sample_size": price.get("sample_size", 0),
            "price_prediction": price,
            "demand_prediction": {
                "status": market["status"],
                "demand_index": market["demand_index"],
                "confidence": demand_confidence,
                "active_listings": market["active_listings"],
                "total_supply": market["total_supply"],
                "total_demand": market["total_demand"],
            },
            "recommended_action": cls._prediction_action(market["status"], price.get("trend", "STABLE")),
        }

    @classmethod
    def dispute_resolution_suggestion(cls, db: Session, dispute_id: str) -> Dict[str, Any]:
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise ValueError("Dispute not found")

        description = f"{dispute.type} {dispute.description}".lower()
        refund = 0.0
        discount = 0.0
        action = "manual_review"
        memo = dispute.ai_recommendation

        if any(term in description for term in ["quality", "grade", "damaged", "spoiled"]):
            discount = 15.0
            refund = round(float(dispute.amount) * 0.15, 2)
            action = "agent_regrade_or_discount"
        elif any(term in description for term in ["quantity", "short", "weight", "missing"]):
            discount = 10.0
            refund = round(float(dispute.amount) * 0.10, 2)
            action = "partial_refund_after_weight_check"
        elif any(term in description for term in ["late", "delivery", "transport"]):
            discount = 5.0
            refund = round(float(dispute.amount) * 0.05, 2)
            action = "logistics_fee_adjustment"

        return {
            "dispute_id": str(dispute.id),
            "status": dispute.status.value if hasattr(dispute.status, "value") else str(dispute.status),
            "risk_score": cls._dispute_risk(dispute),
            "recommended_action": action,
            "proposed_discount": discount,
            "proposed_refund_amount": refund,
            "memo": memo,
            "requires_agent_review": True,
        }

    @classmethod
    def _role_to_assistant(cls, role: UserRole) -> str:
        mapping = {
            UserRole.FARMER: "farmer",
            UserRole.BUYER: "buyer",
            UserRole.SUPPLIER: "supplier",
            UserRole.AGENT: "agent",
            UserRole.ADMIN: "admin",
            UserRole.SUPER_ADMIN: "admin",
            UserRole.REGIONAL_ADMIN: "admin",
            UserRole.REGIONAL_MANAGER: "admin",
            UserRole.FINANCE_ADMIN: "admin",
            UserRole.SYSTEM_ADMIN: "admin",
        }
        return mapping.get(role, "buyer")

    @staticmethod
    def _context_product(context: Optional[Dict[str, Any]]) -> Optional[str]:
        if not context:
            return None
        value = (
            context.get("product")
            or context.get("agriculture_product")
            or context.get("commodity")
            or context.get("crop")
            or context.get("sector")
        )
        return str(value).strip() if value else None

    @staticmethod
    def _detect_intent(message: str) -> str:
        text = message.lower()
        if any(word in text for word in ["loan", "credit", "advance", "finance"]):
            return "credit"
        if any(word in text for word in ["dispute", "refund", "complaint", "quality"]):
            return "dispute"
        if any(word in text for word in ["price", "forecast", "demand", "market"]):
            return "market"
        if any(word in text for word in ["delivery", "transport", "driver", "pickup"]):
            return "logistics"
        return "general"

    @classmethod
    def _intent_guidance(
        cls,
        role: str,
        intent: str,
        market: Dict[str, Any],
        recommendations: Dict[str, Any],
    ) -> str:
        if intent == "market":
            return f"Market status is {market['status']} with demand index {market['demand_index']}. {market['recommendation']}"
        if intent == "credit":
            return "Use platform history before lending: wallet activity, completed orders, trust score, and open disputes should drive eligibility."
        if intent == "dispute":
            return "Collect evidence first, preserve escrow, and use an agent-reviewed settlement before releasing funds."
        if intent == "logistics":
            return "Use platform delivery for high-value, perishable, or long-distance orders and keep pickup proof attached."
        return recommendations["actions"][0] if recommendations["actions"] else cls.ROLE_PLAYBOOKS[role]["actions"][0]

    @staticmethod
    def _market_recommendation(status: str) -> str:
        if status == "HIGH":
            return "Strong buyer demand. Sellers can list confidently; buyers should secure supply early."
        if status == "MODERATE":
            return "Balanced market. Negotiate around verified quality, transport cost, and trust score."
        if status == "SUPPLY_HEAVY":
            return "Supply is ahead of demand. Consider boosting listings, adjusting price, or targeting buyers by district."
        return "Low observed demand. Hold stock if storage allows or use subscriptions/alerts to find buyers."

    @staticmethod
    def _prediction_action(demand_status: str, price_trend: str) -> str:
        if demand_status == "HIGH":
            return "Sell or source quickly; demand pressure is elevated."
        if price_trend.upper() == "UP":
            return "Prices are trending upward; sellers can list confidently and buyers should secure supply early."
        if price_trend.upper() == "DOWN":
            return "Prices are softening; buyers can negotiate while sellers should improve quality, delivery, or price."
        if price_trend.upper() == "STABLE":
            return "Use verified quality and delivery terms to improve conversion rather than waiting on price movement."
        return "Monitor market movement and set alerts before committing to large orders."

    @staticmethod
    def _dispute_risk(dispute: Dispute) -> int:
        risk = 35
        if dispute.amount > 500:
            risk += 20
        if dispute.buyer_trust < 40 or dispute.seller_trust < 40:
            risk += 20
        if dispute.status.value in {"escalated", "under_review"}:
            risk += 15
        return min(risk, 100)


ai_assistant_service = AIAssistantService()
