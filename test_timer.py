#!/usr/bin/env python3
"""
Test script to verify configuration file reload timer functionality.
This script will monitor the configuration files and test the reload behavior.
"""

import time
import json
from pathlib import Path
from datetime import datetime

def test_config_reload():
    """Test the configuration reload functionality."""
    print("Testing configuration file reload functionality...")
    print(f"Test started at: {datetime.now()}")
    
    settings_file = Path("settings.json")
    keystrokes_file = Path("keystrokes.txt")
    
    # Check initial state
    print(f"\nInitial file states:")
    if settings_file.exists():
        mtime = settings_file.stat().st_mtime
        print(f"  settings.json: {datetime.fromtimestamp(mtime)}")
    else:
        print(f"  settings.json: NOT FOUND")
        
    if keystrokes_file.exists():
        mtime = keystrokes_file.stat().st_mtime
        print(f"  keystrokes.txt: {datetime.fromtimestamp(mtime)}")
    else:
        print(f"  keystrokes.txt: NOT FOUND")
    
    print(f"\nTo test the timer:")
    print(f"1. Make sure Clicker is running")
    print(f"2. Edit one of the configuration files")
    print(f"3. Wait up to 30 seconds for the change to be detected")
    print(f"4. Check the clicker.log file for reload messages")
    
    print(f"\nExpected log messages:")
    print(f"  - 'Settings file modified externally' or")
    print(f"  - 'Keystrokes file modified externally'")
    print(f"  - 'Configuration files changed, applying changes...'")
    print(f"  - 'Configuration changes applied successfully'")

if __name__ == "__main__":
    test_config_reload() 