"""
Administrator privileges management for Windows.

This module provides functionality to check and request administrator privileges,
which are required for sending keystrokes to elevated applications.
"""

import ctypes
import logging
import sys
from typing import Optional

from PyQt5 import QtWidgets


class AdminChecker:
    """Utility class for checking and managing administrator privileges."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def is_admin(self) -> bool:
        """
        Check if the current process has administrator privileges.
        
        Returns:
            True if running as admin, False otherwise
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            self.logger.error(f"Error checking admin status: {e}")
            return False
    
    def request_admin_restart(self, parent: Optional[QtWidgets.QWidget] = None) -> bool:
        """
        Request admin restart with elevated privileges.
        
        Args:
            parent: Parent widget for the dialog
            
        Returns:
            True if user accepted restart, False if they declined
        """
        return self.show_admin_warning(parent)
    
    def show_admin_warning(self, parent: Optional[QtWidgets.QWidget] = None) -> bool:
        """
        Show warning about admin privileges and offer to restart with elevated privileges.
        
        Args:
            parent: Parent widget for the dialog
            
        Returns:
            True if user accepted restart, False if they declined
        """
        try:
            msg = QtWidgets.QMessageBox(parent)
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setWindowTitle("Administrator Rights Recommended")
            msg.setText("This application will work better with administrator privileges.")
            msg.setInformativeText(
                "Clicker can send keystrokes to more applications when running as administrator.\n\n"
                "Click 'Restart as Admin' to close this window and restart with elevated privileges.\n"
                "Click 'Continue Anyway' to keep using the app without admin rights."
            )
            msg.setDetailedText(
                "When sending keystrokes to applications running with elevated privileges "
                "(like games, system utilities, or other admin-required programs), "
                "Clicker needs to run as administrator too. Without admin rights, keystrokes "
                "may only work with non-elevated applications.\n\n"
                "Note: When you click 'Restart as Admin', this window will close and Windows "
                "may show a User Account Control (UAC) prompt. After you approve it, "
                "Clicker will restart automatically with administrator privileges."
            )
            
            # Create custom buttons to be more explicit
            restart_button = msg.addButton("Restart as Admin", QtWidgets.QMessageBox.AcceptRole)
            continue_button = msg.addButton("Continue Anyway", QtWidgets.QMessageBox.RejectRole)
            msg.setDefaultButton(restart_button)
            
            choice = msg.exec_()
            clicked_button = msg.clickedButton()
            
            if clicked_button == restart_button:
                self.logger.info("User requested restart with admin privileges")
                return self._restart_with_admin()
            else:
                self.logger.info("User declined to restart with admin privileges")
                return False
                
        except Exception as e:
            self.logger.error(f"Error showing admin warning: {e}")
            return False
    
    def _restart_with_admin(self) -> bool:
        """
        Restart the application with administrator privileges.
        
        Returns:
            True if restart was initiated, False if it failed
        """
        try:
            self.logger.info("Initiating restart with admin privileges")
            
            # Show a brief notification that restart is happening
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setWindowTitle("Restarting...")
            msg.setText("Restarting Clicker with administrator privileges...")
            msg.setInformativeText("This window will close automatically.")
            msg.setStandardButtons(QtWidgets.QMessageBox.NoButton)
            msg.show()
            
            # Process events to ensure message shows
            QtWidgets.QApplication.processEvents()
            
            # Brief delay to let user see the message
            import time
            time.sleep(1.5)
            
            # Use ShellExecute with "runas" to restart with admin privileges
            result = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                " ".join(sys.argv), 
                None, 
                1
            )
            
            # Check if ShellExecute was successful (result > 32 means success)
            if result > 32:
                self.logger.info("Admin restart initiated successfully - exiting current instance")
                # Exit current non-admin instance
                sys.exit(0)
            else:
                self.logger.error(f"ShellExecute failed with result: {result}")
                msg.close()
                raise Exception(f"ShellExecute returned error code: {result}")
                
        except Exception as e:
            self.logger.error(f"Failed to restart with admin privileges: {e}")
            QtWidgets.QMessageBox.critical(
                None, 
                "Error", 
                f"Failed to restart with admin privileges: {e}\n\n"
                "Continuing without admin privileges."
            )
            return False


def request_admin_privileges(parent: Optional[QtWidgets.QWidget] = None) -> bool:
    """
    Convenience function to check admin privileges and request them if needed.
    
    Args:
        parent: Parent widget for dialogs
        
    Returns:
        True if admin privileges are available, False otherwise
    """
    checker = AdminChecker()
    
    if checker.is_admin():
        return True
    
    # Show warning and offer to restart with admin privileges
    return checker.show_admin_warning(parent) 