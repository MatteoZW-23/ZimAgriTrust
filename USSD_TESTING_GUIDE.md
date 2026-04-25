# USSD Testing Guide

## 🧪 Complete Testing Scenarios

### Prerequisites
```bash
# 1. Start services
docker-compose up -d postgres redis backend ussd-simulator

# 2. Sync existing users (one-time)
cd backend
python scripts/sync_ussd_pins.py

# 3. Open USSD Simulator
http://localhost:5000
```

## Test Suite 1: User Registration & Authentication

### Test 1.1: Register New User
```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test Farmer",
    "phone_number": "+263771234567",
    "password": "1234",
    "role": "FARMER"
  }'
```

**Expected**: 
- Status 200
- User created with both `password_hash` and `ussd_pin_hash` set

### Test 1.2: Initial USSD Dial
**USSD Simulator**:
- Session ID: `test-session-001`
- Phone: `+263771234567`
- Text: `` (empty)

**Expected**:
```
🇿🇼 AgriTrust Marketplace
━━━━━━━━━━━━━━━━━━━━
1. Sell Product
2. Buy Products
3. AI Price Intel
4. My Profile
5. My Wallet
6. Raise Dispute
7. Change PIN
8. Transactions
9. Help
```

### Test 1.3: PIN Authentication
**Text**: `4` (My Profile - requires PIN)

**Expected**:
```
CON Enter your secret 4-digit PIN
```

**Text**: `4*1234`

**Expected**: Profile information displayed

### Test 1.4: Wrong PIN
**Text**: `4*9999`

**Expected**:
```
CON Incorrect PIN. Try again:
```

## Test Suite 2: Sell Product Flow

### Test 2.1: Complete Sell Flow
| Step | Text Input | Expected Response |
|------|-----------|-------------------|
| 1 | `1` | `CON [SELL] Step 1/5\nEnter product name` |
| 2 | `1*Maize` | `CON Enter quantity in kilograms` |
| 3 | `1*Maize*500` | `CON Enter product grade (A/B/C)` |
| 4 | `1*Maize*500*A` | `CON Enter price per kg (USD)` |
| 5 | `1*Maize*500*A*2.50` | `CON Enter province` |
| 6 | `1*Maize*500*A*2.50*Harare` | `END ✅ Listing Created!` |

**Verify in Database**:
```sql
SELECT * FROM listings 
WHERE seller_id = (SELECT id FROM users WHERE phone_number = '+263771234567')
ORDER BY created_at DESC LIMIT 1;
```

**Expected**:
- product_type: "Maize"
- quantity: 500
- grade: "A"
- price_per_unit: 2.50
- location_province: "Harare"
- status: "ACTIVE"

### Test 2.2: Invalid Quantity
**Text**: `1*Maize*abc`

**Expected**:
```
CON Invalid number. Enter quantity in kg:
```

### Test 2.3: Negative Quantity
**Text**: `1*Maize*-100`

**Expected**:
```
CON Invalid quantity. Enter a positive number:
```

### Test 2.4: Invalid Price
**Text**: `1*Maize*500*A*xyz`

**Expected**:
```
CON Invalid amount. Enter price in USD:
```

## Test Suite 3: Buy Product Flow

### Test 3.1: Browse Products
**Setup**: Create some listings first (use Test 2.1)

**Text**: `2` (requires PIN)

**Expected**:
```
CON Enter your secret 4-digit PIN
```

**Text**: `2*1234`

**Expected**:
```
CON Available Products:
1. Maize 500kg @$2.50/kg
2. [other listings...]
0. Back to Menu
```

### Test 3.2: Select Product
**Text**: `2*1234*1` (select first product)

**Expected**:
```
CON Enter quantity to buy (kg)
```

### Test 3.3: Enter Quantity
**Text**: `2*1234*1*100`

**Expected**:
```
CON Confirm Purchase:
Maize 100kg
$2.50/kg
Total: $250.00
1. Confirm
2. Cancel
```

### Test 3.4: Confirm Purchase
**Text**: `2*1234*1*100*1`

**Expected**:
```
END ✅ Offer Sent!
Offer ID: #[number]
Total: $250.00
Seller will be notified.
```

**Verify in Database**:
```sql
SELECT * FROM offers 
WHERE buyer_id = (SELECT id FROM users WHERE phone_number = '+263771234567')
ORDER BY created_at DESC LIMIT 1;
```

### Test 3.5: Quantity Exceeds Stock
**Text**: `2*1234*1*1000` (more than available)

