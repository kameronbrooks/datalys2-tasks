# Datalys2 Tasks

A lightweight, local task orchestration system for Python.

## Installation

1. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

## Usage

### 1. Start the Server

You can start the server manually:
```bash
datalys2-server start
```
Or register it to start automatically on Windows logon:
```bash
datalys2-server install
```

### 2. Create a Task

Define a task in any Python file:

```python
from datalys2_tasks.client.decorator import task

@task
def my_process(data):
    return sorted(data)

if __name__ == "__main__":
    my_process.submit([3, 1, 2])
```

### 3. Check Status

Visit `http://localhost:8000/docs` to see the API Swagger UI.
