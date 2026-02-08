import sys
import os
import subprocess
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def install_service():
    if not is_admin():
        print("Administrative privileges are required to register the task.")
        return False

    script_path = os.path.abspath(sys.argv[0])
    # The command we want to run on startup. 
    # We assume 'datalys2-server' is installed as a generic console script or we run module directly.
    # To be safe, we use the current python executable running the server.module
    
    python_exe = sys.executable
    # Running the module as a script
    command = f'"{python_exe}" -m datalys2_tasks.server.app'
    
    task_name = "Datalys2Server"
    
    # Create the scheduled task
    # /SC ONLOGON : Run when user logs on (better for interactive tasks on desktop)
    # /TR : The command to run
    # /TN : Task Name
    # /F : Force create (overwrite)
    # /RL HIGHEST : Run with highest privileges (optional, might not be needed for simple server)
    
    schtasks_cmd = [
        "schtasks", "/Create", 
        "/SC", "ONLOGON", 
        "/TN", task_name, 
        "/TR", command, 
        "/F"
    ]

    try:
        subprocess.check_call(schtasks_cmd, shell=True)
        print(f"Successfully registered '{task_name}' to run on logon.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to register task: {e}")
        return False

def remove_service():
    if not is_admin():
        print("Administrative privileges are required to remove the task.")
        return False

    task_name = "Datalys2Server"
    schtasks_cmd = ["schtasks", "/Delete", "/TN", task_name, "/F"]

    try:
        subprocess.check_call(schtasks_cmd, shell=True)
        print(f"Successfully removed '{task_name}'.")
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to remove task (it might not exist).")
        return False
