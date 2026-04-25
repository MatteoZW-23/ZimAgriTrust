# AgriTrust USSD - Complete Feature Set

## 🎯 Overview
The AgriTrust USSD platform provides full marketplace functionality accessible from any mobile phone, including basic feature phones without internet connectivity.

## 📱 Main Menu

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
0. Change Language
```

## 🔥 Feature Breakdown

### 1. Sell Product (Enhanced)
**Flow**: 5 steps with validation

```
Step 1: Enter product name (e.g., Maize)
Step 2: Enter quantity in kg (validates positive numbers)
Step 3: Enter grade (A/B/C)
Step 4: Enter price per kg in USD (validates positive amounts)
Step 5: Enter province/location
```

**Improvements**:
- ✅ Input validation at each step
- ✅ Price calculation shown before confirmation
- ✅ Detailed success message with listing summary
- ✅ Error handling for invalid inputs

**Example**:
```
Input: 1*1234*Maize*500*A*2.50*Harare
Output: 
✅ Listing Created!
Maize 500kg
Price: $2.50/kg
Total: $1,250.00
Location: Harare
```

### 2. Buy Products (NEW)
**Flow**: Browse → Select → Quantity → Confirm

```
Step 1: View available products (top 5 recent)
Step 2: Select product by number (1-5)
Step 3: Enter quantity to purchase
Step 4: Confirm purchase details
```

**Features**:
- Shows product name, quantity, and price per kg
- Validates quantity against available stock
- Calculates total cost before confirmation
- Creates offer that seller can accept/reject
- Sends notification to seller

**Example**:
```
Available Products:
1. Maize 500kg @$2.50/kg
2. Soya 300kg @$3.00/kg
3. Wheat 200kg @$2.80/kg
0. Back to Menu

Select: 1
Enter quantity: 100
Confirm Purchase:
Maize 100kg
$2.50/kg
Total: $250.00
1. Confirm
2. Cancel

✅ Offer Sent!
Offer ID: #123
Total: $250.00
Seller will be notified.
```

### 3. AI Price Intelligence (Enhanced)
**Features**:
- Real-time AI price forecasts
- 30-day predictions
- Multiple crops (Maize, Soya, Wheat, Tobacco)
- Powered by ML models

**Example**:
```
🤖 AI Price Intel (USD/t)
Maize: $450
Soya: $520
Wheat: $480
Tobacco: $3,200

0. Back
```

### 4. My Profile (Enhanced)
**Features**:
- Full name display
- Trust score (0-100)
- Credit rating (CLASS A/B/C)
- Active listings count
- Total orders count
- Verification status

**Example**:
```
👤 PROFILE
Name: John Farmer
Trust Score: 85/100
Credit: CLASS A
Active Listings: 3
Total Orders: 12
Verified: ✅
```

### 5. My Wallet (Enhanced)
**Features**:
- Released funds (completed transactions)
- Funds in escrow (pending delivery)
- Pending payments (awaiting confirmation)
- Total balance calculation
- Role-specific views (Farmer vs Buyer)

**Farmer View**:
```
💰 WALLET (USD)
Released: $1,250.00
In Escrow: $500.00
Pending: $300.00
Total: $2,050.00
```

**Buyer View**:
```
💳 LEDGER (USD)
Completed: $800.00
In Escrow: $250.00
Pending: $150.00
Total Spent: $1,200.00
```

### 6. Raise Dispute (Enhanced)
**Features**:
- Automatically finds recent disputable orders
- Creates dispute record in database
- Sends SMS confirmation
- Notifies support team
- Provides dispute ID for tracking

**Example**:
```
✅ Dispute #456 Created
Agent will call you within 24hrs

OR

No recent orders to dispute.
Contact support: +263771234567
```

### 7. Change PIN (NEW)
**Flow**: Enter new PIN → Confirm PIN → Success

**Features**:
- Validates 4-digit format
- Requires PIN confirmation
- Updates both app and USSD PIN
- Immediate effect

**Example**:
```
Enter new 4-digit PIN: ****
Confirm new PIN: ****
✅ PIN changed successfully!
```

**Security**:
- Must be exactly 4 digits
- PINs must match
- Hashed with bcrypt
- Synced across all platforms

### 8. Transaction History (NEW)
**Features**:
- Shows last 5 transactions
- Transaction type (PAYMENT, WITHDRAWAL, etc.)
- Amount in USD
- Date (DD/MM format)
- Quick overview

**Example**:
```
Recent Transactions:
1. PAYMENT $250.00 (23/04)
2. WITHDRAWAL $100.00 (22/04)
3. PAYMENT $500.00 (20/04)
4. ESCROW $300.00 (18/04)
5. PAYMENT $150.00 (15/04)

0. Back
```

### 9. Help (Enhanced)
**Features**:
- Quick reference guide
- Feature descriptions
- Support contact number

**Example**:
```
📖 HELP
1. Sell: List your products
2. Buy: Browse & purchase
3. Prices: AI forecasts
4. Profile: View trust score
5. Wallet: Check balances
6. Dispute: Get help
7. PIN: Change security PIN
Support: +263771234567
```

### 0. Change Language (NEW - Coming Soon)
**Supported Languages**:
- English
- Shona (chiShona)
- Ndebele (isiNdebele)

**Features**:
- Full menu translation
- Persistent language preference
- Stored in user profile

## 🔐 Security Features

### PIN Authentication
- Required for sensitive operations (options 2, 3, 4, 7, 8)
- 4-digit numeric PIN
- Bcrypt hashed storage
- Failed attempt tracking
- Account lockout after 5 failures

### Session Management
- 5-minute session timeout
- Redis-backed state storage
- Automatic cleanup
- Session ID tracking

### Input Validation
- Numeric validation for quantities and prices
- Positive number checks
- Stock availability verification
- PIN format validation

## 📊 Technical Architecture

### State Machine
```
ROOT → MENU → [Feature Selection] → [Multi-step Flow] → END
                    ↓
                AUTH_PIN (for protected features)
