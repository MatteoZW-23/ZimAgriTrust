from typing import Dict
from datetime import datetime


# Zimbabwe agro-ecological zone yield benchmarks (tonnes/ha)
# Source: AGRITEX / FAO Zimbabwe country data
_CROP_BENCHMARKS: Dict[str, Dict] = {
    "Maize":          {"base": 5.5, "irrigated_bonus": 2.5, "optimal_ph": 6.5},
    "Wheat":          {"base": 4.0, "irrigated_bonus": 2.0, "optimal_ph": 6.5},
    "Soybeans":       {"base": 2.5, "irrigated_bonus": 1.0, "optimal_ph": 6.3},
    "Tobacco":        {"base": 2.2, "irrigated_bonus": 0.8, "optimal_ph": 5.8},
    "Sorghum":        {"base": 3.0, "irrigated_bonus": 1.5, "optimal_ph": 6.0},
    "Groundnuts":     {"base": 1.8, "irrigated_bonus": 0.7, "optimal_ph": 6.0},
    "Sunflower Seeds":{"base": 1.5, "irrigated_bonus": 0.5, "optimal_ph": 6.5},
    "Sugar Beans":    {"base": 1.2, "irrigated_bonus": 0.6, "optimal_ph": 6.2},
    "Cotton":         {"base": 1.0, "irrigated_bonus": 0.5, "optimal_ph": 6.0},
}

_DEFAULT_BENCHMARK = {"base": 3.0, "irrigated_bonus": 1.0, "optimal_ph": 6.5}

# Zimbabwe seasonal rainfall index by month (1=Jan … 12=Dec)
# Rainy season Nov–Mar; dry Apr–Oct
_RAINFALL_INDEX: Dict[int, float] = {
    1: 1.10, 2: 1.05, 3: 1.00, 4: 0.85, 5: 0.70,
    6: 0.60, 7: 0.60, 8: 0.65, 9: 0.75, 10: 0.85,
    11: 1.05, 12: 1.10,
}


class YieldPredictor:
    """
    Deterministic yield forecasting engine.
    Uses AGRITEX benchmark yields adjusted for:
      - Soil pH deviation from crop optimum
      - Irrigation availability
      - Seasonal rainfall index (current month)
      - Fertiliser application
    No random values — same inputs always produce the same output.
    """

    def __init__(self):
        self.architecture = "Agronomic Rule Engine (AGRITEX benchmarks)"

    def forecast_yield(self, farm_data: Dict) -> Dict:
        """
        farm_data keys (all optional, sensible defaults applied):
          crop_type, hectares, soil_ph, has_irrigation,
          fertiliser_applied (bool), province
        """
        try:
            crop = farm_data.get("crop_type", "Maize")
            hectares = max(0.1, float(farm_data.get("hectares", 1.0)))
            soil_ph = float(farm_data.get("soil_ph", 6.5))
            has_irrigation = bool(farm_data.get("has_irrigation", False))
            fertiliser = bool(farm_data.get("fertiliser_applied", False))

            bench = _CROP_BENCHMARKS.get(crop, _DEFAULT_BENCHMARK)

            # 1. Base yield from benchmark
            base = bench["base"]

            # 2. Irrigation bonus
            if has_irrigation:
                base += bench["irrigated_bonus"]

            # 3. Soil pH adjustment (±5% per 0.5 unit deviation from optimum)
            ph_dev = abs(soil_ph - bench["optimal_ph"])
            ph_factor = max(0.6, 1.0 - (ph_dev / 0.5) * 0.05)
            base *= ph_factor

            # 4. Fertiliser bonus (+15%)
            if fertiliser:
                base *= 1.15

            # 5. Seasonal rainfall index
            month = datetime.utcnow().month
            rainfall_factor = _RAINFALL_INDEX.get(month, 0.85)
            final_yield_per_ha = round(base * rainfall_factor, 2)
            total_tonnage = round(final_yield_per_ha * hectares, 1)

            # Confidence: lower when pH is far from optimum or no irrigation in dry season
            confidence = 0.88
            if ph_dev > 1.0:
                confidence -= 0.10
            if not has_irrigation and rainfall_factor < 0.75:
                confidence -= 0.08
            confidence = round(max(0.50, confidence), 2)

            return {
                "status": "success",
                "crop": crop,
                "forecasted_yield": {
                    "tonnes_per_hectare": final_yield_per_ha,
                    "total_tonnage": total_tonnage,
                },
                "confidence": confidence,
                "factors": {
                    "base_benchmark_t_ha": bench["base"],
                    "irrigation_applied": has_irrigation,
                    "ph_factor": round(ph_factor, 3),
                    "fertiliser_bonus": fertiliser,
                    "seasonal_rainfall_index": rainfall_factor,
                    "month": month,
                },
                "architecture": self.architecture,
                "note": "Based on AGRITEX Zimbabwe benchmark yields. Actual results vary by variety and management.",
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}


# Global instance
yield_engine = YieldPredictor()
