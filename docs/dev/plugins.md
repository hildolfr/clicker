# Plugin Development Guide

Guide for developing plugins for the Clicker automation system.

## 🔌 Plugin System Overview

Clicker's plugin system allows you to extend functionality without modifying the core application. The plugin architecture is designed for extensibility and safety.

### Plugin Architecture

```
clicker/
├── plugins/              # Built-in plugins
│   ├── __init__.py
│   └── base.py          # Base plugin class
├── custom_plugins/      # User plugins (auto-detected)
└── config/
    └── plugins.json     # Plugin configuration
```

## 🚀 Getting Started

### Basic Plugin Structure

All plugins must inherit from the base `Plugin` class:

```python
# my_plugin.py
from clicker.plugins.base import Plugin
from clicker.core.events import EventSystem, EventType

class MyPlugin(Plugin):
    """Example plugin that demonstrates basic functionality."""
    
    def __init__(self, event_system: EventSystem):
        super().__init__("MyPlugin", "1.0.0", event_system)
        self.description = "Example plugin for demonstration"
        
    def initialize(self) -> bool:
        """Initialize the plugin."""
        self.logger.info(f"Initializing {self.name}")
        
        # Subscribe to events
        self.event_system.subscribe(EventType.AUTOMATION_STARTED, self.on_automation_started)
        self.event_system.subscribe(EventType.KEYSTROKE_SENT, self.on_keystroke_sent)
        
        return True
    
    def cleanup(self) -> None:
        """Cleanup when plugin is unloaded."""
        self.logger.info(f"Cleaning up {self.name}")
        # Unsubscribe from events
        self.event_system.unsubscribe_all(self)
    
    def on_automation_started(self, event):
        """Handle automation start events."""
        self.logger.info("Automation started - plugin notified")
    
    def on_keystroke_sent(self, event):
        """Handle keystroke events."""
        key = event.data.get('key', 'unknown')
        self.logger.debug(f"Keystroke sent: {key}")

# Required: Plugin factory function
def create_plugin(event_system: EventSystem) -> Plugin:
    """Factory function to create plugin instance."""
    return MyPlugin(event_system)
```

### Plugin Metadata

Each plugin should define metadata:

```python
class MyPlugin(Plugin):
    def __init__(self, event_system: EventSystem):
        super().__init__(
            name="MyPlugin",
            version="1.0.0", 
            event_system=event_system
        )
        self.description = "Plugin description"
        self.author = "Your Name"
        self.requires = ["clicker>=2.1.0"]  # Version requirements
        self.category = "utility"  # Plugin category
```

## 📋 Plugin Base Class

### Required Methods

```python
class Plugin:
    def __init__(self, name: str, version: str, event_system: EventSystem):
        """Initialize plugin with name, version, and event system."""
        pass
    
    def initialize(self) -> bool:
        """Initialize plugin. Return True if successful."""
        raise NotImplementedError
    
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        raise NotImplementedError
```

### Optional Methods

```python
class Plugin:
    def configure(self, config: dict) -> bool:
        """Configure plugin with settings."""
        return True
    
    def get_status(self) -> dict:
        """Get plugin status information."""
        return {"active": True, "status": "running"}
    
    def get_settings_schema(self) -> dict:
        """Get JSON schema for plugin settings."""
        return {}
```

## 🎯 Event System Integration

### Available Events

Plugins can subscribe to these events:

```python
from clicker.core.events import EventType

# Automation events
EventType.AUTOMATION_STARTED
EventType.AUTOMATION_STOPPED
EventType.AUTOMATION_PAUSED
EventType.AUTOMATION_RESUMED
EventType.AUTOMATION_ERROR

# Keystroke events
EventType.KEYSTROKE_SENT
EventType.KEYSTROKE_FAILED
EventType.KEYSTROKE_QUEUED

# Configuration events
EventType.CONFIG_LOADED
EventType.CONFIG_CHANGED
EventType.CONFIG_SAVED

# System events
EventType.HOTKEY_PRESSED
EventType.SHUTDOWN_REQUESTED
```

