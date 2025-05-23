"""
Utility modules for the Clicker application.

This package contains various utility modules that provide support
functionality for the main application.
"""

from .exceptions import ClickerError, ConfigurationError, AutomationError, UpdateError
from .hotkeys import HotkeyManager
from .file_watcher import FileWatcher
from .updater import AutoUpdater, UpdateChecker, UpdateInfo

__all__ = [
    'ClickerError',
    'ConfigurationError', 
    'AutomationError',
    'UpdateError',
    'HotkeyManager',
    'FileWatcher',
    'AutoUpdater',
    'UpdateChecker',
    'UpdateInfo'
] 