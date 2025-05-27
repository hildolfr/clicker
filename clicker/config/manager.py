"""
Configuration Manager for the Clicker application.

This module provides centralized configuration management with:
- Type-safe configuration loading/saving
- Automatic migration from legacy formats
- Configuration validation and error handling
- Backup and recovery functionality
- File watching for real-time updates
"""

from __future__ import annotations

import json
import logging
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

from clicker.config.models import (
    AppSettings, 
    KeystrokeConfig, 
    ProfileConfig,
    migrate_legacy_settings
)
from clicker.utils.exceptions import ConfigurationError


class ConfigManager:
    """Centralized configuration management with validation and backup."""
    
    def __init__(
        self, 
        config_dir: Optional[Path] = None,
        settings_file: str = "settings.json",
        keystrokes_file: str = "keystrokes.txt"
    ):
        """Initialize configuration manager."""
        self.config_dir = Path(config_dir) if config_dir else Path.cwd()
        self.settings_file = self.config_dir / settings_file
        self.keystrokes_file = self.config_dir / keystrokes_file
        # Remove backup directory creation - users don't want excessive files
        # self.backup_dir = self.config_dir / "backups"
        
        # Initialize default values
        self._settings = AppSettings()
        self._keystrokes: List[KeystrokeConfig] = []
        self._profiles: Dict[str, ProfileConfig] = {}
        
        # Progress tracking
        self._progress_callbacks: List[Callable[[str, int, int], None]] = []
        self._operation_timeout = 30.0  # 30 second timeout for operations
        
        # Change tracking
        self._change_callbacks: List[Callable[[str], None]] = []
        self._last_modified: Dict[str, float] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Ensure directory structure exists
        self._ensure_directories()
        
        self.logger = logging.getLogger(__name__)
        
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.config_dir.mkdir(exist_ok=True)
        # Remove backup directory creation - users don't want excessive files
        # self.backup_dir.mkdir(exist_ok=True)
        
    @property
    def settings(self) -> AppSettings:
        """Get current application settings."""
        with self._lock:
            return self._settings
    
    @property
    def keystrokes(self) -> List[KeystrokeConfig]:
        """Get current keystroke configurations."""
        return self._keystrokes.copy()
    
    def register_progress_callback(self, callback: Callable[[str, int, int], None]) -> None:
        """Register a callback for progress updates during long operations.
        
        Args:
            callback: Function that receives (operation_name, current_step, total_steps)
        """
        with self._lock:
            self._progress_callbacks.append(callback)

    def _notify_progress(self, operation: str, current: int, total: int) -> None:
        """Notify all progress callbacks about operation progress."""
        for callback in self._progress_callbacks:
            try:
                callback(operation, current, total)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {e}")

    def load(self) -> None:
        """Load all configuration files with validation and migration."""
        with self._lock:
            self.logger.info("Loading configuration...")
            total_steps = 4  # Settings, keystrokes, profiles, cleanup
            
            # Step 1: Load settings
            self._notify_progress("Loading Settings", 1, total_steps)
            self._load_settings()
            
            # Step 2: Load keystrokes
            self._notify_progress("Loading Keystrokes", 2, total_steps)
            self._load_keystrokes()
            
            # Step 3: Load profiles
            self._notify_progress("Loading Profiles", 3, total_steps)
            self._load_profiles()
            
            # Step 4: Finalization
            self._notify_progress("Finalizing Configuration", 4, total_steps)
            
            self.logger.info("Configuration loaded successfully")
            self._notify_progress("Configuration Load Complete", total_steps, total_steps)
    
    def _load_settings(self) -> None:
        """Load and validate settings from file."""
        if not self.settings_file.exists():
            self.logger.info("Settings file not found, creating with defaults")
            self._create_default_settings()
            return
            
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check if migration is needed
            if self._needs_migration(data):
                self.logger.info("Migrating legacy settings format")
                self._backup_file(self.settings_file)
                data = self._migrate_settings(data)
                
            self._settings = AppSettings.from_dict(data)
            self._last_modified['settings'] = self.settings_file.stat().st_mtime
            
            self.logger.info("Settings loaded successfully")
            
        except PermissionError as e:
            self.logger.error(f"Permission denied accessing settings file: {e}")
            if self._restore_from_backup("settings"):
                self.logger.info("Successfully restored settings from backup")
            else:
                self.logger.warning("Could not restore from backup, using defaults")
                self._create_default_settings()
                
        except FileNotFoundError as e:
            self.logger.error(f"Settings file not found: {e}")
            self._create_default_settings()
            
        except OSError as e:
            # Handles file locked, disk full, etc.
            self.logger.error(f"OS error accessing settings file: {e}")
            if self._restore_from_backup("settings"):
                self.logger.info("Successfully restored settings from backup")
            else:
                self.logger.warning("Could not restore from backup, using defaults")
                self._create_default_settings()
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in settings file: {e}")
            self._handle_corrupted_settings()
            
        except Exception as e:
            self.logger.error(f"Unexpected error loading settings: {e}")
            self._handle_corrupted_settings()
    
    def _load_keystrokes(self) -> None:
        """Load and validate keystrokes from file."""
        if not self.keystrokes_file.exists():
            self.logger.info("Keystrokes file not found, creating with defaults")
            self._create_default_keystrokes()
            return
            
        try:
            keystrokes = []
            with open(self.keystrokes_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        keystroke = KeystrokeConfig.from_string(line)
                        if keystroke:
                            keystrokes.append(keystroke)
                    except ValueError as e:
                        self.logger.warning(f"Invalid keystroke at line {line_num}: {e}")
                        
            if not keystrokes:
                self.logger.warning("No valid keystrokes found, creating defaults")
                self._create_default_keystrokes()
                return
                
            self._keystrokes = keystrokes
            self._last_modified['keystrokes'] = self.keystrokes_file.stat().st_mtime
            
            self.logger.info(f"Loaded {len(keystrokes)} keystroke configurations")
            
        except PermissionError as e:
            self.logger.error(f"Permission denied accessing keystrokes file: {e}")
            if self._restore_from_backup("keystrokes"):
                self.logger.info("Successfully restored keystrokes from backup")
            else:
                self.logger.warning("Could not restore from backup, using defaults")
                self._create_default_keystrokes()
                
        except FileNotFoundError as e:
            self.logger.error(f"Keystrokes file not found: {e}")
            self._create_default_keystrokes()
            
        except OSError as e:
            # Handles file locked, disk full, etc.
            self.logger.error(f"OS error accessing keystrokes file: {e}")
            if self._restore_from_backup("keystrokes"):
                self.logger.info("Successfully restored keystrokes from backup")
            else:
                self.logger.warning("Could not restore from backup, using defaults")
                self._create_default_keystrokes()
                
        except Exception as e:
            self.logger.error(f"Unexpected error loading keystrokes: {e}")
            self._create_default_keystrokes()
    
    def _load_profiles(self) -> None:
        """Load configuration profiles if they exist."""
        profiles_dir = self.config_dir / "profiles"
        if not profiles_dir.exists():
            self.logger.debug("Profiles directory does not exist, skipping profile loading")
            return
            
        # Resolve the profiles directory to get absolute path for security validation
        try:
            resolved_profiles_dir = profiles_dir.resolve()
        except (OSError, RuntimeError) as e:
            self.logger.error(f"Could not resolve profiles directory: {e}")
            return
            
        profile_count = 0
        for profile_file in profiles_dir.glob("*.json"):
            try:
                # SECURITY: Validate that the profile file is actually within the profiles directory
                # This prevents directory traversal attacks via symlinks or relative paths
                resolved_profile_path = profile_file.resolve()
                
                # Check if the resolved path is within the expected profiles directory
                try:
                    resolved_profile_path.relative_to(resolved_profiles_dir)
                except ValueError:
                    self.logger.error(f"Security violation: Profile file outside profiles directory: {profile_file}")
                    continue
                
                # Additional security check: ensure filename doesn't contain dangerous characters
                if not self._is_safe_filename(profile_file.name):
                    self.logger.error(f"Security violation: Unsafe filename detected: {profile_file.name}")
                    continue
                
                # Limit file size to prevent DoS attacks
                file_size = profile_file.stat().st_size
                if file_size > 1024 * 1024:  # 1MB limit
                    self.logger.error(f"Profile file too large: {profile_file} ({file_size} bytes)")
                    continue
                
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Validate profile data structure
                if not isinstance(data, dict):
                    self.logger.error(f"Invalid profile format: {profile_file}")
                    continue
                
                # Load the profile using ProfileConfig.from_dict
                try:
                    profile = ProfileConfig.from_dict(data)
                    profile_name = profile.name
                    
                    # Store profile with validation
                    self._profiles[profile_name] = profile
                    profile_count += 1
                    
                    self.logger.debug(f"Loaded profile: {profile_name} from {profile_file.name}")
                    
                except Exception as profile_error:
                    self.logger.error(f"Error creating profile from {profile_file}: {profile_error}")
                    continue
                    
            except (OSError, IOError) as e:
                self.logger.error(f"Error accessing profile file {profile_file}: {e}")
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in profile file {profile_file}: {e}")
            except Exception as e:
                self.logger.error(f"Error loading profile {profile_file}: {e}")
        
        self.logger.info(f"Loaded {profile_count} configuration profiles")
    
    def get_profiles(self) -> Dict[str, ProfileConfig]:
        """Get all loaded profiles."""
        return self._profiles.copy()
    
    def get_profile(self, name: str) -> Optional[ProfileConfig]:
        """Get a specific profile by name."""
        return self._profiles.get(name)
    
    def save_profile(self, profile: ProfileConfig) -> None:
        """Save a profile to file with validation."""
        with self._lock:
            # Validate profile
            if not isinstance(profile, ProfileConfig):
                raise ValueError("profile must be a ProfileConfig instance")
            
            # Update timestamps
            current_time = datetime.now().isoformat() + "Z"
            if not profile.created_at:
                profile.created_at = current_time
            profile.modified_at = current_time
            
            # Store in memory
            self._profiles[profile.name] = profile
            
            # Save to file
            profiles_dir = self.config_dir / "profiles"
            profiles_dir.mkdir(exist_ok=True)
            
            # Sanitize filename
            safe_filename = self._sanitize_profile_filename(profile.name)
            profile_file = profiles_dir / f"{safe_filename}.json"
            
            try:
                # Create backup if file exists
                if profile_file.exists():
                    self._backup_file(profile_file, "profiles")
                
                # Save profile data
                profile_data = profile.to_dict()
                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(profile_data, f, indent=4, sort_keys=True)
                
                self.logger.info(f"Profile '{profile.name}' saved successfully")
                self._notify_change('profiles')
                
            except Exception as e:
                self.logger.error(f"Error saving profile '{profile.name}': {e}")
                raise ConfigurationError(f"Failed to save profile '{profile.name}': {e}")
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile by name."""
        with self._lock:
            if name not in self._profiles:
                self.logger.warning(f"Profile '{name}' not found for deletion")
                return False
            
            # Remove from memory
            del self._profiles[name]
            
            # Remove file
            profiles_dir = self.config_dir / "profiles"
            safe_filename = self._sanitize_profile_filename(name)
            profile_file = profiles_dir / f"{safe_filename}.json"
            
            try:
                if profile_file.exists():
                    # Create backup before deletion
                    self._backup_file(profile_file, "profiles")
                    profile_file.unlink()
                    self.logger.info(f"Profile '{name}' deleted successfully")
                else:
                    self.logger.warning(f"Profile file for '{name}' not found on disk")
                
                self._notify_change('profiles')
                return True
                
            except Exception as e:
                self.logger.error(f"Error deleting profile '{name}': {e}")
                # Re-add to memory since file deletion failed
                if name in self._profiles:
                    pass  # Already removed
                return False
    
    def load_profile(self, name: str) -> bool:
        """Load a profile as the current configuration."""
        with self._lock:
            if name not in self._profiles:
                self.logger.error(f"Profile '{name}' not found")
                return False
            
            try:
                profile = self._profiles[name]
                
                # Create backup of current configuration
                self._backup_current_configuration()
                
                # Load profile settings and keystrokes
                self._settings = profile.settings
                self._keystrokes = profile.keystrokes.copy()
                
                # Save as current configuration
                self._save_settings()
                self._save_keystrokes()
                
                self.logger.info(f"Profile '{name}' loaded successfully")
                self._notify_change('configuration')
                return True
                
            except Exception as e:
                self.logger.error(f"Error loading profile '{name}': {e}")
                return False
    
    def save_current_as_profile(self, name: str, description: str = "", author: str = "", tags: List[str] = None) -> bool:
        """Save current configuration as a new profile."""
        with self._lock:
            try:
                # Create new profile from current configuration
                profile = ProfileConfig(
                    name=name,
                    description=description,
                    author=author,
                    tags=tags or [],
                    settings=AppSettings.from_dict(self._settings.to_dict()),  # Deep copy
                    keystrokes=[KeystrokeConfig(
                        key=ks.key,
                        delay=ks.delay,
                        enabled=ks.enabled,
                        description=ks.description,
                        tags=ks.tags.copy(),
                        priority=ks.priority,
                        max_failures=ks.max_failures
                    ) for ks in self._keystrokes]  # Deep copy
                )
                
                # Save the profile
                self.save_profile(profile)
                
                self.logger.info(f"Current configuration saved as profile '{name}'")
                return True
                
            except Exception as e:
                self.logger.error(f"Error saving current configuration as profile '{name}': {e}")
                return False
    
    def list_profiles(self) -> List[str]:
        """Get a list of all profile names."""
        return list(self._profiles.keys())
    
    def _sanitize_profile_filename(self, profile_name: str) -> str:
        """Sanitize profile name for use as filename."""
        import re
        # Replace spaces and special characters with underscores
        sanitized = re.sub(r'[^\w\-_\.]', '_', profile_name)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure not empty
        if not sanitized:
            sanitized = "unnamed_profile"
        # Limit length
        return sanitized[:50]
    
    def _backup_current_configuration(self) -> None:
        """Create a backup of the current configuration before profile switching."""
        # Backup functionality disabled to reduce file clutter
        self.logger.debug("Configuration backup skipped before profile switch (backups disabled)")
    
    def _backup_file(self, file_path: Path, category: str = "general") -> None:
        """Create a timestamped backup of a file with category support."""
        # Backup functionality disabled to reduce file clutter
        # Users can manually backup files if needed
        self.logger.debug(f"Backup skipped for {file_path.name} (backups disabled)")
    
    def _cleanup_old_backups(self, file_stem: str, category: str, keep_count: int = 10) -> None:
        """Clean up old backup files, keeping only the most recent ones."""
        # Backup functionality disabled to reduce file clutter
        pass
    
    def export_profile(self, name: str, export_path: Path) -> bool:
        """Export a profile to a file."""
        if name not in self._profiles:
            self.logger.error(f"Profile '{name}' not found for export")
            return False
        
        try:
            profile = self._profiles[name]
            profile_data = profile.to_dict()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=4, sort_keys=True)
            
            self.logger.info(f"Profile '{name}' exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting profile '{name}': {e}")
            return False
    
    def import_profile(self, import_path: Path, new_name: str = None) -> bool:
        """Import a profile from a file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create profile from imported data
            profile = ProfileConfig.from_dict(data)
            
            # Use new name if provided
            if new_name:
                profile.name = new_name
            
            # Check for name conflicts
            original_name = profile.name
            counter = 1
            while profile.name in self._profiles:
                profile.name = f"{original_name}_{counter}"
                counter += 1
            
            # Update timestamps
            current_time = datetime.now().isoformat() + "Z"
            profile.created_at = current_time
            profile.modified_at = current_time
            
            # Save the imported profile
            self.save_profile(profile)
            
            self.logger.info(f"Profile imported as '{profile.name}' from {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing profile from {import_path}: {e}")
            return False
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe and doesn't contain dangerous characters."""
        import re
        
        # Allow only alphanumeric characters, dots, hyphens, and underscores
        # This prevents directory traversal and other filename-based attacks
        safe_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
        
        if not safe_pattern.match(filename):
            return False
            
        # Reject files starting with dots (hidden files) except .json extension
        if filename.startswith('.') and not filename.endswith('.json'):
            return False
            
        # Reject overly long filenames
        if len(filename) > 255:
            return False
            
        # Reject reserved Windows filenames
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in reserved_names:
            return False
            
        return True
    
    def _create_default_settings(self) -> None:
        """Create default settings file."""
        self._settings = AppSettings()
        self._save_settings()
        self.logger.info("Created default settings file")
    
    def _create_default_keystrokes(self) -> None:
        """Create default keystrokes file."""
        default_keystrokes = [
            KeystrokeConfig(key="1", delay=2.0, description="Example key 1"),
            KeystrokeConfig(key="2", delay=2.0, description="Example key 2"),
            KeystrokeConfig(key="3", delay=2.0, description="Example key 3"),
        ]
        self._keystrokes = default_keystrokes
        self._save_keystrokes()
        self.logger.info("Created default keystrokes file")
    
    def save(self) -> None:
        """Save all configuration to files with progress feedback."""
        with self._lock:
            self.logger.debug("Saving configuration...")
            total_steps = 4  # Backup, validation, settings save, keystrokes save
            
            # Step 1: Create backups
            self._notify_progress("Creating Backups", 1, total_steps)
            if self.settings_file.exists():
                self._backup_file(self.settings_file)
            if self.keystrokes_file.exists():
                self._backup_file(self.keystrokes_file)
            
            # Step 2: Validation
            self._notify_progress("Validating Configuration", 2, total_steps)
            self._validate_settings_comprehensive()
            
            # Step 3: Save settings
            self._notify_progress("Saving Settings", 3, total_steps)
            self._save_settings()
            
            # Step 4: Save keystrokes
            self._notify_progress("Saving Keystrokes", 4, total_steps)
            self._save_keystrokes()
            
            self.logger.info("Configuration saved successfully")
            self._notify_progress("Configuration Save Complete", total_steps, total_steps)
    
    def _save_settings(self) -> None:
        """Save settings to file with comprehensive validation."""
        try:
            # Comprehensive validation before saving
            self._validate_settings_comprehensive()
            
            # Create backup before saving
            self._backup_file(self.settings_file)
            
            data = self._settings.to_dict()
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, sort_keys=True)
            
            self._last_modified['settings'] = self.settings_file.stat().st_mtime
            self.logger.debug("Settings saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            raise ConfigurationError(f"Failed to save settings: {e}")
    
    def _validate_settings_comprehensive(self) -> None:
        """Perform comprehensive validation of settings."""
        # Basic validation first
        self._settings.validate()
        
        # Cross-field validation
        self._validate_timing_settings()
        self._validate_path_accessibility()
        self._validate_performance_settings()
        self._validate_keystroke_conflicts()
    
    def _validate_timing_settings(self) -> None:
        """Validate timing-related settings for logical consistency."""
        settings = self._settings
        
        # Check global cooldown vs individual keystroke delays
        min_keystroke_delay = min((ks.delay for ks in self._keystrokes if ks.enabled), default=1.0)
        
        if settings.global_cooldown > min_keystroke_delay:
            self.logger.warning(
                f"Global cooldown ({settings.global_cooldown}s) is longer than minimum keystroke delay "
                f"({min_keystroke_delay}s). This may cause unexpected timing behavior."
            )
        
        # Check start time stagger vs delays
        if settings.start_time_stagger > min_keystroke_delay / 2:
            self.logger.warning(
                f"Start time stagger ({settings.start_time_stagger}s) may interfere with keystroke timing."
            )
    
    def _validate_path_accessibility(self) -> None:
        """Validate file paths and accessibility."""
        import os
        
        # Backup functionality disabled to reduce file clutter
        # Skip backup directory validation
        self.logger.debug("Backup directory validation skipped (backups disabled)")
        
        # Check if log directory is writable (current directory)
        try:
            test_log = Path("test_log.tmp")
            test_log.touch()
            test_log.unlink()
        except (OSError, PermissionError) as e:
            raise ConfigurationError(f"Log directory is not writable: {e}")
    
    def _validate_performance_settings(self) -> None:
        """Validate performance-related settings."""
        settings = self._settings
        
        # Check memory limit vs expected usage
        keystroke_count = len([ks for ks in self._keystrokes if ks.enabled])
        estimated_memory_mb = max(50, keystroke_count * 0.1)  # Rough estimate
        
        if settings.memory_limit_mb < estimated_memory_mb:
            raise ConfigurationError(
                f"Memory limit ({settings.memory_limit_mb}MB) may be too low for "
                f"{keystroke_count} keystrokes (estimated need: {estimated_memory_mb:.1f}MB)"
            )
        
        # Check thread pool size vs keystroke count
        if keystroke_count > 100 and settings.thread_pool_size < 3:
            self.logger.warning(
                f"Thread pool size ({settings.thread_pool_size}) may be too small for "
                f"{keystroke_count} keystrokes. Consider increasing to at least 3."
            )
    
    def _validate_keystroke_conflicts(self) -> None:
        """Check for potential keystroke conflicts."""
        enabled_keystrokes = [ks for ks in self._keystrokes if ks.enabled]
        
        # Check for duplicate keys
        key_counts = {}
        for ks in enabled_keystrokes:
            key_counts[ks.key] = key_counts.get(ks.key, 0) + 1
        
        duplicates = [key for key, count in key_counts.items() if count > 1]
        if duplicates:
            self.logger.warning(f"Duplicate keystroke definitions found: {duplicates}")
        
        # Check for rapid-fire combinations (same key with short delays)
        rapid_fire_keys = []
        for key, count in key_counts.items():
            if count > 1:
                delays = [ks.delay for ks in enabled_keystrokes if ks.key == key]
                min_delay = min(delays)
                if min_delay < 0.5:  # Less than 500ms
                    rapid_fire_keys.append(f"{key} (min delay: {min_delay}s)")
        
        if rapid_fire_keys:
            self.logger.warning(f"Rapid-fire keystroke combinations detected: {rapid_fire_keys}")
        
        # Check for conflicts with system emergency keys
        emergency_key = self._settings.emergency_stop_key.lower()
        for ks in enabled_keystrokes:
            if ks.key.lower() == emergency_key:
                raise ConfigurationError(
                    f"Keystroke '{ks.key}' conflicts with emergency stop key '{emergency_key}'"
                )
    
    def _save_keystrokes(self) -> None:
        """Save keystrokes to file."""
        try:
            with open(self.keystrokes_file, 'w', encoding='utf-8') as f:
                f.write("# Clicker Keystrokes Configuration\n")
                f.write("# Format: [KEY] [DELAY] [OPTIONAL_DESCRIPTION]\n")
                f.write("# Use S- for Shift, C- for Control, A- for Alt\n")
                f.write("#\n\n")
                
                for keystroke in self._keystrokes:
                    if keystroke.enabled:
                        f.write(keystroke.to_string() + "\n")
                    else:
                        f.write(f"# DISABLED: {keystroke.to_string()}\n")
                        
            self._last_modified['keystrokes'] = self.keystrokes_file.stat().st_mtime
            self.logger.debug("Keystrokes saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving keystrokes: {e}")
            raise ConfigurationError(f"Failed to save keystrokes: {e}")
    
    def update_settings(self, **kwargs) -> None:
        """Update settings with validation."""
        with self._lock:
            # Create new settings with updates
            current_dict = self._settings.to_dict()
            current_dict.update(kwargs)
            
            # Validate new settings
            new_settings = AppSettings.from_dict(current_dict)
            new_settings.validate()
            
            self._settings = new_settings
            self._notify_change('settings')
    
    def add_keystroke(self, keystroke: KeystrokeConfig) -> None:
        """Add a new keystroke configuration."""
        with self._lock:
            keystroke.validate()  # This happens in __post_init__ but be explicit
            self._keystrokes.append(keystroke)
            self._notify_change('keystrokes')
    
    def remove_keystroke(self, index: int) -> None:
        """Remove a keystroke by index."""
        with self._lock:
            if 0 <= index < len(self._keystrokes):
                del self._keystrokes[index]
                self._notify_change('keystrokes')
            else:
                raise IndexError(f"Keystroke index {index} out of range")
    
    def update_keystroke(self, index: int, keystroke: KeystrokeConfig) -> None:
        """Update a keystroke at the specified index."""
        with self._lock:
            if 0 <= index < len(self._keystrokes):
                keystroke.validate()
                self._keystrokes[index] = keystroke
                self._notify_change('keystrokes')
            else:
                raise IndexError(f"Keystroke index {index} out of range")
    
    def get_enabled_keystrokes(self) -> List[KeystrokeConfig]:
        """Get only enabled keystrokes."""
        with self._lock:
            return [ks for ks in self._keystrokes if ks.enabled]
    
    def register_change_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback for configuration changes."""
        with self._lock:
            self._change_callbacks.append(callback)
    
    def _notify_change(self, change_type: str) -> None:
        """Notify registered callbacks of configuration changes."""
        for callback in self._change_callbacks:
            try:
                callback(change_type)
            except Exception as e:
                self.logger.error(f"Error in change callback: {e}")
    
    def _needs_migration(self, data: Dict[str, Any]) -> bool:
        """Check if settings need migration from legacy format."""
        legacy_keys = ['pause_time', 'visual_indicator']
        return any(key in data for key in legacy_keys)
    
    def _migrate_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate settings from legacy format."""
        self.logger.info("Migrating legacy settings")
        migrated_settings = migrate_legacy_settings(data)
        
        # Save migrated settings
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(migrated_settings.to_dict(), f, indent=4, sort_keys=True)
            
        return migrated_settings.to_dict()
    
    def _handle_corrupted_settings(self) -> None:
        """Handle corrupted settings by restoring from backup or creating defaults."""
        self.logger.warning("Settings file is corrupted, attempting recovery")
        
        # Try to restore from backup
        if self._restore_from_backup("settings"):
            return
            
        # Fall back to defaults
        self.logger.warning("No valid backup found, using defaults")
        self._create_default_settings()
    
    def _restore_from_backup(self, file_type: str) -> bool:
        """Try to restore a file from the most recent backup with improved error handling."""
        # Backup functionality disabled to reduce file clutter
        self.logger.warning(f"Backup restoration not available for {file_type} (backups disabled)")
        return False
    
    def _validate_backup_file(self, backup_path: Path, file_type: str) -> bool:
        """Validate backup file before attempting restoration."""
        try:
            # Check file size (should not be empty or extremely large)
            file_size = backup_path.stat().st_size
            if file_size == 0:
                self.logger.warning(f"Backup file is empty: {backup_path}")
                return False
            
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                self.logger.warning(f"Backup file is suspiciously large ({file_size} bytes): {backup_path}")
                return False
            
            # Check file format
            if file_type == "settings":
                return self._validate_json_backup(backup_path)
            else:
                return self._validate_keystrokes_backup(backup_path)
                
        except Exception as e:
            self.logger.error(f"Error validating backup file {backup_path}: {e}")
            return False
    
    def _validate_json_backup(self, backup_path: Path) -> bool:
        """Validate JSON backup file structure."""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if it's a valid settings structure
            if not isinstance(data, dict):
                return False
            
            # Check for essential keys
            essential_keys = ['toggle_key', 'global_cooldown', 'start_time_stagger']
            return all(key in data for key in essential_keys)
            
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
    
    def _validate_keystrokes_backup(self, backup_path: Path) -> bool:
        """Validate keystrokes backup file structure."""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Should have at least some non-comment lines
            non_comment_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
            return len(non_comment_lines) > 0
            
        except UnicodeDecodeError:
            return False
    
    def _test_load_settings(self, test_file: Path) -> bool:
        """Test loading settings file without affecting current state."""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Try creating settings object to validate
            if self._needs_migration(data):
                data = self._migrate_settings(data)
            
            test_settings = AppSettings.from_dict(data)
            test_settings.validate()
            return True
            
        except Exception as e:
            self.logger.debug(f"Test load failed for {test_file}: {e}")
            return False
    
    def _test_load_keystrokes(self, test_file: Path) -> bool:
        """Test loading keystrokes file without affecting current state."""
        try:
            test_keystrokes = []
            with open(test_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Try parsing the keystroke
                    if line.startswith('# DISABLED:'):
                        line = line[12:].strip()
                    
                    keystroke = KeystrokeConfig.from_string(line)
                    if keystroke:
                        test_keystrokes.append(keystroke)
            
            # Should have at least one valid keystroke
            return len(test_keystrokes) > 0
            
        except Exception as e:
            self.logger.debug(f"Test load failed for {test_file}: {e}")
            return False
    
    def _notify_backup_restoration(self, file_type: str, backup_path: Path) -> None:
        """Notify about backup restoration (placeholder for UI updates)."""
        self.logger.info(f"Backup restored for {file_type} from {backup_path}")
        # Here you could add a call to a registered callback for UI updates
        self._notify_change(f"{file_type}_restored_from_backup")

    def reload(self) -> None:
        """Reload configuration from files."""
        self.logger.info("Manually reloading configuration")
        self.load()

    def _save_with_timeout(self, file_path: Path, content: str, timeout: float = None) -> None:
        """Save content to file with timeout protection and proper resource cleanup."""
        import threading
        
        if timeout is None:
            timeout = self._operation_timeout
        
        success = threading.Event()
        error_container = []
        
        def save_operation():
            try:
                # Use context manager to ensure file handle is always closed
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    f.flush()  # Ensure data is written
                success.set()
            except Exception as e:
                error_container.append(e)
            finally:
                # Ensure success event is set even on error to prevent deadlock
                success.set()
        
        save_thread = threading.Thread(target=save_operation, daemon=True)
        save_thread.start()
        
        # Wait for completion with timeout
        if not success.wait(timeout):
            # Thread is still running, but we can't force-kill it safely
            # Log the timeout and raise error
            self.logger.error(f"File save operation timed out after {timeout} seconds for {file_path}")
            raise ConfigurationError(f"File save operation timed out after {timeout} seconds")
        
        # Check if save operation failed
        if error_container:
            raise error_container[0]
        
        # Wait for thread to complete to ensure proper cleanup
        save_thread.join(timeout=1.0)  # Give thread 1 second to cleanup
        if save_thread.is_alive():
            self.logger.warning(f"Save thread for {file_path} did not complete cleanup within 1 second") 