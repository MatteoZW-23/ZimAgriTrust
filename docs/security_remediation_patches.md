# Security Remediation Patches
**IMMEDIATE ACTION REQUIRED**

---

## PATCH 1: JWT Algorithm Validation (CRITICAL)

**File:** `backend/app/core/security.py`

**Replace lines 59-60:**
```python
def decode_token(token: str) -> dict:
    """Decode and validate JWT with strict algorithm enforcement."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],  # Only HS256 allowed
        options={
            "require": ["exp", "iat", "sub", "type"],
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
            "verify_nbf": True,
        }
    )
```

---

## PATCH 2: Mandatory Webhook Signature Verification (CRITICAL)

**File:** `backend/app/api/v1/endpoints/payments.py`

**Replace lines 49-74:**
```python
@router.post("/ecocash/callback")
async def ecocash_webhook(payload: EcoCashCallbackPayload, request: Request, db: Session = Depends(get_db)):
    """Production EcoCash callback receiver with HMAC signature verification."""
    signature = request.headers.get("X-EcoCash-Signature")
    secret_key = os.getenv("ECOCASH_WEBHOOK_SECRET", "").encode("utf-8")
    
    # MANDATORY verification - fail closed
    if not secret_key:
        logger.error("ECOCASH_WEBHOOK_SECRET not configured - rejecting webhook")
        raise HTTPException(status_code=500, detail="Webhook verification not configured")
    
    if not signature:
        logger.warning("EcoCash webhook missing signature")
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    try:
        raw_body = await request.body()
        expected = hmac.new(secret_key, raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            logger.warning("EcoCash webhook invalid signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
    except Exception as e:
        logger.error(f"EcoCash webhook verification error: {e}")
        raise HTTPException(status_code=401, detail="Signature verification failed")

    try:
        success = process_ecocash_callback(
            db,
            payload.request_id,
            "PAID" if payload.status == "SUCCESS" else "FAILED",
            payload.merchant_reference,
        )
        if not success:
            raise HTTPException(status_code=400, detail="Callback failed to process")
        return {"status": "accepted", "message": "Transaction state updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"EcoCash webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="EcoCash service error")
```

---

## PATCH 3: OneMoney Webhook Fix (HIGH)

**File:** `backend/app/services/webhook_verification.py`

**Replace lines 54-66:**
```python
@staticmethod
def verify_onemoney(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify OneMoney webhook signature using HMAC-SHA256.
    """
    if not secret:
        logger.error("ONEMONEY_WEBHOOK_SECRET not configured")
        raise ValueError("ONEMONEY_WEBHOOK_SECRET not configured")
    
    if not signature:
        return False
    
    try:
        expected = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)
    except Exception as e:
        logger.error(f"OneMoney signature verification error: {e}")
        return False
```

---

## PATCH 4: Secret Key Validation (CRITICAL)

**File:** `backend/app/core/config.py`

**Add to Settings class:**
```python
from pydantic import field_validator, ValidationInfo

@field_validator("SECRET_KEY", "REFRESH_SECRET_KEY", "PIN_PEPPER")
@classmethod
def validate_secrets(cls, v: str, info: ValidationInfo) -> str:
    """Ensure secrets are properly configured and not default values."""
    field_name = info.field_name
    
    # Check for default/placeholder values
    placeholders = [
        "CHANGE_ME",
        "CHANGE-ME",
        "default",
        "secret",
        "password",
        "123456",
        "admin",
    ]
    
    v_lower = v.lower()
    if any(p in v_lower for p in placeholders):
        raise ValueError(f"{field_name} cannot contain placeholder values")
    
    # Minimum length requirements
    min_lengths = {
        "SECRET_KEY": 32,
        "REFRESH_SECRET_KEY": 32,
        "PIN_PEPPER": 16,
    }
    
    if len(v) < min_lengths.get(field_name, 16):
        raise ValueError(f"{field_name} must be at least {min_lengths.get(field_name, 16)} characters")
    
    return v

@field_validator("MASTER_TEST_LOGIN_ENABLED")
@classmethod
def validate_master_test(cls, v: bool, info: ValidationInfo) -> bool:
    """Prevent master test account in production."""
    app_env = os.getenv("APP_ENV", "development")
    if v and app_env == "production":
        raise ValueError("MASTER_TEST_LOGIN_ENABLED cannot be True in production environment")
    return v
```

