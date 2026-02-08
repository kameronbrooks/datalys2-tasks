import sys
import os
import logging
from typing import Optional, List
from .windows import WindowsTaskScheduler

# Use a logger instead of print where appropriate, but fallback to print for visibility in CLI usage
logger = logging.getLogger("datalys2.autorun")

def schedule_me(
    name: str,
    frequency: str = "DAILY",
    at: Optional[str] = None,
    interval: Optional[int] = None,
    args: Optional[List[str]] = None,
    overwrite: bool = False
) -> bool:
    """
    Automatically schedules the current script as a Windows Task.
    
    This function is designed to be the "one-line" setup for your periodic tasks.
    It checks if the task is already scheduled (by name). If not, it creates it.
    If it is, it does nothing (unless `overwrite=True`).

    It is best placed at the very top of your main execution block.

    Example:
        >>> if __name__ == "__main__":
        ...     from datalys2_tasks.scheduler import autorun
        ...     # Run this script every day at 08:30 AM
        ...     autorun.schedule_me("daily-report-job", at="08:30")
        ...     # ... Rest of your script logic

    Args:
        name (str): 
            A unique name for this task. It will be stored in the Windows Task Scheduler
            under the '\\datalys2\\' folder. 
            Example: "sales-report-generator"

        frequency (str, optional): 
            How often the task should run. 
            Options:
            - "DAILY": Runs once every day (default).
            - "ONCE": Runs a single time (useful for deferred tasks).
            - "ONLOGON": Runs when the user logs in.
            - "MINUTE": Runs every `interval` minutes.
            - "HOURLY": Runs every hour.
            Defaults to "DAILY".

        at (str, optional): 
            The start time for the schedule in "HH:MM" 24-hour format.
            Required for "DAILY" and "ONCE" if you want a specific time.
            If None, defaults to current time.
            Example: "14:00" for 2:00 PM.

        interval (int, optional): 
            Used when frequency is "MINUTE". Specifies the number of minutes between runs.
            Example: 15 (run every 15 minutes).

        args (List[str], optional): 
            A list of command-line arguments to pass to the script when the scheduler runs it.
            Example: ["--mode", "production", "--verbose"]

        overwrite (bool, optional): 
            If True, forces the task to be updated in the Windows Task Scheduler even if it
            already exists. Use this if you've changed the schedule or arguments. 
            Defaults to False (safe mode).

    Returns:
        bool: True if the task is successfully scheduled (or was already there). 
              False if something went wrong during scheduling.
    """
    
    # 1. Normalize inputs
    frequency = frequency.upper()
    
    # 2. Initialize Scheduler Interface
    scheduler = WindowsTaskScheduler()
    
    # 3. Check for existing task
    # The scheduler handles the folder prefix (e.g. \\datalys2\\) internal to query_task
    print(f"✨ [Datalys2] Checking status for task: '{name}'")
    existing_task = scheduler.query_task(name)
    
    if existing_task and not overwrite:
        print(f"✅ [Datalys2] Task '{name}' is already scheduled. Continuing execution...")
        return True
        
    # 4. Prepare Context
    # We need the absolute path to this script so the scheduler knows what to run.
    # Note: This relies on sys.argv[0] being the script path.
    script_path = os.path.abspath(sys.argv[0])
    
    action_verb = "Updating" if existing_task else "Registering"
    print(f"⚙️  [Datalys2] {action_verb} '{name}' to run {frequency}...")
    if at:
        print(f"   🕒 Time: {at}")
    if interval:
        print(f"   ⏱️ Interval: {interval} minutes")
    
    # 5. Execute Creation/Update
    success = scheduler.create_task(
        task_name=name,
        script_path=script_path,
        schedule=frequency,
        start_time=at,
        interval_minutes=interval,
        args=args,
        force=True # We force here because we've already decided to update/create
    )
    
    if success:
        print(f"🚀 [Datalys2] Success! '{name}' is scheduled.")
    else:
        print(f"❌ [Datalys2] Failed to schedule '{name}'. Check permissions or logs.")
        
    return success

# Alias for backward compatibility
def ensure_task(
    task_name: str,
    schedule: str = "DAILY",
    start_time: Optional[str] = None,
    interval_minutes: Optional[int] = None,
    script_args: Optional[List[str]] = None,
    force_update: bool = False
) -> bool:
    """
    Deprecated alias for `schedule_me`.
    Please use `datalys2_tasks.scheduler.autorun.schedule_me` instead.
    """
    return schedule_me(
        name=task_name,
        frequency=schedule,
        at=start_time,
        interval=interval_minutes,
        args=script_args,
        overwrite=force_update
    )
