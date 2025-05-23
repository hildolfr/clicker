"""
Global hotkey management for the Clicker application.

This module provides functionality to register and manage global hotkeys
that work across the entire system.
"""

import keyboard
import logging
from typing import Optional, Callable, Dict, Any

from clicker.utils.exceptions import ClickerError


class HotkeyManager:
    """Manages global hotkeys for the application."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._hotkeys: Dict[str, Any] = {}
        self._current_toggle_key: Optional[str] = None
        self._toggle_callback: Optional[Callable] = None
    
    def register_toggle_hotkey(self, key: str, callback: Callable) -> bool:
        """
        Register a global hotkey for toggling automation.
        
        Args:
            key: Key combination string (e.g., '~', 'ctrl+shift+t')
            callback: Function to call when hotkey is pressed
            
        Returns:
            True if registration successful, False otherwise
        """
        # Remove existing hotkey if any
        self.unregister_toggle_hotkey()
        
        try:
            hotkey_id = keyboard.add_hotkey(key, callback)
            self._hotkeys[key] = hotkey_id
            self._current_toggle_key = key
            self._toggle_callback = callback
            
            self.logger.info(f"Registered toggle hotkey: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register hotkey '{key}': {e}")
            
            # Try to use a fallback hotkey if the requested one fails
            if key != '~':  # Don't recurse if ~ itself fails
                self.logger.info("Attempting to use fallback hotkey: ~")
                return self.register_toggle_hotkey('~', callback)
            
            return False
    
    def unregister_toggle_hotkey(self) -> None:
        """Unregister the current toggle hotkey."""
        if self._current_toggle_key and self._current_toggle_key in self._hotkeys:
            try:
                keyboard.remove_hotkey(self._hotkeys[self._current_toggle_key])
                del self._hotkeys[self._current_toggle_key]
                self.logger.debug(f"Unregistered hotkey: {self._current_toggle_key}")
            except Exception as e:
                self.logger.error(f"Error unregistering hotkey: {e}")
            finally:
                self._current_toggle_key = None
                self._toggle_callback = None
    
    def update_toggle_hotkey(self, new_key: str) -> bool:
        """
        Update the toggle hotkey with a new key combination.
        
        Args:
            new_key: New key combination string
            
        Returns:
            True if update successful, False otherwise
        """
        if not self._toggle_callback:
            self.logger.error("No toggle callback registered")
            return False
        
        return self.register_toggle_hotkey(new_key, self._toggle_callback)
    
    def get_current_toggle_key(self) -> Optional[str]:
        """Get the currently registered toggle key."""
        return self._current_toggle_key
    
    def cleanup(self) -> None:
        """Clean up all registered hotkeys."""
        keys_to_remove = list(self._hotkeys.keys())
        for key in keys_to_remove:
            try:
                keyboard.remove_hotkey(self._hotkeys[key])
                del self._hotkeys[key]
            except Exception as e:
                self.logger.error(f"Error removing hotkey {key}: {e}")
        
        self._current_toggle_key = None
        self._toggle_callback = None
        self.logger.debug("Cleaned up all hotkeys")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup() 