---

## PATCH 5: USSD Brute Force Protection (MEDIUM)

**File:** `backend/app/services/ussd_service.py`

**Add at top of file:**
```python
from app.services.cache_service import cache_service

USSD_PIN_ATTEMPTS_LIMIT = 5  # per hour across all sessions
USSD_PIN_ATTEMPTS_WINDOW = 3600  # 1 hour
```

**Modify AUTH_PIN handler (lines 48-66):**
```python
if state == "AUTH_PIN":
    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user or not user.ussd_pin_hash:
        await delete_key(session_key)
        return USSDResponse(
            message="END Phone not registered or no PIN set.\nDownload ZimAgritrust app to register.",
            end_session=True,
        )
    
    # Check phone-based rate limiting across ALL sessions
    rate_limit_key = f"ussd:pin_attempts:{payload.phone_number}"
    total_attempts = await cache_service.get_counter(rate_limit_key)
    
    if total_attempts >= USSD_PIN_ATTEMPTS_LIMIT:
        await delete_key(session_key)
        return USSDResponse(
            message="END Too many PIN attempts. Please try again in 1 hour.",
            end_session=True,
        )
    
    from app.core.security import verify_password
    if not verify_password(latest, user.ussd_pin_hash):
        # Increment global counter
        await cache_service.increment_counter(rate_limit_key, USSD_PIN_ATTEMPTS_WINDOW)
        
        # Track per-session attempts for UX
        sess["pin_attempts"] = sess.get("pin_attempts", 0) + 1
        if sess["pin_attempts"] >= 3:
            await delete_key(session_key)
            return USSDResponse(message="END Too many wrong PINs. Dial *123# to retry.", end_session=True)
        await set_json(session_key, sess)
        return USSDResponse(message=f"CON Wrong PIN ({sess['pin_attempts']}/3). Try again:")
    
    # Success - clear attempts
    sess["pin_attempts"] = 0
    selection = sess.get("pending_selection")
    return await self._route(db, payload.phone_number, selection, session_key)
```

---

## PATCH 6: Docker Compose Security Hardening

**File:** `docker-compose.yml`

**Replace PostgreSQL service:**
```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: agri_trust
    POSTGRES_USER: agritrust
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  expose:
    - "5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
  networks:
    - backend-network
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U agritrust"]
    interval: 10s
    retries: 5
    timeout: 5s
  # NO ports mapping to host in production
  # Use: docker-compose exec postgres psql -U agritrust
```

**Replace Redis service:**
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  expose:
    - "6379"
  networks:
    - backend-network
  volumes:
    - redis_data:/data
  # NO ports mapping to host in production
```

**Add network definition:**
```yaml
networks:
  backend-network:
    driver: bridge
    internal: true  # No external access
```

---

## PATCH 7: Redis Authentication in Cache Service

**File:** `backend/app/services/cache_service.py`

**Update connection (lines 47-58):**
```python
async def get_cache_client() -> redis_async.Redis:
    global _async_client, _incr_script
    if _async_client is not None:
        return _async_client
    
    # Parse password from URL or use separate setting
    redis_url = settings.REDIS_URL
    if hasattr(settings, 'REDIS_PASSWORD') and settings.REDIS_PASSWORD:
        # Inject password into URL
        if '://' in redis_url:
            protocol, rest = redis_url.split('://', 1)
            redis_url = f"{protocol}://:{settings.REDIS_PASSWORD}@{rest}"
    
    client: redis_async.Redis = redis_async.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    await client.ping()
    _incr_script = client.register_script(_INCR_WITH_TTL_SCRIPT)
    _async_client = client
    return _async_client