### Event Handling

```python
def initialize(self) -> bool:
    # Subscribe to events
    self.event_system.subscribe(EventType.KEYSTROKE_SENT, self.handle_keystroke)
    return True

def handle_keystroke(self, event):
    """Handle keystroke events."""
    key = event.data.get('key')
    timestamp = event.timestamp
    source = event.source
    
    # Process the event
    self.logger.info(f"Keystroke {key} from {source} at {timestamp}")
```

### Emitting Events

```python
def some_method(self):
    # Emit custom events
    self.event_system.emit_simple(
        EventType.CONFIG_CHANGED,
        self.name,
        {"setting": "value"}
    )
```

## 🔧 Plugin Configuration

### Configuration Schema

Define configuration schema for your plugin:

```python
def get_settings_schema(self) -> dict:
    return {
        "type": "object",
        "properties": {
            "enabled": {"type": "boolean", "default": True},
            "interval": {"type": "number", "minimum": 0.1, "default": 1.0},
            "message": {"type": "string", "default": "Hello World"}
        },
        "required": ["enabled"]
    }
```

### Loading Configuration

```python
def configure(self, config: dict) -> bool:
    """Configure plugin with user settings."""
    self.enabled = config.get('enabled', True)
    self.interval = config.get('interval', 1.0)
    self.message = config.get('message', 'Hello World')
    
    # Validate configuration
    if self.interval < 0.1:
        self.logger.error("Interval must be at least 0.1 seconds")
        return False
    
    return True
```

## 📝 Example Plugins

### Statistics Plugin

```python
class StatisticsPlugin(Plugin):
    """Plugin that tracks automation statistics."""
    
    def __init__(self, event_system: EventSystem):
        super().__init__("StatisticsPlugin", "1.0.0", event_system)
        self.keystroke_count = 0
        self.start_time = None
        
    def initialize(self) -> bool:
        self.event_system.subscribe(EventType.AUTOMATION_STARTED, self.on_start)
        self.event_system.subscribe(EventType.KEYSTROKE_SENT, self.on_keystroke)
        return True
    
    def on_start(self, event):
        """Reset statistics when automation starts."""
        self.keystroke_count = 0
        self.start_time = time.time()
        
    def on_keystroke(self, event):
        """Count keystrokes."""
        self.keystroke_count += 1
        
    def get_status(self) -> dict:
        """Return current statistics."""
        runtime = time.time() - self.start_time if self.start_time else 0
        return {
            "keystrokes": self.keystroke_count,
            "runtime": runtime,
            "rate": self.keystroke_count / runtime if runtime > 0 else 0
        }
```

### Notification Plugin

```python
class NotificationPlugin(Plugin):
    """Plugin that shows notifications for automation events."""
    
    def initialize(self) -> bool:
        self.event_system.subscribe(EventType.AUTOMATION_STARTED, self.on_start)
        self.event_system.subscribe(EventType.AUTOMATION_STOPPED, self.on_stop)
        return True
    
    def on_start(self, event):
        """Show notification when automation starts."""
        self.show_notification("Automation Started", "Clicker automation is now active")
    
    def on_stop(self, event):
        """Show notification when automation stops."""
        self.show_notification("Automation Stopped", "Clicker automation has stopped")
    
    def show_notification(self, title: str, message: str):
        """Show system notification."""
        try:
            import plyer
            plyer.notification.notify(
                title=title,
                message=message,
                app_name="Clicker",
                timeout=3
            )
        except ImportError:
            self.logger.warning("plyer not available for notifications")
```

## 📦 Plugin Installation

### Directory Structure

Place plugins in the `custom_plugins/` directory:

```
custom_plugins/
├── my_plugin.py
├── advanced_plugin/
│   ├── __init__.py
│   ├── plugin.py
│   └── helpers.py
└── requirements.txt  # Plugin dependencies
```

### Plugin Discovery

