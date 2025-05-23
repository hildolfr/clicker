"""
Singleton application instance management.

This module ensures only one instance of the Clicker application runs at a time
using Windows mutex and lockfile mechanisms.
"""

import ctypes
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from PyQt5 import QtWidgets


class SingletonManager:
    """Manages singleton application instance using Windows mutex and lockfile."""
    
    def __init__(self, app_name: str = "Clicker", lockfile_path: Optional[Path] = None):
        self.app_name = app_name
        self.lockfile_path = lockfile_path or Path("clicker.lock")
        self.mutex_name = f"Global\\{app_name}SingletonMutex"
        self.mutex_handle: Optional[int] = None
        self.logger = logging.getLogger(__name__)
    
    def acquire_lock(self) -> bool:
        """
        Acquire singleton lock using Windows mutex and lockfile.
        
        Returns:
            True if singleton lock acquired successfully, False if another instance exists
        """
        return self.acquire_singleton_lock()
    
    def acquire_singleton_lock(self) -> bool:
        """
        Acquire singleton lock using Windows mutex and lockfile.
        
        Returns:
            True if singleton lock acquired successfully, False if another instance exists
        """
        # Try to create mutex first - this is more reliable than file locks
        try:
            self.mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, self.mutex_name)
            if not self.mutex_handle:
                self.logger.error("Failed to create mutex handle")
                return False
                
            last_error = ctypes.windll.kernel32.GetLastError()
            
            if last_error == 183:  # ERROR_ALREADY_EXISTS
                self.logger.warning("Mutex already exists - another instance is running")
                # Clean up the handle we just created since another instance exists
                try:
                    ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
                except Exception as cleanup_error:
                    self.logger.error(f"Error cleaning up mutex handle: {cleanup_error}")
                finally:
                    self.mutex_handle = None
                # Don't show dialog here - let the caller handle the messaging
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating mutex: {e}")
            # Ensure handle is cleaned up even if an exception occurred
            if self.mutex_handle:
                try:
                    ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
                except Exception as cleanup_error:
                    self.logger.error(f"Error cleaning up mutex handle after exception: {cleanup_error}")
                finally:
                    self.mutex_handle = None
            # Continue with file-based detection as fallback
        
        # Check lockfile as secondary measure
        if self.lockfile_path.exists():
            if not self._check_and_cleanup_stale_lockfile():
                # Failed to acquire lock, clean up mutex if we have one
                if self.mutex_handle:
                    try:
                        ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
                    except Exception as cleanup_error:
                        self.logger.error(f"Error cleaning up mutex handle: {cleanup_error}")
                    finally:
                        self.mutex_handle = None
                return False
        
        # Write our PID to the lockfile
        try:
            current_pid = os.getpid()
            self.lockfile_path.write_text(str(current_pid))
            self.logger.debug(f"Created lock file with PID: {current_pid}")
        except Exception as e:
            self.logger.error(f"Failed to create lock file: {e}")
            # If we can't create lockfile, clean up mutex and fail
            if self.mutex_handle:
                try:
                    ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
                except Exception as cleanup_error:
                    self.logger.error(f"Error cleaning up mutex handle: {cleanup_error}")
                finally:
                    self.mutex_handle = None
            return False
        
        return True
    
    def release_lock(self) -> None:
        """Release the singleton lock."""
        return self.release_singleton_lock()
    
    def release_singleton_lock(self) -> None:
        """Release the singleton lock."""
        try:
            # Remove lockfile
            if self.lockfile_path.exists():
                self.lockfile_path.unlink()
                self.logger.debug("Removed lockfile")
            
            # Close mutex handle if we have one
            if self.mutex_handle:
                ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
                self.mutex_handle = None
                
        except Exception as e:
            self.logger.error(f"Error releasing singleton lock: {e}")
    
    def _check_and_cleanup_stale_lockfile(self) -> bool:
        """
        Check if lockfile is stale and clean it up if needed.
        
        Returns:
            True if lockfile was stale and cleaned up, False if another instance is running
        """
        try:
            content = self.lockfile_path.read_text().strip()
            
            try:
                pid = int(content)
                self.logger.debug(f"Found lock file with PID: {pid}")
                
                # Check if the process is still running
                if self._is_process_running(pid):
                    self.logger.warning(f"Process with PID {pid} is still running")
                    # Don't show dialog here - let the caller handle the messaging
                    return False
                else:
                    self.logger.info(f"Removing stale lock file for process {pid}")
                    self.lockfile_path.unlink()
                    return True
                    
            except ValueError:
                # If PID is not an integer, file is corrupted
                self.logger.warning(f"Lock file contains invalid PID: '{content}'")
                self.lockfile_path.unlink()
                return True
                
        except (IOError, OSError) as e:
            # If we can't read the lock file, remove it
            self.logger.warning(f"Error reading lock file: {e}")
            try:
                self.lockfile_path.unlink()
                return True
            except Exception as e2:
                self.logger.error(f"Failed to remove invalid lock file: {e2}")
                return False
    
    def _is_process_running(self, pid: int) -> bool:
        """
        Check if a process with given PID is still running on Windows.
        
        Args:
            pid: Process ID to check
            
        Returns:
            True if process is running, False otherwise
        """
        try:
            # Use CreateToolhelp32Snapshot method for reliable process checking
            TH32CS_SNAPPROCESS = 0x00000002
            INVALID_HANDLE_VALUE = -1
            
            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ("dwSize", ctypes.wintypes.DWORD),
                    ("cntUsage", ctypes.wintypes.DWORD),
                    ("th32ProcessID", ctypes.wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.POINTER(ctypes.wintypes.ULONG)),
                    ("th32ModuleID", ctypes.wintypes.DWORD),
                    ("cntThreads", ctypes.wintypes.DWORD),
                    ("th32ParentProcessID", ctypes.wintypes.DWORD),
                    ("pcPriClassBase", ctypes.wintypes.LONG),
                    ("dwFlags", ctypes.wintypes.DWORD),
                    ("szExeFile", ctypes.c_char * 260)
                ]
            
            # Create a snapshot of the system processes
            hProcessSnap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if hProcessSnap == INVALID_HANDLE_VALUE:
                return False
            
            pe32 = PROCESSENTRY32()
            pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)
            
            # Get the first process from the snapshot
            if not ctypes.windll.kernel32.Process32First(hProcessSnap, ctypes.byref(pe32)):
                ctypes.windll.kernel32.CloseHandle(hProcessSnap)
                return False
            
            # Iterate through all processes
            found = False
            while True:
                if pe32.th32ProcessID == pid:
                    found = True
                    break
                
                if not ctypes.windll.kernel32.Process32Next(hProcessSnap, ctypes.byref(pe32)):
                    break
            
            # Clean up the snapshot handle
            ctypes.windll.kernel32.CloseHandle(hProcessSnap)
            return found
            
        except Exception as e:
            self.logger.error(f"Error checking process existence: {e}")
            # Fall back to simpler method if the complex one fails
            try:
                handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)
                if handle:
                    ctypes.windll.kernel32.CloseHandle(handle)
                    return True
                return False
            except Exception as e2:
                self.logger.error(f"Fallback process check also failed: {e2}")
                return False
    
    def _show_already_running_message(self) -> None:
        """Show message that another instance is already running."""
        QtWidgets.QMessageBox.critical(
            None, 
            'Already Running', 
            'Another instance of Clicker is already running.'
        )
        sys.exit(1)
    
    def __enter__(self):
        """Context manager entry."""
        if not self.acquire_singleton_lock():
            sys.exit(1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release_singleton_lock() 