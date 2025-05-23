"""Core automation engine package."""

from clicker.core.automation import AutomationEngine, AutomationState, ExecutionStats
from clicker.core.scheduler import KeystrokeScheduler, ScheduledKeystroke
from clicker.core.keystrokes import KeystrokeSender, WindowsKeystrokeSender
from clicker.core.events import EventSystem, AutomationEvent, EventType

__all__ = [
    "AutomationEngine",
    "AutomationState", 
    "ExecutionStats",
    "KeystrokeScheduler",
    "ScheduledKeystroke",
    "KeystrokeSender",
    "WindowsKeystrokeSender",
    "EventSystem",
    "AutomationEvent",
    "EventType",
] 