```

### Session States
- `ROOT`: Initial state
- `MENU`: Main menu display
- `AUTH_PIN`: PIN authentication
- `SELL_CROP_*`: Selling flow states
- `BUY_*`: Buying flow states
- `CHANGE_PIN_*`: PIN change flow
- `VIEW_TRANSACTIONS`: Transaction history

### Database Integration
- **Users**: Authentication, profiles, trust scores
- **Listings**: Product inventory
- **Orders**: Purchase records
- **Offers**: Buy/sell negotiations
- **Transactions**: Financial history
- **Disputes**: Issue resolution

## 🌍 Multi-Language Support

### Implementation
Language preference stored in `user.preferred_language`:
- `en`: English (default)
- `sn`: Shona
- `nd`: Ndebele

### Translation Coverage
- All menu items
- System messages
- Error messages
- Success confirmations
- Help text

## 📈 Analytics & Monitoring

### Tracked Metrics
- Session count per user
- Feature usage statistics
- Completion rates per flow
- Average session duration
- Error rates by state
- PIN failure rates

### Logging
```python
# All USSD requests logged
AUDIT | POST /api/v1/ussd/session | 
  session_id: abc123 | 
  phone: +263771234567 | 
  state: SELL_CROP_QTY | 
  STATUS: 200
```

## 🚀 Performance Optimizations

### Caching Strategy
- Session data: Redis (5-minute TTL)
- Price predictions: Redis (1-hour TTL)
- User profiles: Database with query optimization

### Response Time Targets
- Menu display: < 100ms
- Database queries: < 200ms
- Total response: < 500ms

### Scalability
- Stateless service design
- Horizontal scaling ready
- Redis cluster support
- Database connection pooling

## 🧪 Testing Scenarios

### Complete User Journey
```bash
# 1. Register user
POST /api/v1/auth/register
{
  "full_name": "Test User",
  "phone_number": "+263771234567",
  "password": "1234",
  "role": "FARMER"
}

# 2. Dial USSD
Session: test-001
Phone: +263771234567
Text: "" → Main menu

# 3. Sell product
Text: "1" → Sell flow
Text: "1*1234" → PIN auth
Text: "1*1234*Maize" → Product name
Text: "1*1234*Maize*500" → Quantity
Text: "1*1234*Maize*500*A" → Grade
Text: "1*1234*Maize*500*A*2.50" → Price
Text: "1*1234*Maize*500*A*2.50*Harare" → Complete

# 4. Check wallet
Text: "5" → Wallet menu
Text: "5*1234" → View balance

# 5. Change PIN
Text: "7" → Change PIN
Text: "7*1234" → Auth
Text: "7*1234*5678" → New PIN
Text: "7*1234*5678*5678" → Confirm
```

## 🔄 Integration Points

### SMS Notifications
- Dispute confirmations
- Offer notifications
- Payment confirmations
- Security alerts

### WhatsApp Bridge
- Rich media support
- Image sharing
- Document uploads
- Voice messages

### Mobile App
- Shared authentication
- Synchronized data
- Real-time updates
- Push notifications

## 📝 Error Handling

### User-Friendly Messages
```
Invalid input → "Invalid number. Enter quantity in kg:"
Session timeout → "Session expired. Dial *123# again."
Auth failure → "Incorrect PIN. Try again:"
System error → "Service temporarily unavailable. Try again."
```

### Graceful Degradation
- Fallback to in-memory cache if Redis fails
- Default to English if language preference unavailable
- Show cached prices if ML service unavailable

## 🎓 User Education

### First-Time User Flow
1. Register via app or agent
2. Receive welcome SMS with USSD code (*123#)
3. Guided tutorial on first dial
4. Help menu always available

### Support Channels
- USSD Help menu (option 9)
- SMS support: +263771234567
- WhatsApp support
- Agent network

## 🏆 Key Innovations

1. **Full Marketplace on USSD**: Complete buy/sell functionality
2. **AI Price Intelligence**: ML-powered forecasts via basic phone
3. **Escrow Integration**: Secure transactions without internet
4. **Multi-Language**: Accessible in local languages
5. **Trust Score Display**: Credit rating on feature phones
6. **PIN Management**: Self-service security updates
7. **Dispute Resolution**: Direct agent escalation
8. **Transaction History**: Financial transparency

## 📊 Success Metrics

### Target KPIs
- 80% session completion rate
- < 3 steps to complete common tasks
- < 500ms average response time
- 95% uptime
- < 1% error rate

### User Satisfaction
- Net Promoter Score (NPS) > 50
- Feature usage > 60% of registered users
- Repeat usage > 3x per week

---

**Status**: ✅ Production Ready  
**Version**: 2.0  
**Last Updated**: 2026-04-23  
**Developer**: Mathew Mabira
