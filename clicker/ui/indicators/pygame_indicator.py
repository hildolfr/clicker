"""
Pygame-based Visual Indicator.

Uses Pygame to create a visual indicator window.
"""

from __future__ import annotations

import os
import time
import threading
from typing import Optional

try:
    import pygame
    import win32gui
    import win32con
    import pyautogui
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from .base import VisualIndicator, IndicatorState


class PygameIndicator(VisualIndicator):
    """
    Pygame-based visual indicator.
    
    Creates a small window using Pygame to show automation status.
    This is an alternative to the GDI indicator that doesn't work
    as well with fullscreen applications but is easier to use.
    """
    
    def __init__(self, width: int = 150, height: int = 50):
        super().__init__()
        
        if not PYGAME_AVAILABLE:
            raise ImportError("Pygame and related dependencies are not available")
        
        # Configuration
        self.width = width
        self.height = height
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.font: Optional[pygame.font.Font] = None
        self.hwnd = None
        
        # Visual state
        self.flash_state = False
        self.update_timer = 0
        self.last_activity_time = time.time()
        self.fade_start_delay = 3.0  # Start fading after 3 seconds of no activity
        self.fade_duration = 2.0     # Complete fade over 2 seconds
        self.alpha = 204             # Initial alpha (80% of 255)
        self.min_alpha = 51          # Minimum alpha (20% visibility)
        self.is_fading = False
        
        # Position window in the middle-right of the screen
        screen_width, screen_height = pyautogui.size()
        position_x = screen_width - self.width - 20
        position_y = (screen_height // 2) - (self.height // 2)  # Center vertically
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{position_x},{position_y}"
    
    def _initialize(self) -> bool:
        """Initialize Pygame and create the window."""
        try:
            # Initialize pygame
            pygame.init()
            
            # Create a small window
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
            pygame.display.set_caption('Clicker Status')
            
            # Make window always on top and semi-transparent
            self.hwnd = pygame.display.get_wm_info()['window']
            
            # Set window style: layered, topmost, and transparent to mouse clicks
            style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style)
            
            # Set window position to ensure it's in the right location
            screen_width, screen_height = pyautogui.size()
            position_x = screen_width - self.width - 20
            position_y = (screen_height // 2) - (self.height // 2)
            
            win32gui.SetWindowPos(
                self.hwnd, 
                win32con.HWND_TOPMOST,
                position_x, position_y, 
                self.width, self.height, 
                win32con.SWP_SHOWWINDOW
            )
            
            # Set window transparency
            win32gui.SetLayeredWindowAttributes(self.hwnd, 0, self.alpha, win32con.LWA_ALPHA)
            
            # Initialize font
            pygame.font.init()
            self.font = pygame.font.SysFont('Arial', 14)
            if not self.font:
                # Fallback to default font if Arial is not available
                self.font = pygame.font.Font(None, 14)
            
            # Initialize clock for FPS control
            self.clock = pygame.time.Clock()
            
            self._logger.info("Pygame indicator initialized successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to initialize pygame indicator: {e}")
            return False
    
    def _cleanup(self) -> None:
        """Clean up Pygame resources."""
        try:
            if pygame.get_init():
                pygame.quit()
            self._logger.debug("Pygame resources cleaned up")
        except Exception as e:
            self._logger.error(f"Error cleaning up pygame: {e}")
    
    def _render_loop(self) -> None:
        """Main rendering loop for the indicator."""
        try:
            while self._running and not self._shutdown_event.is_set():
                current_time = time.time()
                pygame_time = pygame.time.get_ticks()
                
                # Handle events to prevent window from becoming unresponsive
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self._running = False
                        break
                
                if not self._running:
                    break
                
                # Clear screen with a base color
                bg_color = (30, 30, 30)  # Dark gray background
                self.screen.fill(bg_color)
                
                # Update flash state every 500ms when active
                if self._state == IndicatorState.ACTIVE and pygame_time - self.update_timer > 500:
                    self.flash_state = not self.flash_state
                    self.update_timer = pygame_time
                    # Reset fade timer when flashing
                    self.last_activity_time = current_time
                    self.is_fading = False
                    self.alpha = 204  # Reset to full visibility
                
                # Handle fade effect when not active or after period of inactivity
                if self._state != IndicatorState.ACTIVE and current_time - self.last_activity_time > self.fade_start_delay:
                    if not self.is_fading:
                        self.is_fading = True
                        self.fade_start_time = current_time
                    
                    # Calculate fade progress
                    fade_progress = min(1.0, (current_time - self.fade_start_time) / self.fade_duration)
                    # Linear interpolation from full alpha to min_alpha
                    self.alpha = int(204 - (204 - self.min_alpha) * fade_progress)
                    
                    # Apply new alpha
                    if self.hwnd:
                        win32gui.SetLayeredWindowAttributes(self.hwnd, 0, self.alpha, win32con.LWA_ALPHA)
                
                # Draw status indicator based on state
                if self._state == IndicatorState.ACTIVE:
                    # Draw flashing green indicator when active
                    indicator_color = (0, 255, 0) if self.flash_state else (0, 200, 0)
                    pygame.draw.circle(self.screen, indicator_color, (30, self.height // 2), 15)
                    
                    # Draw "AUTOMATION ON" text
                    text = self.font.render("AUTOMATION ON", True, (255, 255, 255))
                    self.screen.blit(text, (55, self.height // 2 - 7))
                    
                elif self._state == IndicatorState.INACTIVE:
                    # Draw gray indicator when inactive
                    pygame.draw.circle(self.screen, (100, 100, 100), (30, self.height // 2), 15)
                    
                    # Draw "AUTOMATION OFF" text
                    text = self.font.render("AUTOMATION OFF", True, (200, 200, 200))
                    self.screen.blit(text, (55, self.height // 2 - 7))
                    
                elif self._state == IndicatorState.ERROR:
                    # Draw red indicator for error
                    pygame.draw.circle(self.screen, (255, 0, 0), (30, self.height // 2), 15)
                    
                    # Draw "ERROR" text
                    text = self.font.render("ERROR", True, (255, 255, 255))
                    self.screen.blit(text, (55, self.height // 2 - 7))
                
                # Update display
                pygame.display.flip()
                
                # Cap at 30 FPS to save CPU
                if self.clock:
                    self.clock.tick(30)
                
                # Check for shutdown
                if self._shutdown_event.wait(0.01):
                    break
                    
        except Exception as e:
            self._logger.error(f"Error in pygame render loop: {e}")
        finally:
            self._logger.debug("Pygame render loop exiting")
    
    def _update_visual_state(self, new_state: IndicatorState) -> None:
        """Update the visual representation of the state."""
        # Reset fade effect and restore full visibility when state changes
        if self._state != new_state:
            self.alpha = 204  # Reset to full visibility
            if self.hwnd:
                win32gui.SetLayeredWindowAttributes(self.hwnd, 0, self.alpha, win32con.LWA_ALPHA)
            self.is_fading = False
            self.last_activity_time = time.time()
            
            self._logger.debug(f"Pygame indicator state updated to: {new_state.name}")
    
    def hide_window(self) -> None:
        """Hide the pygame window."""
        if self.hwnd:
            win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
            self._logger.debug("Pygame indicator window hidden")
    
    def show_window(self) -> None:
        """Show the pygame window."""
        if self.hwnd:
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNA)
            self._logger.debug("Pygame indicator window shown") 