import joblib
import os
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

class RiskScorer:
    """
    Multi-factor risk scoring engine.
    Scores are derived from real user behaviour in the database:
    transaction velocity, dispute history, cancellation rate,
    verification tier, and trust score.
    """
    def __init__(self, db=None):
        self.db = db

    def calculate_risk_score(self, user_id: int) -> Dict[str, Any]:
        from app.models.user import User
        from app.models.transaction import Order, OrderStatus
        from app.models.dispute import Dispute

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"risk_score": 100, "status": "HARD_BLOCK", "recommendation": "Reject Access"}

        # ── 1. Transaction velocity (last 24 h) ──────────────────────────
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_orders = self.db.query(Order).filter(
            (Order.buyer_id == user_id) | (Order.seller_id == user_id),
            Order.created_at >= cutoff
        ).count()
        # >10 orders in 24 h is unusual for a smallholder marketplace
        velocity_penalty = min(30, recent_orders * 3)

        # ── 2. Dispute rate ───────────────────────────────────────────────
        total_orders = self.db.query(Order).filter(
            (Order.buyer_id == user_id) | (Order.seller_id == user_id)
        ).count()
        dispute_count = self.db.query(Dispute).join(Order, Dispute.order_id == Order.id).filter(
            (Order.buyer_id == user_id) | (Order.seller_id == user_id)
        ).count()
        dispute_rate = (dispute_count / total_orders) if total_orders > 0 else 0.0
        dispute_penalty = min(25, dispute_rate * 100)

        # ── 3. Cancellation / refund rate ────────────────────────────────
        refunded = self.db.query(Order).filter(
            (Order.buyer_id == user_id) | (Order.seller_id == user_id),
            Order.status == OrderStatus.REFUNDED
        ).count()
        cancel_rate = (refunded / total_orders) if total_orders > 0 else 0.0
        cancel_penalty = min(20, cancel_rate * 80)

        # ── 4. Trust score contribution ──────────────────────────────────
        trust = float(user.trust_score or 50)
        trust_penalty = max(0, (50 - trust) * 0.5)  # penalty only below 50

        # ── 5. Verification bonus (reduces risk) ─────────────────────────
        verification_bonus = 0
        if user.is_verified:
            verification_bonus = 10
        if getattr(user, 'verification_tier', None) in ('FULL', 'PREMIUM'):
            verification_bonus = 15

        # ── Final score ───────────────────────────────────────────────────
        risk_score = velocity_penalty + dispute_penalty + cancel_penalty + trust_penalty - verification_bonus
        risk_score = max(0.0, min(100.0, round(risk_score, 2)))

        if risk_score > 70:
            status = "HARD_BLOCK"
            recommendation = "Account flagged — manual review required"
        elif risk_score > 45:
            status = "SOFT_BLOCK"
            recommendation = "ID re-verification required"
        elif risk_score > 20:
            status = "MONITORED"
            recommendation = "Escrow enforcement active"
        else:
            status = "VERIFIED"
            recommendation = "Allow transaction"

        return {
            "risk_score": risk_score,
            "status": status,
            "recommendation": recommendation,
            "risk_level": status,
            "metrics": {
                "velocity_penalty": velocity_penalty,
                "dispute_penalty": round(dispute_penalty, 2),
                "cancel_penalty": round(cancel_penalty, 2),
                "trust_penalty": round(trust_penalty, 2),
                "verification_bonus": verification_bonus,
            },
            "audit_timestamp": datetime.utcnow().isoformat()
        }

    def train(self, behavioral_log_path: str):
        """Placeholder — risk scoring uses live DB queries, no weights file needed."""
        return {"status": "ok", "note": "Risk scorer uses live DB queries — no training required."}

# Production instance (db injected per-request via risk_service)
risk_engine = RiskScorer()
