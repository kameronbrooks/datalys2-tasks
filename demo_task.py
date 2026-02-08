import time
import datetime
import sys
# Import the new simple auto-scheduler
from datalys2_tasks.scheduler.autorun import ensure_task

def my_job_logic():
    """The actual work this script performs."""
    print(">>> JOB STARTED <<<")
    print(f"Current time: {datetime.datetime.now()}")
    print("Working hard...")
    time.sleep(10)
    print(">>> JOB FINISHED <<<")

if __name__ == "__main__":
    # Define how we want this script to be scheduled
    # We want it to run once, 2 minutes from now.
    
    # Calculate start time for demo purposes
    start_dt = datetime.datetime.now() + datetime.timedelta(minutes=2)
    start_time_str = start_dt.strftime("%H:%M")

    # This single line handles the "self-scheduling" logic.
    # 1. If the task "SimpleDemoTask" exists, it does nothing and returns True.
    # 2. If it doesn't exist, it uses 'schtasks' to register this file to run at the specified time.
    ensure_task(
        task_name="SimpleDemoTask",
        schedule="ONCE",
        start_time=start_time_str
        # force_update=True # Uncomment this if you want to change the schedule every time you run it manually
    )

    # After ensuring the schedule exists, we run the actual logic.
    my_job_logic()
