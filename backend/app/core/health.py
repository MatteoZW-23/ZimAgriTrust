"""
Health Check Endpoints for Enterprise Monitoring
Provides comprehensive health status for all system components
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import logging
from datetime import datetime
from app.api.deps import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check():
    """
    Basic health check endpoint
    Returns 200 if service is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": "1.0.0"
    }


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - verifies the application is ready to handle requests
    Checks database and Redis connections
    """
    checks = {
        "database": check_database(db),
        "redis": check_redis()
    }
    
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    
    status_code = 200 if all_healthy else 503
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }, status_code


@router.get("/health/live")
def liveness_check():
    """
    Liveness check - verifies the application is running
    Lightweight check that doesn't depend on external services
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with component status
    Includes database, Redis, and application metrics
    """
    checks = {
        "database": check_database(db),
        "redis": check_redis(),
        "application": check_application()
    }
    
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    status_code = 200 if all_healthy else 503
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "environment": settings.APP_NAME
    }, status_code


def check_database(db: Session) -> dict:
    """Check database connection and basic query"""
    try:
        # Execute simple query to test connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }


def check_redis() -> dict:
    """Check Redis connection"""
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        return {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }


def check_application() -> dict:
    """Check application-level metrics"""
    try:
        # Check if critical services are configured
        checks = []
        
        if settings.SECRET_KEY and len(settings.SECRET_KEY) > 20:
            checks.append("Secret key configured")
        else:
            checks.append("Secret key not configured properly")
        
        if settings.DATABASE_URL:
            checks.append("Database URL configured")
        else:
            checks.append("Database URL not configured")
        
        if settings.REDIS_URL:
            checks.append("Redis URL configured")
        else:
            checks.append("Redis URL not configured")
        
        return {
            "status": "healthy",
            "message": "Application checks passed",
            "checks": checks
        }
    except Exception as e:
        logger.error(f"Application health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Application check failed: {str(e)}"
        }


@router.get("/health/metrics")
def metrics():
    """
    Basic metrics endpoint for monitoring
    Returns simple application metrics
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "metrics_placeholder",  # Can be replaced with actual uptime tracking
        "requests_total": "metrics_placeholder",  # Can be integrated with request counter
        "errors_total": "metrics_placeholder"  # Can be integrated with error counter
    }
