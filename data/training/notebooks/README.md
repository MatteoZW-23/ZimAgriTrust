# AgriTrust — Jupyter Training Notebooks

| # | Notebook | Model | Output |
|---|---|---|---|
| 01 | `01_train_risk_scorer.ipynb` | Risk Scorer (Random Forest) | `ml_weights/risk_scorer_v4.pkl` |
| 02 | `02_train_fraud_detector.ipynb` | Fraud Detector (Isolation Forest) | `ml_weights/fraud_model_v1.pkl` |
| 03 | `03_train_price_forecaster.ipynb` | Price Forecaster (ARIMA + LSTM) | `ml_weights/arima_model.pkl` |
| 04 | `04_train_demand_forecaster.ipynb` | Demand Forecaster (XGBoost) | `ml_weights/demand_model_v1.pkl` |
| 05 | `05_train_crop_vision.ipynb` | Crop Vision (YOLOv8) | `ml_weights/crop_classifier.pt` |

## Quick Start

```bash
# 1. Install Jupyter + dependencies
pip install jupyter notebook kagglehub ultralytics xgboost tensorflow

# 2. Launch Jupyter from the repo root
jupyter notebook

# 3. Navigate to data/training/notebooks/
# 4. Open and run notebooks in order (01 → 05)
```

## Notes
- Each notebook tries to load **real data from the database first**, then falls back to synthetic data if the DB is empty.
- Notebooks 01–04 work immediately. Notebook 05 requires Kaggle credentials.
- All weights are saved to `ml_weights/` at the repo root — the backend loads them automatically.