**Expected**:
```
CON Only 500kg available. Enter quantity:
```

### Test 3.6: Cancel Purchase
**Text**: `2*1234*1*100*2`

**Expected**:
```
END Purchase cancelled.
```

## Test Suite 4: AI Price Intelligence

### Test 4.1: View Prices
**Text**: `3`

**Expected**:
```
CON 🤖 AI Price Intel (USD/t)
Maize: $[price]
Soya: $[price]
Wheat: $[price]
Tobacco: $[price]

0. Back
```

**Note**: Prices come from ML service or defaults

### Test 4.2: Return to Menu
**Text**: `3*0`

**Expected**: Main menu displayed

## Test Suite 5: Profile & Trust Score

### Test 5.1: View Profile
**Text**: `4*1234`

**Expected**:
```
END 👤 PROFILE
Name: Test Farmer
Trust Score: [0-100]/100
Credit: CLASS [A/B/C]
Active Listings: [number]
Total Orders: [number]
Verified: [✅/❌]
```

### Test 5.2: Profile Without PIN
**Text**: `4`

**Expected**: PIN prompt first

## Test Suite 6: Wallet & Balances

### Test 6.1: Farmer Wallet
**Text**: `5*1234`

**Expected**:
```
END 💰 WALLET (USD)
Released: $[amount]
In Escrow: $[amount]
Pending: $[amount]
Total: $[amount]
```

### Test 6.2: Buyer Ledger
**Setup**: Register a buyer user

**Text**: `5*1234`

**Expected**:
```
END 💳 LEDGER (USD)
Completed: $[amount]
In Escrow: $[amount]
Pending: $[amount]
Total Spent: $[amount]
```

## Test Suite 7: Dispute Resolution

### Test 7.1: Raise Dispute (With Orders)
**Setup**: Create an order in DELIVERED status

**Text**: `6*1234`

**Expected**:
```
END ✅ Dispute #[number] Created
Agent will call you within 24hrs
```

**Verify in Database**:
```sql
SELECT * FROM disputes 
WHERE raised_by = (SELECT id FROM users WHERE phone_number = '+263771234567')
ORDER BY created_at DESC LIMIT 1;
```

### Test 7.2: Raise Dispute (No Orders)
**Text**: `6*1234`

**Expected**:
```
END No recent orders to dispute.
Contact support: +263771234567
```

## Test Suite 8: Change PIN

### Test 8.1: Successful PIN Change
| Step | Text Input | Expected Response |
|------|-----------|-------------------|
| 1 | `7*1234` | `CON Enter new 4-digit PIN:` |
| 2 | `7*1234*5678` | `CON Confirm new PIN:` |
| 3 | `7*1234*5678*5678` | `END ✅ PIN changed successfully!` |

**Verify**: Try logging in with new PIN (5678)

### Test 8.2: Invalid PIN Format
**Text**: `7*1234*12` (only 2 digits)

**Expected**:
```
CON PIN must be 4 digits. Enter new PIN:
```

### Test 8.3: PIN Mismatch
**Text**: `7*1234*5678*9999`

**Expected**:
```
END PINs don't match. Try again.
```

### Test 8.4: Non-Numeric PIN
**Text**: `7*1234*abcd`

**Expected**:
```
CON PIN must be 4 digits. Enter new PIN:
```

## Test Suite 9: Transaction History

### Test 9.1: View Transactions
**Setup**: Create some transactions

**Text**: `8*1234`

**Expected**:
```
CON Recent Transactions:
1. PAYMENT $250.00 (23/04)
2. WITHDRAWAL $100.00 (22/04)
3. PAYMENT $500.00 (20/04)
...
0. Back
```

### Test 9.2: No Transactions
**Text**: `8*1234`

**Expected**:
```
END No transactions yet.
```

## Test Suite 10: Help & Navigation

### Test 10.1: View Help
**Text**: `9`

**Expected**:
```
END 📖 HELP
1. Sell: List your products
2. Buy: Browse & purchase
...
Support: +263771234567
```

### Test 10.2: Back to Menu
**Text**: `3*0` (from any submenu)

**Expected**: Main menu displayed

### Test 10.3: Invalid Option
**Text**: `99`

**Expected**:
```
END Invalid option. Dial *123# again.
```

## Test Suite 11: Session Management

### Test 11.1: Session Persistence
1. Start session: `1*Maize`
2. Wait 2 minutes
3. Continue: `1*Maize*500`

**Expected**: Session continues from where it left off

