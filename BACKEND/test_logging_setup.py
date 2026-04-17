#!/usr/bin/env python3
"""
Quick setup and test script for Project Nexus logging system.
This script verifies the logging configuration is working correctly.
"""

import json
import sys
from pathlib import Path

def test_logging_setup():
    """Test the logging configuration."""
    print("🔍 Project Nexus Logger Setup Test\n")
    
    # Check if python-json-logger is installed
    print("1. Checking dependencies...")
    try:
        import pythonjsonlogger
        print("   ✅ python-json-logger is installed")
    except ImportError:
        print("   ❌ python-json-logger not found")
        print("   Run: pip install python-json-logger")
        return False
    
    # Check if logger module exists
    print("\n2. Checking logger module...")
    logger_path = Path(__file__).parent / "core" / "logger.py"
    if logger_path.exists():
        print(f"   ✅ Logger module found at {logger_path}")
    else:
        print(f"   ❌ Logger module not found at {logger_path}")
        return False
    
    # Test logger initialization
    print("\n3. Testing logger initialization...")
    try:
        from core.logger import get_logger, init_logging
        init_logging(log_level="DEBUG", log_dir="logs")
        logger = get_logger(__name__)
        print("   ✅ Logger initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize logger: {e}")
        return False
    
    # Test logging output
    print("\n4. Testing log output...")
    try:
        logger.debug("Debug message test")
        logger.info("Info message test", extra={"test_field": "value"})
        logger.warning("Warning message test")
        logger.error("Error message test")
        print("   ✅ All log levels working")
    except Exception as e:
        print(f"   ❌ Logging failed: {e}")
        return False
    
    # Check log file
    print("\n5. Checking log file...")
    log_file = Path("logs/nexus.log")
    if log_file.exists():
        print(f"   ✅ Log file created at {log_file}")
        
        # Show sample log entries
        print("\n   📋 Sample log entries:")
        with open(log_file, "r") as f:
            lines = f.readlines()[-4:]  # Last 4 lines
            for line in lines:
                try:
                    data = json.loads(line)
                    level = data.get("level", "UNKNOWN")
                    message = data.get("message", "")
                    filename = data.get("filename", "?")
                    funcName = data.get("funcName", "?")
                    lineno = data.get("lineno", "?")
                    print(f"   [{level}] {filename}:{funcName}:{lineno} - {message}")
                except json.JSONDecodeError:
                    print(f"   (Could not parse): {line.strip()}")
    else:
        print(f"   ❌ Log file not created at {log_file}")
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    success = test_logging_setup()
    print("=" * 60)
    
    if success:
        print("\n✅ Logger setup verified successfully!")
        print("\nNext steps:")
        print("1. Start the API server: python main.py serve-api")
        print("2. View logs in real-time: tail -f logs/nexus.log")
        print("3. Parse JSON logs: cat logs/nexus.log | jq '.'")
        print("\nFor detailed logging guide, see: LOGGING_SETUP.md")
        sys.exit(0)
    else:
        print("\n❌ Logger setup has issues. Please check the errors above.")
        sys.exit(1)
