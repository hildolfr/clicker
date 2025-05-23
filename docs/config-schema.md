# Configuration Schema Reference

Complete reference for all configuration options in Clicker.

## 📋 Configuration Files

Clicker uses two main configuration files:

- **`settings.json`** - Application settings
- **`keystrokes.txt`** - Keystroke automation definitions

## ⚙️ Settings Schema (settings.json)

### Core Settings

```json
{
  "toggle_key": "~",
  "start_time_stagger": 1.7,
  "order_obeyed": false,
  "global_cooldown": 1.5
}
```

| Field | Type | Default | Range | Description |
|-------|------|---------|--------|-------------|
| `toggle_key` | string | `"~"` | Valid key name | Global hotkey to toggle automation |
| `start_time_stagger` | number | `1.7` | 0.0 - 60.0 | Delay before starting automation (seconds) |
| `order_obeyed` | boolean | `false` | true/false | Execute keystrokes in file order vs. sorted by delay |
| `global_cooldown` | number | `1.5` | 0.1 - 300.0 | Minimum time between any keystroke executions |

### UI Settings

```json
{
  "indicator_type": "gdi",
  "show_notifications": true,
  "minimize_to_tray": true
}
```

| Field | Type | Default | Options | Description |
|-------|------|---------|---------|-------------|
| `indicator_type` | string | `"gdi"` | "gdi", "pygame" | Visual indicator type |
| `show_notifications` | boolean | `true` | true/false | Show system notifications |
| `minimize_to_tray` | boolean | `true` | true/false | Minimize to system tray |

### Performance Settings

```json
{
  "keystroke_method": "windows_api",
  "high_performance_mode": false,
  "logging_enabled": true,
  "thread_pool_size": 2,
  "memory_limit_mb": 100
}
```

| Field | Type | Default | Range | Description |
|-------|------|---------|--------|-------------|
| `keystroke_method` | string | `"windows_api"` | "windows_api" | Method for sending keystrokes |
| `high_performance_mode` | boolean | `false` | true/false | Enable performance optimizations |
| `logging_enabled` | boolean | `true` | true/false | Enable detailed logging |
| `thread_pool_size` | integer | `2` | 1 - 10 | Number of worker threads |
| `memory_limit_mb` | integer | `100` | 10 - 1000 | Memory usage limit in MB |

### Safety Settings

```json
{
  "fail_safe_enabled": true,
  "max_execution_time": 3600.0,
  "emergency_stop_key": "ctrl+shift+esc"
}
```

| Field | Type | Default | Range | Description |
|-------|------|---------|--------|-------------|
| `fail_safe_enabled` | boolean | `true` | true/false | Enable fail-safe mechanisms |
| `max_execution_time` | number | `3600.0` | 1.0 - 86400.0 | Maximum automation runtime (seconds) |
| `emergency_stop_key` | string | `"ctrl+shift+esc"` | Valid key combo | Emergency stop key (must include modifiers) |

### Update Settings

```json
{
  "check_updates_on_startup": true,
  "auto_install_updates": false,
  "update_channel": "stable"
}
```

| Field | Type | Default | Options | Description |
|-------|------|---------|---------|-------------|
| `check_updates_on_startup` | boolean | `true` | true/false | Check for updates on startup |
| `auto_install_updates` | boolean | `false` | true/false | Automatically install updates |
| `update_channel` | string | `"stable"` | "stable", "beta", "dev" | Update channel |

### Maintenance Settings

```json
{
  "log_retention_days": 7,
  "config_backup_count": 5
}
```

| Field | Type | Default | Range | Description |
|-------|------|---------|--------|-------------|
| `log_retention_days` | integer | `7` | 1 - 365 | Days to retain log files |
| `config_backup_count` | integer | `5` | 1 - 20 | Number of configuration backups to keep |

## ⌨️ Keystrokes Schema (keystrokes.txt)

### File Format

```
# Comment lines start with #
KEY DELAY [DESCRIPTION]
```

### Keystroke Definition

Each line defines a keystroke with:

| Component | Required | Format | Description |
|-----------|----------|--------|-------------|
| Key | Yes | See key formats below | Key to press |
| Delay | Yes | Positive number | Seconds between repetitions |
| Description | No | Any text | Human-readable description |

### Key Formats

#### Basic Keys

```
a 1.5           # Letter 'a'
1 2.0           # Number '1'
space 1.0       # Spacebar
enter 2.0       # Enter key
f1 1.5          # Function key F1
```

#### Modified Keys

```
C-a 1.0         # Ctrl+A
S-f1 2.0        # Shift+F1
A-tab 1.5       # Alt+Tab
C-S-z 2.0       # Ctrl+Shift+Z
```

**Modifier Prefixes:**
- `C-` - Control key
- `S-` - Shift key
- `A-` - Alt key

#### Special Keys

