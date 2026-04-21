from sqlalchemy import Column, Integer, String, JSON, DateTime, Float
from app.db.base_class import Base
from datetime import datetime

class ModelVersion(Base):
    __tablename__ = "ml_model_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)
    version = Column(String)
    architecture = Column(String)
    trained_at = Column(DateTime, default=datetime.utcnow)
    deployed_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=0) # 1 for active, 0 for inactive
    accuracy = Column(Float)
    weights_path = Column(String)
    metrics = Column(JSON, default={})

class MLJobLog(Base):
    __tablename__ = "ml_job_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String)
    status = Column(String) # 'success', 'failed'
    duration_seconds = Column(Integer, nullable=True)
    accuracy = Column(Float, nullable=True)
    metrics = Column(JSON, default={})
    completed_at = Column(DateTime, default=datetime.utcnow)

class MLPrediction(Base):
    __tablename__ = "ml_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_type = Column(String) # 'price', 'risk', etc.
    crop_type = Column(String, nullable=True)
    location = Column(String, nullable=True)
    predicted_value = Column(String)
    confidence = Column(Float)
    valid_until = Column(DateTime)
    prediction_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

class MLInsight(Base):
    __tablename__ = "ml_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    insight_type = Column(String)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Alias for backward compatibility if needed, though MLModelMetadata was not used elsewhere
class MLModelMetadata(ModelVersion):
    __abstract__ = True
