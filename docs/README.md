<div align="center">
  <img src="logo.png" alt="Clicker Logo" width="300"/>
</div>

# Clicker

A modern, professional Windows automation tool with clean architecture and comprehensive testing. Runs as a tray icon with no visible window. Configure your keystrokes and timing in simple text files, and control automation with a global hotkey.

**Version: 2.0** - Major Architecture Refactor & Feature Release

## Installation

### Option 1: Download the Executable (Recommended)
Download the standalone executable: [Clicker.exe](https://github.com/hildolfr/clicker/releases/download/2.1/Clicker.exe) (direct download link). No installation required!

### Option 2: Run from Source
Follow the setup instructions below.

## Features
- **Modern Architecture:** Complete refactor with clean, testable code architecture
- **Configuration Profiles:** Save, load, and switch between different configurations
- **Comprehensive Testing:** Full test suite with unit and integration tests
- **Enhanced Security:** Input validation and security hardening throughout
- **Tray icon only:** No window, just a system tray icon for control
- **Global hotkey:** Toggle automation from anywhere
- **Human-like automation:** Keystrokes are serialized and never overlap, even with complex timing
- **Visual indicators:** See automation status with GDI (fullscreen) or Pygame (windowed) indicators
- **Global cooldown:** Enforce minimum time between any keystroke executions, enhancing human-like behavior
- **Configurable:** Edit `keystrokes.txt` and `settings.json` to control behavior
- **Auto-reload:** Changes to config files are detected instantly
- **Open config from tray:** Edit your settings or keystrokes with one click
- **Singleton:** Only one instance can run at a time
- **Customizable execution order:** Run keystrokes in file order or sorted by delay
- **Keystroke randomization:** Identical timers are automatically randomized for more natural input patterns
- **Performance Optimizations:** Schedule caching, memory management, and efficient execution
- **Error Recovery:** Graceful handling of errors with automatic recovery

## Setup
1. Install requirements:
   ```
   pip install -r requirements.txt
   ```
2. Run the app:
   ```
   python main.py
   ```
3. For optimal compatibility with all applications, run with administrator privileges.

## Configuration
- **settings.json**
    ```json
    {
      "toggle_key": "~",
      "start_time_stagger": 1.7,
      "order_obeyed": false,
      "indicator_type": "gdi",
      "global_cooldown": 1.5,
      "logging_enabled": true,
      "high_performance_mode": false,
      "emergency_stop_key": "ctrl+shift+esc"
    }
    ```
  - `toggle_key`: The global hotkey that toggles automation on/off
  - `start_time_stagger`: Time in seconds to stagger initial keystroke scheduling (doesn't affect repeat timing)
  - `order_obeyed`: When true, executes keystrokes in file order; when false, sorts by delay
  - `indicator_type`: Visual indicator type ('gdi' works in fullscreen, 'pygame' is window-based)
  - `global_cooldown`: Minimum time in seconds between any keystroke executions (global rate limit)
  - `logging_enabled`: When true, enables detailed logging; when false, only logs warnings and errors (better performance)
  - `high_performance_mode`: Enable performance optimizations for high-frequency automation
  - `emergency_stop_key`: Emergency stop key combination for safety

- **keystrokes.txt**
  ```
  A 0.5
  C-2 1.0
  S-B 0.7
  ```
  Format: `key delay` where:
  - `key`: The key to press, with optional modifiers (S- for Shift, C- for Ctrl, A- for Alt)
  - `delay`: Time in seconds to wait before pressing this key again

## Configuration Profiles

Version 2.0 introduces a powerful profile system for managing multiple configurations:

```bash
# Create a profile from current configuration
python -m clicker.cli.profile_manager create "Gaming Setup"

# List all profiles
python -m clicker.cli.profile_manager list

# Load a profile
python -m clicker.cli.profile_manager load "Gaming Setup"

# Export/import profiles for sharing
python -m clicker.cli.profile_manager export "Gaming Setup" gaming.json
python -m clicker.cli.profile_manager import gaming.json
```

See [PROFILE_USAGE.md](PROFILE_USAGE.md) for complete profile management documentation.

## API Documentation

Comprehensive API documentation is available in [docs/API.md](docs/API.md), covering:
- Core application components
- Configuration management
- Automation engine
- System integration
- Code examples and best practices

## Testing

Version 2.0 includes a comprehensive test suite:

```bash
# Run all tests
python tests/run_tests.py

# Run with coverage
python tests/run_tests.py --coverage

# Run specific test types
python tests/run_tests.py --unit
python tests/run_tests.py --integration
```

See [tests/README.md](tests/README.md) for complete testing documentation.

## Usage
- Use the tray icon menu to open config files, reload, or quit.
- Use the global hotkey (default: `~`) to start/stop automation.
- Edit `keystrokes.txt` to define your automation sequence.
- Modify `settings.json` to customize behavior.
- Double-click the tray icon to toggle automation on/off.

## Compatibility
- Windows 10/11 (64-bit recommended)
- Python 3.8 or higher
- Some applications may require Clicker to run with administrator privileges to receive keystrokes properly.

## Troubleshooting
- **Keystrokes not working in some applications**: Run Clicker with administrator privileges.
- **Cannot find the tray icon**: Check the system tray overflow menu (up arrow in the taskbar).
- **Settings not applying**: Make sure settings.json contains valid JSON format.
- **Application won't start**: Check if another instance is already running or if a stale lock file exists (delete clicker.lock).
- **Log file**: Review clicker.log for detailed error information.

## Platform
- Windows only (uses Windows-specific APIs for reliable keystroke simulation).

## Changelog

### v2.0 - Major Architecture Release
- **Complete Architecture Refactor**: Clean, modular, testable code architecture
- **Configuration Profiles**: Save, load, and switch between different configurations with CLI management
- **Comprehensive Testing**: Full test suite with 350+ unit tests and integration tests
- **Enhanced Security**: Input validation, path traversal protection, and security hardening
- **Performance Improvements**: Schedule caching, memory management, and optimized execution
- **Error Recovery**: Graceful error handling with automatic recovery mechanisms
- **Thread Safety**: Comprehensive thread safety improvements throughout the application
- **Resource Management**: Proper cleanup of file handles, mutex handles, and memory usage
- **API Documentation**: Complete API documentation with examples and best practices
- **Emergency Stop**: Configurable emergency stop key for enhanced safety
- **High Performance Mode**: Optimizations for high-frequency automation scenarios
- **Log Rotation**: Automatic log rotation with configurable retention
- **Progress Feedback**: Progress reporting for long-running operations
- **Conflict Detection**: Automatic detection of keystroke conflicts and validation
- **Backup System**: Automatic configuration backups with restoration capabilities

### v1.3
- Added configurable logging control to improve performance
- Set `"logging": false` in settings.json to disable detailed logging for better performance
- Fixed issue with GDI overlay not appearing after toggling automation

### v1.2
- Significant performance improvements, especially for first keypress after toggle
- Added automatic randomization for keystrokes with identical timers for more natural input patterns
- Optimized thread initialization to reduce startup delay
- Improved keystroke execution efficiency with pre-parsing and caching
- Reduced internal delays for faster and more responsive keystroke execution
- Enhanced memory efficiency with pre-allocation of data structures

### v1.1.2
- Fixed logging errors and improved stability
- Increased default start_time_stagger to 1.7 seconds for better compatibility
- Increased default global_cooldown to 1.5 seconds for more human-like interactions

### v1.1.1
- Fixed bug where GDI overlay was drawn on top of the first-run dialogue for new users.

### v1.1.0
- Initial release candidate.

## License
This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details. 