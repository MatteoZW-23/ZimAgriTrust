"""
RESULT PUBLISHER
Pushes notebook results to backend API for app consumption
"""

import requests
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ResultPublisher:
    """
    Publishes ML results to backend API
    This is the bridge between research notebooks and the app
    """
    
    def __init__(self, api_base_url="http://backend:8000/api/v1"):
        self.api_base_url = api_base_url
        self.endpoints = {
            'predictions': f"{api_base_url}/ml/predictions",
            'model_metrics': f"{api_base_url}/ml/metrics",
            'insights': f"{api_base_url}/ml/insights",
            'job_logs': f"{api_base_url}/ml/jobs/log",
            'alert': f"{api_base_url}/ml/jobs/alert",
            'weights': f"{api_base_url}/ml/weights"
        }
    
    def publish_results(self, results):
        """
        Publish notebook results to backend
        
        Results can include:
        - Model accuracy metrics
        - Price predictions
        - Risk scores
        - Fraud alerts
        - Insights
        """
        
        logger.info(f"📤 Publishing results to backend: {self.api_base_url}")
        
        published = {
            'success': False,
            'items_published': []
        }
        
        # Publish predictions if available
        if results.get('predictions'):
            pred_result = self._publish_predictions(results['predictions'])
            if pred_result:
                published['items_published'].append('predictions')
        
        # Publish metrics if available
        if results.get('metrics'):
            metrics_result = self._publish_metrics(results['metrics'], results.get('job_name'))
            if metrics_result:
                published['items_published'].append('metrics')
        
        # Publish insights if available
        if results.get('insights'):
            insights_result = self._publish_insights(results['insights'])
            if insights_result:
                published['items_published'].append('insights')
        
        # Publish accuracy if available
        if results.get('accuracy'):
            self._publish_accuracy(results['accuracy'], results.get('job_name'))
            published['items_published'].append('accuracy')
        
        if published['items_published']:
            published['success'] = True
            published['message'] = f"Published: {', '.join(published['items_published'])}"
        else:
            published['message'] = "No data to publish"
        
        return published
    
    def _publish_predictions(self, predictions):
        """Send price predictions to backend"""
        try:
            response = requests.post(
                f"{self.endpoints['predictions']}/price",
                json={
                    'predictions': predictions,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'notebook_scheduler'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Published {len(predictions)} price predictions")
                return True
            else:
                logger.error(f"Failed to publish predictions: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing predictions: {e}")
            return False
    
    def _publish_metrics(self, metrics, job_name):
        """Send model metrics to backend"""
        try:
            response = requests.post(
                self.endpoints['model_metrics'],
                json={
                    'job_name': job_name,
                    'metrics': metrics,
                    'timestamp': datetime.now().isoformat()
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Published model metrics: {list(metrics.keys())}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error publishing metrics: {e}")
            return False
    
    def _publish_insights(self, insights):
        """Send insights to backend"""
        try:
            response = requests.post(
                self.endpoints['insights'],
                json={
                    'insights': insights,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'scheduled_analysis'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Published {len(insights)} insights")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error publishing insights: {e}")
            return False
    
    def _publish_accuracy(self, accuracy, job_name):
        """Send model accuracy to backend"""
        try:
            response = requests.post(
                self.endpoints['model_metrics'],
                json={
                    'job_name': job_name,
                    'metrics': {'accuracy': accuracy},
                    'timestamp': datetime.now().isoformat()
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def update_model_weights(self, weights_path):
        """
        Notify backend that new model weights are available
        Triggers backend to reload the model
        """
        try:
            response = requests.post(
                self.endpoints['weights'],
                json={
                    'weights_path': str(weights_path),
                    'timestamp': datetime.now().isoformat()
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Model weights updated: {weights_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating model weights: {e}")
            return False
