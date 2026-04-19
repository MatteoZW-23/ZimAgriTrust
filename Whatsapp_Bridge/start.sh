#!/bin/sh

echo "Cleaning up stale session locks..."
find /app/.wwebjs_auth -name "SingletonLock" -delete 2>/dev/null
find /app/.wwebjs_auth -name "SingletonCookie" -delete 2>/dev/null
find /app/.wwebjs_auth -name "SingletonSocket" -delete 2>/dev/null

echo "Starting WhatsApp Bridge Node process..."
npm start