Clicker automatically discovers plugins in:
1. `clicker/plugins/` (built-in plugins)
2. `custom_plugins/` (user plugins)
3. Paths specified in `plugins.json`

### Configuration File

Configure plugins in `config/plugins.json`:

```json
{
  "enabled": true,
  "auto_load": true,
  "plugin_paths": [
    "custom_plugins/",
    "C:/path/to/other/plugins/"
  ],
  "active_plugins": [
    "StatisticsPlugin",
    "NotificationPlugin"
  ],
  "plugin_settings": {
    "StatisticsPlugin": {
      "save_to_file": true,
      "file_path": "stats.json"
    },
    "NotificationPlugin": {
      "show_start": true,
      "show_stop": true,
      "timeout": 5
    }
  }
}
```

## 🛡️ Plugin Security

### Safe Practices

1. **Validate all inputs**
2. **Handle exceptions gracefully**
3. **Don't modify core application state**
4. **Use the event system for communication**
5. **Clean up resources properly**

### Security Restrictions

Plugins should not:
- Modify global configuration directly
- Access private application data
- Block the main application thread
- Execute arbitrary system commands without user consent

### Error Handling

```python
def initialize(self) -> bool:
    try:
        # Plugin initialization code
        self.setup_components()
        return True
    except Exception as e:
        self.logger.error(f"Failed to initialize plugin: {e}")
        return False

def handle_event(self, event):
    try:
        # Event handling code
        self.process_event(event)
    except Exception as e:
        self.logger.error(f"Error handling event: {e}")
        # Don't re-raise - let other plugins continue
```

## 🔍 Testing Plugins

### Unit Testing

```python
import unittest
from unittest.mock import Mock
from clicker.core.events import EventSystem
from my_plugin import MyPlugin

class TestMyPlugin(unittest.TestCase):
    def setUp(self):
        self.event_system = Mock(spec=EventSystem)
        self.plugin = MyPlugin(self.event_system)
    
    def test_initialization(self):
        result = self.plugin.initialize()
        self.assertTrue(result)
        self.event_system.subscribe.assert_called()
    
    def test_event_handling(self):
        event = Mock()
        event.data = {'key': 'a'}
        
        self.plugin.on_keystroke_sent(event)
        # Assert expected behavior
```

### Integration Testing

```python
def test_plugin_with_real_events():
    from clicker.core.events import EventSystem, EventType
    
    event_system = EventSystem()
    plugin = MyPlugin(event_system)
    
    # Initialize plugin
    assert plugin.initialize()
    
    # Emit test event
    event_system.emit_simple(EventType.KEYSTROKE_SENT, "test", {"key": "a"})
    
    # Verify plugin handled event
    # Add assertions based on plugin behavior
```

## 📚 Advanced Topics

### Plugin Dependencies

```python
class AdvancedPlugin(Plugin):
    def __init__(self, event_system: EventSystem):
        super().__init__("AdvancedPlugin", "1.0.0", event_system)
        self.requires = ["requests>=2.25.0", "numpy>=1.20.0"]
    
    def initialize(self) -> bool:
        try:
            import requests
            import numpy
            return True
        except ImportError as e:
            self.logger.error(f"Missing dependency: {e}")
            return False
```

### Plugin Communication

```python
class PluginA(Plugin):
    def initialize(self) -> bool:
        # Register plugin service
        self.event_system.register_service("PluginA", self)
        return True
    
    def get_data(self):
        return {"value": 42}

class PluginB(Plugin):
    def initialize(self) -> bool:
        # Use service from PluginA
        plugin_a = self.event_system.get_service("PluginA")
        if plugin_a:
            data = plugin_a.get_data()
        return True
```

## 📖 Documentation

Document your plugins with:

1. **Clear docstrings**
2. **Configuration examples**
3. **Event descriptions**
4. **Usage instructions**
5. **Requirements list**

For more information, see the [API Documentation](../API.md) and [Configuration Guide](../configuration.md). 