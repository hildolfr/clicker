# Getting Started with Clicker

Welcome to Clicker, the professional Windows automation suite! This guide will help you get up and running quickly.

## 📋 Prerequisites

Before you begin, ensure you have:
- Windows 10 or 11 (64-bit)
- Python 3.11 or higher
- At least 50MB of free RAM
- 100MB of free disk space

## 🚀 Quick Installation

### 1. Download and Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/clicker.git
cd clicker

# Install dependencies
pip install -r requirements.txt
```

### 2. First Launch
```bash
# Start the application
python main.py
```

## 🎯 Your First Automation

### Basic Auto-Clicking Setup

1. **Launch Clicker**: Run `python main.py`
2. **Open the GUI**: The main window will appear with the Clicker interface
3. **Set Click Position**: 
   - Click "Set Position" and move your mouse to the desired click location
   - Press the capture hotkey (default: `Ctrl+Shift+C`) to save the position
4. **Configure Settings**:
   - Set the number of clicks (e.g., 10)
   - Set the interval between clicks (e.g., 1.0 seconds)
   - Choose click type (left, right, or double-click)
5. **Start Automation**: Press `F6` (default start hotkey) or click "Start"

### Emergency Stop
- **Hotkey**: Press `F7` (default stop hotkey)
- **GUI**: Click the "Stop" button
- **Mouse**: Move mouse to any corner of the screen (safety feature)

## ⚙️ Basic Configuration

### Setting Up Hotkeys
1. Open the **Settings** menu
2. Navigate to **Hotkeys** tab
3. Customize your preferred key combinations:
   - Start/Stop automation
   - Position capture
   - Emergency stop

### Creating Your First Profile
1. Configure your automation settings
2. Click **File** > **Save Profile**
3. Name your profile (e.g., "Gaming Clicks")
4. Your settings are now saved for future use

## 🖥️ Interface Overview

### Main Window
- **Control Panel**: Start/stop buttons and status indicators
- **Position Display**: Shows current click coordinates
- **Settings Panel**: Quick access to common options
- **Status Bar**: Real-time automation status

### System Tray
- **Right-click** the tray icon for quick controls
- **Double-click** to show/hide the main window
- **Green icon**: Idle state
- **Red icon**: Active automation

## 🔧 Common Use Cases

### Gaming Automation
Perfect for:
- Idle games requiring periodic clicking
- Resource collection in strategy games
- Training repetitive actions

### Productivity Tasks
Ideal for:
- Data entry automation
- Repetitive form filling
- Testing user interfaces

### Development Testing
Great for:
- UI stress testing
- Button interaction testing
- Performance testing scenarios

## 🛡️ Safety Features

### Built-in Safeguards
- **Emergency Stop**: Multiple ways to stop automation instantly
- **Safe Mode**: Prevents accidental system damage
- **Position Validation**: Confirms click targets before automation
- **Resource Monitoring**: Automatic cleanup and resource management

### Best Practices
1. **Always test** with a few clicks before running long automations
2. **Use profiles** to save and organize different automation setups  
3. **Set reasonable intervals** to avoid overwhelming target applications
4. **Enable emergency stops** and familiarize yourself with stop methods
5. **Monitor resource usage** during long automation sessions

## 🆘 Quick Troubleshooting

### Common Issues

**Application won't start**
- Verify Python 3.11+ is installed
- Check all dependencies are installed: `pip install -r requirements.txt`
- Run as administrator if needed

**Clicks not registering**
- Verify target application is active and visible
- Check if click position is accurate
- Ensure target application isn't blocking automated input

**Hotkeys not working**
- Check for hotkey conflicts with other applications
- Run Clicker as administrator for global hotkey access
- Verify hotkey settings in the configuration

## 📚 Next Steps

Now that you're up and running:

1. **Explore Advanced Features**: Check out the [Configuration Guide](configuration.md) for advanced settings
2. **Learn Hotkeys**: Master all shortcuts with the [Hotkey Reference](hotkeys.md)  
3. **Customize**: Create custom profiles and automation sequences
4. **Get Help**: Visit the [Troubleshooting Guide](troubleshooting.md) if you encounter issues

## 🤝 Need Help?

- **Documentation**: Comprehensive guides in the `docs/` folder
- **API Reference**: Complete API documentation for advanced users
- **Community**: Join our community for tips and support
- **Issues**: Report bugs or request features on our issue tracker

Welcome to the world of professional automation with Clicker! 🎉 