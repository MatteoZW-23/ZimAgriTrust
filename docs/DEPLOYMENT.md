# Deployment Guide

## Prerequisites
* Docker and Docker Compose
* PostgreSQL 16
* Python 3.11+
* Node.js 18+

## Production Deployment
We use a hardened Docker Compose configuration for orchestrated launches.

```bash
docker-compose -f docker-compose.yml up -d --build
```

### Environment Variables
Ensure `.env` matches `.env.example` but using strong passwords and securely rotated `SECRET_KEY` variables. 
Set `MASTER_TEST_LOGIN_ENABLED="false"`.

## High Availability Setup
* Use a managed PostgreSQL instance instead of Docker volumes in production. 
* Put the API and Node Gateway behind an Nginx reverse proxy with SSL termination.
