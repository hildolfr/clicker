import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import os
import json
import time
import threading
import pyautogui
import keyboard
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import heapq
import atexit
import signal
import ctypes
from ctypes import wintypes
import logging
import win32gui
import win32con
import traceback

# Hide console window
if sys.platform == 'win32':
    kernel32 = ctypes.WinDLL('kernel32')
    user32 = ctypes.WinDLL('user32')
    SW_HIDE = 0
    hWnd = kernel32.GetConsoleWindow()
    if hWnd:
        user32.ShowWindow(hWnd, SW_HIDE)

# Set up logging
log_file = 'clicker.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Log startup information
logging.info(f"Starting Clicker application, Python {sys.version}, PyQt5 {QtCore.QT_VERSION_STR}")

# Constants and Paths
SETTINGS_FILE = 'settings.json'
KEYSTROKES_FILE = 'keystrokes.txt'
LOCKFILE = 'clicker.lock'

# Windows API constants
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001
INPUT_KEYBOARD = 1

# Windows API structures
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [
            ("ki", KEYBDINPUT),
            ("padding", ctypes.c_byte * 8)
        ]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT)
    ]

# Virtual key codes
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt key

# Virtual key code mapping
VK_MAP = {
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
    'z': 0x5A,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
    'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
    'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
    'space': 0x20,
    'enter': 0x0D,
    'tab': 0x09,
    'escape': 0x1B,
    'backspace': 0x08,
    'delete': 0x2E,
    'insert': 0x2D,
    'home': 0x24,
    'end': 0x23,
    'pageup': 0x21,
    'pagedown': 0x22,
    'up': 0x26,
    'down': 0x28,
    'left': 0x25,
    'right': 0x27,
}

# Default settings with documentation
DEFAULT_SETTINGS = {
    # Key used as global hotkey to toggle automation on/off
    'toggle_key': '~',
    
    # Time in seconds between initial keystrokes when automation starts
    'pause_time': 0.5,
    
    # When True: execute keystrokes in file order 
    # When False: sort keystrokes by delay (lowest first)
    'order_obeyed': False
}

# Default keystrokes (example)
DEFAULT_KEYSTROKES = [
    "# Clicker Keystrokes Configuration",
    "# ",
    "# Format: [KEY] [DELAY]",
    "#   - KEY: The key to press (can include modifiers)",
    "#     * Use S- for Shift (e.g., S-a for Shift+A)",
    "#     * Use C- for Control (e.g., C-v for Ctrl+V)",
    "#     * Use A- for Alt (e.g., A-f4 for Alt+F4)",
    "#   - DELAY: Time in seconds to wait before pressing this key again",
    "# ",
    "# Note: The order of keys in this file matters if \"order_obeyed\" is set to true",
    "# in settings.json. When order_obeyed is false, keys will be sorted by delay.",
    "#",
    "# Lines starting with # are comments and will be ignored",
    "",
    "1 2.0",
    "2 2.0",
    "3 2.0"
]

# Global state
settings = {}
keystrokes = []
toggle_key = DEFAULT_SETTINGS['toggle_key']
pause_time = DEFAULT_SETTINGS['pause_time']
order_obeyed = DEFAULT_SETTINGS['order_obeyed']
running_flag = {'active': False}
thread = {'obj': None}
observer = None
hotkey_ref = {'key': None}
lock = threading.Lock()
cleanup_initiated = False  # Flag to prevent double cleanup
shutdown_event = threading.Event()  # Event to signal threads to shut down

# --- File validation and creation ---

def ensure_file_exists(filename, default_content=None):
    """Ensure a file exists, creating it with default content if necessary."""
    try:
        if not os.path.exists(filename):
            logging.info(f"Creating missing file: {filename}")
            with open(filename, 'w') as f:
                if default_content is not None:
                    if isinstance(default_content, dict):
                        json.dump(default_content, f, indent=4)
                    elif isinstance(default_content, list):
                        f.write('\n'.join(default_content))
                    else:
                        f.write(str(default_content))
            return True
        return False
    except Exception as e:
        logging.error(f"Error creating file {filename}: {e}")
        return False

