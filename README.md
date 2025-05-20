<div align="center">
  <img src="logo.png" alt="Clicker Logo" width="300"/>
</div>

# Clicker

A modern, background Windows automation tool for sending keystrokes at human-like intervals. Runs as a tray icon with no visible window. Configure your keystrokes and timing in simple text files, and control automation with a global hotkey.

## Features
- **Tray icon only:** No window, just a system tray icon for control.
- **Global hotkey:** Toggle automation from anywhere.
- **Human-like automation:** Keystrokes are serialized and never overlap, even with complex timing.
- **Configurable:** Edit `keystrokes.txt` and `settings.json` to control behavior.
- **Auto-reload:** Changes to config files are detected instantly.
- **Open config from tray:** Edit your settings or keystrokes with one click.
- **Singleton:** Only one instance can run at a time.

## Setup
1. Install requirements:
   ```
   pip install -r requirements.txt
   ```
2. Run the app:
   ```
   python main.py
   ```

## Configuration
- **settings.json**
  ```json
  {
    "toggle_key": "~",
    "pause_time": 0.5
  }
  ```
- **keystrokes.txt**
  ```
  A 0.5
  C-2 1.0
  S-B 0.7
  ```
  (Format: key [delay in seconds]. Modifiers: S- (shift), C- (ctrl), A- (alt))

## Usage
- Use the tray icon menu to open config files, reload, or quit.
- Use the global hotkey (default: `~`) to start/stop automation.

## Platform
- Windows only (uses `os.startfile` and `pyautogui`).

## License
This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details. 