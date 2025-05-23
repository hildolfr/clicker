"""
Configuration data models for the Clicker application.

This module defines type-safe configuration classes with validation,
replacing the scattered global variables from the original implementation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union, Dict, Any, Set
from pathlib import Path

from .enums import IndicatorType, KeystrokeMethod


@dataclass
class KeystrokeConfig:
    """Configuration for a single keystroke automation."""
    
    key: str
    delay: float
    enabled: bool = True
    description: str = ""
    tags: List[str] = field(default_factory=list)
    priority: int = 0
    max_failures: int = 3

    def __post_init__(self) -> None:
        """Validate keystroke configuration after initialization."""
        self._validate_delay()
        self._validate_key()
        self._validate_description()
        self._validate_tags()
        self._validate_priority()
        self._validate_max_failures()
    
    def _validate_delay(self) -> None:
        """Validate delay value with strict bounds."""
        if not isinstance(self.delay, (int, float)):
            raise ValueError("Delay must be a numeric value")
        
        if self.delay < 0.1:
            raise ValueError("Delay must be at least 0.1 seconds")
        
        if self.delay > 3600:
            raise ValueError("Delay cannot exceed 1 hour (3600 seconds)")
    
    def _validate_key(self) -> None:
        """Validate key string with comprehensive checks."""
        if not isinstance(self.key, str):
            raise ValueError("Key must be a string")
        
        # Basic length and content validation
        if not self.key or not self.key.strip():
            raise ValueError("Key cannot be empty")
        
        self.key = self.key.strip()
        
        if len(self.key) > KeystrokeConfig.MAX_KEY_LENGTH:
            raise ValueError(f"Key length cannot exceed {KeystrokeConfig.MAX_KEY_LENGTH} characters")
        
        # Check for dangerous characters that could cause issues
        dangerous_chars = set('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x7f')
        if any(char in dangerous_chars for char in self.key):
            raise ValueError("Key contains invalid control characters")
        
        # Validate key format (basic check for modifier syntax)
        if not self._is_valid_key_format(self.key):
            raise ValueError(f"Invalid key format: {self.key}")
    
    def _validate_description(self) -> None:
        """Validate description string with length limits."""
        if not isinstance(self.description, str):
            raise ValueError("Description must be a string")
        
        if len(self.description) > KeystrokeConfig.MAX_DESCRIPTION_LENGTH:
            raise ValueError(f"Description cannot exceed {KeystrokeConfig.MAX_DESCRIPTION_LENGTH} characters")
        
        # Check for control characters in description
        if any(ord(char) < 32 and char not in '\t\n\r' for char in self.description):
            raise ValueError("Description contains invalid control characters")
    
    def _validate_tags(self) -> None:
        """Validate tags list with comprehensive checks."""
        if not isinstance(self.tags, list):
            raise ValueError("Tags must be a list")
        
        if len(self.tags) > KeystrokeConfig.MAX_TAGS_COUNT:
            raise ValueError(f"Cannot have more than {KeystrokeConfig.MAX_TAGS_COUNT} tags")
        
        seen_tags = set()
        for i, tag in enumerate(self.tags):
            if not isinstance(tag, str):
                raise ValueError(f"Tag {i} must be a string")
            
            tag = tag.strip()
            if not tag:
                raise ValueError(f"Tag {i} cannot be empty")
            
            if len(tag) > KeystrokeConfig.MAX_TAG_LENGTH:
                raise ValueError(f"Tag {i} cannot exceed {KeystrokeConfig.MAX_TAG_LENGTH} characters")
            
            # Check for duplicates (case-insensitive)
            tag_lower = tag.lower()
            if tag_lower in seen_tags:
                raise ValueError(f"Duplicate tag found: {tag}")
            seen_tags.add(tag_lower)
            
            # Validate tag format (alphanumeric, spaces, hyphens, underscores)
            if not re.match(r'^[a-zA-Z0-9_\-\s]+$', tag):
                raise ValueError(f"Tag '{tag}' contains invalid characters")
            
            # Update the cleaned tag
            self.tags[i] = tag
    
    def _validate_priority(self) -> None:
        """Validate priority value."""
        if not isinstance(self.priority, int):
            raise ValueError("Priority must be an integer")
        
        if self.priority < KeystrokeConfig.MIN_PRIORITY or self.priority > KeystrokeConfig.MAX_PRIORITY:
            raise ValueError(f"Priority must be between {KeystrokeConfig.MIN_PRIORITY} and {KeystrokeConfig.MAX_PRIORITY}")
    
    def _validate_max_failures(self) -> None:
        """Validate max_failures value."""
        if not isinstance(self.max_failures, int):
            raise ValueError("max_failures must be an integer")
        
        if self.max_failures < KeystrokeConfig.MIN_MAX_FAILURES or self.max_failures > KeystrokeConfig.MAX_MAX_FAILURES:
            raise ValueError(f"max_failures must be between {KeystrokeConfig.MIN_MAX_FAILURES} and {KeystrokeConfig.MAX_MAX_FAILURES}")

    @staticmethod
    def _is_valid_key_format(key: str) -> bool:
        """Validate key format with whitelist-based validation."""
        # Check for duplicate modifiers first
        if key.count('C-') > 1 or key.count('S-') > 1 or key.count('A-') > 1:
            return False
        
        # Parse the key to extract modifiers and main key
        parts = key.split('-')
        main_key = parts[-1].lower()
        modifiers = parts[:-1] if len(parts) > 1 else []
        
        # Validate modifiers (must be C, S, or A)
        valid_modifiers = {'C', 'S', 'A'}
        if not all(mod in valid_modifiers for mod in modifiers):
            return False
        
        # Check for proper modifier order (C-S-A-)
        if len(modifiers) > 1:
            expected_order = ['C', 'S', 'A']
            modifier_positions = {mod: expected_order.index(mod) for mod in modifiers if mod in expected_order}
            if list(modifier_positions.keys()) != sorted(modifier_positions.keys(), key=lambda x: modifier_positions[x]):
                return False
        
        # Validate main key using whitelist approach
        # Single character keys (alphanumeric)
        if len(main_key) == 1 and main_key.isalnum():
            return True
        
        # Function keys (f1-f24)
        if re.match(r'^f([1-9]|1[0-9]|2[0-4])$', main_key):
            return True
        
        # Special keys from whitelist
        if main_key in KeystrokeConfig.VALID_SPECIAL_KEYS:
            return True
        
        # Reject anything else
        return False
    
    @classmethod
    def from_string(cls, line: str) -> Optional['KeystrokeConfig']:
        """Parse keystroke from config file line with enhanced validation."""
        if not isinstance(line, str):
            raise ValueError("Input line must be a string")
        
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        
        # Prevent excessively long lines that might indicate an attack
        if len(line) > 1000:
            raise ValueError("Configuration line too long (max 1000 characters)")
            
        parts = line.split(None, 2)  # Split into max 3 parts
        if len(parts) < 2:
            raise ValueError(f"Invalid keystroke format: {line}")
            
        key = parts[0]
        try:
            delay = float(parts[1])
        except ValueError:
            raise ValueError(f"Invalid delay value: {parts[1]}")
            
        # Optional description (everything after second space)
        description = parts[2] if len(parts) > 2 else ""
        
        return cls(key=key, delay=delay, description=description)
    
    def to_string(self) -> str:
        """Convert keystroke to config file line format."""
        base = f"{self.key} {self.delay}"
        if self.description:
            base += f" {self.description}"
        return base


# Class constants (defined after the class to avoid dataclass conflicts)
KeystrokeConfig.MAX_DESCRIPTION_LENGTH = 500
KeystrokeConfig.MAX_TAG_LENGTH = 50
KeystrokeConfig.MAX_TAGS_COUNT = 20
KeystrokeConfig.MAX_KEY_LENGTH = 50
KeystrokeConfig.MIN_PRIORITY = -100
KeystrokeConfig.MAX_PRIORITY = 100
KeystrokeConfig.MIN_MAX_FAILURES = 1
KeystrokeConfig.MAX_MAX_FAILURES = 100

# Whitelist of valid special key names
KeystrokeConfig.VALID_SPECIAL_KEYS = {
    'space', 'enter', 'return', 'tab', 'escape', 'esc', 'backspace', 'delete', 'del',
    'insert', 'ins', 'home', 'end', 'pageup', 'pagedown', 'up', 'down', 'left', 'right',
    'capslock', 'numlock', 'scrolllock', 'printscreen', 'pause', 'break', 'menu',
    'lwin', 'rwin', 'apps', 'sleep', 'wake', 'volumeup', 'volumedown', 'mute',
    'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
    'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f20', 'f21', 'f22', 'f23', 'f24',
    'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'num7', 'num8', 'num9',
    'multiply', 'add', 'separator', 'subtract', 'decimal', 'divide'
}


@dataclass
class AppSettings:
    """Application settings with validation and type safety."""
    
    # Core automation settings
    toggle_key: str = '~'
    start_time_stagger: float = 1.7
    order_obeyed: bool = False
    global_cooldown: float = 1.5
    
    # UI preferences
    indicator_type: IndicatorType = IndicatorType.GDI
    show_notifications: bool = True
    minimize_to_tray: bool = True
    
    # Performance settings
    keystroke_method: KeystrokeMethod = KeystrokeMethod.WINDOWS_API
    high_performance_mode: bool = False
    logging_enabled: bool = True
    
    # Safety settings
    fail_safe_enabled: bool = True
    max_execution_time: float = 3600.0  # 1 hour
    emergency_stop_key: str = 'ctrl+shift+esc'
    
    # Update settings
    check_updates_on_startup: bool = True
    auto_install_updates: bool = False
    update_channel: str = 'stable'  # 'stable', 'beta', 'dev'
    
    # Advanced settings
    thread_pool_size: int = 2
    memory_limit_mb: int = 100
    log_retention_days: int = 7
    config_backup_count: int = 5
    
    # Input validation constants
    MAX_KEY_LENGTH = 20
    MAX_UPDATE_CHANNEL_LENGTH = 20
    MIN_STAGGER_TIME = 0.0
    MAX_STAGGER_TIME = 60.0
    MIN_COOLDOWN = 0.1
    MAX_COOLDOWN = 300.0
    MIN_EXECUTION_TIME = 1.0
    MAX_EXECUTION_TIME = 86400.0  # 24 hours
    MIN_THREAD_POOL = 1
    MAX_THREAD_POOL = 10
    MIN_MEMORY_LIMIT = 10
    MAX_MEMORY_LIMIT = 1000
    MIN_RETENTION_DAYS = 1
    MAX_RETENTION_DAYS = 365
    MIN_BACKUP_COUNT = 1
    MAX_BACKUP_COUNT = 20
    
    # Valid update channels whitelist
    VALID_UPDATE_CHANNELS = {'stable', 'beta', 'dev'}
    
    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Comprehensive validation of all settings with enhanced checks."""
        self._validate_toggle_key()
        self._validate_timing_settings()
        self._validate_emergency_stop_key()
        self._validate_update_channel()
        self._validate_performance_settings()
        self._validate_maintenance_settings()
        self._validate_types()
    
    def _validate_toggle_key(self) -> None:
        """Validate toggle key with enhanced checks."""
        if not isinstance(self.toggle_key, str):
            raise ValueError("toggle_key must be a string")
        
        if not self.toggle_key or not self.toggle_key.strip():
            raise ValueError("toggle_key cannot be empty")
        
        self.toggle_key = self.toggle_key.strip()
        
        if len(self.toggle_key) > self.MAX_KEY_LENGTH:
            raise ValueError(f"toggle_key cannot exceed {self.MAX_KEY_LENGTH} characters")
        
        # Check for dangerous characters
        if any(ord(char) < 32 for char in self.toggle_key):
            raise ValueError("toggle_key contains invalid control characters")
        
        # Validate against common problematic keys
        problematic_keys = {'ctrl+alt+del', 'alt+f4', 'win+l', 'ctrl+shift+esc'}
        if self.toggle_key.lower() in problematic_keys:
            raise ValueError(f"toggle_key '{self.toggle_key}' conflicts with system shortcuts")
    
    def _validate_timing_settings(self) -> None:
        """Validate timing-related settings with strict bounds."""
        # Validate start_time_stagger
        if not isinstance(self.start_time_stagger, (int, float)):
            raise ValueError("start_time_stagger must be numeric")
        
        if self.start_time_stagger < self.MIN_STAGGER_TIME:
            raise ValueError(f"start_time_stagger must be at least {self.MIN_STAGGER_TIME}")
        
        if self.start_time_stagger > self.MAX_STAGGER_TIME:
            raise ValueError(f"start_time_stagger cannot exceed {self.MAX_STAGGER_TIME} seconds")
        
        # Validate global_cooldown
        if not isinstance(self.global_cooldown, (int, float)):
            raise ValueError("global_cooldown must be numeric")
        
        if self.global_cooldown < self.MIN_COOLDOWN:
            raise ValueError(f"global_cooldown must be at least {self.MIN_COOLDOWN} seconds")
        
        if self.global_cooldown > self.MAX_COOLDOWN:
            raise ValueError(f"global_cooldown cannot exceed {self.MAX_COOLDOWN} seconds")
        
        # Validate max_execution_time
        if not isinstance(self.max_execution_time, (int, float)):
            raise ValueError("max_execution_time must be numeric")
        
        if self.max_execution_time < self.MIN_EXECUTION_TIME:
            raise ValueError(f"max_execution_time must be at least {self.MIN_EXECUTION_TIME} second")
        
        if self.max_execution_time > self.MAX_EXECUTION_TIME:
            raise ValueError(f"max_execution_time cannot exceed {self.MAX_EXECUTION_TIME} seconds (24 hours)")
    
    def _validate_emergency_stop_key(self) -> None:
        """Validate emergency stop key with enhanced security checks."""
        if not isinstance(self.emergency_stop_key, str):
            raise ValueError("emergency_stop_key must be a string")
        
        if not self.emergency_stop_key or not self.emergency_stop_key.strip():
            raise ValueError("emergency_stop_key cannot be empty")
        
        self.emergency_stop_key = self.emergency_stop_key.strip().lower()
        
        if len(self.emergency_stop_key) > self.MAX_KEY_LENGTH:
            raise ValueError(f"emergency_stop_key cannot exceed {self.MAX_KEY_LENGTH} characters")
        
        # Validate emergency key format (should include modifiers for safety)
        if not ('+' in self.emergency_stop_key and 
                any(mod in self.emergency_stop_key for mod in ['ctrl', 'alt', 'shift'])):
            raise ValueError("emergency_stop_key should include modifier keys for safety (e.g., 'ctrl+shift+esc')")
        
        # Check for dangerous characters
        if any(ord(char) < 32 for char in self.emergency_stop_key):
            raise ValueError("emergency_stop_key contains invalid control characters")
    
    def _validate_update_channel(self) -> None:
        """Validate update channel with whitelist."""
        if not isinstance(self.update_channel, str):
            raise ValueError("update_channel must be a string")
        
        if not self.update_channel or not self.update_channel.strip():
            raise ValueError("update_channel cannot be empty")
        
        self.update_channel = self.update_channel.strip().lower()
        
        if len(self.update_channel) > self.MAX_UPDATE_CHANNEL_LENGTH:
            raise ValueError(f"update_channel cannot exceed {self.MAX_UPDATE_CHANNEL_LENGTH} characters")
        
        if self.update_channel not in self.VALID_UPDATE_CHANNELS:
            raise ValueError(f"update_channel must be one of: {', '.join(self.VALID_UPDATE_CHANNELS)}")
    
    def _validate_performance_settings(self) -> None:
        """Validate performance-related settings with strict bounds."""
        # Validate thread_pool_size
        if not isinstance(self.thread_pool_size, int):
            raise ValueError("thread_pool_size must be an integer")
        
        if self.thread_pool_size < self.MIN_THREAD_POOL or self.thread_pool_size > self.MAX_THREAD_POOL:
            raise ValueError(f"thread_pool_size must be between {self.MIN_THREAD_POOL} and {self.MAX_THREAD_POOL}")
        
        # Validate memory_limit_mb
        if not isinstance(self.memory_limit_mb, int):
            raise ValueError("memory_limit_mb must be an integer")
        
        if self.memory_limit_mb < self.MIN_MEMORY_LIMIT or self.memory_limit_mb > self.MAX_MEMORY_LIMIT:
            raise ValueError(f"memory_limit_mb must be between {self.MIN_MEMORY_LIMIT} and {self.MAX_MEMORY_LIMIT}")
    
    def _validate_maintenance_settings(self) -> None:
        """Validate maintenance-related settings."""
        # Validate log_retention_days
        if not isinstance(self.log_retention_days, int):
            raise ValueError("log_retention_days must be an integer")
        
        if self.log_retention_days < self.MIN_RETENTION_DAYS or self.log_retention_days > self.MAX_RETENTION_DAYS:
            raise ValueError(f"log_retention_days must be between {self.MIN_RETENTION_DAYS} and {self.MAX_RETENTION_DAYS}")
        
        # Validate config_backup_count
        if not isinstance(self.config_backup_count, int):
            raise ValueError("config_backup_count must be an integer")
        
        if self.config_backup_count < self.MIN_BACKUP_COUNT or self.config_backup_count > self.MAX_BACKUP_COUNT:
            raise ValueError(f"config_backup_count must be between {self.MIN_BACKUP_COUNT} and {self.MAX_BACKUP_COUNT}")
    
    def _validate_types(self) -> None:
        """Validate all boolean and enum types."""
        # Boolean validations
        boolean_fields = [
            'order_obeyed', 'show_notifications', 'minimize_to_tray',
            'high_performance_mode', 'logging_enabled', 'fail_safe_enabled',
            'check_updates_on_startup', 'auto_install_updates'
        ]
        
        for field in boolean_fields:
            value = getattr(self, field)
            if not isinstance(value, bool):
                raise ValueError(f"{field} must be a boolean")
        
        # Enum validations
        if not isinstance(self.indicator_type, IndicatorType):
            raise ValueError(f"indicator_type must be a valid IndicatorType, got {type(self.indicator_type)}")
        
        if not isinstance(self.keystroke_method, KeystrokeMethod):
            raise ValueError(f"keystroke_method must be a valid KeystrokeMethod, got {type(self.keystroke_method)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for JSON serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """Create AppSettings from dictionary with enhanced validation."""
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary")
        
        # Prevent excessively large configuration data
        if len(str(data)) > 10000:  # 10KB limit
            raise ValueError("Configuration data too large")
        
        # Create a copy to avoid modifying the original
        data = data.copy()
        
        # Handle enum conversions with validation
        if 'indicator_type' in data:
            try:
                data['indicator_type'] = IndicatorType(data['indicator_type'])
            except ValueError:
                raise ValueError(f"Invalid indicator_type: {data['indicator_type']}")
        
        if 'keystroke_method' in data:
            try:
                data['keystroke_method'] = KeystrokeMethod(data['keystroke_method'])
            except ValueError:
                raise ValueError(f"Invalid keystroke_method: {data['keystroke_method']}")
        
        # Filter out unknown fields to prevent injection
        valid_fields = {
            'toggle_key', 'start_time_stagger', 'order_obeyed', 'global_cooldown',
            'indicator_type', 'show_notifications', 'minimize_to_tray',
            'keystroke_method', 'high_performance_mode', 'logging_enabled',
            'fail_safe_enabled', 'max_execution_time', 'emergency_stop_key',
            'check_updates_on_startup', 'auto_install_updates', 'update_channel',
            'thread_pool_size', 'memory_limit_mb', 'log_retention_days', 'config_backup_count'
        }
        
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # Log filtered fields for security monitoring
        filtered_out = set(data.keys()) - valid_fields
        if filtered_out:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Filtered out unknown configuration fields: {filtered_out}")
        
        return cls(**filtered_data)


@dataclass
class ProfileConfig:
    """Configuration profile that bundles settings and keystrokes."""
    
    name: str
    description: str = ""
    settings: AppSettings = field(default_factory=AppSettings)
    keystrokes: List[KeystrokeConfig] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    author: str = ""
    version: str = "1.0"
    
    # Input validation constants
    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_AUTHOR_LENGTH = 100
    MAX_VERSION_LENGTH = 20
    MAX_KEYSTROKES_COUNT = 1000
    MAX_TAGS_COUNT = 50
    MAX_TAG_LENGTH = 50
    
    # Valid version pattern
    VERSION_PATTERN = re.compile(r'^\d+\.\d+(\.\d+)?(-[a-zA-Z0-9]+)?$')
    
    def __post_init__(self) -> None:
        """Validate profile after initialization with comprehensive checks."""
        self._validate_name()
        self._validate_description()
        self._validate_author()
        self._validate_version()
        self._validate_keystrokes()
        self._validate_tags()
        self._validate_timestamps()
        self._validate_settings()
    
    def _validate_name(self) -> None:
        """Validate profile name with enhanced security checks."""
        if not isinstance(self.name, str):
            raise ValueError("Profile name must be a string")
        
        if not self.name or not self.name.strip():
            raise ValueError("Profile name cannot be empty")
        
        self.name = self.name.strip()
        
        if len(self.name) > self.MAX_NAME_LENGTH:
            raise ValueError(f"Profile name cannot exceed {self.MAX_NAME_LENGTH} characters")
        
        # Check for dangerous characters
        if any(ord(char) < 32 for char in self.name):
            raise ValueError("Profile name contains invalid control characters")
        
        # Validate profile name (alphanumeric, spaces, hyphens, underscores only for file system safety)
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', self.name):
            raise ValueError("Profile name contains invalid characters (only letters, numbers, spaces, hyphens, and underscores allowed)")
        
        # Prevent reserved names that could cause issues
        reserved_names = {
            'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5', 
            'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 
            'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
        }
        if self.name.lower() in reserved_names:
            raise ValueError(f"Profile name '{self.name}' is a reserved system name")
    
    def _validate_description(self) -> None:
        """Validate description with length and content checks."""
        if not isinstance(self.description, str):
            raise ValueError("Description must be a string")
        
        if len(self.description) > self.MAX_DESCRIPTION_LENGTH:
            raise ValueError(f"Description cannot exceed {self.MAX_DESCRIPTION_LENGTH} characters")
        
        # Check for control characters in description (except tabs, newlines, carriage returns)
        if any(ord(char) < 32 and char not in '\t\n\r' for char in self.description):
            raise ValueError("Description contains invalid control characters")
    
    def _validate_author(self) -> None:
        """Validate author field with length and content checks."""
        if not isinstance(self.author, str):
            raise ValueError("Author must be a string")
        
        if len(self.author) > self.MAX_AUTHOR_LENGTH:
            raise ValueError(f"Author cannot exceed {self.MAX_AUTHOR_LENGTH} characters")
        
        # Check for control characters
        if any(ord(char) < 32 for char in self.author):
            raise ValueError("Author contains invalid control characters")
        
        # If author is provided, validate format (letters, numbers, spaces, basic punctuation)
        if self.author and not re.match(r'^[a-zA-Z0-9_\-\s\.\@]+$', self.author):
            raise ValueError("Author contains invalid characters")
    
    def _validate_version(self) -> None:
        """Validate version string with semantic version checking."""
        if not isinstance(self.version, str):
            raise ValueError("Version must be a string")
        
        if not self.version or not self.version.strip():
            raise ValueError("Version cannot be empty")
        
        self.version = self.version.strip()
        
        if len(self.version) > self.MAX_VERSION_LENGTH:
            raise ValueError(f"Version cannot exceed {self.MAX_VERSION_LENGTH} characters")
        
        # Validate semantic version format
        if not self.VERSION_PATTERN.match(self.version):
            raise ValueError("Version must follow semantic versioning format (e.g., '1.0', '1.0.0', '1.0.0-beta')")
    
    def _validate_keystrokes(self) -> None:
        """Validate keystrokes list with size and content checks."""
        if not isinstance(self.keystrokes, list):
            raise ValueError("Keystrokes must be a list")
        
        if len(self.keystrokes) > self.MAX_KEYSTROKES_COUNT:
            raise ValueError(f"Cannot have more than {self.MAX_KEYSTROKES_COUNT} keystrokes")
        
        # Validate each keystroke
        for i, keystroke in enumerate(self.keystrokes):
            if not isinstance(keystroke, KeystrokeConfig):
                raise ValueError(f"Keystroke {i} must be a KeystrokeConfig instance")
        
        # Check for duplicate keys
        enabled_keys = [ks.key for ks in self.keystrokes if ks.enabled]
        if len(enabled_keys) != len(set(enabled_keys)):
            duplicates = [key for key in enabled_keys if enabled_keys.count(key) > 1]
            raise ValueError(f"Duplicate keystroke definitions found: {set(duplicates)}")
    
    def _validate_tags(self) -> None:
        """Validate tags list with comprehensive checks."""
        if not isinstance(self.tags, list):
            raise ValueError("Tags must be a list")
        
        if len(self.tags) > self.MAX_TAGS_COUNT:
            raise ValueError(f"Cannot have more than {self.MAX_TAGS_COUNT} tags")
        
        seen_tags = set()
        for i, tag in enumerate(self.tags):
            if not isinstance(tag, str):
                raise ValueError(f"Tag {i} must be a string")
            
            tag = tag.strip()
            if not tag:
                raise ValueError(f"Tag {i} cannot be empty")
            
            if len(tag) > self.MAX_TAG_LENGTH:
                raise ValueError(f"Tag {i} cannot exceed {self.MAX_TAG_LENGTH} characters")
            
            # Check for duplicates (case-insensitive)
            tag_lower = tag.lower()
            if tag_lower in seen_tags:
                raise ValueError(f"Duplicate tag found: {tag}")
            seen_tags.add(tag_lower)
            
            # Validate tag format (alphanumeric, spaces, hyphens, underscores)
            if not re.match(r'^[a-zA-Z0-9_\-\s]+$', tag):
                raise ValueError(f"Tag '{tag}' contains invalid characters")
            
            # Update the cleaned tag
            self.tags[i] = tag
    
    def _validate_timestamps(self) -> None:
        """Validate timestamp fields if provided."""
        timestamp_fields = ['created_at', 'modified_at']
        
        for field_name in timestamp_fields:
            value = getattr(self, field_name)
            if value is not None:
                if not isinstance(value, str):
                    raise ValueError(f"{field_name} must be a string or None")
                
                if len(value) > 50:  # ISO format should be much shorter
                    raise ValueError(f"{field_name} timestamp too long")
                
                # Try to validate ISO format (basic check)
                try:
                    # Allow both with and without microseconds
                    for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            datetime.strptime(value, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        raise ValueError(f"{field_name} is not in valid ISO format")
                except ImportError:
                    # If datetime is not available, just do basic format check
                    if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
                        raise ValueError(f"{field_name} is not in valid ISO format")
    
    def _validate_settings(self) -> None:
        """Validate the settings object."""
        if not isinstance(self.settings, AppSettings):
            raise ValueError("Settings must be an AppSettings instance")
    
    def add_keystroke(self, keystroke: KeystrokeConfig) -> None:
        """Add a keystroke to this profile with validation."""
        if not isinstance(keystroke, KeystrokeConfig):
            raise ValueError("keystroke must be a KeystrokeConfig instance")
        
        if len(self.keystrokes) >= self.MAX_KEYSTROKES_COUNT:
            raise ValueError(f"Cannot add keystroke: maximum limit of {self.MAX_KEYSTROKES_COUNT} reached")
        
        # Check for duplicate key
        if keystroke.enabled and any(ks.key == keystroke.key and ks.enabled for ks in self.keystrokes):
            raise ValueError(f"Keystroke with key '{keystroke.key}' already exists")
        
        self.keystrokes.append(keystroke)
    
    def remove_keystroke(self, index: int) -> None:
        """Remove a keystroke by index with validation."""
        if not isinstance(index, int):
            raise ValueError("Index must be an integer")
        
        if 0 <= index < len(self.keystrokes):
            del self.keystrokes[index]
        else:
            raise IndexError(f"Keystroke index {index} out of range (0-{len(self.keystrokes)-1})")
    
    def get_enabled_keystrokes(self) -> List[KeystrokeConfig]:
        """Get only enabled keystrokes."""
        return [ks for ks in self.keystrokes if ks.enabled]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'settings': self.settings.to_dict(),
            'keystrokes': [ks.to_string() for ks in self.keystrokes],
            'tags': self.tags,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'author': self.author,
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfileConfig':
        """Create ProfileConfig from dictionary with validation."""
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary")
        
        # Prevent excessively large profile data
        if len(str(data)) > 100000:  # 100KB limit
            raise ValueError("Profile data too large")
        
        # Create a copy to avoid modifying the original
        data = data.copy()
        
        # Filter out unknown fields
        valid_fields = {
            'name', 'description', 'settings', 'keystrokes', 'tags',
            'created_at', 'modified_at', 'author', 'version'
        }
        
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # Convert nested objects
        if 'settings' in filtered_data:
            filtered_data['settings'] = AppSettings.from_dict(filtered_data['settings'])
        
        if 'keystrokes' in filtered_data and isinstance(filtered_data['keystrokes'], list):
            keystrokes = []
            for ks_data in filtered_data['keystrokes']:
                if isinstance(ks_data, str):
                    # Parse from string format
                    ks = KeystrokeConfig.from_string(ks_data)
                    if ks:
                        keystrokes.append(ks)
                elif isinstance(ks_data, dict):
                    # Create from dict
                    keystrokes.append(KeystrokeConfig(**ks_data))
            filtered_data['keystrokes'] = keystrokes
        
        return cls(**filtered_data)


# Legacy compatibility functions for migration
def migrate_legacy_settings(old_settings: Dict[str, Any]) -> AppSettings:
    """Migrate settings from old format to new format."""
    # Handle renamed fields
    migrations = {
        'pause_time': 'start_time_stagger',
        'visual_indicator': 'indicator_type',
    }
    
    migrated = {}
    for old_key, value in old_settings.items():
        new_key = migrations.get(old_key, old_key)
        migrated[new_key] = value
    
    # Convert string enum values to enum instances
    if 'indicator_type' in migrated and isinstance(migrated['indicator_type'], str):
        try:
            migrated['indicator_type'] = IndicatorType(migrated['indicator_type'])
        except ValueError:
            migrated['indicator_type'] = IndicatorType.GDI
    
    if 'keystroke_method' in migrated and isinstance(migrated['keystroke_method'], str):
        try:
            migrated['keystroke_method'] = KeystrokeMethod(migrated['keystroke_method'])
        except ValueError:
            migrated['keystroke_method'] = KeystrokeMethod.WINDOWS_API
    
    return AppSettings.from_dict(migrated) 