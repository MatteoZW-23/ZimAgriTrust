"""WhatsApp Bridge client for communicating with Node.js service and main backend."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppBridgeClient:
    """Client for communicating with the Node.js WhatsApp Bridge."""

    def __init__(self):
        self._base_url = settings.whatsapp_bridge_url
        self._backend_url = settings.main_backend_url.rstrip("/")
        self._timeout = settings.whatsapp_bridge_timeout

    async def send_message(self, phone: str, message: str) -> bool:
        """Send message via WhatsApp Bridge."""
        # Sanitize phone number
        if not phone.endswith("@c.us"):
            clean_phone = phone.replace("+", "")
            if not clean_phone.endswith("@c.us"):
                clean_phone += "@c.us"
        else:
            clean_phone = phone

        url = f"{self._base_url}/send"
        payload = {"to": clean_phone, "message": message}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=self._timeout)
                if response.status_code == 200:
                    logger.info(f"Message sent to {clean_phone}")
                    return True
                else:
                    logger.error(f"WhatsApp bridge returned {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"WhatsApp bridge unreachable: {e}")
            return False

    async def get_status(self) -> dict:
        """Check WhatsApp Bridge status."""
        url = f"{self._base_url}/status"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=self._timeout)
                if response.status_code == 200:
                    return response.json()
                return {"status": "DISCONNECTED", "reason": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "OFFLINE", "reason": str(e)}

    async def get(self, path: str, token: Optional[str] = None) -> Dict[str, Any]:
        """GET request to the main backend API."""
        url = f"{self._backend_url}/api/v1{path}"
        headers: Dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=self._timeout)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning("Backend GET %s returned %s", path, e.response.status_code)
            raise Exception(f"Backend error {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            logger.error("Backend GET %s failed: %s", path, e)
            raise

    async def post(self, path: str, data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """POST request to the main backend API."""
        url = f"{self._backend_url}/api/v1{path}"
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers, timeout=self._timeout)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning("Backend POST %s returned %s", path, e.response.status_code)
            raise Exception(f"Backend error {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            logger.error("Backend POST %s failed: %s", path, e)
            raise
