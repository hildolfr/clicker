# Release Notes

Version history and release information for Clicker.

## Current Version: 2.1.0

For detailed release notes for the current version, see [Version 2.1 Release Notes](RELEASE_NOTES_v2.1.md).

## Version History

### Version 2.1.0 (Current)
- **Release Date**: 2025
- **Type**: Major bugfix and reorganization release
- **Highlights**: 
  - Complete codebase reorganization with clean architecture
  - Improved error handling and reliability
  - Enhanced configuration management
  - Better performance and resource usage
  - Professional system tray integration
  - Comprehensive logging system

[View detailed 2.1.0 release notes →](RELEASE_NOTES_v2.1.md)

### Version 2.0.x
- **Release Date**: 2024
- **Type**: Major rewrite
- **Highlights**:
  - Complete application rewrite from monolithic structure
  - Introduction of profile system
  - Modern architecture with dependency injection
  - Enhanced automation engine
  - Improved GUI and user experience

## Breaking Changes

### Version 2.1.0
- Configuration file format updates
- Legacy settings migration required
- Some command-line arguments changed

### Version 2.0.0
- Complete configuration format change from v1.x
- New keystroke format in `keystrokes.txt`
- Updated hotkey system

## Migration Guides

### Upgrading to 2.1.0
The application automatically migrates configurations from version 2.0.x. No manual intervention required.

### Upgrading from 1.x to 2.0+
Version 2.0+ is a complete rewrite. Manual migration of settings is required:

1. **Backup v1.x configuration**
2. **Install v2.1.0**
3. **Manually configure settings** based on old configuration
4. **Test thoroughly** before production use

## System Requirements

### Current Requirements (v2.1.0)
- **Operating System**: Windows 10/11 (64-bit)
- **Python**: 3.11 or higher
- **Memory**: 50MB RAM minimum
- **Disk Space**: 100MB free space
- **Dependencies**: See `requirements.txt`

### Legacy Requirements
- **v2.0.x**: Python 3.9+, Windows 10+
- **v1.x**: Python 3.7+, Windows 7+

## Download Information

### Current Release
- **Version**: 2.1.0
- **Download**: Clone from repository
- **Installation**: `pip install -r requirements.txt`
- **Documentation**: Full documentation in `docs/` folder

### Development Builds
Development builds and beta versions are available in the `dev` branch.

## Support Information

### Support Lifecycle
- **Current Version (2.1.x)**: Full support
- **Previous Version (2.0.x)**: Security updates only
- **Legacy Versions (1.x)**: No longer supported

### Getting Help
- **Documentation**: Complete guides in `docs/` folder
- **Troubleshooting**: See [Troubleshooting Guide](troubleshooting.md)
- **Issues**: Report via repository issue tracker
- **API**: See [API Documentation](API.md)

## Development Information

### Release Schedule
- **Major versions**: Annual (architectural changes)
- **Minor versions**: Quarterly (new features)
- **Patch versions**: As needed (bug fixes)

### Contributing
See [Contributing Guide](dev/contributing.md) for development information.

### Changelog Format
All releases follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes, architectural rewrites
- **MINOR**: New features, enhancements
- **PATCH**: Bug fixes, security updates 