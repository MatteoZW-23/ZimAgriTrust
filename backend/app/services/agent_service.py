from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict

from app.models.agent import Agent, AgentAssignment, AgentStatus
from app.models.report import ListingVerificationReport, DeliveryReport
from app.models.listing import Listing, ListingStatus
from app.models.transaction import Order, OrderStatus
from app.models.user import User
from app.schemas.report import VerificationReportCreate, DeliveryReportCreate


class AgentService:
    @staticmethod
    def submit_verification_report(db: Session, payload: VerificationReportCreate, agent_user: User):
        # Verify assignment
        assignment = db.query(AgentAssignment).filter(
            AgentAssignment.id == payload.assignment_id,
            AgentAssignment.status == "accepted"
        ).first()
        
        if not assignment:
             raise HTTPException(status_code=404, detail="Active assignment not found")

        # Create report
        report = ListingVerificationReport(
            **payload.model_dump(),
            agent_id=assignment.agent_id
        )
        db.add(report)

        # Update assignment
        assignment.status = "completed"
        assignment.completed_at = datetime.now()
        
        # Update listing
        listing = db.query(Listing).filter(Listing.id == payload.listing_id).first()
        if listing:
            listing.verification_status = "verified" if payload.is_approved else "rejected"
            if not payload.exists:
                listing.status = ListingStatus.SUSPENDED
            
            # Track which agent verified for commission calculation
            listing.verified_by_agent_id = assignment.agent_id
            listing.verified_by_ai = False
            
            # Update quantity and grade if agent provided new info
            listing.quantity = payload.verified_quantity
            listing.grade = payload.matching_grade
            listing.latitude = payload.latitude
            listing.longitude = payload.longitude
            listing.is_location_verified = True

        # Handle agent workload
        agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
        if agent:
            agent.current_load = max(0, agent.current_load - 1)
            agent.status = AgentStatus.ACTIVE if agent.current_load < 3 else AgentStatus.BUSY

        # Payout logic (simulated call to earnings service)
        from app.services.agent_earnings_service import AgentEarningsService
        AgentEarningsService.finalize_earnings(db, assignment)

        db.commit()
        return report

    @staticmethod
    def submit_delivery_confirmation(db: Session, payload: DeliveryReportCreate, agent_user: User):
        # Verify assignment
        assignment = db.query(AgentAssignment).filter(
            AgentAssignment.id == payload.assignment_id,
            AgentAssignment.status == "accepted"
        ).first()
        
        if not assignment:
             raise HTTPException(status_code=404, detail="Active assignment not found")

        # Create report
        report = DeliveryReport(
            **payload.model_dump(),
            agent_id=assignment.agent_id
        )
        db.add(report)

        # Update assignment
        assignment.status = "completed"
        assignment.completed_at = datetime.now()
        
        # Update Order
        order = db.query(Order).filter(Order.id == payload.order_id).first()
        if order:
            if payload.is_complete:
                order.status = OrderStatus.DELIVERED
                # Track which agent fulfilled for commission calculation
                order.fulfilled_by_agent_id = assignment.agent_id
            else:
                order.status = OrderStatus.DISPUTED # If agent flags issues

        # Handle agent workload
        agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
        if agent:
            agent.current_load = max(0, agent.current_load - 1)
            agent.status = AgentStatus.ACTIVE if agent.current_load < 3 else AgentStatus.BUSY

        # Payout logic
        from app.services.agent_earnings_service import AgentEarningsService
        AgentEarningsService.finalize_earnings(db, assignment)

        db.commit()
        return {
            "report_id": report.id,
            "ai_analysis": AgentService._analyze_listing_photos(payload.photos)
        }

    @staticmethod
    def _analyze_listing_photos(photos: List[str]) -> Dict:
        """
        AI Photo Analysis — integrate with vision service for real analysis.
        Returns empty result until vision model is connected.
        """
        return {
            "detected_produce": None,
            "quality_confidence": None,
            "anomalies_detected": None,
            "suggested_grade": None,
            "gps_metadata_match": None
        }

    @staticmethod
    def get_assigned_tasks(db: Session, agent_id: uuid.UUID) -> List[AgentAssignment]:
        return db.query(AgentAssignment).filter(
            AgentAssignment.agent_id == agent_id,
            AgentAssignment.status.in_(["assigned", "accepted"])
        ).all()

    @staticmethod
    def accept_task(db: Session, assignment_id: uuid.UUID, agent_user: User):
        assignment = db.query(AgentAssignment).filter(AgentAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        assignment.status = "accepted"
        assignment.accepted_at = datetime.now()
        db.commit()
        return assignment

    @staticmethod
    def log_support_activity(db: Session, agent_user: User, activity_type: str, farmer_id: uuid.UUID, notes: str):
        """Log support and training activities performed by agents"""
        # This could be stored in a new SupportActivity model, for now we log it in SystemAudit or similar
        from app.models.system_audit import SystemAudit
        
        agent = db.query(Agent).filter(Agent.user_id == agent_user.id).first()
        
        audit = SystemAudit(
            action=f"AGENT_SUPPORT_{activity_type.upper()}",
            user_id=agent_user.id,
            details={
                "agent_id": str(agent.id) if agent else None,
                "farmer_id": str(farmer_id),
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            }
        )
        db.add(audit)
        
        # Give a small bounty for support tasks if they are assigned (optional)
        db.commit()
        return {"status": "activity logged"}

    # ────────────────────────────────────────────────────────────────────────
    # Certification level auto-promotion
    # ────────────────────────────────────────────────────────────────────────
    @staticmethod
    def evaluate_promotion(db: Session, agent_id: uuid.UUID) -> dict:
        """
        Re-evaluate an agent's certification level based on tenure, task volume,
        accuracy, and rating. Idempotent — only ever promotes upward.

        Promotion rules (per spec Part 1.1):
          • SENIOR : 6 months tenure + 200 successful tasks + 95% accuracy + 4.5 rating
          • MASTER : 12 months tenure + 500 successful tasks + 98% accuracy + 4.8 rating

        Returns a dict describing the action taken.
        """
        from datetime import datetime, timezone, timezone, timedelta
        from app.models.agent import Agent
        from app.models.academy import AgentTraining, CertificationLevel

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return {"promoted": False, "reason": "agent not found"}

        training = db.query(AgentTraining).filter(AgentTraining.agent_id == agent.id).first()
        if not training or training.certification_level == CertificationLevel.TRAINEE:
            return {"promoted": False, "reason": "agent not certified yet"}

        # Tenure
        certified_at = training.certified_at
        if not certified_at:
            return {"promoted": False, "reason": "no certification date"}
        if certified_at.tzinfo is None:
            certified_at = certified_at.replace(tzinfo=timezone.utc)
        tenure = datetime.now(timezone.utc) - certified_at

        # Successful tasks + accuracy from agent_assignments
        successful_tasks = db.query(AgentAssignment).filter(
            AgentAssignment.agent_id == agent.id,
            AgentAssignment.status == "completed",
        ).count()
        total_tasks = db.query(AgentAssignment).filter(
            AgentAssignment.agent_id == agent.id,
            AgentAssignment.status.in_(["completed", "rejected", "failed"]),
        ).count()
        accuracy = (successful_tasks / total_tasks * 100) if total_tasks else 0
        rating = agent.rating or 0

        target_level = training.certification_level
        if (
            tenure >= timedelta(days=365)
            and successful_tasks >= 500
            and accuracy >= 98
            and rating >= 4.8
        ):
            target_level = CertificationLevel.MASTER
        elif (
            tenure >= timedelta(days=180)
            and successful_tasks >= 200
            and accuracy >= 95
            and rating >= 4.5
        ):
            # Only promote upward — do not demote MASTER back to SENIOR
            if training.certification_level != CertificationLevel.MASTER:
                target_level = CertificationLevel.SENIOR

        if target_level == training.certification_level:
            return {
                "promoted": False,
                "current_level": training.certification_level.value,
                "tenure_days": tenure.days,
                "successful_tasks": successful_tasks,
                "accuracy": round(accuracy, 2),
                "rating": rating,
            }

        prior = training.certification_level
        training.certification_level = target_level
        db.commit()
        return {
            "promoted": True,
            "from": prior.value,
            "to": target_level.value,
            "tenure_days": tenure.days,
            "successful_tasks": successful_tasks,
            "accuracy": round(accuracy, 2),
            "rating": rating,
        }