def validate_settings_file():
    """Validate and create settings file if needed.
    
    Ensures the settings.json file exists and contains all required keys.
    If missing, the file is created with default values.
    If the file exists but keys are missing, they are added with default values.
    
    This ensures backward compatibility when new settings are added to newer versions.
    """
    was_created = ensure_file_exists(SETTINGS_FILE, DEFAULT_SETTINGS)
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
        
        # Check for required keys
        for key, default_value in DEFAULT_SETTINGS.items():
            if key not in data:
                logging.warning(f"Missing key '{key}' in settings file, adding default: {default_value}")
                data[key] = default_value
                was_created = True
        
        # Write updated settings if needed
        if was_created:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f, indent=4)
                
        return True
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in {SETTINGS_FILE}, recreating with defaults")
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)
        return False
    except Exception as e:
        logging.error(f"Error validating settings file: {e}")
        return False

def validate_keystrokes_file():
    """Validate and create keystrokes file if needed.
    
    Ensures the keystrokes.txt file exists and contains valid keystroke configurations.
    Each line should have a key/key combination and a numeric delay value.
    
    If the file doesn't exist or contains no valid entries, it is created/populated
    with default keystrokes as examples.
    
    The file format is checked line-by-line, with validation errors logged as warnings.
    Lines starting with # are treated as comments and skipped during validation.
    """
    was_created = ensure_file_exists(KEYSTROKES_FILE, DEFAULT_KEYSTROKES)
    
    if was_created:
        logging.info(f"Created {KEYSTROKES_FILE} with example keystrokes")
    
    try:
        with open(KEYSTROKES_FILE, 'r') as f:
            valid_lines = []
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                    
                parts = line.split()
                if len(parts) == 2:
                    key, delay = parts
                    try:
                        float(delay)  # Check if delay is a valid number
                        valid_lines.append(line)
                    except ValueError:
                        logging.warning(f"Invalid delay value at line {line_num}: '{line}'")
                else:
                    logging.warning(f"Invalid keystroke format at line {line_num}: '{line}'")
            
            # If no valid keystrokes, write defaults
            if not valid_lines and not was_created:
                logging.warning(f"No valid keystrokes found, writing defaults to {KEYSTROKES_FILE}")
                with open(KEYSTROKES_FILE, 'w') as f:
                    f.write('\n'.join(DEFAULT_KEYSTROKES))
        
        return True
    except Exception as e:
        logging.error(f"Error validating keystrokes file: {e}")
        return False

# --- Singleton check ---

def check_singleton():
    """Ensure only one instance of the application is running."""
    if os.path.exists(LOCKFILE):
        try:
            with open(LOCKFILE, 'r') as f:
                pid = int(f.read().strip())
            # Check if the process is still running
            try:
                os.kill(pid, 0)
                QtWidgets.QMessageBox.critical(None, 'Already running', 'Another instance of Clicker is already running.')
                logging.warning(f"Attempted to start while another instance (PID: {pid}) is running")
                sys.exit(1)
            except OSError:
                # Process is not running, we can safely remove the lock file
                logging.info(f"Removing stale lock file for process {pid}")
                os.remove(LOCKFILE)
        except (ValueError, IOError) as e:
            # If we can't read the lock file or it's invalid, remove it
            logging.warning(f"Invalid lock file: {e}")
            os.remove(LOCKFILE)
    
    # Write our PID to the lock file
    try:
        with open(LOCKFILE, 'w') as f:
            f.write(str(os.getpid()))
        logging.debug(f"Created lock file with PID: {os.getpid()}")
    except Exception as e:
        logging.error(f"Failed to create lock file: {e}")

def cleanup():
    """Clean up resources on exit."""
    try:
        if os.path.exists(LOCKFILE):
            logging.debug("Cleanup: Removing lockfile")
            os.remove(LOCKFILE)
    except Exception as e:
        logging.error(f"Cleanup error: {e}")

