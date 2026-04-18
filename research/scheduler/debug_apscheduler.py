import apscheduler
from apscheduler.jobs import Job
print(f"APScheduler Version: {apscheduler.__version__}")
# Print attributes of Job class
print(f"Job attributes: {dir(Job)}")
