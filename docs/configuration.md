# Configuration Guide

This guide covers all configuration options available in Clicker, from basic settings to advanced automation configurations.

## 📁 Configuration Files

Clicker uses JSON-based configuration files for maximum flexibility and readability:

```
clicker/
├── config/
│   ├── default.json      # Default configuration
│   ├── profiles/         # User profiles
│   │   ├── gaming.json
│   │   ├── work.json
│   │   └── testing.json
│   └── hotkeys.json     # Global hotkey settings
```

## ⚙️ Basic Configuration

### Main Settings

```json
{
  "automation": {
    "click_type": "left",           // left, right, middle, double
    "interval": 1.0,                // seconds between clicks
    "position": [100, 200],         // x, y coordinates
    "click_count": 10,              // number of clicks (0 = infinite)
    "randomize_interval": false,    // add random variation
    "interval_variance": 0.1        // variance in seconds
  },
  "safety": {
    "emergency_stop_corners": true, // stop when mouse hits corners
    "max_clicks_per_minute": 1000, // rate limiting
    "safe_mode": true,              // enable safety checks
    "position_validation": true     // verify click positions
  }
}
```

### GUI Settings

```json
{
  "interface": {
    "theme": "dark",                // dark, light, auto
    "always_on_top": false,         // keep window on top
    "start_minimized": false,       // start in system tray
    "show_notifications": true,     // system notifications
    "transparency": 1.0,            // window transparency (0.1-1.0)
    "compact_mode": false           // smaller interface
  }
}
```

## 🎮 Advanced Automation

### Pattern-Based Clicking

Define complex clicking patterns:

```json
{
  "patterns": {
    "spiral": {
      "type": "geometric",
      "shape": "spiral",
      "center": [400, 300],
      "radius": 50,
      "points": 8,
      "interval": 0.5
    },
    "grid": {
      "type": "grid",
      "start": [100, 100],
      "rows": 3,
      "columns": 3,
      "spacing": [50, 50],
      "interval": 0.2
    },
    "sequence": {
      "type": "sequence",
      "positions": [
        [100, 100],
        [200, 150],
        [300, 100],
        [400, 200]
      ],
      "intervals": [0.5, 1.0, 0.3, 0.8]
    }
  }
}
```

### Conditional Automation

Set up condition-based automation:

```json
{
  "conditions": {
    "color_detection": {
      "enabled": true,
      "target_color": "#FF0000",
      "tolerance": 10,
      "area": [100, 100, 200, 200]
    },
    "window_detection": {
      "enabled": true,
      "window_title": "Game Window",
      "process_name": "game.exe"
    },
    "time_based": {
      "enabled": false,
      "start_time": "09:00",
      "end_time": "17:00",
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
    }
  }
}
```

## ⌨️ Hotkey Configuration

### Global Hotkeys

```json
{
  "hotkeys": {
    "start_automation": {
      "key": "F6",
      "modifiers": [],
      "global": true
    },
    "stop_automation": {
      "key": "F7", 
      "modifiers": [],
      "global": true
    },
    "emergency_stop": {
      "key": "Escape",
      "modifiers": ["ctrl", "shift"],
      "global": true
    },
    "capture_position": {
      "key": "C",
      "modifiers": ["ctrl", "shift"],
      "global": true
    },
    "toggle_window": {
      "key": "F8",
      "modifiers": [],
      "global": true
    }
  }
}
```

### Modifier Keys
- `ctrl` - Control key
- `shift` - Shift key  
- `alt` - Alt key
- `win` - Windows key

## 🔌 Plugin Configuration

### Loading Plugins

```json
{
  "plugins": {
    "enabled": true,
    "auto_load": true,
    "plugin_paths": [
      "plugins/",
      "custom_plugins/"
    ],
    "active_plugins": [
      "image_recognition",
      "macro_recorder", 
      "statistics_tracker"
    ]
  }
}
```

### Plugin-Specific Settings

```json
{
  "plugin_settings": {
    "image_recognition": {
      "confidence_threshold": 0.8,
      "search_area": "full_screen",
      "template_path": "templates/"
    },
    "macro_recorder": {
      "record_mouse": true,
      "record_keyboard": false,
      "max_sequence_length": 1000
    },
    "statistics_tracker": {
      "track_performance": true,
      "save_logs": true,
      "log_file": "stats/automation_stats.json"
    }
  }
}
```

## 📊 Logging Configuration

### Log Settings

