import time
import schedule
import os

def run_retraining_pipeline():
    print("Executing Sovereign Retraining Pipeline...")
    os.system("python master_pipeline.py")

def monitor_data_drift():
    print("Checking for Data Drift in High-Trust Marketplace...")

# Schedule daily training
schedule.every().day.at("02:00").do(run_retraining_pipeline)
schedule.every(6).hours.do(monitor_data_drift)

if __name__ == "__main__":
    print("Sovereign Research Scheduler Online.")
    while True:
        schedule.run_pending()
        time.sleep(60)
