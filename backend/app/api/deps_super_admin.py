"""
FastAPI dependencies for /super-admin/* endpoints.

These are kept SEPARATE from `app.api.deps.get_current_user` so that:
  - A compromised normal access token cannot reach super-admin endpoints.
  - Super-admin tokens use a different signing key (SUPER_ADMIN_SECRET_KEY).
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.security import SuperAdmin
from app.services.super_admin_service import authenticate_super_admin


_bearer = HTTPBearer(auto_error=False)


def get_current_super_admin(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> SuperAdmin:
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Super-admin bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authenticate_super_admin(creds.credentials, db, request)
