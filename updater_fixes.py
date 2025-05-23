#!/usr/bin/env python3
"""
Clean fixes for updater.py - manually copy these into the actual file.
"""

# FIX 1: Update check_and_prompt_user method (replace the malformed method around line 123)
updater_fix = '''
    def check_and_prompt_user(self, parent: QtWidgets.QWidget = None) -> bool:
        """
        Check for updates and prompt user if one is available.
        
        Args:
            parent: Parent widget for dialogs
            
        Returns:
            bool: True if update was initiated, False otherwise
        """
        try:
            from clicker.ui.indicators.manager import show_dialog_with_indicator_handling
            
            update_info = self.check_for_updates()
            
            if not update_info.is_available:
                show_dialog_with_indicator_handling(
                    QtWidgets.QMessageBox.information,
                    parent,
                    "No Updates",
                    f"You're running the latest version ({update_info.current_version})."
                )
                return False
            
            if not update_info.download_url:
                show_dialog_with_indicator_handling(
                    QtWidgets.QMessageBox.warning,
                    parent,
                    "Update Available",
                    f"Version {update_info.latest_version} is available, "
                    f"but no executable was found. Please update manually."
                )
                return False
            
            # Show update dialog with indicator handling
            def show_update_dialog():
                msg = QtWidgets.QMessageBox(parent)
                msg.setIcon(QtWidgets.QMessageBox.Question)
                msg.setWindowTitle("Update Available")
                msg.setText(f"A new version ({update_info.latest_version}) is available.")
                msg.setInformativeText("Would you like to update now?")
                
                if update_info.release_notes:
                    msg.setDetailedText(f"Release Notes:\\n{update_info.release_notes}")
                
                msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
                
                return msg.exec_()
            
            result = show_dialog_with_indicator_handling(show_update_dialog)
            
            if result == QtWidgets.QMessageBox.Yes:
                return self.download_and_install(update_info, parent)
            
            return False
            
        except UpdateError as e:
            self.logger.error(f"Update check failed: {e}")
            show_dialog_with_indicator_handling(
                QtWidgets.QMessageBox.warning,
                parent,
                "Update Check Failed",
                f"Could not check for updates: {e}"
            )
            return False
'''

print("=" * 60)
print("FIXES FOR updater.py")
print("=" * 60)
print()
print("1. Replace the malformed check_and_prompt_user method around line 123 with:")
print(updater_fix)
print()
print("This fix will:")
print("- Use show_dialog_with_indicator_handling for all dialogs")
print("- Prevent the GDI overlay from blocking update dialogs")
print("- Ensure users can see and interact with update prompts") 