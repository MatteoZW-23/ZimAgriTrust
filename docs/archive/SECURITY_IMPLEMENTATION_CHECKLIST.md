# ⚡ SECURITY FIXES IMPLEMENTATION CHECKLIST

**Start Date**: ___________  
**Target Completion**: 1 Week (CRITICAL) + 3 Weeks (HIGH/MEDIUM)

---

## PHASE 1: CRITICAL FIXES (Week 1)

### 1. Payment Webhook Verification
**File**: `backend/app/api/v1/endpoints/payments.py`  
**Time**: 4 hours  
**Status**: ⏳ NOT STARTED

#### Tasks
- [ ] Backup original file
- [ ] Add mandatory signature verification (no optional check)
- [ ] Add IP whitelist check
- [ ] Add idempotency key validation
- [ ] Add timestamp validation (prevent replay)
- [ ] Add rate limiting per transaction
- [ ] Test with valid/invalid signatures
- [ ] Test with invalid IP addresses
- [ ] Test with old timestamps
- [ ] Code review (2 reviewers)
- [ ] Merge to security branch
- [ ] Deploy to staging

**Code Template**: See SECURITY_REMEDIATION_CODE.md Section 1

**Tests Required**:
```python
- test_missing_signature_401()
- test_invalid_signature_401()
- test_unauthorized_ip_403()
- test_duplicate_callback_accepted()
- test_old_timestamp_rejected()
```

---

### 2. Authorization Checks on Transactions
**File**: `backend/app/api/v1/endpoints/transactions.py`  
**Time**: 2 hours  
**Status**: ⏳ NOT STARTED

#### Tasks
- [ ] Add authorization check to `get_order_transactions()`
- [ ] Add authorization check to `get_order_details()`
- [ ] Add authorization check to `list_order_reviews()`
- [ ] Log unauthorized access attempts
- [ ] Test with unauthorized user
- [ ] Test with authorized buyer/seller/admin
- [ ] Code review (2 reviewers)
- [ ] Merge to security branch
- [ ] Deploy to staging

**Code Template**: See SECURITY_REMEDIATION_CODE.md Section 2

**Tests Required**:
```python
- test_unauthorized_user_403()
- test_buyer_can_view_own_orders()
- test_seller_can_view_own_orders()
- test_admin_can_view_any_order()
```

---

### 3. Atomic Transaction Handling
**File**: `backend/app/services/escrow_service.py`  
**Time**: 3 hours  
**Status**: ⏳ NOT STARTED

#### Tasks
- [ ] Update `release_payment()` with FOR UPDATE lock
- [ ] Test concurrent requests (simulate race condition)
- [ ] Verify only one release succeeds
- [ ] Verify other releases fail gracefully
- [ ] Test transaction rollback on error
- [ ] Code review (2 reviewers)
- [ ] Merge to security branch
- [ ] Deploy to staging

**Code Template**: See SECURITY_REMEDIATION_CODE.md Section 3

**Tests Required**:
```python
- test_concurrent_release_only_one_succeeds()
- test_second_release_fails()
- test_rollback_on_error()
- test_idempotency_after_failure()
```

---

### 4. Input Validation
**File**: `backend/app/schemas/transaction.py` and others  
**Time**: 2 hours  
**Status**: ⏳ NOT STARTED

#### Tasks
- [ ] Add strict validation to `DeliveryConfirmRequest`
- [ ] Add validation to `ListingCreate`
- [ ] Add validation to `PaymentInitiateRequest`
- [ ] Add regex patterns (alphanumeric only)
- [ ] Add length limits
- [ ] Test empty/null inputs
- [ ] Test negative quantities
- [ ] Test negative prices
- [ ] Test SQL injection payloads
- [ ] Code review
- [ ] Merge to security branch
- [ ] Deploy to staging

**Code Template**: See SECURITY_REMEDIATION_CODE.md Section 4

**Tests Required**:
```python
- test_empty_handover_code_rejected()
- test_invalid_handover_code_rejected()
- test_negative_quantity_rejected()
- test_negative_price_rejected()
- test_sql_injection_rejected()
- test_html_xss_rejected()
```

---

### 5. CSRF Protection
**File**: `backend/app/core/main.py`  
**Time**: 3 hours  
**Status**: ⏳ NOT STARTED

