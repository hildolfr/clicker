"""
Clicker - Professional Windows automation tool.

A modern, efficient auto-clicker application with GUI and hotkey support.
"""

__version__ = "2.2.2"
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