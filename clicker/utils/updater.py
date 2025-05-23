"""
Auto-update functionality for the Clicker application.

This module handles checking for updates from GitHub and optionally
installing them automatically or with user consent.
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Tuple, NamedTuple

import requests
from packaging.version import parse as parse_version
from PyQt5 import QtWidgets, QtCore

from clicker.utils.exceptions import UpdateError


class UpdateInfo(NamedTuple):
    """Information about an available update."""
    is_available: bool
    latest_version: str
    current_version: str
    download_url: Optional[str] = None
    release_notes: Optional[str] = None


class AutoUpdater:
    """
    Handles automatic update checking and installation.
    
    Features:
    - Check for updates from GitHub releases
    - Download and install updates automatically or with user consent
    - Progress reporting during download
    - Graceful error handling with fallbacks
    """
    
    def __init__(
        self, 
        current_version: str,
        github_owner: str = "hildolfr",
        github_repo: str = "clicker"
    ):
        self.current_version = current_version
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.logger = logging.getLogger(__name__)
        
        # API endpoint for latest release
        self.api_url = f"https://api.github.com/repos/{github_owner}/{github_repo}/releases/latest"
    
    def check_for_updates(self, timeout: float = 10.0) -> UpdateInfo:
        """
        Check for available updates.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            UpdateInfo: Information about available updates
            
        Raises:
            UpdateError: If the update check fails
        """
        try:
            self.logger.info(f"Checking for updates (current: {self.current_version})")
            
            # Make request to GitHub API with explicit timeout
            response = requests.get(
                self.api_url,
                timeout=timeout,
                headers={'User-Agent': f'Clicker/{self.current_version}'}
            )
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip("v")
            
            self.logger.info(f"Latest version available: {latest_version}")
            
            # Compare versions
            is_newer = parse_version(latest_version) > parse_version(self.current_version)
            
            if not is_newer:
                return UpdateInfo(
                    is_available=False,
                    latest_version=latest_version,
                    current_version=self.current_version
                )
            
            # Find executable download URL
            download_url = None
            for asset in release_data["assets"]:
                if asset["name"].endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break
            
            if not download_url:
                self.logger.warning("Update available but no executable found in release assets")
                return UpdateInfo(
                    is_available=True,
                    latest_version=latest_version,
                    current_version=self.current_version,
                    download_url=None
                )
            
            return UpdateInfo(
                is_available=True,
                latest_version=latest_version,
                current_version=self.current_version,
                download_url=download_url,
                release_notes=release_data.get("body", "")
            )
            
        except requests.exceptions.RequestException as e:
            raise UpdateError(f"Network error during update check: {e}")
        except Exception as e:
            raise UpdateError(f"Failed to check for updates: {e}")
    
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
            
            # Create update dialog
            msg = QtWidgets.QMessageBox(parent)
            msg.setIcon(QtWidgets.QMessageBox.Question)
            msg.setWindowTitle("Update Available")
            msg.setText(f"A new version ({update_info.latest_version}) is available.")
            msg.setInformativeText("Would you like to update now?")
            
            if update_info.release_notes:
                msg.setDetailedText(f"Release Notes:\n{update_info.release_notes}")
            
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
            
            # Show dialog with indicator handling
            result = show_dialog_with_indicator_handling(msg.exec)
            
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
    
    def download_and_install(
        self, 
        update_info: UpdateInfo, 
        parent: QtWidgets.QWidget = None
    ) -> bool:
        """
        Download and install an update.
        
        Args:
            update_info: Update information
            parent: Parent widget for progress dialog
            
        Returns:
            bool: True if update was initiated successfully
        """
        if not update_info.download_url:
            raise UpdateError("No download URL available")
        
        try:
            from clicker.ui.indicators.manager import show_dialog_with_indicator_handling
            
            self.logger.info(f"Starting update to version {update_info.latest_version}")
            
            # Create progress dialog - but don't use indicator handling to avoid conflicts
            progress = QtWidgets.QProgressDialog(
                "Downloading update...", 
                "Cancel", 
                0, 100, 
                parent
            )
            progress.setWindowTitle(f"Updating to version {update_info.latest_version}")
            progress.setWindowModality(QtCore.Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            
            # Force immediate display
            QtWidgets.QApplication.processEvents()
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="clicker_update_")
            temp_file = Path(temp_dir) / f"Clicker_v{update_info.latest_version}.exe"
            
            # Download with timeout and progress updates
            try:
                # Use timeout for the download request too
                response = requests.get(
                    update_info.download_url, 
                    stream=True,
                    timeout=(10, 30)  # 10s connect, 30s read timeout
                )
                response.raise_for_status()
                
                # Get total size, but don't rely on it
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                self.logger.info(f"Download starting - Total size: {total_size} bytes")
                
                # Set initial status based on whether we know the size
                if total_size > 0:
                    progress.setLabelText(f"Downloading update... (0 / {total_size // 1024} KB)")
                else:
                    progress.setLabelText("Downloading update... (size unknown)")
                
                QtWidgets.QApplication.processEvents()
                
                with open(temp_file, 'wb') as f:
                    chunk_count = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if progress.wasCanceled():
                            self.logger.info("Update download canceled by user")
                            progress.close()
                            # Clean up temp files
                            try:
                                temp_file.unlink(missing_ok=True)
                                Path(temp_dir).rmdir()
                            except:
                                pass
                            return False
                        
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            chunk_count += 1
                            
                            # Update progress every 10 chunks to avoid UI lag
                            if chunk_count % 10 == 0:
                                if total_size > 0:
                                    percent = min(99, int(downloaded * 100 / total_size))
                                    progress.setValue(percent)
                                    progress.setLabelText(
                                        f"Downloading update... ({downloaded // 1024} / {total_size // 1024} KB)"
                                    )
                                else:
                                    progress.setLabelText(
                                        f"Downloading update... ({downloaded // 1024} KB)"
                                    )
                                QtWidgets.QApplication.processEvents()
                
                # Ensure we show 100% completion
                progress.setValue(100)
                QtWidgets.QApplication.processEvents()
                
                self.logger.info(f"Download completed: {temp_file}")
                
            except Exception as e:
                progress.close()
                # Clean up temp files
                try:
                    temp_file.unlink(missing_ok=True)
                    Path(temp_dir).rmdir()
                except:
                    pass
                raise UpdateError(f"Download failed: {e}")
            
            # Close download progress
            progress.close()
            
            # Execute the update
            self._execute_update(temp_file, update_info.latest_version)
            
            return True
            
        except UpdateError:
            raise
        except Exception as e:
            raise UpdateError(f"Update installation failed: {e}")
    
    def _create_update_script(self, new_exe_path: Path, version: str) -> Path:
        """
        Create a batch script that will replace the current executable.
        
        Args:
            new_exe_path: Path to the new executable
            version: Version being installed
            
        Returns:
            Path: Path to the created update script
        """
        current_exe = Path(sys.executable)
        if not current_exe.name.endswith('.exe'):
            # If running from Python interpreter, use the main.py location
            current_exe = Path(__file__).parent.parent.parent / "main.py"
            if current_exe.exists():
                # Create a script that overwrites the entire directory
                current_exe = current_exe.parent / "Clicker.exe"
        
        script_content = f'''@echo off
echo Starting Clicker update to version {version}...
timeout /t 3 /nobreak >nul

echo Waiting for Clicker to close...
:wait_loop
tasklist /FI "IMAGENAME eq Clicker.exe" 2>NUL | find /I /N "Clicker.exe">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak >nul
    goto wait_loop
)

echo Replacing executable...
copy /Y "{new_exe_path}" "{current_exe}"
if errorlevel 1 (
    echo Error: Failed to replace executable
    pause
    exit /b 1
)

echo Cleaning up temporary files...
del /Q "{new_exe_path}" 2>nul
rmdir "{new_exe_path.parent}" 2>nul

echo Starting updated Clicker...
start "" "{current_exe}"

echo Update completed successfully!
del "%~f0"
'''
        
        script_path = new_exe_path.parent / "update_clicker.bat"
        
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)
            self.logger.info(f"Created update script: {script_path}")
            return script_path
        except Exception as e:
            raise UpdateError(f"Failed to create update script: {e}")
    
    def _execute_update(self, new_exe_path: Path, version: str) -> None:
        """
        Execute the update by running the update script.
        
        Args:
            new_exe_path: Path to the new executable
            version: Version being installed
        """
        try:
            script_path = self._create_update_script(new_exe_path, version)
            
            # Run the update script in a detached process
            subprocess.Popen(
                [str(script_path)],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS
            )
            
            self.logger.info(f"Update script started: {script_path}")
            
            # Give the script a moment to start
            import time
            time.sleep(1)
            
            # Exit the current application
            self.logger.info("Exiting application for update...")
            
            # Use QApplication.quit() if available, otherwise sys.exit()
            try:
                app = QtWidgets.QApplication.instance()
                if app:
                    app.quit()
                else:
                    sys.exit(0)
            except:
                sys.exit(0)
                
        except Exception as e:
            raise UpdateError(f"Failed to execute update: {e}")


class UpdateChecker:
    """
    Convenience class for checking updates without UI interaction.
    """
    
    def __init__(self, updater: AutoUpdater):
        self.updater = updater
        self.logger = logging.getLogger(__name__)
    
    def check_silent(self) -> Optional[UpdateInfo]:
        """
        Check for updates silently without any UI.
        
        Returns:
            UpdateInfo if an update is available, None otherwise
        """
        try:
            update_info = self.updater.check_for_updates()
            return update_info if update_info.is_available else None
        except Exception as e:
            self.logger.error(f"Silent update check failed: {e}")
            return None
    
    def check_and_auto_install(self) -> bool:
        """
        Check for updates and install automatically if available.
        
        Returns:
            bool: True if update was initiated, False otherwise
        """
        try:
            update_info = self.updater.check_for_updates()
            
            if update_info.is_available and update_info.download_url:
                return self.updater.download_and_install(update_info)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Auto-update failed: {e}")
            return False 