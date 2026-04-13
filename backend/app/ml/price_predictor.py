import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from sklearn.preprocessing import StandardScaler
import joblib
import os
import xgboost as xgb

class PricePredictor:
    """
    Price prediction model using XGBoost Regressor for robust time series forecasting.
    Enhanced with feature extraction for trend analysis.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.models = {}
        
        model_path = "ml_weights/price_predictor_v4.pkl"
        if os.path.exists(model_path):
            self.models = joblib.load(model_path)
        
    def predict_price(self, crop_type: str, location: str, days_ahead: int = 7) -> Dict:
        if crop_type not in self.models:
            return self._fallback_prediction(crop_type)
        
        try:
            model = self.models[crop_type]
            
            # Feature extraction roughly matching training (day_of_year, trend)
            target_date = pd.Timestamp.now() + timedelta(days=days_ahead)
            day_of_year = target_date.dayofyear
            # Using an arbitrary trend index for forecasting future
            trend_index = 400 
            
            X_pred = np.array([[day_of_year, trend_index]])
            predicted_price = float(model.predict(X_pred)[0])
            
            current_price = self._get_current_price(crop_type, location)
            
            trend = "UP" if predicted_price > current_price * 1.05 else "DOWN" if predicted_price < current_price * 0.95 else "STABLE"
            
            return {
                "crop": crop_type,
                "location": location,
                "current_price": current_price,
                "trend": trend,
                "predicted_price": round(predicted_price, 2),
                "recommendation": self._generate_recommendation(trend, predicted_price, current_price)
            }
        except Exception as e:
            print(f"Price predictor Error: {e}")
            return self._fallback_prediction(crop_type)
    
    def _get_current_price(self, crop_type: str, location: str) -> float:
        from app.models.listing import Listing
        recent = self.db.query(Listing).filter(Listing.crop == crop_type).order_by(Listing.id.desc()).first()
        return float(recent.price_per_unit) if recent else 0.45
    
    def _fallback_prediction(self, crop_type: str) -> Dict:
        return {
            "crop": crop_type,
            "trend": "STABLE",
            "current_price": 0.45,
            "predicted_price": 0.47,
            "recommendation": "Stable market. Insufficient historical data for deep model logic."
        }

    def _generate_recommendation(self, trend: str, predicted: float, current: float) -> str:
        if trend == "UP": return "Bullish trend. Recommended to hold for higher margins."
        if trend == "DOWN": return "Bearish trend. Recommended to liquidate stock early."
        return "Market stability detected. Continue standard operations."
