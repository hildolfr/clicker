# 🖱️ Clicker - Professional Windows Automation Suite

<div align="center">

<img src="docs/assets/logo.png" alt="Clicker Logo" width="200" height="auto">

**A lightweight Windows keystroke automation tool with system tray integration and configurable timing**

[![Version](https://img.shields.io/badge/version-2.1.1-blue.svg)](https://github.com/hildolfr/clicker)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://microsoft.com/windows)

[![Download Latest Release](https://img.shields.io/badge/📦%20Download-Latest%20Release-brightgreen.svg?style=for-the-badge)](https://github.com/hildolfr/clicker/releases/latest)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-documentation) • [Development](#-development)

</div>

---

## 🚀 Features

### 🎯 **Core Automation**
- **Keystroke Automation** - Send keyboard keys at configurable intervals and timing
- **Configurable Key Sequences** - Define multiple keystrokes with individual delays and descriptions  
- **Hotkey Toggle Control** - Start/stop automation using configurable hotkeys (default: `~`)
- **System Integration** - Uses Windows API for reliable keystroke sending

### 🖥️ **User Interface**
- **System Tray Integration** - Runs minimized in system tray with context menu access
- **Visual Indicators** - Optional on-screen indicators showing automation status (GDI-based)
- **Qt5-based GUI** - Clean PyQt5 interface for system tray and configuration
- **Real-time Status** - Live status updates via tray icon tooltip

### ⚙️ **Configuration Management**
- **Profile System** - Save and load different keystroke configurations
- **JSON Configuration** - Human-readable settings.json and profile management
- **File-based Keystrokes** - Simple keystrokes.txt format for easy editing
- **Command-Line Profile Tools** - CLI utilities for profile management

### 🔧 **Automation Features**
- **Flexible Timing** - Individual delay settings per keystroke (0.1s - 1 hour)
- **Modifier Key Support** - Ctrl, Shift, Alt combinations (e.g., C-S-a for Ctrl+Shift+A)
- **Error Handling** - Robust error tracking with statistics and failure recovery
- **Threading** - Background automation with proper thread management

### 🛡️ **Safety & Control**
- **Emergency Stop** - Configurable emergency stop hotkey (default: Ctrl+Shift+Esc)
- **Execution Limits** - Maximum execution time limits to prevent runaway automation
- **Fail-safe Mode** - Built-in safeguards and error detection
- **Logging System** - Comprehensive logging with rotation and retention settings

### 🔧 **Technical Features**
- **Windows API Integration** - Native Windows keystroke sending via user32.dll
- **File Watching** - Automatic configuration reload when files change
- **Statistics Tracking** - Success/failure rates and execution monitoring
- **Memory Management** - Configurable memory limits and resource cleanup

## 📦 Installation

### Quick Start
```bash
# Clone the repository
git clone https://github.com/hildolfr/clicker.git
cd clicker

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### System Requirements
- **Operating System**: Windows 10/11 (64-bit)
- **Python**: 3.11 or higher
- **Memory**: 50MB RAM minimum
- **Disk Space**: 100MB free space

## 🎮 Usage

### Basic Operation
1. **Launch Application**: Run `python main.py`
2. **Configure Keystrokes**: Edit `keystrokes.txt` with your desired key sequences
3. **Adjust Settings**: Modify `settings.json` for timing and behavior preferences
4. **Start Automation**: Press the toggle key (`~` by default) or use system tray controls

### Keystroke Configuration Format
```
# keystrokes.txt format
key delay description
1 2.0 Press number 1 every 2 seconds
C-c 5.0 Ctrl+C every 5 seconds
S-A-f4 10.0 Shift+Alt+F4 every 10 seconds
```

### Key Syntax
- **Single Keys**: `a`, `1`, `space`, `enter`, `f1`-`f12`
- **Modifiers**: `C-` (Ctrl), `S-` (Shift), `A-` (Alt)
- **Combinations**: `C-S-a` (Ctrl+Shift+A)

## 📚 Documentation

### 📖 **User Guides**
- **[Getting Started Guide](docs/getting-started.md)** - Basic setup and configuration
- **[Configuration Guide](docs/configuration.md)** - Detailed configuration options
- **[Hotkey Reference](docs/hotkeys.md)** - Supported keys and combinations
- **[Troubleshooting Guide](docs/troubleshooting.md)** - Common issues and solutions

### 🔧 **Technical Documentation**
- **[Profile Usage](docs/PROFILE_USAGE.md)** - Profile management and CLI tools
- **[Configuration Schema](docs/config-schema.md)** - Configuration file reference
- **[Command Line Reference](docs/cli-reference.md)** - CLI commands and options
- **[API Reference](docs/API.md)** - Code structure and architecture

### 📋 **References**
- **[Release Notes](docs/release-notes.md)** - Version history and changes

## 🛠️ Development

### Project Architecture

Clicker follows a modular architecture for maintainability:

```
clicker/
├── 🏗️ core/              # Automation engine and keystrokes
├── 🖥️ ui/                # System tray and visual indicators  
├── ⚙️ config/            # Configuration management and models
├── 🔌 plugins/           # Plugin system (framework ready)
├── 🛠️ utils/             # Utility modules and helpers
├── 💻 cli/               # Command-line profile management
├── 🖱️ system/            # Windows API integration
└── 📱 app.py             # Main application orchestrator
```

### Key Technologies
- **PyQt5** - System tray and GUI components
- **Windows API** - Native keystroke sending via ctypes
- **Threading** - Background automation execution
- **JSON** - Configuration storage and profiles
- **File Watching** - Automatic configuration reloading

### Build & Development Tools

```bash
# Development setup
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Profile management CLI
python -m clicker.cli.profile_manager --help

# Build with PyInstaller
pyinstaller Clicker.spec
```

## 🌟 What Makes Clicker Useful

### 🎯 **Simple but Reliable**
Clicker focuses on doing keystroke automation well with minimal complexity and reliable Windows integration.

### 🏗️ **Clean Architecture**
Modular design with proper separation of concerns, making it maintainable and extensible.

### 🔧 **Flexible Configuration**
Easy-to-edit text files combined with a robust profile system for different automation scenarios.

### 🛡️ **Safety First**
Built-in safety mechanisms, error handling, and emergency stops to prevent issues during automation.

## 🤝 Contributing

We welcome contributions! Whether it's bug reports, feature requests, or code contributions, please see our [Contributing Guide](docs/dev/contributing.md) for details.

### 🐛 Bug Reports
Found a bug? Please create an issue with detailed reproduction steps.

### 💡 Feature Requests
Have an idea? We'd love to hear it! Open a feature request issue.

### 🔧 Code Contributions
Ready to contribute code? Check out our development documentation and submit a pull request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Special thanks to all contributors and the open-source community for making this project possible.

---

<div align="center">

**Made with ❤️ for the automation community**

[⬆ Back to Top](#-clicker---professional-windows-automation-suite)

</div> 