#### Tasks
- [ ] Install `fastapi-csrf-protect` package
- [ ] Add CSRF middleware to app
- [ ] Implement token generation endpoint
- [ ] Add CSRF token validation to all POST/PUT/DELETE endpoints
- [ ] Test with valid CSRF token
- [ ] Test with missing CSRF token
- [ ] Test with invalid CSRF token
- [ ] Code review
- [ ] Merge to security branch
- [ ] Deploy to staging

**Code Template**: See SECURITY_REMEDIATION_CODE.md Section 5

**Tests Required**:
```python
- test_post_without_csrf_token_403()
- test_post_with_valid_csrf_token_success()
- test_post_with_invalid_csrf_token_403()
- test_get_request_not_requires_csrf()
```

---

### 6. HTTPS Enforcement
**File**: `backend/app/core/main.py`  
**Time**: 1 hour  
**Status**: ⏳ NOT STARTED

#### Tasks
- [ ] Install `fastapi.middleware.httpsredirect`
- [ ] Add HTTPSRedirectMiddleware
- [ ] Add HSTS headers
- [ ] Add Secure cookie flag
- [ ] Test HTTP → HTTPS redirect
- [ ] Code review
- [ ] Merge to security branch
- [ ] Deploy to staging

**Tests Required**:
```python
- test_http_redirects_to_https()
- test_hsts_header_present()
- test_secure_cookie_flag_set()
```

---

### 7. Rate Limiting
**File**: `backend/app/core/main.py` and endpoints  
**Time**: 2 hours  
**Status**: ⏳ NOT STARTED

#### Tasks
- [ ] Install `slowapi` package
- [ ] Add rate limiting middleware
- [ ] Add limit to `/ecocash/callback` (30/minute)
- [ ] Add limit to `/payments/initiate` (5/minute)
- [ ] Add limit to `/{listing_id}/offers` (10/minute)
- [ ] Add limit to `/search` (100/minute)
- [ ] Test rate limit enforcement
- [ ] Test 429 response on limit exceeded
- [ ] Code review
- [ ] Merge to security branch
- [ ] Deploy to staging

**Code Template**: See SECURITY_REMEDIATION_CODE.md Section 6

**Tests Required**:
```python
- test_rate_limit_payment_endpoint()
- test_429_response_when_limit_exceeded()
- test_rate_limit_reset_after_minute()
```

---

### 8. Idempotency for Payments
**File**: `backend/app/api/v1/endpoints/payments.py`  
**Time**: 2 hours  
**Status**: ⏳ NOT STARTED

#### Tasks
- [ ] Add `idempotency_key` field to `PaymentInitiateRequest`
- [ ] Check for existing transaction with same key
- [ ] Return existing transaction if found
- [ ] Create new transaction with idempotency key stored
- [ ] Test duplicate payment requests
- [ ] Test idempotency key uniqueness
- [ ] Code review
- [ ] Merge to security branch
- [ ] Deploy to staging

**Code Template**: See SECURITY_REMEDIATION_CODE.md Section 8

**Tests Required**:
```python
- test_duplicate_payment_returns_existing()
- test_same_idempotency_key_same_transaction()
- test_different_idempotency_key_new_transaction()
```

---

## PHASE 1 SUMMARY

**Total Time**: ~19 hours (≈ 2-3 days with 2 developers)

**Critical Fixes**:
- [x] 1. Payment verification
- [x] 2. Authorization checks
- [x] 3. Atomic transactions
- [x] 4. Input validation
- [x] 5. CSRF protection
- [x] 6. HTTPS enforcement
- [x] 7. Rate limiting
- [x] 8. Idempotency

**Pre-Deployment Testing**:
- [ ] All security tests pass
- [ ] All regression tests pass
- [ ] Staging deployment successful
- [ ] Security team approval

**Deployment Window**: Friday EOD, Week 1

---

## PHASE 2: HIGH PRIORITY FIXES (Week 2-3)

### 1. Prevent Self-Trading
**File**: `backend/app/api/v1/endpoints/listings.py`  
**Time**: 1 hour  
**Status**: ⏳ NOT STARTED

- [ ] Add check: `if listing.seller_id == current_user.id`
- [ ] Reject offer with 400 error
- [ ] Log attempt
- [ ] Test self-offer rejection

---

