"""
Role-Based Access Control (RBAC) and permission management
Enforces hierarchical role structure with granular permissions
"""
import uuid
from typing import Optional, List, Set, Callable
from functools import wraps
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.user import User, UserRole
from app.models.rbac import Role, Permission, RolePermission
from app.models.security_enhanced import (
    SecurityAuditLog, AuditLogAction, TokenBlacklist
)
from app.models.session import UserSession
from app.services.security_service import TokenManager
from app.core.config import settings
from app.db.session import get_db
from jose import jwt


# ============================================================================
# PERMISSION REGISTRY
# ============================================================================

# All granular permissions
PERMISSIONS = {
    # User Management
    "user:create": "Create new users",
    "user:read": "View user information",
    "user:update": "Update user information",
    "user:delete": "Delete users",
    "user:verify": "Verify users (KYC)",
    "user:suspend": "Suspend users",
    "user:ban": "Ban users",
    "user:impersonate": "Impersonate users",
    
    # Role Management
    "role:create": "Create roles",
    "role:read": "Read roles",
    "role:update": "Update roles",
    "role:delete": "Delete roles",
    
    # Permission Management
    "permission:assign": "Assign permissions",
    "permission:revoke": "Revoke permissions",
    
    # Transaction Management
    "transaction:read": "View transactions",
    "transaction:freeze": "Freeze transactions",
    "transaction:refund": "Process refunds",
    "transaction:approve": "Approve transactions",
    
    # Payment Management
    "payment:initiate": "Initiate payments",
    "payment:approve": "Approve payments",
    "payment:reject": "Reject payments",
    "payment:reverse": "Reverse payments",
    
    # Withdrawal Management
    "withdrawal:request": "Request withdrawals",
    "withdrawal:approve": "Approve withdrawals",
    "withdrawal:reject": "Reject withdrawals",
    
    # Dispute Management
    "dispute:read": "View disputes",
    "dispute:assign": "Assign disputes",
    "dispute:resolve": "Resolve disputes",
    "dispute:appeal": "Appeal dispute decisions",
    
    # Listing Management
    "listing:create": "Create listings",
    "listing:read": "View listings",
    "listing:update": "Update listings",
    "listing:delete": "Delete listings",
    "listing:verify": "Verify listings",
    
    # Input Management
    "input:create": "Create inputs",
    "input:read": "View inputs",
    "input:update": "Update inputs",
    "input:delete": "Delete inputs",
    "input:verify": "Verify inputs",
    
    # Reporting
    "report:generate": "Generate reports",
    "report:export": "Export reports",
    "report:schedule": "Schedule reports",
    
    # Audit
    "audit:read": "View audit logs",
    "audit:export": "Export audit logs",
    "audit:delete": "Delete audit logs",
    
    # System Settings
    "settings:read": "View system settings",
    "settings:update": "Update system settings",
    "settings:delete": "Delete system settings",
    
    # System Administration
    "system:health": "View system health",
    "system:backup": "Backup system",
    "system:restore": "Restore system",
    "system:shutdown": "Shutdown system",
}


# Default permission sets by role
DEFAULT_ROLE_PERMISSIONS = {
    "SUPER_ADMIN": list(PERMISSIONS.keys()),  # All permissions
    
    "SYSTEM_ADMIN": [
        "user:create", "user:read", "user:update", "user:delete",
        "user:verify", "user:suspend", "user:ban",
        "role:create", "role:read", "role:update", "role:delete",
        "permission:assign", "permission:revoke",
        "transaction:read", "transaction:freeze", "transaction:approve",
        "payment:initiate", "payment:approve", "payment:reject", "payment:reverse",
        "withdrawal:approve", "withdrawal:reject",
        "dispute:read", "dispute:assign", "dispute:resolve",
        "report:generate", "report:export", "report:schedule",
        "audit:read", "audit:export",
        "settings:read", "settings:update",
        "system:health", "system:backup", "system:restore",
    ],
    
    "FINANCE_ADMIN": [
        "transaction:read", "transaction:freeze", "transaction:refund", "transaction:approve",
        "payment:initiate", "payment:approve", "payment:reject", "payment:reverse",
        "withdrawal:approve", "withdrawal:reject",
        "report:generate", "report:export",
        "audit:read",
    ],
    
    "REGIONAL_ADMIN": [
        "user:read", "user:verify", "user:suspend",
        "listing:read", "listing:verify",
        "input:read", "input:verify",
        "dispute:read", "dispute:assign",
        "transaction:read",
        "report:generate",
    ],
    
    "SUPPORT_ADMIN": [
        "user:read", "user:update",
        "transaction:read",
        "dispute:read", "dispute:assign",
        "report:read",
    ],
    
    "BRANCH_ADMIN": [
        "user:read", "user:update",
        "listing:read",
        "transaction:read",
    ],
    
    "AGENT": [
        "user:read",
        "listing:read", "listing:verify",
        "input:read", "input:verify",
        "dispute:read",
        "transaction:read",
    ],
    
    "STAFF": [
        "user:read",
        "listing:read",
        "transaction:read",
    ],
    
    "FARMER": [
        "listing:create", "listing:read", "listing:update", "listing:delete",
        "input:read",
        "transaction:read",
    ],
    
    "BUYER": [
        "listing:read",
        "transaction:read",
        "payment:initiate",
    ],
    
    "DRIVER": [
        "transaction:read",
    ],
    
    "SUPPLIER": [
        "listing:create", "listing:read", "listing:update", "listing:delete",
        "input:create", "input:read", "input:update", "input:delete",
        "transaction:read",
        "payment:initiate",
    ],
}


