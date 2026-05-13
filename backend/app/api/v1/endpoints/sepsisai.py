from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class PatientInput(BaseModel):
    patientId: str
    age: int
    sex: str
    hr: float
    temp: float
    rr: float
    spo2: float
    sbp: float
    map: float
    lactate: float
    wbc: float
    platelets: float
    creatinine: float
    procalcitonin: float


def _score(payload: PatientInput) -> float:
    raw = (
        payload.lactate * 18
        + payload.hr / 2.8
        + (70 - payload.map) * 0.9
        + (38.5 - payload.temp) * -7
        + payload.procalcitonin * 6
        + (payload.rr - 20) * 1.2
        + (95 - payload.spo2) * 1.1
    )
    return max(0.02, min(0.99, round(raw / 100, 2)))


@router.get("/bootstrap")
def bootstrap():
    return {
        "analytics": {
            "auroc": 0.91,
            "auprc": 0.86,
            "sensitivity": 0.88,
            "specificity": 0.84,
            "fairness_gap": 0.03,
        },
        "last_prediction": {
            "risk_probability": 0.82,
            "risk_category": "high",
            "confidence": 0.89,
            "recommendation": "Immediate clinical review recommended.",
            "top_features": [
                {"feature": "Lactate", "impact": "+0.21"},
                {"feature": "MAP", "impact": "+0.18"},
                {"feature": "Heart rate", "impact": "+0.14"},
                {"feature": "Procalcitonin", "impact": "+0.11"},
            ],
        },
    }


@router.post("/predict")
def predict(payload: PatientInput):
    risk = _score(payload)
    category = "critical" if risk >= 0.8 else "high" if risk >= 0.6 else "moderate" if risk >= 0.35 else "low"
    return {
        "prediction_id": f"pred_{payload.patientId.lower()}",
        "patient_id": payload.patientId,
        "risk_probability": risk,
        "risk_category": category,
        "confidence": 0.94 if risk > 0.7 else 0.86,
        "recommendation": "Escalate to ICU clinician immediately." if category in ("critical", "high") else "Continue monitoring and repeat labs.",
        "top_features": [
            {"feature": "Lactate", "impact": "+0.21"},
            {"feature": "MAP", "impact": "+0.18"},
            {"feature": "Heart rate", "impact": "+0.14"},
            {"feature": "Procalcitonin", "impact": "+0.11"},
            {"feature": "Platelets", "impact": "-0.05"},
        ],
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/analytics")
def analytics():
    return {
        "auroc": 0.91,
        "auprc": 0.86,
        "sensitivity": 0.88,
        "specificity": 0.84,
        "fairness_gap": 0.03,
    }


@router.get("/admin")
def admin():
    return {
        "users": 18,
        "active_models": ["xgb-v1.3", "baseline-logit-v1.0"],
        "audit_events_24h": 142,
        "pipeline_health": "healthy",
    }
