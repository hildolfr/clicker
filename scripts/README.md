# Scripts Directory

This directory contains various utility scripts for the Clicker project.

## Directory Structure

- **[build/](build/)** - Build and packaging scripts
  - `build.bat` - Main Windows build script
  - `build.ps1` - PowerShell build script
  - `build_alt.bat` - Alternative build configuration
  - `Clicker.spec` - PyInstaller specification file

- **[fixes/](fixes/)** - Development utilities and fix scripts
  - Various Python scripts for testing and fixing specific issues
  - Batch files for running fixes

## Usage

### Building the Application

From the project root directory:

```bash
# Using batch script
scripts\build\build.bat

# Using PowerShell
scripts\build\build.ps1
```

### Running Fix Scripts

Navigate to the fixes directory and run the appropriate script for your issue.

## Notes

- Build scripts should be run from the project root directory
- Fix scripts may need to be run with appropriate permissions
- Always backup your configuration before running fix scripts 