```

**Update sync client (lines 71-78):**
```python
def get_sync_client() -> redis_sync.Redis:
    global _sync_client
    if _sync_client is not None:
        return _sync_client
    
    redis_url = settings.REDIS_URL
    if hasattr(settings, 'REDIS_PASSWORD') and settings.REDIS_PASSWORD:
        if '://' in redis_url:
            protocol, rest = redis_url.split('://', 1)
            redis_url = f"{protocol}://:{settings.REDIS_PASSWORD}@{rest}"
    
    _sync_client = redis_sync.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )
    _sync_client.ping()
    return _sync_client
```

---

## PATCH 8: Idempotency Lock Timeout Fix (MEDIUM)

**File:** `backend/app/core/idempotency.py`

**Update constants (lines 29-32):**
```python
_LOCK_TTL = 30        # seconds — max time a request may hold the processing lock
_RESULT_TTL = 86400   # seconds — 24h result cache
_POLL_INTERVAL = 0.1  # seconds between lock-wait polls
_POLL_TIMEOUT = 35    # MUST be > _LOCK_TTL to detect lock expiration
```

**Update polling logic (lines 109-132):**
```python
if not lock_acquired:
    # Another request is currently processing this key.
    # Poll until the result appears, we time out, or lock expires.
    elapsed = 0.0
    lock_still_present = True
    
    while elapsed < _POLL_TIMEOUT:
        await asyncio.sleep(_POLL_INTERVAL)
        elapsed += _POLL_INTERVAL
        
        # Check if result appeared
        cached = await cache_service.get(result_key)
        if cached:
            payload = json.loads(cached)
            return JSONResponse(
                content=payload["body"],
                status_code=payload["status_code"],
                headers={"X-Idempotency-Replayed": "true"},
            )
        
        # Check if lock disappeared (processing failed/crashed)
        lock_exists = await cache_service.get(lock_key)
        if not lock_exists and lock_still_present:
            # Lock expired without result → processing failed
            logger.warning(f"Idempotency lock expired without result for key: {idempotency_key}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Previous request processing failed. Please retry with same Idempotency-Key.",
            )
        lock_still_present = lock_exists
    
    # Timed out waiting for result
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="A request with this Idempotency-Key is currently being processed. Retry after a few seconds.",
    )
```

---

## PATCH 9: Redis Degraded Mode for Rate Limiting

**File:** `backend/app/core/security_middleware.py`

**Add imports and in-memory fallback:**
```python
import time
from collections import defaultdict

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Emergency in-memory counters for when Redis is down
        self._emergency_counters = {}
        self._emergency_lock = asyncio.Lock()
        self._last_cleanup = time.time()
    
    async def _check_rate_limit(self, request: Request, client_ip: str) -> bool:
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        limit = (
            settings.RATE_LIMIT_API_GENERAL // 2
            if self._is_admin_route(request)
            else settings.RATE_LIMIT_API_GENERAL
        )
        key = f"rate_limit:{client_ip}:{request.url.path}"
        
        try:
            count = await cache_service.increment_counter(key, window)
            if int(count) > limit:
                logger.warning(
                    "rate_limit_exceeded",
                    extra={"key": key, "count": count, "limit": limit, "ip": client_ip},
                )
                return False
            return True
        except Exception as exc:
            logger.error(
                "rate_limit_redis_unavailable",
                extra={"error": str(exc), "ip": client_ip, "path": request.url.path},
            )
            # Degraded mode: in-memory fallback
            return await self._emergency_rate_limit(client_ip, request.url.path, limit, window)
    
    async def _emergency_rate_limit(self, client_ip: str, path: str, limit: int, window: int) -> bool:
        """Emergency in-memory rate limiting when Redis is down."""
        async with self._emergency_lock:
            now = time.time()
            bucket = int(now / window)
            key = f"{client_ip}:{path}:{bucket}"
            
            # Cleanup old buckets every 60 seconds
            if now - self._last_cleanup > 60:
                current_bucket = bucket
                self._emergency_counters = {
                    k: v for k, v in self._emergency_counters.items()
                    if int(k.split(":")[-1]) >= current_bucket - 1
                }
                self._last_cleanup = now
            
            current = self._emergency_counters.get(key, 0)
            if current >= limit:
                logger.warning(f"Emergency rate limit exceeded for {client_ip}")
                return False
            
            self._emergency_counters[key] = current + 1
            return True
