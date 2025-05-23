"""
Base Visual Indicator Interface.

Defines the common interface for all visual indicators.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional
import threading


class IndicatorState(Enum):
    """States for visual indicators."""
    
    HIDDEN = auto()
    INACTIVE = auto()
    ACTIVE = auto()
    ERROR = auto()


class VisualIndicator(ABC):
    """
    Abstract base class for visual indicators.
    
    This defines the interface that all visual indicators must implement,
    allowing for different indicator types (pygame, GDI, etc.) with a 
    consistent API.
    """
    
    def __init__(self):
        self._state = IndicatorState.HIDDEN
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._logger = logging.getLogger(self.__class__.__name__)
        
    @property
    def state(self) -> IndicatorState:
        """Get the current indicator state."""
        return self._state
        
    @property
    def is_running(self) -> bool:
        """Check if the indicator is running."""
        return self._running
    
    @abstractmethod
    def _initialize(self) -> bool:
        """
        Initialize the indicator-specific resources.
        
        Returns:
            True if initialization succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def _cleanup(self) -> None:
        """Clean up indicator-specific resources."""
        pass
    
    @abstractmethod
    def _render_loop(self) -> None:
        """Main rendering loop - runs in separate thread."""
        pass
    
    @abstractmethod
    def _update_visual_state(self, new_state: IndicatorState) -> None:
        """Update the visual representation of the state."""
        pass
    
    def start(self) -> bool:
        """
        Start the visual indicator.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            self._logger.warning("Indicator already running")
            return True
            
        try:
            self._logger.info("Starting visual indicator")
            
            # Initialize indicator-specific resources
            if not self._initialize():
                self._logger.error("Failed to initialize indicator")
                return False
            
            # Start the rendering thread
            self._shutdown_event.clear()
            self._running = True
            
            self._thread = threading.Thread(
                target=self._safe_render_loop,
                name=f"{self.__class__.__name__}Thread",
                daemon=True
            )
            self._thread.start()
            
            # Set initial state
            self.set_state(IndicatorState.INACTIVE)
            
            self._logger.info("Visual indicator started successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to start indicator: {e}")
            self._running = False
            return False
    
    def stop(self) -> None:
        """Stop the visual indicator."""
        if not self._running:
            return
            
        self._logger.info("Stopping visual indicator")
        
        # Signal shutdown
        self._running = False
        self._shutdown_event.set()
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self._logger.warning("Indicator thread did not stop in time")
        
        # Clean up resources
        try:
            self._cleanup()
        except Exception as e:
            self._logger.error(f"Error during cleanup: {e}")
        
        self._state = IndicatorState.HIDDEN
        self._logger.info("Visual indicator stopped")
    
    def set_state(self, state: IndicatorState) -> None:
        """
        Set the indicator state.
        
        Args:
            state: New state to set
        """
        if self._state != state:
            old_state = self._state
            self._state = state
            
            self._logger.debug(f"State changed: {old_state.name} -> {state.name}")
            
            try:
                self._update_visual_state(state)
            except Exception as e:
                self._logger.error(f"Error updating visual state: {e}")
    
    def set_active(self, active: bool) -> None:
        """
        Convenience method to set active/inactive state.
        
        Args:
            active: True for active, False for inactive
        """
        if active:
            self.set_state(IndicatorState.ACTIVE)
        else:
            self.set_state(IndicatorState.INACTIVE)
    
    def hide(self) -> None:
        """Hide the indicator."""
        self.set_state(IndicatorState.HIDDEN)
    
    def show(self) -> None:
        """Show the indicator (as inactive)."""
        self.set_state(IndicatorState.INACTIVE)
    
    def _safe_render_loop(self) -> None:
        """Safe wrapper around the render loop."""
        try:
            self._render_loop()
        except Exception as e:
            self._logger.error(f"Error in render loop: {e}")
        finally:
            self._logger.debug("Render loop exiting")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop() 