| Key Name | Description |
|----------|-------------|
| `space` | Spacebar |
| `enter` | Enter key |
| `tab` | Tab key |
| `escape` | Escape key |
| `backspace` | Backspace key |
| `delete` | Delete key |
| `insert` | Insert key |
| `home` | Home key |
| `end` | End key |
| `pageup` | Page Up key |
| `pagedown` | Page Down key |
| `up`, `down`, `left`, `right` | Arrow keys |

#### Function Keys

```
f1, f2, f3, ..., f12    # Function keys F1-F12
```

### Validation Rules

#### Key Validation

- Keys must be alphanumeric or from the special keys list
- Modifier order must be: `C-S-A-` (Control, Shift, Alt)
- No duplicate modifiers allowed
- Maximum key length: 50 characters

#### Delay Validation

- Must be a positive number
- Minimum: 0.1 seconds
- Maximum: 3600.0 seconds (1 hour)

#### Line Format

- Lines starting with `#` are comments
- Empty lines are ignored
- Invalid lines are skipped with warnings

### Example Configuration

```
# Gaming automation
1 1.0 Health potion
2 1.5 Mana potion
q 0.8 Quick attack
e 2.0 Special ability

# Productivity
C-s 5.0 Save document
C-c 2.0 Copy
C-v 2.0 Paste

# System navigation
A-tab 3.0 Switch windows
C-A-del 10.0 Task manager (careful!)
```

## 🔧 JSON Schema

### Complete settings.json Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Clicker Settings",
  "type": "object",
  "properties": {
    "toggle_key": {
      "type": "string",
      "minLength": 1,
      "maxLength": 20,
      "description": "Global hotkey to toggle automation"
    },
    "start_time_stagger": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 60.0,
      "description": "Delay before starting automation"
    },
    "order_obeyed": {
      "type": "boolean",
      "description": "Execute keystrokes in file order"
    },
    "global_cooldown": {
      "type": "number",
      "minimum": 0.1,
      "maximum": 300.0,
      "description": "Minimum time between keystrokes"
    },
    "indicator_type": {
      "type": "string",
      "enum": ["gdi", "pygame"],
      "description": "Visual indicator type"
    },
    "show_notifications": {
      "type": "boolean",
      "description": "Show system notifications"
    },
    "minimize_to_tray": {
      "type": "boolean",
      "description": "Minimize to system tray"
    },
    "keystroke_method": {
      "type": "string",
      "enum": ["windows_api"],
      "description": "Keystroke sending method"
    },
    "high_performance_mode": {
      "type": "boolean",
      "description": "Enable performance optimizations"
    },
    "logging_enabled": {
      "type": "boolean",
      "description": "Enable detailed logging"
    },
    "fail_safe_enabled": {
      "type": "boolean",
      "description": "Enable fail-safe mechanisms"
    },
    "max_execution_time": {
      "type": "number",
      "minimum": 1.0,
      "maximum": 86400.0,
      "description": "Maximum automation runtime"
    },
    "emergency_stop_key": {
      "type": "string",
      "pattern": ".*\\+.*",
      "description": "Emergency stop key (must include modifiers)"
    },
    "check_updates_on_startup": {
      "type": "boolean",
      "description": "Check for updates on startup"
    },
    "auto_install_updates": {
      "type": "boolean",
      "description": "Automatically install updates"
    },
    "update_channel": {
      "type": "string",
      "enum": ["stable", "beta", "dev"],
      "description": "Update channel"
    },
    "thread_pool_size": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10,
      "description": "Number of worker threads"
    },
    "memory_limit_mb": {
      "type": "integer",
      "minimum": 10,
      "maximum": 1000,
      "description": "Memory usage limit"
    },
    "log_retention_days": {
      "type": "integer",
      "minimum": 1,
      "maximum": 365,
      "description": "Log retention period"
    },
    "config_backup_count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20,
      "description": "Configuration backup count"
    }
  },
  "additionalProperties": false
}
```

## ✅ Validation

### Configuration Validation

Clicker automatically validates all configuration:

```bash
# Validate current configuration
python main.py --validate-config

# Check specific settings
python main.py --validate-settings

# Check keystrokes file
python main.py --validate-keystrokes
```

### Common Validation Errors

**Invalid Toggle Key:**
```
ValueError: toggle_key conflicts with system shortcuts
```

**Invalid Delay:**
```
ValueError: delay must be between 0.1 and 3600.0 seconds
```

**Invalid Key Format:**
```
ValueError: Invalid key format: 'invalid-key'
```

**Missing Required Settings:**
```
ValueError: emergency_stop_key cannot be empty
```

## 🔄 Migration

### Automatic Migration

Clicker automatically migrates old configuration formats:

- Legacy setting names are converted
- Invalid values are reset to defaults
- Backup copies are created before migration

### Manual Migration

If automatic migration fails:

1. **Backup current configuration**
2. **Delete settings.json**
3. **Restart Clicker** (creates default configuration)
4. **Manually apply your settings**

For more information, see the [Configuration Guide](configuration.md). 