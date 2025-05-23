#!/usr/bin/env python3
"""
Clicker - Professional Windows Automation Tool

Modern, extensible automation tool with clean architecture.
This is the new minimal entry point that replaces the 2,500-line monolith.
"""

import sys
from pathlib import Path

# Add clicker package to path if running from source
sys.path.insert(0, str(Path(__file__).parent))

from clicker.app import main

if __name__ == "__main__":
    sys.exit(main()) 