import functools
import inspect
import os
import sys
from typing import Optional, List, Union, Callable
from ..core.config import settings
from ..scheduler.windows import WindowsTaskScheduler
from ..server.database import SessionLocal, ScheduledTaskDB, init_db

class TaskWrapper:
    def __init__(self, func, task_name: Optional[str] = None):
        self.func = func
        self.default_task_name = task_name or func.__name__
        functools.update_wrapper(self, func)
        
        # Determine the absolute path of the module defining the function
        module = inspect.getmodule(func)
        
        # Safely get __file__, defaulting to None if it doesn't exist
        module_file = getattr(module, '__file__', None) if module else None
        
        if module_file:
            self.module_path = os.path.abspath(module_file)
        else:
            # Fallback (might fail in interactive shells)
            self.module_path = os.path.abspath(sys.argv[0])

    def __call__(self, *args, **kwargs):
        """Allow normal local execution."""
        return self.func(*args, **kwargs)

    def schedule_run(
        self, 
        task_name: Optional[str] = None, 
        schedule: str = "DAILY", 
        start_time: Optional[str] = None, 
        interval: Optional[int] = None,
        force: bool = False,
        cli_args: Optional[List[str]] = None
    ) -> bool:
        """
        Register this function's script as a Windows Scheduled Task.
        
        Args:
            task_name (str, optional): Unique identifier for the Windows Task Scheduler. 
                                       Defaults to the name provided in @task decorator or function name.
            schedule (str): Frequency ('DAILY', 'HOURLY', 'minute', 'ONCE', 'ONLOGON').
            start_time (str): Time to start (HH:mm).
            interval (int): Interval in minutes (if applicable).
            force (bool): Overwrite existing task.
            cli_args (List[str]): Command line arguments to pass to the script execution.

        Returns:
            bool: Success status.
        """
        final_task_name = task_name or self.default_task_name
        
        scheduler = WindowsTaskScheduler()
        print(f"Scheduling script: {self.module_path} as '{final_task_name}'")
        success = scheduler.create_task(
            task_name=final_task_name,
            script_path=self.module_path,
            schedule=schedule,
            start_time=start_time,
            interval_minutes=interval,
            args=cli_args,
            force=force
        )

        if success:
            # Save to SQLite DB in %APPDATA%
            try:
                # Ensure DB tables exist (idempotent)
                init_db()
                
                db = SessionLocal()
                # Check if exists to update or create
                existing = db.query(ScheduledTaskDB).filter(ScheduledTaskDB.task_name == final_task_name).first()
                if existing:
                    existing.script_path = self.module_path
                    existing.schedule_type = schedule
                    existing.schedule_time = start_time
                    existing.interval_minutes = interval
                    existing.description = f"Scheduled via decorator from {self.func.__name__}"
                else:
                    new_task = ScheduledTaskDB(
                        task_name=final_task_name,
                        script_path=self.module_path,
                        schedule_type=schedule,
                        schedule_time=start_time,
                        interval_minutes=interval,
                        description=f"Scheduled via decorator from {self.func.__name__}"
                    )
                    db.add(new_task)
                
                db.commit()
                db.close()
                print("Task registration saved to local database.")
            except Exception as e:
                print(f"Warning: Failed to save task to local database: {e}")

        return success

def task(func: Union[Callable, None] = None, *, name: Optional[str] = None):
    """
    Decorator to wrap a function as a Datalys2 task.
    Usage:
        @task
        def my_func(): ...
        
        @task(name="MyCustomTask")
        def my_func(): ...
    """
    if func is None:
        return functools.partial(task, name=name)
    return TaskWrapper(func, task_name=name)
