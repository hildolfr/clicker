"""
GDI-based Visual Indicator.

Uses Windows GDI API to create an overlay that works in fullscreen applications.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import time
import win32gui
import win32con
import win32api

from .base import VisualIndicator, IndicatorState


class GDIIndicator(VisualIndicator):
    """
    GDI-based visual indicator that can overlay on fullscreen applications.
    
    This creates a small overlay window using Windows GDI API that can
    be displayed on top of fullscreen applications.
    """
    
    def __init__(self, width: int = 30, height: int = 30):
        super().__init__()
        
        # Configuration
        self.width = width
        self.height = height
        self.flash_state = False
        self.last_update_time = 0
        self.last_activity_time = time.time()
        self.fade_start_delay = 1.0  # Start fading after 1 second of inactivity
        self.fade_duration = 1.5     # Complete fade over 1.5 seconds
        self.alpha = 204             # Initial alpha (80% of 255)
        self.min_alpha = 0           # Fade completely away
        self.is_fading = False
        
        # Window handles
        self.hwnd = None
        self.hdc = None
        
        # Position in bottom-right of primary screen
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        self.position_x = screen_width - self.width - 20
        self.position_y = screen_height - self.height - 20
    
    def _initialize(self) -> bool:
        """Initialize the GDI overlay window."""
        try:
            self._create_overlay_window()
            return True
        except Exception as e:
            self._logger.error(f"Failed to initialize GDI window: {e}")
            return False
    
    def _cleanup(self) -> None:
        """Clean up GDI resources."""
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
            self._logger.error(f"Error cleaning up GDI window: {e}")
    
    def _create_overlay_window(self) -> None:
        """Create a layered window that can overlay on fullscreen applications."""
        try:
            # Define window class name
            class_name = "ClickerGDIOverlay"
            
            # Register window class
            wc = win32gui.WNDCLASS()
            wc.lpszClassName = class_name
            wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
            wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
            hinst = win32api.GetModuleHandle(None)
            wc.hInstance = hinst
            wc.hbrBackground = win32con.COLOR_WINDOW + 1
            wc.lpfnWndProc = self._wnd_proc
            
            try:
                self.atom = win32gui.RegisterClass(wc)
                self._logger.debug(f"Registered window class: {class_name}")
            except Exception:
                # Class may already exist
                pass
            
            # Create window (layered, topmost, with no visible frame)
            style = win32con.WS_POPUP
            
            # Important: Use WS_EX_NOACTIVATE to prevent the window from stealing focus
            # and WS_EX_TRANSPARENT to allow mouse events to pass through
            ex_style = (win32con.WS_EX_LAYERED | 
                       win32con.WS_EX_TOPMOST | 
                       win32con.WS_EX_TRANSPARENT | 
                       win32con.WS_EX_TOOLWINDOW |
                       win32con.WS_EX_NOACTIVATE)
            
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
                raise Exception("Failed to create window")
            
            # Make it transparent
            win32gui.SetLayeredWindowAttributes(
                self.hwnd, 0, self.alpha, win32con.LWA_ALPHA
            )
            
            # Make window click-through by setting the extended transparency style
            current_ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(
                self.hwnd, 
                win32con.GWL_EXSTYLE, 
                current_ex_style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE
            )
            
            # Show the window without activating it
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNA)
            
            # Store handle to device context
            self.hdc = win32gui.GetDC(self.hwnd)
            
            self._logger.info(f"Created overlay window at position ({self.position_x}, {self.position_y})")
            
        except Exception as e:
            self._logger.error(f"Error creating overlay window: {e}")
            raise
    
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
    
    def _draw(self, hdc) -> None:
        """Direct drawing to the window during WM_PAINT."""
        try:
            # Get client rect
            rect = win32gui.GetClientRect(self.hwnd)
            
            if self._state == IndicatorState.ACTIVE:
                # Draw bright red rectangle when active
                rect_color = win32api.RGB(255, 50, 50) if self.flash_state else win32api.RGB(220, 30, 30)
                brush = win32gui.CreateSolidBrush(rect_color)
                win32gui.FillRect(hdc, rect, brush)
                win32gui.DeleteObject(brush)
            elif self._state == IndicatorState.INACTIVE:
                # Draw gray rectangle when inactive
                brush = win32gui.CreateSolidBrush(win32api.RGB(100, 100, 100))
                win32gui.FillRect(hdc, rect, brush)
                win32gui.DeleteObject(brush)
            else:  # HIDDEN or ERROR
                # Draw nothing (transparent)
                brush = win32gui.CreateSolidBrush(win32api.RGB(0, 0, 0))
                win32gui.FillRect(hdc, rect, brush)
                win32gui.DeleteObject(brush)
                
        except Exception as e:
            self._logger.error(f"Error in _draw: {e}")
    
    def _render_loop(self) -> None:
        """Main rendering loop for the indicator."""
        try:
            last_render_time = time.time()
            
            while self._running and not self._shutdown_event.is_set():
                # Check if window is still valid
                if not self.hwnd or not win32gui.IsWindow(self.hwnd):
                    self._logger.warning("Window no longer valid, exiting render loop")
                    break
                
                current_time = time.time()
                
                # Process Windows messages
                try:
                    user32 = ctypes.windll.user32
                    msg = wintypes.MSG()
                    # Process all waiting messages
                    while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, win32con.PM_REMOVE):
                        # Skip mouse/keyboard messages to prevent interference
                        if not ((msg.message >= win32con.WM_MOUSEFIRST and msg.message <= win32con.WM_MOUSELAST) or 
                                (msg.message >= win32con.WM_KEYFIRST and msg.message <= win32con.WM_KEYLAST)):
                            user32.TranslateMessage(ctypes.byref(msg))
                            user32.DispatchMessageW(ctypes.byref(msg))
                except Exception as e:
                    self._logger.error(f"Error in message pump: {e}")
                
                # Only update visuals at most 16 times per second (62.5ms)
                if current_time - last_render_time < 0.0625:
                    # Check for exit signal
                    if self._shutdown_event.wait(0.01):
                        break
                    continue
                
                last_render_time = current_time
                
                # Update flash state every 500ms when active
                state_changed = False
                if self._state == IndicatorState.ACTIVE:
                    if current_time - self.last_update_time > 0.5:  # 500ms
                        self.flash_state = not self.flash_state
                        self.last_update_time = current_time
                        state_changed = True
                
                # Handle fade effect when not active
                if self._state != IndicatorState.ACTIVE:
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
                if self._shutdown_event.wait(0.02):
                    break
        
        except Exception as e:
            self._logger.error(f"Error in GDI render loop: {e}")
        finally:
            self._logger.debug("GDI render loop exiting")
    
    def _update_visual_state(self, new_state: IndicatorState) -> None:
        """Update the visual representation of the state."""
        if not self.hwnd or not win32gui.IsWindow(self.hwnd):
            return
        
        # Reset fade effect and restore full visibility when activated
        if new_state == IndicatorState.ACTIVE:
            self.alpha = 204  # Reset to full visibility
            win32gui.SetLayeredWindowAttributes(self.hwnd, 0, self.alpha, win32con.LWA_ALPHA)
        
        self.is_fading = False
        self.last_activity_time = time.time()
        
        # Force window redraw
        win32gui.InvalidateRect(self.hwnd, None, True)
        win32gui.UpdateWindow(self.hwnd)
    
    def hide_window(self) -> None:
        """Hide the indicator window."""
        if self.hwnd and win32gui.IsWindow(self.hwnd):
            win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
            self._logger.debug("GDI indicator window hidden")
    
    def show_window(self) -> None:
        """Show the indicator window."""
        if self.hwnd and win32gui.IsWindow(self.hwnd):
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNA)
            self._logger.debug("GDI indicator window shown") 