# Command Line Reference

Complete reference for Clicker's command-line interface.

## 🚀 Basic Usage

### Starting Clicker

```bash
# Start with default configuration
python main.py

# Start with specific configuration directory
python main.py --config-dir /path/to/config

# Start with specific profile
python main.py --profile gaming
```

## 📋 Command Line Options

### General Options

| Option | Description | Example |
|--------|-------------|---------|
| `--help`, `-h` | Show help message | `python main.py --help` |
| `--version` | Show version information | `python main.py --version` |
| `--config-dir DIR` | Use custom configuration directory | `python main.py --config-dir ./config` |
| `--profile NAME` | Load specific profile | `python main.py --profile work` |

### Validation Options

| Option | Description | Example |
|--------|-------------|---------|
| `--validate-config` | Validate all configuration files | `python main.py --validate-config` |
| `--validate-settings` | Validate settings.json only | `python main.py --validate-settings` |
| `--validate-keystrokes` | Validate keystrokes.txt only | `python main.py --validate-keystrokes` |
| `--test-hotkeys` | Test hotkey registration | `python main.py --test-hotkeys` |

### Debug Options

| Option | Description | Example |
|--------|-------------|---------|
| `--debug` | Enable debug logging | `python main.py --debug` |
| `--no-gui` | Run without GUI (console only) | `python main.py --no-gui` |
| `--stats` | Show performance statistics | `python main.py --stats` |
| `--check-permissions` | Check system permissions | `python main.py --check-permissions` |

## 🔧 Profile Management

### Profile Commands

The profile manager provides commands for managing automation profiles:

```bash
# List available profiles
python -m clicker.cli.profile_manager list

# Create new profile
python -m clicker.cli.profile_manager create --name "gaming" --description "Gaming automation"

# Load profile
python -m clicker.cli.profile_manager load --name "gaming"

# Delete profile
python -m clicker.cli.profile_manager delete --name "old_profile"

# Export profile
python -m clicker.cli.profile_manager export --name "gaming" --output "./gaming.profile"

# Import profile
python -m clicker.cli.profile_manager import --file "./gaming.profile"
```

### Profile Options

| Option | Description | Required |
|--------|-------------|----------|
| `--name NAME` | Profile name | Yes (for most commands) |
| `--description DESC` | Profile description | No |
| `--output FILE` | Output file for export | Yes (for export) |
| `--file FILE` | Profile file to import | Yes (for import) |
| `--force` | Overwrite existing profile | No |

## ⚙️ Configuration Commands

### Settings Validation

```bash
# Validate all configuration
python main.py --validate-config
# Output: Configuration validation passed

# Validate with detailed output
python main.py --validate-config --verbose
# Output: Detailed validation results for each setting

# Validate specific configuration file
python main.py --validate-settings
python main.py --validate-keystrokes
```

### Configuration Testing

```bash
# Test hotkey registration
python main.py --test-hotkeys
# Output: Testing hotkey registration...
#         Toggle key '~': OK
#         Emergency stop 'ctrl+shift+esc': OK

# Check system permissions
python main.py --check-permissions
# Output: Administrator privileges: Not available
#         Keyboard access: OK
#         File system access: OK
```

## 🔍 Debugging Commands

### Debug Mode

```bash
# Start with debug logging
python main.py --debug

# Run without GUI for debugging
python main.py --no-gui --debug

# Show performance statistics
python main.py --stats
# Output: Performance Statistics:
#         Memory usage: 45.2 MB
#         CPU usage: 2.1%
#         Keystrokes sent: 1,234
#         Uptime: 00:15:32
```

### Verbose Output

```bash
# Verbose configuration validation
python main.py --validate-config --verbose
# Output: Validating settings.json...
#         - toggle_key: '~' (OK)
#         - global_cooldown: 1.5 (OK)
#         - emergency_stop_key: 'ctrl+shift+esc' (OK)
#         Validating keystrokes.txt...
#         - Line 1: 'a 1.5' (OK)
#         - Line 2: 'b 2.0' (OK)
#         Configuration validation completed successfully.
```

