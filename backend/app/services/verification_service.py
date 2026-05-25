import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List

from sqlalchemy.orm import Session

from app.models.user import User, UserRole, TrustScoreEvent
from app.models.transaction import Order, OrderStatus
from app.models.listing import Listing
from app.models.dispute import Dispute

logger = logging.getLogger(__name__)


class VerificationService:
    """
    Handles verification flows for all user types and manages trust score updates.
    """
    
    # Trust score constants per user type and action
    TRUST_SCORES = {
        UserRole.FARMER: {
            "phone_verified": 5,
            "id_verified": 15,
            "location_verified": 20,
            "first_transaction": 10,
            "positive_rating": 5,
            "milestone_5_transactions": 10,
            "dispute_raised": -15,
            "dispute_ruled_against": -20,
            "inactive_30_days": -5,
            "inactive_60_days": -10,
            "fraudulent_listing": -50,
            "no_delivery": -40,
            "wrong_quality": -15,
            "multiple_disputes_3plus": -5,
        },
        UserRole.BUYER: {
            "phone_verified": 5,
            "id_verified": 15,
            "business_verified": 25,
            "first_purchase": 10,
            "positive_rating": 5,
            "on_time_payment": 2,
            "dispute_raised": -15,
            "dispute_ruled_against": -20,
            "payment_failure": -10,
            "false_dispute": -25,
            "chargeback": -30,
        },
        UserRole.AGENT: {
            "phone_verified": 5,
            "id_verified": 15,
            "background_cleared": 10,
            "module_completed": 2,
            "final_exam_passed": 20,
            "practical_passed": 15,
            "shadowing_complete": 10,
            "accurate_verification_10": 1,
            "positive_farmer_rating": 2,
            "verification_error": -5,
            "incorrect_grading": -10,
            "missing_gps_photo": -5,
            "dispute_caused_by_error": -20,
            "slow_response_24h": -3,
            "bribery_complaint": -50,
            "fraudulent_verification": -100,
        },
    }
    
    # Recovery actions
    RECOVERY = {
        UserRole.FARMER: {
            "successful_transaction": 2,
            "positive_rating": 5,
            "no_disputes_30_days": 10,
        },
        UserRole.BUYER: {
            "successful_purchase": 2,
            "on_time_payment": 1,
        },
        UserRole.AGENT: {
            "accurate_verification_10": 1,
            "positive_farmer_rating": 2,
            "refresher_training": 15,
        },
    }
    
    @staticmethod
    def _record_trust_event(db: Session, user: User, delta: int, reason: str, details: Optional[str] = None, triggered_by: Optional[str] = "system") -> None:
        """Record a trust score change event in the audit log."""
        previous = user.trust_score
        new_score = max(0, min(100, previous + delta))
        user.trust_score = new_score
        
        event = TrustScoreEvent(
            user_id=user.id,
            previous_score=previous,
            new_score=new_score,
            delta=delta,
            reason=reason,
            details=details,
            triggered_by=triggered_by,
        )
        db.add(event)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Trust score update: user={user.id}, {previous} -> {new_score} ({delta:+d}) reason={reason}")
    
    @classmethod
    def get_initial_trust(cls, user: User) -> int:
        """Calculate initial trust score based on verified items at registration."""
        score = 0
        role_scores = cls.TRUST_SCORES.get(user.role, {})
        
        if user.is_phone_verified and "phone_verified" in role_scores:
            score += role_scores["phone_verified"]
        if user.id_verified and "id_verified" in role_scores:
            score += role_scores["id_verified"]
        if user.is_location_verified and "location_verified" in role_scores:
            score += role_scores["location_verified"]
        if user.business_verified and "business_verified" in role_scores:
            score += role_scores["business_verified"]
        if user.background_verified and "background_cleared" in role_scores:
            score += role_scores["background_cleared"]
        if user.training_completed and "final_exam_passed" in role_scores:
            score += role_scores["final_exam_passed"]
        if user.practical_passed and "practical_passed" in role_scores:
            score += role_scores["practical_passed"]
        if user.shadowing_complete and "shadowing_complete" in role_scores:
            score += role_scores["shadowing_complete"]
        
        return min(100, score)
    
    # --- PHONE VERIFICATION ---
    @classmethod
    def verify_phone(cls, db: Session, user: User) -> Dict:
        if user.is_phone_verified:
            return {"success": True, "message": "Phone already verified.", "delta": 0}
        
        user.is_phone_verified = True
        user.phone_verified_at = datetime.now(timezone.utc)
        
        delta = cls.TRUST_SCORES.get(user.role, {}).get("phone_verified", 5)
        cls._record_trust_event(db, user, delta, "Phone verified via OTP", triggered_by="system")
        
        return {"success": True, "message": f"Phone verified! Trust Score +{delta}", "delta": delta}
    
    # --- IDENTITY VERIFICATION ---
    @classmethod
    def verify_id(cls, db: Session, user: User, approved: bool = True, notes: Optional[str] = None) -> Dict:
        if approved:
            if user.id_verified:
                return {"success": True, "message": "ID already verified.", "delta": 0}
            
            user.id_verified = True
            user.id_verified_at = datetime.now(timezone.utc)
            user.id_verification_notes = notes
            
            delta = cls.TRUST_SCORES.get(user.role, {}).get("id_verified", 15)
            cls._record_trust_event(db, user, delta, "Identity verified by admin", triggered_by="admin")
            
            return {"success": True, "message": f"Identity verified! Trust Score +{delta}", "delta": delta}
        else:
            user.id_verification_notes = notes or "ID rejected. Please upload a clearer photo."
            return {"success": False, "message": "ID verification rejected.", "delta": 0}
    
    # --- LOCATION / FARM VERIFICATION ---
    @classmethod
    def verify_location(cls, db: Session, user: User, approved: bool = True, notes: Optional[str] = None) -> Dict:
        if user.role != UserRole.FARMER and user.role != UserRole.AGENT:
            return {"success": False, "message": "Location verification not applicable.", "delta": 0}
        
        if approved:
            if user.is_location_verified:
                return {"success": True, "message": "Location already verified.", "delta": 0}
            
            user.is_location_verified = True
            user.location_verified_at = datetime.now(timezone.utc)
            
            delta = cls.TRUST_SCORES.get(user.role, {}).get("location_verified", 20)
            cls._record_trust_event(db, user, delta, "Farm/location verified by agent", triggered_by="agent")
            
            return {"success": True, "message": f"Location verified! Trust Score +{delta}", "delta": delta}
        else:
            return {"success": False, "message": "Location verification rejected.", "delta": 0}
    
    # --- BUYER BUSINESS VERIFICATION ---
    @classmethod
    def verify_business(cls, db: Session, user: User, approved: bool = True) -> Dict:
        if user.role != UserRole.BUYER:
            return {"success": False, "message": "Business verification only for buyers.", "delta": 0}
        
        if approved:
            if user.business_verified:
                return {"success": True, "message": "Business already verified.", "delta": 0}
            
            user.business_verified = True
            user.business_verified_at = datetime.now(timezone.utc)
            
            delta = cls.TRUST_SCORES.get(UserRole.BUYER, {}).get("business_verified", 25)
            cls._record_trust_event(db, user, delta, "Business account verified by admin", triggered_by="admin")
            
            return {"success": True, "message": f"Business verified! Trust Score +{delta}", "delta": delta}
        else:
            return {"success": False, "message": "Business verification rejected.", "delta": 0}
    
    # --- AGENT VERIFICATION STAGES ---
    @classmethod
    def verify_background(cls, db: Session, user: User, approved: bool = True) -> Dict:
        if user.role != UserRole.AGENT:
            return {"success": False, "message": "Background check only for agents.", "delta": 0}
        
        if approved:
            user.background_verified = True
            user.background_verified_at = datetime.now(timezone.utc)
            delta = cls.TRUST_SCORES.get(UserRole.AGENT, {}).get("background_cleared", 10)
            cls._record_trust_event(db, user, delta, "Background check cleared by admin", triggered_by="admin")
            return {"success": True, "message": f"Background check passed! Trust Score +{delta}", "delta": delta}
        else:
            return {"success": False, "message": "Background check failed.", "delta": 0}
    
    @classmethod
    def complete_training(cls, db: Session, user: User) -> Dict:
        if user.role != UserRole.AGENT:
            return {"success": False, "message": "Training only for agents.", "delta": 0}
        
        if user.training_completed:
            return {"success": True, "message": "Training already completed.", "delta": 0}
        
        user.training_completed = True
        user.training_completed_at = datetime.now(timezone.utc)
        delta = cls.TRUST_SCORES.get(UserRole.AGENT, {}).get("final_exam_passed", 20)
        cls._record_trust_event(db, user, delta, "Agent training completed and exam passed", triggered_by="admin")
        return {"success": True, "message": f"Training completed! Trust Score +{delta}", "delta": delta}
    
    @classmethod
    def complete_practical(cls, db: Session, user: User) -> Dict:
        if user.role != UserRole.AGENT:
            return {"success": False, "message": "Practical only for agents.", "delta": 0}
        
        if user.practical_passed:
            return {"success": True, "message": "Practical already passed.", "delta": 0}
        
        user.practical_passed = True
        user.practical_passed_at = datetime.now(timezone.utc)
        delta = cls.TRUST_SCORES.get(UserRole.AGENT, {}).get("practical_passed", 15)
        cls._record_trust_event(db, user, delta, "Practical assessment passed by senior agent", triggered_by="senior_agent")
        return {"success": True, "message": f"Practical passed! Trust Score +{delta}", "delta": delta}
    
    @classmethod
    def complete_shadowing(cls, db: Session, user: User) -> Dict:
        if user.role != UserRole.AGENT:
            return {"success": False, "message": "Shadowing only for agents.", "delta": 0}
        
        if user.shadowing_complete:
            return {"success": True, "message": "Shadowing already complete.", "delta": 0}
        
        user.shadowing_complete = True
        user.shadowing_complete_at = datetime.now(timezone.utc)
        delta = cls.TRUST_SCORES.get(UserRole.AGENT, {}).get("shadowing_complete", 10)
        cls._record_trust_event(db, user, delta, "Shadowing period completed by senior agent", triggered_by="senior_agent")
        return {"success": True, "message": f"Shadowing complete! Trust Score +{delta}", "delta": delta}
    
    # --- TRANSACTION-BASED TRUST UPDATES ---
    @classmethod
    def record_first_transaction(cls, db: Session, user: User) -> Dict:
        role_key = "first_transaction" if user.role == UserRole.FARMER else "first_purchase"
        delta = cls.TRUST_SCORES.get(user.role, {}).get(role_key, 10)
        cls._record_trust_event(db, user, delta, f"First {user.role.value} transaction completed", triggered_by="system")
        return {"success": True, "message": f"First transaction complete! Trust Score +{delta}", "delta": delta}
    
    @classmethod
    def record_positive_rating(cls, db: Session, user: User, rater_role: UserRole) -> Dict:
        role_key = "positive_rating" if user.role == UserRole.FARMER else "positive_farmer_rating" if user.role == UserRole.AGENT else "positive_rating"
        delta = cls.TRUST_SCORES.get(user.role, {}).get(role_key, 5)
        cls._record_trust_event(db, user, delta, f"Positive rating received from {rater_role.value}", triggered_by=rater_role.value)
        return {"success": True, "message": f"Positive rating! Trust Score +{delta}", "delta": delta}
    
    @classmethod
    def record_payment_on_time(cls, db: Session, user: User) -> Dict:
        if user.role != UserRole.BUYER:
            return {"success": False, "message": "Only for buyers.", "delta": 0}
        delta = cls.TRUST_SCORES.get(UserRole.BUYER, {}).get("on_time_payment", 2)
        cls._record_trust_event(db, user, delta, "Payment confirmed on time", triggered_by="system")
        return {"success": True, "message": f"Payment confirmed! Trust Score +{delta}", "delta": delta}
    
    @classmethod
    def record_milestone(cls, db: Session, user: User, milestone_type: str) -> Dict:
        if milestone_type == "5_transactions" and user.role == UserRole.FARMER:
            delta = cls.TRUST_SCORES.get(UserRole.FARMER, {}).get("milestone_5_transactions", 10)
            cls._record_trust_event(db, user, delta, "Milestone: 5 successful trades", triggered_by="system")
            return {"success": True, "message": f"Milestone reached! Trust Score +{delta}", "delta": delta}
        
        if milestone_type == "100_verifications" and user.role == UserRole.AGENT:
            delta = cls.TRUST_SCORES.get(UserRole.AGENT, {}).get("accurate_verification_10", 1)
            cls._record_trust_event(db, user, delta, "Milestone: 100 accurate verifications", triggered_by="system")
            return {"success": True, "message": f"Verification milestone! Trust Score +{delta}", "delta": delta}
        
        return {"success": False, "message": "Unknown milestone.", "delta": 0}
    
    # --- TRUST LOSS SCENARIOS ---
    @classmethod
    def apply_dispute_penalty(cls, db: Session, user: User, ruled_against: bool = False) -> Dict:
        role_scores = cls.TRUST_SCORES.get(user.role, {})
        delta = role_scores.get("dispute_ruled_against", -20) if ruled_against else role_scores.get("dispute_raised", -15)
        reason = "Dispute resolved against user" if ruled_against else "Dispute opened against user"
        cls._record_trust_event(db, user, delta, reason, triggered_by="admin" if ruled_against else "system")
        return {"success": True, "message": f"Trust Score {delta:+d} due to dispute.", "delta": delta}
    
    @classmethod
    def apply_fraud_penalty(cls, db: Session, user: User, fraud_type: str = "listing") -> Dict:
        role_scores = cls.TRUST_SCORES.get(user.role, {})
        
        if fraud_type == "listing" and user.role == UserRole.FARMER:
            delta = role_scores.get("fraudulent_listing", -50)
            cls._record_trust_event(db, user, delta, "Fraudulent listing detected and removed", triggered_by="admin")
        elif fraud_type == "verification" and user.role == UserRole.AGENT:
            delta = role_scores.get("fraudulent_verification", -100)
            cls._record_trust_event(db, user, delta, "Fraudulent verification detected", triggered_by="admin")
            user.is_suspended = True
            user.status_notes = "Agent privileges revoked permanently due to fraudulent verification."
        elif fraud_type == "false_dispute" and user.role == UserRole.BUYER:
            delta = role_scores.get("false_dispute", -25)
            cls._record_trust_event(db, user, delta, "False dispute detected", triggered_by="admin")
        else:
            delta = -50
            cls._record_trust_event(db, user, delta, f"Fraud activity detected: {fraud_type}", triggered_by="admin")
        
        db.commit()
        return {"success": True, "message": f"Trust Score {delta:+d} due to fraud penalty.", "delta": delta}
    
    @classmethod
    def apply_payment_failure(cls, db: Session, user: User) -> Dict:
        if user.role != UserRole.BUYER:
            return {"success": False, "message": "Only for buyers.", "delta": 0}
        delta = cls.TRUST_SCORES.get(UserRole.BUYER, {}).get("payment_failure", -10)
        cls._record_trust_event(db, user, delta, "Payment failed", triggered_by="system")
        return {"success": True, "message": f"Payment failed. Trust Score {delta:+d}", "delta": delta}
    
    @classmethod
    def apply_inactivity_penalty(cls, db: Session, user: User, days: int) -> Dict:
        role_scores = cls.TRUST_SCORES.get(user.role, {})
        
        if days >= 60:
            delta = role_scores.get("inactive_60_days", -10)
        elif days >= 30:
            delta = role_scores.get("inactive_30_days", -5)
        else:
            return {"success": False, "message": "Inactivity period too short.", "delta": 0}
        
        cls._record_trust_event(db, user, delta, f"Inactivity penalty ({days} days)", triggered_by="system")
        return {"success": True, "message": f"Inactivity penalty applied. Trust Score {delta:+d}", "delta": delta}
    
    @classmethod
    def apply_agent_error(cls, db: Session, user: User, error_type: str) -> Dict:
        if user.role != UserRole.AGENT:
            return {"success": False, "message": "Only for agents.", "delta": 0}
        
        role_scores = cls.TRUST_SCORES.get(UserRole.AGENT, {})
        
        if error_type == "verification":
            delta = role_scores.get("verification_error", -5)
            reason = "Verification flagged for review"
        elif error_type == "grading":
            delta = role_scores.get("incorrect_grading", -10)
            reason = "Grade mismatch detected"
        elif error_type == "missing_gps":
            delta = role_scores.get("missing_gps_photo", -5)
            reason = "Missing GPS data in verification report"
        elif error_type == "dispute_caused":
            delta = role_scores.get("dispute_caused_by_error", -20)
            reason = "Dispute caused by verification error"
        elif error_type == "slow_response":
            delta = role_scores.get("slow_response_24h", -3)
            reason = "Task response time exceeded 24 hours"
        elif error_type == "bribery":
            delta = role_scores.get("bribery_complaint", -50)
            reason = "Bribery complaint received"
            user.is_suspended = True
            user.status_notes = "Account suspended pending investigation."
        else:
            delta = -5
            reason = f"Agent error: {error_type}"
        
        cls._record_trust_event(db, user, delta, reason, triggered_by="admin")
        db.commit()
        return {"success": True, "message": f"{reason}. Trust Score {delta:+d}", "delta": delta}
    
    # --- RECOVERY ---
    @classmethod
    def apply_recovery(cls, db: Session, user: User, recovery_type: str) -> Dict:
        role_recovery = cls.RECOVERY.get(user.role, {})
        delta = role_recovery.get(recovery_type, 0)
        
        if delta == 0:
            return {"success": False, "message": "Unknown recovery type.", "delta": 0}
        
        cls._record_trust_event(db, user, delta, f"Trust recovery: {recovery_type}", triggered_by="system")
        return {"success": True, "message": f"Trust recovery applied! Trust Score +{delta}", "delta": delta}
    
    # --- UTILITY ---
    @classmethod
    def get_verification_status(cls, user: User) -> Dict:
        """Get complete verification status for any user type."""
        status = {
            "user_id": str(user.id),
            "role": user.role.value,
            "trust_score": user.trust_score,
            "phone_verified": user.is_phone_verified,
            "id_verified": user.id_verified,
            "location_verified": user.is_location_verified,
        }
        
        if user.role == UserRole.BUYER:
            status["business_verified"] = user.business_verified
        
        if user.role == UserRole.AGENT:
            status.update({
                "background_verified": user.background_verified,
                "training_completed": user.training_completed,
                "practical_passed": user.practical_passed,
                "shadowing_complete": user.shadowing_complete,
            })
        
        return status
    
    @classmethod
    def update_last_activity(cls, db: Session, user: User) -> None:
        """Update user's last activity timestamp."""
        user.last_activity_at = datetime.now(timezone.utc)
        db.commit()


verification_service = VerificationService()
