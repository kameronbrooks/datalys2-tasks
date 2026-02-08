from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..scheduler.windows import WindowsTaskScheduler
from ..server.database import get_db, ScheduledTaskDB
import urllib.parse

router = APIRouter(prefix="/api/scheduled-tasks", tags=["scheduler"])
scheduler = WindowsTaskScheduler()

@router.get("/", response_model=List[Dict[str, Any]])
def list_scheduled_tasks():
    """List all Datalys2 scheduled tasks from Windows Task Scheduler."""
    # We filter for tasks in our folder
    raw_tasks = scheduler.list_tasks(pattern="\\datalys2\\")
    
    # Process tasks to return cleaner JSON
    processed_tasks = []
    for t in raw_tasks:
        # TaskName usually comes back like "\datalys2\MyTask"
        full_name = t.get("TaskName", "")
        # Strip the prefix for display if desired, but keeping full path is safer for uniqueness
        short_name = full_name.split("\\")[-1]
        
        processed_tasks.append({
            "name": full_name,
            "short_name": short_name,
            "status": t.get("Status", "Unknown"),
            "next_run_time": t.get("Next Run Time", "N/A"),
            "last_run_time": t.get("Last Run Time", "N/A"),
            "last_result": t.get("Last Result", "N/A"),
            "author": t.get("Author", "N/A"),
            "schedule": t.get("Schedule Type", "Unknown") # Might vary based on locale/columns
        })
    return processed_tasks

@router.post("/{task_name}/run")
def run_scheduled_task(task_name: str):
    """Manually trigger a scheduled task."""
    # Decode task_name just in case it contains slashes passed as %2F
    decoded_name = urllib.parse.unquote(task_name)
    success = scheduler.run_task(decoded_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to trigger task")
    return {"message": f"Task '{decoded_name}' triggered successfully"}

@router.delete("/{task_name}")
def delete_scheduled_task(task_name: str):
    """Delete a scheduled task."""
    decoded_name = urllib.parse.unquote(task_name)
    success = scheduler.delete_task(decoded_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete task")
    return {"message": f"Task '{decoded_name}' deleted successfully"}
