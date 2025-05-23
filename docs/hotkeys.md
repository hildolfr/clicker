# Hotkey Reference

Complete reference for keyboard shortcuts and hotkey functionality in Clicker.

## 🎮 Global Hotkeys

Clicker supports **one global hotkey** that toggles automation on/off. This hotkey works system-wide, even when Clicker is running in the background.

### Toggle Hotkey
- **Default**: `~` (tilde key)
- **Function**: Start/stop automation
- **Scope**: Global (works when Clicker is minimized to system tray)
- **Configurable**: Yes, via settings.json

### Emergency Stop Key
- **Default**: `ctrl+shift+esc`
- **Function**: Emergency stop for safety
- **Scope**: Global system hotkey
- **Configurable**: Yes, via settings.json
- **Safety**: Requires modifier keys to prevent accidental activation

## ⚙️ Hotkey Configuration

### Setting the Toggle Key

The toggle key can be configured in your `settings.json` file:

```json
{
  "toggle_key": "~",
  "emergency_stop_key": "ctrl+shift+esc"
}
```

### Supported Key Formats

**Single Keys:**
- Letters: `a`, `b`, `c`, etc.
- Numbers: `1`, `2`, `3`, etc.  
- Special keys: `space`, `enter`, `tab`, `escape`, etc.
- Function keys: `f1`, `f2`, `f3`, etc.

**Key Combinations:**
- Simple combinations: `ctrl+a`, `alt+f1`, `shift+space`
- Complex combinations: `ctrl+shift+esc`, `ctrl+alt+q`

### Key Name Reference

**Letters and Numbers:**
- All alphanumeric keys: `a-z`, `0-9`

**Function Keys:**
- `f1` through `f12`

**Special Keys:**
- `space` - Spacebar
- `enter` - Enter key
- `tab` - Tab key
- `escape` - Escape key
- `backspace` - Backspace key
- `delete` - Delete key
- `insert` - Insert key
- `home` - Home key
- `end` - End key
- `pageup` - Page Up key
- `pagedown` - Page Down key
- `up`, `down`, `left`, `right` - Arrow keys

**Modifier Keys:**
- `ctrl` - Control key
- `shift` - Shift key
- `alt` - Alt key

## 🔧 Hotkey Examples

### Common Configurations

**Gaming Setup:**
```json
{
  "toggle_key": "f1",
  "emergency_stop_key": "ctrl+alt+q"
}
```

**Work Setup:**
```json
{
  "toggle_key": "ctrl+f12",
  "emergency_stop_key": "ctrl+shift+esc"
}
```

**Simple Setup:**
```json
{
  "toggle_key": "`",
  "emergency_stop_key": "shift+ctrl+esc"
}
```

## 🛡️ Safety Features

### Emergency Stop
The emergency stop key provides an immediate way to halt all automation:
- Requires modifier keys for safety (e.g., `ctrl+shift+esc`)
- Works even if the main toggle hotkey fails
- Cannot be disabled or empty for safety reasons

### Hotkey Conflicts
- Clicker validates hotkeys to prevent conflicts with critical system shortcuts
- Automatically falls back to `~` if the configured hotkey fails to register
- Warns about potentially problematic key combinations

### Restricted Keys
These key combinations are **not allowed** as toggle keys for safety:
- `ctrl+alt+del` - System security
- `alt+f4` - Window close
- `win+l` - Lock screen
- `ctrl+shift+esc` - Task manager (reserved for emergency stop)

## 🔍 Troubleshooting

### Hotkey Not Working

**Check Administrator Privileges:**
```bash
# Run Clicker as administrator for global hotkey access
# Right-click main.py -> Run as administrator
```

**Verify Configuration:**
```json
{
  "toggle_key": "~",  // Make sure this is valid
  "emergency_stop_key": "ctrl+shift+esc"  // Must include modifiers
}
```

**Check for Conflicts:**
- Other applications may be using the same hotkey
- Try a different key combination
- Check Windows hotkey settings

### Common Issues

**"Hotkey manager unavailable"**
- The `keyboard` library is not installed
- Install dependencies: `pip install -r requirements.txt`

**"Failed to register hotkey"**
- Another application is using the same key
- Try running as administrator
- Use a different key combination

**Hotkey stops working**
- The hotkey service may have crashed
- Restart Clicker to re-register hotkeys
- Check Windows Event Viewer for errors

## 📱 System Tray Integration

When Clicker is minimized to the system tray, hotkeys remain active:

### System Tray Controls
- **Left-click**: Show main window (if GUI exists)
- **Right-click**: Context menu with options:
  - Toggle automation
  - Reload configuration  
  - Open files
  - Check for updates
  - Quit application

### Tray Icon States
- **Green**: Automation is running
- **Gray**: Automation is stopped
- **Red**: Error state

## 🎯 Keystroke Automation Keys

Beyond hotkeys, Clicker automates individual keystrokes defined in `keystrokes.txt`:

### Keystroke Format
```
# Format: KEY DELAY
a 1.5
C-c 2.0    # Ctrl+C
S-f1 1.0   # Shift+F1
A-tab 2.5  # Alt+Tab
```

### Keystroke Modifiers
- `C-` - Control modifier
- `S-` - Shift modifier  
- `A-` - Alt modifier

### Examples
```
# Basic keys
1 1.0        # Press '1' every 1 second
space 2.0    # Press spacebar every 2 seconds
enter 1.5    # Press enter every 1.5 seconds

# Modified keys
C-a 3.0      # Ctrl+A every 3 seconds
S-f1 1.0     # Shift+F1 every 1 second
A-tab 4.0    # Alt+Tab every 4 seconds
C-S-z 2.0    # Ctrl+Shift+Z every 2 seconds
```

## 🔄 Dynamic Configuration

### Runtime Changes
- Configuration changes are detected automatically via file watching
- Hotkeys are re-registered when settings.json is modified
- No restart required for hotkey changes

### Configuration Validation
```bash
# Validate configuration
python main.py --validate-config

# Test hotkey registration
python main.py --test-hotkeys
```

## 📚 API Integration

### Programmatic Hotkey Management
```python
from clicker.system.hotkeys import HotkeyManager

# Register a hotkey
hotkey_manager = HotkeyManager()
hotkey_manager.register_hotkey("toggle", "f1", callback_function)

# Update hotkey
hotkey_manager.update_hotkey("toggle", "f2")

# Unregister hotkey
hotkey_manager.unregister_hotkey("toggle")
```

For more configuration options, see the [Configuration Guide](configuration.md). 