"""
System tray interface for the Clicker application.

This module provides a clean interface for system tray functionality,
including icon management, context menus, and user interactions.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from PyQt5 import QtWidgets, QtGui, QtCore

from clicker.core.automation import AutomationState
from clicker.ui.indicators.manager import set_menu_active, hide_indicator


class SystemTrayManager:
    """Manages system tray icon and interactions."""
    
    def __init__(self, app_version: str = "2.0.0"):
        self.app_version = app_version
        self.logger = logging.getLogger(__name__)
        
        # Qt components
        self.tray_icon: Optional[QtWidgets.QSystemTrayIcon] = None
        self.context_menu: Optional[QtWidgets.QMenu] = None
        
        # Menu actions for dynamic updates
        self.status_action: Optional[QtWidgets.QAction] = None
        
        # Callbacks
        self.toggle_callback: Optional[Callable] = None
        self.reload_callback: Optional[Callable] = None
        self.quit_callback: Optional[Callable] = None
        self.open_file_callback: Optional[Callable[[str], None]] = None
        self.check_updates_callback: Optional[Callable] = None
        
        # State
        self.current_state = AutomationState.STOPPED
    
    def initialize(self) -> bool:
        """
        Initialize the system tray icon and menu.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Check if system tray is available
            if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
                self.logger.error("System tray is not available")
                return False
            
            # Create tray icon
            self._create_tray_icon()
            
            # Create context menu
            self._create_context_menu()
            
            # Set up connections
            self._setup_connections()
            
            # Show the tray icon
            self.tray_icon.show()
            
            self.logger.info("System tray initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system tray: {e}")
            return False
    
    def _create_tray_icon(self) -> None:
        """Create the system tray icon."""
        # Load icon
        icon = self._load_icon()
        
        # Create tray icon
        self.tray_icon = QtWidgets.QSystemTrayIcon(icon)
        self.tray_icon.setToolTip(f"Clicker v{self.app_version} - OFF")
    
    def _load_icon(self) -> QtGui.QIcon:
        """Load the application icon."""
        icon_path = Path("icon.ico")
        
        if icon_path.exists():
            icon = QtGui.QIcon(str(icon_path))
            self.logger.debug("Using custom icon.ico")
        else:
            # Fallback to system icon
            icon = QtWidgets.QApplication.instance().style().standardIcon(
                QtWidgets.QStyle.SP_ComputerIcon
            )
            self.logger.debug("Using default system icon")
        
        return icon
    
    def _create_context_menu(self) -> None:
        """Create the context menu for the tray icon."""
        self.context_menu = QtWidgets.QMenu()
        
        # Status action (disabled, shows current state)
        self.status_action = QtWidgets.QAction("Status: OFF", self.context_menu)
        self.status_action.setEnabled(False)
        self.context_menu.addAction(self.status_action)
        
        self.context_menu.addSeparator()
        
        # File actions
        open_keystrokes_action = self.context_menu.addAction("Open keystrokes.txt")
        open_settings_action = self.context_menu.addAction("Open settings.json")
        reload_action = self.context_menu.addAction("Reload configuration")
        open_log_action = self.context_menu.addAction("View log file")
        
        self.context_menu.addSeparator()
        
        # Update action
        check_updates_action = self.context_menu.addAction("Check for updates")
        
        self.context_menu.addSeparator()
        
        # Quit action
        quit_action = self.context_menu.addAction("Quit")
        
        # Connect actions to callbacks
        open_keystrokes_action.triggered.connect(
            lambda: self._open_file_safe("keystrokes.txt")
        )
        open_settings_action.triggered.connect(
            lambda: self._open_file_safe("settings.json")
        )
        open_log_action.triggered.connect(
            lambda: self._open_file_safe("clicker.log")
        )
        reload_action.triggered.connect(self._reload_safe)
        check_updates_action.triggered.connect(self._check_updates_safe)
        quit_action.triggered.connect(self._quit_safe)
        
        # Set up menu signal connections for indicator management
        self.context_menu.aboutToShow.connect(self._on_menu_about_to_show)
        self.context_menu.aboutToHide.connect(self._on_menu_about_to_hide)
        
        # Set context menu
        self.tray_icon.setContextMenu(self.context_menu)
    
    def _setup_connections(self) -> None:
        """Set up signal connections for the tray icon."""
        self.tray_icon.activated.connect(self._on_tray_activated)
    
    def _on_tray_activated(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation events."""
        self.logger.debug(f"Tray activated with reason: {reason}")
        
        # If this is a context menu activation, set menu active flag
        if reason == QtWidgets.QSystemTrayIcon.Context:
            set_menu_active(True)
            self.logger.debug("Tray context menu activated")
        
        # Hide indicator when any interaction with tray happens
        hide_indicator()
        
        # Double-click toggles automation
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            if self.toggle_callback:
                self.toggle_callback()
    
    def _on_menu_about_to_show(self) -> None:
        """Handle menu about to show event."""
        set_menu_active(True)
        hide_indicator()
        self.logger.debug("Context menu about to show - indicator hidden")
    
    def _on_menu_about_to_hide(self) -> None:
        """Handle menu about to hide event."""
        set_menu_active(False)
        self.logger.debug("Context menu about to hide - menu state reset")
    
    def _toggle_safe(self) -> None:
        """Safely call the toggle callback."""
        if self.toggle_callback:
            try:
                self.toggle_callback()
            except Exception as e:
                self.logger.error(f"Error in toggle callback: {e}")
    
    def _reload_safe(self) -> None:
        """Safely call the reload callback."""
        if self.reload_callback:
            try:
                self.reload_callback()
            except Exception as e:
                self.logger.error(f"Error in reload callback: {e}")
    
    def _quit_safe(self) -> None:
        """Safely call the quit callback."""
        if self.quit_callback:
            try:
                self.quit_callback()
            except Exception as e:
                self.logger.error(f"Error in quit callback: {e}")
    
    def _open_file_safe(self, filename: str) -> None:
        """Safely call the open file callback."""
        if self.open_file_callback:
            try:
                self.open_file_callback(filename)
            except Exception as e:
                self.logger.error(f"Error opening file {filename}: {e}")
    
    def _check_updates_safe(self) -> None:
        """Safely call the check updates callback."""
        if self.check_updates_callback:
            try:
                self.check_updates_callback()
            except Exception as e:
                self.logger.error(f"Error checking updates: {e}")
    
    def set_callbacks(self, callbacks: Dict[str, Callable]) -> None:
        """
        Set callback functions for tray actions.
        
        Args:
            callbacks: Dictionary mapping callback names to functions
                Expected keys: 'toggle', 'reload', 'quit', 'open_file', 'check_updates'
        """
        self.toggle_callback = callbacks.get('toggle')
        self.reload_callback = callbacks.get('reload')
        self.quit_callback = callbacks.get('quit')
        self.open_file_callback = callbacks.get('open_file')
        self.check_updates_callback = callbacks.get('check_updates')
    
    def update_state(self, state: AutomationState) -> None:
        """
        Update the tray icon and status text based on automation state.
        
        Args:
            state: Current automation state
        """
        self.current_state = state
        
        if not self.tray_icon or not self.status_action:
            return
        
        # Map states to display text
        state_text_map = {
            AutomationState.STOPPED: "OFF",
            AutomationState.STARTING: "STARTING",
            AutomationState.RUNNING: "ON",
            AutomationState.PAUSED: "PAUSED",
            AutomationState.STOPPING: "STOPPING",
            AutomationState.ERROR: "ERROR"
        }
        
        status_text = state_text_map.get(state, "UNKNOWN")
        
        # Update tooltip
        self.tray_icon.setToolTip(f"Clicker v{self.app_version} - {status_text}")
        
        # Update status action text
        self.status_action.setText(f"Status: {status_text}")
        
        self.logger.debug(f"Updated tray status to: {status_text}")
    
    def show_message(self, title: str, message: str, 
                    icon: QtWidgets.QSystemTrayIcon.MessageIcon = QtWidgets.QSystemTrayIcon.Information,
                    timeout: int = 3000) -> None:
        """
        Show a system tray notification message.
        
        Args:
            title: Message title
            message: Message content
            icon: Message icon type
            timeout: Display timeout in milliseconds
        """
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, timeout)
    
    def hide(self) -> None:
        """Hide the system tray icon."""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def show(self) -> None:
        """Show the system tray icon."""
        if self.tray_icon:
            self.tray_icon.show()
    
    def cleanup(self) -> None:
        """Clean up tray resources."""
        try:
            if self.tray_icon:
                self.tray_icon.hide()
                self.tray_icon = None
            
            if self.context_menu:
                self.context_menu = None
            
            self.logger.debug("System tray cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during tray cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup() 