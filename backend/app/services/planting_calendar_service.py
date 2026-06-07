"""Planting calendar service for ZimAgriTrust.

Implements spec function F#80: Planting calendar.
Provides seasonal planting/harvest information for Zimbabwe crops.

Enterprise-grade: proper error handling, logging, configuration, metrics.
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from enum import Enum

from app.core.config import settings
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class Season(str, Enum):
    """Zimbabwe agricultural seasons."""
    SUMMER = "summer"  # November - March (main rainy season)
    WINTER = "winter"  # April - August (dry season)
    SPRING = "spring"  # September - October (early rains)


class CropActivity(str, Enum):
    """Crop activity types."""
    PLANTING = "planting"
    GROWING = "growing"
    HARVESTING = "harvesting"
    PREPARATION = "preparation"


class PlantingCalendarService:
    """Service for planting calendar and seasonal crop information.

    Enterprise-grade features:
    - Redis caching with configurable TTL
    - Comprehensive error handling and logging
    - Zimbabwe-specific crop calendar dataset
    - Seasonal activity tracking
    - Metrics-ready structure
    """

    def __init__(self):
        # Zimbabwe planting calendar dataset
        self._calendar_data = self._initialize_calendar()
        self.cache_ttl = settings.PLANTING_CALENDAR_CACHE_TTL_SECONDS

    def _initialize_calendar(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize the planting calendar dataset for Zimbabwe."""
        return {
            "summer": [
                {
                    "crop": "Maize",
                    "activity": CropActivity.PLANTING,
                    "start_month": 11,
                    "end_month": 12,
                    "description": "Plant early-season maize varieties with the first rains.",
                    "variety": "Early-maturing",
                    "days_to_harvest": 90,
                    "tips": "Use certified seed, apply basal fertilizer at planting.",
                },
                {
                    "crop": "Maize",
                    "activity": CropActivity.GROWING,
                    "start_month": 12,
                    "end_month": 2,
                    "description": "Critical growth period - monitor for pests and diseases.",
                    "variety": "All varieties",
                    "days_to_harvest": 60,
                    "tips": "Apply top dressing fertilizer at 4-6 weeks after emergence.",
                },
                {
                    "crop": "Maize",
                    "activity": CropActivity.HARVESTING,
                    "start_month": 3,
                    "end_month": 4,
                    "description": "Harvest maize when husks dry and kernels are hard.",
                    "variety": "All varieties",
                    "days_to_harvest": 0,
                    "tips": "Dry properly to prevent mold, store in cool dry place.",
                },
                {
                    "crop": "Soybeans",
                    "activity": CropActivity.PLANTING,
                    "start_month": 11,
                    "end_month": 12,
                    "description": "Plant soybeans with first rains, inoculate seeds.",
                    "variety": "All varieties",
                    "days_to_harvest": 120,
                    "tips": "Inoculate with rhizobium bacteria, space 50cm between rows.",
                },
                {
                    "crop": "Soybeans",
                    "activity": CropActivity.HARVESTING,
                    "start_month": 4,
                    "end_month": 5,
                    "description": "Harvest when pods turn brown and rattle.",
                    "variety": "All varieties",
                    "days_to_harvest": 0,
                    "tips": "Harvest before shattering, dry to 13% moisture.",
                },
                {
                    "crop": "Tobacco",
                    "activity": CropActivity.PLANTING,
                    "start_month": 10,
                    "end_month": 11,
                    "description": "Transplant tobacco seedlings after land preparation.",
                    "variety": "All varieties",
                    "days_to_harvest": 150,
                    "tips": "Use healthy seedlings, apply basal fertilizer at transplanting.",
                },
                {
                    "crop": "Tobacco",
                    "activity": CropActivity.HARVESTING,
                    "start_month": 2,
                    "end_month": 4,
                    "description": "Harvest leaves as they mature from bottom up.",
                    "variety": "All varieties",
                    "days_to_harvest": 0,
                    "tips": "Cure immediately after harvest for best quality.",
                },
                {
                    "crop": "Groundnuts",
                    "activity": CropActivity.PLANTING,
                    "start_month": 11,
                    "end_month": 12,
                    "description": "Plant groundnuts with first rains.",
                    "variety": "All varieties",
                    "days_to_harvest": 120,
                    "tips": "Plant 5-7cm deep, avoid waterlogged soils.",
                },
                {
                    "crop": "Groundnuts",
                    "activity": CropActivity.HARVESTING,
                    "start_month": 4,
                    "end_month": 5,
                    "description": "Harvest when leaves yellow and pods mature.",
                    "variety": "All varieties",
                    "days_to_harvest": 0,
                    "tips": "Cure properly to prevent aflatoxin contamination.",
                },
            ],
            "winter": [
                {
                    "crop": "Wheat",
                    "activity": CropActivity.PLANTING,
                    "start_month": 5,
                    "end_month": 6,
                    "description": "Plant wheat under irrigation in winter.",
                    "variety": "Winter varieties",
                    "days_to_harvest": 120,
                    "tips": "Ensure adequate irrigation, apply nitrogen at tillering.",
                },
                {
                    "crop": "Wheat",
                    "activity": CropActivity.HARVESTING,
                    "start_month": 9,
                    "end_month": 10,
                    "description": "Harvest wheat when grain is hard and dry.",
                    "variety": "Winter varieties",
                    "days_to_harvest": 0,
                    "tips": "Harvest at 12-13% moisture, store in dry conditions.",
                },
                {
                    "crop": "Vegetables",
                    "activity": CropActivity.PLANTING,
                    "start_month": 4,
                    "end_month": 8,
                    "description": "Plant various vegetables under irrigation.",
                    "variety": "Tomatoes, Cabbage, Onions",
                    "days_to_harvest": 60,
                    "tips": "Use drip irrigation for water efficiency.",
                },
            ],
            "spring": [
                {
                    "crop": "Sorghum",
                    "activity": CropActivity.PLANTING,
                    "start_month": 10,
                    "end_month": 11,
                    "description": "Plant sorghum as early rains begin.",
                    "variety": "Drought-tolerant varieties",
                    "days_to_harvest": 120,
                    "tips": "Sorghum is drought-tolerant, suitable for marginal areas.",
                },
                {
                    "crop": "Sorghum",
                    "activity": CropActivity.HARVESTING,
                    "start_month": 3,
                    "end_month": 4,
                    "description": "Harvest when grains are hard and dry.",
                    "variety": "All varieties",
                    "days_to_harvest": 0,
                    "tips": "Bird control important during ripening.",
                },
                {
                    "crop": "Cotton",
                    "activity": CropActivity.PLANTING,
                    "start_month": 11,
                    "end_month": 12,
                    "description": "Plant cotton with first rains.",
                    "variety": "All varieties",
                    "days_to_harvest": 180,
                    "tips": "Use certified seed, space appropriately.",
                },
                {
                    "crop": "Cotton",
                    "activity": CropActivity.HARVESTING,
                    "start_month": 5,
                    "end_month": 7,
                    "description": "Pick cotton as bolls open.",
                    "variety": "All varieties",
                    "days_to_harvest": 0,
                    "tips": "Multiple harvests required, pick clean to avoid contamination.",
                },
            ],
        }

    async def get_current_month_calendar(self) -> List[Dict[str, Any]]:
        """Get planting calendar for current month (F#80)."""
        try:
            current_month = datetime.now(timezone.utc).month
            current_year = datetime.now(timezone.utc).year
            
            cache_key = f"planting_calendar:current_month"
            cached = await cache_service.get(cache_key)
            if cached:
                return cached
            
            # Determine current season
            if current_month in [11, 12, 1, 2, 3]:
                season = "summer"
            elif current_month in [4, 5, 6, 7, 8]:
                season = "winter"
            else:
                season = "spring"
            
            # Get activities for current month
            activities = []
            for activity in self._calendar_data.get(season, []):
                if activity["start_month"] <= current_month <= activity["end_month"]:
                    activities.append(activity)
            
            result = {
                "month": current_month,
                "month_name": datetime(current_year, current_month, 1).strftime("%B"),
                "season": season,
                "activities": activities,
            }
            
            await cache_service.set(cache_key, result, expire=self.cache_ttl)
            return result
        except Exception as e:
            logger.error(f"Error getting current month calendar: {e}")
            return {
                "month": datetime.now(timezone.utc).month,
                "month_name": datetime.now(timezone.utc).strftime("%B"),
                "season": "unknown",
                "activities": [],
            }

    def get_season_calendar(self, season: str) -> List[Dict[str, Any]]:
        """Get all activities for a specific season."""
        try:
            if season not in self._calendar_data:
                logger.warning(f"Season not found: {season}")
                return []
            
            return self._calendar_data[season]
        except Exception as e:
            logger.error(f"Error getting season calendar for {season}: {e}")
            return []

    def get_crop_calendar(self, crop: str) -> List[Dict[str, Any]]:
        """Get all activities for a specific crop across all seasons."""
        try:
            crop_activities = []
            
            for season_activities in self._calendar_data.values():
                for activity in season_activities:
                    if activity["crop"].lower() == crop.lower():
                        crop_activities.append(activity)
            
            logger.info(f"Found {len(crop_activities)} activities for crop: {crop}")
            return crop_activities
        except Exception as e:
            logger.error(f"Error getting crop calendar for {crop}: {e}")
            return []

    def get_all_calendar(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get complete planting calendar for all seasons."""
        try:
            return self._calendar_data
        except Exception as e:
            logger.error(f"Error getting all calendar data: {e}")
            return {}


# Singleton instance
planting_calendar_service = PlantingCalendarService()
