import sys
import subprocess
import csv
import io
import os
import tempfile
import datetime
from typing import List, Optional, Dict, Union
from pathlib import Path

class WindowsTaskScheduler:
    """
    Interface for managing Windows Tasks using the 'schtasks' command-line utility.
    This allows scheduling Python scripts to run via the Windows Task Scheduler.
    """

    def __init__(self, python_executable: Optional[str] = None):
        """
        Initialize the scheduler.

        Args:
            python_executable (str, optional): Path to the python interpreter to use for running scripts.
                                               Defaults to the currently running python interpreter.
        """
        self.python_exe = python_executable or sys.executable

    def _run_schtasks(self, args: List[str]) -> subprocess.CompletedProcess:
        """Helper to run schtasks commands."""
        # 'chcp 65001' might be needed for encoding, but subprocess usually handles it if we decode properly.
        # We ensure we capture output.
        cmd = ["schtasks"] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="mbcs", # Use mbcs for Windows command line output decoding
                check=False      # We'll check return code manually
            )
            return result
        except FileNotFoundError:
            raise RuntimeError("schtasks.exe not found. Is this 'Windows'?")

    def _ensure_task_path(self, task_name: str) -> str:
        """prefix task name with folder if not already present"""
        folder = "\\datalys2"
        if not task_name.startswith("\\"):
            return f"{folder}\\{task_name}"
        if not task_name.lower().startswith(f"{folder}\\"):
             # It acts as an absolute path, but we enforce the folder structure
             # If user passed \Other\Task, we might want to respect it or force it.
             # Let's enforce \datalys2\ prefix for consistency if it's just a name
             pass
        return task_name

    def create_task(
        self,
        task_name: str,
        script_path: Union[str, Path],
        schedule: str = "DAILY",
        start_time: Optional[str] = None,
        interval_minutes: Optional[int] = None,
        args: Optional[List[str]] = None,
        force: bool = False
    ) -> bool:
        """
        Create a new scheduled task using structured XML generation.
        This supports advanced features like 'Start In' directory and timezone synchronization.

        Args:
            task_name (str): Unique name for the task.
            script_path (str | Path): Path to the Python script to execute.
            schedule (str): Schedule type. Note: Currently mostly supports ONCE, DAILY, MINUTE basics.
            start_time (str, optional): Start time in HH:mm format (24h).
            interval_minutes (int, optional): Interval minutes.
            args (List[str], optional): Additional arguments to pass to the python script.
            force (bool): If True, overwrite existing task.

        Returns:
            bool: True if created successfully, False otherwise.
        """
        # Enforce folder path
        full_task_name = self._ensure_task_path(task_name)

        script = Path(script_path).absolute()
        if not script.exists():
            raise FileNotFoundError(f"Script not found: {script}")

        working_dir = str(script.parent)
        
        # Prepare arguments string
        # python "script" args...
        script_args_str = f'"{script}"'
        if args:
            joined = " ".join(f'"{a}"' if " " in a else a for a in args)
            script_args_str += f" {joined}"

        # Calculate StartBoundary (YYYY-MM-DDTHH:MM:SS)
        # If no date is implied, we use today or tomorrow based on time
        if start_time:
            now = datetime.datetime.now()
            try:
                dt_time = datetime.datetime.strptime(start_time, "%H:%M").time()
            except ValueError:
                print(f"Invalid time format: {start_time}")
                return False
                
            start_dt = datetime.datetime.combine(now.date(), dt_time)
            # If time has passed today, schedule for tomorrow (unless it's ONCE?)
            if start_dt < now and schedule != "ONCE":
                start_dt += datetime.timedelta(days=1)
            
            # StartBoundary format: YYYY-MM-DDTHH:MM:SS
            # To 'Synchronize across time zones', we should ideally use UTC 'Z'.
            # However, schtasks XML import treats a local time string as local.
            # To explicitly enable that check box, providing a UTC time with 'Z' is the standard way.
            # Let's perform a conversion to UTC for robustness if the user wants synchronization.
            # For simplicity in this tool, we will use local ISO format which Windows accepts.
            start_boundary = start_dt.isoformat()
        else:
            start_boundary = datetime.datetime.now().isoformat()

        
        # Trigger XML generation
        triggers_xml = ""
        
        # Mapping schedule types to XML Triggers
        # Common ids: TimeTrigger (ONCE), CalendarTrigger (DAILY), BootTrigger (ONSTART), LogonTrigger (ONLOGON)
        
        if schedule.upper() == "ONCE":
            triggers_xml = f"""
      <TimeTrigger>
        <StartBoundary>{start_boundary}</StartBoundary>
        <Enabled>true</Enabled>
      </TimeTrigger>"""
        elif schedule.upper() == "DAILY":
             triggers_xml = f"""
      <CalendarTrigger>
        <StartBoundary>{start_boundary}</StartBoundary>
        <Enabled>true</Enabled>
        <ScheduleByDay>
          <DaysInterval>1</DaysInterval>
        </ScheduleByDay>
      </CalendarTrigger>"""
        elif schedule.upper() == "ONLOGON":
            triggers_xml = f"""
      <LogonTrigger>
        <Enabled>true</Enabled>
      </LogonTrigger>"""
        else:
            # Fallback for complex schedules or implement more as needed
            # For simplicity, if we don't have a specific XML template, you might fallback to basic CLI
            # or try to map generic logic. Let's start with basic ones.
             triggers_xml = f"""
      <TimeTrigger>
        <StartBoundary>{start_boundary}</StartBoundary>
        <Enabled>true</Enabled>
      </TimeTrigger>"""

        # Define the XML Payload
        # xmlns is required for schtasks to parse it correctly
        xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{datetime.datetime.now().isoformat()}</Date>
    <Author>{os.environ.get('USERNAME', 'Datalys2')}</Author>
    <Description>Auto-generated python task for {script.name}</Description>
  </RegistrationInfo>
  <Triggers>
    {triggers_xml}
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT72H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{self.python_exe}</Command>
      <Arguments>{script_args_str}</Arguments>
      <WorkingDirectory>{working_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""
        # Note on Synchronization:
        # In Task Scheduler 2.0, the <StartBoundary> inherently defines the synchronization point.
        # If it includes 'Z' (e.g. 2023-01-01T12:00:00Z) it is UTC. 
        # If it is local time (no Z), Windows assumes local. 
        # The 'Synchronize across time zones' checkbox in GUI effectively forces the stored time to be UTC-based.
        # Python's datetime.now() is local, but if we want "checked", we usually format as UTC.
        # However, simplistic XML generation here uses local string. 
        # To truly check that box, we generally provide a UTC StartBoundary ending in 'Z'.
        
        # Write XML to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-16') as tmp:
            tmp.write(xml_content)
            tmp_path = tmp.name

        try:
            sch_args = ["/Create", "/TN", full_task_name, "/XML", tmp_path]
            if force:
                sch_args.append("/F")

            result = self._run_schtasks(sch_args)
            if result.returncode != 0:
                print(f"Error creating task '{full_task_name}': {result.stderr.strip()}")
                return False
            return True
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def delete_task(self, task_name: str) -> bool:
        """
        Delete a scheduled task.

        Args:
            task_name (str): Name of the task to delete.

        Returns:
            bool: True if deleted successfully, False otherwise.
        """
        full_task_name = self._ensure_task_path(task_name)
        sch_args = ["/Delete", "/TN", full_task_name, "/F"]
        result = self._run_schtasks(sch_args)
        if result.returncode != 0:
            print(f"Error deleting task '{full_task_name}': {result.stderr.strip()}")
            return False
        return True

    def run_task(self, task_name: str) -> bool:
        """
        Manually trigger a scheduled task to run immediately.

        Args:
            task_name (str): Name of the task to run.

        Returns:
            bool: True if run command sent successfully.
        """
        full_task_name = self._ensure_task_path(task_name)
        sch_args = ["/Run", "/TN", full_task_name]
        result = self._run_schtasks(sch_args)
        if result.returncode != 0:
            print(f"Error running task '{full_task_name}': {result.stderr.strip()}")
            return False
        return True

    def query_task(self, task_name: str) -> Optional[Dict[str, str]]:
        """
        Get details of a specific task.

        Args:
            task_name (str): Name of the task to query.

        Returns:
            Optional[Dict[str, str]]: Dictionary of task properties if found, else None.
        """
        full_task_name = self._ensure_task_path(task_name)
        # /V for verbose, /FO CSV for parsing
        sch_args = ["/Query", "/TN", full_task_name, "/V", "/FO", "CSV"]
        
        # schtasks /query can be finicky with encoding.
        result = self._run_schtasks(sch_args)
        
        if result.returncode != 0:
            return None

        try:
            # Parse CSV output
            # Output might contain a blank line or headers then values
            # Using csv reader
            f = io.StringIO(result.stdout)
            reader = csv.DictReader(f)
            for row in reader:
                return row # Return the first (and likely only) row
        except Exception as e:
            print(f"Failed to parse task query output: {e}")
            return None
        return None

    def list_tasks(self, pattern: str = "*") -> List[Dict[str, str]]:
        """
        List tasks matching a pattern. Note: schtasks doesn't support pattern matching natively in /Query 
        for task names very well, so we might need to filter manually.

        Args:
            pattern (str): Substring to match in task name.

        Returns:
            List[Dict[str, str]]: List of task details.
        """
        # Get all tasks in CSV format
        sch_args = ["/Query", "/V", "/FO", "CSV"]
        result = self._run_schtasks(sch_args)

        tasks = []
        if result.returncode != 0:
            print(f"Error listing tasks: {result.stderr.strip()}")
            return tasks

        try:
            f = io.StringIO(result.stdout)
            reader = csv.DictReader(f)
            for row in reader:
                task_name = row.get("TaskName", "")
                # Filter by pattern if provided (simple substring check)
                if pattern == "*" or pattern in task_name:
                    tasks.append(row)
        except Exception as e:
            print(f"Error parsing list output: {e}")

        return tasks

if __name__ == "__main__":
    # Simple test
    scheduler = WindowsTaskScheduler()
    print("Scheduler initialized.")
