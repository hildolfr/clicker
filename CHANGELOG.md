# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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