"""
Global Indicator Manager.

Manages visual indicators and handles dialog interference issues.
This solves the problem of GDI overlays covering system tray menus and dialogs.
"""

from __future__ import annotations

import logging
from typing import Optional, Any, Callable
from PyQt5 import QtWidgets

from .base import VisualIndicator


class IndicatorManager:
    """
    Global manager for visual indicators with dialog handling.
    
    This class solves the issue where GDI overlays can cover system tray
    menus and other dialogs by automatically hiding/showing indicators
    when menus and dialogs are active.
    """
    
    def __init__(self):
        self.visual_indicator: Optional[VisualIndicator] = None
        self.menu_active = False
        self.hidden_for_menu = False
        self.logger = logging.getLogger(__name__)
    
    def set_indicator(self, indicator: VisualIndicator) -> None:
        """Set the active visual indicator."""
        self.visual_indicator = indicator
        self.logger.info(f"Indicator manager set to use: {type(indicator).__name__}")
    
    def hide_indicator(self) -> bool:
        """
        Hide the visual indicator.
        
        Returns:
            True if indicator was hidden, False otherwise
        """
        if self.visual_indicator and hasattr(self.visual_indicator, 'hide_window'):
            try:
                self.visual_indicator.hide_window()
                self.hidden_for_menu = True
                self.logger.debug("Visual indicator hidden for dialog/menu")
                return True
            except Exception as e:
                self.logger.error(f"Error hiding visual indicator: {e}")
        return False
    
    def show_indicator(self) -> bool:
        """
        Show the visual indicator if it was hidden and no menu is active.
        
        Returns:
            True if indicator was shown, False otherwise
        """
        # Don't show the indicator if a menu is active
        if self.menu_active:
            self.logger.debug("Not showing indicator because menu is active")
            return False
        
        if (self.visual_indicator and 
            hasattr(self.visual_indicator, 'show_window') and 
            self.hidden_for_menu):
            try:
                self.visual_indicator.show_window()
                self.hidden_for_menu = False
                self.logger.debug("Visual indicator shown after dialog/menu")
                return True
            except Exception as e:
                self.logger.error(f"Error showing visual indicator: {e}")
        return False
    
    def set_menu_active(self, active: bool) -> None:
        """Set the menu active state."""
        self.menu_active = active
        self.logger.debug(f"Menu active state set to: {active}")
        
        if active:
            # Hide indicator when menu becomes active
            self.hide_indicator()
        else:
            # Show indicator when menu becomes inactive (only if it was hidden for menu)
            if self.hidden_for_menu:
                self.show_indicator()
    
    def show_dialog_with_indicator_handling(self, dialog_func: Callable, *args, **kwargs) -> Any:
        """
        Show a dialog with proper indicator hiding/showing.
        
        Args:
            dialog_func: Function to call (like QtWidgets.QMessageBox.information)
            *args, **kwargs: Arguments to pass to the dialog function
            
        Returns:
            Whatever the dialog function returns
        """
        # Hide indicator
        was_hidden = self.hide_indicator()
        
        try:
            # Show dialog
            result = dialog_func(*args, **kwargs)
            return result
        finally:
            # Always restore indicator if it was active
            if was_hidden:
                self.show_indicator()


# Global instance
indicator_manager = IndicatorManager()


def hide_indicator() -> bool:
    """Global function to hide the visual indicator."""
    return indicator_manager.hide_indicator()


def show_indicator() -> bool:
    """Global function to show the visual indicator."""
    return indicator_manager.show_indicator()


def set_menu_active(active: bool) -> None:
    """Global function to set menu active state."""
    indicator_manager.set_menu_active(active)


def show_dialog_with_indicator_handling(dialog_func: Callable, *args, **kwargs) -> Any:
    """Global function to show a dialog with proper indicator handling."""
    return indicator_manager.show_dialog_with_indicator_handling(dialog_func, *args, **kwargs)


def set_indicator(indicator: VisualIndicator) -> None:
    """Global function to set the active indicator."""
    indicator_manager.set_indicator(indicator) 