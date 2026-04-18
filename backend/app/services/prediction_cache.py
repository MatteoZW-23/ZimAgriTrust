"""
PREDICTION CACHE SERVICE
Manages Redis cache for fast app access to ML predictions
"""

import json
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PredictionCache:
    """
    Redis-based cache for ML predictions
    Ensures app gets instant access to latest model outputs
    """
    
    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.ttl_predictions = 3600  # 1 hour
        self.ttl_insights = 86400     # 24 hours
    
    # ========== PRICE PREDICTIONS ==========
    
    def update_price_predictions(self, predictions: Dict):
        """Update price predictions in cache"""
        for crop, data in predictions.items():
            key = f"price:{crop}:{data.get('location', 'national')}"
            self.redis_client.setex(
                key,
                self.ttl_predictions,
                json.dumps({
                    'price': data.get('price'),
                    'trend': data.get('trend'),
                    'confidence': data.get('confidence', 0.85),
                    'updated_at': datetime.now().isoformat()
                })
            )
        logger.info(f"Updated {len(predictions)} price predictions in cache")
    
    def get_price_prediction(self, crop: str, location: str) -> Optional[Dict]:
        """Get price prediction from cache"""
        key = f"price:{crop}:{location}"
        data = self.redis_client.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    # ========== RISK SCORES ==========
    
    def update_risk_score(self, user_id: int, risk_score: float):
        """Update user risk score in cache"""
        key = f"risk:{user_id}"
        self.redis_client.setex(
            key,
            self.ttl_predictions,
            json.dumps({
                'risk_score': risk_score,
                'updated_at': datetime.now().isoformat()
            })
        )
    
    def get_risk_score(self, user_id: int) -> Optional[float]:
        """Get user risk score from cache"""
        key = f"risk:{user_id}"
        data = self.redis_client.get(key)
        
        if data:
            return json.loads(data).get('risk_score')
        return None
    
    # ========== INSIGHTS ==========
    
    def update_insights(self, insights: list):
        """Update insights in cache"""
        key = "insights:latest"
        self.redis_client.setex(
            key,
            self.ttl_insights,
            json.dumps({
                'insights': insights,
                'updated_at': datetime.now().isoformat()
            })
        )
    
    def get_latest_insights(self, limit: int = 5) -> list:
        """Get latest insights from cache"""
        key = "insights:latest"
        data = self.redis_client.get(key)
        
        if data:
            insights_data = json.loads(data)
            return insights_data.get('insights', [])[:limit]
        return []
    
    # ========== MODEL METRICS ==========
    
    def update_model_accuracy(self, model_name: str, accuracy: float):
        """Update model accuracy in cache"""
        key = f"metrics:{model_name}"
        self.redis_client.setex(
            key,
            self.ttl_insights,
            json.dumps({
                'accuracy': accuracy,
                'updated_at': datetime.now().isoformat()
            })
        )
    
    def update_model_metrics(self, metrics: Dict):
        """Update all model metrics"""
        for model, metric_data in metrics.items():
            self.update_model_accuracy(model, metric_data.get('accuracy', 0))
    
    def get_model_metrics(self) -> Dict:
        """Get all model metrics from cache"""
        metrics = {}
        keys = self.redis_client.keys("metrics:*")
        
        for key in keys:
            model_name = key.replace("metrics:", "")
            data = self.redis_client.get(key)
            if data:
                metrics[model_name] = json.loads(data)
        
        return metrics
    
    # ========== FRAUD ALERTS ==========
    
    def set_fraud_alert(self, transaction_id: int, fraud_score: float):
        """Set fraud alert for a transaction"""
        key = f"fraud_alert:{transaction_id}"
        self.redis_client.setex(
            key,
            3600,  # 1 hour
            json.dumps({
                'fraud_score': fraud_score,
                'alert': fraud_score > 0.7,
                'timestamp': datetime.now().isoformat()
            })
        )
    
    def get_fraud_alert(self, transaction_id: int) -> Optional[Dict]:
        """Get fraud alert for a transaction"""
        key = f"fraud_alert:{transaction_id}"
        data = self.redis_client.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    # ========== DEMAND FORECAST ==========
    
    def update_demand_forecast(self, forecasts: Dict):
        """Update demand forecasts in cache"""
        key = "demand:forecast"
        self.redis_client.setex(
            key,
            self.ttl_insights,
            json.dumps({
                'forecasts': forecasts,
                'updated_at': datetime.now().isoformat()
            })
        )
    
    def get_demand_forecast(self, crop: str = None) -> Dict:
        """Get demand forecasts from cache"""
        key = "demand:forecast"
        data = self.redis_client.get(key)
        
        if data:
            forecasts = json.loads(data)
            if crop:
                return forecasts.get('forecasts', {}).get(crop, {})
            return forecasts.get('forecasts', {})
        return {}
