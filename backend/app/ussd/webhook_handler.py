"""
USSD Webhook Handler
====================
Unified webhook endpoint for all Zimbabwe telco providers.
Routes provider-specific callbacks through the new USSD infrastructure.
"""
from __future__ import annotations

import logging
import time
from typing import Any
from fastapi import Request, HTTPException, BackgroundTasks

from app.ussd.providers.common.normalizer import normalizer
from app.ussd.providers.econet.adapter import econet_adapter
from app.ussd.providers.netone.adapter import netone_adapter
from app.ussd.providers.telecel.adapter import telecel_adapter
from app.ussd.engine.router import ussd_router
from app.ussd.engine.middleware import (
    validation_middleware,
    retry_middleware,
    logging_middleware,
    metrics_middleware,
)
from app.ussd.engine.session_manager import session_manager
from app.ussd.providers.common.request_types import NormalizedUSSDResponse, ProviderName

logger = logging.getLogger("ussd.webhook")

# Provider adapter mapping
PROVIDER_ADAPTERS = {
    "econet": econet_adapter,
    "netone": netone_adapter,
    "telecel": telecel_adapter,
}


async def handle_ussd_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Any,
    provider: str = None,
) -> dict:
    """
    Handle incoming USSD webhook from any Zimbabwe telco.
    
    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        db: Database session
        provider: Provider name (optional, auto-detected if omitted)
    
    Returns:
        Provider-formatted response dict
    """
    start_time = time.time()
    
    # Parse request body
    try:
        payload = await request.json()
    except Exception as e:
        logger.error("Invalid JSON payload", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Auto-detect provider if not specified
    if not provider:
        detected = normalizer.detect_provider(payload)
        provider = detected.value
    
    # Get provider adapter
    adapter = PROVIDER_ADAPTERS.get(provider)
    if not adapter:
        logger.error("Unknown provider", extra={"provider": provider})
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    
    # Validate provider signature
    headers = dict(request.headers)
    if not adapter.validate_signature(payload, headers):
        logger.warning("Signature validation failed", extra={"provider": provider})
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Normalize request
    try:
        normalized = adapter.normalize_request(payload)
    except Exception as e:
        logger.error("Normalization failed", extra={"provider": provider, "error": str(e)})
        raise HTTPException(status_code=400, detail="Normalization failed")
    
    # Create context for middleware
    from app.ussd.engine.middleware import USSDContext
    ctx = USSDContext(
        session_id=normalized.session_id,
        phone_number=normalized.phone_number,
        text=normalized.text,
        provider=provider,
        correlation_id=normalized.correlation_id,
    )
    
    # Run middleware chain
    for middleware in [validation_middleware, retry_middleware]:
        result = await middleware.process(ctx)
        if not result.proceed:
            elapsed_ms = int((time.time() - start_time) * 1000)
            await logging_middleware.after(ctx, result.response, elapsed_ms)
            await metrics_middleware.record_request(provider, elapsed_ms, error=True)
            return adapter.format_response(
                NormalizedUSSDResponse(
                    message=result.response["message"],
                    end_session=result.response.get("end_session", False),
                    session_id=normalized.session_id,
                )
            )
        ctx = result.context
    
    # Log before processing
    await logging_middleware.before(ctx)
    
    # Route through USSD engine
    try:
        response = await ussd_router.route(
            session_id=normalized.session_id,
            phone_number=normalized.phone_number,
            text=normalized.text,
            provider=provider,
            db=db,
            service_code=normalized.service_code,
            correlation_id=normalized.correlation_id,
        )
    except Exception as e:
        logger.error("USSD routing error", extra={"provider": provider, "error": str(e)}, exc_info=True)
        elapsed_ms = int((time.time() - start_time) * 1000)
        await metrics_middleware.record_request(provider, elapsed_ms, error=True)
        error_response = {
            "message": "END System error. Please try again.",
            "end_session": True,
        }
        return adapter.format_response(
            NormalizedUSSDResponse(
                message=error_response["message"],
                end_session=error_response["end_session"],
                session_id=normalized.session_id,
            )
        )
    
    # Log after processing
    elapsed_ms = int((time.time() - start_time) * 1000)
    await logging_middleware.after(ctx, response, elapsed_ms)
    await metrics_middleware.record_request(provider, elapsed_ms)
    
    # Format response for provider
    normalized_response = NormalizedUSSDResponse(
        message=response["message"],
        end_session=response.get("end_session", False),
        session_id=normalized.session_id,
    )
    
    return adapter.format_response(normalized_response)
