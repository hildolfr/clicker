"""
Main Clicker Application.

This module provides the main application class that coordinates all
components with proper dependency injection and clean architecture.
"""

from __future__ import annotations

import logging
import sys
import os
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import time
import threading

# PyQt5 imports
from PyQt5 import QtWidgets, QtCore, QtGui

# Clicker imports
from clicker.config.manager import ConfigManager
from clicker.config.models import AppSettings, KeystrokeConfig
from clicker.core.automation import AutomationEngine, AutomationState
from clicker.core.keystrokes import WindowsKeystrokeSender
from clicker.core.events import EventSystem, AutomationEvent, EventType
from clicker.ui.gui.system_tray import SystemTrayManager
from clicker.ui.indicators import VisualIndicator, PygameIndicator, GDIIndicator, IndicatorManager
from clicker.ui.indicators.base import IndicatorState
from clicker.ui.indicators.manager import set_indicator, show_dialog_with_indicator_handling, hide_indicator
from clicker.utils.exceptions import ClickerError, ConfigurationError
from clicker.system.hotkeys import HotkeyManager
# File watching replaced with timer-based reload
# from clicker.utils.file_watcher import FileWatcher
from clicker.utils.file_watcher import FileWatcher
from clicker.utils.updater import AutoUpdater, UpdateChecker
from clicker.system.admin import AdminChecker
from clicker.system.singleton import SingletonManager


