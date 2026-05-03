"""
Security Dependencies for API Endpoints
Provides additional security checks for API endpoints
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def verify_csrf_token(request: Request) -> dict:
    """
    Verify CSRF token for state-changing requests
    
    Args:
        request: FastAPI request
        
    Returns:
        CSRF token data
        
    Raises:
        HTTPException if CSRF validation fails
    """
    # For GET, HEAD, OPTIONS, TRACE methods, CSRF is not required
    if request.method in ["GET", "HEAD", "OPTIONS", "TRACE"]:
        return {"csrf_exempt": True}
    
    # Get CSRF token from headers
    csrf_token = request.headers.get("X-CSRF-Token")
    
    # Get session token (from cookie or session)
    session_csrf_token = request.cookies.get("csrf_token")
    
    if not csrf_token or not session_csrf_token:
        logger.warning(f"CSRF token missing from request: {request.method} {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing"
        )
    
    # Validate CSRF token (using constant-time comparison)
    import secrets
    if not secrets.compare_digest(csrf_token, session_csrf_token):
        logger.warning(f"CSRF token mismatch: {request.method} {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token invalid"
        )
    
    return {"csrf_valid": True}


def check_content_type(request: Request, allowed_types: list[str]) -> dict:
    """
    Verify Content-Type header for API requests
    
    Args:
        request: FastAPI request
        allowed_types: List of allowed content types
        
    Returns:
        Content type data
        
    Raises:
        HTTPException if content type is invalid
    """
    # Skip content type check for GET requests
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return {"content_type_exempt": True}
    
    content_type = request.headers.get("Content-Type", "")
    
    # Check if content type is in allowed list
    if not any(allowed in content_type for allowed in allowed_types):
        logger.warning(f"Invalid Content-Type: {content_type} for {request.method} {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported Media Type. Allowed: {', '.join(allowed_types)}"
        )
    
    return {"content_type_valid": True}


def check_user_agent(request: Request) -> dict:
    """
    Verify User-Agent header for API requests
    
    Args:
        request: FastAPI request
        
    Returns:
        User agent data
        
    Raises:
        HTTPException if User-Agent is suspicious
    """
    user_agent = request.headers.get("User-Agent", "")
    
    # Check for suspicious user agents
    suspicious_patterns = [
        "sqlmap",
        "nmap",
        "nikto",
        "burpsuite",
        "metasploit",
        "curl",
        "wget",
    ]
    
    for pattern in suspicious_patterns:
        if pattern.lower() in user_agent.lower():
            logger.warning(f"Suspicious User-Agent detected: {user_agent}")
            # In production, you might want to block these
            # For now, just log it
    
    return {"user_agent": user_agent}


def check_request_size(request: Request, max_size_mb: int = 10) -> dict:
    """
    Check request size to prevent DoS attacks
    
    Args:
        request: FastAPI request
        max_size_mb: Maximum request size in MB
        
    Returns:
        Request size data
        
    Raises:
        HTTPException if request is too large
    """
    content_length = request.headers.get("Content-Length")
    
    if content_length:
        size_bytes = int(content_length)
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb > max_size_mb:
            logger.warning(f"Request too large: {size_mb:.2f}MB for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request too large. Maximum size: {max_size_mb}MB"
            )
    
    return {"size_valid": True}


def rate_limit_by_ip(request: Request, max_requests: int = 100, window_seconds: int = 60) -> dict:
    """
    Rate limit requests by IP address
    
    Args:
        request: FastAPI request
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
        
    Returns:
        Rate limit data
        
    Raises:
        HTTPException if rate limit exceeded
    """
    # This should use Redis in production
    # For now, it's a placeholder
    client_ip = request.client.host if request.client else "unknown"
    
    # TODO: Implement Redis-based rate limiting
    # For now, just pass through
    return {"rate_limit": "not_implemented", "ip": client_ip}


def sanitize_request_data(request: Request) -> dict:
    """
    Sanitize request data to prevent injection attacks
    
    Args:
        request: FastAPI request
        
    Returns:
        Sanitized data
    """
    from app.core.input_validation import InputValidator
    
    sanitized = {}
    
    # Sanitize query parameters
    for key, value in request.query_params.items():
        if isinstance(value, str):
            sanitized[key] = InputValidator.sanitize_string(value)
        else:
            sanitized[key] = value
    
    return {"sanitized": sanitized}
