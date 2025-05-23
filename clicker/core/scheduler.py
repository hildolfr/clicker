"""
Keystroke scheduler for managing execution timing.

This module provides scheduling functionality for the automation engine.
"""

from __future__ import annotations

import heapq
import logging
import time
from dataclasses import dataclass
from typing import List, Optional

from clicker.config.models import KeystrokeConfig, AppSettings


@dataclass
class ScheduledKeystroke:
    """A keystroke scheduled for execution."""
    execution_time: float
    keystroke: KeystrokeConfig
    priority: int = 0
    
    def __lt__(self, other: 'ScheduledKeystroke') -> bool:
        """For heap ordering."""
        return self.execution_time < other.execution_time


class KeystrokeScheduler:
    """Manages keystroke scheduling and timing."""
    
    def __init__(self, keystrokes: List[KeystrokeConfig], settings: AppSettings, event_system=None):
        self.keystrokes = keystrokes
        self.settings = settings
        self.event_system = event_system
        self.logger = logging.getLogger(__name__)
        
        # Schedule storage
        self._schedule: List[ScheduledKeystroke] = []
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the scheduler with keystrokes."""
        if self._initialized:
            return
            
        self._build_initial_schedule()
        self._initialized = True
        self.logger.info(f"Scheduler initialized with {len(self._schedule)} keystrokes")
    
    def _build_initial_schedule(self) -> None:
        """Build the initial execution schedule."""
        now = time.time()
        
        for idx, keystroke in enumerate(self.keystrokes):
            if keystroke.enabled:
                # Apply stagger time
                initial_time = now + (idx * self.settings.start_time_stagger)
                scheduled = ScheduledKeystroke(
                    execution_time=initial_time,
                    keystroke=keystroke,
                    priority=keystroke.priority
                )
                heapq.heappush(self._schedule, scheduled)
    
    def get_next_keystroke(self) -> Optional[ScheduledKeystroke]:
        """Get the next keystroke to execute."""
        if not self._schedule:
            return None
            
        return heapq.heappop(self._schedule)
    
    def reschedule_keystroke(self, scheduled_keystroke: ScheduledKeystroke) -> None:
        """Reschedule a keystroke for future execution."""
        # Calculate next execution time
        next_time = time.time() + scheduled_keystroke.keystroke.delay
        
        new_scheduled = ScheduledKeystroke(
            execution_time=next_time,
            keystroke=scheduled_keystroke.keystroke,
            priority=scheduled_keystroke.priority
        )
        
        heapq.heappush(self._schedule, new_scheduled)
    
    async def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self._schedule.clear()
        self._initialized = False
        self.logger.debug("Scheduler shutdown complete") 