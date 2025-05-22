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
import pygame  # Added pygame for visual indicator
import win32api
import win32ui

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

# Pygame Visual Indicator
class PygameIndicator:
    """Visual indicator using Pygame to show automation status."""
    def __init__(self):
        # Position window in the middle-right of the screen (must be set before pygame.init())
        screen_width, screen_height = pyautogui.size()
        self.width, self.height = 150, 50
        position_x = screen_width - self.width - 20
        position_y = (screen_height // 2) - (self.height // 2)  # Center vertically
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{position_x},{position_y}"
        
        # Initialize pygame
        pygame.init()
        
        # Create a small transparent window
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
        pygame.display.set_caption('Clicker Status')
        
        # Make window always on top and semi-transparent
        hwnd = pygame.display.get_wm_info()['window']
        
        # Set window style: layered, topmost, and transparent to mouse clicks
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
        
        # Set window position to ensure it's in the right location
        win32gui.SetWindowPos(
            hwnd, 
            win32con.HWND_TOPMOST,
            position_x, position_y, 
            self.width, self.height, 
            win32con.SWP_SHOWWINDOW
        )
        
        # Set window transparency (initially 80% opaque)
        self.hwnd = hwnd
        self.alpha = 204  # Initial alpha (80% of 255)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, self.alpha, win32con.LWA_ALPHA)
        
        # Initialize font
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 14)
        if not self.font:
            # Fallback to default font if Arial is not available
            self.font = pygame.font.Font(None, 14)
        
        self.active = False
        self.running = True
        self.thread = None
        self.update_timer = 0
        self.flash_state = False
        
        # Fade effect variables
        self.last_activity_time = pygame.time.get_ticks()
        self.fade_start_delay = 3000  # Start fading after 3 seconds of no activity
        self.fade_duration = 2000     # Complete fade over 2 seconds
        self.min_alpha = 51           # Minimum alpha (20% visibility)
        self.is_fading = False
        
    def start(self):
        """Start the indicator thread."""
        self.running = True
        self.thread = threading.Thread(target=self._render_loop)
        self.thread.daemon = True
        self.thread.start()
        logging.info("Pygame visual indicator started")
        
    def stop(self):
        """Stop the indicator thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)
        pygame.quit()
        logging.info("Pygame visual indicator stopped")
        
    def set_state(self, active):
        """Set the indicator's active state."""
        # Reset fade effect and restore full visibility when state changes
        if self.active != active:
            self.alpha = 204  # Reset to full visibility
            win32gui.SetLayeredWindowAttributes(self.hwnd, 0, self.alpha, win32con.LWA_ALPHA)
            self.is_fading = False
            self.last_activity_time = pygame.time.get_ticks()
        
        self.active = active
        
    def _render_loop(self):
        """Main rendering loop for the indicator."""
        clock = pygame.time.Clock()
        
        try:
            while self.running:
                current_time = pygame.time.get_ticks()
                
                # Handle events to prevent window from becoming unresponsive
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                
                # Clear screen with a base color
                bg_color = (30, 30, 30)  # Dark gray background
                self.screen.fill(bg_color)
                
                # Update flash state every 500ms when active
                if self.active and current_time - self.update_timer > 500:
                    self.flash_state = not self.flash_state
                    self.update_timer = current_time
                    # Reset fade timer when flashing
                    self.last_activity_time = current_time
                    self.is_fading = False
                    self.alpha = 204  # Reset to full visibility
                
                # Handle fade effect when not active or after period of inactivity
                if not self.active and current_time - self.last_activity_time > self.fade_start_delay:
                    if not self.is_fading:
                        self.is_fading = True
                        self.fade_start_time = current_time
                    
                    # Calculate fade progress
                    fade_progress = min(1.0, (current_time - self.fade_start_time) / self.fade_duration)
                    # Linear interpolation from full alpha to min_alpha
                    self.alpha = int(204 - (204 - self.min_alpha) * fade_progress)
                    
                    # Apply new alpha
                    win32gui.SetLayeredWindowAttributes(self.hwnd, 0, self.alpha, win32con.LWA_ALPHA)
                
                # Draw status indicator
                if self.active:
                    # Draw flashing green indicator when active
                    indicator_color = (0, 255, 0) if self.flash_state else (0, 200, 0)
                    pygame.draw.circle(self.screen, indicator_color, (30, self.height // 2), 15)
                    
                    # Draw "AUTOMATION ON" text
                    text = self.font.render("AUTOMATION ON", True, (255, 255, 255))
                    self.screen.blit(text, (55, self.height // 2 - 7))
                else:
                    # Draw gray indicator when inactive
                    pygame.draw.circle(self.screen, (100, 100, 100), (30, self.height // 2), 15)
                    
                    # Draw "AUTOMATION OFF" text
                    text = self.font.render("AUTOMATION OFF", True, (200, 200, 200))
                    self.screen.blit(text, (55, self.height // 2 - 7))
                
                # Update display
                pygame.display.flip()
                
                # Cap at 30 FPS to save CPU
                clock.tick(30)
        except Exception as e:
            logging.error(f"Error in pygame render loop: {e}")
            logging.error(traceback.format_exc())

# GDI-based Indicator for Fullscreen Games
class GDIIndicator:
    """GDI-based visual indicator that can overlay on fullscreen applications."""
    def __init__(self):
        # Configuration
        self.width = 30  # Smaller width for simple rectangle
        self.height = 30  # Square shape
        self.active = False
        self.running = True
        self.thread = None
        self.flash_state = False
        self.last_update_time = 0
        self.last_activity_time = time.time()
        self.fade_start_delay = 1.0  # Start fading after 1 second of inactivity
        self.fade_duration = 1.5     # Complete fade over 1.5 seconds
        self.alpha = 204             # Initial alpha (80% of 255)
        self.min_alpha = 0           # Fade completely away
        self.is_fading = False
        self.hwnd = None
        self.hdc = None
        self.hidden_for_menu = False  # Track if we've hidden the window for menu interaction
        
        # Position in bottom-right of primary screen
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        self.position_x = screen_width - self.width - 20
        self.position_y = screen_height - self.height - 20
        
        # Thread synchronization
        self.exit_event = threading.Event()
        
        # Create an overlay window
        self._create_overlay_window()
        logging.info("GDI indicator initialized")
    
    def _create_overlay_window(self):
        """Create a layered window that can overlay on fullscreen applications."""
        try:
            # Define window class name
            class_name = "ClickerGDIOverlay"
            
            # First check if the class is already registered
            try:
                wndclass = win32gui.GetClassInfo(0, class_name)
                # Class exists, use existing
                logging.info("Using existing window class")
            except:
                # Class doesn't exist, register it
                wc = win32gui.WNDCLASS()
                wc.lpszClassName = class_name
                wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
                wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
                hinst = win32api.GetModuleHandle(None)
                wc.hInstance = hinst
                wc.hbrBackground = win32con.COLOR_WINDOW + 1
                wc.lpfnWndProc = self._wnd_proc
                
                # Register class
                self.atom = win32gui.RegisterClass(wc)
                logging.info(f"Registered window class: {class_name}")
            
            # Create window (layered, topmost, with no visible frame)
            style = win32con.WS_POPUP
            
            # Important: Use WS_EX_NOACTIVATE to prevent the window from stealing focus
            # and WS_EX_TRANSPARENT to allow mouse events to pass through
            ex_style = (win32con.WS_EX_LAYERED | 
                       win32con.WS_EX_TOPMOST | 
                       win32con.WS_EX_TRANSPARENT | 
                       win32con.WS_EX_TOOLWINDOW |
                       win32con.WS_EX_NOACTIVATE)
            
            hinst = win32api.GetModuleHandle(None)
            self.hwnd = win32gui.CreateWindowEx(
                ex_style,
                class_name,
                "Clicker Indicator",
                style,
                self.position_x, self.position_y,
                self.width, self.height,
                0, 0, hinst, None
            )
            
            if not self.hwnd:
                logging.error("Failed to create window!")
                raise Exception("Failed to create window")
            
            # Make it transparent
            win32gui.SetLayeredWindowAttributes(
                self.hwnd, 0, self.alpha, win32con.LWA_ALPHA
            )
            
            # Make window click-through by setting the extended transparency style
            # This ensures mouse events pass through to windows beneath
            current_ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(
                self.hwnd, 
                win32con.GWL_EXSTYLE, 
                current_ex_style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE
            )
            
            # Show the window without activating it
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNA)
            
            # Store handle to device context (will be released in stop())
            self.hdc = win32gui.GetDC(self.hwnd)
            
            logging.info(f"Created overlay window at position ({self.position_x}, {self.position_y})")
            logging.info(f"Window handle: {self.hwnd}")
        except Exception as e:
            logging.error(f"Error creating overlay window: {e}")
            logging.error(traceback.format_exc())
            raise
    
    def hide_window(self):
        """Hide the indicator window."""
        if self.hwnd and win32gui.IsWindow(self.hwnd):
            win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
            self.hidden_for_menu = True
            logging.debug("GDI indicator hidden for menu interaction")
    
    def show_window(self):
        """Show the indicator window if it was hidden."""
        if self.hwnd and win32gui.IsWindow(self.hwnd) and self.hidden_for_menu:
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNA)
            self.hidden_for_menu = False
            logging.debug("GDI indicator shown after menu interaction")
    
    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure for the overlay window."""
        if msg == win32con.WM_PAINT:
            # Handle paint message
            ps = win32gui.PAINTSTRUCT()
            hdc = win32gui.BeginPaint(hwnd, ps)
            self._draw(hdc)
            win32gui.EndPaint(hwnd, ps)
            return 0
        elif msg == win32con.WM_CLOSE:
            win32gui.DestroyWindow(hwnd)
            return 0
        elif msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        # Make sure we don't process any mouse messages
        elif msg >= win32con.WM_MOUSEFIRST and msg <= win32con.WM_MOUSELAST:
            return 0
        else:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def _draw(self, hdc):
        """Direct drawing to the window during WM_PAINT."""
        # Get client rect
        rect = win32gui.GetClientRect(self.hwnd)
        
        if self.active:
            # Draw bright red rectangle when active
            rect_color = win32api.RGB(255, 50, 50) if self.flash_state else win32api.RGB(220, 30, 30)
            brush = win32gui.CreateSolidBrush(rect_color)
            win32gui.FillRect(hdc, rect, brush)
            win32gui.DeleteObject(brush)
        else:
            # Draw nothing when inactive (it will fade away)
            # This is just a placeholder for the paint message
            brush = win32gui.CreateSolidBrush(win32api.RGB(0, 0, 0))
            win32gui.FillRect(hdc, rect, brush)
            win32gui.DeleteObject(brush)
        
    def start(self):
        """Start the indicator thread."""
        if self.thread and self.thread.is_alive():
            logging.warning("Indicator thread already running")
            return
            
        self.running = True
        self.exit_event.clear()
        self.thread = threading.Thread(target=self._render_loop, name="GDIIndicatorThread")
        self.thread.daemon = True
        self.thread.start()
        logging.info("GDI visual indicator started")
        
    def stop(self):
        """Stop the indicator thread."""
        logging.debug("Stopping GDI indicator")
        
        # Signal the thread to exit and wait
        self.running = False
        self.exit_event.set()
        
        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=1.0)  # Wait longer to ensure thread exits
                if self.thread.is_alive():
                    logging.warning("GDI indicator thread did not exit in time")
            except Exception as e:
                logging.error(f"Error joining indicator thread: {e}")
        
        # Clean up window resources
        try:
            if self.hwnd and win32gui.IsWindow(self.hwnd):
                # Release device context if we have one
                if self.hdc:
                    win32gui.ReleaseDC(self.hwnd, self.hdc)
                    self.hdc = None
                
                # Destroy window
                win32gui.DestroyWindow(self.hwnd)
                self.hwnd = None
        except Exception as e:
            logging.error(f"Error cleaning up GDI window: {e}")
            
        self.thread = None
        logging.info("GDI visual indicator stopped")
        
    def set_state(self, active):
        """Set the indicator's active state."""
        if not self.hwnd or not win32gui.IsWindow(self.hwnd):
            logging.warning("Cannot set indicator state - window not available")
            return
            
        logging.info(f"Setting GDI indicator state to: {active}")
        
        # Reset fade effect and restore full visibility when activated
        if active:
            self.alpha = 204  # Reset to full visibility
            if self.hwnd and win32gui.IsWindow(self.hwnd):
                win32gui.SetLayeredWindowAttributes(self.hwnd, 0, self.alpha, win32con.LWA_ALPHA)
        
        self.is_fading = False
        self.last_activity_time = time.time()
        self.active = active
        
        # Force window redraw
        if self.hwnd and win32gui.IsWindow(self.hwnd):
            win32gui.InvalidateRect(self.hwnd, None, True)
            win32gui.UpdateWindow(self.hwnd)
        
    def _render_loop(self):
        """Main rendering loop for the indicator."""
        try:
            # Set thread name for easier debugging
            threading.current_thread().name = "GDIIndicatorThread"
            
            last_render_time = time.time()
            
            while self.running:
                # Check if window is still valid
                if not self.hwnd or not win32gui.IsWindow(self.hwnd):
                    logging.warning("Window no longer valid, exiting render loop")
                    break
                    
                current_time = time.time()
                
                # Use a more selective message pump to avoid interfering with Qt
                # Only process paint and system messages, skip input messages
                try:
                    msg = wintypes.MSG()
                    while win32gui.PeekMessage(msg, 0, 0, 0, win32con.PM_REMOVE):
                        # Skip mouse/keyboard messages to prevent interference with Qt
                        if not ((msg.message >= win32con.WM_MOUSEFIRST and msg.message <= win32con.WM_MOUSELAST) or 
                                (msg.message >= win32con.WM_KEYFIRST and msg.message <= win32con.WM_KEYLAST)):
                            win32gui.TranslateMessage(msg)
                            win32gui.DispatchMessage(msg)
                except Exception as e:
                    logging.error(f"Error in message pump: {e}")
                
                # Only update visuals at most 16 times per second (62.5ms)
                if current_time - last_render_time < 0.0625:
                    # Check for exit signal
                    if self.exit_event.wait(0.01):  # Short sleep to not hog CPU
                        break
                    continue
                
                last_render_time = current_time
                
                # Update flash state every 500ms when active
                state_changed = False
                if self.active:
                    if current_time - self.last_update_time > 0.5:  # 500ms
                        self.flash_state = not self.flash_state
                        self.last_update_time = current_time
                        state_changed = True
                
                # Handle fade effect when not active
                if not self.active:
                    if current_time - self.last_activity_time > self.fade_start_delay:
                        if not self.is_fading:
                            self.is_fading = True
                            self.fade_start_time = current_time
                        
                        # Calculate fade progress
                        fade_progress = min(1.0, (current_time - self.fade_start_time) / self.fade_duration)
                        # Linear interpolation from full alpha to min_alpha (zero)
                        new_alpha = int(204 * (1 - fade_progress))
                        
                        # Only update if alpha changed significantly and window still exists
                        if abs(new_alpha - self.alpha) > 4 and win32gui.IsWindow(self.hwnd):
                            self.alpha = new_alpha
                            win32gui.SetLayeredWindowAttributes(self.hwnd, 0, self.alpha, win32con.LWA_ALPHA)
                
                # Force window redraw only if state changed and window still exists
                if state_changed and win32gui.IsWindow(self.hwnd):
                    win32gui.InvalidateRect(self.hwnd, None, True)
                    win32gui.UpdateWindow(self.hwnd)
                
                # Check for exit signal
                if self.exit_event.wait(0.02):  # Wait with timeout to check exit signal
                    break
        
        except Exception as e:
            logging.error(f"Error in GDI render loop: {e}")
            logging.error(traceback.format_exc())
        finally:
            logging.debug("GDI render loop exiting")

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
    
    # Time in seconds to stagger initial keystroke scheduling when automation starts
    # This creates an initial spacing between keystrokes but does not affect subsequent executions
    'start_time_stagger': 0.5,
    
    # When True: execute keystrokes in file order 
    # When False: sort keystrokes by delay (lowest first)
    'order_obeyed': False,
    
    # Visual indicator type: 'pygame' (window-based) or 'gdi' (works in fullscreen)
    'indicator_type': 'gdi',
    
    # Minimum time in seconds between any keystroke executions (global cooldown)
    # This ensures no keys are pressed faster than this value, regardless of their delay settings
    'global_cooldown': 0.1
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
start_time_stagger = DEFAULT_SETTINGS['start_time_stagger']  # Renamed from pause_time
order_obeyed = DEFAULT_SETTINGS['order_obeyed']
indicator_type = DEFAULT_SETTINGS['indicator_type']
global_cooldown = DEFAULT_SETTINGS['global_cooldown']
running_flag = {'active': False}
thread = {'obj': None}
observer = None
hotkey_ref = {'key': None}
lock = threading.Lock()
cleanup_initiated = False  # Flag to prevent double cleanup
shutdown_event = threading.Event()  # Event to signal threads to shut down
pygame_indicator = None  # Visual indicator instance
gdi_indicator = None     # GDI-based indicator instance

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
    
    This function also handles renaming of fields for backward compatibility:
    - 'pause_time' → 'start_time_stagger'
    
    This ensures backward compatibility when new settings are added or renamed in newer versions.
    """
    was_created = ensure_file_exists(SETTINGS_FILE, DEFAULT_SETTINGS)
    needs_update = False
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
        
        # Handle renamed fields
        field_renames = {
            'pause_time': 'start_time_stagger'  # Old field name -> New field name
        }
        
        # Process field renames
        for old_field, new_field in field_renames.items():
            if old_field in data and new_field not in data:
                old_value = data[old_field]
                logging.warning(f"Renaming legacy field '{old_field}' to '{new_field}' with value: {old_value}")
                data[new_field] = old_value
                del data[old_field]
                needs_update = True
        
        # Check for required keys
        for key, default_value in DEFAULT_SETTINGS.items():
            if key not in data:
                logging.warning(f"Missing key '{key}' in settings file, adding default: {default_value}")
                data[key] = default_value
                needs_update = True
        
        # Write updated settings if needed
        if was_created or needs_update:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f, indent=4)
                if needs_update:
                    logging.info("Updated settings.json with renamed/new fields")
                
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

def is_process_running(pid):
    """Check if a process with given PID is still running on Windows."""
    try:
        # Use a more reliable method to check process existence
        import ctypes
        import ctypes.wintypes

        TH32CS_SNAPPROCESS = 0x00000002
        INVALID_HANDLE_VALUE = -1

        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.wintypes.DWORD),
                ("cntUsage", ctypes.wintypes.DWORD),
                ("th32ProcessID", ctypes.wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.wintypes.ULONG)),
                ("th32ModuleID", ctypes.wintypes.DWORD),
                ("cntThreads", ctypes.wintypes.DWORD),
                ("th32ParentProcessID", ctypes.wintypes.DWORD),
                ("pcPriClassBase", ctypes.wintypes.LONG),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("szExeFile", ctypes.c_char * 260)
            ]

        # Create a snapshot of the system processes
        hProcessSnap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hProcessSnap == INVALID_HANDLE_VALUE:
            return False

        pe32 = PROCESSENTRY32()
        pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)

        # Get the first process from the snapshot
        if not ctypes.windll.kernel32.Process32First(hProcessSnap, ctypes.byref(pe32)):
            ctypes.windll.kernel32.CloseHandle(hProcessSnap)
            return False

        # Iterate through all processes
        found = False
        while True:
            if pe32.th32ProcessID == pid:
                found = True
                break
            
            if not ctypes.windll.kernel32.Process32Next(hProcessSnap, ctypes.byref(pe32)):
                break

        # Clean up the snapshot handle
        ctypes.windll.kernel32.CloseHandle(hProcessSnap)
        return found
    except Exception as e:
        logging.error(f"Error checking process existence: {e}")
        logging.error(traceback.format_exc())
        # Fall back to the simpler method if the complex one fails
        try:
            handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return False
        except Exception as e2:
            logging.error(f"Fallback process check also failed: {e2}")
            return False

def check_singleton():
    """Ensure only one instance of the application is running."""
    # Create a unique mutex (named object) first - this is more reliable than file locks
    try:
        mutex_name = "Global\\ClickerSingletonMutex"
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        last_error = ctypes.windll.kernel32.GetLastError()
        
        if last_error == 183:  # ERROR_ALREADY_EXISTS
            logging.warning("Mutex already exists - another instance is running")
            QtWidgets.QMessageBox.critical(None, 'Already running', 'Another instance of Clicker is already running.')
            sys.exit(1)
            
        # Even if we got the mutex, still do the file check as a secondary measure
    except Exception as e:
        logging.error(f"Error creating mutex: {e}")
        # Continue with file-based detection as fallback
    
    if os.path.exists(LOCKFILE):
        try:
            with open(LOCKFILE, 'r') as f:
                content = f.read().strip()
                try:
                    pid = int(content)
                    logging.debug(f"Found lock file with PID: {pid}")
                    
                    # Check if the process is still running using Windows-specific code
                    if is_process_running(pid):
                        logging.warning(f"Process with PID {pid} is still running")
                        QtWidgets.QMessageBox.critical(None, 'Already running', 'Another instance of Clicker is already running.')
                        sys.exit(1)
                    else:
                        logging.info(f"Removing stale lock file for process {pid}")
                        os.remove(LOCKFILE)
                except ValueError:
                    # If PID is not an integer, file is corrupted
                    logging.warning(f"Lock file contains invalid PID: '{content}'")
                    os.remove(LOCKFILE)
        except (IOError, OSError) as e:
            # If we can't read the lock file, remove it
            logging.warning(f"Error reading lock file: {e}")
            try:
                os.remove(LOCKFILE)
            except Exception as e2:
                logging.error(f"Failed to remove invalid lock file: {e2}")
    
    # Write our PID to the lock file
    try:
        with open(LOCKFILE, 'w') as f:
            current_pid = os.getpid()
            f.write(str(current_pid))
            logging.debug(f"Created lock file with PID: {current_pid}")
    except Exception as e:
        logging.error(f"Failed to create lock file: {e}")

def cleanup():
    """Clean up resources on exit."""
    try:
        if os.path.exists(LOCKFILE):
            logging.debug("Cleanup: Removing lockfile")
            os.remove(LOCKFILE)
        
        # Shut down pygame indicator if active
        global pygame_indicator, gdi_indicator
        if pygame_indicator:
            pygame_indicator.stop()
            pygame_indicator = None
            
        # Shut down GDI indicator if active
        if gdi_indicator:
            gdi_indicator.stop()
            gdi_indicator = None
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
    - start_time_stagger: Time to stagger initial keystroke scheduling
    - order_obeyed: Controls execution order (file order vs sorted by delay)
    - indicator_type: Type of visual indicator to use
    - global_cooldown: Minimum time between any keystroke executions
    - Other settings used for UI and notifications
    
    Note: Field renaming (e.g., pause_time → start_time_stagger) is handled in validate_settings_file()
    which should be called before this function to ensure the settings file is properly updated.
    """
    global settings, toggle_key, start_time_stagger, order_obeyed, indicator_type, global_cooldown
    try:
        with lock:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            
            # Load all settings with fallbacks to defaults
            toggle_key = settings.get('toggle_key', DEFAULT_SETTINGS['toggle_key'])
            start_time_stagger = settings.get('start_time_stagger', DEFAULT_SETTINGS['start_time_stagger'])
            order_obeyed = settings.get('order_obeyed', DEFAULT_SETTINGS['order_obeyed'])
            indicator_type = settings.get('indicator_type', DEFAULT_SETTINGS['indicator_type'])
            global_cooldown = settings.get('global_cooldown', DEFAULT_SETTINGS['global_cooldown'])
            
        logging.info(f"Settings loaded: toggle_key={toggle_key}, start_time_stagger={start_time_stagger}, order_obeyed={order_obeyed}, indicator_type={indicator_type}, global_cooldown={global_cooldown}")
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
    
    Timing mechanisms:
    - start_time_stagger: Controls the initial spacing between keystrokes when automation starts
                         (only affects the first execution of each key)
    - global_cooldown: Minimum time between ANY keystroke executions (global rate limiting)
    - per-key delay: Individual delay time for each keystroke specified in keystrokes.txt
                     (controls how often each specific key repeats)
    """
    schedule = []
    last_execution_time = 0  # Track the last time any key was executed
    try:
        with lock:
            now = time.time()
            # Process keystrokes based on order_obeyed setting
            if order_obeyed:
                # Execute in file order (stagger initial firings by start_time_stagger)
                logging.info("Using file order for keystrokes (order_obeyed=True)")
                for idx, (key_str, delay) in enumerate(keystrokes):
                    # Apply staggered start time to space out initial keystrokes
                    initial_time = now + (idx * start_time_stagger)
                    heapq.heappush(schedule, (initial_time, idx, key_str, delay))
                    logging.debug(f"Scheduled keystroke {key_str} to start at {initial_time - now:.2f}s from now")
            else:
                # Execute in order of lowest delay value
                logging.info("Sorting keystrokes by delay value (order_obeyed=False)")
                sorted_keystrokes = sorted(keystrokes, key=lambda x: x[1])
                for idx, (key_str, delay) in enumerate(sorted_keystrokes):
                    # Apply staggered start time to space out initial keystrokes
                    initial_time = now + (idx * start_time_stagger)
                    heapq.heappush(schedule, (initial_time, idx, key_str, delay))
                    logging.debug(f"Scheduled keystroke {key_str} (delay={delay}) to start at {initial_time - now:.2f}s from now")
        
        while not shutdown_event.is_set():
            with lock:
                active = running_flag['active']
            if not active or not schedule:
                break
            
            next_fire, idx, key_str, delay = heapq.heappop(schedule)
            
            # Apply global cooldown if needed
            current_time = time.time()
            cooldown_time = last_execution_time + global_cooldown
            if cooldown_time > current_time and cooldown_time > next_fire:
                # Global cooldown not satisfied yet - this ensures minimum time between ANY keystrokes
                # This takes precedence over the per-key delay from the keystrokes file
                logging.debug(f"Global cooldown enforced for {key_str}, delaying by {cooldown_time - next_fire:.3f}s")
                next_fire = cooldown_time
            
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
                
                # Update last execution time for global cooldown
                last_execution_time = time.time()
            except Exception as e:
                logging.error(f"Error processing keystroke {key_str}: {e}")
            
            with lock:
                # Calculate next execution time based on the key's individual delay
                # This determines how often this specific key will be pressed again
                # Note: The actual execution may still be delayed by global_cooldown if needed
                next_time = time.time() + delay
                heapq.heappush(schedule, (next_time, idx, key_str, delay))
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
    
    # Visual indicator is already updated in start_automation and stop_automation

def start_automation():
    """Start the automation thread with better thread safety."""
    global thread
    
    with lock:
        if running_flag['active']:
            return
        running_flag['active'] = True
    
    # Reset shutdown event
    shutdown_event.clear()
    
    # Update the active indicator
    if pygame_indicator and indicator_type.lower() == 'pygame':
        pygame_indicator.set_state(True)
    elif gdi_indicator:
        gdi_indicator.set_state(True)
    
    # Create and start worker thread
    thread['obj'] = threading.Thread(target=automation_worker)
    thread['obj'].daemon = True
    thread['obj'].start()
    logging.debug("Automation thread started")

def stop_automation():
    """Stop automation with graceful thread shutdown."""
    with lock:
        running_flag['active'] = False
    
    # Update the active indicator
    if pygame_indicator and indicator_type.lower() == 'pygame':
        pygame_indicator.set_state(False)
    elif gdi_indicator:
        gdi_indicator.set_state(False)
    
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
    global cleanup_initiated, app, tray, observer, pygame_indicator, gdi_indicator
    
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
    
    # Stop Pygame indicator if it's running
    if pygame_indicator:
        try:
            logging.debug("Stopping pygame indicator")
            pygame_indicator.stop()
            pygame_indicator = None
        except Exception as e:
            logging.error(f"Error stopping pygame indicator: {e}")
    
    # Stop GDI indicator if it's running
    if gdi_indicator:
        try:
            logging.debug("Stopping GDI indicator")
            gdi_indicator.stop()
            gdi_indicator = None
        except Exception as e:
            logging.error(f"Error stopping GDI indicator: {e}")
    
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
    global app, tray, observer, pygame_indicator, gdi_indicator
    
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
        
        # Initialize pygame indicator here if selected (no overlay issues with dialogs)
        pygame_indicator = None
        gdi_indicator = None
        try:
            if indicator_type.lower() == 'pygame':
                logging.info("Initializing pygame visual indicator")
                pygame_indicator = PygameIndicator()
                pygame_indicator.start()
                logging.info("Pygame indicator initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize pygame indicator: {e}")
            logging.error(traceback.format_exc())
            pygame_indicator = None
            # Show error message to user
            QtWidgets.QMessageBox.warning(
                None, 
                "Visual Indicator Error",
                f"Failed to initialize visual indicator: {e}\n\nThe application will work without a visual indicator."
            )
        
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
        
        # Initialize GDI indicator after first-run dialog is shown
        if indicator_type.lower() != 'pygame' and gdi_indicator is None:
            try:
                logging.info("Initializing GDI visual indicator (fullscreen compatible)")
                gdi_indicator = GDIIndicator()
                gdi_indicator.start()
                logging.info("GDI indicator initialized successfully")
                
                # Connect GDI indicator to menu signals now that it's initialized
                menu.aboutToShow.connect(lambda: gdi_indicator.hide_window() if gdi_indicator else None)
                menu.aboutToHide.connect(lambda: gdi_indicator.show_window() if gdi_indicator else None)
            except Exception as e:
                logging.error(f"Failed to initialize GDI indicator: {e}")
                logging.error(traceback.format_exc())
                gdi_indicator = None
                # Show error message to user
                QtWidgets.QMessageBox.warning(
                    None, 
                    "Visual Indicator Error",
                    f"Failed to initialize visual indicator: {e}\n\nThe application will work without a visual indicator."
                )
        
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