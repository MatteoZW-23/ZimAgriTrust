from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta, timezone
from typing import List
import logging
import enum

from app.models.agent import Agent, AgentStatus
from app.models.onboarding import AgentTrainingProgress
from app.services.whatsapp_service import WhatsAppService
from app.services.email_service import email_service
from app.services.notification_service import notification_service


class CertificationLevel(str, enum.Enum):
    NOT_CERTIFIED = "not_certified"
    CERTIFIED = "certified"
    EXPIRED = "expired"

logger = logging.getLogger(__name__)


class CertificationService:
    """Service for certification expiry tracking and renewal notifications"""
    
    @staticmethod
    def check_certification_expiry(db: Session) -> dict:
        """
        Check all certifications for expiry and send notifications
        
        Returns summary of checks performed
        """
        now = datetime.now(timezone.utc)
        
        trainings = db.query(AgentTrainingProgress).filter(
            AgentTrainingProgress.certification_expires_at.isnot(None),
            or_(
                AgentTrainingProgress.certification_status == "certified",
                AgentTrainingProgress.certification_status == "active"
            )
        ).all()
        
        summary = {
            "total_checked": len(trainings),
            "notifications_sent": 0,
            "expired_count": 0,
            "expiring_soon": {
                "30_days": 0,
                "14_days": 0,
                "7_days": 0,
                "1_day": 0
            }
        }
        
        for training in trainings:
            agent = db.query(Agent).filter(Agent.id == training.application_id).first()
            if not agent or not agent.user:
                continue
            
            days_until_expiry = (training.certification_expires_at - now).days
            
            # Check if already expired
            if days_until_expiry <= 0:
                summary["expired_count"] += 1
                CertificationService._handle_expired_certification(db, agent, training)
                continue
            
            # Send expiry reminders
            if days_until_expiry == 30:
                summary["expiring_soon"]["30_days"] += 1
                CertificationService._send_expiry_reminder(agent, training, 30)
                summary["notifications_sent"] += 1
            
            elif days_until_expiry == 14:
                summary["expiring_soon"]["14_days"] += 1
                CertificationService._send_expiry_reminder(agent, training, 14)
                summary["notifications_sent"] += 1
            
            elif days_until_expiry == 7:
                summary["expiring_soon"]["7_days"] += 1
                CertificationService._send_expiry_reminder(agent, training, 7)
                summary["notifications_sent"] += 1
            
            elif days_until_expiry == 1:
                summary["expiring_soon"]["1_day"] += 1
                CertificationService._send_expiry_reminder(agent, training, 1)
                summary["notifications_sent"] += 1
        
        db.commit()
        return summary
    
    @staticmethod
    def _handle_expired_certification(db: Session, agent: Agent, training: AgentTrainingProgress):
        """Handle expired certification by suspending agent"""
        training.certification_status = "expired"
        training.review_required = True
        agent.status = AgentStatus.SUSPENDED
    
    @staticmethod
    def _send_expiry_reminder(agent: Agent, training: AgentTrainingProgress, days_remaining: int):
        """Send certification expiry reminder"""
        try:
            if agent.user and agent.user.phone_number:
                WhatsAppService.send_message(
                    agent.user.phone_number,
                    f"Certification expires in {days_remaining} day(s). Complete renewal in academy."
                )
            if agent.user and agent.user.email:
                email_service.send_email(
                    to_email=agent.user.email,
                    subject="Certification Renewal Required",
                    html_content=f"Your certification expires in {days_remaining} day(s). Please renew immediately."
                )
            notification_service.create_notification(
                db=None,
                user_id=agent.user_id,
                title="Certification Renewal Required",
                message=f"Your certification expires in {days_remaining} day(s).",
                notification_type="certification_expiry"
            )
        except Exception:
            logger.exception("Failed to send one or more certification reminders")
    
    @staticmethod
    def renew_certification(db: Session, agent_id: str, renewal_days: int = 365) -> dict:
        """
        Renew an agent's certification
        
        Args:
            db: Database session
            agent_id: Agent UUID
            renewal_days: Number of days to extend (default 365)
        
        Returns:
            Updated certification details
        """
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError("Agent not found")
        
        training = db.query(AgentTrainingProgress).filter(
            AgentTrainingProgress.application_id == agent.id
        ).order_by(AgentTrainingProgress.updated_at.desc() if hasattr(AgentTrainingProgress, "updated_at") else AgentTrainingProgress.id.desc()).first()
        if not training:
            raise ValueError("Training record not found")
        now = datetime.now(timezone.utc)
        training.certification_status = "certified"
        training.review_required = False
        training.certification_issued_at = now
        training.certification_expires_at = now + timedelta(days=renewal_days)
        agent.status = AgentStatus.ACTIVE
        db.commit()
        return {
            "agent_id": str(agent.id),
            "status": training.certification_status,
            "issued_at": training.certification_issued_at,
            "expires_at": training.certification_expires_at
        }


certification_service = CertificationService()