# Register cleanup for normal exit
atexit.register(cleanup)

# Register cleanup for SIGTERM and SIGINT
signal.signal(signal.SIGTERM, lambda signum, frame: (cleanup(), sys.exit(0)))
signal.signal(signal.SIGINT, lambda signum, frame: (cleanup(), sys.exit(0)))

# --- Settings and keystrokes management ---

def load_settings():
    """Load settings from file with better error handling.
    
    Loads:
    - toggle_key: Global hotkey to activate/deactivate automation
    - pause_time: Time between initial keystrokes
    - order_obeyed: Controls execution order (file order vs sorted by delay)
    - Other settings used for UI and notifications
    
    Handles JSON parsing errors and missing keys gracefully.
    """
    global settings, toggle_key, pause_time, order_obeyed
    try:
        with lock:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            toggle_key = settings.get('toggle_key', DEFAULT_SETTINGS['toggle_key'])
            pause_time = settings.get('pause_time', DEFAULT_SETTINGS['pause_time'])
            order_obeyed = settings.get('order_obeyed', DEFAULT_SETTINGS['order_obeyed'])
        logging.info(f"Settings loaded: toggle_key={toggle_key}, pause_time={pause_time}, order_obeyed={order_obeyed}")
        return True
    except json.JSONDecodeError:
        logging.error(f"Error parsing {SETTINGS_FILE} - invalid JSON format")
        return False
    except Exception as e:
        logging.error(f"Error loading settings: {e}")
        return False

