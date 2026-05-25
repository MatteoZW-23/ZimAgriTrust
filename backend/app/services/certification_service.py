from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List
import logging

from app.models.agent import Agent, AgentStatus
from app.models.academy import AgentTraining, CertificationLevel
from app.services.whatsapp_service import WhatsAppService
from app.services.email_service import email_service

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
        
        # Get all active agents with certifications
        trainings = db.query(AgentTraining).filter(
            AgentTraining.certification_level == CertificationLevel.CERTIFIED,
            AgentTraining.certification_expires_at.isnot(None)
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
            agent = db.query(Agent).filter(Agent.id == training.agent_id).first()
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
    def _handle_expired_certification(db: Session, agent: Agent, training: AgentTraining):
        """Handle expired certification by suspending agent"""
        agent.status = AgentStatus.SUSPENDED
        training.certification_level = CertificationLevel.TRAINEE
        
        # Send notification
        msg = (
            f"⚠️ *CERTIFICATION EXPIRED*\n\n"
            f"Dear {agent.user.full_name},\n\n"
            f"Your ZimAgritrust Field Agent certification has expired.\n\n"
            f"Your account has been suspended until renewal.\n"
            f"Please contact administration to begin the recertification process."
        )
        
        try:
            WhatsAppService.send_whatsapp_message(agent.user.phone_number, msg)
        except Exception as e:
            logger.error(f"Failed to send expiry notification to {agent.user.phone_number}: {e}")
        
        # Send email if available
        if agent.user.email:
            try:
                email_service.send_template(
                    "email.certification_expired",
                    to=agent.user.email,
                    context={
                        "name": agent.user.full_name,
                        "agent_code": agent.agent_code,
                        "expired_date": training.certification_expires_at.strftime("%Y-%m-%d")
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send expiry email to {agent.user.email}: {e}")
    
    @staticmethod
    def _send_expiry_reminder(agent: Agent, training: AgentTraining, days_remaining: int):
        """Send certification expiry reminder"""
        expiry_date = training.certification_expires_at.strftime("%Y-%m-%d")
        
        msg = (
            f"⏰ *CERTIFICATION EXPIRY REMINDER*\n\n"
            f"Dear {agent.user.full_name},\n\n"
            f"Your ZimAgritrust Field Agent certification expires in {days_remaining} day(s).\n\n"
            f"📅 Expiry Date: {expiry_date}\n\n"
            f"Please contact administration to renew your certification before expiry to avoid account suspension."
        )
        
        try:
            WhatsAppService.send_whatsapp_message(agent.user.phone_number, msg)
        except Exception as e:
            logger.error(f"Failed to send reminder to {agent.user.phone_number}: {e}")
        
        # Send email if available
        if agent.user.email:
            try:
                email_service.send_template(
                    "email.certification_reminder",
                    to=agent.user.email,
                    context={
                        "name": agent.user.full_name,
                        "agent_code": agent.agent_code,
                        "days_remaining": days_remaining,
                        "expiry_date": expiry_date
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send reminder email to {agent.user.email}: {e}")
    
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
        
        training = db.query(AgentTraining).filter(AgentTraining.agent_id == agent.id).first()
        if not training:
            raise ValueError("Training record not found")
        
        # Calculate new expiry date
        if training.certification_expires_at and training.certification_expires_at > datetime.now(timezone.utc):
            # Extend from current expiry
            new_expiry = training.certification_expires_at + timedelta(days=renewal_days)
        else:
            # Set from now
            new_expiry = datetime.now(timezone.utc) + timedelta(days=renewal_days)
        
        training.certification_expires_at = new_expiry
        training.certification_level = CertificationLevel.CERTIFIED
        agent.status = AgentStatus.ACTIVE
        
        db.commit()
        
        # Send renewal confirmation
        msg = (
            f"✅ *CERTIFICATION RENEWED*\n\n"
            f"Dear {agent.user.full_name},\n\n"
            f"Your ZimAgritrust Field Agent certification has been successfully renewed.\n\n"
            f"📅 New Expiry Date: {new_expiry.strftime('%Y-%m-%d')}\n\n"
            f"Your account is now active with full portal access."
        )
        
        try:
            WhatsAppService.send_whatsapp_message(agent.user.phone_number, msg)
        except Exception as e:
            logger.error(f"Failed to send renewal notification: {e}")
        
        return {
            "agent_id": str(agent.id),
            "agent_code": agent.agent_code,
            "certification_level": training.certification_level.value,
            "certified_at": training.certified_at,
            "certification_expires_at": training.certification_expires_at,
            "agent_status": agent.status.value
        }


certification_service = CertificationService()
