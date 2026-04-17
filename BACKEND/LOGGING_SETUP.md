# Project Nexus Logger Configuration Guide

## Overview

The Project Nexus backend now uses **Python JSON Logger** (equivalent to Winston) to provide structured, JSON-formatted logging with automatic tracking of file, function, and line information.

## Features

✅ **JSON Format**: All logs are output in JSON format for easy parsing and analysis  
✅ **File & Function Tracking**: Automatically captures the filename, function name, and line number  
✅ **Dual Output**: Logs to both console and file simultaneously  
✅ **Contextual Data**: Support for arbitrary key-value pairs to add business context  
✅ **Timestamps**: ISO 8601 formatted timestamps on all logs  
✅ **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL  

## Configuration

### Environment Variables

Set these environment variables to customize logging behavior:

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export NEXUS_LOG_LEVEL=INFO

# Set log directory (creates logs/ directory by default)
export NEXUS_LOG_DIR=logs
```

### Log Output

- **Console**: Logs are printed to stdout in JSON format
- **File**: Logs are written to `logs/nexus.log` (or custom directory via `NEXUS_LOG_DIR`)

## Usage Examples

### Example 1: Basic Logging

```python
from core.logger import get_logger

logger = get_logger(__name__)

# Info level
logger.info("Application started")

# With context data
logger.info("Processing skill", extra={"skill_id": "context-builder", "duration_ms": 1234})

# Warning
logger.warning("API rate limit approaching", extra={"remaining_requests": 5})

# Error with stack trace
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", extra={"operation": "risky_operation"}, exc_info=True)
```

### Example 2: API Request Logging (as implemented)

```python
def do_POST(self) -> None:
    logger.info("POST request received", extra={"path": self.path})
    try:
        result = self._service().run(request)
        logger.info("Request successful", extra={"status": "ok", "duration_ms": elapsed})
    except Exception as exc:
        logger.error("Request failed", extra={"error": str(exc)}, exc_info=True)
```

## Log Output Example

### Console/File Output

```json
{"timestamp": "2026-04-17T14:23:45.123Z", "level": "INFO", "name": "nexus", "filename": "server.py", "funcName": "do_POST", "lineno": 65, "message": "Skill execution completed", "confidence": 0.95, "mode": "new"}
{"timestamp": "2026-04-17T14:23:46.456Z", "level": "ERROR", "name": "nexus", "filename": "service.py", "funcName": "run", "lineno": 30, "message": "Error during skill execution", "error": "Path resolution failed", "skill_key": "context-builder"}
```

## Initialization

### Option 1: Automatic (Recommended)

The logger is automatically initialized in `main.py` when running the application:

```bash
python main.py serve-api
# Logs initialize automatically with INFO level to logs/nexus.log
```

### Option 2: Manual Initialization

```python
from core.logger import init_logging

# Initialize with custom settings
init_logging(log_level="DEBUG", log_dir="custom_logs_dir")
```

### Option 3: Direct Logger Creation

```python
from core.logger import setup_logger
from pathlib import Path

# Create a custom logger for a specific module
logger = setup_logger(
    name="my_module",
    log_level="DEBUG",
    log_file=Path("logs/my_module.log"),
    console_output=True
)
```

## Viewing Logs

### Real-time Console View

```bash
python main.py serve-api
# Logs appear in console as JSON lines
```

### Parse Log File with jq

```bash
# Pretty print JSON logs
cat logs/nexus.log | jq '.'

# Filter by level
cat logs/nexus.log | jq 'select(.level == "ERROR")'

# Filter by function
cat logs/nexus.log | jq 'select(.funcName == "do_POST")'

# Extract specific fields
cat logs/nexus.log | jq '{timestamp, level, message, error}'
```

### Follow Log File in Real-time (Unix/Mac)

```bash
tail -f logs/nexus.log | jq '.'
```

### Follow Log File in Real-time (PowerShell)

```powershell
Get-Content logs/nexus.log -Wait | ConvertFrom-Json | Format-Table
```

## Files Modified

The following files have been updated with logging:

- ✅ `main.py` - Initialization and mode-specific logging
- ✅ `src/api/server.py` - HTTP request and response logging
- ✅ `src/api/service.py` - Business logic execution logging
- ✅ `core/logger.py` - New logging configuration module

## Adding Logging to New Modules

To add structured logging to any Python module in the backend:

```python
# At the top of your file
from core.logger import get_logger

logger = get_logger(__name__)

# In your functions
logger.info("Operation completed", extra={"items_processed": 42})
logger.error("Something went wrong", exc_info=True)
```

## Performance Considerations

- JSON logging adds minimal overhead (~1-2ms per log statement)
- Logs are buffered in memory before writing to disk
- Consider using `log_level=WARNING` in production for high-traffic scenarios

## Troubleshooting

### Logs not appearing?

1. Check that `logs/` directory exists and is writable
2. Verify `NEXUS_LOG_LEVEL` environment variable is set correctly
3. Ensure `init_logging()` is called before creating loggers

### Cannot import logger?

```bash
# Install the required package
pip install python-json-logger
```

### JSON parsing errors?

Make sure to use the `jq` tool for parsing:

```bash
cat logs/nexus.log | python -m json.tool  # Alternative to jq
```

## Integration with Monitoring Tools

The JSON format makes it easy to integrate with:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk** - Direct JSON ingestion
- **DataDog** - JSON schema support
- **CloudWatch** - AWS log insights
- **Google Cloud Logging** - Structured logs

Simply pipe the log file to these services for advanced analysis and alerting.