### 2. Fix Offer Acceptance Race Condition
**File**: `backend/app/api/v1/endpoints/listings.py`  
**Time**: 2 hours  
**Status**: ⏳ NOT STARTED

- [ ] Use `with_for_update()` on offer query
- [ ] Verify offer not already accepted
- [ ] Update status atomically
- [ ] Test concurrent acceptances
- [ ] Verify only one succeeds

---

### 3. Fix Market Analytics Authorization
**File**: `backend/app/api/v1/endpoints/market.py`  
**Time**: 1 hour  
**Status**: ⏳ NOT STARTED

- [ ] Add authorization check to `get_user_risk()`
- [ ] Only allow viewing own risk profile or admin access
- [ ] Log unauthorized access attempts
- [ ] Test unauthorized access rejected

---

### 4. Validate Search Filters
**File**: `backend/app/api/v1/endpoints/listings.py`  
**Time**: 1 hour  
**Status**: ⏳ NOT STARTED

- [ ] Add regex to `crop` query parameter
- [ ] Add regex to `location` query parameter
- [ ] Test XSS payload rejection
- [ ] Test valid searches still work

---

### 5. Add Comprehensive Audit Logging
**File**: `backend/app/models/audit_log.py` (new)  
**Time**: 3 hours  
**Status**: ⏳ NOT STARTED

- [ ] Create AuditLog model
- [ ] Create migration for audit_logs table
- [ ] Add logging to all payment endpoints
- [ ] Add logging to all transaction endpoints
- [ ] Add logging to all listing endpoints
- [ ] Test audit log entries created
- [ ] Test audit log is queryable

---

### 6. Add Fraud Detection Checks
**File**: `backend/app/services/escrow_service.py`  
**Time**: 2 hours  
**Status**: ⏳ NOT STARTED

- [ ] Check `order.fraud_risk_level` before releasing
- [ ] Reject payment if fraud level is "high"
- [ ] Add error message explaining hold
- [ ] Test high-risk order payment rejected
- [ ] Test normal order payment accepted

---

### 7. Add Transaction Isolation Level
**File**: `backend/app/core/config.py` or database config  
**Time**: 1 hour  
**Status**: ⏳ NOT STARTED

- [ ] Set PostgreSQL isolation to SERIALIZABLE for critical transactions
- [ ] Update SQLAlchemy session config
- [ ] Test transactions are isolated
- [ ] Monitor performance impact

---

### 8. Validate All Listing Fields
**File**: `backend/app/schemas/listing.py`  
**Time**: 1 hour  
**Status**: ⏳ NOT STARTED

- [ ] Add validators to product_type
- [ ] Add validators to quantity (>0, max 1M)
- [ ] Add validators to price (>0, max $100k)
- [ ] Add validators to location
- [ ] Test invalid values rejected

---

### 9. Add Pagination to List Endpoints
**File**: `backend/app/api/v1/endpoints/listings.py`  
**Time**: 2 hours  
**Status**: ⏳ NOT STARTED

- [ ] Add `skip` and `limit` query parameters
- [ ] Default limit to 20, max 100
- [ ] Add offset-based pagination
- [ ] Test pagination works correctly
- [ ] Test limit enforcement

---

### 10. Add IP Whitelisting for Webhooks
**File**: `backend/app/api/v1/endpoints/payments.py`  
**Time**: 1 hour  
**Status**: ⏳ NOT STARTED

- [ ] Add IP whitelist constants for EcoCash
- [ ] Add IP whitelist constants for OneMoney
- [ ] Check client IP in webhook handlers
- [ ] Reject if IP not whitelisted
- [ ] Test with whitelisted IP (accept)
- [ ] Test with non-whitelisted IP (reject)

---

### 11. Add Seller Identity Verification
**File**: `backend/app/models/user.py` or verification service  
**Time**: 2 hours  
**Status**: ⏳ NOT STARTED

- [ ] Add `id_verified` flag to User model
- [ ] Add `id_verification_date` field
- [ ] Require ID verification before selling
- [ ] Add verification endpoint
- [ ] Test unverified seller cannot create listing

---

### 12. Implement Request Size Limits
**File**: `backend/app/core/main.py`  
**Time**: 1 hour  
**Status**: ⏳ NOT STARTED

- [ ] Add middleware to limit request body size
- [ ] Set limit to 1MB
- [ ] Return 413 if exceeded
- [ ] Test large payload rejected