### Test 11.2: Session Timeout
1. Start session: `1*Maize`
2. Wait 6 minutes (> 5 min TTL)
3. Try to continue: `1*Maize*500`

**Expected**: Session expired, start over

### Test 11.3: Session Reset
**Text**: Click "Reset Session" button in simulator

**Expected**: New session ID generated, state cleared

## Test Suite 12: Error Handling

### Test 12.1: Unregistered Phone
**Text**: Use phone number not in database

**Expected**:
```
END Unregistered phone number or no PIN set.
```

### Test 12.2: Backend Unavailable
**Setup**: Stop backend service

**Expected** (in simulator):
```
Could not reach FastAPI backend: [error]
```

### Test 12.3: Redis Unavailable
**Setup**: Stop Redis service

**Expected**: Falls back to in-memory cache, continues working

## Test Suite 13: Multi-User Scenarios

### Test 13.1: Concurrent Sessions
1. User A: Session `session-a`, Phone `+263771111111`
2. User B: Session `session-b`, Phone `+263772222222`
3. Both navigate independently

**Expected**: No session interference

### Test 13.2: Same User, Different Sessions
1. Session 1: Start sell flow
2. Session 2: Start buy flow
3. Both should work independently

**Expected**: Sessions isolated by session_id

## Performance Tests

### Test P1: Response Time
**Measure**: Time from request to response

**Target**: < 500ms for all operations

**Test**:
```bash
time curl -X POST http://localhost:8080/api/v1/ussd/session \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","phone_number":"+263771234567","text":"1"}'
```

### Test P2: Load Test
**Tool**: Apache Bench or k6

```bash
ab -n 1000 -c 10 -p ussd_request.json \
  -T application/json \
  http://localhost:8080/api/v1/ussd/session
```

**Target**: 
- 100 requests/second
- < 1% error rate

### Test P3: Session Storage
**Test**: Create 1000 concurrent sessions

**Verify**: Redis memory usage stays reasonable

## Integration Tests

### Test I1: SMS Notification
**Trigger**: Raise dispute

**Verify**: SMS sent via notification service

### Test I2: Database Consistency
**Test**: Complete sell flow

**Verify**: 
- Listing created
- User trust score updated
- Transaction logged

### Test I3: Cache Invalidation
**Test**: 
1. View prices (cached)
2. Update price in database
3. Wait for cache expiry
4. View prices again

**Verify**: New prices displayed

## Regression Tests

### Test R1: PIN Sync
**Verify**: 
- New users have both password_hash and ussd_pin_hash
- Password reset updates both fields
- Agent recruitment sets both fields

### Test R2: Backward Compatibility
**Test**: Existing users (before PIN sync)

**Verify**: Migration script updates them correctly

## Security Tests

### Test S1: PIN Brute Force
**Test**: Try 10 wrong PINs rapidly

**Expected**: Account locked after 5 attempts

### Test S2: Session Hijacking
**Test**: Try to use another user's session_id

**Expected**: Phone number validation prevents access

### Test S3: SQL Injection
**Test**: Enter `'; DROP TABLE users; --` as product name

**Expected**: Safely escaped, no SQL execution

## Acceptance Criteria

### ✅ All Tests Pass
- [ ] User Registration & Auth (4 tests)
- [ ] Sell Product Flow (4 tests)
- [ ] Buy Product Flow (6 tests)
- [ ] AI Price Intelligence (2 tests)
- [ ] Profile & Trust Score (2 tests)
- [ ] Wallet & Balances (2 tests)
- [ ] Dispute Resolution (2 tests)
- [ ] Change PIN (4 tests)
- [ ] Transaction History (2 tests)
- [ ] Help & Navigation (3 tests)
- [ ] Session Management (3 tests)
- [ ] Error Handling (3 tests)
- [ ] Multi-User Scenarios (2 tests)
- [ ] Performance Tests (3 tests)
- [ ] Integration Tests (3 tests)
- [ ] Regression Tests (2 tests)
- [ ] Security Tests (3 tests)

### ✅ Performance Metrics
- [ ] Average response time < 500ms
- [ ] 95th percentile < 1000ms
- [ ] Error rate < 1%
- [ ] Session success rate > 95%

### ✅ User Experience
- [ ] Clear error messages
- [ ] Intuitive navigation
- [ ] Consistent formatting
- [ ] Helpful prompts

---

**Total Tests**: 50+  
**Estimated Testing Time**: 4-6 hours  
**Automation**: Can be scripted with pytest + requests
