# WhatsApp Service Redis Streams Architecture

## Overview
Decompose the monolithic `whatsapp_service.py` (2398 lines) into a separate microservice that communicates via Redis Streams for ZimAgriTrust.

## Redis Streams Design

### Stream: `whatsapp:outbound`
**Direction**: Main Backend → WhatsApp Service
**Purpose**: Send messages to users via WhatsApp
**Message Schema**:
```json
{
  "message_id": "uuid",
  "phone": "263777123456@c.us",
  "message": "Hello from AgriTrust",
  "timestamp": "2026-05-04T12:00:00Z",
  "priority": "normal",
  "retry_count": 0
}
```

### Stream: `whatsapp:inbound`
**Direction**: WhatsApp Service → Main Backend
**Purpose**: Process incoming WhatsApp messages
**Message Schema**:
```json
{
  "message_id": "uuid",
  "phone": "263777123456@c.us",
  "body": "menu",
  "has_media": false,
  "media": null,
  "timestamp": "2026-05-04T12:00:00Z"
}
```

### Stream: `whatsapp:notifications`
**Direction**: WhatsApp Service → Main Backend (async)
**Purpose**: Send bulk notifications (price alerts, weather alerts, etc.)
**Message Schema**:
```json
{
  "notification_id": "uuid",
  "type": "price_alert|weather_alert|harvest_reminder|delivery_reminder",
  "target_role": "farmer|agent|buyer|admin",
  "province_filter": "Mashonaland East",
  "data": {
    "commodity": "maize",
    "old_price": 450.0,
    "new_price": 500.0
  },
  "timestamp": "2026-05-04T12:00:00Z"
}
```

### Stream: `whatsapp:responses`
**Direction**: WhatsApp Service → Main Backend
**Purpose**: Return processed message responses
**Message Schema**:
```json
{
  "message_id": "uuid",
  "phone": "263777123456@c.us",
  "response": "Here is your menu...",
  "timestamp": "2026-05-04T12:00:00Z"
}
```

## Service Components

### Main Backend (Producer)
- `RedisProducer`: Publishes messages to `whatsapp:outbound`
- `RedisConsumer`: Consumes from `whatsapp:inbound` and `whatsapp:responses`
- Endpoints updated to use Redis Producer instead of direct WhatsApp Service calls

### WhatsApp Service (Consumer/Producer)
- `RedisConsumer`: Consumes from `whatsapp:outbound`
- `WhatsAppBridgeClient`: Communicates with Node.js WhatsApp Bridge
- `MessageProcessor`: Processes inbound messages (conversational flows)
- `NotificationProcessor`: Handles bulk notifications
- `StateManager`: Manages conversational state (migrated from cache_service)
- `RedisProducer`: Publishes to `whatsapp:inbound`, `whatsapp:responses`, `whatsapp:notifications`

## Migration Strategy

### Phase 1: Infrastructure Setup
1. Create Redis Streams client library
2. Set up WhatsApp service microservice structure
3. Implement producer/consumer patterns

### Phase 2: Core Message Processing
1. Migrate `send_whatsapp_message` to WhatsApp Service
2. Migrate `process_message` to WhatsApp Service
3. Update webhook endpoint to use Redis Streams

### Phase 3: State Management
1. Migrate state management from cache_service to WhatsApp Service
2. Implement Redis-based state storage

### Phase 4: Notifications
1. Migrate notification functions (price alerts, weather alerts, etc.)
2. Implement bulk processing with Redis Streams

### Phase 5: Advanced Features
1. Migrate flow handlers (listing, dispute, search, etc.)
2. Migrate admin commands
3. Migrate vision verification

### Phase 6: Feature Flag
1. Add `WHATSAPP_USE_REDIS` feature flag
2. Toggle between direct calls and Redis Streams
3. Gradual rollout

## Benefits
- **Decoupling**: Main backend no longer depends on WhatsApp bridge availability
- **Scalability**: WhatsApp service can scale independently
- **Resilience**: Redis provides message persistence and retry logic
- **Observability**: Redis Streams provide message tracking and monitoring
- **Flexibility**: Easy to add new WhatsApp features without touching main backend
