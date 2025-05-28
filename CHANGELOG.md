# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.2] - 2025-05-27

### 🐛 Fixed
- **Tilde Key Combinations**: Fixed critical bug where tilde (~) key combinations were not being properly registered
- **Hotkey Registration**: Enhanced hotkey registration to properly handle tilde character in key combinations
- **Key Mapping**: Improved key mapping logic to correctly process tilde-based hotkey sequences
- **Combination Detection**: Fixed detection and processing of complex tilde key combinations (e.g., `Ctrl+~`, `~+letter`)

### 🔧 Technical Improvements
- **Enhanced Key Processing**: Updated key combination parsing to handle special characters like tilde
- **Improved Hotkey System**: Strengthened hotkey registration system for better compatibility with all key types
- **Better Error Handling**: Added more robust error handling for edge cases in key combination registration

### 📝 Documentation
- **Test Coverage**: Added test cases for tilde key combination functionality
- **Code Documentation**: Enhanced documentation for key combination processing logic

## [2.2.1] - 2024-12-28

### 🐛 Fixed
- **Order Obeyed Setting**: Fixed critical bug where `order_obeyed` setting was not properly controlling keystroke execution order
- **File Order Execution**: When `order_obeyed=True`, keystrokes now correctly execute in file order (top to bottom)
- **Delay Order Execution**: When `order_obeyed=False`, keystrokes now correctly execute sorted by delay value (lowest to highest)
- **Schedule Cache Invalidation**: Fixed schedule cache not being invalidated when `order_obeyed` setting changes

### 🔧 Technical Improvements
- **Enhanced Schedule Building**: Improved schedule building logic to properly respect `order_obeyed` configuration
- **Cache Hash Calculation**: Updated schedule cache hash to include `order_obeyed` setting for proper invalidation
- **Test Coverage**: Added comprehensive test cases for `order_obeyed` functionality

### 📝 Documentation
- **Test Suite**: Enhanced test suite with specific test cases for order execution scenarios
- **Code Documentation**: Improved documentation for scheduling and execution order logic

## [2.2.0] - 2024-12-28

### 🚀 Added
- **Real-time File Watching**: Implemented `watchdog`-based file monitoring for `settings.json` and `keystrokes.txt`
- **Instant Configuration Reload**: Configuration files are now automatically reloaded immediately when changed
- **Improved Reliability**: File watching uses OS-native APIs for more reliable change detection

### 🔧 Changed
- **Replaced Timer-based Monitoring**: Removed the previous 30-second timer approach in favor of event-driven file watching
- **Enhanced File Change Detection**: Now detects file modifications, creations, and moves (compatible with various text editors)
- **Optimized Performance**: Eliminated unnecessary polling, reducing CPU usage

### 🐛 Fixed
- **Configuration Reload Issues**: Resolved persistent problems with configuration files not being detected
- **Timer Reliability**: Eliminated issues where the timer-based approach would miss file changes
- **Application Shutdown**: Fixed shutdown sequence to properly stop file watcher

### 🛠️ Technical Improvements
- **Debouncing**: Added 1-second cooldown to prevent duplicate reloads from rapid file changes
- **Error Handling**: Enhanced error handling in file change callbacks
- **Resource Management**: Improved cleanup of file watching resources during application shutdown

### 📝 Documentation
- **Updated README**: Enhanced documentation to reflect real-time file watching capabilities
- **Code Comments**: Added comprehensive documentation for new file watching implementation

## [2.1.3] - Previous Release
- Previous features and functionality (timer-based configuration reload, system tray integration, etc.) 