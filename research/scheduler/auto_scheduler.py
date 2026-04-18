#!/usr/bin/env python
"""
AUTOMATIC JUPYTER NOTEBOOK SCHEDULER
Runs notebooks on schedule and pushes results to backend app
"""

import os
import sys
import yaml
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from notebook_executor import NotebookExecutor
from result_publisher import ResultPublisher

# Setup logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoNotebookScheduler:
    """
    Automatic scheduler that:
    1. Runs Jupyter notebooks on schedule
    2. Captures results (model accuracy, predictions, insights)
    3. Sends results to backend API
    4. Updates app cache with fresh predictions
    """
    
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).parent / 'schedule_config.yaml'
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.scheduler = BackgroundScheduler(timezone='Africa/Harare')
        self.executor = NotebookExecutor()
        self.publisher = ResultPublisher(
            api_base_url=self.config['global']['backend_api_url']
        )
        self.jobs = []
        
        logger.info("✅ Auto Notebook Scheduler initialized")
    
    def setup_all_jobs(self):
        """Setup all scheduled jobs from config"""
        
        for job_config in self.config['jobs']:
            job_name = job_config['name']
            notebook_path = job_config['notebook_path']
            schedule_type = job_config['schedule']['type']
            
            # Create trigger based on schedule type
            if schedule_type == 'cron':
                cron = job_config['schedule']['cron']
                trigger = CronTrigger(
                    hour=cron.get('hour', 0),
                    minute=cron.get('minute', 0),
                    day=cron.get('day', '*'),
                    month=cron.get('month', '*'),
                    day_of_week=cron.get('day_of_week', '*')
                )
            elif schedule_type == 'interval':
                interval = job_config['schedule']['interval']
                trigger = IntervalTrigger(
                    hours=interval.get('hours', 0),
                    minutes=interval.get('minutes', 0)
                )
            else:
                logger.error(f"Unknown schedule type: {schedule_type}")
                continue
            
            # Add job to scheduler
            job = self.scheduler.add_job(
                func=self._run_and_publish,
                trigger=trigger,
                id=job_name,
                args=[job_name, notebook_path, job_config.get('parameters', {})],
                replace_existing=True
            )
            
            # Defensive check for next_run_time (handles version mismatches or tentative scheduling)
            next_run = getattr(job, 'next_run_time', None)
            if next_run is None:
                # If scheduler isn't started yet, it might be tentatively scheduled
                next_run = "Tentatively Scheduled"
            
            self.jobs.append({
                'name': job_name,
                'notebook': notebook_path,
                'schedule': schedule_type,
                'next_run': str(next_run)
            })
            
            logger.info(f"📅 Scheduled: {job_name} - {schedule_type} (Next: {next_run})")
        
        return self.jobs
    
    def _run_and_publish(self, job_name, notebook_path, parameters):
        """
        Execute notebook and publish results to backend
        This is the main workflow for each scheduled job
        """
        
        logger.info(f"🚀 Starting scheduled job: {job_name}")
        logger.info(f"   Notebook: {notebook_path}")
        logger.info(f"   Parameters: {parameters}")
        
        start_time = datetime.now()
        
        try:
            # STEP 1: Execute the notebook
            execution_result = self.executor.execute_notebook(
                notebook_path=notebook_path,
                parameters=parameters,
                timeout_seconds=self.config['global'].get('timeout_seconds', 3600)
            )
            
            if not execution_result['success']:
                logger.error(f"❌ Notebook execution failed: {execution_result.get('error')}")
                self._send_alert(job_name, execution_result)
                return
            
            logger.info(f"✅ Notebook executed in {execution_result['execution_time']:.2f}s")
            
            # STEP 2: Extract results from notebook
            results = self.executor.extract_results(execution_result['output_path'])
            
            # STEP 3: Add metadata
            results['job_name'] = job_name
            results['executed_at'] = datetime.now().isoformat()
            results['execution_time_seconds'] = execution_result['execution_time']
            
            # STEP 4: Publish results to backend API
            publish_result = self.publisher.publish_results(results)
            
            if publish_result['success']:
                logger.info(f"✅ Results published to backend: {publish_result['message']}")
            else:
                logger.error(f"❌ Failed to publish results: {publish_result.get('error')}")
            
            # STEP 5: Update model weights if needed
            if 'model_weights_path' in results:
                self.publisher.update_model_weights(results['model_weights_path'])
            
            # STEP 6: Log completion
            self._log_job_completion(job_name, results, start_time)
            
        except Exception as e:
            logger.error(f"❌ Job failed: {str(e)}")
            self._send_alert(job_name, {'error': str(e)})
    
    def _log_job_completion(self, job_name, results, start_time):
        """Log job completion to database via API"""
        
        duration = (datetime.now() - start_time).total_seconds()
        
        log_data = {
            'job_name': job_name,
            'status': 'success',
            'duration_seconds': duration,
            'accuracy': results.get('accuracy'),
            'metrics': results.get('metrics', {}),
            'completed_at': datetime.now().isoformat()
        }
        
        # Send to backend for persistence
        try:
            response = requests.post(
                f"{self.config['global']['backend_api_url']}/ml/jobs/log",
                json=log_data,
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"📝 Job log saved to database")
        except Exception as e:
            logger.warning(f"Could not save job log: {e}")
    
    def _send_alert(self, job_name, error_info):
        """Send alert when job fails"""
        alert_data = {
            'job_name': job_name,
            'status': 'failed',
            'error': str(error_info),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            requests.post(
                f"{self.config['global']['backend_api_url']}/ml/jobs/alert",
                json=alert_data,
                timeout=5
            )
        except Exception:
            pass
        
        logger.error(f"🚨 ALERT: Job {job_name} failed")
    
    def start(self):
        """Start the scheduler"""
        self.setup_all_jobs()
        self.scheduler.start()
        
        logger.info("="*60)
        logger.info("🚀 AUTO NOTEBOOK SCHEDULER STARTED")
        logger.info("="*60)
        
        for job in self.jobs:
            logger.info(f"   📓 {job['name']} - Next run: {job['next_run']}")
        
        return self
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("🛑 Auto Notebook Scheduler stopped")
    
    def run_job_now(self, job_name):
        """Manually trigger a job"""
        for job_config in self.config['jobs']:
            if job_config['name'] == job_name:
                logger.info(f"▶️ Manually triggering: {job_name}")
                self._run_and_publish(
                    job_name,
                    job_config['notebook_path'],
                    job_config.get('parameters', {})
                )
                return True
        
        logger.error(f"Job not found: {job_name}")
        return False
    
    def list_jobs(self):
        """List all scheduled jobs"""
        print("\n" + "="*60)
        print("📋 SCHEDULED NOTEBOOK JOBS")
        print("="*60)
        
        for job in self.jobs:
            print(f"\n📓 {job['name']}")
            print(f"   Notebook: {job['notebook']}")
            print(f"   Schedule: {job['schedule']}")
            print(f"   Next run: {job['next_run']}")
        
        return self.jobs


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto Notebook Scheduler')
    parser.add_argument('--start', action='store_true', help='Start scheduler')
    parser.add_argument('--run-now', type=str, help='Run specific job now')
    parser.add_argument('--list', action='store_true', help='List scheduled jobs')
    parser.add_argument('--config', type=str, help='Config file path')
    
    args = parser.parse_args()
    
    scheduler = AutoNotebookScheduler(config_path=args.config)
    
    if args.list:
        scheduler.list_jobs()
    elif args.run_now:
        scheduler.run_job_now(args.run_now)
    elif args.start:
        try:
            scheduler.start()
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
