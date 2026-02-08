import argparse
import sys
from pathlib import Path
from .server.app import start_server
from .server.startup import install_service, remove_service
from .scheduler.windows import WindowsTaskScheduler

def main():
    parser = argparse.ArgumentParser(description="Datalys2 Tasks Server & Scheduler CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Server Commands ---
    # Start Server
    subparsers.add_parser("start", help="Start the Task Server immediately")

    # Install Service
    subparsers.add_parser("install", help="Register server as a Windows startup task")

    # Remove Service
    subparsers.add_parser("remove", help="Remove the Windows startup task")

    # --- Scheduler Commands ---
    sched_parser = subparsers.add_parser("schedule", help="Manage Windows Scheduled Tasks direct execution mode")
    sched_subs = sched_parser.add_subparsers(dest="sched_command", help="Scheduler actions")

    # Schedule: Create/Add
    add_p = sched_subs.add_parser("add", help="Create a new scheduled task")
    add_p.add_argument("name", help="Unique name for the task")
    add_p.add_argument("script", help="Path to the Python script to execute")
    add_p.add_argument("--schedule", default="DAILY", choices=["DAILY", "HOURLY", "MINUTE", "ONCE", "ONLOGON"], help="Schedule type")
    add_p.add_argument("--time", help="Start time (HH:mm)")
    add_p.add_argument("--interval", type=int, help="Interval (minutes) if schedule is MINUTE or modifier for others")
    add_p.add_argument("--force", action="store_true", help="Overwrite existing task")
    add_p.add_argument("--args", nargs="*", help="Arguments to pass to the script")

    # Schedule: List
    list_p = sched_subs.add_parser("list", help="List scheduled tasks")
    list_p.add_argument("--pattern", default="*", help="Filter tasks by name (substring)")

    # Schedule: Delete
    del_p = sched_subs.add_parser("remove", help="Delete a scheduled task")
    del_p.add_argument("name", help="Name of the task to delete")

    # Schedule: Run (Manual)
    run_p = sched_subs.add_parser("run", help="Manually run a scheduled task now")
    run_p.add_argument("name", help="Name of the task to run")


    args = parser.parse_args()

    if args.command == "start":
        print("Starting Datalys2 Server...")
        start_server()
    elif args.command == "install":
        install_service()
    elif args.command == "remove":
        remove_service()
    elif args.command == "schedule":
        scheduler = WindowsTaskScheduler()
        
        if args.sched_command == "add":
            success = scheduler.create_task(
                task_name=args.name,
                script_path=args.script,
                schedule=args.schedule,
                start_time=args.time,
                interval_minutes=args.interval,
                args=args.args,
                force=args.force
            )
            if success:
                print(f"Task '{args.name}' scheduled successfully.")
            else:
                sys.exit(1)

        elif args.sched_command == "list":
            tasks = scheduler.list_tasks(pattern=args.pattern)
            if not tasks:
                print("No matching tasks found.")
            else:
                print(f"{'Task Name':<40} {'Next Run Time':<25} {'Status':<15}")
                print("-" * 80)
                for t in tasks:
                    name = t.get('TaskName', 'N/A').replace('\\', '') # Cleanup backslashes often returned by schtasks
                    next_run = t.get('Next Run Time', 'N/A')
                    status = t.get('Status', 'N/A')
                    print(f"{name:<40} {next_run:<25} {status:<15}")

        elif args.sched_command == "remove":
            if scheduler.delete_task(args.name):
                print(f"Task '{args.name}' deleted.")
            else:
                sys.exit(1)

        elif args.sched_command == "run":
            if scheduler.run_task(args.name):
                print(f"Task '{args.name}' triggered.")
            else:
                sys.exit(1)
        else:
            sched_parser.print_help()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
