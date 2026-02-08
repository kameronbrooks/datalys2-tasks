# Datalys2 Tasks

**A lightweight, local task orchestration system built for Windows.**

Datalys2 Tasks is a robust wrapper around the native **Windows Task Scheduler**. It provides a modern Python interface for scheduling, managing, and monitoring background tasks without the need for a heavy, always-on server process consuming resources.

## Philosophy

Existing solutions like Prefect, Airflow, or Celery are powerful but often too heavy for local development or single-machine deployments. They typically require:
- A dedicated server process running 24/7.
- A database backend (Postgres, Redis, etc.).
- Complex configuration.

**Datalys2 Tasks is different:**
- **No Background Process Required:** It uses Windows' built-in Task Scheduler (`schtasks.exe`) as the execution engine. If your computer is on, your tasks will run.
- **Self-Scheduling Scripts:** You can write a Python script that schedules *itself* simply by running it once.
- **Lightweight:** Minimal dependencies. Perfect for local automation, data pipelines, and maintenance scripts.
- **Robust:** Relies on the OS's proven scheduling capabilities. If Python crashes, the scheduler remains.

---

## Installation

```bash
pip install dl2-tasks
```
*(Assuming package availability or local install)*

---

## 🚀 Quick Start: Self-Scheduling Scripts

The most powerful feature of Datalys2 Tasks is the **Auto-Scheduler**. You can add a simple block of code to the top of any Python script to handle its own scheduling.

### Example: `my_daily_task.py`

```python
import datetime
from datalys2_tasks.scheduler.autorun import schedule_me

def main():
    print("Doing important work...")
    print(f"Finished at {datetime.datetime.now()}")

if __name__ == "__main__":
    # ---------------------------------------------------------
    # SELF-SCHEDULING BLOCK
    # ---------------------------------------------------------
    # When this script is run, it checks if "MyDailyReport" is 
    # already in the Windows Task Scheduler.
    # If not, it registers itself to run DAILY at 08:30.
    # ---------------------------------------------------------
    schedule_me(
        name="MyDailyReport",
        frequency="DAILY",
        at="08:30"
    )

    # Run the actual logic
    main()
```

1. **Run it once manually:**
   ```bash
   python my_daily_task.py
   ```
   *Output:*
   ```text
   ✨ [Datalys2] Registering 'MyDailyReport' to run DAILY...
      🕒 Time: 08:30
   Doing important work...
   ```
2. **Forget it:** Windows will now automatically run this script every day at 8:30 AM.

---

## CLI Usage

Datalys2 Tasks includes a CLI to manage your scheduled tasks easily.

### 1. List All Tasks
See what's currently scheduled (filters for tasks created by Datalys2).

```bash
datalys2-server schedule list
```

### 2. Manually Add a Task
If you prefer not to modify your scripts, you can schedule them from the command line.

```bash
datalys2-server schedule add \
    "WeeklyBackup" \
    "C:\Scripts\backup.py" \
    --schedule DAILY \
    --time 02:00
```

### 3. Run a Task Immediately
Test a scheduled task without waiting for its time.

```bash
datalys2-server schedule run "WeeklyBackup"
```

### 4. Remove a Task

```bash
datalys2-server schedule remove "WeeklyBackup"
```

---

## The Optional Server (Dashboard)

While the core functionality works entirely without a running server, Datalys2 Tasks includes an optional web dashboard for better visibility.

To start the dashboard:

```bash
datalys2-server start
```
*Visits http://localhost:8000/dashboard*

This provides a UI to view task status and history, but remember: **The server does NOT need to be running for your tasks to execute.** Windows handles the execution.

---

## Architecture

| Component | Description |
| :--- | :--- |
| **`schedule_me(...)`** | Python function that calls `schtasks.exe /Create` to register the script. |
| **Windows Task Scheduler** | The engine that wakes up and executes the python command at the right time. |
| **Datalys2 CLI** | Wrapper for `schtasks` to make management easy. |