def load_keystrokes():
    """Load keystrokes from file with better error handling.
    
    Reads the keystrokes.txt file and parses each line into a (key, delay) tuple.
    Each line should contain a key/key combination and a numeric delay value.
    
    - Key can be a single character or include modifiers (S- for Shift, C- for Ctrl, A- for Alt)
    - Delay is in seconds and must be a valid number
    
    Invalid lines are logged as warnings and skipped. If no valid keystrokes are found,
    a warning is logged but the application will continue to run (though no keys will be pressed).
    """
    global keystrokes
    try:
        with lock:
            keystrokes = []
            with open(KEYSTROKES_FILE, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    # Skip comment lines (starting with #) and empty lines
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    parts = line.split()
                    if len(parts) == 2:
                        key, delay = parts
                        try:
                            delay = float(delay)
                            keystrokes.append((key, delay))
                        except ValueError:
                            logging.warning(f"Invalid delay at line {line_num}: '{delay}' is not a number")
                    else:
                        logging.warning(f"Invalid keystroke format at line {line_num}: '{line}'")
            
            if not keystrokes:
                logging.warning("No valid keystrokes loaded")
            else:
                logging.info(f"Loaded {len(keystrokes)} keystroke configurations")
        return True
    except Exception as e:
        logging.error(f"Error loading keystrokes: {e}")
        return False

# --- Keystroke processing ---

def parse_keystroke(key_str):
    """Parse keystroke string into modifiers and key.
    
    Breaks down a keystroke string into modifier keys and the main key:
    - S- prefix for Shift
    - C- prefix for Control
    - A- prefix for Alt
    
    For example:
    - "a" -> no modifiers, key="a"
    - "S-a" -> modifiers=["shift"], key="a"
    - "C-S-a" -> modifiers=["ctrl", "shift"], key="a"
    
    Returns a tuple of (modifiers_list, key).
    Logs warnings for unknown modifiers.
    """
    parts = key_str.split('-')
    mods = []
    key = parts[-1]
    for p in parts[:-1]:
        if p == 'S':
            mods.append('shift')
        elif p == 'C':
            mods.append('ctrl')
        elif p == 'A':
            mods.append('alt')
        else:
            logging.warning(f"Unknown modifier in keystroke: '{p}'")
    return mods, key

def send_key_event(vk_code, is_key_up=False):
    """Send a key event using Windows API."""
    try:
        flags = KEYEVENTF_KEYUP if is_key_up else 0
        ctypes.windll.user32.keybd_event(
            wintypes.BYTE(vk_code),
            wintypes.BYTE(0),
            wintypes.DWORD(flags),
            wintypes.DWORD(0)
        )
        time.sleep(0.01)
        return True
    except Exception as e:
        logging.error(f"Error in send_key_event: {e}")
        return False

def send_key_combination(modifiers, key):
    """Send a key combination with modifiers."""
    try:
        logging.debug(f"Sending key combination: modifiers={modifiers}, key={key}")
        
        # Get virtual key code
        vk_code = VK_MAP.get(key.lower())
        if vk_code is None:
            logging.error(f"Unknown key '{key}'")
            return False
        
        # Press modifiers
        for mod in modifiers:
            if mod == 'shift':
                if not send_key_event(VK_SHIFT):
                    return False
            elif mod == 'ctrl':
                if not send_key_event(VK_CONTROL):
                    return False
            elif mod == 'alt':
                if not send_key_event(VK_MENU):
                    return False
        
        time.sleep(0.02)
        
        # Press and release the main key
        if not send_key_event(vk_code):
            return False
        time.sleep(0.02)
        if not send_key_event(vk_code, is_key_up=True):
            return False
        
        time.sleep(0.02)
        
        # Release modifiers in reverse order
        for mod in reversed(modifiers):
            if mod == 'shift':
                if not send_key_event(VK_SHIFT, is_key_up=True):
                    return False
            elif mod == 'ctrl':
                if not send_key_event(VK_CONTROL, is_key_up=True):
                    return False
            elif mod == 'alt':
                if not send_key_event(VK_MENU, is_key_up=True):
                    return False
        
        return True
    except Exception as e:
        logging.error(f"Error in send_key_combination: {e}")
        return False

# --- Automation worker ---

def automation_worker():
    """Worker thread for automation.
    
    This function handles the keystroke scheduling and execution:
    - When order_obeyed=True: Executes keystrokes in the exact order from keystrokes.txt
    - When order_obeyed=False: Sorts keystrokes by delay value before execution
    
    Uses a priority queue to manage the execution timing, ensuring keystrokes
    never overlap and maintain their intended timing intervals.
    """
    schedule = []
    try:
        with lock:
            now = time.time()
            # Process keystrokes based on order_obeyed setting
            if order_obeyed:
                # Execute in file order (stagger initial firings by pause_time)
                logging.info("Using file order for keystrokes (order_obeyed=True)")
                for idx, (key_str, delay) in enumerate(keystrokes):
                    initial_time = now + (idx * pause_time)
                    heapq.heappush(schedule, (initial_time, idx, key_str, delay))
                    logging.debug(f"Scheduled keystroke {key_str} to start at {initial_time - now:.2f}s from now")
            else:
                # Execute in order of lowest delay value
                logging.info("Sorting keystrokes by delay value (order_obeyed=False)")
                sorted_keystrokes = sorted(keystrokes, key=lambda x: x[1])
                for idx, (key_str, delay) in enumerate(sorted_keystrokes):
                    initial_time = now + (idx * pause_time)
                    heapq.heappush(schedule, (initial_time, idx, key_str, delay))
                    logging.debug(f"Scheduled keystroke {key_str} (delay={delay}) to start at {initial_time - now:.2f}s from now")
        
        while not shutdown_event.is_set():
            with lock:
                active = running_flag['active']
            if not active or not schedule:
                break
            
            next_fire, idx, key_str, delay = heapq.heappop(schedule)
            wait_time = max(0, next_fire - time.time())
            if wait_time > 0:
                # Use wait with timeout to check shutdown event periodically
                is_shutdown = shutdown_event.wait(min(wait_time, 0.1))
                if is_shutdown:
                    logging.debug("Automation worker received shutdown signal during wait")
                    break
                if next_fire > time.time():
                    # Still need to wait more
                    heapq.heappush(schedule, (next_fire, idx, key_str, delay))
                    continue
            
            with lock:
                if not running_flag['active'] or shutdown_event.is_set():
                    break
            
            mods, key = parse_keystroke(key_str)
            logging.debug(f"Processing keystroke: {key_str} -> mods={mods}, key={key}")
            
            try:
                if mods:
                    send_key_combination(mods, key)
                else:
                    send_key_combination([], key)
            except Exception as e:
                logging.error(f"Error processing keystroke {key_str}: {e}")
            
            with lock:
                heapq.heappush(schedule, (time.time() + delay, idx, key_str, delay))
    except Exception as e:
        logging.error(f"Error in automation worker: {e}")
        logging.error(traceback.format_exc())
    finally:
        logging.debug("Automation worker exiting")

# --- Core application functions ---

def toggle():
    """Toggle automation state."""
    with lock:
        active = running_flag['active']
        
    if active:
        stop_automation()
        tray.setToolTip("Clicker: OFF")
        logging.info("Automation turned OFF")
    else:
        start_automation()
        tray.setToolTip("Clicker: ON")
        logging.info("Automation turned ON")

def start_automation():
    """Start the automation thread with better thread safety."""
    global thread
    
    with lock:
        if running_flag['active']:
            return
        running_flag['active'] = True
    
    # Reset shutdown event
    shutdown_event.clear()
    
    # Create and start worker thread
    thread['obj'] = threading.Thread(target=automation_worker)
    thread['obj'].daemon = True
    thread['obj'].start()
    logging.debug("Automation thread started")

def stop_automation():
    """Stop automation with graceful thread shutdown."""
    with lock:
        running_flag['active'] = False
    
    # Signal worker thread to exit
    shutdown_event.set()
    
    # Wait briefly for thread to exit
    if thread['obj'] is not None and thread['obj'].is_alive():
        logging.debug("Waiting for automation thread to exit")
        thread['obj'].join(timeout=0.5)
        if thread['obj'].is_alive():
            logging.warning("Automation thread did not exit in time")

def rebind_hotkey():
    """Rebind the hotkey with better error handling."""
    global hotkey_ref
    
    # Remove previous hotkey if set
    if hotkey_ref['key'] is not None:
        try:
            keyboard.remove_hotkey(hotkey_ref['key'])
            logging.debug(f"Removed previous hotkey: {toggle_key}")
        except Exception as e:
            logging.error(f"Error removing previous hotkey: {e}")
    
    # Add new hotkey
    try:
        hotkey_ref['key'] = keyboard.add_hotkey(toggle_key, toggle)
        logging.info(f"Hotkey bound to: {toggle_key}")
    except Exception as e:
        logging.error(f"Failed to bind hotkey {toggle_key}: {e}")
        # Try to use default hotkey as fallback
        if toggle_key != DEFAULT_SETTINGS['toggle_key']:
            try:
                toggle_key_backup = DEFAULT_SETTINGS['toggle_key']
                hotkey_ref['key'] = keyboard.add_hotkey(toggle_key_backup, toggle)
                logging.warning(f"Using fallback hotkey: {toggle_key_backup}")
            except Exception as e2:
                logging.error(f"Failed to bind fallback hotkey: {e2}")

def reload_all():
    """Reload settings and keystrokes with validation.
    
    This function is called when configuration files are modified.
    It performs these operations in sequence:
    
    1. Stops any running automation
    2. Validates both settings.json and keystrokes.txt files
    3. Reloads settings, including the order_obeyed preference
    4. Reloads keystroke configurations
    5. Rebinds the global hotkey
    
    This ensures changes to configuration files take effect immediately
    without requiring an application restart.
    """
    logging.info("Reloading all settings and keystrokes")
    
    stop_automation()
    
    # Validate files first
    validate_settings_file()
    validate_keystrokes_file()
    
    # Load settings and keystrokes
    load_settings()
    load_keystrokes()
    
    # Rebind hotkey
    rebind_hotkey()
    
    logging.info("Reload completed")

class FileChangeHandler(FileSystemEventHandler):
    """Handle file changes with better error handling and debouncing."""
    def __init__(self):
        super().__init__()
        self.last_modified = 0
        self.cooldown = 1.0  # 1 second cooldown between reloads
    
    def on_modified(self, event):
        if event.src_path.endswith(SETTINGS_FILE) or event.src_path.endswith(KEYSTROKES_FILE):
            current_time = time.time()
            if current_time - self.last_modified > self.cooldown:
                self.last_modified = current_time
                logging.info(f"Detected change in {os.path.basename(event.src_path)}")
                reload_all()

def cleanup_and_quit():
    """Clean up resources and quit the application."""
    global cleanup_initiated, app, tray, observer
    
    if cleanup_initiated:
        logging.debug("Cleanup already initiated, returning")
        return
    
    cleanup_initiated = True
    logging.info("Starting application cleanup for exit")
    
    # Signal threads to shut down
    shutdown_event.set()
    
    # Stop automation thread
    stop_automation()
    logging.debug("Automation stopped")
    
    # Stop watchdog observer
    if observer:
        try:
            logging.debug("Stopping file observer")
            observer.stop()
            observer.join(timeout=0.5)
            logging.debug("Observer thread joined")
        except Exception as e:
            logging.error(f"Error stopping observer: {e}")
    
    # Remove lockfile
    cleanup()
    logging.info("All resources cleaned up")
    
    # Force exit the application
    logging.info("Exiting application")
    os._exit(0)  # Use force exit to ensure we terminate

def is_admin():
    """Check if the application is running with admin privileges.
    
    Some Windows applications require admin access to receive simulated keystrokes.
    This function checks if the current process has administrator privileges.
    
    Returns:
        bool: True if running as admin, False otherwise
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logging.error(f"Error checking admin status: {e}")
        return False

def show_admin_warning():
    """Show warning about admin privileges with better UI.
    
    This function displays a warning dialog about running without admin privileges
    and offers to restart the application with elevated privileges.
    
    If the user declines, the application continues to run without admin rights.
    If the user accepts but the elevation fails, error handling ensures graceful continuation.
    """
    try:
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setWindowTitle("Administrator Rights Required")
        msg.setText("This application is not running with administrator privileges.")
        msg.setInformativeText("Some applications may not receive keystrokes properly. Would you like to restart with administrator privileges?")
        msg.setDetailedText("When sending keystrokes to applications running with elevated privileges, Clicker needs to run as administrator too. Without admin rights, keystrokes may only work with non-elevated applications.")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
        
        choice = msg.exec_()
        if choice == QtWidgets.QMessageBox.Yes:
            logging.info("User requested restart with admin privileges")
            try:
                # Re-run the program with admin rights
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                # Exit current non-admin instance
                sys.exit(0)
            except Exception as e:
                logging.error(f"Failed to restart with admin privileges: {e}")
                QtWidgets.QMessageBox.critical(None, "Error", 
                    f"Failed to restart with admin privileges: {e}\n\nContinuing without admin privileges.")
                # Continue execution without admin rights
                return False
        else:
            logging.info("User declined to restart with admin privileges")
            # Continue execution without admin rights
            return False
            
        return True
    except Exception as e:
        logging.error(f"Error showing admin warning: {e}")
        return False

def main():
    """Main application entry point with improved error handling and setup.
    
    This is the main function that:
    1. Initializes the Qt application and system tray
    2. Validates and loads configuration files
    3. Sets up hotkeys, file watchers, and event handlers
    4. Checks for admin privileges
    5. Creates the tray menu with various actions
    6. Shows startup help if first run
    7. Handles application exit and cleanup
    
    Uses multiple layers of error handling to ensure graceful behavior
    even when configuration files are invalid or missing.
    """
    global app, tray, observer
    
    try:
        # Create application instance
        app = QtWidgets.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        
        # Validate and create config files if needed
        validate_settings_file()
        validate_keystrokes_file()
        
        # Check for admin rights before proceeding
        if not is_admin():
            # show_admin_warning() returns False if user declines or elevation fails
            # We continue execution either way with appropriate logging
            show_admin_warning()
        
        # Check singleton
        check_singleton()
        
        # Load settings and keystrokes
        load_settings()
        load_keystrokes()
        
        # Create the icon
        if os.path.exists('icon.ico'):
            icon = QtGui.QIcon('icon.ico')
            logging.debug("Using custom icon.ico")
        else:
            icon = QtGui.QIcon()
            icon.addPixmap(app.style().standardPixmap(QtWidgets.QStyle.SP_ComputerIcon))
            logging.debug("Using default computer icon")
        
        # Create the tray
        tray = QtWidgets.QSystemTrayIcon()
        tray.setIcon(icon)
        tray.setVisible(True)
        tray.setToolTip("Clicker: OFF")
        
        # Create the menu
        menu = QtWidgets.QMenu()
        
        # Add status indicator to the menu
        status_action = QtWidgets.QAction("Status: OFF", menu)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        
        # Separator
        menu.addSeparator()
        
        open_keystrokes_action = menu.addAction('Open keystrokes.txt')
        open_settings_action = menu.addAction('Open settings.json')
        reload_action = menu.addAction('Reload settings/keystrokes')
        open_log_action = menu.addAction('View log file')
        
        # Separator
        menu.addSeparator()
        
        quit_action = menu.addAction('Quit')
        
        def open_file(path):
            abs_path = os.path.abspath(path)
            try:
                logging.info(f"Opening file: {abs_path}")
                os.startfile(abs_path)
            except Exception as e:
                logging.error(f"Could not open {abs_path}: {e}")
                QtWidgets.QMessageBox.critical(None, 'Error', f'Could not open {abs_path}: {e}')
        
        # Connect signals to slots
        open_keystrokes_action.triggered.connect(lambda: open_file(KEYSTROKES_FILE))
        open_settings_action.triggered.connect(lambda: open_file(SETTINGS_FILE))
        open_log_action.triggered.connect(lambda: open_file(log_file))
        reload_action.triggered.connect(reload_all)
        quit_action.triggered.connect(cleanup_and_quit)
        
        # Add double-click handler to toggle automation
        tray.activated.connect(lambda reason: toggle() if reason == QtWidgets.QSystemTrayIcon.DoubleClick else None)
        
        # Set context menu
        tray.setContextMenu(menu)
        
        # Update tray status when automation state changes
        def update_tray_status():
            with lock:
                active = running_flag['active']
            status_action.setText(f"Status: {'ON' if active else 'OFF'}")
        
        # Periodically update tray status
        status_timer = QtCore.QTimer()
        status_timer.timeout.connect(update_tray_status)
        status_timer.start(1000)  # Update every second
        
        # Bind hotkey
        rebind_hotkey()
        
        # Watchdog setup for file changes
        event_handler = FileChangeHandler()
        observer = Observer()
        observer.daemon = True
        observer.schedule(event_handler, '.', recursive=False)
        observer.start()
        logging.debug("File change observer started")
        
        # Show startup message if first time or files were created
        if not os.path.exists(".clicker_setup_done"):
            # Show startup help message
            QtWidgets.QMessageBox.information(None, "Clicker Setup",
                "Clicker is now running in the system tray.\n\n"
                f"Press '{toggle_key}' to toggle automation on/off.\n\n"
                "You can also double-click the tray icon.\n\n"
                "Right-click the tray icon for options."
            )
            # Mark setup as done
            with open(".clicker_setup_done", "w") as f:
                f.write("1")
        
        # Log successful startup
        logging.info("Clicker application started successfully")
        
        # Run the application
        sys.exit(app.exec_())
    
    except Exception as e:
        logging.error(f"Unexpected error in main: {e}")
        logging.error(traceback.format_exc())
        try:
            QtWidgets.QMessageBox.critical(None, "Critical Error", 
                f"An unexpected error occurred:\n{e}\n\nCheck the log file for details.")
        except:
            pass
        cleanup()
        sys.exit(1)

if __name__ == '__main__':
    main() 