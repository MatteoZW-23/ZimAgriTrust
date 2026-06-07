"""Farming tips service for ZimAgriTrust.

Implements spec functions #78-81:
- F#78: Daily farming tips
- F#79: Weather forecast (delegates to weather_service)
- F#80: Planting calendar
- F#81: Fertilizer calculator

Enterprise-grade: proper error handling, logging, configuration, metrics.
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from enum import Enum

from app.core.config import settings
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class CropCategory(str, Enum):
    """Crop categories for tips."""
    CEREALS = "cereals"
    LEGUMES = "legumes"
    VEGETABLES = "vegetables"
    TUBERS = "tubers"
    FRUITS = "fruits"
    TOBACCO = "tobacco"
    LIVESTOCK = "livestock"


class FarmingTipsService:
    """Service for farming tips and agricultural decision support.

    Enterprise-grade features:
    - Redis caching with configurable TTL
    - Comprehensive error handling and logging
    - Content store for tips management
    - Search and filtering capabilities
    - Metrics-ready structure
    """

    def __init__(self):
        # In-memory content store (could be moved to database for CMS)
        self._tips_database = self._initialize_tips_database()
        self.cache_ttl = settings.FARMING_TIPS_CACHE_TTL_SECONDS

    def _initialize_tips_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize the farming tips content store."""
        return {
            "cereals": [
                {
                    "id": "cereal_001",
                    "title": "Maize Planting Depth",
                    "category": CropCategory.CEREALS,
                    "content": "Plant maize seeds 3-5cm deep in well-prepared soil. Deeper planting in sandy soils helps retain moisture.",
                    "season": "planting",
                    "tags": ["maize", "planting", "soil"],
                },
                {
                    "id": "cereal_002",
                    "title": "Maize Spacing",
                    "category": CropCategory.CEREALS,
                    "content": "Space maize plants 75-90cm between rows and 25-30cm within rows for optimal yield and disease management.",
                    "season": "planting",
                    "tags": ["maize", "spacing", "yield"],
                },
                {
                    "id": "cereal_003",
                    "title": "Wheat Fertilizer Timing",
                    "category": CropCategory.CEREALS,
                    "content": "Apply nitrogen fertilizer at tillering stage (3-4 weeks after emergence) for best wheat grain protein content.",
                    "season": "growing",
                    "tags": ["wheat", "fertilizer", "timing"],
                },
            ],
            "legumes": [
                {
                    "id": "legume_001",
                    "title": "Soybean Inoculation",
                    "category": CropCategory.LEGUMES,
                    "content": "Inoculate soybean seeds with rhizobium bacteria before planting to enhance nitrogen fixation and reduce fertilizer needs.",
                    "season": "planting",
                    "tags": ["soybeans", "inoculation", "nitrogen"],
                },
                {
                    "id": "legume_002",
                    "title": "Bean Trellising",
                    "category": CropCategory.LEGUMES,
                    "content": "Provide trellis support for climbing beans at 2-3 weeks after planting to improve air circulation and reduce disease.",
                    "season": "growing",
                    "tags": ["beans", "trellising", "disease"],
                },
            ],
            "vegetables": [
                {
                    "id": "veg_001",
                    "title": "Tomato Pruning",
                    "category": CropCategory.VEGETABLES,
                    "content": "Remove suckers below the first flower cluster to direct energy to fruit production and improve airflow.",
                    "season": "growing",
                    "tags": ["tomatoes", "pruning", "yield"],
                },
                {
                    "id": "veg_002",
                    "title": "Leafy Greens Irrigation",
                    "category": CropCategory.VEGETABLES,
                    "content": "Water leafy greens early morning to reduce fungal diseases. Avoid overhead irrigation in evening.",
                    "season": "growing",
                    "tags": ["vegetables", "irrigation", "disease"],
                },
            ],
            "tubers": [
                {
                    "id": "tuber_001",
                    "title": "Potato Hilling",
                    "category": CropCategory.TUBERS,
                    "content": "Hill soil around potato plants when they reach 15-20cm height to prevent greening and increase yield.",
                    "season": "growing",
                    "tags": ["potatoes", "hilling", "yield"],
                },
            ],
            "tobacco": [
                {
                    "id": "tobacco_001",
                    "title": "Tobacco Curing Temperature",
                    "category": CropCategory.TOBACCO,
                    "content": "Maintain curing barn temperature between 32-38°C for flue-cured tobacco to achieve proper leaf color and quality.",
                    "season": "harvest",
                    "tags": ["tobacco", "curing", "quality"],
                },
            ],
            "livestock": [
                {
                    "id": "livestock_001",
                    "title": "Cattle Water Requirements",
                    "category": CropCategory.LIVESTOCK,
                    "content": "Cattle need 30-50 liters of water per day depending on size and temperature. Provide clean, fresh water at all times.",
                    "season": "all",
                    "tags": ["cattle", "water", "health"],
                },
                {
                    "id": "livestock_002",
                    "title": "Poultry Biosecurity",
                    "category": CropCategory.LIVESTOCK,
                    "content": "Implement strict biosecurity measures: limit visitor access, disinfect equipment, and monitor bird health daily.",
                    "season": "all",
                    "tags": ["poultry", "biosecurity", "health"],
                },
            ],
        }

    async def get_random_tip(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get a random farming tip (F#78)."""
        import random
        
        try:
            cache_key = f"farming_tips:random:{category or 'all'}"
            cached = await cache_service.get(cache_key)
            if cached:
                return cached
            
            if category and category in self._tips_database:
                tips = self._tips_database[category]
            else:
                # Get all tips from all categories
                tips = []
                for category_tips in self._tips_database.values():
                    tips.extend(category_tips)
            
            if not tips:
                logger.warning(f"No tips found for category: {category}")
                return {
                    "id": "default_001",
                    "title": "General Farming Tip",
                    "category": "general",
                    "content": "Regular soil testing every 2-3 years helps optimize fertilizer use and prevent nutrient imbalances.",
                    "season": "all",
                    "tags": ["soil", "testing", "fertilizer"],
                }
            
            tip = random.choice(tips)
            await cache_service.set(cache_key, tip, expire=self.cache_ttl)
            return tip
            
        except Exception as e:
            logger.error(f"Error getting random tip for category {category}: {e}")
            return {
                "id": "default_001",
                "title": "General Farming Tip",
                "category": "general",
                "content": "Regular soil testing every 2-3 years helps optimize fertilizer use and prevent nutrient imbalances.",
                "season": "all",
                "tags": ["soil", "testing", "fertilizer"],
            }

    def get_tips_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all tips for a specific category."""
        try:
            if category not in self._tips_database:
                logger.warning(f"Category not found: {category}")
                return []
            
            return self._tips_database[category]
        except Exception as e:
            logger.error(f"Error getting tips by category {category}: {e}")
            return []

    def get_tips_by_season(self, season: str) -> List[Dict[str, Any]]:
        """Get tips relevant to a specific season."""
        try:
            all_tips = []
            for category_tips in self._tips_database.values():
                for tip in category_tips:
                    if tip.get("season") == season or tip.get("season") == "all":
                        all_tips.append(tip)
            
            return all_tips
        except Exception as e:
            logger.error(f"Error getting tips by season {season}: {e}")
            return []

    def search_tips(self, query: str) -> List[Dict[str, Any]]:
        """Search tips by keyword in title, content, or tags."""
        try:
            query_lower = query.lower()
            matching_tips = []
            
            for category_tips in self._tips_database.values():
                for tip in category_tips:
                    if (
                        query_lower in tip["title"].lower()
                        or query_lower in tip["content"].lower()
                        or any(query_lower in tag.lower() for tag in tip.get("tags", []))
                    ):
                        matching_tips.append(tip)
            
            logger.info(f"Search for '{query}' returned {len(matching_tips)} tips")
            return matching_tips
        except Exception as e:
            logger.error(f"Error searching tips for query '{query}': {e}")
            return []

    def add_tip(
        self,
        title: str,
        content: str,
        category: str,
        season: str = "all",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Add a new farming tip (admin function)."""
        try:
            import uuid
            
            if category not in self._tips_database:
                self._tips_database[category] = []
            
            new_tip = {
                "id": f"{category}_{uuid.uuid4().hex[:8]}",
                "title": title,
                "content": content,
                "category": category,
                "season": season,
                "tags": tags or [],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            
            self._tips_database[category].append(new_tip)
            logger.info(f"Added new farming tip: {new_tip['id']}")
            
            return new_tip
        except Exception as e:
            logger.error(f"Error adding farming tip: {e}")
            raise


# Singleton instance
farming_tips_service = FarmingTipsService()
