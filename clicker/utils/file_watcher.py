"""
File watching utilities for configuration file monitoring.

This module provides functionality to watch for changes in configuration files
and trigger reloads when needed.
"""

import logging
import time
from pathlib import Path
from typing import Callable, Optional, List, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


class ConfigFileHandler(FileSystemEventHandler):
    """Handles file system events for configuration files."""
    
    def __init__(self, watched_files: Set[str], callback: Callable):
        """
        Initialize the file handler.
        
        Args:
            watched_files: Set of filenames to watch for changes
            callback: Function to call when a watched file changes
        """
        super().__init__()
        self.watched_files = watched_files
        self.callback = callback
        self.last_modified = 0
        self.cooldown = 1.0  # 1 second cooldown between reloads
        self.logger = logging.getLogger(__name__)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if isinstance(event, FileModifiedEvent) and not event.is_directory:
            filename = Path(event.src_path).name
            
            if filename in self.watched_files:
                current_time = time.time()
                if current_time - self.last_modified > self.cooldown:
                    self.last_modified = current_time
                    self.logger.info(f"Detected change in {filename}")
                    
                    try:
                        self.callback(filename)
                    except Exception as e:
                        self.logger.error(f"Error in file change callback: {e}")


class FileWatcher:
    """Watches configuration files for changes and triggers callbacks."""
    
    def __init__(self, watch_directory: Optional[Path] = None):
        """
        Initialize the file watcher.
        
        Args:
            watch_directory: Directory to watch (defaults to current directory)
        """
        self.watch_directory = watch_directory or Path.cwd()
        self.observer: Optional[Observer] = None
        self.watched_files: Set[str] = set()
        self.callback: Optional[Callable] = None
        self.logger = logging.getLogger(__name__)
    
    def start_watching(self, files_to_watch: List[str], callback: Callable) -> bool:
        """
        Start watching specified files for changes.
        
        Args:
            files_to_watch: List of filenames to watch
            callback: Function to call when files change
            
        Returns:
            True if watching started successfully, False otherwise
        """
        try:
            self.watched_files = set(files_to_watch)
            self.callback = callback
            
            # Create event handler
            event_handler = ConfigFileHandler(self.watched_files, callback)
            
            # Create observer
            self.observer = Observer()
            self.observer.daemon = True
            self.observer.schedule(
                event_handler, 
                str(self.watch_directory), 
                recursive=False
            )
            
            # Start watching
            self.observer.start()
            
            self.logger.info(f"Started watching {len(files_to_watch)} files in {self.watch_directory}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start file watching: {e}")
            return False
    
    def stop_watching(self) -> None:
        """Stop watching files for changes."""
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=1.0)
                
                if self.observer.is_alive():
                    self.logger.warning("File observer did not stop in time")
                else:
                    self.logger.debug("File observer stopped successfully")
                    
            except Exception as e:
                self.logger.error(f"Error stopping file observer: {e}")
            finally:
                self.observer = None
                
        self.watched_files.clear()
        self.callback = None
    
    def is_watching(self) -> bool:
        """Check if file watching is active."""
        return self.observer is not None and self.observer.is_alive()
    
    def get_watched_files(self) -> List[str]:
        """Get list of currently watched files."""
        return list(self.watched_files)
    
    def add_file(self, filename: str) -> None:
        """
        Add a file to the watch list.
        
        Args:
            filename: Name of file to add to watch list
        """
        if self.is_watching():
            self.watched_files.add(filename)
            self.logger.debug(f"Added {filename} to watch list")
    
    def remove_file(self, filename: str) -> None:
        """
        Remove a file from the watch list.
        
        Args:
            filename: Name of file to remove from watch list
        """
        if filename in self.watched_files:
            self.watched_files.remove(filename)
            self.logger.debug(f"Removed {filename} from watch list")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_watching() 