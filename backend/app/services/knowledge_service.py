from typing import Dict, List
import random

class KnowledgeService:
    """
    AgriTrust Knowledge Authority.
    Provides regional farming advice and pseudo-real-time weather data.
    """
    
    TIPS = [
        "🌽 *Maize Optimisation*: Split your Nitrogen application: 50% at planting and 50% at 6-8 weeks (knee high).",
        "🌱 *Crop Rotation*: Rotating Soybeans after Maize can reduce fertilizer needs by 20% due to nitrogen fixation.",
        "💧 *Water Conservation*: Use mulch in dry provinces like Matabeleland to retain soil moisture.",
        "🐛 *Pest Control*: Scout for Fall Armyworm every 3 days. Early detection is critical for crop survival.",
        "📉 *Market Timing*: Historical data shows prices for Maize peak 4 months after harvest. Store if you have dry facilities.",
        "🚜 *Soil Testing*: Knowing your pH can save you hundreds in lime costs. Test every 2 seasons."
    ]
    
    REGIONAL_WEATHER = {
        "harare": {"temp": "22\u00b0C", "cond": "Partly Cloudy", "advice": "Good for spraying."},
        "bulawayo": {"temp": "26\u00b0C", "cond": "Sunny/Dry", "advice": "Prioritize irrigation."},
        "mutare": {"temp": "19\u00b0C", "cond": "Light Rain", "advice": "High humidity risk for fungi."},
        "mazowe": {"temp": "24\u00b0C", "cond": "Clear Skies", "advice": "Optimal for harvesting."},
        "gweru": {"temp": "21\u00b0C", "cond": "Windy", "advice": "Avoid aerial spraying."}
    }

    def get_random_tip(self) -> str:
        return random.choice(self.TIPS)

    def get_weather(self, region: str) -> Dict[str, str]:
        region_key = region.lower().strip()
        # Fallback to a default if region not in list
        return self.REGIONAL_WEATHER.get(region_key, {
            "temp": "23\u00b0C", 
            "cond": "Seasonal", 
            "advice": "Monitor regional broadcasts."
        })

knowledge_service = KnowledgeService()
