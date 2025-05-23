"""
Clicker - Professional Windows Automation Tool

A modern, extensible automation tool for Windows with clean architecture,
comprehensive testing, and professional-grade features.
"""

__version__ = "2.1.2"
__author__ = "Clicker Team"
__email__ = "contact@clicker.dev"
__license__ = "MIT"

# Core imports for easy access
from clicker.config.models import AppSettings, KeystrokeConfig
from clicker.core.automation import AutomationEngine, AutomationState
from clicker.app import ClickerApp

__all__ = [
    "ClickerApp",
    "AutomationEngine", 
    "AutomationState",
    "AppSettings",
    "KeystrokeConfig",
    "__version__",
] 