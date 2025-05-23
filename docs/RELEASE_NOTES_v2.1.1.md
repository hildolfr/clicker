# Clicker v2.1.1 Release Notes

**Release Date**: May 23, 2025  
**Version**: 2.1.1  
**Type**: Bugfix Release

Version 2.1.1 is a critical bugfix release that resolves autoupdate issues affecting users on systems without Python installed. This release ensures reliable application updates and improved user experience.

## 🐛 Critical Bugfixes

### Autoupdate System Overhaul
**Issue**: Users were experiencing "Python missing" errors after autoupdates completed, preventing the application from restarting properly.

**Root Cause**: The autoupdate system was using flawed executable path detection logic that could result in restart commands pointing to Python scripts instead of the actual executable file.

**Resolution**: Complete overhaul of the autoupdate system with:
- **Enhanced Executable Path Detection**: Smart detection algorithm that searches for actual `.exe` files in common locations
- **Multi-layer Validation**: Multiple validation checks to ensure restart commands target executable files
- **Improved Batch Scripts**: Enhanced update scripts with built-in validation and error handling
- **Comprehensive Error Handling**: Better error messages and fallback mechanisms
- **Detailed Logging**: Enhanced logging for troubleshooting update issues

### Technical Details

#### Enhanced Path Detection Algorithm
```python
# NEW: Intelligent executable detection
possible_exe_paths = [
    script_dir / "Clicker.exe",  # Same directory as script
    script_dir / "dist" / "Clicker.exe",  # In dist subdirectory
    script_dir.parent / "Clicker.exe",  # Parent directory
    script_dir.parent / "dist" / "Clicker.exe",  # Parent/dist
]
```

#### Improved Update Script Validation
- Validates target paths are actual executable files
- Checks file existence before attempting restart
- Provides clear error messages when issues occur
- Includes fallback mechanisms for recovery

#### Enhanced Error Handling
- File size validation for download integrity
- Process validation for script execution
- Comprehensive logging throughout update process
- User-friendly error messages with recovery instructions

## 🛡️ Safety Improvements

### Update Process Validation
- **Download Integrity**: Validates downloaded file size and accessibility
- **Script Validation**: Ensures update scripts are created successfully
- **Path Validation**: Confirms executable paths before restart attempts
- **Process Monitoring**: Tracks update script execution with proper error handling

### User Experience Enhancements
- **Clear Error Messages**: Improved error reporting with actionable instructions
- **Better Logging**: Enhanced logging for support and troubleshooting
- **Graceful Fallbacks**: Better handling when automatic restart fails
- **Manual Recovery**: Clear instructions for manual update completion

## 📋 Files Modified

### Core Components
- `clicker/utils/updater.py`: Complete autoupdate system overhaul
- `clicker/app.py`: Version bump to 2.1.1
- `clicker/__init__.py`: Version update
- `pyproject.toml`: Project version update

### Documentation Updates
- `README.md`: Version and link updates
- `docs/RELEASE_NOTES_v2.1.1.md`: This release notes file
- Version references updated throughout documentation

## 🔄 Upgrade Instructions

### For Existing Users
1. **Automatic Update**: If you have autoupdates enabled, version 2.1.1 will be downloaded and installed automatically
2. **Manual Update**: Download the new executable from the releases page
3. **No Configuration Changes**: Your existing settings and configurations remain unchanged

### For New Users
- Download and install version 2.1.1 directly
- All new installations include the improved autoupdate system

## 🧪 Testing

### Autoupdate Testing
- ✅ Tested update process from 2.1.0 to 2.1.1
- ✅ Verified executable path detection on various system configurations
- ✅ Confirmed proper restart functionality after updates
- ✅ Validated error handling and fallback mechanisms

### Compatibility Testing
- ✅ Windows 10 compatibility confirmed
- ✅ Windows 11 compatibility confirmed
- ✅ Tested on systems with and without Python installed
- ✅ Verified integration with existing configuration files

## 📈 Impact

### User Impact
- **Eliminates "Python missing" errors** after autoupdates
- **Improves update reliability** with enhanced validation
- **Better error reporting** for easier troubleshooting
- **Seamless update experience** for all users

### Technical Impact
- **Robust update system** resistant to path detection issues
- **Enhanced logging** for better support capabilities
- **Improved error handling** throughout update process
- **Future-proof architecture** for reliable updates

## 🔗 Download

**Direct Download**: [Clicker v2.1.1 Executable](https://github.com/hildolfr/clicker/releases/download/v2.1.1/Clicker.exe)

**System Requirements**:
- Windows 10/11 (64-bit)
- 50MB RAM minimum
- 100MB free disk space
- Internet connection for autoupdates

## 📞 Support

If you experience any issues with this release:
1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review the application logs
3. Create an issue on GitHub with detailed information
4. Contact support with log files if needed

## 🙏 Acknowledgments

Special thanks to users who reported the autoupdate issues and provided detailed feedback that made this fix possible.

---

**Previous Release**: [v2.1.0 Release Notes](RELEASE_NOTES_v2.1.md)  
**Next Release**: Coming soon... 