# ============================================================================
# RBAC SERVICE
# ============================================================================

class RBACService:
    """Role-Based Access Control service"""
    
    @staticmethod
    def create_default_roles(db: Session):
        """Create default roles from registry"""
        for role_name, permissions in DEFAULT_ROLE_PERMISSIONS.items():
            role = db.query(Role).filter(Role.name == role_name).first()
            
            if role:
                continue  # Already exists
            
            # Create role
            role = Role(
                name=role_name,
                level=RBACService.get_role_level(role_name),
            )
            db.add(role)
            db.flush()
            
            # Add permissions
            for perm_key in permissions:
                perm = db.query(Permission).filter(Permission.key == perm_key).first()
                
                if not perm:
                    perm = Permission(
                        key=perm_key,
                        module=perm_key.split(":")[0],
                    )
                    db.add(perm)
                    db.flush()
                
                role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
                db.add(role_perm)
        
        db.commit()
    
    @staticmethod
    def get_role_level(role_name: str) -> int:
        """Get role level from hierarchy"""
        levels = {
            "FARMER": 10,
            "BUYER": 10,
            "DRIVER": 20,
            "STAFF": 30,
            "AGENT": 40,
            "SUPPLIER": 60,
            "BRANCH_ADMIN": 70,
            "SUPPORT_ADMIN": 75,
            "REGIONAL_ADMIN": 80,
            "REGIONAL_MANAGER": 80,
            "FINANCE_ADMIN": 85,
            "SYSTEM_ADMIN": 90,
            "ADMIN": 100,
            "SUPER_ADMIN": 100,
        }
        return levels.get(role_name, 1)
    
    @staticmethod
    def user_has_permission(db: Session, user: User, permission: str) -> bool:
        """Check if user has permission"""
        
        # Super admins have all permissions
        if user.role == UserRole.SUPER_ADMIN or (user.role_id and user.dynamic_role and user.dynamic_role.level >= 100):
            return True
        
        # Get user's role permissions
        if user.role_id and user.dynamic_role:
            role_permissions = db.query(Permission).join(
                RolePermission, RolePermission.permission_id == Permission.id
            ).filter(
                RolePermission.role_id == user.role_id,
                Permission.key == permission,
            ).first()
            
            return role_permissions is not None
        
        # Check legacy role-based permissions
        role_perms = DEFAULT_ROLE_PERMISSIONS.get(user.role.value.upper(), [])
        return permission in role_perms
    
    @staticmethod
    def user_can_access_resource(db: Session, user: User, resource_type: str, resource_owner_id: uuid.UUID = None) -> bool:
        """Check if user can access a resource"""
        
        # Admins can access anything
        if user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            return True
        
        # Users can access their own resources
        if resource_owner_id and resource_owner_id == user.id:
            return True
        
        # Check permissions
        read_perm = f"{resource_type}:read"
        return RBACService.user_has_permission(db, user, read_perm)


# ============================================================================
# JWT SECURITY
# ============================================================================

class JWTBearer(HTTPBearer):
    """JWT Bearer token authentication"""
    
    async def __call__(self, request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code.",
            )
        
        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication scheme.",
            )
        
        if not self.verify_jwt(credentials.credentials):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token or expired token.",
            )
        
        return credentials.credentials
    
    @staticmethod
    def verify_jwt(token: str) -> bool:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload.get('exp') is not None
        except:
            return False


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_current_user(
    token: str = Depends(JWTBearer()),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token"""
    
    payload = TokenManager.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    user_id = payload.get('sub')
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


async def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Get current admin user (requires admin role)"""
    
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return user


async def check_permission(permission: str):
    """Factory for permission checker"""
    
    async def checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not RBACService.user_has_permission(db, user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return user
    
    return checker


# ============================================================================
# DECORATOR FOR PERMISSION CHECKS
# ============================================================================

def require_permission(permission: str):
    """Decorator to require permission"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db = kwargs.get('db')
            user = kwargs.get('current_user')
            
            if db and user:
                if not RBACService.user_has_permission(db, user, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission '{permission}' required",
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_role(*roles):
    """Decorator to require specific role"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            
            if user:
                role = user.role.value.upper() if hasattr(user.role, 'value') else str(user.role).upper()
                if role not in roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Role {roles} required",
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
