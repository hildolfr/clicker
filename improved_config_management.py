"""
Improved Configuration Management Example
Replaces scattered global variables with a proper configuration system
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import os
import logging
from pathlib import Path
import jsonschema
from jsonschema import validate

@dataclass
class KeystrokeConfig:
    """Configuration for a single keystroke"""
    key: str
    delay: float
    enabled: bool = True
    description: str = ""
    
    def __post_init__(self):
        if self.delay < 0.1:
            raise ValueError("Delay must be at least 0.1 seconds")
        
    @classmethod
    def from_string(cls, line: str) -> Optional['KeystrokeConfig']:
        """Parse keystroke from config file line"""
        line = line.strip()
        if not line or line.startswith('#'):
            return None
            
        parts = line.split()
        if len(parts) < 2:
            raise ValueError(f"Invalid keystroke format: {line}")
            
        key = parts[0]
        try:
            delay = float(parts[1])
        except ValueError:
            raise ValueError(f"Invalid delay value: {parts[1]}")
            
        description = ' '.join(parts[2:]) if len(parts) > 2 else ""
        return cls(key=key, delay=delay, description=description)

@dataclass
class AppSettings:
    """Application settings with validation and defaults"""
    # Core settings
    toggle_key: str = '~'
    start_time_stagger: float = 1.7
    order_obeyed: bool = False
    global_cooldown: float = 1.5
    
    # UI settings
    indicator_type: str = 'gdi'
    show_notifications: bool = True
    
    # Update settings
    check_updates_on_startup: bool = True
    auto_install_updates: bool = False
    
    # Performance settings
    logging_enabled: bool = True
    high_performance_mode: bool = False
    
    # Advanced settings
    keystroke_method: str = 'windows_api'  # 'windows_api', 'sendkeys', 'pyautogui'
    fail_safe_enabled: bool = True
    max_execution_time: float = 3600.0  # 1 hour max
    
    def __post_init__(self):
        """Validate settings after initialization"""
        self.validate()
    
    def validate(self):
        """Validate all settings"""
        if self.start_time_stagger < 0:
            raise ValueError("start_time_stagger must be non-negative")
        
        if self.global_cooldown < 0.1:
            raise ValueError("global_cooldown must be at least 0.1 seconds")
            
        if self.indicator_type not in ['pygame', 'gdi', 'none']:
            raise ValueError("indicator_type must be 'pygame', 'gdi', or 'none'")
            
        if self.keystroke_method not in ['windows_api', 'sendkeys', 'pyautogui']:
            raise ValueError("Invalid keystroke_method")

class ConfigManager:
    """Centralized configuration management"""
    
    SETTINGS_SCHEMA = {
        "type": "object",
        "properties": {
            "toggle_key": {"type": "string", "minLength": 1},
            "start_time_stagger": {"type": "number", "minimum": 0},
            "order_obeyed": {"type": "boolean"},
            "global_cooldown": {"type": "number", "minimum": 0.1},
            "indicator_type": {"enum": ["pygame", "gdi", "none"]},
            "check_updates_on_startup": {"type": "boolean"},
            "auto_install_updates": {"type": "boolean"},
            "logging_enabled": {"type": "boolean"},
            "high_performance_mode": {"type": "boolean"},
            "keystroke_method": {"enum": ["windows_api", "sendkeys", "pyautogui"]},
            "fail_safe_enabled": {"type": "boolean"},
            "max_execution_time": {"type": "number", "minimum": 1}
        },
        "additionalProperties": True  # Allow for future expansion
    }
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path.cwd()
        self.settings_file = self.config_dir / "settings.json"
        self.keystrokes_file = self.config_dir / "keystrokes.txt"
        
        self._settings: Optional[AppSettings] = None
        self._keystrokes: List[KeystrokeConfig] = []
        self._change_callbacks: List[callable] = []
        
        self.logger = logging.getLogger(__name__)
    
    @property
    def settings(self) -> AppSettings:
        """Get current settings, loading if necessary"""
        if self._settings is None:
            self.load_settings()
        return self._settings
    
    @property
    def keystrokes(self) -> List[KeystrokeConfig]:
        """Get current keystrokes, loading if necessary"""
        if not self._keystrokes:
            self.load_keystrokes()
        return self._keystrokes
    
    def load_settings(self) -> AppSettings:
        """Load settings from file with validation and migration"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                
                # Validate against schema
                validate(data, self.SETTINGS_SCHEMA)
                
                # Handle legacy field names
                data = self._migrate_settings(data)
                
                self._settings = AppSettings(**data)
            else:
                self._settings = AppSettings()
                self.save_settings()
                
        except (json.JSONDecodeError, jsonschema.ValidationError, ValueError) as e:
            self.logger.error(f"Invalid settings file: {e}")
            self.logger.info("Using default settings")
            self._settings = AppSettings()
            self.save_settings()
        
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            self._settings = AppSettings()
        
        return self._settings
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            # Convert to dict and remove None values
            data = {k: v for k, v in self._settings.__dict__.items() if v is not None}
            
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=4)
                
            self.logger.info("Settings saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            raise
    
    def load_keystrokes(self) -> List[KeystrokeConfig]:
        """Load keystrokes from file with validation"""
        self._keystrokes = []
        
        try:
            if self.keystrokes_file.exists():
                with open(self.keystrokes_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            keystroke = KeystrokeConfig.from_string(line)
                            if keystroke:
                                self._keystrokes.append(keystroke)
                        except ValueError as e:
                            self.logger.warning(f"Line {line_num}: {e}")
            else:
                # Create default keystrokes file
                self._create_default_keystrokes()
                
        except Exception as e:
            self.logger.error(f"Error loading keystrokes: {e}")
            self._create_default_keystrokes()
        
        return self._keystrokes
    
    def save_keystrokes(self):
        """Save keystrokes to file"""
        try:
            with open(self.keystrokes_file, 'w') as f:
                f.write("# Clicker Keystrokes Configuration\n")
                f.write("# Format: [KEY] [DELAY] [DESCRIPTION]\n\n")
                
                for keystroke in self._keystrokes:
                    if keystroke.enabled:
                        line = f"{keystroke.key} {keystroke.delay}"
                        if keystroke.description:
                            line += f" {keystroke.description}"
                        f.write(line + "\n")
                    else:
                        f.write(f"# DISABLED: {keystroke.key} {keystroke.delay} {keystroke.description}\n")
                        
            self.logger.info("Keystrokes saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving keystrokes: {e}")
            raise
    
    def _migrate_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle migration of legacy setting names"""
        migrations = {
            'pause_time': 'start_time_stagger',  # Legacy name
            'visual_indicator': 'indicator_type',  # Legacy name
        }
        
        for old_key, new_key in migrations.items():
            if old_key in data and new_key not in data:
                data[new_key] = data.pop(old_key)
                self.logger.info(f"Migrated setting: {old_key} -> {new_key}")
        
        return data
    
    def _create_default_keystrokes(self):
        """Create default keystrokes configuration"""
        defaults = [
            KeystrokeConfig("1", 2.0, description="Number key 1"),
            KeystrokeConfig("2", 2.0, description="Number key 2"),
            KeystrokeConfig("3", 2.0, description="Number key 3"),
        ]
        
        self._keystrokes = defaults
        self.save_keystrokes()
    
    def add_change_callback(self, callback: callable):
        """Add callback for configuration changes"""
        self._change_callbacks.append(callback)
    
    def notify_change(self):
        """Notify all callbacks of configuration change"""
        for callback in self._change_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in change callback: {e}")
    
    def reload(self):
        """Reload all configuration from files"""
        self._settings = None
        self._keystrokes = []
        self.load_settings()
        self.load_keystrokes()
        self.notify_change()
        self.logger.info("Configuration reloaded")

# Usage example:
if __name__ == "__main__":
    config = ConfigManager()
    
    # Access settings
    print(f"Toggle key: {config.settings.toggle_key}")
    print(f"Global cooldown: {config.settings.global_cooldown}")
    
    # Access keystrokes
    for keystroke in config.keystrokes:
        print(f"Key: {keystroke.key}, Delay: {keystroke.delay}")
    
    # Modify and save
    config.settings.toggle_key = "F1"
    config.save_settings() 