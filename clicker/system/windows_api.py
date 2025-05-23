"""
Windows API utilities and virtual key code management.

This module provides Windows-specific functionality for keyboard input
and system integration.
"""

import ctypes
from ctypes import wintypes
from enum import IntEnum
from typing import Dict


class VirtualKeyCodes(IntEnum):
    """Windows virtual key codes for keyboard input."""
    
    # Numbers
    VK_0 = 0x30
    VK_1 = 0x31
    VK_2 = 0x32
    VK_3 = 0x33
    VK_4 = 0x34
    VK_5 = 0x35
    VK_6 = 0x36
    VK_7 = 0x37
    VK_8 = 0x38
    VK_9 = 0x39
    
    # Letters
    VK_A = 0x41
    VK_B = 0x42
    VK_C = 0x43
    VK_D = 0x44
    VK_E = 0x45
    VK_F = 0x46
    VK_G = 0x47
    VK_H = 0x48
    VK_I = 0x49
    VK_J = 0x4A
    VK_K = 0x4B
    VK_L = 0x4C
    VK_M = 0x4D
    VK_N = 0x4E
    VK_O = 0x4F
    VK_P = 0x50
    VK_Q = 0x51
    VK_R = 0x52
    VK_S = 0x53
    VK_T = 0x54
    VK_U = 0x55
    VK_V = 0x56
    VK_W = 0x57
    VK_X = 0x58
    VK_Y = 0x59
    VK_Z = 0x5A
    
    # Function keys
    VK_F1 = 0x70
    VK_F2 = 0x71
    VK_F3 = 0x72
    VK_F4 = 0x73
    VK_F5 = 0x74
    VK_F6 = 0x75
    VK_F7 = 0x76
    VK_F8 = 0x77
    VK_F9 = 0x78
    VK_F10 = 0x79
    VK_F11 = 0x7A
    VK_F12 = 0x7B
    
    # Modifiers
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_ALT = 0x12
    
    # Special keys
    VK_SPACE = 0x20
    VK_ENTER = 0x0D
    VK_TAB = 0x09
    VK_ESCAPE = 0x1B
    VK_BACKSPACE = 0x08
    VK_DELETE = 0x2E
    VK_INSERT = 0x2D
    VK_HOME = 0x24
    VK_END = 0x23
    VK_PAGEUP = 0x21
    VK_PAGEDOWN = 0x22
    
    # Arrow keys
    VK_UP = 0x26
    VK_DOWN = 0x28
    VK_LEFT = 0x25
    VK_RIGHT = 0x27


