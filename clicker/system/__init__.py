"""
System utilities for Windows automation.

This module provides Windows-specific functionality including:
- Admin privilege checks
- Singleton instance management
- Windows API integration
"""

from .admin import AdminChecker, request_admin_privileges
from .singleton import SingletonManager
from .windows_api import WindowsAPI, VirtualKeyCodes

__all__ = [
    'AdminChecker',
    'request_admin_privileges', 
    'SingletonManager',
    'WindowsAPI',
    'VirtualKeyCodes'
] 