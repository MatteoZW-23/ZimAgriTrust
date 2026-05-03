from typing import Dict, List
import random

class KnowledgeService:
    """
    ZimAgritrust Knowledge Authority.
    Provides regional farming advice. Tips are informational only — no fake market data.
    """
    
    TIPS = [
        "🌽 *Maize Optimisation*: Split your Nitrogen application: 50% at planting and 50% at 6-8 weeks (knee high).",
        "🌱 *Crop Rotation*: Rotating Soybeans after Maize can reduce fertilizer needs by 20% due to nitrogen fixation.",
        "💧 *Water Conservation*: Use mulch in dry provinces like Matabeleland to retain soil moisture.",
        "🐛 *Pest Control*: Scout for Fall Armyworm every 3 days. Early detection is critical for crop survival.",
        "📉 *Market Timing*: Historical data shows prices for Maize peak 4 months after harvest. Store if you have dry facilities.",
        "🚜 *Soil Testing*: Knowing your pH can save you hundreds in lime costs. Test every 2 seasons."
    ]

    def get_random_tip(self) -> str:
        return random.choice(self.TIPS)

    def get_weather(self, region: str) -> dict:
        return {
            "temp": "--",
            "cond": "Unavailable",
            "advice": "Check local weather services."
        }

knowledge_service = KnowledgeService()