## 📊 Output Formats

### Standard Output

```bash
# Default output format
python main.py --validate-config
Configuration validation passed.

# JSON output format
python main.py --validate-config --format json
{
  "status": "success",
  "message": "Configuration validation passed",
  "errors": [],
  "warnings": []
}
```

### Error Handling

```bash
# Configuration errors
python main.py --validate-config
Error: Invalid toggle_key 'ctrl+alt+del' conflicts with system shortcuts

# Exit codes
echo $?  # 0 = success, 1 = error, 2 = warning
```

## 🔧 Advanced Usage

### Automation Control

```bash
# Start automation immediately
python main.py --start

# Run automation for specific duration
python main.py --start --duration 300  # 5 minutes

# Run with specific keystroke file
python main.py --keystrokes custom_keys.txt
```

### Configuration Override

```bash
# Override specific settings
python main.py --set toggle_key=f1
python main.py --set global_cooldown=2.0

# Multiple overrides
python main.py --set toggle_key=f1 --set logging_enabled=false
```

### Batch Operations

```bash
# Process multiple profiles
for profile in gaming work testing; do
    python main.py --profile $profile --validate-config
done

# Batch validation of custom configurations
python main.py --validate-config --config-dir ./configs/gaming
python main.py --validate-config --config-dir ./configs/work
```

## 🔄 Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Operation completed successfully |
| 1 | Error | Configuration error or runtime failure |
| 2 | Warning | Operation completed with warnings |
| 3 | Permission | Insufficient permissions |
| 4 | Not Found | Configuration or profile not found |

## 📝 Environment Variables

### Configuration Override

```bash
# Override configuration directory
export CLICKER_CONFIG_DIR="/path/to/config"
python main.py

# Override default profile
export CLICKER_DEFAULT_PROFILE="gaming"
python main.py

# Override log level
export CLICKER_LOG_LEVEL="DEBUG"
python main.py
```

### System Integration

```bash
# Windows service mode
export CLICKER_SERVICE_MODE="true"
python main.py --no-gui

# Disable auto-updates
export CLICKER_NO_AUTO_UPDATE="true"
python main.py
```

## 🔧 Scripting Examples

### Profile Automation

```bash
#!/bin/bash
# setup_profiles.sh - Set up gaming and work profiles

# Create gaming profile
python -m clicker.cli.profile_manager create \
    --name "gaming" \
    --description "Optimized for gaming automation"

# Configure gaming-specific settings
python main.py --profile gaming \
    --set toggle_key=f1 \
    --set global_cooldown=0.5 \
    --set high_performance_mode=true

# Create work profile  
python -m clicker.cli.profile_manager create \
    --name "work" \
    --description "Conservative settings for productivity"

# Configure work-specific settings
python main.py --profile work \
    --set toggle_key=f12 \
    --set global_cooldown=2.0 \
    --set logging_enabled=false
```

### Validation Script

```bash
#!/bin/bash
# validate_all.sh - Validate all configurations

echo "Validating default configuration..."
python main.py --validate-config || exit 1

echo "Validating all profiles..."
for profile in $(python -m clicker.cli.profile_manager list --names-only); do
    echo "Validating profile: $profile"
    python main.py --profile "$profile" --validate-config || exit 1
done

echo "All configurations valid!"
```

### Maintenance Script

```bash
#!/bin/bash
# maintenance.sh - Perform maintenance tasks

# Clean old logs
echo "Cleaning old log files..."
find logs/ -name "*.log" -mtime +7 -delete

# Validate configurations
echo "Validating configurations..."
python main.py --validate-config

# Check system permissions
echo "Checking system permissions..."
python main.py --check-permissions

# Show statistics
echo "Current statistics:"
python main.py --stats
```

For more information, see the [Configuration Guide](configuration.md) and [API Documentation](API.md). 