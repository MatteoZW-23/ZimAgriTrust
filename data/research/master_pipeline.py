#!/usr/bin/env python
"""
MASTER PIPELINE ORCHESTRATION
==============================
Runs all notebooks in sequence and exports to production

Usage:
    python master_pipeline.py --all
    python master_pipeline.py --clean-only
    python master_pipeline.py --train-risk
"""

import subprocess
import sys
import argparse
from datetime import datetime
import json

class NotebookOrchestrator:
    """Run and manage notebook execution sequence"""
    
    NOTEBOOKS = {
        'data_cleaning': {
            'path': 'notebooks/01_data/02_data_cleaning.ipynb',
            'depends_on': [],
            'exports_to': ['backend/app/ml/preprocessing.py']
        },
        'feature_engineering': {
            'path': 'notebooks/01_data/04_feature_engineering.ipynb',
            'depends_on': ['data_cleaning'],
            'exports_to': ['backend/app/ml/feature_engineering.py']
        },
        'risk_model': {
            'path': 'notebooks/02_modeling/01_risk_scoring_model.ipynb',
            'depends_on': ['feature_engineering'],
            'exports_to': ['backend/app/ml/risk_scorer.py', 
                          'backend/ml_weights/risk_scorer_v4.pkl']
        },
        'price_model': {
            'path': 'notebooks/02_modeling/02_price_prediction_model.ipynb',
            'depends_on': ['feature_engineering'],
            'exports_to': ['backend/app/ml/price_predictor.py',
                          'backend/ml_weights/price_engine_v2.pt']
        },
        'fraud_model': {
            'path': 'notebooks/02_modeling/03_fraud_detection_model.ipynb',
            'depends_on': ['feature_engineering'],
            'exports_to': ['backend/app/ml/fraud_detector.py',
                          'backend/ml_weights/fraud_model_v1.pkl']
        },
        'model_validation': {
            'path': 'notebooks/03_evaluation/04_production_readiness.ipynb',
            'depends_on': ['risk_model', 'price_model', 'fraud_model'],
            'exports_to': []
        }
    }
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
    
    def run_notebook(self, notebook_name, execute=True):
        """Execute a notebook using papermill or jupyter nbconvert"""
        
        notebook_info = self.NOTEBOOKS[notebook_name]
        notebook_path = notebook_info['path']
        
        print(f"\n{'='*60}")
        print(f"📓 Running: {notebook_name}")
        print(f"   Path: {notebook_path}")
        print(f"{'='*60}")
        
        if execute:
            # Use nbconvert to execute notebook
            cmd = [
                "jupyter", "nbconvert", "--to", "notebook", 
                "--execute", notebook_path,
                "--output", f"{notebook_name}_executed.ipynb",
                "--ExecutePreprocessor.timeout=600"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {notebook_name} completed successfully")
                self.results[notebook_name] = {'status': 'success', 'timestamp': datetime.now().isoformat()}
                return True
            else:
                print(f"❌ {notebook_name} failed")
                print(f"Error: {result.stderr}")
                self.results[notebook_name] = {'status': 'failed', 'error': result.stderr}
                return False
        
        return True
    
    def run_pipeline(self, start_from=None, stop_at=None):
        """Run notebooks in dependency order"""
        
        # Order by dependencies
        execution_order = ['data_cleaning', 'feature_engineering', 
                          'risk_model', 'price_model', 'fraud_model', 
                          'model_validation']
        
        if start_from:
            start_idx = execution_order.index(start_from)
            execution_order = execution_order[start_idx:]
        
        if stop_at:
            stop_idx = execution_order.index(stop_at)
            execution_order = execution_order[:stop_idx+1]
        
        print("\n" + "="*60)
        print("🚀 STARTING MASTER PIPELINE")
        print(f"   Start time: {self.start_time}")
        print(f"   Notebooks to run: {len(execution_order)}")
        print("="*60)
        
        for notebook in execution_order:
            success = self.run_notebook(notebook)
            if not success:
                print(f"\n❌ Pipeline stopped at {notebook}")
                break
        
        # Save results
        self.save_results()
        
        return self.results
    
    def save_results(self):
        """Save pipeline execution results"""
        results_path = "exports/pipeline_results.json"
        
        with open(results_path, 'w') as f:
            json.dump({
                'execution_time': str(datetime.now() - self.start_time),
                'results': self.results
            }, f, indent=2)
        
        print(f"\n📊 Results saved to: {results_path}")
    
    def export_to_production(self):
        """Run the production export script"""
        print("\n" + "="*60)
        print("📤 EXPORTING TO PRODUCTION")
        print("="*60)
        
        subprocess.run(["python", "production_pipeline_run.py", "--export-all"])

def main():
    parser = argparse.ArgumentParser(description='Run ZimAgritrust ML Pipeline')
    parser.add_argument('--all', action='store_true', help='Run all notebooks')
    parser.add_argument('--clean-only', action='store_true', help='Run only data cleaning')
    parser.add_argument('--train-risk', action='store_true', help='Train risk model only')
    parser.add_argument('--train-price', action='store_true', help='Train price model only')
    parser.add_argument('--train-fraud', action='store_true', help='Train fraud model only')
    parser.add_argument('--validate', action='store_true', help='Run validation only')
    parser.add_argument('--export', action='store_true', help='Export to production')
    
    args = parser.parse_args()
    
    orchestrator = NotebookOrchestrator()
    
    if args.all:
        orchestrator.run_pipeline()
    elif args.clean_only:
        orchestrator.run_pipeline(start_from='data_cleaning', stop_at='data_cleaning')
    elif args.train_risk:
        orchestrator.run_pipeline(start_from='risk_model', stop_at='risk_model')
    elif args.train_price:
        orchestrator.run_pipeline(start_from='price_model', stop_at='price_model')
    elif args.train_fraud:
        orchestrator.run_pipeline(start_from='fraud_model', stop_at='fraud_model')
    elif args.validate:
        orchestrator.run_pipeline(start_from='model_validation', stop_at='model_validation')
    elif args.export:
        orchestrator.export_to_production()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
