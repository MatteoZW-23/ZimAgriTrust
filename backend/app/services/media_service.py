"""
Media Service - Download and process WhatsApp media files
"""

import logging
import aiohttp
import os
import uuid
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class MediaService:
    """
    Handles downloading and processing of media from WhatsApp
    """
    
    def __init__(self):
        # Use system temp directory to avoid permission issues in Docker containers
        self.temp_dir = Path(tempfile.gettempdir()) / "agritelecom_media"
        self.temp_dir.mkdir(exist_ok=True, parents=True)
    
    async def download_whatsapp_media(self, media_id: str, media_url: str, auth_token: str) -> Optional[bytes]:
        """
        Download media from WhatsApp servers
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {auth_token}"
                }
                async with session.get(media_url, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Failed to download media: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Media download error: {e}")
            return None
    
    async def save_temp_file(self, image_data: bytes) -> str:
        """
        Save image to temporary file and return path
        """
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = self.temp_dir / filename
        filepath.write_bytes(image_data)
        return str(filepath)
    
    def cleanup_temp_file(self, filepath: str):
        """
        Remove temporary file after processing
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file: {e}")
    
    async def process_uploaded_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Basic image validation before AI processing
        """
        # Check image size (max 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            return {
                "valid": False,
                "error": "Image too large. Maximum size is 10MB."
            }
        
        # Check if it looks like an image
        if not image_data.startswith(b'\xff\xd8') and not image_data.startswith(b'\x89PNG'):
            return {
                "valid": False,
                "error": "File does not appear to be a valid image. Please send a JPG or PNG photo."
            }
        
        return {
            "valid": True,
            "size_bytes": len(image_data),
            "size_mb": len(image_data) / (1024 * 1024)
        }


# Singleton
media_service = MediaService()
