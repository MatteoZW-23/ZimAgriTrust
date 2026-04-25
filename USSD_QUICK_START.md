# USSD Quick Start Guide

## 🚀 Start the System

```bash
# Start all services
docker-compose up -d

# Or start individually:
docker-compose up -d postgres redis backend ussd-simulator
```

## 🔧 Sync Existing Users (One-time)

If you have existing users in the database, run this migration:

```bash
cd backend
python scripts/sync_ussd_pins.py
```

This ensures existing users can use USSD with their current password.

## 🧪 Test USSD Flow

### 1. Open USSD Simulator
Navigate to: **http://localhost:5000**

### 2. Register a Test User (if needed)

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

### 3. Test Basic Flow

**In the USSD Simulator:**

| Field | Value |
|-------|-------|
| Session ID | `test-session-001` |
| Phone Number | `+263771234567` |
| USSD Text | `1` |

Click **"Send to Backend"**

You should see the main menu:
```
🇿🇼 AgriTrust Marketplace
Verification Dashboard
1. Sell Product (Escrow)
2. Buy Product
3. My Orders & Trust Score
4. EcoCash My Wallet
5. Raise Dispute
6. Help / Instructions
```

### 4. Test Selling a Product

Continue the session by updating the USSD Text field:

| Step | USSD Text | Expected Response |
|------|-----------|-------------------|
| 1 | `1` | "Enter your secret 4-digit PIN" |
| 2 | `1*1234` | "[SELL] Step 1/4 Enter product name" |
| 3 | `1*1234*Maize` | "Enter quantity in kilograms" |
| 4 | `1*1234*Maize*500` | "Enter product grade" |
| 5 | `1*1234*Maize*500*A` | "Enter province" |
| 6 | `1*1234*Maize*500*A*Harare` | "Listing created for Maize" |

### 5. Test Price Check (No PIN)

Reset session and try:

| USSD Text | Expected Response |
|-----------|-------------------|
| `2` | AI Price Intel with forecasts for Maize, Soya, Wheat |

### 6. Test Trust Score Check

| USSD Text | Expected Response |
|-----------|-------------------|
| `3` | "Enter your secret 4-digit PIN" |
| `3*1234` | Trust score, credit rating, recent trades |

## 🔍 Verify Backend Connection

Check backend logs:
```bash
docker-compose logs -f backend
```

You should see:
```
AUDIT | POST /api/v1/ussd/session | STATUS: 200 | TIME: 0.0234s
```

## 🐛 Troubleshooting

### USSD Simulator Can't Reach Backend

**Error**: "Could not reach FastAPI backend"

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8080/

# Check docker network
docker-compose ps

# Restart services
docker-compose restart backend ussd-simulator
```

### "Unregistered phone number or no PIN set"

**Solution**: Run the migration script or register a new user with a 4-digit PIN.

### Redis Connection Issues

**Solution**:
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

## 📱 Real Telecom Integration (Production)

When ready to connect to a real USSD gateway:

1. **Get webhook URL from your telecom provider** (Africa's Talking, Twilio, etc.)

2. **Configure their webhook to POST to**:
   ```
   https://your-domain.com/api/v1/ussd/session
   ```

3. **Request format** (already compatible):
   ```json
   {
     "session_id": "ATUid_abc123",
     "phone_number": "+263771234567",
     "text": "1*1234*Maize"
   }
   ```

4. **Response format** (already compatible):
   ```json
   {
     "message": "CON Enter quantity in kilograms",
     "end_session": false
   }
   ```

The backend is already production-ready for telecom gateway integration!

## ✅ Success Indicators

- ✅ USSD simulator loads at http://localhost:5000
- ✅ Backend responds to USSD requests
- ✅ Sessions persist across multiple requests
- ✅ PIN authentication works
- ✅ Listings are created successfully
- ✅ Session history shows in the simulator

---

**Need Help?** Check `USSD_INTEGRATION_STATUS.md` for detailed architecture and troubleshooting.
