"""
Event System for Clicker Application.

Provides a clean, decoupled event system for communication between components.
This replaces the tightly coupled global state from the original code.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set
from weakref import WeakSet
import threading


class EventType(Enum):
    """Event types for the Clicker application."""
    
    # Automation events
    AUTOMATION_STARTED = auto()
    AUTOMATION_STOPPED = auto()
    AUTOMATION_PAUSED = auto()
    AUTOMATION_RESUMED = auto()
    AUTOMATION_ERROR = auto()
    
    # Keystroke events
    KEYSTROKE_SENT = auto()
    KEYSTROKE_FAILED = auto()
    KEYSTROKE_QUEUED = auto()
    
    # Configuration events
    CONFIG_LOADED = auto()
    CONFIG_CHANGED = auto()
    CONFIG_SAVED = auto()
    CONFIG_ERROR = auto()
    
    # System events
    HOTKEY_PRESSED = auto()
    SHUTDOWN_REQUESTED = auto()
    SINGLETON_VIOLATION = auto()
    
    # UI events
    TRAY_ACTIVATED = auto()
    MENU_OPENED = auto()
    MENU_CLOSED = auto()


@dataclass
class AutomationEvent:
    """Represents an event in the Clicker application."""
    
    event_type: EventType
    source: str
    timestamp: float
    data: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None
    
    def __str__(self) -> str:
        return f"Event({self.event_type.name}, source={self.source})"


EventHandler = Callable[[AutomationEvent], None]


class EventSystem:
    """
    Thread-safe event system for component communication.
    
    This provides a clean way for components to communicate without
    tight coupling, replacing the global state pattern from the original code.
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, WeakSet[EventHandler]] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event occurs
        """
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = WeakSet()
            
            self._handlers[event_type].add(handler)
            self._logger.debug(f"Subscribed handler to {event_type.name}")
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
            
        Returns:
            True if handler was removed, False if not found
        """
        with self._lock:
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].discard(handler)
                    self._logger.debug(f"Unsubscribed handler from {event_type.name}")
                    return True
                except KeyError:
                    pass
            return False
    
    def emit(self, event: AutomationEvent) -> None:
        """
        Emit an event to all subscribers.
        
        Args:
            event: Event to emit
        """
        with self._lock:
            if event.event_type in self._handlers:
                # Create a copy to avoid issues with concurrent modification
                handlers = list(self._handlers[event.event_type])
                
                self._logger.debug(f"Emitting {event} to {len(handlers)} handlers")
                
                for handler in handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        self._logger.error(f"Error in event handler for {event}: {e}")
    
    def emit_simple(self, event_type: EventType, source: str, 
                   data: Optional[Dict[str, Any]] = None) -> None:
        """
        Convenience method to emit a simple event.
        
        Args:
            event_type: Type of event
            source: Source component name
            data: Optional event data
        """
        import time
        
        event = AutomationEvent(
            event_type=event_type,
            source=source,
            timestamp=time.time(),
            data=data
        )
        self.emit(event)
    
    def get_handler_count(self, event_type: EventType) -> int:
        """Get the number of handlers for an event type."""
        with self._lock:
            if event_type in self._handlers:
                return len(self._handlers[event_type])
            return 0
    
    def clear_handlers(self, event_type: Optional[EventType] = None) -> None:
        """
        Clear handlers for an event type, or all handlers.
        
        Args:
            event_type: Event type to clear, or None for all
        """
        with self._lock:
            if event_type is None:
                self._handlers.clear()
                self._logger.debug("Cleared all event handlers")
            elif event_type in self._handlers:
                self._handlers[event_type].clear()
                self._logger.debug(f"Cleared handlers for {event_type.name}")


# Global event system instance
# This provides a singleton-like access pattern while still being testable
_global_event_system: Optional[EventSystem] = None


def get_event_system() -> EventSystem:
    """Get the global event system instance."""
    global _global_event_system
    if _global_event_system is None:
        _global_event_system = EventSystem()
    return _global_event_system


def set_event_system(event_system: EventSystem) -> None:
    """Set the global event system instance (for testing)."""
    global _global_event_system
    _global_event_system = event_system


# Convenience functions for common operations
def emit_automation_started(source: str) -> None:
    """Emit automation started event."""
    get_event_system().emit_simple(EventType.AUTOMATION_STARTED, source)


def emit_automation_stopped(source: str) -> None:
    """Emit automation stopped event."""
    get_event_system().emit_simple(EventType.AUTOMATION_STOPPED, source)


def emit_config_changed(source: str, changes: Dict[str, Any]) -> None:
    """Emit configuration changed event."""
    get_event_system().emit_simple(EventType.CONFIG_CHANGED, source, {"changes": changes})


def emit_keystroke_sent(source: str, keystroke: str) -> None:
    """Emit keystroke sent event."""
    get_event_system().emit_simple(EventType.KEYSTROKE_SENT, source, {"keystroke": keystroke}) 