class ClickerApp:
    """
    Main application class with dependency injection and clean architecture.
    
    This replaces the monolithic main() function from the original code
    with a clean, testable architecture.
    """
    
    # Application version for auto-updater
    VERSION = "2.2.2"
    
    def __init__(self, config_dir: Optional[Path] = None):
        # Initialize logger first, before any other operations
        self.logger = logging.getLogger(__name__)
        
        # Core dependencies - dependency injection pattern
        self.config_manager = ConfigManager(config_dir)
        self.event_system = EventSystem()
        self.keystroke_sender = WindowsKeystrokeSender()
        self.automation_engine = AutomationEngine(self.keystroke_sender)
        
        # System utilities
        self.admin_checker = AdminChecker()
        self.singleton_manager = SingletonManager()
        
        # Initialize hotkey manager (may fail if keyboard library unavailable)
        try:
            self.hotkey_manager = HotkeyManager(self.event_system)
        except ImportError as e:
            # Use print as fallback if logger not fully configured yet
            try:
                self.logger.warning(f"Hotkey manager unavailable: {e}")
            except:
                print(f"Warning: Hotkey manager unavailable: {e}")
            self.hotkey_manager = None
        
        # Auto-update components
        self.auto_updater = AutoUpdater(self.VERSION)
        self.update_checker = UpdateChecker(self.auto_updater)
        
        # UI components  
        self.visual_indicator: Optional[VisualIndicator] = None
        self.file_watcher: Optional[FileWatcher] = None
        self.tray_manager: Optional[SystemTrayManager] = None
        
        # Qt Application
        self.qt_app: Optional[QtWidgets.QApplication] = None
        
        # State
        self._running = False
        self._shutdown_requested = False
        
        # Wire up event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers for component communication."""
        # Configuration change events
        self.config_manager.register_change_callback(self._on_config_changed)
        
        # Automation state change events  
        self.automation_engine.register_state_callback(self._on_automation_state_changed)
        
        # System events
        self.event_system.subscribe(EventType.SHUTDOWN_REQUESTED, self._on_shutdown_requested)
    
    def run(self) -> int:
        """
        Main application run loop.
        
        Returns:
            int: Exit code (0 for success, non-zero for error)
        """
        startup_completed = False
        try:
            # Initialize logging first
            self._setup_logging()
            self.logger.info(f"Starting Clicker application v{self.VERSION}")
            
            # Check for singleton first, before any Qt operations
            if not self._check_singleton():
                return 1  # Another instance is running
            
            # Initialize Qt application
            if not self._initialize_qt():
                self.logger.error("Failed to initialize Qt application")
                return 1
            
            # Hide console window on Windows
            self._hide_console_window()
            
            # Load configuration
            self._load_configuration()
            
            # Set up config reload timer instead of file watching
            self._setup_file_watcher()
            
            # Check admin privileges (only after Qt is ready)
            self._check_admin_privileges()
            
            # Initialize subsystems
            self._initialize_subsystems()
            
            # Create visual indicator
            self._create_visual_indicator()
            
            # Create system tray
            self._create_system_tray()
            
            # Set up hotkeys
            self._setup_hotkeys()
            
            # Check for updates if enabled
            self._check_for_updates()
            
            startup_completed = True
            self.logger.info("Application startup completed successfully")
            
            # Start the Qt event loop
            self._running = True
            exit_code = self.qt_app.exec_()
            
            self.logger.info(f"Application exiting with code: {exit_code}")
            return exit_code
            
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
            return 0
        except SystemExit as e:
            # Handle explicit sys.exit() calls
            self.logger.info(f"Application exit requested with code: {e.code}")
            return e.code if e.code is not None else 0
        except Exception as e:
            if startup_completed:
                self.logger.error(f"Runtime error: {e}", exc_info=True)
                return 1
            else:
                self.logger.error(f"Startup error: {e}", exc_info=True)
                # For startup errors, try to show a user-friendly message
                self._show_startup_error(e)
                return 1
        finally:
            self._shutdown()
    
    def _setup_logging(self) -> None:
        """Set up application logging with rotation and cleanup."""
        import logging.handlers
        
        # Get logging configuration from settings
        try:
            settings = self.config_manager.settings
            # Use INFO level instead of DEBUG to reduce log spam
            log_level = logging.INFO if settings.logging_enabled else logging.WARNING
            retention_days = settings.log_retention_days
        except:
            # Fallback if config not loaded yet
            log_level = logging.INFO
            retention_days = 7
        
        # Calculate max log file size (1.75MB as requested)
        max_log_size = int(1.75 * 1024 * 1024)  # 1.75MB in bytes
        backup_count = 5  # Keep 5 rotated log files
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create rotating file handler with improved error handling
        file_handler = None
        try:
            # Try to close any existing file handlers to avoid conflicts
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                if isinstance(handler, (logging.FileHandler, logging.handlers.RotatingFileHandler)):
                    handler.close()
                    root_logger.removeHandler(handler)
            
            # Try rotating handler first
            file_handler = logging.handlers.RotatingFileHandler(
                'clicker.log',
                maxBytes=max_log_size,
                backupCount=backup_count,
                encoding='utf-8',
                delay=True  # Don't open file until first write
            )
            file_handler.setFormatter(formatter)
            
        except (PermissionError, OSError) as e:
            # If rotation fails, try a simple file handler as fallback
            self.logger.warning(f"Could not create rotating log handler ({e}), trying simple file handler")
            try:
                file_handler = logging.FileHandler('clicker.log', encoding='utf-8')
                file_handler.setFormatter(formatter)
            except (PermissionError, OSError) as e2:
                # If we can't even create a file handler, use console only
                self.logger.warning(f"Could not create file handler ({e2}), using console logging only")
                file_handler = None
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Add handlers
        if file_handler:
            root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Clean up old log files
        try:
            self._cleanup_old_logs(retention_days)
        except Exception as e:
            self.logger.warning(f"Log cleanup failed: {e}")
        
        self.logger.info(f"Logging configured: level={logging.getLevelName(log_level)}, max_size={max_log_size/1024/1024:.2f}MB, retention={retention_days}days")

    def _cleanup_old_logs(self, retention_days: int) -> None:
        """Clean up log files older than the retention period."""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Find all log files (including rotated ones)
            log_files = glob.glob('clicker.log*')
            
            removed_count = 0
            for log_file in log_files:
                try:
                    # Get file modification time
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                    
                    # Remove if older than retention period
                    if file_mtime < cutoff_date:
                        os.remove(log_file)
                        removed_count += 1
                        
                except (OSError, IOError) as e:
                    # Log error but continue with other files
                    print(f"Warning: Could not remove old log file {log_file}: {e}")
            
            if removed_count > 0:
                print(f"Cleaned up {removed_count} old log files (retention: {retention_days} days)")
            
        except Exception as e:
            # Don't let log cleanup failures crash the application
            print(f"Warning: Log cleanup failed: {e}")

    def _check_singleton(self) -> bool:
        """Ensure only one instance is running."""
        if not self.singleton_manager.acquire_lock():
            # Don't use Qt dialogs before Qt is initialized
            print("Error: Another instance of Clicker is already running.")
            return False
        
        self.logger.info("Singleton lock acquired")
        return True
    
    def _hide_console_window(self) -> None:
        """Hide console window on Windows."""
        if sys.platform == 'win32':
            import ctypes
            kernel32 = ctypes.WinDLL('kernel32')
            user32 = ctypes.WinDLL('user32')
            SW_HIDE = 0
            hWnd = kernel32.GetConsoleWindow()
            if hWnd:
                user32.ShowWindow(hWnd, SW_HIDE)
                self.logger.debug("Console window hidden")
    
    def _initialize_qt(self) -> bool:
        """Initialize Qt application."""
        try:
            # Check if QApplication already exists
            existing_app = QtWidgets.QApplication.instance()
            if existing_app is not None:
                self.qt_app = existing_app
                self.logger.debug("Using existing Qt application instance")
            else:
                self.qt_app = QtWidgets.QApplication(sys.argv)
                self.logger.debug("Created new Qt application instance")
            
            # Configure application behavior
            self.qt_app.setQuitOnLastWindowClosed(False)
            
            # Set application metadata
            self.qt_app.setApplicationName("Clicker")
            self.qt_app.setApplicationVersion(self.VERSION)
            self.qt_app.setOrganizationName("Clicker Team")
            self.qt_app.setApplicationDisplayName("Clicker - Windows Automation Tool")
            
            # Set application icon if available
            icon_path = Path("icon.ico")
            if icon_path.exists():
                self.qt_app.setWindowIcon(QtGui.QIcon(str(icon_path)))
            
            self.logger.info(f"Qt application initialized (version: {self.VERSION})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Qt application: {e}")
            return False
    
    def _load_configuration(self) -> None:
        """Load application configuration."""
        try:
            self.config_manager.load()
            self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration load failed: {e}")
    
    def _check_admin_privileges(self) -> None:
        """Check and potentially request admin privileges."""
        settings = self.config_manager.settings
        
        if not self.admin_checker.is_admin():
            if settings.prompt_for_admin_privileges:
                self.logger.warning("Application is not running with administrator privileges")
                
                # Hide GDI indicator before showing admin dialog
                hide_indicator()
                
                # Use the AdminChecker's unified dialog instead of duplicating
                if self.admin_checker.request_admin_restart():
                    # The request_admin_restart will handle sys.exit() if user accepts
                    pass
            else:
                self.logger.info("Application is not running with administrator privileges (prompts disabled)")
        else:
            self.logger.info("Application is running with administrator privileges")
    
    def _initialize_subsystems(self) -> None:
        """Initialize all subsystems."""
        try:
            # Configure automation engine
            keystrokes = self.config_manager.get_enabled_keystrokes()
            settings = self.config_manager.settings
            
            self.automation_engine.configure(keystrokes, settings)
            
            self.logger.info("Subsystems initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize subsystems: {e}")
            raise ClickerError(f"Subsystem initialization failed: {e}")
    
    def _create_visual_indicator(self) -> None:
        """Create the visual indicator based on settings."""
        try:
            settings = self.config_manager.settings
            
            if settings.indicator_type.value.lower() == 'pygame':
                self.visual_indicator = PygameIndicator()
            else:
                self.visual_indicator = GDIIndicator()
            
            self.visual_indicator.start()
            
            # Register the indicator with the global manager
            set_indicator(self.visual_indicator)
            
            self.logger.info(f"Visual indicator created: {type(self.visual_indicator).__name__}")
            
        except Exception as e:
            self.logger.error(f"Failed to create visual indicator: {e}")
            show_dialog_with_indicator_handling(
                QtWidgets.QMessageBox.warning,
                None,
                "Visual Indicator Error", 
                f"Failed to initialize visual indicator: {e}\n\nThe application will work without a visual indicator."
            )
    
    def _create_system_tray(self) -> None:
        """Create and configure the system tray."""
        try:
            # Create tray manager
            self.tray_manager = SystemTrayManager(self.VERSION)
            
            # Set up callbacks
            callbacks = {
                'toggle': self._toggle_automation,
                'reload': self._reload_configuration,
                'open_file': self._open_file,
                'check_updates': self._check_updates_manual,
                'quit': self._request_shutdown
            }
            self.tray_manager.set_callbacks(callbacks)
            
            # Initialize the system tray
            if not self.tray_manager.initialize():
                raise ClickerError("Failed to initialize system tray")
            
            self.logger.info("System tray created successfully")
            
            # Show new user dialog if this is the first run
            self._show_new_user_dialog_if_needed()
            
        except Exception as e:
            self.logger.error(f"Failed to create system tray: {e}")
            raise ClickerError(f"System tray creation failed: {e}")
    
    def _is_new_user(self) -> bool:
        """
        Simplified new user detection without requiring extra files.
        User is considered new if both settings.json and keystrokes.txt don't exist.
        """
        settings_exists = self.config_manager.settings_file.exists()
        keystrokes_exists = self.config_manager.keystrokes_file.exists()
        
        # New user if neither config file exists initially
        # This is checked before the files are created by ConfigManager.load()
        return not (settings_exists and keystrokes_exists)
    
    def _show_new_user_dialog_if_needed(self) -> None:
        """Show a helpful dialog for new users, but only if actually needed."""
        # Simple detection: if we just created default files, user is likely new
        # But don't show dialog if user has existing config files
        try:
            settings = self.config_manager.settings
            
            # Only show if both files were missing (indicating truly new user)
            # We detect this by checking if we're using all default values
            if (settings.toggle_key == "~" and  # Default toggle key
                len(self.config_manager.keystrokes) <= 3 and  # Only default keystrokes
                all(ks.description.startswith("Example") for ks in self.config_manager.keystrokes)):
                
                self.logger.info("New user detected, showing welcome dialog")
                
                # Hide GDI indicator during dialog
                hide_indicator()
                
                # Show welcome dialog
                show_dialog_with_indicator_handling(
                    QtWidgets.QMessageBox.information,
                    None,
                    "Welcome to Clicker!",
                    f"Clicker is now running in the system tray.\n\n"
                    f"• Press '{settings.toggle_key}' to toggle automation on/off\n"
                    f"• Right-click the tray icon for more options\n"
                    f"• Edit keystrokes.txt to customize your automation\n\n"
                    f"Tip: You can disable these startup messages in settings.json"
                )
                
        except Exception as e:
            self.logger.error(f"Error checking new user status: {e}")
            # Don't show dialog if we can't determine user status
    
    def _setup_hotkeys(self) -> None:
        """Set up global hotkeys."""
        if not self.hotkey_manager:
            self.logger.warning("Hotkey manager not available - skipping hotkey setup")
            return
            
        try:
            settings = self.config_manager.settings
            # Register all tilde combinations instead of just the configured toggle_key
            self.hotkey_manager.register_tilde_combinations("toggle", self._toggle_automation)
            self.logger.info(f"Tilde combination hotkeys registered for toggle")
            
        except Exception as e:
            self.logger.error(f"Failed to set up hotkeys: {e}")
            # Non-fatal error - continue without hotkeys
    
    def _setup_file_watcher(self) -> None:
        """Set up file watching for configuration changes."""
        try:
            self.file_watcher = FileWatcher(watch_directory=self.config_manager.config_dir)
            self.file_watcher.start_watching(
                files_to_watch=["settings.json", "keystrokes.txt"],
                callback=self._on_config_files_changed
            )
            self.logger.info("File watching for settings.json and keystrokes.txt started.")
        except Exception as e:
            self.logger.error(f"Failed to set up file watcher: {e}")
            # Non-fatal error - continue without file watching
    
    def _on_config_files_changed(self, filename: str) -> None:
        """Callback for when a watched configuration file changes."""
        self.logger.info(f"Configuration file {filename} changed, attempting to reload.")
        try:
            # Stop automation if running
            was_running = self.automation_engine.state == AutomationState.RUNNING
            if was_running:
                self.automation_engine.stop()
            
            # Reload configuration from the manager
            # The config_manager.load() should ideally handle which file to reload
            # or reload all. For now, assume it reloads everything necessary.
            self.config_manager.load()
            
            # Reconfigure automation engine with new settings
            keystrokes = self.config_manager.get_enabled_keystrokes()
            settings = self.config_manager.settings
            self.automation_engine.configure(keystrokes, settings)
            
            # Update hotkeys
            if self.hotkey_manager:
                self.hotkey_manager.unregister_all()
                self.hotkey_manager.register_tilde_combinations("toggle", self._toggle_automation)
            
            # Restart automation if it was running
            if was_running:
                self.automation_engine.start()
            
            self.logger.info(f"Configuration changes from {filename} applied successfully.")
            # Notify listeners that config has changed (e.g. UI)
            self.event_system.publish(AutomationEvent(EventType.CONFIG_CHANGED, {"filename": filename}))

        except Exception as e:
            self.logger.error(f"Error reloading configuration after change in {filename}: {e}", exc_info=True)
            # Optionally, show a dialog to the user
            # show_dialog_with_indicator_handling(
            #     QtWidgets.QMessageBox.warning,
            #     None,
            #     "Configuration Reload Error",
            #     f"Failed to reload configuration after changes to {filename}:\n{e}"
            # )
    
    def _check_for_updates(self) -> None:
        """Check for updates on startup if enabled."""
        try:
            settings = self.config_manager.settings
            
            if settings.check_updates_on_startup:
                self.logger.info("Checking for updates on startup")
                
                # Use a timer to check after UI is ready
                QtCore.QTimer.singleShot(2000, self._startup_update_check)
            else:
                self.logger.info("Startup update check disabled in settings")
                
        except Exception as e:
            self.logger.error(f"Error setting up startup update check: {e}")
    
    def _startup_update_check(self) -> None:
        """Perform startup update check."""
        try:
            settings = self.config_manager.settings
            
            if settings.auto_install_updates:
                # Auto-install if enabled
                self.update_checker.check_and_auto_install()
            else:
                # Silent check, but don't show dialogs
                update_info = self.update_checker.check_silent()
                if update_info and update_info.is_available:
                    self.logger.info(f"Update available: {update_info.latest_version}")
                    
        except Exception as e:
            self.logger.error(f"Startup update check failed: {e}")
    
    def _check_updates_manual(self) -> None:
        """Manual update check triggered by user."""
        try:
            self.auto_updater.check_and_prompt_user(parent=None)
        except Exception as e:
            self.logger.error(f"Manual update check failed: {e}")
            show_dialog_with_indicator_handling(
                QtWidgets.QMessageBox.warning,
                None,
                "Update Check Failed",
                f"Failed to check for updates: {e}"
            )
    
    def _toggle_automation(self) -> None:
        """Toggle automation state."""
        try:
            current_state = self.automation_engine.state
            
            if current_state == AutomationState.STOPPED:
                self.automation_engine.start()
                self.logger.info("Automation started")
            else:
                self.automation_engine.stop()
                self.logger.info("Automation stopped")
                
        except Exception as e:
            self.logger.error(f"Failed to toggle automation: {e}")
            show_dialog_with_indicator_handling(
                QtWidgets.QMessageBox.critical,
                None,
                "Automation Error",
                f"Failed to toggle automation: {e}"
            )
    
    def _reload_configuration(self) -> None:
        """Reload configuration from files."""
        try:
            # Stop automation
            was_running = self.automation_engine.state == AutomationState.RUNNING
            if was_running:
                self.automation_engine.stop()
            
            # Reload configuration
            self.config_manager.reload()
            
            # Reconfigure automation engine
            keystrokes = self.config_manager.get_enabled_keystrokes()
            settings = self.config_manager.settings
            self.automation_engine.configure(keystrokes, settings)
            
            # Update hotkeys
            if self.hotkey_manager:
                self.hotkey_manager.unregister_all()
                self.hotkey_manager.register_tilde_combinations("toggle", self._toggle_automation)
            
            # Restart automation if it was running
            if was_running:
                self.automation_engine.start()
            
            self.logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            show_dialog_with_indicator_handling(
                QtWidgets.QMessageBox.critical,
                None,
                "Reload Error", 
                f"Failed to reload configuration: {e}"
            )
    
    def _open_file(self, filename: str) -> None:
        """Open a file with the default system application."""
        try:
            file_path = Path(filename).resolve()
            
            if sys.platform == 'win32':
                os.startfile(str(file_path))
            elif sys.platform == 'darwin':
                os.system(f'open "{file_path}"')
            else:
                os.system(f'xdg-open "{file_path}"')
                
            self.logger.info(f"Opened file: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to open file {filename}: {e}")
            show_dialog_with_indicator_handling(
                QtWidgets.QMessageBox.critical,
                None,
                "File Error",
                f"Could not open {filename}: {e}"
            )
    
    def _on_config_changed(self, change_type: str) -> None:
        """Handle configuration change events."""
        self.logger.info(f"Configuration changed: {change_type}")
        # Configuration changes are handled by the reload mechanism
    
    def _on_automation_state_changed(self, old_state: AutomationState, new_state: AutomationState) -> None:
        """Handle automation state change events."""
        self.logger.info(f"Automation state changed: {old_state} -> {new_state}")
        
        # Update visual indicator
        if self.visual_indicator:
            if new_state == AutomationState.RUNNING:
                self.visual_indicator.set_state(IndicatorState.ACTIVE)
            else:
                self.visual_indicator.set_state(IndicatorState.INACTIVE)
        
        # Update tray status
        if self.tray_manager:
            self.tray_manager.update_state(new_state)

    def _on_shutdown_requested(self, event: AutomationEvent) -> None:
        """Handle shutdown request events."""
        self.logger.info("Shutdown requested via event system")
        self._request_shutdown()

    def _request_shutdown(self) -> None:
        """Request application shutdown."""
        if not self._shutdown_requested:
            self._shutdown_requested = True
            self.logger.info("Shutdown requested")
            if self.qt_app:
                # Schedule graceful shutdown to happen after current event processing
                QtCore.QTimer.singleShot(0, self._initiate_qt_shutdown)

    def _initiate_qt_shutdown(self) -> None:
        """Initiate graceful Qt application shutdown."""
        try:
            self.logger.info("Initiating Qt application shutdown")
            
            # Perform pre-shutdown cleanup
            self._shutdown()
            
            # Now safely quit the Qt application
            if self.qt_app:
                # Set a maximum shutdown timeout
                shutdown_timer = QtCore.QTimer()
                shutdown_timer.setSingleShot(True)
                shutdown_timer.timeout.connect(self._force_qt_shutdown)
                shutdown_timer.start(5000)  # 5 second timeout
                
                # Attempt graceful shutdown
                self.qt_app.quit()
                
        except Exception as e:
            self.logger.error(f"Error during Qt shutdown initiation: {e}")
            self._force_qt_shutdown()

    def _force_qt_shutdown(self) -> None:
        """Force Qt application shutdown if graceful shutdown fails."""
        self.logger.warning("Forcing Qt application shutdown due to timeout")
        try:
            if self.qt_app:
                # Force process exit if Qt doesn't shut down gracefully
                import os
                os._exit(0)
        except Exception as e:
            self.logger.error(f"Error during forced shutdown: {e}")

    def _shutdown(self) -> None:
        """Gracefully shut down the application."""
        if self._shutdown_requested:
            self.logger.info("Shutdown already in progress.")
            return
            
        self._shutdown_requested = True
        self.logger.info("Initiating application shutdown...")

        if self.file_watcher:
            self.logger.debug("Stopping file watcher...")
            self.file_watcher.stop_watching()
            self.logger.info("File watcher stopped.")

        # Stop automation if running
        if self.automation_engine and self.automation_engine.state != AutomationState.STOPPED:
            self.logger.debug("Stopping automation engine...")
            self.automation_engine.stop()
        
        if self.visual_indicator:
            try:
                self.visual_indicator.stop()
            except Exception as e:
                self.logger.error(f"Error stopping visual indicator: {e}")
        
        # Unregister hotkeys
        if self.hotkey_manager:
            try:
                self.hotkey_manager.unregister_all()
            except Exception as e:
                self.logger.error(f"Error unregistering hotkeys: {e}")
        
        # Clean up system tray
        if self.tray_manager:
            try:
                self.tray_manager.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up system tray: {e}")
        
        # Release singleton lock
        if self.singleton_manager:
            try:
                self.singleton_manager.release_lock()
            except Exception as e:
                self.logger.error(f"Error releasing singleton lock: {e}")
        
        self.logger.info("Application shutdown completed")
    
    def _show_startup_error(self, e: Exception) -> None:
        """Show a user-friendly startup error message."""
        try:
            # Only show dialog if Qt is available
            if self.qt_app is not None:
                show_dialog_with_indicator_handling(
                    QtWidgets.QMessageBox.critical,
                    None,
                    "Startup Error",
                    f"An error occurred during startup: {e}\n\nPlease check the logs for more details."
                )
            else:
                # Fallback to console if Qt not available
                print(f"Startup Error: {e}")
                print("Please check the logs for more details.")
        except Exception as dialog_error:
            # If even the error dialog fails, just log it
            print(f"Startup Error: {e}")
            print(f"Could not show error dialog: {dialog_error}")
            print("Please check the logs for more details.")


def main() -> int:
    """
    Application entry point.
    
    Returns:
        int: Exit code
    """
    app = ClickerApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main()) 