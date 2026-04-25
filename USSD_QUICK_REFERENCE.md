# USSD Quick Reference Card

## 🚀 Quick Start
```bash
# 1. Start services
docker-compose up -d

# 2. Sync existing users (one-time)
python backend/scripts/sync_ussd_pins.py

# 3. Open simulator
http://localhost:5000
```

## 📱 USSD Code
**Dial**: `*123#`

## 🎯 Main Menu Options

| Option | Feature | PIN Required | Description |
|--------|---------|--------------|-------------|
| 1 | Sell Product | No | List products for sale (5 steps) |
| 2 | Buy Products | Yes | Browse and purchase products |
| 3 | AI Price Intel | No | View ML price forecasts |
| 4 | My Profile | Yes | Trust score, listings, orders |
| 5 | My Wallet | Yes | View balances (released/escrow/pending) |
| 6 | Raise Dispute | Yes | Create dispute, notify agent |
| 7 | Change PIN | Yes | Update 4-digit PIN |
| 8 | Transactions | Yes | View last 5 transactions |
| 9 | Help | No | Feature guide & support |

## 🔑 Default Test Credentials
```
Phone: +263771234567
PIN: 1234
```

## 📝 Common Flows

### Sell Product
```
1 → Maize → 500 → A → 2.50 → Harare
```

### Buy Product
```
2 → 1234 → 1 → 100 → 1
(PIN → Select → Quantity → Confirm)
```

### Check Wallet
```
5 → 1234
```

### Change PIN
```
7 → 1234 → 5678 → 5678
(Old PIN → New PIN → Confirm)
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Unregistered phone" | Register user first or run migration |
| "Incorrect PIN" | Use correct 4-digit PIN |
| "Backend unavailable" | Check backend is running on port 8080 |
| "Session expired" | Dial *123# again (5 min timeout) |
| "Invalid input" | Follow prompt format (numbers only for qty/price) |

## 🔍 Verification Commands

```bash
# Check backend
curl http://localhost:8080/

# Check Redis
docker-compose exec redis redis-cli ping

# Check USSD endpoint
curl -X POST http://localhost:8080/api/v1/ussd/session \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","phone_number":"+263771234567","text":"1"}'

# View logs
docker-compose logs -f backend
```

## 📊 Session States

| State | Description |
|-------|-------------|
| ROOT | Initial dial |
| MENU | Main menu |
| AUTH_PIN | PIN authentication |
| SELL_CROP_* | Selling flow |
| BUY_* | Buying flow |
| CHANGE_PIN_* | PIN change flow |
| VIEW_TRANSACTIONS | Transaction history |

## 🎨 Response Prefixes

| Prefix | Meaning |
|--------|---------|
| CON | Continue (more input needed) |
| END | End session (final message) |

## 📈 Performance Targets

| Metric | Target |
|--------|--------|
| Response Time | < 500ms |
| Uptime | > 95% |
| Error Rate | < 1% |
| Session Success | > 95% |

## 🔐 Security Notes

- PIN must be exactly 4 digits
- 5 failed attempts = account lock
- Sessions expire after 5 minutes
- All sensitive operations require PIN
- PINs are bcrypt hashed

## 📞 Support

**Phone**: +263771234567  
**USSD Help**: Dial *123# → 9  
**Docs**: See `USSD_FEATURES_COMPLETE.md`

## 🧪 Test User Creation

```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "phone_number": "+263771234567",
    "password": "1234",
    "role": "FARMER"
  }'
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `USSD_QUICK_START.md` | Getting started guide |
| `USSD_FEATURES_COMPLETE.md` | Complete feature list |
| `USSD_TESTING_GUIDE.md` | 50+ test scenarios |
| `USSD_PIN_SYNC_SUMMARY.md` | PIN synchronization |
| `USSD_BUILD_COMPLETE.md` | Build summary |
| `USSD_INTEGRATION_STATUS.md` | Technical details |

## ⚡ Quick Commands

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# Restart USSD simulator
docker-compose restart ussd-simulator

# View USSD logs
docker-compose logs -f ussd-simulator

# Run migration
cd backend && python scripts/sync_ussd_pins.py

# Run tests
pytest backend/tests/test_ussd.py -v
```

## 🎯 Success Indicators

✅ Simulator loads at http://localhost:5000  
✅ Backend responds to USSD requests  
✅ Sessions persist across requests  
✅ PIN authentication works  
✅ Listings created successfully  
✅ Purchases create offers  
✅ Wallet shows correct balances  
✅ PIN change updates both fields  

---

**Quick Ref Version**: 1.0  
**Last Updated**: 2026-04-23  
**Print this for easy reference!**
