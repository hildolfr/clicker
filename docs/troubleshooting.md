# Troubleshooting Guide

Comprehensive guide for resolving common issues with Clicker.

## 🚀 Installation Issues

### Python Version Problems

**Issue**: Application won't start, Python version error
```
Python 3.11 or higher is required
```

**Solution**:
1. Check your Python version: `python --version`
2. Install Python 3.11+ from [python.org](https://python.org)
3. Verify installation: `python --version`

### Dependency Installation

**Issue**: Missing dependencies, import errors
```
ModuleNotFoundError: No module named 'keyboard'
ModuleNotFoundError: No module named 'PyQt5'
```

**Solution**:
```bash
# Install all dependencies
pip install -r requirements.txt

# If that fails, try upgrading pip first
python -m pip install --upgrade pip
pip install -r requirements.txt

# Install individual dependencies if needed
pip install keyboard PyQt5 psutil
```

### Windows-Specific Issues

**Issue**: `keyboard` library not working
```
OSError: [WinError 5] Access is denied
```

**Solution**:
1. Run as administrator
2. Check antivirus software isn't blocking the application
3. Verify Windows version compatibility (Windows 10/11)

## ⌨️ Hotkey Issues

### Hotkeys Not Working

**Issue**: Global hotkeys don't respond
```
Hotkey manager unavailable
Failed to register hotkey
```

**Solutions**:

**Check Dependencies**:
```bash
pip install keyboard
```

**Run as Administrator**:
- Right-click `main.py` → "Run as administrator"
- Or run from elevated command prompt

**Check for Conflicts**:
- Other applications using the same hotkey
- Try different key combination in `settings.json`:
```json
{
  "toggle_key": "f1",  // Instead of "~"
  "emergency_stop_key": "ctrl+shift+esc"
}
```

### Hotkey Configuration Errors

**Issue**: Invalid hotkey configuration
```
ValueError: toggle_key conflicts with system shortcuts
```

**Solution**: Use safe key combinations
```json
{
  "toggle_key": "f1",           // ✅ Good
  "toggle_key": "ctrl+alt+del", // ❌ System shortcut
  "emergency_stop_key": "ctrl+shift+esc"  // ✅ Required modifiers
}
```

## 🔧 Automation Issues

### Keystrokes Not Sending

**Issue**: Automation runs but keys don't register in target application

**Solutions**:

**Check Target Application**:
- Some games/applications block automated input
- Try running target application as normal user (not administrator)
- Test with simple applications like Notepad first

**Verify Keystroke Format**:
```
# keystrokes.txt - Correct format
a 1.5        # ✅ Key 'a' every 1.5 seconds
C-c 2.0      # ✅ Ctrl+C every 2 seconds
invalid-key  # ❌ Missing delay
```

**Check Configuration**:
```json
{
  "keystroke_method": "windows_api",  // Try different methods
  "global_cooldown": 1.5,            // Increase if too fast
  "high_performance_mode": false     // Disable for compatibility
}
```

### Timing Issues

**Issue**: Keystrokes too fast or inconsistent

**Solutions**:

**Adjust Global Cooldown**:
```json
{
  "global_cooldown": 2.0  // Minimum 2 seconds between keystrokes
}
```

**Individual Keystroke Delays**:
```
# Slower intervals for better reliability
a 3.0    # 3 second intervals
b 2.5    # 2.5 second intervals
```

**Performance Settings**:
```json
{
  "high_performance_mode": false,  // Disable for stability
  "thread_pool_size": 1           // Reduce concurrency
}
```

## 📁 Configuration Issues

### Settings File Problems

**Issue**: Configuration file errors
```
JSONDecodeError: Expecting ',' delimiter
ConfigurationError: Invalid configuration
```

**Solutions**:

**Validate JSON Syntax**:
```bash
# Use online JSON validator or
python -m json.tool settings.json
```

**Reset to Defaults**:
```bash
# Backup current settings
copy settings.json settings.json.backup

# Delete settings.json to regenerate defaults
del settings.json
python main.py
```

**Fix Common JSON Errors**:
```json
{
  "toggle_key": "~",        // ✅ Use double quotes
  "global_cooldown": 1.5,   // ✅ No trailing comma on last item
  "logging_enabled": true   // ✅ Use lowercase true/false
}
```

### Keystrokes File Issues

**Issue**: Keystrokes not loading
```
Error parsing keystrokes.txt
Invalid keystroke format
```

**Solutions**:

**Check File Format**:
```
# keystrokes.txt - Correct format
# Lines starting with # are comments
a 1.5
b 2.0
C-c 1.0  # Ctrl+C

# Invalid examples:
a        # Missing delay
1.5 a    # Wrong order
x -1.0   # Negative delay
```

**Validate Keystrokes**:
```bash
python main.py --validate-config
```

## 🖥️ System Tray Issues

### Tray Icon Missing

**Issue**: System tray icon doesn't appear

**Solutions**:

**Check Windows Settings**:
1. Right-click system tray → "Taskbar settings"
2. Scroll to "Notification area"
3. Click "Select which icons appear on the taskbar"
4. Enable "Clicker" or "Python"

**Run with Qt Dependencies**:
```bash
pip install PyQt5
python main.py
```

### Tray Menu Not Working

**Issue**: Right-click menu doesn't appear or work

**Solutions**:

**Check Qt Installation**:
```bash
pip install --upgrade PyQt5
```

**Reset Tray Settings**:
```json
{
  "minimize_to_tray": true,
  "show_notifications": true
}
```

## 🔄 Performance Issues

### High CPU Usage

**Issue**: Clicker consuming too much CPU

**Solutions**:

**Optimize Settings**:
```json
{
  "high_performance_mode": false,
  "thread_pool_size": 1,
  "global_cooldown": 2.0,
  "logging_enabled": false  // Reduces I/O
}
```

**Check Keystroke Intervals**:
```
# Avoid very fast intervals
a 0.1    # ❌ Too fast, high CPU
a 1.0    # ✅ Better performance
```

### Memory Usage

**Issue**: Memory usage growing over time

**Solutions**:

**Configure Limits**:
```json
{
  "memory_limit_mb": 50,     // Limit memory usage
  "log_retention_days": 3,   // Reduce log retention
  "config_backup_count": 3   // Fewer config backups
}
```

**Monitor Resources**:
```bash
# Check memory usage
python main.py --stats
```

## 🔍 Debugging Issues

### Enable Debug Logging

**Issue**: Need more detailed error information

**Solution**:
```json
{
  "logging_enabled": true  // Enable detailed logging
}
```

**Check Log Files**:
- Log location: `logs/clicker.log`
- View recent errors: `tail -f logs/clicker.log`

### Common Error Messages

**"Singleton violation detected"**
- Another instance of Clicker is already running
- Close other instances or check task manager

**"Admin privileges required"**
- Some features need administrator access
- Run as administrator

**"Configuration validation failed"**
- Check `settings.json` syntax
- Run `python main.py --validate-config`

**"Keystroke sender unavailable"**
- Windows API access issue
- Try running as administrator
- Check antivirus software

## 🛡️ Security Issues

### Antivirus False Positives

**Issue**: Antivirus blocking Clicker

**Solutions**:
1. Add Clicker folder to antivirus exclusions
2. Add `python.exe` to exclusions
3. Whitelist the keyboard library
4. Run from trusted location

### Windows Defender SmartScreen

**Issue**: "Windows protected your PC" warning

**Solutions**:
1. Click "More info" → "Run anyway"
2. Right-click `main.py` → Properties → Unblock
3. Add exception in Windows Defender

## 🔧 Advanced Troubleshooting

### Reset Application State

**Complete Reset**:
```bash
# Backup current configuration
copy settings.json settings_backup.json
copy keystrokes.txt keystrokes_backup.txt

# Delete configuration files
del settings.json
del keystrokes.txt

# Clear logs
rmdir /s logs

# Restart application
python main.py
```

### Configuration Validation

**Validate All Settings**:
```bash
python main.py --validate-config
python main.py --test-hotkeys
python main.py --check-permissions
```

### Environment Information

**System Check**:
```bash
python --version
pip list | findstr -i "keyboard PyQt5 psutil"
python -c "import sys; print(sys.platform)"
```

## 📞 Getting Help

### Before Reporting Issues

1. **Check this troubleshooting guide**
2. **Enable debug logging** and check log files
3. **Try with default configuration**
4. **Test with administrator privileges**
5. **Verify system requirements**

### Information to Include

When reporting issues, include:
- Python version (`python --version`)
- Windows version
- Error messages from logs
- Configuration files (settings.json, keystrokes.txt)
- Steps to reproduce the issue

### Log File Locations

- **Main log**: `logs/clicker.log`
- **Error log**: `logs/clicker_error.log`
- **Debug log**: `logs/clicker_debug.log` (when debug enabled)

### Emergency Recovery

**If Clicker won't start**:
1. Delete `settings.json`
2. Delete `keystrokes.txt`
3. Run `python main.py` to regenerate defaults

**If automation stuck**:
1. Press `Ctrl+Shift+Esc` (emergency stop)
2. Close from task manager if needed
3. Check for singleton file: `.clicker_singleton`

For additional support, see the [API Documentation](API.md) and [Configuration Guide](configuration.md). 