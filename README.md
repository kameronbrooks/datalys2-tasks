# Datalys2 Tasks

**A lightweight, local task orchestration system built for Windows.**

`dl2-tasks` (Datalys2 Tasks) is a robust wrapper around the native **Windows Task Scheduler**. It provides a modern Python interface for scheduling, managing, and monitoring background tasks without the need for a heavy, always-on server process.

## 🌟 Features

- **No Background Process Required:** Leverages Windows' built-in `schtasks.exe`.
- **Self-Scheduling Scripts:** Add `schedule_me()` to your script, run it once, and it's scheduled forever.
- **Lightweight:** Minimal dependencies.
- **Robust:** If Python crashes, the scheduler remains.

## 📦 Installation

```bash
pip install dl2-tasks
```

## 🚀 Quick Start

### Auto-Scheduling (The "Magic" Way)

The easiest way to use Datalys2 Tasks is to let your scripts schedule themselves.

1.  Create `my_task.py`:

    ```python
    import datetime
    from datalys2_tasks.scheduler.autorun import schedule_me
    
    def job():
        with open("log.txt", "a") as f:
            f.write(f"Ran at {datetime.datetime.now()}\n")
    
    if __name__ == "__main__":
        # Registers this script to run everyday at 08:00
        schedule_me("MyDailyLog", frequency="DAILY", at="08:00")
        
        job()
    ```

2.  Run it once manually:
    ```bash
    python my_task.py
    ```

3.  That's it! Windows will now run this script every day at 08:00.

### CLI Management

You can also manage tasks via the command line.

- **List tasks:** `datalys2-server schedule list`
- **Add a task:** `datalys2-server schedule add "Backup" "C:\scripts\backup.py" --schedule DAILY --time 02:00`
- **Run manually:** `datalys2-server schedule run "Backup"`

## 🖥️ Optional Dashboard

Includes a local dashboard for viewing task status.

```bash
datalys2-server start
```
*Opens http://localhost:8000/dashboard*

---

For full details, see the documentation.