```

---

## PATCH 10: Audit Logging Enablement

**File:** `backend/app/core/config.py`

**Change line 146:**
```python
ADMIN_AUDIT_LOGGING: bool = True  # Enable by default
```

**File:** `backend/app/core/security_middleware.py`

**Update AuditLoggingMiddleware (lines 248-298):**
```python
class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Audit logging middleware for admin actions.
    Logs all admin operations with tamper-resistant hashing.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        if not self._is_admin_route(request):
            return await call_next(request)
        
        # Get user info if authenticated
        user_info = self._get_user_info(request)
        client_ip = self._get_client_ip(request)
        request_id = request.headers.get("X-Request-ID", str(int(time.time() * 1000000)))
        
        # Create audit entry
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": client_ip,
            "user": user_info,
            "user_agent": request.headers.get("User-Agent", "")[:100],
        }
        
        # Process request
        try:
            response = await call_next(request)
            audit_entry["status_code"] = response.status_code
            audit_entry["outcome"] = "success" if response.status_code < 400 else "failure"
        except Exception as e:
            audit_entry["status_code"] = 500
            audit_entry["outcome"] = "error"
            audit_entry["error"] = str(e)[:200]
            raise
        finally:
            # Log with chain hashing for tamper detection
            await self._log_audit_entry(audit_entry)
        
        return response
    
    async def _log_audit_entry(self, entry: dict):
        """Log audit entry with tamper-resistant hashing."""
        from app.core.security import hash_sensitive_value, sign_request
        
        # Get previous hash for chaining
        prev_hash = await cache_service.get("audit:last_hash") or "0" * 64
        
        # Create entry hash
        entry_str = json.dumps(entry, sort_keys=True, default=str)
        entry_hash = hashlib.sha256(entry_str.encode()).hexdigest()
        
        # Chain hash
        chained_hash = hashlib.sha256(f"{prev_hash}:{entry_hash}".encode()).hexdigest()
        
        # Sign the chained hash
        signature = sign_request({"hash": chained_hash, "timestamp": entry["timestamp"]})
        
        # Store complete audit record
        audit_record = {
            **entry,
            "entry_hash": entry_hash,
            "chained_hash": chained_hash,
            "signature": signature,
            "previous_hash": prev_hash,
        }
        
        # Log and store
        logger.info(f"AUDIT | {json.dumps(audit_record, default=str)}")
        await cache_service.set("audit:last_hash", chained_hash, expire=86400 * 365)  # 1 year
        
        # TODO: Also write to persistent store (S3, CloudWatch, or separate DB)
```

---

## DEPLOYMENT CHECKLIST

### Before Production Deploy

- [ ] All secrets generated with `openssl rand -hex 32`
- [ ] PostgreSQL password set via environment variable
- [ ] Redis password configured and enabled
- [ ] Webhook secrets configured for all payment providers
- [ ] MASTER_TEST_LOGIN_ENABLED explicitly set to `false`
- [ ] CORS_ORIGINS contains only production domains (no localhost)
- [ ] ALLOWED_HOSTS configured correctly
- [ ] ADMIN_AUDIT_LOGGING enabled
- [ ] Nginx rate limiting zones active
- [ ] SSL/TLS certificates installed
- [ ] HSTS headers enabled
- [ ] Sentry DSN configured for error tracking

### Verification Commands

```bash
# Check for default secrets
grep -r "CHANGE_ME" backend/app/core/config.py || echo "OK: No default secrets"
grep -r "password.*password" docker-compose.yml || echo "OK: No default passwords"

# Verify Redis auth
redis-cli -h localhost -p 6380 AUTH your_password PING

# Test webhook signature
curl -X POST http://api.zimagritrust.co.zw/api/v1/payments/ecocash/callback \
  -H "Content-Type: application/json" \
  -d '{}' && echo "FAIL: Should require signature" || echo "OK: Requires signature"

# Test JWT algorithm
echo "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIn0." | \
  base64 -d 2>/dev/null && echo "FAIL: Algorithm confusion possible"
```

---

**END OF PATCHES**
