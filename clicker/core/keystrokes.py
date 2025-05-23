"""
Keystroke sending interface and Windows implementation.

This module abstracts keystroke sending operations, making the code
more testable and potentially cross-platform in the future.
"""

from __future__ import annotations

import ctypes
import logging
import time
from abc import ABC, abstractmethod
from ctypes import wintypes
from typing import List, Optional, Dict, Tuple, Protocol

from clicker.utils.exceptions import KeystrokeError, SystemError
from clicker.system.windows_api import WindowsAPI


class KeystrokeSender(Protocol):
    """Interface for sending keystrokes to the system."""
    
    def send_keystroke(self, key: str, modifiers: Optional[List[str]] = None) -> bool:
        """Send a keystroke with optional modifiers."""
        ...
    
    def is_available(self) -> bool:
        """Check if the keystroke sender is available."""
        ...


class WindowsKeystrokeSender:
    """Windows-specific keystroke sender using Windows API."""
    
    # Virtual key codes mapping (extracted from original code)
    VK_MAP = {
        '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
        '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
        'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
        'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
        'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
        'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
        'z': 0x5A,
        'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
        'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
        'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
        'space': 0x20, 'enter': 0x0D, 'tab': 0x09, 'escape': 0x1B,
        'backspace': 0x08, 'delete': 0x2E, 'insert': 0x2D,
        'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
        'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    }
    
    # Modifier key codes
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_MENU = 0x12  # Alt key
    
    # Key event flags
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_EXTENDEDKEY = 0x0001
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._modifier_map = {
            'shift': self.VK_SHIFT,
            'ctrl': self.VK_CONTROL,
            'alt': self.VK_MENU
        }
        
        # Test Windows API availability
        self._api_available = self._test_api_availability()
        
        if self._api_available:
            self.logger.info("Windows keystroke sender initialized successfully")
        else:
            self.logger.error("Windows API not available for keystroke sending")
    
    def _test_api_availability(self) -> bool:
        """Test if Windows API is available for keystroke operations."""
        try:
            # Try to call a simple Windows API function
            ctypes.windll.user32.GetKeyState(0x10)  # VK_SHIFT
            return True
        except Exception as e:
            self.logger.error(f"Windows API test failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if the keystroke sender is available."""
        return self._api_available
    
    def send_keystroke(self, key: str, modifiers: Optional[List[str]] = None) -> bool:
        """
        Send a keystroke with optional modifiers.
        
        Args:
            key: The key to send (e.g., 'a', 'space', 'f1')
            modifiers: Optional list of modifiers (['shift', 'ctrl', 'alt'])
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._api_available:
            self.logger.error("Windows API not available")
            return False
        
        # Parse key string if it contains modifiers (e.g., "C-S-a")
        if '-' in key and not modifiers:
            modifiers, key = self._parse_key_string(key)
        
        modifiers = modifiers or []
        
        try:
            return self._send_key_combination(modifiers, key)
        except Exception as e:
            self.logger.error(f"Error sending keystroke {key}: {e}")
            return False
    
    def _parse_key_string(self, key_str: str) -> Tuple[List[str], str]:
        """Parse keystroke string into modifiers and key (from original code)."""
        if '-' not in key_str:
            return [], key_str
            
        modifier_map = {
            'S': 'shift',
            'C': 'ctrl', 
            'A': 'alt'
        }
        
        parts = key_str.split('-')
        key = parts[-1]
        mods = []
        
        for p in parts[:-1]:
            mod = modifier_map.get(p)
            if mod:
                mods.append(mod)
            else:
                self.logger.warning(f"Unknown modifier in keystroke: '{p}'")
                
        return mods, key
    
    def _send_key_combination(self, modifiers: List[str], key: str) -> bool:
        """Send a key combination with modifiers (adapted from original code)."""
        try:
            self.logger.debug(f"Sending key combination: modifiers={modifiers}, key={key}")
            
            # Get virtual key code
            vk_code = self.VK_MAP.get(key.lower())
            if vk_code is None:
                self.logger.error(f"Unknown key '{key}' - not found in VK_MAP")
                return False
            
            # Track which modifiers were successfully pressed
            pressed_mods = []
            
            # Press modifiers
            for mod in modifiers:
                mod_vk = self._modifier_map.get(mod)
                
                if mod_vk is not None:
                    if not self._send_key_event(mod_vk):
                        self.logger.error(f"Failed to press modifier key: {mod}")
                        # Release any modifiers we've already pressed
                        self._release_modifiers(pressed_mods)
                        return False
                    pressed_mods.append(mod)
            
            # Small delay between modifiers and main key
            if pressed_mods:
                time.sleep(0.01)
            
            # Press and release the main key
            if not self._send_key_event(vk_code):
                self.logger.error(f"Failed to press main key: {key} (VK: 0x{vk_code:02X})")
                self._release_modifiers(pressed_mods)
                return False
            
            # Small delay between press and release
            time.sleep(0.01)
            
            if not self._send_key_event(vk_code, is_key_up=True):
                self.logger.error(f"Failed to release main key: {key} (VK: 0x{vk_code:02X})")
                self._release_modifiers(pressed_mods)
                return False
            
            # Small delay before releasing modifiers
            if pressed_mods:
                time.sleep(0.01)
                self._release_modifiers(pressed_mods)
            
            self.logger.debug(f"Successfully sent key combination: {modifiers}, {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in _send_key_combination: {e}")
            return False
    
    def _release_modifiers(self, pressed_mods: List[str]) -> None:
        """Release pressed modifier keys."""
        for mod in reversed(pressed_mods):
            mod_vk = self._modifier_map.get(mod)
            if mod_vk is not None:
                if not self._send_key_event(mod_vk, is_key_up=True):
                    self.logger.error(f"Failed to release modifier key: {mod}")
    
    def _send_key_event(self, vk_code: int, is_key_up: bool = False) -> bool:
        """Send a key event using Windows API (from original code)."""
        try:
            event_type = "KEY UP" if is_key_up else "KEY DOWN"
            self.logger.debug(f"Sending {event_type} event for VK code: 0x{vk_code:02X}")
            
            flags = self.KEYEVENTF_KEYUP if is_key_up else 0
            
            # Cast parameters to appropriate types
            vk_byte = wintypes.BYTE(vk_code)
            scan_byte = wintypes.BYTE(0)
            flags_dword = wintypes.DWORD(flags)
            extra_dword = wintypes.DWORD(0)
            
            # Send the key event
            result = ctypes.windll.user32.keybd_event(
                vk_byte,
                scan_byte,
                flags_dword,
                extra_dword
            )
            
            # Check if the call succeeded
            if result == 0:
                error_code = ctypes.get_last_error()
                self.logger.error(f"Windows API error in keybd_event: code {error_code}")
                return False
                
            # Small delay after sending key event
            time.sleep(0.005)
            return True
            
        except Exception as e:
            self.logger.error(f"Error in _send_key_event (VK: 0x{vk_code:02X}, up={is_key_up}): {e}")
            return False
    
    def get_supported_keys(self) -> List[str]:
        """Get list of supported key names."""
        return list(self.VK_MAP.keys())
    
    def validate_key(self, key: str) -> bool:
        """Validate if a key is supported."""
        # Parse modifiers if present
        if '-' in key:
            modifiers, main_key = self._parse_key_string(key)
            return main_key.lower() in self.VK_MAP
        
        return key.lower() in self.VK_MAP


class MockKeystrokeSender:
    """Mock keystroke sender for testing purposes."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sent_keystrokes: List[Dict] = []
        self._available = True
        self._should_fail = False
    
    def send_keystroke(self, key: str, modifiers: Optional[List[str]] = None) -> bool:
        """Mock keystroke sending for testing."""
        if not self._available:
            return False
        
        if self._should_fail:
            return False
        
        self.sent_keystrokes.append({
            'key': key,
            'modifiers': modifiers or [],
            'timestamp': time.time()
        })
        
        self.logger.debug(f"Mock sent keystroke: {key} with modifiers: {modifiers}")
        return True
    
    def is_available(self) -> bool:
        """Check if mock sender is available."""
        return self._available
    
    def set_available(self, available: bool) -> None:
        """Set availability for testing."""
        self._available = available
    
    def set_should_fail(self, should_fail: bool) -> None:
        """Set whether keystrokes should fail for testing."""
        self._should_fail = should_fail
    
    def get_sent_keystrokes(self) -> List[Dict]:
        """Get list of sent keystrokes for testing."""
        return self.sent_keystrokes.copy()
    
    def clear_history(self) -> None:
        """Clear keystroke history."""
        self.sent_keystrokes.clear() 