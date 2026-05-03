# WhatsApp Enhanced Features Guide

## Overview

The Enhanced WhatsApp Service extends the base WhatsApp functionality with powerful features for bulk operations, smart notifications, mobile payments, and advanced AI capabilities.

---

## Table of Contents

1. [Bulk Messaging & Broadcasts](#bulk-messaging--broadcasts)
2. [Smart Notifications](#smart-notifications)
3. [Mobile Money Integration](#mobile-money-integration)
4. [Location Services](#location-services)
5. [Interactive Features](#interactive-features)
6. [Analytics & Tracking](#analytics--tracking)
7. [Multi-Language Support](#multi-language-support)
8. [Group Management](#group-management)
9. [Market Intelligence](#market-intelligence)
10. [API Reference](#api-reference)

---

## Bulk Messaging & Broadcasts

### Features

#### 1. General Broadcast
Send messages to multiple users with filters:

```python
# Broadcast to all farmers in Harare
result = await whatsapp_enhanced.broadcast_message(
    db,
    message="Important announcement for all farmers",
    role_filter=UserRole.FARMER,
    province_filter="Harare",
    verified_only=True
)
```

**API Endpoint:**
```http
POST /api/v1/whatsapp-enhanced/broadcast
Authorization: Bearer {admin_token}

{
  "message": "Your message here",
  "role_filter": "FARMER",
  "province_filter": "Harare",
  "verified_only": true
}
```

#### 2. Price Alerts
Automatically notify farmers of price changes:

```python
# Send price alert for Maize
await whatsapp_enhanced.send_price_alert(
    db,
    commodity="Maize",
    old_price=400.0,
    new_price=450.0,
    province="Harare"
)
```

**Message Format:**
```
🚨 PRICE ALERT: Maize

📈 UP 12.5%

Old Price: $400.00/tonne
New Price: $450.00/tonne

🎉 Great time to sell!

Reply 'sell' to list your Maize now!
```

#### 3. Weather Alerts
Send weather warnings to farmers:

```python
await whatsapp_enhanced.send_weather_alert(
    db,
    province="Harare",
    alert_type="rain",
    message_body="Heavy rains expected in the next 24 hours. Protect your crops!"
)
```

**Alert Types:**
- `rain` 🌧️ - Rain warnings
- `drought` ☀️ - Drought alerts
- `storm` ⛈️ - Storm warnings
- `frost` ❄️ - Frost alerts
- `heatwave` 🔥 - Heat warnings

#### 4. Harvest Reminders
Remind farmers about harvest season:

```python
await whatsapp_enhanced.send_harvest_reminder(
    db,
    crop_type="Maize",
    province="Harare"
)
```

---

## Smart Notifications

### Automated Reminders

#### 1. Delivery Reminders
Automatically remind users about pending deliveries:

```python
await whatsapp_enhanced.send_delivery_reminder(
    db,
    order_id="ORD-123",
    recipient_phone="+263771234567",
    days_remaining=2
)
```

**Urgency Levels:**
- 🚨 URGENT (≤1 day remaining)
- ⏰ REMINDER (>1 day remaining)

#### 2. Payment Reminders
Send loan repayment reminders:

```python
await whatsapp_enhanced.send_payment_reminder(
    db,
    user_phone="+263771234567",
    amount=500.0,
    due_date=datetime(2026, 5, 1),
    loan_id="LOAN-123"
)
```

**Status Types:**
- ⚠️ OVERDUE (past due date)
- 🚨 DUE TODAY (due today)
- ⏰ UPCOMING (future due date)

#### 3. Verification Reminders
Encourage users to complete verification:

```python
await whatsapp_enhanced.send_verification_reminder(
    db,
    user_phone="+263771234567",
    user_name="John Doe",
    verification_type="id"
)
```

**Verification Types:**
- `phone` - Phone verification
- `id` - Identity verification
- `location` - Farm/location verification

---

## Mobile Money Integration

### Payment Processing

#### 1. Initiate Payment
Start mobile money payment:

```python
result = await whatsapp_enhanced.initiate_mobile_payment(
    db,
    user=current_user,
    amount=100.0,
    reference="ORDER-123",
    provider="ecocash"
)
```

**Supported Providers:**
- `ecocash` - EcoCash
- `onemoney` - OneMoney
- `telecash` - TeleCash

**API Endpoint:**
```http
POST /api/v1/whatsapp-enhanced/payment/initiate

{
  "amount": 100.0,
  "reference": "ORDER-123",
  "provider": "ecocash"
}
```

#### 2. Send Receipt
Send payment confirmation:

```python
await whatsapp_enhanced.send_payment_receipt(
    db,
    user_phone="+263771234567",
    transaction_id="TXN-123",
    amount=100.0,
    recipient="ZimAgritrust Marketplace",
    timestamp=datetime.utcnow()
)
```

**Receipt Format:**
```
✅ PAYMENT SUCCESSFUL

━━━━━━━━━━━━━━━━━━━━
Transaction ID: TXN-123
Amount: $100.00
To: ZimAgritrust Marketplace
Date: 25 Apr 2026 14:30
━━━━━━━━━━━━━━━━━━━━

Thank you for using ZimAgritrust! 🌾
```

---

## Location Services

### GPS Tracking

#### Share Location
Process shared GPS coordinates:

```python
response = await whatsapp_enhanced.process_location_share(
    db,
    user=current_user,
    latitude=-17.8252,
    longitude=31.0335
)
```

**Benefits:**
- Find nearby listings
- Connect with local agents
- Get regional market data
- Verify farm location

**API Endpoint:**
```http
POST /api/v1/whatsapp-enhanced/location/share

{
  "latitude": -17.8252,
  "longitude": 31.0335
}
```

---

## Interactive Features

### Quick Action Buttons

Send listings with interactive buttons:

```python
await whatsapp_enhanced.send_interactive_listing(
    db,
    user_phone="+263771234567",
    listing=listing_object
)
```

**Message Format:**
```
🌾 Maize

Grade: A
Quantity: 10 tonnes
Price: $450/tonne
Location: Harare
Seller: John Farmer
Trust Score: ⭐ 85/100

━━━━━━━━━━━━━━━━━━━━
Quick Actions:
• Reply 'buy LST-123' to purchase
• Reply 'offer LST-123 400' to negotiate
• Reply 'details LST-123' for more info
• Reply 'chat LST-123' to message seller
```

---

## Analytics & Tracking

### Engagement Metrics

#### Track Engagement
Log user interactions:

```python
await whatsapp_enhanced.track_message_engagement(
    db,
    user_id="user-123",
    message_type="price_check",
    action_taken="viewed"
)
```

#### Get Statistics
Retrieve engagement stats:

```python
stats = await whatsapp_enhanced.get_user_engagement_stats(
    db,
    user_id="user-123"
)
```

**Returns:**
```json
{
  "messages_sent": 150,
  "messages_received": 200,
  "response_rate": 0.85,
  "avg_response_time": 120,
  "most_used_commands": ["prices", "sell", "wallet"]
}
```

---

## Multi-Language Support

### Translation

#### Detect Language
Automatically detect message language:

```python
language = await whatsapp_enhanced.detect_language("Ndiri kuda chibage")
# Returns: "sn" (Shona)
```

**Supported Languages:**
- `en` - English
- `sn` - Shona
- `nd` - Ndebele

#### Translate Message
Translate to local language:

```python
translated = await whatsapp_enhanced.translate_message(
    "Welcome to ZimAgritrust",
    target_language="sn"
)
```

---

## Group Management

### Farmer Groups

#### Create Group
Create WhatsApp group for farmers:

```python
result = await whatsapp_enhanced.create_farmer_group(
    db,
    group_name="Harare Maize Farmers",
    province="Harare",
    crop_type="Maize"
)
```

#### Send Group Message
Broadcast to group:

```python
await whatsapp_enhanced.send_group_message(
    db,
    group_id="GRP-HARARE-MAIZE",
    message="Important update for all members"
)
```

---

## Market Intelligence

### Demand Prediction

Predict market demand for crops:

```python
prediction = await whatsapp_enhanced.predict_market_demand(
    db,
    crop_type="Maize",
    province="Harare",
    days_ahead=7
)
```

**Returns:**
```json
{
  "crop": "Maize",
  "province": "Harare",
  "demand_level": "HIGH",
  "active_listings": 8,
  "recommendation": "Good time to sell!"
}
```

**Demand Levels:**
- `HIGH` - Low supply, high demand (< 10 listings)
- `MEDIUM` - Balanced market (10-20 listings)
- `LOW` - High supply, low demand (> 20 listings)

---

## API Reference

### Base URL
```
https://api.ZimAgritrust.co.zw/api/v1/whatsapp-enhanced
```

### Authentication
All endpoints require Bearer token authentication:
```http
Authorization: Bearer {your_token}
```

### Endpoints Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/broadcast` | POST | Admin | Broadcast message to users |
| `/alerts/price` | POST | Admin | Send price alerts |
| `/alerts/weather` | POST | Admin | Send weather alerts |
| `/alerts/harvest` | POST | Admin | Send harvest reminders |
| `/reminders/delivery` | POST | User | Send delivery reminder |
| `/reminders/payment` | POST | Admin | Send payment reminder |
| `/reminders/verification/{user_id}` | POST | Admin | Send verification reminder |
| `/payment/initiate` | POST | User | Initiate mobile payment |
| `/payment/receipt` | POST | User | Send payment receipt |
| `/location/share` | POST | User | Share GPS location |
| `/interactive/listing/{listing_id}` | POST | User | Send interactive listing |
| `/analytics/engagement/{user_id}` | GET | Admin | Get engagement stats |
| `/analytics/track` | POST | User | Track engagement |
| `/market/demand` | POST | User | Predict market demand |
| `/groups/create` | POST | Admin | Create farmer group |
| `/groups/{group_id}/message` | POST | Admin | Send group message |
| `/translate` | POST | User | Translate message |
| `/detect-language` | POST | User | Detect language |

---

## Best Practices

### 1. Rate Limiting
- Add delays between bulk messages (0.1s minimum)
- Batch large broadcasts into smaller groups
- Monitor WhatsApp API rate limits

### 2. Message Templates
- Use pre-approved templates for business messages
- Keep messages concise and actionable
- Include clear call-to-action

### 3. User Privacy
- Only send relevant messages
- Respect opt-out preferences
- Secure user data

### 4. Error Handling
- Implement retry logic for failed messages
- Log all errors for debugging
- Provide fallback options

### 5. Testing
- Test with small user groups first
- Verify message formatting
- Check all interactive buttons

---

## Future Enhancements

### Planned Features
1. ✅ Voice message transcription
2. ✅ Video support
3. ✅ Advanced chatbot learning
4. ✅ Sentiment analysis
5. ✅ Automated customer support
6. ✅ Rich media carousels
7. ✅ Payment gateway integration
8. ✅ Blockchain receipts

---

## Support

For technical support or feature requests:
- Email: dev@ZimAgritrust.co.zw
- WhatsApp: +263771234567
- Documentation: https://docs.ZimAgritrust.co.zw

---

## License

Copyright © 2026 ZimAgritrust. All rights reserved.
