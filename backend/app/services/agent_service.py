from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
from datetime import datetime
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
        AI Photo Analysis (Mock): 
        Pre-screens crop photos for quality issues or fraud before agent review.
        """
        return {
            "detected_produce": "White Maize",
            "quality_confidence": 0.92,
            "anomalies_detected": False,
            "suggested_grade": "Grade A",
            "gps_metadata_match": True
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
