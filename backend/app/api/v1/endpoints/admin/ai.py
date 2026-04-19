import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.ml_metadata import ModelVersion, MLJobLog
from app.models.system_audit import SystemAudit

router = APIRouter()

@router.get("/models")
def list_ml_models(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 199: View all ML models and their performance metrics.
    """
    return db.query(ModelVersion).order_by(ModelVersion.deployed_at.desc()).all()

@router.get("/models/{model_name}/versions")
def get_model_versions(
    model_name: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 207: Compare model versions.
    """
    return db.query(ModelVersion).filter(ModelVersion.model_name == model_name).order_by(ModelVersion.version.desc()).all()

@router.post("/models/{model_id}/activate")
def activate_model_version(
    model_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 206: Deploy new version (Switch active model).
    """
    model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model version not found")
        
    # Deactivate others of same name
    db.query(ModelVersion).filter(ModelVersion.model_name == model.model_name).update({"is_active": 0})
    model.is_active = 1
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="ML_MODEL_ACTIVATE",
        target_type="ML_MODEL",
        target_id=None,
        note=f"Activated {model.model_name} version {model.version}"
    )
    db.add(audit)
    db.commit()
    return {"status": "SUCCESS", "active_version": model.version}

@router.get("/models/{model_name}/drift")
def get_model_drift(
    model_name: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 200: View model drift.
    """
    # Mock drift calculation
    return {
        "model": model_name,
        "drift_score": 0.12,
        "status": "STABLE", # OR DRIFT_DETECTED
        "feature_impact": [
            {"feature": "tx_amount", "drift": 0.05},
            {"feature": "user_age", "drift": 0.22}
        ]
    }

@router.post("/models/{model_name}/retrain")
def trigger_model_retrain(
    model_name: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 202: Manually trigger model retraining.
    """
    # In a real system, this would trigger a Celery task
    audit = SystemAudit(
        admin_id=admin.id,
        action="ML_MODEL_RETRAIN",
        target_type="ML_MODEL",
        note=f"Manual retraining of {model_name} triggered"
    )
    db.add(audit)
    db.commit()
    return {"status": "JOB_QUEUED", "job_id": str(uuid.uuid4())}
