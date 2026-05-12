"""
Invitation system for privileged roles (admins, agents, staff)
Handles invitation creation, verification, and role provisioning
"""
import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.rbac import Invitation, Role, InvitationStatus
from app.models.user import User, UserStatus
from app.models.security_enhanced import AuditLog, AuditLogAction
from app.core.config import settings


# ============================================================================
# INVITATION SYSTEM
# ============================================================================

class InvitationService:
    """Manage invitations for privileged roles"""
    
    PRIVILEGED_ROLES = [
        'SYSTEM_ADMIN',
        'FINANCE_ADMIN',
        'REGIONAL_ADMIN',
        'SUPPORT_ADMIN',
        'BRANCH_ADMIN',
        'AGENT',
        'STAFF',
    ]
    
    @staticmethod
    def generate_invitation_token() -> Tuple[str, str]:
        """
        Generate invitation token
        Returns: (token, token_hash)
        """
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token, token_hash
    
    @staticmethod
    def create_invitation(
        db: Session,
        email: str,
        role_name: str,
        invited_by: User,
        expires_hours: int = 72,
    ) -> Tuple[Invitation, str]:
        """
        Create invitation for privileged role
        
        Args:
            email: Email of invitee
            role_name: Role to invite for
            invited_by: User creating invitation
            expires_hours: Expiration time in hours
        
        Returns:
            (invitation, token_plain)
        """
        
        # Validate role
        if role_name not in InvitationService.PRIVILEGED_ROLES:
            raise ValueError(f"Cannot invite for role: {role_name}")
        
        # Get role
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise ValueError(f"Role not found: {role_name}")
        
        # Check if user already invited
        existing = db.query(Invitation).filter(
            and_(
                Invitation.email == email,
                Invitation.status == InvitationStatus.PENDING,
            )
        ).first()
        
        if existing:
            raise ValueError(f"User already invited: {email}")
        
        # Generate token
        token, token_hash = InvitationService.generate_invitation_token()
        try:
            inviter_user_id = uuid.UUID(str(invited_by.id)) if invited_by.id else None
        except (TypeError, ValueError):
            inviter_user_id = None
        
        # Create invitation
        invitation = Invitation(
            email=email,
            role_id=role.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours),
            created_by=inviter_user_id,
            status=InvitationStatus.PENDING,
        )
        
        db.add(invitation)
        
        # Log audit event
        log_entry = AuditLog(
            action=AuditLogAction.PERMISSION_GRANT,
            user_id=None,  # Not a user yet
            actor_id=inviter_user_id,
            resource_type='invitation',
            resource_id=invitation.id,
            details={
                'email': email,
                'role': role_name,
                'expires_hours': expires_hours,
                'invited_by': str(invited_by.id) if invited_by.id else None,
            }
        )
        db.add(log_entry)
        
        db.commit()
        
        return invitation, token
    
    @staticmethod
    def verify_invitation(db: Session, email: str, token: str) -> Tuple[bool, Optional[str], Optional[Invitation]]:
        """
        Verify and claim invitation
        
        Returns:
            (is_valid, error_message, invitation)
        """
        
        # Hash token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Find invitation
        invitation = db.query(Invitation).filter(
            and_(
                Invitation.email == email,
                Invitation.token_hash == token_hash,
                Invitation.status == InvitationStatus.PENDING,
            )
        ).first()
        
        if not invitation:
            return False, "Invalid or expired invitation", None
        
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        expires = invitation.expires_at if invitation.expires_at.tzinfo else invitation.expires_at.replace(tzinfo=timezone.utc)
        if expires < now_utc:
            invitation.status = InvitationStatus.EXPIRED
            db.commit()
            return False, "Invitation has expired", None
        
        return True, None, invitation
    
    @staticmethod
    def accept_invitation(
        db: Session,
        invitation: Invitation,
        user: User,
    ) -> Tuple[bool, Optional[str]]:
        """
        Accept invitation and assign role
        
        Returns:
            (success, error_message)
        """
        
        # Verify email matches
        if user.email != invitation.email:
            return False, "Email does not match invitation"
        
        # Update invitation
        from datetime import timezone
        invitation.status = InvitationStatus.ACCEPTED
        invitation.used_at = datetime.now(timezone.utc)
        
        # Assign role to user
        user.role_id = invitation.role_id
        user.status = UserStatus.ACTIVE
        
        # Log audit event
        log_entry = AuditLog(
            action=AuditLogAction.PERMISSION_GRANT,
            user_id=user.id,
            resource_type='user_role',
            resource_id=user.id,
            details={
                'role_id': str(invitation.role_id),
                'via_invitation': str(invitation.id),
            }
        )
        db.add(log_entry)
        
        db.commit()
        
        return True, None
    
    @staticmethod
    def revoke_invitation(db: Session, invitation_id: uuid.UUID, reason: str = None):
        """Revoke an invitation"""
        
        invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
        
        if not invitation:
            raise ValueError("Invitation not found")
        
        invitation.status = InvitationStatus.REVOKED
        
        db.commit()
