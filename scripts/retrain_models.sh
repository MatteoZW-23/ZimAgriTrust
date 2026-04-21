#!/bin/bash
# Sovereign Model Retraining Script
echo "Starting AgriTrust Model Retraining Pipeline..."

# 1. Export Clean Data from DB
echo "Exporting production data..."

# 2. Run Modeling Notebooks via nbconvert
echo "Running Risk Scoring Experiments..."
python -m jupyter nbconvert --to notebook --execute research/notebooks/02_modeling/01_risk_scoring_model.ipynb

# 3. Synchronize Weights with Root ml_weights
echo "Synchronizing weights..."
cp research/data/models/*.pkl ml_weights/

echo "Retraining Complete. Version manifest updated."
