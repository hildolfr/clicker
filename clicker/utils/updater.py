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
            
            # Make request to GitHub API
            response = requests.get(self.api_url, timeout=timeout)
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
            
            # Create progress dialog with indicator handling
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
            
            # Show progress dialog with indicator handling
            show_dialog_with_indicator_handling(progress.show)
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="clicker_update_")
            temp_file = Path(temp_dir) / f"Clicker_v{update_info.latest_version}.exe"
            
            # Download with progress updates
            response = requests.get(update_info.download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if progress.wasCanceled():
                        self.logger.info("Update download canceled by user")
                        progress.close()
                        return False
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                            progress.setValue(percent)
                            QtWidgets.QApplication.processEvents()
            
            progress.setValue(100)
            progress.setLabelText("Download complete. Installing update...")
            QtWidgets.QApplication.processEvents()
            
            # Create update script
            self._create_update_script(temp_file, update_info.latest_version)
            
            progress.close()
            
            # Show confirmation and execute update
            show_dialog_with_indicator_handling(
                QtWidgets.QMessageBox.information,
                parent,
                "Update Ready",
                f"Update to version {update_info.latest_version} is ready. "
                f"The application will now restart."
            )
            
            # Execute update and exit
            self._execute_update(temp_file, update_info.latest_version)
            return True
            
        except Exception as e:
            self.logger.error(f"Update installation failed: {e}")
            show_dialog_with_indicator_handling(
                QtWidgets.QMessageBox.critical,
                parent,
                "Update Failed",
                f"Failed to install update: {e}"
            )
            return False
    
    def _create_update_script(self, new_exe_path: Path, version: str) -> Path:
        """Create a batch script to handle the update process."""
        # Get current executable path with improved detection
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            current_exe = Path(sys.executable)
        else:
            # Running as Python script - need to find the actual executable
            # This handles the case where we're running from source but need to update an exe
            script_dir = Path(sys.argv[0]).parent.resolve()
            
            # Look for the executable in common locations
            possible_exe_paths = [
                script_dir / "Clicker.exe",  # Same directory as script
                script_dir / "dist" / "Clicker.exe",  # In dist subdirectory
                script_dir.parent / "Clicker.exe",  # Parent directory
                script_dir.parent / "dist" / "Clicker.exe",  # Parent/dist
            ]
            
            # Find the first existing executable
            current_exe = None
            for exe_path in possible_exe_paths:
                if exe_path.exists() and exe_path.suffix.lower() == '.exe':
                    current_exe = exe_path
                    break
            
            # If no executable found, fall back to the script path but warn
            if current_exe is None:
                current_exe = Path(sys.argv[0]).resolve()
                self.logger.warning(
                    f"Could not find executable for update restart, using script path: {current_exe}"
                )
        
        # Ensure we have an absolute path
        current_exe = current_exe.resolve()
        
        # Log the paths for debugging
        self.logger.info(f"Update script will replace: {current_exe}")
        self.logger.info(f"Update script will restart: {current_exe}")
        
        # Validate that target path looks like an executable
        if current_exe.suffix.lower() != '.exe':
            self.logger.warning(
                f"Target path '{current_exe}' is not an executable file. "
                f"Users may experience 'Python missing' errors after update."
            )
        
        # Create update script
        script_path = new_exe_path.parent / "update.bat"
        
        with open(script_path, 'w') as f:
            f.write(f'''@echo off
echo Updating Clicker to version {version}...
echo Target executable: {current_exe}
set TARGET={current_exe}

REM Validate that target is an executable
echo %TARGET% | findstr /i ".exe" >nul
if errorlevel 1 (
    echo ERROR: Target path is not an executable file: %TARGET%
    echo This could cause "Python missing" errors after update.
    echo Please contact support or update manually.
    pause
    exit /b 1
)

timeout /t 2 /nobreak > nul

:retry
echo Copying new executable...
copy /Y "{new_exe_path}" "%TARGET%" > nul
if errorlevel 1 (
    echo Update failed, retrying in 1 second...
    timeout /t 1 /nobreak > nul
    goto retry
)

echo Update successful!
echo Validating updated executable...
if not exist "%TARGET%" (
    echo ERROR: Updated executable not found at %TARGET%
    echo Update may have failed.
    pause
    exit /b 1
)

echo Starting updated application...
start "" "%TARGET%"
if errorlevel 1 (
    echo ERROR: Failed to start updated application.
    echo Please manually run: %TARGET%
    pause
    exit /b 1
)

timeout /t 2 /nobreak > nul
echo Cleaning up temporary files...
rd /s /q "{new_exe_path.parent}"
echo Update process completed successfully.
exit
''')
        
        return script_path
    
    def _execute_update(self, new_exe_path: Path, version: str) -> None:
        """Execute the update process and exit current application."""
        script_path = self._create_update_script(new_exe_path, version)
        
        # Validate the update script was created successfully
        if not script_path.exists():
            raise UpdateError(f"Update script creation failed: {script_path}")
        
        # Validate the new executable exists and is accessible
        if not new_exe_path.exists():
            raise UpdateError(f"Downloaded update file not found: {new_exe_path}")
        
        # Check file size to ensure download completed
        if new_exe_path.stat().st_size < 1024 * 1024:  # Less than 1MB is suspicious
            self.logger.warning(f"Downloaded file is unusually small: {new_exe_path.stat().st_size} bytes")
        
        self.logger.info(f"Launching update script: {script_path}")
        self.logger.info(f"Update file size: {new_exe_path.stat().st_size} bytes")
        
        try:
            # Start the update script with better error handling
            process = subprocess.Popen(
                str(script_path), 
                shell=True,
                cwd=str(script_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.logger.info(f"Update script launched with PID: {process.pid}")
            
        except Exception as e:
            raise UpdateError(f"Failed to launch update script: {e}")
        
        # Give the script a moment to start
        import time
        time.sleep(0.5)
        
        # Exit current application
        self.logger.info("Exiting current application for update")
        sys.exit(0)


class UpdateChecker:
    """
    Simple update checker that can be used for silent background checks.
    """
    
    def __init__(self, updater: AutoUpdater):
        self.updater = updater
        self.logger = logging.getLogger(__name__)
    
    def check_silent(self) -> Optional[UpdateInfo]:
        """
        Perform a silent update check without user interaction.
        
        Returns:
            Optional[UpdateInfo]: Update info if check successful, None if failed
        """
        try:
            return self.updater.check_for_updates()
        except UpdateError as e:
            self.logger.error(f"Silent update check failed: {e}")
            return None
    
    def check_and_auto_install(self) -> bool:
        """
        Check for updates and automatically install if available.
        
        Returns:
            bool: True if update was initiated, False otherwise
        """
        try:
            update_info = self.updater.check_for_updates()
            
            if update_info.is_available and update_info.download_url:
                self.logger.info(f"Auto-installing update to {update_info.latest_version}")
                return self.updater.download_and_install(update_info)
            
            return False
            
        except UpdateError as e:
            self.logger.error(f"Auto-update failed: {e}")
            return False 