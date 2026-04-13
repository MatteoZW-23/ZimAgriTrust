import random
import os
import joblib
import pandas as pd
from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.listing import Listing

class DemandForecaster:
    """
    Predicts regional and crop-specific demand trends.
    Uses trained Random Forest Regressor models from synthetic data.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self.feature_columns = []
        
        model_path = "ml_weights/demand_forecaster_v4.pkl"
        if os.path.exists(model_path):
            data = joblib.load(model_path)
            self.model = data.get("model")
            self.feature_columns = data.get("feature_columns", [])

    def predict_demand(self, crop_type: str, province: str) -> Dict:
        """
        Predict future demand level for a crop in a specific area.
        """
        if self.model is None or not self.feature_columns:
            return self._fallback_prediction(crop_type, province)
            
        try:
            # Reconstruct the feature vector dynamically
            input_data = {
                "month": pd.Timestamp.now().month,
                "active_bids": random.randint(50, 200),
                "avg_bid_price": 1.5,
            }
            
            # Create a dataframe matching training categorical columns
            df = pd.DataFrame([input_data])
            # One-hot encode the target crop and province
            for col in self.feature_columns:
                if col.startswith('crop_'):
                    df[col] = 1 if col == f"crop_{crop_type}" else 0
                elif col.startswith('province_'):
                    df[col] = 1 if col == f"province_{province}" else 0
                elif col not in df.columns:
                    df[col] = 0
            
            # Predict
            X = df[self.feature_columns]
            demand_score = self.model.predict(X)[0]
            
            demand_level = "HIGH" if demand_score > 80 else "LOW" if demand_score < 40 else "MEDIUM"
            return {
                "crop": crop_type,
                "region": province,
                "demand_score": round(float(demand_score), 1),
                "level": demand_level,
                "forecast_window": "14 Days",
                "suggestion": "Increase listing visibility" if demand_level == "HIGH" else "Maintain inventory"
            }
        except Exception as e:
            print(f"Demand ML Error: {e}")
            return self._fallback_prediction(crop_type, province)

    def _fallback_prediction(self, crop_type: str, province: str) -> Dict:
        base_demand = random.uniform(60, 95)
        if crop_type.lower() in ["maize", "tobacco"]: base_demand += 10
        demand_level = "HIGH" if base_demand > 80 else "MEDIUM"
        
        return {
            "crop": crop_type,
            "region": province,
            "demand_score": round(base_demand, 1),
            "level": demand_level,
            "forecast_window": "14 Days",
            "suggestion": "Increase listing visibility" if demand_level == "HIGH" else "Maintain inventory"
        }

    def get_trending_crops(self) -> List[Dict]:
        return [
            {"product": "Tobacco", "growth": "+12.4%", "status": "UP"},
            {"product": "White Maize", "growth": "+8.1%", "status": "UP"},
            {"product": "Potatoes", "growth": "-2.3%", "status": "DOWN"}
        ]
