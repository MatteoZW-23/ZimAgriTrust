"""Fertilizer calculator service for ZimAgriTrust.

Implements spec function F#81: Fertilizer calculator.
Provides fertilizer recommendations based on crop, area, and soil type.

Enterprise-grade: proper error handling, logging, configuration, metrics.
"""
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class CropType(str, Enum):
    """Crop types for fertilizer calculations."""
    MAIZE = "maize"
    SOYBEANS = "soybeans"
    WHEAT = "wheat"
    TOBACCO = "tobacco"
    VEGETABLES = "vegetables"
    POTATOES = "potatoes"
    GROUNDNUTS = "groundnuts"


class SoilType(str, Enum):
    """Soil types affecting fertilizer requirements."""
    SANDY = "sandy"
    LOAMY = "loamy"
    CLAY = "clay"
    RED_SOIL = "red_soil"


class FertilizerCalculatorService:
    """Service for fertilizer calculations and recommendations.

    Enterprise-grade features:
    - Comprehensive error handling and logging
    - Crop-specific NPK requirements
    - Soil type adjustments
    - Fertilizer blend recommendations
    - Metrics-ready structure
    """

    def __init__(self):
        # Fertilizer requirements per hectare (kg/ha) for different crops
        self._crop_requirements = {
            CropType.MAIZE: {
                "basal": {"n": 30, "p": 30, "k": 30},  # NPK at planting
                "top_dressing": {"n": 70, "p": 0, "k": 0},  # Nitrogen at 4-6 weeks
                "total": {"n": 100, "p": 30, "k": 30},
            },
            CropType.SOYBEANS: {
                "basal": {"n": 10, "p": 40, "k": 20},
                "top_dressing": {"n": 0, "p": 0, "k": 0},  # Soybeans fix nitrogen
                "total": {"n": 10, "p": 40, "k": 20},
            },
            CropType.WHEAT: {
                "basal": {"n": 40, "p": 30, "k": 30},
                "top_dressing": {"n": 60, "p": 0, "k": 0},
                "total": {"n": 100, "p": 30, "k": 30},
            },
            CropType.TOBACCO: {
                "basal": {"n": 40, "p": 60, "k": 80},
                "top_dressing": {"n": 80, "p": 0, "k": 40},
                "total": {"n": 120, "p": 60, "k": 120},
            },
            CropType.VEGETABLES: {
                "basal": {"n": 50, "p": 50, "k": 50},
                "top_dressing": {"n": 50, "p": 0, "k": 30},
                "total": {"n": 100, "p": 50, "k": 80},
            },
            CropType.POTATOES: {
                "basal": {"n": 60, "p": 80, "k": 100},
                "top_dressing": {"n": 60, "p": 0, "k": 60},
                "total": {"n": 120, "p": 80, "k": 160},
            },
            CropType.GROUNDNUTS: {
                "basal": {"n": 10, "p": 30, "k": 30},
                "top_dressing": {"n": 0, "p": 0, "k": 0},
                "total": {"n": 10, "p": 30, "k": 30},
            },
        }

        # Soil type adjustment factors
        self._soil_adjustments = {
            SoilType.SANDY: {"n": 1.3, "p": 1.2, "k": 1.4},  # Sandy soils leach more
            SoilType.LOAMY: {"n": 1.0, "p": 1.0, "k": 1.0},  # Baseline
            SoilType.CLAY: {"n": 0.9, "p": 1.1, "k": 0.9},  # Clay holds nutrients better
            SoilType.RED_SOIL: {"n": 1.2, "p": 1.3, "k": 1.2},  # Red soils often acidic
        }

        # Common fertilizer blends and their NPK content
        self._fertilizer_blends = {
            "compound_d": {"n": 7, "p": 14, "k": 7},  # 7-14-7
            "compound_c": {"n": 14, "p": 23, "k": 14},  # 14-23-14
            "urea": {"n": 46, "p": 0, "k": 0},  # 46-0-0
            "dap": {"n": 18, "p": 46, "k": 0},  # 18-46-0
            "mop": {"n": 0, "p": 0, "k": 60},  # 0-0-60 (Muriate of Potash)
            "ammonium_sulphate": {"n": 21, "p": 0, "k": 0},  # 21-0-0
            "can": {"n": 27, "p": 0, "k": 0},  # 27-0-0
        }

    def calculate_fertilizer(
        self,
        crop: str,
        area_hectares: float,
        soil_type: str = "loamy",
    ) -> Dict[str, Any]:
        """Calculate fertilizer requirements (F#81)."""
        try:
            crop_enum = CropType(crop.lower())
        except ValueError:
            logger.error(f"Invalid crop type: {crop}")
            raise ValueError(f"Invalid crop type: {crop}. Valid options: {[c.value for c in CropType]}")

        try:
            soil_enum = SoilType(soil_type.lower())
        except ValueError:
            logger.error(f"Invalid soil type: {soil_type}")
            raise ValueError(f"Invalid soil type: {soil_type}. Valid options: {[s.value for s in SoilType]}")

        try:
            # Get base requirements
            requirements = self._crop_requirements[crop_enum]
            soil_factor = self._soil_adjustments[soil_enum]

            # Calculate adjusted requirements
            basal_adjusted = {
                "n": round(requirements["basal"]["n"] * soil_factor["n"] * area_hectares, 2),
                "p": round(requirements["basal"]["p"] * soil_factor["p"] * area_hectares, 2),
                "k": round(requirements["basal"]["k"] * soil_factor["k"] * area_hectares, 2),
            }

            top_dressing_adjusted = {
                "n": round(requirements["top_dressing"]["n"] * soil_factor["n"] * area_hectares, 2),
                "p": round(requirements["top_dressing"]["p"] * soil_factor["p"] * area_hectares, 2),
                "k": round(requirements["top_dressing"]["k"] * soil_factor["k"] * area_hectares, 2),
            }

            total_adjusted = {
                "n": round(requirements["total"]["n"] * soil_factor["n"] * area_hectares, 2),
                "p": round(requirements["total"]["p"] * soil_factor["p"] * area_hectares, 2),
                "k": round(requirements["total"]["k"] * soil_factor["k"] * area_hectares, 2),
            }

            # Recommend fertilizer blends
            basal_recommendations = self._recommend_blends(basal_adjusted)
            top_dressing_recommendations = self._recommend_blends(top_dressing_adjusted)

            logger.info(f"Calculated fertilizer for {crop} ({area_hectares} ha, {soil_type} soil)")

            return {
                "crop": crop,
                "area_hectares": area_hectares,
                "soil_type": soil_type,
                "basal_fertilizer": {
                    "npk_kg": basal_adjusted,
                    "recommendations": basal_recommendations,
                },
                "top_dressing_fertilizer": {
                    "npk_kg": top_dressing_adjusted,
                    "recommendations": top_dressing_recommendations,
                },
                "total_requirements": {
                    "npk_kg": total_adjusted,
                },
                "tips": self._get_fertilizer_tips(crop_enum),
            }
        except Exception as e:
            logger.error(f"Error calculating fertilizer for {crop}: {e}")
            raise

    def _recommend_blends(self, npk_requirements: Dict[str, float]) -> List[Dict[str, Any]]:
        """Recommend specific fertilizer blends to meet NPK requirements."""
        recommendations = []

        # Simple recommendation logic - suggest common blends
        if npk_requirements["p"] > 0 and npk_requirements["k"] > 0:
            # Need compound fertilizer
            if npk_requirements["n"] > npk_requirements["p"]:
                recommendations.append({
                    "blend": "compound_c",
                    "amount_kg": round(npk_requirements["p"] / 0.23, 2),
                    "npk": self._fertilizer_blends["compound_c"],
                })
            else:
                recommendations.append({
                    "blend": "compound_d",
                    "amount_kg": round(npk_requirements["p"] / 0.14, 2),
                    "npk": self._fertilizer_blends["compound_d"],
                })

        # Additional nitrogen if needed
        remaining_n = npk_requirements["n"]
        for rec in recommendations:
            remaining_n -= (rec["amount_kg"] * rec["npk"]["n"] / 100)

        if remaining_n > 5:
            recommendations.append({
                "blend": "urea",
                "amount_kg": round(remaining_n / 0.46, 2),
                "npk": self._fertilizer_blends["urea"],
            })

        # Additional potassium if needed
        remaining_k = npk_requirements["k"]
        for rec in recommendations:
            remaining_k -= (rec["amount_kg"] * rec["npk"]["k"] / 100)

        if remaining_k > 5:
            recommendations.append({
                "blend": "mop",
                "amount_kg": round(remaining_k / 0.60, 2),
                "npk": self._fertilizer_blends["mop"],
            })

        return recommendations

    def _get_fertilizer_tips(self, crop: CropType) -> List[str]:
        """Get crop-specific fertilizer application tips."""
        tips = {
            CropType.MAIZE: [
                "Apply basal fertilizer at planting in planting furrow",
                "Apply top dressing 4-6 weeks after emergence when maize is knee-high",
                "Avoid fertilizer contact with seeds to prevent burning",
            ],
            CropType.SOYBEANS: [
                "Inoculate seeds with rhizobium bacteria to reduce nitrogen needs",
                "Apply phosphorus and potassium at planting",
                "Avoid excessive nitrogen as it reduces nodulation",
            ],
            CropType.WHEAT: [
                "Apply basal fertilizer at planting",
                "Apply nitrogen at tillering stage (3-4 weeks after emergence)",
                "Split nitrogen application for better efficiency",
            ],
            CropType.TOBACCO: [
                "Apply high potassium fertilizer for leaf quality",
                "Apply fertilizer in split doses throughout the season",
                "Avoid late nitrogen applications to reduce nicotine content",
            ],
            CropType.VEGETABLES: [
                "Apply fertilizer based on soil test results",
                "Use drip irrigation with fertigation for efficiency",
                "Avoid over-fertilization to prevent nutrient burn",
            ],
            CropType.POTATOES: [
                "High potassium requirement for tuber development",
                "Apply fertilizer in bands at planting",
                "Avoid chloride-containing fertilizers for some varieties",
            ],
            CropType.GROUNDNUTS: [
                "Low nitrogen requirement due to nitrogen fixation",
                "Ensure adequate calcium for pod development",
                "Apply gypsum if soil calcium is low",
            ],
        }
        return tips.get(crop, [])


# Singleton instance
fertilizer_calculator_service = FertilizerCalculatorService()
