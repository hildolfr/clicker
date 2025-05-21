<div align="center">
  <img src="logo.png" alt="Clicker Logo" width="300"/>
</div>

# Clicker

A modern, background Windows automation tool for sending keystrokes at human-like intervals. Runs as a tray icon with no visible window. Configure your keystrokes and timing in simple text files, and control automation with a global hotkey.

**Version: 1.0.0** - Milestone Release

## Installation

### Option 1: Download the Executable (Recommended)
Download the standalone executable: [Clicker.exe](https://github.com/hildolfr/clicker/releases/download/1.0/Clicker.exe) (direct download link). No installation required!

### Option 2: Run from Source
Follow the setup instructions below.

## Features
- **Tray icon only:** No window, just a system tray icon for control.
- **Global hotkey:** Toggle automation from anywhere.
- **Human-like automation:** Keystrokes are serialized and never overlap, even with complex timing.
- **Configurable:** Edit `keystrokes.txt` and `settings.json` to control behavior.
- **Auto-reload:** Changes to config files are detected instantly.
- **Open config from tray:** Edit your settings or keystrokes with one click.
- **Singleton:** Only one instance can run at a time.
- **Customizable execution order:** Run keystrokes in file order or sorted by delay.

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
    "pause_time": 0.5,
    "flash_count": 3,
    "flash_interval": 200,
    "order_obeyed": false
  }
  ```
  - `toggle_key`: The global hotkey that toggles automation on/off
  - `pause_time`: Time in seconds between initial keystrokes
  - `flash_count`: Number of times to flash the tray icon when toggling
  - `flash_interval`: Milliseconds between icon flashes
  - `order_obeyed`: When true, executes keystrokes in file order; when false, sorts by delay

- **keystrokes.txt**
  ```
  A 0.5
  C-2 1.0
  S-B 0.7
  ```
  Format: `key delay` where:
  - `key`: The key to press, with optional modifiers (S- for Shift, C- for Ctrl, A- for Alt)
  - `delay`: Time in seconds to wait before pressing this key again

## Usage
- Use the tray icon menu to open config files, reload, or quit.
- Use the global hotkey (default: `~`) to start/stop automation.
- Edit `keystrokes.txt` to define your automation sequence.
- Modify `settings.json` to customize behavior.
- Double-click the tray icon to toggle automation on/off.

## Compatibility
- Windows 10/11 (64-bit recommended)
- Python 3.7 or higher
- Some applications may require Clicker to run with administrator privileges to receive keystrokes properly.

## Troubleshooting
- **Keystrokes not working in some applications**: Run Clicker with administrator privileges.
- **Cannot find the tray icon**: Check the system tray overflow menu (up arrow in the taskbar).
- **Settings not applying**: Make sure settings.json contains valid JSON format.
- **Application won't start**: Check if another instance is already running or if a stale lock file exists (delete clicker.lock).
- **Log file**: Review clicker.log for detailed error information.

## Platform
- Windows only (uses Windows-specific APIs for reliable keystroke simulation).

## License
This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details. 