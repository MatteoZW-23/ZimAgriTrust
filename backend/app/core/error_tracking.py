"""
Error Tracking Integration with Sentry
Captures and reports errors for production monitoring
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from app.core.config import settings


def init_sentry():
    """
    Initialize Sentry error tracking
    Only enabled in production when SENTRY_DSN is configured
    """
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            # Performance monitoring
            traces_sample_rate=0.1,  # Sample 10% of transactions
            # Session recording
            session_sample_rate=0.1,  # Sample 10% of sessions
            # Environment
            environment="production",
            # Release tracking
            release="1.0.0",
            # Before send callback for filtering
            before_send=before_send_filter,
            # Tags
            tags={
                "service": "agritrust-backend",
                "environment": "production",
            },
        )
        return True
    return False


def before_send(event, hint):
    """
    Filter events before sending to Sentry
    Add custom context and filter out unwanted events
    """
    # Filter out 404 errors
    if event.get("level") == "error":
        exception = hint.get("exc_info")
        if exception:
            # Filter out HTTP 404 errors
            if "404" in str(exception[1]):
                return None
            
            # Filter out specific exceptions
            ignored_exceptions = [
                "NotFound",
                "ValidationError",
                "HTTPException",
            ]
            for exc in ignored_exceptions:
                if exc in exception[0].__name__:
                    return None
    
    # Add custom context
    event["contexts"] = event.get("contexts", {})
    event["contexts"]["custom"] = {
        "app_name": settings.APP_NAME,
        "api_version": settings.API_V1_STR,
    }
    
    return event


def capture_exception(exception, extra_context=None):
    """
    Capture an exception and send to Sentry
    
    Args:
        exception: The exception to capture
        extra_context: Additional context to include
    """
    if settings.SENTRY_DSN:
        with sentry_sdk.push_scope() as scope:
            if extra_context:
                for key, value in extra_context.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exception)


def capture_message(message, level="info"):
    """
    Capture a message and send to Sentry
    
    Args:
        message: The message to capture
        level: The log level (info, warning, error)
    """
    if settings.SENTRY_DSN:
        sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id, email=None, username=None):
    """
    Set user context for error tracking
    
    Args:
        user_id: User ID
        email: User email (optional)
        username: User username (optional)
    """
    if settings.SENTRY_DSN:
        sentry_sdk.set_user({
            "id": str(user_id),
            "email": email,
            "username": username,
        })


def clear_user_context():
    """Clear user context"""
    if settings.SENTRY_DSN:
        sentry_sdk.set_user(None)