```json
{
  "logging": {
    "level": "INFO",                // DEBUG, INFO, WARNING, ERROR
    "console_output": true,         // show logs in console
    "file_output": true,            // save logs to file
    "log_file": "logs/clicker.log", // log file path
    "max_file_size": "10MB",        // rotate when file reaches size
    "backup_count": 5,              // number of backup files
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

### Log Categories

```json
{
  "log_categories": {
    "automation": "INFO",
    "gui": "WARNING", 
    "hotkeys": "INFO",
    "plugins": "DEBUG",
    "safety": "INFO",
    "performance": "WARNING"
  }
}
```

## 🎯 Performance Tuning

### Optimization Settings

```json
{
  "performance": {
    "click_precision": "high",      // low, medium, high, ultra
    "cpu_priority": "normal",       // low, normal, high
    "memory_limit": "100MB",        // maximum memory usage
    "threading": {
      "enabled": true,
      "worker_threads": 2,
      "background_processing": true
    },
    "optimization": {
      "reduce_cpu_usage": true,
      "efficient_sleep": true,
      "batch_operations": false
    }
  }
}
```

## 🛡️ Security Settings

### Access Control

```json
{
  "security": {
    "require_admin": false,         // require administrator rights
    "allow_system_control": true,   // allow system-level automation
    "restricted_areas": [           // forbidden click areas
      [0, 0, 100, 50],             // taskbar area
      [1820, 0, 1920, 100]         // notification area
    ],
    "process_whitelist": [          // allowed target processes
      "notepad.exe",
      "chrome.exe",
      "game.exe"
    ]
  }
}
```

## 📱 Profile Management

### Creating Custom Profiles

1. **Basic Profile Setup**:
   ```json
   {
     "profile_name": "Gaming Setup",
     "description": "Optimized for gaming automation",
     "version": "1.0",
     "created": "2024-01-01T00:00:00Z"
   }
   ```

2. **Profile Inheritance**:
   ```json
   {
     "inherits_from": "default",
     "overrides": {
       "automation": {
         "click_type": "left",
         "interval": 0.1
       }
     }
   }
   ```

### Profile Switching

- **GUI**: Use the profile dropdown in the main interface
- **Hotkey**: Set up profile switching hotkeys
- **CLI**: `python main.py --profile gaming`
- **API**: `clicker.load_profile("gaming")`

## 🔧 Troubleshooting Configuration

### Validation

Clicker automatically validates configuration files:

```bash
# Validate configuration
python main.py --validate-config

# Check specific profile
python main.py --validate-profile gaming

# Show configuration errors
python main.py --config-debug
```

### Common Issues

**Invalid JSON Format**
- Use a JSON validator to check syntax
- Ensure proper escaping of special characters
- Check for trailing commas

**Permission Errors**
- Run as administrator for global hotkeys
- Check file permissions on config directory
- Verify write access to log files

**Performance Issues**
- Reduce click precision for better performance
- Disable unnecessary plugins
- Increase intervals for CPU-intensive tasks

## 📚 Configuration Examples

### Gaming Profile
```json
{
  "profile_name": "Gaming",
  "automation": {
    "click_type": "left",
    "interval": 0.1,
    "randomize_interval": true,
    "interval_variance": 0.05
  },
  "safety": {
    "max_clicks_per_minute": 600,
    "safe_mode": false
  },
  "performance": {
    "click_precision": "high",
    "cpu_priority": "high"
  }
}
```

### Work Profile
```json
{
  "profile_name": "Productivity",
  "automation": {
    "click_type": "left",
    "interval": 2.0,
    "randomize_interval": false
  },
  "safety": {
    "max_clicks_per_minute": 30,
    "safe_mode": true,
    "position_validation": true
  },
  "interface": {
    "theme": "light",
    "show_notifications": false
  }
}
```

### Testing Profile
```json
{
  "profile_name": "UI Testing",
  "automation": {
    "click_type": "left",
    "interval": 0.5
  },
  "logging": {
    "level": "DEBUG",
    "console_output": true
  },
  "plugins": {
    "active_plugins": ["statistics_tracker", "image_recognition"]
  }
}
```

## 🔄 Configuration Updates

### Auto-Update Settings
```json
{
  "updates": {
    "check_for_updates": true,
    "auto_backup_config": true,
    "migration_enabled": true,
    "backup_directory": "config/backups/"
  }
}
```

Clicker automatically backs up your configuration before updates and provides migration tools for configuration format changes.

For more advanced configuration options, see the [Configuration Schema](config-schema.md) reference. 