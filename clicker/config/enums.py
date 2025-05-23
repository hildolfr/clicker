"""
Configuration enums for the Clicker application.
"""

from enum import Enum


class IndicatorType(Enum):
    """Visual indicator types for automation status."""
    PYGAME = "pygame"
    GDI = "gdi" 
    NONE = "none"


class KeystrokeMethod(Enum):
    """Methods for sending keystrokes."""
    WINDOWS_API = "windows_api"
    SEND_KEYS = "sendkeys"
    PYAUTOGUI = "pyautogui" 