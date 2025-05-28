"""
Hotkey Management System.

Handles global hotkeys for the Clicker application.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, Optional, Any, List
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

    def register_tilde_combinations(self, hotkey_id: str, callback: Callable[[], None]) -> bool:
        """
        Register all possible tilde key combinations.
        
        This will register the tilde key by itself and with all common modifier combinations.
        
        Args:
            hotkey_id: Base identifier for this hotkey group
            callback: Function to call when any tilde combination is pressed
            
        Returns:
            True if at least one combination was registered successfully, False otherwise
        """
        with self._lock:
            # Remove any existing tilde combinations
            self.unregister_tilde_combinations(hotkey_id)
            
            # Define valid tilde combinations using proper keyboard library syntax
            tilde_combinations = [
                '~',                    # Just tilde
                'ctrl+~',              # Ctrl + tilde
                'shift+~',             # Shift + tilde  
                'alt+~',               # Alt + tilde
                'ctrl+shift+~',        # Ctrl + Shift + tilde
                'ctrl+alt+~',          # Ctrl + Alt + tilde
                'shift+alt+~',         # Shift + Alt + tilde
                'ctrl+shift+alt+~',    # All modifiers + tilde
            ]
            
            # Add number combinations with tilde (these are more likely to work)
            numbers = '0123456789'
            for number in numbers:
                tilde_combinations.extend([
                    f'~+{number}',         # Tilde + number
                    f'ctrl+~+{number}',    # Ctrl + tilde + number
                    f'shift+~+{number}',   # Shift + tilde + number
                    f'alt+~+{number}',     # Alt + tilde + number
                ])
            
            # Add some common letter combinations (limit to reduce registration overhead)
            common_letters = 'asdwqe'  # Common gaming/typing keys
            for letter in common_letters:
                tilde_combinations.extend([
                    f'~+{letter}',         # Tilde + letter
                    f'ctrl+~+{letter}',    # Ctrl + tilde + letter
                    f'shift+~+{letter}',   # Shift + tilde + letter
                    f'alt+~+{letter}',     # Alt + tilde + letter
                ])
            
            successful_registrations = 0
            failed_registrations = 0
            
            for i, combination in enumerate(tilde_combinations):
                try:
                    # Create unique ID for each combination
                    combo_id = f"{hotkey_id}_tilde_{i}"
                    
                    # Register the combination
                    handle = keyboard.add_hotkey(combination, self._on_hotkey_pressed, args=[combo_id])
                    
                    self._hotkeys[combo_id] = handle
                    self._callbacks[combo_id] = callback
                    
                    successful_registrations += 1
                    self._logger.debug(f"Registered tilde combination: {combination}")
                    
                except Exception as e:
                    failed_registrations += 1
                    self._logger.debug(f"Failed to register tilde combination '{combination}': {e}")
                    # Continue trying other combinations
            
            self._logger.info(f"Registered {successful_registrations} tilde combinations for '{hotkey_id}' "
                            f"({failed_registrations} failed)")
            
            return successful_registrations > 0

    def unregister_tilde_combinations(self, hotkey_id: str) -> bool:
        """
        Unregister all tilde combinations for a given hotkey ID.
        
        Args:
            hotkey_id: Base identifier for the hotkey group
            
        Returns:
            True if any combinations were removed, False if none found
        """
        with self._lock:
            removed_count = 0
            
            # Find all hotkeys that match the tilde pattern for this ID
            hotkeys_to_remove = []
            for combo_id in self._hotkeys.keys():
                if combo_id.startswith(f"{hotkey_id}_tilde_"):
                    hotkeys_to_remove.append(combo_id)
            
            # Remove each matching hotkey
            for combo_id in hotkeys_to_remove:
                try:
                    handle = self._hotkeys[combo_id]
                    keyboard.remove_hotkey(handle)
                    
                    del self._hotkeys[combo_id]
                    del self._callbacks[combo_id]
                    
                    removed_count += 1
                    
                except Exception as e:
                    self._logger.error(f"Failed to unregister tilde combination '{combo_id}': {e}")
            
            if removed_count > 0:
                self._logger.info(f"Unregistered {removed_count} tilde combinations for '{hotkey_id}'")
                return True
            
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
                try:
                    handle = self._hotkeys[hotkey_id]
                    keyboard.remove_hotkey(handle)
                except Exception as e:
                    self._logger.error(f"Error removing hotkey {hotkey_id}: {e}")
            
            self._hotkeys.clear()
            self._callbacks.clear()
            
            self._logger.info("Unregistered all hotkeys")
    
    def _on_hotkey_pressed(self, hotkey_id: str) -> None:
        """Internal callback when a hotkey is pressed."""
        with self._lock:
            # For tilde combinations, we need to find the base hotkey ID for events
            base_hotkey_id = hotkey_id
            if "_tilde_" in hotkey_id:
                base_hotkey_id = hotkey_id.split("_tilde_")[0]
            
            # Look for callback using the actual hotkey_id that was registered
            callback = self._callbacks.get(hotkey_id)
            
            if callback:
                try:
                    self._logger.debug(f"Hotkey pressed: {hotkey_id}")
                    
                    # Emit event if event system is available
                    if self.event_system:
                        self.event_system.emit_simple(
                            EventType.HOTKEY_PRESSED, 
                            "HotkeyManager",
                            {"hotkey_id": base_hotkey_id}
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