class WindowsAPI:
    """Windows API utilities for keyboard input and system integration."""
    
    # Windows API constants
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_EXTENDEDKEY = 0x0001
    INPUT_KEYBOARD = 1
    SW_HIDE = 0
    
    def __init__(self):
        # Load required DLLs
        self.user32 = ctypes.WinDLL('user32')
        self.kernel32 = ctypes.WinDLL('kernel32')
        
        # Define Windows API structures
        self._define_structures()
        
        # Create key mapping
        self.key_map = self._create_key_mapping()
    
    def _define_structures(self):
        """Define Windows API structures."""
        
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
            ]
        
        class INPUT(ctypes.Structure):
            class _INPUT(ctypes.Union):
                _fields_ = [
                    ("ki", KEYBDINPUT),
                    ("padding", ctypes.c_byte * 8)
                ]
            _anonymous_ = ("_input",)
            _fields_ = [
                ("type", wintypes.DWORD),
                ("_input", _INPUT)
            ]
        
        self.KEYBDINPUT = KEYBDINPUT
        self.INPUT = INPUT
    
    def _create_key_mapping(self) -> Dict[str, int]:
        """Create mapping from key names to virtual key codes."""
        return {
            # Numbers
            '0': VirtualKeyCodes.VK_0, '1': VirtualKeyCodes.VK_1, '2': VirtualKeyCodes.VK_2,
            '3': VirtualKeyCodes.VK_3, '4': VirtualKeyCodes.VK_4, '5': VirtualKeyCodes.VK_5,
            '6': VirtualKeyCodes.VK_6, '7': VirtualKeyCodes.VK_7, '8': VirtualKeyCodes.VK_8,
            '9': VirtualKeyCodes.VK_9,
            
            # Letters (both lower and upper case)
            'a': VirtualKeyCodes.VK_A, 'b': VirtualKeyCodes.VK_B, 'c': VirtualKeyCodes.VK_C,
            'd': VirtualKeyCodes.VK_D, 'e': VirtualKeyCodes.VK_E, 'f': VirtualKeyCodes.VK_F,
            'g': VirtualKeyCodes.VK_G, 'h': VirtualKeyCodes.VK_H, 'i': VirtualKeyCodes.VK_I,
            'j': VirtualKeyCodes.VK_J, 'k': VirtualKeyCodes.VK_K, 'l': VirtualKeyCodes.VK_L,
            'm': VirtualKeyCodes.VK_M, 'n': VirtualKeyCodes.VK_N, 'o': VirtualKeyCodes.VK_O,
            'p': VirtualKeyCodes.VK_P, 'q': VirtualKeyCodes.VK_Q, 'r': VirtualKeyCodes.VK_R,
            's': VirtualKeyCodes.VK_S, 't': VirtualKeyCodes.VK_T, 'u': VirtualKeyCodes.VK_U,
            'v': VirtualKeyCodes.VK_V, 'w': VirtualKeyCodes.VK_W, 'x': VirtualKeyCodes.VK_X,
            'y': VirtualKeyCodes.VK_Y, 'z': VirtualKeyCodes.VK_Z,
            
            # Function keys
            'f1': VirtualKeyCodes.VK_F1, 'f2': VirtualKeyCodes.VK_F2, 'f3': VirtualKeyCodes.VK_F3,
            'f4': VirtualKeyCodes.VK_F4, 'f5': VirtualKeyCodes.VK_F5, 'f6': VirtualKeyCodes.VK_F6,
            'f7': VirtualKeyCodes.VK_F7, 'f8': VirtualKeyCodes.VK_F8, 'f9': VirtualKeyCodes.VK_F9,
            'f10': VirtualKeyCodes.VK_F10, 'f11': VirtualKeyCodes.VK_F11, 'f12': VirtualKeyCodes.VK_F12,
            
            # Special keys
            'space': VirtualKeyCodes.VK_SPACE,
            'enter': VirtualKeyCodes.VK_ENTER,
            'tab': VirtualKeyCodes.VK_TAB,
            'escape': VirtualKeyCodes.VK_ESCAPE,
            'backspace': VirtualKeyCodes.VK_BACKSPACE,
            'delete': VirtualKeyCodes.VK_DELETE,
            'insert': VirtualKeyCodes.VK_INSERT,
            'home': VirtualKeyCodes.VK_HOME,
            'end': VirtualKeyCodes.VK_END,
            'pageup': VirtualKeyCodes.VK_PAGEUP,
            'pagedown': VirtualKeyCodes.VK_PAGEDOWN,
            'up': VirtualKeyCodes.VK_UP,
            'down': VirtualKeyCodes.VK_DOWN,
            'left': VirtualKeyCodes.VK_LEFT,
            'right': VirtualKeyCodes.VK_RIGHT,
        }
    
    def get_virtual_key_code(self, key_name: str) -> int:
        """
        Get virtual key code for a key name.
        
        Args:
            key_name: Name of the key (e.g., 'a', 'f1', 'space')
            
        Returns:
            Virtual key code, or 0 if not found
        """
        return self.key_map.get(key_name.lower(), 0)
    
    def hide_console_window(self) -> None:
        """Hide the console window."""
        try:
            hwnd = self.kernel32.GetConsoleWindow()
            if hwnd:
                self.user32.ShowWindow(hwnd, self.SW_HIDE)
        except Exception:
            pass  # Silently fail if console hiding doesn't work
    
    def send_key_event(self, vk_code: int, is_key_up: bool = False) -> bool:
        """
        Send a single key event using Windows API.
        
        Args:
            vk_code: Virtual key code
            is_key_up: True for key release, False for key press
            
        Returns:
            True if successful, False otherwise
        """
        try:
            flags = self.KEYEVENTF_KEYUP if is_key_up else 0
            
            # Use keybd_event for simplicity and compatibility
            result = self.user32.keybd_event(
                wintypes.BYTE(vk_code),
                wintypes.BYTE(0),  # Scan code
                wintypes.DWORD(flags),
                wintypes.DWORD(0)  # Extra info
            )
            
            return result != 0
            
        except Exception:
            return False
    
    def send_key_combination(self, modifiers: list, main_key: str) -> bool:
        """
        Send a key combination with modifiers.
        
        Args:
            modifiers: List of modifier keys ('shift', 'ctrl', 'alt')
            main_key: Main key to press
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get virtual key code for main key
            main_vk = self.get_virtual_key_code(main_key)
            if main_vk == 0:
                return False
            
            # Map modifiers to virtual key codes
            modifier_map = {
                'shift': VirtualKeyCodes.VK_SHIFT,
                'ctrl': VirtualKeyCodes.VK_CONTROL,
                'alt': VirtualKeyCodes.VK_ALT
            }
            
            # Press modifiers
            pressed_modifiers = []
            for modifier in modifiers:
                mod_vk = modifier_map.get(modifier)
                if mod_vk:
                    if self.send_key_event(mod_vk, False):
                        pressed_modifiers.append(mod_vk)
                    else:
                        # Release any modifiers we've already pressed
                        for pressed_mod in reversed(pressed_modifiers):
                            self.send_key_event(pressed_mod, True)
                        return False
            
            # Small delay between modifiers and main key
            if pressed_modifiers:
                ctypes.windll.kernel32.Sleep(10)
            
            # Press and release main key
            if not self.send_key_event(main_vk, False):
                # Release modifiers
                for mod_vk in reversed(pressed_modifiers):
                    self.send_key_event(mod_vk, True)
                return False
            
            # Small delay for key press
            ctypes.windll.kernel32.Sleep(10)
            
            if not self.send_key_event(main_vk, True):
                # Release modifiers anyway
                for mod_vk in reversed(pressed_modifiers):
                    self.send_key_event(mod_vk, True)
                return False
            
            # Small delay before releasing modifiers
            if pressed_modifiers:
                ctypes.windll.kernel32.Sleep(10)
            
            # Release modifiers in reverse order
            for mod_vk in reversed(pressed_modifiers):
                if not self.send_key_event(mod_vk, True):
                    return False
            
            return True
            
        except Exception:
            return False 