"""
Hardened Security Middleware for AgriTrust Platform
Enforces CSRF, request size limits, content-type validation, scanner blocking,
rate limiting, admin IP whitelisting, and anomaly detection.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import logging
from typing import Callable, Optional
from app.core.config import settings
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
rate_limit_store = {}

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for admin endpoints
    """
    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        method = request.method
        client_ip = self._get_client_ip(request)
        request_id = request.headers.get("X-Request-ID", str(int(time.time() * 1000000)))

        # 0. Skip security for preflight (OPTIONS) requests
        if method == "OPTIONS":
            return await call_next(request)

        # Skip security for public endpoints
        if self._should_skip(request):
            response = await call_next(request)
            return self._add_security_headers(response)

        # 1. Scanner / suspicious UA detection
        ua = request.headers.get("User-Agent", "").lower()
        scanners = {"sqlmap", "nmap", "nikto", "burpsuite", "metasploit", "gobuster", "dirbuster"}
        if any(s in ua for s in scanners):
            logger.warning(f"SECURITY | Suspicious UA blocked | ip={client_ip} | path={path} | ua={ua[:60]}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Request blocked by security policy."}
            )

        # 2. Super-admin IP whitelist (stricter, evaluated first)
        if self._is_super_admin_route(request):
            if settings.SUPER_ADMIN_IP_WHITELIST and not self._is_super_admin_ip_whitelisted(client_ip):
                logger.warning(f"SECURITY | Super-admin IP blocked | ip={client_ip} | path={path}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Access denied from this IP address"}
                )
        # 2b. Regular admin IP whitelist
        elif self._is_admin_route(request):
            if settings.ADMIN_IP_WHITELIST and not self._is_ip_whitelisted(client_ip):
                logger.warning(f"SECURITY | Admin IP blocked | ip={client_ip} | path={path}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Access denied from this IP address"}
                )

        # 3. Request size limit
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                size_mb = int(content_length) / (1024 * 1024)
                limit = 5 if "upload" in path else 10
                if size_mb > limit:
                    logger.warning(f"SECURITY | Request too large | size={size_mb:.2f}MB | ip={client_ip} | path={path}")
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": f"Request body exceeds maximum allowed size of {limit}MB."}
                    )
            except ValueError:
                pass

        # 4. Content-Type validation for mutating API endpoints
        if method in ("POST", "PUT", "PATCH", "DELETE") and path.startswith("/api/"):
            ct = request.headers.get("Content-Type", "").lower()
            if not ct.startswith("multipart/"):
                allowed = {"application/json", "application/x-www-form-urlencoded", "text/plain"}
                if not any(a in ct for a in allowed):
                    logger.warning(f"SECURITY | Invalid Content-Type | ct={ct} | ip={client_ip} | path={path}")
                    return JSONResponse(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        content={"detail": "Unsupported Media Type."}
                    )

        # 5. CSRF validation for state-changing requests (skip if cookie absent)
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            csrf_header = request.headers.get("X-CSRF-Token")
            csrf_cookie = request.cookies.get("csrf_token")
            if csrf_cookie and csrf_header:
                import secrets
                if not secrets.compare_digest(csrf_header, csrf_cookie):
                    logger.warning(f"SECURITY | CSRF mismatch | ip={client_ip} | path={path}")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "CSRF token invalid."}
                    )

        # 6. Rate limiting
        if settings.RATE_LIMIT_ENABLED:
            if not await self._check_rate_limit(request, client_ip):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests. Please try again later."}
                )

        # 7. Anomaly detection
        if settings.ANOMALY_DETECTION_ENABLED:
            await self._check_anomaly(request, client_ip, path)

        response = await call_next(request)
        return self._add_security_headers(response)
    
    def _should_skip(self, request: Request) -> bool:
        path = request.url.path
        skip = {"/", "/health", "/api/v1/auth/login", "/api/v1/auth/verify-login-2fa", "/api/v1/auth/refresh"}
        if path in skip:
            return True
        for prefix in ("/health", "/api/v1/auth/forgot-password", "/api/v1/auth/reset-password", "/api/v1/public"):
            if path.startswith(prefix):
                return True
        return False

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP considering X-Forwarded-For / X-Real-IP."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "unknown"

    def _is_admin_route(self, request: Request) -> bool:
        """Check if request is to an admin endpoint (excluding super-admin)."""
        path = request.url.path
        if self._is_super_admin_route(request):
            return False
        return "/admin" in path or path.startswith("/api/v1/admin")

    def _is_super_admin_route(self, request: Request) -> bool:
        """Check if request targets the super-admin namespace."""
        path = request.url.path
        return path.startswith("/api/v1/super-admin") or path.startswith("/super-admin")

    def _is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is in admin whitelist"""
        whitelist = settings.admin_ip_whitelist_list
        return ip in whitelist or "127.0.0.1" in whitelist or "localhost" in whitelist

    def _is_super_admin_ip_whitelisted(self, ip: str) -> bool:
        whitelist = settings.super_admin_ip_whitelist_list
        if not whitelist:
            return True  # not configured → off
        return ip in whitelist

    def _add_security_headers(self, response):
        """Add comprehensive security headers."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self';"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self), payment=()"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        return response

    async def _check_anomaly(self, request: Request, client_ip: str, path: str) -> None:
        """Lightweight anomaly detection using Redis counters."""
        try:
            key = f"anomaly:{client_ip}:{path}"
            count = await cache_service.increment_counter(key, 60)
            if count and int(count) >= settings.ANOMALY_THRESHOLD:
                logger.warning(f"SECURITY | Anomaly detected | count={count} | ip={client_ip} | path={path}")
        except Exception:
            pass
    
    async def _check_rate_limit(self, request: Request, client_ip: str) -> bool:
        """Check if request is within rate limits"""
        now = time.time()
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        
        # Use stricter limits for admin routes
        if self._is_admin_route(request):
            limit = settings.RATE_LIMIT_API_GENERAL // 2  # Stricter for admin
            window = settings.RATE_LIMIT_WINDOW_SECONDS
        else:
            limit = settings.RATE_LIMIT_API_GENERAL
        
        # Get or create rate limit entry
        key = f"{client_ip}:{request.url.path}"
        if key not in rate_limit_store:
            rate_limit_store[key] = {"count": 0, "window_start": now}
        
        # Reset if window expired
        if now - rate_limit_store[key]["window_start"] > window:
            rate_limit_store[key] = {"count": 0, "window_start": now}
        
        # Increment counter
        rate_limit_store[key]["count"] += 1
        
        # Check if over limit
        if rate_limit_store[key]["count"] > limit:
            logger.warning(f"Rate limit exceeded for {key}: {rate_limit_store[key]['count']}/{limit}")
            return False
        
        return True


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Audit logging middleware for admin actions
    Logs all admin operations for security monitoring
    """
    async def dispatch(self, request: Request, call_next: Callable):
        # Only log admin routes
        if not self._is_admin_route(request):
            return await call_next(request)
        
        # Get user info if authenticated
        user_info = self._get_user_info(request)
        
        # Log request
        client_ip = SecurityMiddleware._get_client_ip(None, request)
        logger.info(
            f"AUDIT | {request.method} {request.url.path} | "
            f"IP: {client_ip} | "
            f"User: {user_info} | "
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.info(
            f"AUDIT | {request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"User: {user_info}"
        )
        
        return response
    
    def _is_admin_route(self, request: Request) -> bool:
        """Audit logs both /admin and /super-admin endpoints."""
        path = request.url.path
        return (
            "/admin" in path
            or path.startswith("/api/v1/admin")
            or path.startswith("/api/v1/super-admin")
            or path.startswith("/super-admin")
        )

    def _get_user_info(self, request: Request) -> str:
        """Extract user information from request"""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return "authenticated"
        return "anonymous"


def get_security_headers():
    """Return comprehensive security headers for responses"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self';",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(self), payment=()",
        "X-Permitted-Cross-Domain-Policies": "none",
        "Cross-Origin-Embedder-Policy": "require-corp",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
    }
