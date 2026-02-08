# Datalys2 Tasks - System Documentation

Datalys2 Tasks is a lightweight, local task orchestration system designed to run Python scripts in the background, similar to Prefect or Celery, but optimized for single-machine local environments with minimal setup.

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Installation](#installation)
3. [Core Concepts](#core-concepts)
    - [The Client (@task)](#the-client-task)
    - [The Server](#the-server)
    - [The Database](#the-database)
    - [The Worker (Execution Engine)](#the-worker-execution-engine)
4. [Usage Guide](#usage-guide)
    - [Starting the Server](#starting-the-server)
    - [Creating and Submitting Tasks](#creating-and-submitting-tasks)
    - [Monitoring via Dashboard](#monitoring-via-dashboard)
5. [Configuration & Notifications](#configuration--notifications)
6. [Windows Service Integration](#windows-service-integration)
7. [Troubleshooting](#troubleshooting)

---

## High-Level Architecture

The system consists of three main components running on the local machine:

1.  **The API Server**: A FastAPI application that accepts task submissions and serves the dashboard.
2.  **The Background Worker**: A separate thread running alongside the server that polls the database for pending tasks and executes them.
3.  **The Client**: Your Python scripts, equipped with a decorator that can serialize function calls and send them to the server.

**Data Flow:**
1.  User runs `my_script.py`.
2.  The `@task` decorator intercepts the call.
3.  It sends a generic payload (Module Path + Function Name + Arguments) to the Server via HTTP.
4.  Server saves the task as `PENDING` in SQLite.
5.  Worker detects the pending task, loads the Python file dynamically, and executes the function.
6.  Result/Error is saved back to the DB.

---

## Installation

Since this is a Python package, install it in your environment (virtual environment recommended).

```bash
# From the root directory of the project
pip install -e .
```

This installs the `datalys2-server` command and the `datalys2_tasks` python package.

---

## Core Concepts

### The Client (`@task`)

The magic happens in `src/datalys2_tasks/client/decorator.py`.

When you wrap a function with `@task`:
```python
from datalys2_tasks.client.decorator import task

@task
def process_data(x):
    return x * 2
```

- Calling `process_data(5)` runs it **locally** (normal python behavior).
- Calling `process_data.submit(5)` sends it to **the server**.

**How it works:**
The client doesn't send the *code* to the server. It sends a *reference* to the code:
- `module_path`: Full path to the `.py` file (e.g., `C:\Projects\f1.py`).
- `function_name`: The name of the function (e.g., `process_data`).
- `args/kwargs`: The arguments you passed.

*Requirement: The server must have access to the same filesystem as the client.*

### The Server

Located in `src/datalys2_tasks/server`, the server is a standard FastAPI app.
- **Port**: 8000 (default)
- **Endpoints**:
    - `POST /tasks`: Submit a new task.
    - `GET /tasks`: List task history.
    - `GET /tasks/{id}`: Get status of a specific task.

### The Database

We use **SQLite** via **SQLAlchemy**.
- File: `datalys2_tasks.db` (created in the directory where you run the server).
- No setup required; it's automatic.

### The Worker (Execution Engine)

Located in `src/datalys2_tasks/server/worker.py`.

The worker runs in an infinite loop (polling every 2 seconds):
1.  Checks DB for `PENDING` tasks.
2.  If found, marks it as `RUNNING`.
3.  **Dynamic Import**: It uses python's `importlib` to load the python file specified in `task.module_path`.
4.  It retrieves the function object matching `task.function_name`.
5.  It runs the function with `task.args`.
6.  It captures the return value or any Exceptions.
7.  Updates DB with `COMPLETED` or `FAILED`.

---

## Usage Guide

### Starting the Server

You need the server running to accept tasks.

**Option 1: Manual Start (Foreground)**
```powershell
datalys2-server start
```
*Use this for debugging. Keep the terminal open.*

**Option 2: Windows Service (Background)**
```powershell
# Requires Admin Terminal
datalys2-server install
```
*This registers a scheduled task to start the server automatically when you log in.*

### Creating and Submitting Tasks

Create a python file (e.g., `etl_job.py`):

```python
import time
from datalys2_tasks.client.decorator import task

@task
def daily_report(date_str):
    print(f"Generating report for {date_str}...")
    time.sleep(5) # Simulate work
    return f"Report {date_str} generated!"

if __name__ == "__main__":
    # Submit to background system
    task_id = daily_report.submit("2023-10-27")
    print(f"Submitted task {task_id}")
```

Run this script:
```powershell
python etl_job.py
```

### Monitoring via Dashboard

Open your browser to:
**[http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)**

The dashboard auto-refreshes every 5 seconds. You can see:
- Task Status (Pending, Running, Completed, Failed)
- Output Results (JSON serialized return values)
- Error Tracebacks (if it failed)

---

## Configuration & Notifications

The system looks for a `datalys_config.json` file in the execution directory. If not found, it uses defaults.

**To Enable Email Notifications:**
Create `datalys_config.json`:

```json
{
    "notification": {
        "enabled": true,
        "type": "EMAIL",
        "target": "your.email@example.com",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "your.email@example.com",
        "smtp_password": "your_app_password"
    }
}
```

If a task fails, the server references this config to send an alert.

---

## Windows Service Integration

The `datalys2-server install` command uses the Windows `schtasks` command.

- **Task Name**: `Datalys2Server`
- **Trigger**: Runs at user logon (`ONLOGON`).
- **Command**: It points to the specific python executable in your environment.

To remove it:
```powershell
datalys2-server remove
```

---

## Troubleshooting

### "Task ID not returned / Connection Error"
- Is the server running? Check `http://127.0.0.1:8000`.
- If you installed as a service, check Task Scheduler in Windows to see if `Datalys2Server` is running.

### "ModuleNotFoundError" in the Dashboard Error Log
- The Worker tries to import your script.
- **Critical Rule**: The script defining the task **must** be importable.
- Avoid circular imports in your task file.
- Ensure the server process has read permissions to the folder where your script lives.

### "Changes to my code aren't picked up"
- Because the worker is a long-running process, it might cache imported modules.
- **Current Limitation**: If you change the code *inside* the function, you might need to restart the server to clear python's `sys.modules` cache, depending on how `importlib` handles the re-import.
