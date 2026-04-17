# Project Nexus Logger - Quick Reference

## Basic Log Entry Structure

All logs are output in JSON format with the following fields:

```json
{
  "timestamp": "2026-04-17T16:45:21.953582+00:00",
  "level": "INFO",
  "logger_name": "nexus.init",
  "file": "logger.py",
  "function": "init_logging",
  "line": 151,
  "message": "Logging system initialized",
  "log_dir": "logs/nexus.log",
  "log_level": "DEBUG"
}
```

### Key Fields

| Field | Description | Example |
|-------|-------------|---------|
| `timestamp` | ISO 8601 formatted timestamp | `2026-04-17T16:45:21.953582+00:00` |
| `level` | Log level | `INFO`, `WARNING`, `ERROR`, `DEBUG` |
| `logger_name` | Logger identifier | `nexus.init`, `backend.service` |
| `file` | Source filename | `logger.py`, `server.py` |
| `function` | Function name | `init_logging`, `do_POST` |
| `line` | Line number | `151`, `65` |
| `message` | Log message | User-provided message |
| Custom fields | Any extra context | `request_id`, `duration_ms`, etc |

## Installation

The logger is already installed. To verify:

```bash
pip install python-json-logger -q
```

## Usage in Your Code

### Step 1: Import

```python
from core.logger import get_logger

logger = get_logger(__name__)
```

### Step 2: Add Logging Statements

```python
# Simple log
logger.info("Action completed")

# With context
logger.info("Skill executed", extra={
    "skill_key": "context-builder",
    "duration_ms": 2345,
    "status": "success"
})

# Error with stack trace
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", extra={"operation": "risky_operation"}, exc_info=True)
```

### Step 3: Initialize (if not already in main)

```python
from core.logger import init_logging

init_logging(log_level="INFO", log_dir="logs")
```

## Viewing Logs

### View Real-time Console Output

When you run the server, logs appear in JSON format:

```bash
python main.py serve-api
```

### View Log File

```powershell
type logs\nexus.log | ConvertFrom-Json | Select-Object timestamp, level, message, file, function, line | Format-Table
```

### Parse with jq (if installed)

```bash
cat logs/nexus.log | jq '.[] | {timestamp, level, message, file, function, line}'
```

### Filter Logs by Level

```bash
# PowerShell
cat logs\nexus.log | ConvertFrom-Json | Where-Object {$_.level -eq "ERROR"}

# Unix/jq
cat logs/nexus.log | jq 'select(.level == "ERROR")'
```

### Filter Logs by Module

```bash
# PowerShell - find all errors in server.py
cat logs\nexus.log | ConvertFrom-Json | Where-Object {$_.file -eq "server.py" -and $_.level -eq "ERROR"}

# Unix/jq
cat logs/nexus.log | jq 'select(.file == "server.py" and .level == "ERROR")'
```

## Real-world Examples

### API Server Error Tracking

```python
# In src/api/server.py
logger.info("POST request received", extra={"path": self.path})
try:
    response = self._service().run(request)
    logger.info("Request successful", extra={
        "endpoint": self.path,
        "method": "POST",
        "response_time_ms": elapsed
    })
except Exception as exc:
    logger.error("API request failed", extra={
        "endpoint": self.path,
        "error": str(exc),
        "status": "failed"
    }, exc_info=True)
```

### Business Logic Tracking

```python
# In skill execution
logger.info("Executing skill", extra={
    "skill_key": skill.key,
    "prompt_length": len(prompt),
    "mode": "new"
})

try:
    result = execute_skill(skill, prompt)
    logger.info("Skill completed", extra={
        "skill_key": skill.key,
        "output_length": len(result),
        "artifacts": len(result.artifacts),
        "status": "success"
    })
except Exception as e:
    logger.error("Skill execution failed", extra={
        "skill_key": skill.key,
        "issue": str(e)
    }, exc_info=True)
    raise
```

## Environment Configuration

### Set Log Level from Environment

```bash
# PowerShell
$env:NEXUS_LOG_LEVEL = "DEBUG"
python main.py serve-api

# Or via command
NEXUS_LOG_LEVEL=DEBUG python main.py serve-api
```

### Set Log Directory

```bash
NEXUS_LOG_DIR=custom_logs python main.py serve-api
```

## Log File Rotation

To implement log rotation (optional upgrade):

```python
from logging.handlers import RotatingFileHandler

# In core/logger.py, replace FileHandler with:
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10485760,  # 10MB
    backupCount=5,
    encoding="utf-8"
)
```

## Troubleshooting

### Logs not appearing?

1. **Check initialization**: Ensure `init_logging()` is called
2. **Check permissions**: Verify `logs/` directory is writable
3. **Check log level**: If level is set to WARNING, INFO won't show

### How to find an error?

```bash
# Find the exact time of the error
cat logs\nexus.log | ConvertFrom-Json | Where-Object {$_.level -eq "ERROR"} | Select-Object timestamp, file, function, line, message

# Then view context around that time
cat logs\nexus.log | ConvertFrom-Json | Where-Object {$_.timestamp -like "2026-04-17T16:45:*"}
```

### Performance degradation?

If logging is slow:
- Set `log_level=WARNING` to reduce I/O
- Implement log rotation (see above)
- Use asynchronous handlers for high-throughput scenarios

## Integration Points

Logger is currently integrated in:

✅ `main.py` - Application startup and mode execution
✅ `src/api/server.py` - HTTP request/response handling  
✅ `src/api/service.py` - Skill execution service

## Next: Add Logging to More Modules

To extend logging to other modules:

```python
# At the top of any Python file
from core.logger import get_logger
logger = get_logger(__name__)

# Start using it
logger.info("Something happened", extra={"context": "value"})
```

No other changes needed - the logger will automatically use the same configuration and output to the same log file!
