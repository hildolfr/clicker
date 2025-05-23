# Clicker API Documentation

## Overview

Clicker is a professional Windows automation tool designed with clean architecture and comprehensive testing. This document provides detailed API documentation for all public interfaces.

## Table of Contents

- [Core Application](#core-application)
- [Configuration Management](#configuration-management)
- [Automation Engine](#automation-engine)
- [System Integration](#system-integration)
- [UI Components](#ui-components)
- [Utilities](#utilities)
- [Error Handling](#error-handling)
- [Configuration Format](#configuration-format)
- [Examples](#examples)

## Core Application

### ClickerApp

The main application class that coordinates all components.

```python
from clicker import ClickerApp

app = ClickerApp(config_dir=None)
exit_code = app.run()
```

#### Constructor

```python
ClickerApp(config_dir: Optional[Path] = None)
```

**Parameters:**
- `config_dir` (Optional[Path]): Custom configuration directory. Defaults to user's Documents/clicker.

#### Methods

##### run() -> int

Starts the application and runs the main event loop.

**Returns:**
- `int`: Exit code (0 for success, non-zero for error)

**Example:**
```python
import sys
from clicker import ClickerApp

def main():
    app = ClickerApp()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
```

##### shutdown() -> None

Initiates graceful application shutdown.

**Example:**
```python
app = ClickerApp()
# Later...
app.shutdown()  # Triggers graceful shutdown
```

## Configuration Management

### ConfigManager

Handles loading, saving, and validation of configuration files.

```python
from clicker.config.manager import ConfigManager

config_manager = ConfigManager(config_dir=None)
```

#### Constructor

```python
ConfigManager(config_dir: Optional[Path] = None)
```

**Parameters:**
- `config_dir` (Optional[Path]): Configuration directory path

#### Methods

##### load_configuration(progress_callback: Optional[Callable] = None) -> bool

Loads application configuration from files.

**Parameters:**
- `progress_callback` (Optional[Callable]): Progress reporting function

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
def progress_handler(operation: str, current: int, total: int):
    print(f"{operation}: {current}/{total}")

success = config_manager.load_configuration(progress_callback=progress_handler)
if success:
    print("Configuration loaded successfully")
```

##### save_settings(settings: AppSettings, timeout: float = 30.0) -> bool

Saves application settings with timeout protection.

**Parameters:**
- `settings` (AppSettings): Settings object to save
- `timeout` (float): Maximum time to wait for save operation

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
from clicker.config.models import AppSettings

settings = AppSettings(
    toggle_key='F1',
    global_cooldown=2.0,
    show_notifications=True
)

success = config_manager.save_settings(settings)
```

##### validate_configuration() -> List[str]

Validates current configuration and returns any issues found.

**Returns:**
- `List[str]`: List of validation error messages

**Example:**
```python
issues = config_manager.validate_configuration()
if issues:
    for issue in issues:
        print(f"Configuration issue: {issue}")
```

### Configuration Models

#### AppSettings

Application-wide settings with validation.

```python
from clicker.config.models import AppSettings
from clicker.config.enums import IndicatorType, KeystrokeMethod

settings = AppSettings(
    toggle_key='~',
    start_time_stagger=1.7,
    order_obeyed=False,
    global_cooldown=1.5,
    indicator_type=IndicatorType.GDI,
    keystroke_method=KeystrokeMethod.WINDOWS_API,
    emergency_stop_key='ctrl+shift+esc'
)
```

##### Core Settings

- `toggle_key` (str): Key to toggle automation on/off
- `start_time_stagger` (float): Delay before starting automation (0.0-60.0 seconds)
- `order_obeyed` (bool): Whether to execute keystrokes in order
- `global_cooldown` (float): Minimum delay between keystrokes (0.1-300.0 seconds)

##### UI Settings

- `indicator_type` (IndicatorType): Visual indicator type (GDI, PYGAME)
- `show_notifications` (bool): Show system notifications
- `minimize_to_tray` (bool): Minimize to system tray

##### Performance Settings

- `keystroke_method` (KeystrokeMethod): Method for sending keystrokes
- `high_performance_mode` (bool): Enable high performance optimizations
- `thread_pool_size` (int): Number of worker threads (1-10)
- `memory_limit_mb` (int): Memory usage limit in MB (10-1000)

##### Safety Settings

- `fail_safe_enabled` (bool): Enable fail-safe mechanisms
- `max_execution_time` (float): Maximum automation runtime in seconds
- `emergency_stop_key` (str): Emergency stop key combination

**Example:**
```python
# Create settings with validation
settings = AppSettings(
    toggle_key='F2',
    global_cooldown=1.0,
    indicator_type=IndicatorType.GDI,
    emergency_stop_key='ctrl+alt+q'
)

# Convert to/from dictionary
settings_dict = settings.to_dict()
restored_settings = AppSettings.from_dict(settings_dict)
```

#### KeystrokeConfig

Configuration for individual keystroke automation.

```python
from clicker.config.models import KeystrokeConfig

keystroke = KeystrokeConfig(
    key='a',
    delay=1.5,
    enabled=True,
    description="Press 'a' key",
    tags=['gaming', 'automation'],
    priority=5,
    max_failures=3
)
```

##### Properties

- `key` (str): Key combination to send (e.g., 'a', 'C-a', 'S-f1')
- `delay` (float): Delay between executions in seconds (0.1-3600.0)
- `enabled` (bool): Whether this keystroke is active
- `description` (str): Human-readable description (max 500 chars)
- `tags` (List[str]): Categorization tags (max 20 tags, 50 chars each)
- `priority` (int): Execution priority (0-10)
- `max_failures` (int): Maximum consecutive failures before disabling (1-10)

##### Methods

```python
# Parse from configuration file line
keystroke = KeystrokeConfig.from_string("a 1.5 Press 'a' key")

# Convert to configuration file format
line = keystroke.to_string()  # "a 1.5 Press 'a' key"
```

**Key Format Examples:**
```python
# Simple keys
KeystrokeConfig(key='a', delay=1.0)        # Press 'a'
KeystrokeConfig(key='f1', delay=2.0)       # Press F1
KeystrokeConfig(key='space', delay=1.5)    # Press spacebar

# Modified keys
KeystrokeConfig(key='C-a', delay=1.0)      # Ctrl+A
KeystrokeConfig(key='S-f1', delay=1.0)     # Shift+F1
KeystrokeConfig(key='C-S-a', delay=1.0)    # Ctrl+Shift+A
```

#### ProfileConfig

Configuration profile that bundles settings and keystrokes.

```python
from clicker.config.models import ProfileConfig, AppSettings, KeystrokeConfig

# Create a profile
profile = ProfileConfig(
    name="Gaming Profile",
    description="Optimized for gaming automation",
    author="User123",
    version="1.0",
    settings=AppSettings(global_cooldown=0.5),
    keystrokes=[
        KeystrokeConfig(key='1', delay=1.0, description='Heal'),
        KeystrokeConfig(key='2', delay=2.0, description='Attack')
    ],
    tags=['gaming', 'rpg']
)
```

##### Methods

```python
# Add keystroke
profile.add_keystroke(KeystrokeConfig(key='3', delay=1.5))

# Remove keystroke by index
profile.remove_keystroke(0)

# Get only enabled keystrokes
enabled = profile.get_enabled_keystrokes()

# Serialization
profile_dict = profile.to_dict()
restored_profile = ProfileConfig.from_dict(profile_dict)
```

## Automation Engine

### AutomationEngine

Core automation engine that executes keystrokes.

```python
from clicker.core.automation import AutomationEngine, AutomationState
from clicker.core.keystrokes import WindowsKeystrokeSender

# Create engine
keystroke_sender = WindowsKeystrokeSender()
engine = AutomationEngine(keystroke_sender)
```

#### Constructor

```python
AutomationEngine(keystroke_sender: KeystrokeSender)
```

**Parameters:**
- `keystroke_sender` (KeystrokeSender): Keystroke sender implementation

#### Methods

##### start(keystrokes: List[KeystrokeConfig], settings: AppSettings) -> bool

Starts automation with the given configuration.

**Parameters:**
- `keystrokes` (List[KeystrokeConfig]): Keystrokes to execute
- `settings` (AppSettings): Application settings

**Returns:**
- `bool`: True if started successfully

**Example:**
```python
keystrokes = [
    KeystrokeConfig(key='a', delay=1.0),
    KeystrokeConfig(key='b', delay=2.0)
]
settings = AppSettings(global_cooldown=1.5)

success = engine.start(keystrokes, settings)
if success:
    print("Automation started")
```

##### stop() -> bool

Stops automation gracefully.

**Returns:**
- `bool`: True if stopped successfully

##### pause() -> bool

Pauses automation (can be resumed).

**Returns:**
- `bool`: True if paused successfully

##### resume() -> bool

Resumes paused automation.

**Returns:**
- `bool`: True if resumed successfully

##### get_state() -> AutomationState

Gets current automation state.

**Returns:**
- `AutomationState`: Current state (STOPPED, STARTING, RUNNING, PAUSED, STOPPING, ERROR)

##### get_stats() -> ExecutionStats

Gets execution statistics.

**Returns:**
- `ExecutionStats`: Statistics object with counts and timing information

**Example:**
```python
stats = engine.get_stats()
print(f"Total executions: {stats.total_executions}")
print(f"Success rate: {stats.success_rate:.2%}")
print(f"Average execution time: {stats.average_execution_time:.3f}s")
```

### AutomationState

Enumeration of automation engine states.

```python
from clicker.core.automation import AutomationState

# Check state
if engine.get_state() == AutomationState.RUNNING:
    print("Automation is running")
```

**States:**
- `STOPPED`: Engine is stopped
- `STARTING`: Engine is starting up
- `RUNNING`: Engine is actively executing keystrokes
- `PAUSED`: Engine is paused (can be resumed)
- `STOPPING`: Engine is shutting down
- `ERROR`: Engine encountered an error

### ExecutionStats

Statistics about automation execution.

```python
stats = engine.get_stats()
```

**Properties:**
- `total_executions` (int): Total keystroke executions
- `successful_executions` (int): Successful executions
- `failed_executions` (int): Failed executions
- `success_rate` (float): Success rate (0.0-1.0)
- `average_execution_time` (float): Average execution time in seconds
- `total_runtime` (float): Total engine runtime in seconds

## System Integration

### WindowsKeystrokeSender

Windows-specific keystroke sender using Windows API.

```python
from clicker.core.keystrokes import WindowsKeystrokeSender

sender = WindowsKeystrokeSender()
```

#### Methods

##### send_keystroke(key: str, modifiers: Optional[List[str]] = None) -> bool

Sends a keystroke to the system.

**Parameters:**
- `key` (str): Key to send
- `modifiers` (Optional[List[str]]): Modifier keys ['shift', 'ctrl', 'alt']

**Returns:**
- `bool`: True if successful

**Example:**
```python
# Send simple key
success = sender.send_keystroke('a')

# Send key with modifiers
success = sender.send_keystroke('a', ['ctrl', 'shift'])

# Send function key
success = sender.send_keystroke('f1')
```

##### is_available() -> bool

Checks if keystroke sending is available.

**Returns:**
- `bool`: True if Windows API is available

### AdminChecker

Utility for checking and requesting administrator privileges.

```python
from clicker.system.admin import AdminChecker, request_admin_privileges

admin_checker = AdminChecker()
```

#### Methods

##### is_admin() -> bool

Checks if the current process has administrator privileges.

**Returns:**
- `bool`: True if running as administrator

##### request_admin_privileges() -> bool

Requests administrator privileges (restarts application if needed).

**Returns:**
- `bool`: True if successful or already admin

**Example:**
```python
if not admin_checker.is_admin():
    print("Administrator privileges required")
    if request_admin_privileges():
        print("Restarting with admin privileges...")
    else:
        print("Failed to obtain admin privileges")
```

### SingletonManager

Ensures only one instance of the application runs.

```python
from clicker.system.singleton import SingletonManager

singleton = SingletonManager()
```

#### Methods

##### acquire_lock() -> bool

Acquires singleton lock.

**Returns:**
- `bool`: True if lock acquired (no other instance running)

##### release_lock() -> None

Releases singleton lock.

**Example:**
```python
if singleton.acquire_lock():
    print("Application started")
    # Run application
    singleton.release_lock()
else:
    print("Another instance is already running")
```

## UI Components

### SystemTrayManager

Manages system tray icon and menu.

```python
from clicker.ui.gui.system_tray import SystemTrayManager

tray_manager = SystemTrayManager(app)
```

### IndicatorManager

Manages visual indicators for automation state.

```python
from clicker.ui.indicators import IndicatorManager
from clicker.ui.indicators.base import IndicatorState

indicator_manager = IndicatorManager()
```

#### Methods

##### set_state(state: IndicatorState) -> None

Sets the visual indicator state.

**Parameters:**
- `state` (IndicatorState): New state (HIDDEN, READY, ACTIVE, PAUSED, ERROR)

**Example:**
```python
# Show ready state
indicator_manager.set_state(IndicatorState.READY)

# Show active state
indicator_manager.set_state(IndicatorState.ACTIVE)

# Hide indicator
indicator_manager.set_state(IndicatorState.HIDDEN)
```

## Utilities

### AutoUpdater

Handles automatic application updates.

```python
from clicker.utils.updater import AutoUpdater, UpdateChecker

updater = AutoUpdater(current_version="2.1.1")
update_checker = UpdateChecker(updater)
```

#### Methods

##### check_for_updates() -> Optional[UpdateInfo]

Checks for available updates.

**Returns:**
- `Optional[UpdateInfo]`: Update information if available

##### download_and_install(update_info: UpdateInfo) -> bool

Downloads and installs an update.

**Parameters:**
- `update_info` (UpdateInfo): Update information

**Returns:**
- `bool`: True if successful

### FileWatcher

Monitors configuration files for changes.

```python
from clicker.utils.file_watcher import FileWatcher

watcher = FileWatcher()
```

#### Methods

##### watch_file(file_path: Path, callback: Callable) -> None

Watches a file for changes.

**Parameters:**
- `file_path` (Path): File to watch
- `callback` (Callable): Function to call when file changes

## Error Handling

### Exception Hierarchy

```python
from clicker.utils.exceptions import (
    ClickerError,
    ConfigurationError,
    AutomationError,
    UpdateError
)
```

#### ClickerError

Base exception for all Clicker-related errors.

#### ConfigurationError

Raised when configuration validation fails.

```python
try:
    settings = AppSettings(toggle_key="invalid")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

#### AutomationError

Raised when automation operations fail.

```python
try:
    engine.start(keystrokes, settings)
except AutomationError as e:
    print(f"Automation error: {e}")
```

#### UpdateError

Raised when update operations fail.

## Configuration Format

### Settings File (settings.json)

```json
{
    "toggle_key": "~",
    "start_time_stagger": 1.7,
    "order_obeyed": false,
    "global_cooldown": 1.5,
    "indicator_type": "gdi",
    "show_notifications": true,
    "minimize_to_tray": true,
    "keystroke_method": "windows_api",
    "high_performance_mode": false,
    "logging_enabled": true,
    "fail_safe_enabled": true,
    "max_execution_time": 3600.0,
    "emergency_stop_key": "ctrl+shift+esc",
    "check_updates_on_startup": true,
    "auto_install_updates": false,
    "update_channel": "stable",
    "thread_pool_size": 2,
    "memory_limit_mb": 100,
    "log_retention_days": 7,
    "config_backup_count": 5
}
```

### Keystrokes File (keystrokes.txt)

```text
# Clicker Keystrokes Configuration
# Format: KEY DELAY [DESCRIPTION]
# Modifiers: C- (Ctrl), S- (Shift), A- (Alt)

# Basic keys
a 1.5 Press 'a' key
b 2.0 Press 'b' key
space 1.0 Press spacebar

# Function keys
f1 2.5 Press F1
f12 3.0 Press F12

# Modified keys
C-a 1.0 Ctrl+A (Select All)
S-f1 1.5 Shift+F1
C-S-a 2.0 Ctrl+Shift+A

# Special keys
enter 1.0 Press Enter
tab 0.5 Press Tab
escape 2.0 Press Escape
```

### Profile File (.profile)

```json
{
    "name": "Gaming Profile",
    "description": "Optimized for gaming",
    "author": "User123",
    "version": "1.0",
    "created_at": "2024-01-01T12:00:00Z",
    "modified_at": "2024-01-01T12:00:00Z",
    "tags": ["gaming", "rpg"],
    "settings": {
        "toggle_key": "F2",
        "global_cooldown": 0.5,
        "high_performance_mode": true
    },
    "keystrokes": [
        "1 1.0 Heal",
        "2 1.5 Attack",
        "3 2.0 Special ability"
    ]
}
```

## Examples

### Basic Application Setup

```python
#!/usr/bin/env python3
"""
Basic Clicker application setup example.
"""

import sys
import logging
from pathlib import Path
from clicker import ClickerApp

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    
    # Create application with custom config directory
    config_dir = Path.home() / "my_clicker_config"
    app = ClickerApp(config_dir=config_dir)
    
    # Run application
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
```

### Configuration Management

```python
"""
Configuration management example.
"""

from clicker.config.manager import ConfigManager
from clicker.config.models import AppSettings, KeystrokeConfig

def setup_configuration():
    """Setup and customize configuration."""
    # Create config manager
    config_manager = ConfigManager()
    
    # Create custom settings
    settings = AppSettings(
        toggle_key='F3',
        global_cooldown=2.0,
        show_notifications=True,
        high_performance_mode=True
    )
    
    # Create keystrokes
    keystrokes = [
        KeystrokeConfig(key='1', delay=1.0, description='Heal'),
        KeystrokeConfig(key='2', delay=1.5, description='Attack'),
        KeystrokeConfig(key='C-q', delay=3.0, description='Quick save')
    ]
    
    # Save configuration
    if config_manager.save_settings(settings):
        print("Settings saved successfully")
    
    if config_manager.save_keystrokes(keystrokes):
        print("Keystrokes saved successfully")
    
    # Validate configuration
    issues = config_manager.validate_configuration()
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration is valid")

if __name__ == "__main__":
    setup_configuration()
```

### Custom Automation Engine

```python
"""
Custom automation engine usage example.
"""

from clicker.core.automation import AutomationEngine, AutomationState
from clicker.core.keystrokes import WindowsKeystrokeSender
from clicker.config.models import AppSettings, KeystrokeConfig
import time

def run_custom_automation():
    """Run automation with custom configuration."""
    # Create keystroke sender
    sender = WindowsKeystrokeSender()
    
    if not sender.is_available():
        print("Windows API not available")
        return
    
    # Create automation engine
    engine = AutomationEngine(sender)
    
    # Setup keystrokes
    keystrokes = [
        KeystrokeConfig(key='a', delay=2.0, description='Action A'),
        KeystrokeConfig(key='b', delay=3.0, description='Action B'),
        KeystrokeConfig(key='space', delay=1.0, description='Jump')
    ]
    
    # Setup settings
    settings = AppSettings(
        global_cooldown=1.0,
        max_execution_time=60.0,  # Run for 1 minute
        fail_safe_enabled=True
    )
    
    # Register state change callback
    def on_state_change(new_state: AutomationState):
        print(f"Automation state changed to: {new_state.name}")
    
    engine.register_state_callback(on_state_change)
    
    # Start automation
    if engine.start(keystrokes, settings):
        print("Automation started successfully")
        
        # Monitor for 10 seconds
        for i in range(10):
            time.sleep(1)
            stats = engine.get_stats()
            print(f"Executions: {stats.total_executions}, "
                  f"Success rate: {stats.success_rate:.2%}")
        
        # Stop automation
        if engine.stop():
            print("Automation stopped successfully")
    else:
        print("Failed to start automation")

if __name__ == "__main__":
    run_custom_automation()
```

### Profile Management

```python
"""
Profile management example.
"""

from clicker.config.models import ProfileConfig, AppSettings, KeystrokeConfig
from clicker.config.manager import ConfigManager
import json
from pathlib import Path

def create_gaming_profile():
    """Create a gaming profile."""
    # Create gaming-optimized settings
    gaming_settings = AppSettings(
        toggle_key='F1',
        global_cooldown=0.3,
        high_performance_mode=True,
        indicator_type='gdi',
        emergency_stop_key='ctrl+alt+q'
    )
    
    # Create gaming keystrokes
    gaming_keystrokes = [
        KeystrokeConfig(key='1', delay=1.0, description='Health potion', tags=['healing']),
        KeystrokeConfig(key='2', delay=1.5, description='Mana potion', tags=['mana']),
        KeystrokeConfig(key='q', delay=0.8, description='Quick attack', tags=['combat']),
        KeystrokeConfig(key='e', delay=2.0, description='Special ability', tags=['combat']),
        KeystrokeConfig(key='C-s', delay=5.0, description='Quick save', tags=['utility'])
    ]
    
    # Create profile
    profile = ProfileConfig(
        name="Gaming Profile",
        description="Optimized for RPG gaming with quick actions and fail-safes",
        author="GamerUser",
        version="1.0",
        settings=gaming_settings,
        keystrokes=gaming_keystrokes,
        tags=['gaming', 'rpg', 'action']
    )
    
    return profile

def save_and_load_profile():
    """Demonstrate saving and loading profiles."""
    # Create profile
    profile = create_gaming_profile()
    
    # Save to file
    profile_path = Path("gaming_profile.json")
    with open(profile_path, 'w') as f:
        json.dump(profile.to_dict(), f, indent=2)
    
    print(f"Profile saved to {profile_path}")
    
    # Load from file
    with open(profile_path, 'r') as f:
        profile_data = json.load(f)
    
    loaded_profile = ProfileConfig.from_dict(profile_data)
    print(f"Loaded profile: {loaded_profile.name}")
    print(f"Keystrokes: {len(loaded_profile.keystrokes)}")
    print(f"Tags: {', '.join(loaded_profile.tags)}")

if __name__ == "__main__":
    save_and_load_profile()
```

## Best Practices

### Error Handling

Always wrap configuration operations in try-catch blocks:

```python
try:
    settings = AppSettings.from_dict(user_data)
    config_manager.save_settings(settings)
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Handle configuration error
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle unexpected error
```

### Resource Management

Use context managers for proper resource cleanup:

```python
# Automation engine automatically handles cleanup
engine = AutomationEngine(sender)
try:
    engine.start(keystrokes, settings)
    # Do work
finally:
    engine.stop()  # Ensures clean shutdown
```

### Validation

Always validate user input before creating configuration objects:

```python
def safe_create_keystroke(key: str, delay: float, description: str = ""):
    """Safely create a keystroke with validation."""
    try:
        return KeystrokeConfig(
            key=key.strip(),
            delay=max(0.1, min(3600.0, delay)),  # Clamp delay
            description=description[:500]  # Limit description length
        )
    except ValueError as e:
        print(f"Invalid keystroke configuration: {e}")
        return None
```

### Performance

For high-performance scenarios:

```python
# Enable high performance mode
settings = AppSettings(
    high_performance_mode=True,
    thread_pool_size=4,
    global_cooldown=0.1
)

# Use optimized keystroke method
settings.keystroke_method = KeystrokeMethod.WINDOWS_API
```

## Version History

- **v2.1.1**: Bugfix release with autoupdate improvements
- **v2.1.0**: Post-2.0 reorganization and bugfix release
- **v2.0.0**: Complete architecture refactor with clean API
- **v1.x**: Legacy monolithic implementation

For more information, see the project repository and documentation. 