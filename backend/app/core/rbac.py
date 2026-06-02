from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.models.agent import Agent, AgentStatus
from app.models.user import User, UserRole
from app.models.onboarding import AgentTrainingProgress
from app.services.certification_service import CertificationLevel
from datetime import datetime, timedelta, timezone

TrainingProgress = AgentTrainingProgress


def _certification_level_value(training: Optional[TrainingProgress]) -> str:
    if not training or not training.certification_level:
        return CertificationLevel.NOT_CERTIFIED.value
    level = training.certification_level
    return level.value if hasattr(level, "value") else str(level)


class RBACService:
    """Role-Based Access Control service for Academy vs Portal access"""
    
    @staticmethod
    def check_academy_access(agent: Agent, training: Optional[TrainingProgress] = None) -> bool:
        """
        Check if agent has access to Academy (TRAINEE or ACTIVE with valid certification)
        
        Returns True if access granted, raises HTTPException if denied
        """
        if agent.status == AgentStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ACADEMY_DISMISSAL: This profile has been terminated."
            )
        
        if agent.status not in [AgentStatus.TRAINEE, AgentStatus.ACTIVE]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ACCESS_DENIED: Academy access is restricted to trainees and certified agents."
            )
        
        # Check certification expiry for ACTIVE agents
        if agent.status == AgentStatus.ACTIVE and training:
            if training.certification_expires_at:
                days_until_expiry = (training.certification_expires_at - datetime.now(timezone.utc)).days
                if days_until_expiry <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="CERTIFICATION_EXPIRED: Your certification has expired. Please contact administration for renewal."
                    )
        
        return True
    
    @staticmethod
    def check_portal_access(agent: Agent, training: Optional[TrainingProgress] = None) -> bool:
        """
        Check if agent has access to full Agent Portal (ACTIVE with valid certification only)
        
        Returns True if access granted, raises HTTPException if denied
        """
        if agent.status == AgentStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ACCOUNT_SUSPENDED: Your account has been suspended."
            )
        
        if agent.status != AgentStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ACCESS_DENIED: Portal access is restricted to certified active agents only."
            )
        
        # Check certification expiry
        if training and training.certification_expires_at:
            days_until_expiry = (training.certification_expires_at - datetime.now(timezone.utc)).days
            if days_until_expiry <= 0:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CERTIFICATION_EXPIRED: Your certification has expired. Please contact administration for renewal."
                )
        
        return True
    
    @staticmethod
    def check_marketplace_access(agent: Agent) -> bool:
        """
        Check if agent has access to marketplace features
        
        TRAINEE: Read-only access
        ACTIVE: Full access
        """
        if agent.status == AgentStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ACCOUNT_SUSPENDED: Your account has been suspended."
            )
        
        if agent.status not in [AgentStatus.TRAINEE, AgentStatus.ACTIVE]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ACCESS_DENIED: Marketplace access restricted."
            )
        
        return True
    
    @staticmethod
    def check_wallet_access(agent: Agent) -> bool:
        """
        Check if agent has access to wallet features
        
        TRAINEE: No access
        ACTIVE: Full access
        """
        if agent.status != AgentStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ACCESS_DENIED: Wallet access is restricted to certified active agents only."
            )
        
        return True
    
    @staticmethod
    def check_transaction_access(agent: Agent) -> bool:
        """
        Check if agent has access to transaction features
        
        TRAINEE: No access
        ACTIVE: Full access
        """
        if agent.status != AgentStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ACCESS_DENIED: Transaction access is restricted to certified active agents only."
            )
        
        return True
    
    @staticmethod
    def check_logistics_access(agent: Agent) -> bool:
        """
        Check if agent has access to logistics features
        
        TRAINEE: No access
        ACTIVE: Full access
        """
        if agent.status != AgentStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ACCESS_DENIED: Logistics access is restricted to certified active agents only."
            )
        
        return True
    
    @staticmethod
    def get_access_level(agent: Agent, training: Optional[TrainingProgress] = None) -> dict:
        """
        Get the current access level for an agent
        """
        access_level = {
            "agent_status": agent.status.value,
            "certification_level": _certification_level_value(training),
            "academy_access": False,
            "portal_access": False,
            "marketplace_access": False,
            "wallet_access": False,
            "transaction_access": False,
            "logistics_access": False,
            "certification_expires_at": training.certification_expires_at if training else None,
            "days_until_expiry": None
        }
        
        try:
            access_level["academy_access"] = RBACService.check_academy_access(agent, training)
        except:
            pass
        
        try:
            access_level["portal_access"] = RBACService.check_portal_access(agent, training)
        except:
            pass
        
        try:
            access_level["marketplace_access"] = RBACService.check_marketplace_access(agent)
        except:
            pass
        
        try:
            access_level["wallet_access"] = RBACService.check_wallet_access(agent)
        except:
            pass
        
        try:
            access_level["transaction_access"] = RBACService.check_transaction_access(agent)
        except:
            pass
        
        try:
            access_level["logistics_access"] = RBACService.check_logistics_access(agent)
        except:
            pass
        
        if training and training.certification_expires_at:
            access_level["days_until_expiry"] = (training.certification_expires_at - datetime.now(timezone.utc)).days
        
        return access_level


rbac_service = RBACService()
