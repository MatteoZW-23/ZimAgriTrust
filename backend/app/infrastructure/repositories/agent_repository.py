"""
Agent Repository - Consolidated Single Source for Agent Data Access
Replaces duplicate agent_repository.py, onboarding_repository.py, recruitment_repository.py
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from backend.app.infrastructure.repositories.base import BaseRepository
from backend.app.models import Agent as AgentORM, AgentApplication as AgentApplicationORM
from backend.app.shared.types import AgentStatus


class AgentRepository(BaseRepository):
    """
    Consolidated repository for all agent data access.
    
    Responsibilities:
    - Agent CRUD operations
    - Agent status queries
    - Application retrieval
    
    WHY: Consolidates agent_repository.py (3 duplicates) into single source.
    """
    
    def __init__(self, db: Session):
        super().__init__(db, AgentORM)
        self.db = db
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[AgentORM]:
        """
        Get agent profile for a specific user.
        
        Business logic: Only one agent profile per user.
        """
        return self.db.query(AgentORM).filter(
            AgentORM.user_id == user_id
        ).first()
    
    async def get_by_status(self, status: AgentStatus, skip: int = 0, limit: int = 100) -> List[AgentORM]:
        """
        Get all agents with specific status (e.g., APPLIED, APPROVED, ACTIVE).
        
        Use cases:
        - Admin dashboard: Show pending applications
        - Onboarding workflow: Get agents awaiting verification
        - Analytics: Count agents by status
        """
        return self.db.query(AgentORM).filter(
            AgentORM.status == status
        ).offset(skip).limit(limit).all()
    
    async def get_by_multiple_statuses(self, statuses: List[AgentStatus], skip: int = 0, limit: int = 100) -> List[AgentORM]:
        """Get agents with any of the provided statuses"""
        return self.db.query(AgentORM).filter(
            AgentORM.status.in_(statuses)
        ).offset(skip).limit(limit).all()
    
    async def get_by_specialization(self, specialization: str, skip: int = 0, limit: int = 100) -> List[AgentORM]:
        """Get all agents in a specific specialization"""
        return self.db.query(AgentORM).filter(
            AgentORM.specialization == specialization
        ).offset(skip).limit(limit).all()
    
    async def get_active_agents(self, skip: int = 0, limit: int = 100) -> List[AgentORM]:
        """Get all active agents (shorthand for common query)"""
        return await self.get_by_status(AgentStatus.ACTIVE, skip, limit)
    
    async def get_pending_applications(self, skip: int = 0, limit: int = 100) -> List[AgentORM]:
        """Get all agents with APPLIED status (pending review)"""
        return await self.get_by_status(AgentStatus.APPLIED, skip, limit)
    
    async def count_by_status(self, status: AgentStatus) -> int:
        """Count agents with specific status"""
        return self.db.query(AgentORM).filter(
            AgentORM.status == status
        ).count()
    
    async def search(self, query: str, skip: int = 0, limit: int = 100) -> List[AgentORM]:
        """
        Search agents by name or phone.
        
        Used by admin search functionality.
        """
        return self.db.query(AgentORM).filter(
            or_(
                AgentORM.phone.ilike(f"%{query}%"),
                AgentORM.first_name.ilike(f"%{query}%"),
                AgentORM.last_name.ilike(f"%{query}%")
            )
        ).offset(skip).limit(limit).all()
    
    async def get_top_rated(self, limit: int = 10) -> List[AgentORM]:
        """Get top-rated active agents"""
        return self.db.query(AgentORM).filter(
            AgentORM.status == AgentStatus.ACTIVE
        ).order_by(
            desc(AgentORM.agent_rating)
        ).limit(limit).all()


class AgentApplicationRepository(BaseRepository):
    """
    Repository for agent applications (separate from active agents).
    
    Responsibility: Manage agent application lifecycle during onboarding.
    """
    
    def __init__(self, db: Session):
        super().__init__(db, AgentApplicationORM)
        self.db = db
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[AgentApplicationORM]:
        """Get application for user"""
        return self.db.query(AgentApplicationORM).filter(
            AgentApplicationORM.user_id == user_id
        ).first()
    
    async def get_pending(self, skip: int = 0, limit: int = 100) -> List[AgentApplicationORM]:
        """Get applications awaiting review"""
        return self.db.query(AgentApplicationORM).filter(
            AgentApplicationORM.status == "PENDING"
        ).offset(skip).limit(limit).all()
    
    async def get_approved(self, skip: int = 0, limit: int = 100) -> List[AgentApplicationORM]:
        """Get approved applications"""
        return self.db.query(AgentApplicationORM).filter(
            AgentApplicationORM.status == "APPROVED"
        ).offset(skip).limit(limit).all()
