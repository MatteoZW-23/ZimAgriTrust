"""Farming tools schemas for request/response validation.

Implements spec functions F#78-81:
- F#78: Daily farming tips
- F#79: Weather forecast
- F#80: Planting calendar
- F#81: Fertilizer calculator
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


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


class Season(str, Enum):
    """Zimbabwe agricultural seasons."""
    SUMMER = "summer"
    WINTER = "winter"
    SPRING = "spring"


class CropActivity(str, Enum):
    """Crop activity types."""
    PLANTING = "planting"
    GROWING = "growing"
    HARVESTING = "harvesting"
    PREPARATION = "preparation"


# ============================================================================
# Weather Schemas (F#79)
# ============================================================================

class WeatherResponse(BaseModel):
    """Weather data response."""
    region: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    wind_speed: float
    description: str
    icon: str
    condition: str
    advice: str
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "region": "Harare",
                "temperature": 25.0,
                "feels_like": 26.0,
                "humidity": 65,
                "pressure": 1013,
                "wind_speed": 3.5,
                "description": "partly cloudy",
                "icon": "02d",
                "condition": "cloudy",
                "advice": "Good for field work, moderate irrigation needed.",
                "timestamp": "2026-06-05T16:30:00Z",
            }
        }


class WeatherForecastResponse(BaseModel):
    """Weather forecast response."""
    region: str
    forecasts: List[Dict[str, Any]]
    timestamp: str


# ============================================================================
# Planting Calendar Schemas (F#80)
# ============================================================================

class CalendarActivity(BaseModel):
    """Planting calendar activity."""
    crop: str
    activity: str
    start_month: int
    end_month: int
    description: str
    variety: str
    days_to_harvest: int
    tips: str


class CalendarResponse(BaseModel):
    """Planting calendar response."""
    month: Optional[int] = None
    month_name: Optional[str] = None
    season: Optional[str] = None
    activities: List[CalendarActivity]


# ============================================================================
# Fertilizer Calculator Schemas (F#81)
# ============================================================================

class FertilizerCalculationRequest(BaseModel):
    """Fertilizer calculation request."""
    crop: CropType = Field(..., description="Crop type")
    area_hectares: float = Field(..., gt=0, description="Area in hectares")
    soil_type: SoilType = Field(default=SoilType.LOAMY, description="Soil type")

    @validator('area_hectares')
    def validate_area(cls, v):
        if v > 10000:
            raise ValueError('Area cannot exceed 10,000 hectares')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "crop": "maize",
                "area_hectares": 5.0,
                "soil_type": "loamy",
            }
        }


class NPKRequirements(BaseModel):
    """NPK fertilizer requirements in kg."""
    n: float
    p: float
    k: float


class FertilizerRecommendation(BaseModel):
    """Fertilizer blend recommendation."""
    blend: str
    amount_kg: float
    npk: Dict[str, int]


class FertilizerApplication(BaseModel):
    """Fertilizer application details."""
    npk_kg: NPKRequirements
    recommendations: List[FertilizerRecommendation]


class FertilizerCalculationResponse(BaseModel):
    """Fertilizer calculation response."""
    crop: str
    area_hectares: float
    soil_type: str
    basal_fertilizer: FertilizerApplication
    top_dressing_fertilizer: FertilizerApplication
    total_requirements: Dict[str, NPKRequirements]
    tips: List[str]


# ============================================================================
# Farming Tips Schemas (F#78)
# ============================================================================

class FarmingTip(BaseModel):
    """Farming tip."""
    id: str
    title: str
    category: str
    content: str
    season: str
    tags: List[str]
    created_at: Optional[str] = None


class FarmingTipResponse(BaseModel):
    """Farming tip response."""
    tip: FarmingTip
