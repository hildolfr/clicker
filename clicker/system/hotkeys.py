"""
Hotkey Management System.

Handles global hotkeys for the Clicker application.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, Optional, Any
import threading

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

from clicker.core.events import EventSystem, EventType


class HotkeyManager:
    """
    Manages global hotkeys for the application.
    
    This provides a clean interface for registering and managing
    global hotkeys, replacing the scattered hotkey code from the original.
    """
    
    def __init__(self, event_system: Optional[EventSystem] = None):
        if not KEYBOARD_AVAILABLE:
            raise ImportError("keyboard library is not available")
            
        self.event_system = event_system
        self._hotkeys: Dict[str, Any] = {}  # hotkey_id -> keyboard handle
        self._callbacks: Dict[str, Callable] = {}  # hotkey_id -> callback
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
    def register_hotkey(self, hotkey_id: str, key_combination: str, 
                       callback: Callable[[], None]) -> bool:
        """
        Register a global hotkey.
        
        Args:
            hotkey_id: Unique identifier for this hotkey
            key_combination: Key combination (e.g., 'ctrl+shift+a', '~')
            callback: Function to call when hotkey is pressed
            
        Returns:
            True if hotkey was registered successfully, False otherwise
        """
        with self._lock:
            # Remove existing hotkey if it exists
            if hotkey_id in self._hotkeys:
                self.unregister_hotkey(hotkey_id)
            
            try:
                # Register the hotkey with the keyboard library
                handle = keyboard.add_hotkey(key_combination, self._on_hotkey_pressed, args=[hotkey_id])
                
                self._hotkeys[hotkey_id] = handle
                self._callbacks[hotkey_id] = callback
                
                self._logger.info(f"Registered hotkey '{hotkey_id}': {key_combination}")
                return True
                
            except Exception as e:
                self._logger.error(f"Failed to register hotkey '{hotkey_id}' ({key_combination}): {e}")
                return False
    
    def unregister_hotkey(self, hotkey_id: str) -> bool:
        """
        Unregister a global hotkey.
        
        Args:
            hotkey_id: Identifier of hotkey to remove
            
        Returns:
            True if hotkey was removed, False if not found
        """
        with self._lock:
            if hotkey_id not in self._hotkeys:
                return False
            
            try:
                handle = self._hotkeys[hotkey_id]
                keyboard.remove_hotkey(handle)
                
                del self._hotkeys[hotkey_id]
                del self._callbacks[hotkey_id]
                
                self._logger.info(f"Unregistered hotkey '{hotkey_id}'")
                return True
                
            except Exception as e:
                self._logger.error(f"Failed to unregister hotkey '{hotkey_id}': {e}")
                return False
    
    def update_hotkey(self, hotkey_id: str, new_key_combination: str) -> bool:
        """
        Update an existing hotkey with a new key combination.
        
        Args:
            hotkey_id: Identifier of hotkey to update
            new_key_combination: New key combination
            
        Returns:
            True if hotkey was updated successfully, False otherwise
        """
        with self._lock:
            if hotkey_id not in self._callbacks:
                self._logger.warning(f"Cannot update hotkey '{hotkey_id}' - not found")
                return False
            
            # Keep the existing callback
            callback = self._callbacks[hotkey_id]
            
            # Re-register with new key combination
            return self.register_hotkey(hotkey_id, new_key_combination, callback)
    
    def is_registered(self, hotkey_id: str) -> bool:
        """Check if a hotkey is currently registered."""
        with self._lock:
            return hotkey_id in self._hotkeys
    
    def get_registered_hotkeys(self) -> Dict[str, str]:
        """Get a dictionary of registered hotkey IDs and their key combinations."""
        with self._lock:
            # Note: The keyboard library doesn't provide an easy way to get the key combination
            # back from a handle, so we'd need to track this separately if needed
            return {hotkey_id: "unknown" for hotkey_id in self._hotkeys.keys()}
    
    def unregister_all(self) -> None:
        """Unregister all hotkeys."""
        with self._lock:
            hotkey_ids = list(self._hotkeys.keys())
            for hotkey_id in hotkey_ids:
                self.unregister_hotkey(hotkey_id)
            
            self._logger.info("Unregistered all hotkeys")
    
    def _on_hotkey_pressed(self, hotkey_id: str) -> None:
        """Internal callback when a hotkey is pressed."""
        with self._lock:
            callback = self._callbacks.get(hotkey_id)
            if callback:
                try:
                    self._logger.debug(f"Hotkey pressed: {hotkey_id}")
                    
                    # Emit event if event system is available
                    if self.event_system:
                        self.event_system.emit_simple(
                            EventType.HOTKEY_PRESSED, 
                            "HotkeyManager",
                            {"hotkey_id": hotkey_id}
                        )
                    
                    # Call the registered callback
                    callback()
                    
                except Exception as e:
                    self._logger.error(f"Error in hotkey callback for '{hotkey_id}': {e}")
            else:
                self._logger.warning(f"No callback found for hotkey '{hotkey_id}'")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - unregister all hotkeys."""
        self.unregister_all() 