---

## PHASE 2 SUMMARY

**Total Time**: ~18 hours (≈ 2-3 days with 2 developers)

**HIGH Priority Fixes**: 12 complete

**Deployment**: Week 3, Monday

---

## PHASE 3: MEDIUM PRIORITY FIXES (Week 4)

### Medium Priority Items
- [ ] 1. Add CSP headers
- [ ] 2. Add error message sanitization
- [ ] 3. Implement API key rotation
- [ ] 4. Encrypt sensitive fields
- [ ] 5. Add request timeouts
- [ ] 6. Add backup testing
- [ ] 7. Add data retention policy
- [ ] 8. Add email verification for changes
- [ ] 9. Add admin action logging
- [ ] 10. Webhook signature replay protection
- [ ] 11. Comprehensive test coverage
- [ ] 12. Missing test edge cases
- [ ] 13. Documentation updates
- [ ] 14. Security training
- [ ] 15. Compliance audit

**Total Time**: ~25 hours

**Deployment**: Week 4

---

## TESTING CHECKLIST

### Unit Tests (Per Fix)
- [ ] Test valid inputs accepted
- [ ] Test invalid inputs rejected
- [ ] Test edge cases handled
- [ ] Test error messages appropriate

### Integration Tests
- [ ] Test payment flow end-to-end
- [ ] Test transaction flow with auth
- [ ] Test listing flow with validation
- [ ] Test concurrent operations

### Security Tests
- [ ] Test authorization enforcement
- [ ] Test CSRF protection
- [ ] Test rate limiting
- [ ] Test input validation
- [ ] Test SQL injection prevention
- [ ] Test XSS prevention

### Performance Tests
- [ ] Test atomic transactions don't cause deadlocks
- [ ] Test rate limiting doesn't affect normal users
- [ ] Test HTTPS encryption impact minimal

### Staging Validation
- [ ] Deploy to staging environment
- [ ] Run full test suite
- [ ] Security team review
- [ ] Performance validation
- [ ] Backup/recovery test

---

## ROLLBACK PLAN

**If Issues Found in Production**:

```bash
# 1. Stop traffic to bad version
# 2. Roll back to previous version
git checkout previous-tag
git push

# 3. Kill bad container
docker kill deployment-pod

# 4. Restart with old version
kubernetes rollout undo

# 5. Investigate issues
# 6. Fix and redeploy
```

**Rollback Decision Criteria**:
- ❌ Critical functionality broken
- ❌ Payment processing failing
- ❌ High error rates (>10%)
- ❌ Performance degradation (>50%)
- ❌ Security bypass found

---

## SUCCESS CRITERIA

### Phase 1 Complete (Week 1)
- [x] All 8 critical fixes deployed
- [x] Zero critical CVEs remaining
- [x] All security tests pass
- [x] No performance degradation
- [x] Audit logging working

### Phase 2 Complete (Week 3)
- [x] All 12 high fixes deployed
- [x] All high CVEs fixed
- [x] Audit trail complete
- [x] Rate limiting enforced

### Phase 3 Complete (Week 4)
- [x] All 15 medium fixes deployed
- [x] All CVEs below critical
- [x] Compliance standards met
- [x] Documentation complete

---

## METRICS TO TRACK

### Vulnerability Metrics
```
Start:     45 vulnerabilities (8 critical)
Week 1:    37 vulnerabilities (0 critical)
Week 2:    25 vulnerabilities
Week 3:    10 vulnerabilities
Week 4:     0 vulnerabilities
```

### Test Coverage
```
Start:    45% coverage
Week 1:   65% coverage
Week 2:   75% coverage
Week 4:   85% coverage (target)
```

### Mean Time to Detect (MTTD)
```
Payment fraud: < 5 minutes
Authorization breach: < 1 minute
System compromise: < 10 seconds
```

---

## SIGN-OFF

**Security Lead**: ________________  Date: _________

**Development Lead**: ________________  Date: _________

**DevOps Lead**: ________________  Date: _________

**Management Approval**: ________________  Date: _________

---

**Notes**:
- Document your progress daily
- Update status in this checklist
- Report blockers immediately
- Escalate delays to security lead

---

**Ready to Begin**: ________ YES ________ NO

**Start Date**: ___________  
**Expected Completion**: 1 month
