import sys
import os
from typing import Optional, List
from .windows import WindowsTaskScheduler

def ensure_task(
    task_name: str,
    schedule: str = "DAILY",
    start_time: Optional[str] = None,
    interval_minutes: Optional[int] = None,
    script_args: Optional[List[str]] = None,
    force_update: bool = False
) -> bool:
    """
    Ensures that the currently executing Python script is registered as a Windows Task.
    
    Logic:
    1. Checks if a task with 'task_name' already exists in the scheduler (under \\datalys2\\).
    2. If it exists and force_update is False, does nothing and returns True.
    3. If it doesn't exist (or force_update is True), creates/updates the task pointing to this script.
    
    This allows a script to be "self-scheduling". When run manually, it registers itself.
    When run by the scheduler, it sees it's already registered and proceeds to execute its logic.
    
    Args:
        task_name (str): The unique name for the task (will be prefixed with \\datalys2\\).
        schedule (str): Schedule frequency (DAILY, HOURLY, MINUTE, ONCE, ONLOGON).
        start_time (str): Time in HH:mm format.
        interval_minutes (int): Interval for MINUTE schedule or duration.
        script_args (List[str]): Arguments to pass to the script when triggered by scheduler.
        force_update (bool): If True, updates the task parameters even if it exists.

    Returns:
        bool: True if task exists or was successfully created. False if creation failed.
    """
    scheduler = WindowsTaskScheduler()
    
    # 1. Check if task exists
    # The scheduler class prefix logic (\datalys2\) is handled inside query_task/create_task
    # providing we simply pass the name.
    print(f"[Datalys2] Checking scheduled task status for '{task_name}'...")
    existing_task = scheduler.query_task(task_name)
    
    if existing_task and not force_update:
        print(f"[Datalys2] Task '{task_name}' is already scheduled. Proceeding with execution.")
        return True
        
    # 2. Prepare for Scheduling
    # Determine the absolute path of the currently running script
    script_path = os.path.abspath(sys.argv[0])
    
    action = "Updating" if existing_task else "Creating"
    print(f"[Datalys2] {action} scheduled task for: {script_path}")
    
    # 3. Create/Update the task
    success = scheduler.create_task(
        task_name=task_name,
        script_path=script_path,
        schedule=schedule,
        start_time=start_time,
        interval_minutes=interval_minutes,
        args=script_args,
        force=True # Always force here because we either don't have it, or force_update is True
    )
    
    if success:
        print(f"[Datalys2] Task '{task_name}' successfully scheduled.")
    else:
        print(f"[Datalys2] Failed to schedule task '{task_name}'.")
        
    return success
