# Clicker Portable Distribution v1.1.0

## About This Distribution

This is a portable distribution of the Clicker application. The application has been packaged into a single executable file for easier distribution and use. All necessary dependencies are included within the executable.

## Installation

No installation is required. Simply download the executable file and run it.

## Usage Instructions

1. Double-click the Clicker.exe file to start the application
2. The application will appear in your system tray (bottom right of screen)
3. Right-click on the system tray icon to access options
4. Press the tilde key (`~`) by default to toggle automation on/off

## Important Notes

- This application requires administrator privileges to function properly, especially for keyboard automation
- Windows may show a security warning when running for the first time - this is normal for applications that simulate keyboard input
- The first time you run the application, it will create necessary configuration files in the same folder

## Files Created During Runtime

When you run the application, it will create or use these files in the same directory as the executable:

- `settings.json` - Contains application settings
- `keystrokes.txt` - Contains the keystrokes to automate
- `clicker.log` - Log file for troubleshooting
- `.clicker_setup_done` - Internal file to track initial setup
- `clicker.lock` - Used to prevent multiple instances from running

## Configuration

You can modify the application's behavior by editing these files:

1. **settings.json** - Controls general settings like the toggle key
2. **keystrokes.txt** - Defines what keys are pressed during automation

See the main README.md file for detailed configuration instructions.

## Support

If you encounter any issues, please check the clicker.log file for error messages. 