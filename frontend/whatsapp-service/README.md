# WhatsApp Service Microservice

## Overview
This microservice handles all WhatsApp-related functionality, decoupled from the main backend via Redis Streams.

## Architecture
- **Redis Streams**: Communication with main backend
- **WhatsApp Bridge**: Node.js service for actual WhatsApp communication
- **State Management**: Redis-based conversational state
- **Message Processing**: All conversational flows (listing, dispute, search, etc.)

## Directory Structure
```
whatsapp-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── redis_client.py         # Redis Streams producer/consumer
│   ├── whatsapp_bridge.py      # WhatsApp bridge client
│   ├── message_processor.py    # Message processing logic
│   ├── state_manager.py        # Conversational state management
│   ├── notification_processor.py # Bulk notification processing
│   └── flows/                  # Conversational flow handlers
│       ├── __init__.py
│       ├── listing.py
│       ├── dispute.py
│       ├── search.py
│       └── ...
├── tests/
├── Dockerfile
├── requirements.txt
└── docker-compose.yml
```

## Environment Variables
- `REDIS_URL`: Redis connection string
- `WHATSAPP_BRIDGE_URL`: Node.js WhatsApp bridge URL
- `MAIN_BACKEND_URL`: Main backend URL for API calls
- `LOG_LEVEL`: Logging level

## Redis Streams
- `whatsapp:outbound`: Main backend → WhatsApp Service (send messages)
- `whatsapp:inbound`: WhatsApp Service → Main Backend (incoming messages)
- `whatsapp:responses`: WhatsApp Service → Main Backend (processed responses)
- `whatsapp:notifications`: WhatsApp Service → Main Backend (bulk notifications)
