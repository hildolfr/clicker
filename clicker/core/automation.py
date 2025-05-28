"""
Modern Automation Engine for the Clicker application.

This module provides a clean, testable automation engine that replaces
the monolithic automation_worker function from the original code.
"""

from __future__ import annotations

import asyncio
import heapq
import logging
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Callable, Protocol, Dict, Any

from clicker.config.models import KeystrokeConfig, AppSettings
from clicker.utils.exceptions import AutomationError


class AutomationState(Enum):
    """States of the automation engine."""
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
    ERROR = auto()


@dataclass
class ExecutionStats:
    """Statistics about automation execution."""
    total_keystrokes: int = 0
    successful_keystrokes: int = 0
    failed_keystrokes: int = 0
    start_time: Optional[float] = None
    last_execution_time: Optional[float] = None
    execution_errors: List[str] = field(default_factory=list)
    current_schedule_size: int = 0
    
    # Error tracking with size limits
    max_errors: int = field(default=500, init=False)
    total_error_count: int = field(default=0, init=False)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_keystrokes == 0:
            return 100.0
        return (self.successful_keystrokes / self.total_keystrokes) * 100.0
    
    @property
    def uptime(self) -> float:
        """Calculate uptime in seconds."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time
    
    def add_error(self, error_msg: str) -> None:
        """Add an error message with size limits and rate limiting to prevent memory leaks."""
        import time
        
        current_time = time.time()
        
        # Error rate limiting: prevent spam by limiting errors per minute
        recent_errors = [err_time for err_time in getattr(self, '_error_timestamps', [])
                        if current_time - err_time < 60]  # Last minute
        
        # Initialize error timestamps if not exists
        if not hasattr(self, '_error_timestamps'):
            self._error_timestamps = []
        
        # Rate limiting: max 30 errors per minute
        if len(recent_errors) >= 30:
            # Skip adding this error, but count it
            self.total_error_count += 1
            # Track rate limited errors
            if not hasattr(self, '_rate_limited_count'):
                self._rate_limited_count = 0
            self._rate_limited_count += 1
            return
        
        # Time-based cleanup: remove errors older than 10 minutes
        if hasattr(self, '_error_timestamps_detailed'):
            cutoff_time = current_time - 600  # 10 minutes
            # Remove old errors and timestamps together
            old_count = len(self.execution_errors)
            self.execution_errors = [
                err for i, err in enumerate(self.execution_errors)
                if i < len(self._error_timestamps_detailed) and 
                self._error_timestamps_detailed[i] > cutoff_time
            ]
            self._error_timestamps_detailed = [
                ts for ts in self._error_timestamps_detailed if ts > cutoff_time
            ]
            cleaned_count = old_count - len(self.execution_errors)
            if cleaned_count > 0:
                pass  # Don't log cleanup to avoid spam
        else:
            self._error_timestamps_detailed = []
        
        # Add the new error
        self.execution_errors.append(error_msg)
        self.total_error_count += 1
        self._error_timestamps.append(current_time)
        self._error_timestamps_detailed.append(current_time)
        
        # Update recent timestamps (keep only last minute)
        self._error_timestamps = recent_errors + [current_time]
        
        # Implement circular buffer - remove oldest errors when limit is reached
        if len(self.execution_errors) > self.max_errors:
            # Remove oldest errors to maintain size limit
            excess_count = len(self.execution_errors) - self.max_errors
            self.execution_errors = self.execution_errors[excess_count:]
            self._error_timestamps_detailed = self._error_timestamps_detailed[excess_count:]
    
    @property
    def error_count_stats(self) -> dict:
        """Get error count statistics with memory usage monitoring."""
        # Calculate estimated memory usage
        error_memory_bytes = sum(len(err.encode('utf-8')) for err in self.execution_errors)
        timestamp_memory_bytes = len(getattr(self, '_error_timestamps_detailed', [])) * 8  # 8 bytes per float
        
        return {
            "current_stored_errors": len(self.execution_errors),
            "total_errors_seen": self.total_error_count,
            "max_error_limit": self.max_errors,
            "errors_dropped": max(0, self.total_error_count - len(self.execution_errors)),
            "memory_usage_bytes": error_memory_bytes + timestamp_memory_bytes,
            "memory_usage_kb": (error_memory_bytes + timestamp_memory_bytes) / 1024,
            "rate_limited_errors": getattr(self, '_rate_limited_count', 0),
            "recent_error_rate": len(getattr(self, '_error_timestamps', [])),  # Errors in last minute
        }
    
    def reset(self) -> None:
        """Reset all statistics including enhanced error tracking."""
        self.total_keystrokes = 0
        self.successful_keystrokes = 0
        self.failed_keystrokes = 0
        self.start_time = None
        self.last_execution_time = None
        self.execution_errors.clear()
        self.total_error_count = 0
        
        # Clear enhanced error tracking attributes
        if hasattr(self, '_error_timestamps'):
            self._error_timestamps.clear()
        if hasattr(self, '_error_timestamps_detailed'):
            self._error_timestamps_detailed.clear()
        if hasattr(self, '_rate_limited_count'):
            self._rate_limited_count = 0


class StateChangeCallback(Protocol):
    """Protocol for state change callbacks."""
    def __call__(self, old_state: AutomationState, new_state: AutomationState) -> None: ...


class AutomationEngine:
    """
    Modern automation engine with clean architecture and proper state management.
    
    Features:
    - Type-safe configuration
    - Proper async/await support
    - Comprehensive error handling
    - Real-time statistics
    - Thread-safe operations
    """
    
    def __init__(self, keystroke_sender):
        """Initialize automation engine."""
        # Dependency injection
        self.keystroke_sender = keystroke_sender
        
        # Internal state
        self._state = AutomationState.STOPPED
        self._state_lock = threading.RLock()  # RLock for nested calls
        self._stats = ExecutionStats()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        
        # Configuration
        self._keystrokes: List[KeystrokeConfig] = []
        self._settings: Optional[AppSettings] = None
        
        # Schedule optimization
        self._cached_schedule: Optional[List[tuple]] = None
        self._schedule_cache_hash: Optional[str] = None
        self._schedule_validation_time: Optional[float] = None
        
        # State callbacks
        self._state_callbacks: List[StateChangeCallback] = []
        
        # Error handling
        self._consecutive_failures = 0
        self._max_consecutive_failures = 10
        self._last_global_execution = 0.0
        
        self.logger = logging.getLogger(__name__)
        
        # Hash optimization - cache timestamps for change detection
        self._config_timestamp = 0.0
        self._last_hash_calculation_time = 0.0
        self._cached_hash: Optional[str] = None
        
    @property
    def state(self) -> AutomationState:
        """Get current automation state."""
        with self._state_lock:
            return self._state
    
    @property
    def stats(self) -> ExecutionStats:
        """Get current execution statistics."""
        return self._stats
    
    @property
    def is_running(self) -> bool:
        """Check if automation is currently running."""
        return self.state == AutomationState.RUNNING
    
    def configure(self, keystrokes: List[KeystrokeConfig], settings: AppSettings) -> None:
        """Configure the automation engine with keystrokes and settings."""
        with self._state_lock:
            # Check if configuration actually changed
            keystrokes_changed = self._keystrokes_changed(keystrokes)
            settings_changed = self._settings_changed(settings)
            
            if keystrokes_changed or settings_changed:
                self._keystrokes = keystrokes[:]  # Create a copy
                self._settings = settings
                
                # Update configuration timestamp for hash optimization
                self._config_timestamp = time.time()
                
                # Invalidate schedule cache since configuration changed
                self._invalidate_schedule_cache()
                
                self.logger.info(f"Engine configured with {len(keystrokes)} keystrokes")
    
    def _keystrokes_changed(self, new_keystrokes: List[KeystrokeConfig]) -> bool:
        """Check if keystrokes have changed significantly enough to invalidate cache."""
        if len(self._keystrokes) != len(new_keystrokes):
            return True
        
        for old, new in zip(self._keystrokes, new_keystrokes):
            if (old.key != new.key or 
                old.delay != new.delay or 
                old.enabled != new.enabled):
                return True
        
        return False

    def _settings_changed(self, new_settings: AppSettings) -> bool:
        """Check if settings have changed in ways that affect scheduling."""
        if self._settings is None:
            return True
        
        # Check settings that affect scheduling
        return (self._settings.start_time_stagger != new_settings.start_time_stagger or
                self._settings.global_cooldown != new_settings.global_cooldown or
                self._settings.order_obeyed != new_settings.order_obeyed)

    def _invalidate_schedule_cache(self) -> None:
        """Invalidate the cached schedule and hash when configuration changes."""
        self._cached_schedule = None
        self._schedule_cache_hash = None
        self._schedule_validation_time = None
        # Also invalidate hash cache for consistency
        self._cached_hash = None
        self._last_hash_calculation_time = 0.0
        self.logger.debug("Schedule cache and hash cache invalidated")

    def _get_schedule_hash(self) -> str:
        """Generate a hash for the current configuration with optimization to detect changes."""
        import hashlib
        
        # Check if we can use cached hash
        if (self._cached_hash is not None and 
            self._last_hash_calculation_time >= self._config_timestamp):
            # Configuration hasn't changed since last hash calculation
            return self._cached_hash
        
        # Performance metrics
        hash_start_time = time.time()
        
        # Create hash of relevant configuration
        config_str = ""
        for ks in self._keystrokes:
            if ks.enabled:
                config_str += f"{ks.key}:{ks.delay}:{ks.enabled}|"
        
        if self._settings:
            config_str += f"stagger:{self._settings.start_time_stagger}|"
            config_str += f"cooldown:{self._settings.global_cooldown}|"
            config_str += f"order_obeyed:{self._settings.order_obeyed}"
        
        # Calculate and cache the hash
        self._cached_hash = hashlib.md5(config_str.encode()).hexdigest()
        self._last_hash_calculation_time = time.time()
        
        # Log performance metrics
        hash_calculation_time = self._last_hash_calculation_time - hash_start_time
        if hash_calculation_time > 0.01:  # Log if hash calculation takes >10ms
            self.logger.debug(f"Schedule hash calculation took {hash_calculation_time:.3f}s")
        
        return self._cached_hash

    def _validate_cached_schedule(self) -> bool:
        """Validate that the cached schedule is still valid."""
        if self._cached_schedule is None:
            return False
        
        current_hash = self._get_schedule_hash()
        if self._schedule_cache_hash != current_hash:
            self.logger.debug("Schedule cache invalidated: configuration changed")
            return False
        
        # Check if cache is too old (1 hour)
        if (self._schedule_validation_time and 
            time.time() - self._schedule_validation_time > 3600):
            self.logger.debug("Schedule cache invalidated: too old")
            return False
        
        return True
    
    def start(self) -> bool:
        """Start automation."""
        try:
            with self._state_lock:
                if self.state != AutomationState.STOPPED:
                    self.logger.warning(f"Cannot start automation from state: {self.state}")
                    return False
                
                if not self._settings or not self._keystrokes:
                    raise AutomationError("Engine not configured")
                
                self._set_state(AutomationState.STARTING)
                
                # Reset statistics
                self._stats.reset()
                self._stats.start_time = time.time()
                self._stop_event.clear()
                self._consecutive_failures = 0
                
                # Start execution in background thread (within lock to prevent race conditions)
                self._worker_thread = threading.Thread(
                    target=self._execution_worker,
                    name="AutomationWorker",
                    daemon=True
                )
                self._worker_thread.start()
                
                # Wait briefly to ensure thread actually started
                start_timeout = 2.0  # 2 second timeout
                start_time = time.time()
                
                while (time.time() - start_time) < start_timeout:
                    if self._worker_thread.is_alive():
                        self._set_state(AutomationState.RUNNING)
                        self.logger.info("Automation started successfully")
                        return True
                    time.sleep(0.01)  # Small sleep to prevent busy waiting
                
                # If we get here, thread failed to start within timeout
                self.logger.error("Worker thread failed to start within timeout")
                self._set_state(AutomationState.ERROR)
                return False
                    
        except Exception as e:
            self.logger.error(f"Failed to start automation: {e}")
            with self._state_lock:
                self._set_state(AutomationState.ERROR)
            return False
    
    def stop(self, timeout: float = 5.0) -> bool:
        """Stop automation gracefully."""
        try:
            with self._state_lock:
                if self.state == AutomationState.STOPPED:
                    return True
                
                if self.state != AutomationState.RUNNING:
                    self.logger.warning(f"Cannot stop automation from state: {self.state}")
                    return False
                
                self._set_state(AutomationState.STOPPING)
            
            # Signal worker to stop
            self._stop_event.set()
            
            # Wait for worker thread to finish
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=timeout)
                
                if self._worker_thread.is_alive():
                    self.logger.error("Worker thread did not stop within timeout")
                    return False
            
            with self._state_lock:
                self._set_state(AutomationState.STOPPED)
            
            self.logger.info("Automation stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping automation: {e}")
            with self._state_lock:
                self._set_state(AutomationState.ERROR)
            return False
    
    def register_state_callback(self, callback: StateChangeCallback) -> None:
        """Register a callback for state changes."""
        self._state_callbacks.append(callback)
    
    def _set_state(self, new_state: AutomationState) -> None:
        """Set new state and notify callbacks."""
        old_state = self._state
        self._state = new_state
        
        if old_state != new_state:
            self.logger.debug(f"State changed: {old_state.name} -> {new_state.name}")
            
            # Notify callbacks
            for callback in self._state_callbacks:
                try:
                    callback(old_state, new_state)
                except Exception as e:
                    self.logger.error(f"Error in state callback: {e}")
    
    def _execution_worker(self) -> None:
        """Main execution worker thread with memory leak prevention."""
        try:
            self.logger.debug("Automation worker thread started")
            
            # Build schedule using heap for efficient scheduling
            schedule = self._build_schedule_heap()
            schedule_size_limit = 1000  # Prevent memory leak
            
            while not self._stop_event.is_set() and self.state == AutomationState.RUNNING:
                if not schedule:
                    break
                
                # Get next keystroke (heap automatically maintains order)
                next_fire, keystroke = heapq.heappop(schedule)
                
                # Wait until it's time to execute
                wait_time = max(0, next_fire - time.time())
                if wait_time > 0:
                    if self._stop_event.wait(timeout=wait_time):
                        break  # Stop event was set
                
                # Apply global cooldown
                global_cooldown_time = self._last_global_execution + self._settings.global_cooldown
                current_time = time.time()
                
                if global_cooldown_time > current_time:
                    additional_wait = global_cooldown_time - current_time
                    if self._stop_event.wait(timeout=additional_wait):
                        break
                
                # Execute the keystroke
                success = self._execute_keystroke(keystroke)
                
                if success:
                    self._consecutive_failures = 0
                    self._last_global_execution = time.time()
                else:
                    self._consecutive_failures += 1
                    
                    # Check if we've exceeded failure limit
                    if self._consecutive_failures >= self._max_consecutive_failures:
                        self.logger.error(f"Too many consecutive failures, stopping automation")
                        break
                
                # Re-schedule the keystroke for next execution (with size limit)
                if len(schedule) < schedule_size_limit:
                    next_time = time.time() + keystroke.delay
                    heapq.heappush(schedule, (next_time, keystroke))
                else:
                    # Schedule is full, log warning but continue with existing items
                    self.logger.warning(f"Schedule size limit ({schedule_size_limit}) reached, skipping reschedule")
            
        except Exception as e:
            self.logger.error(f"Fatal error in execution worker: {e}")
        finally:
            self.logger.debug("Automation worker thread exiting")
    
    def _build_schedule_heap(self) -> List[tuple]:
        """Build initial execution schedule as a heap with caching for optimization."""
        # Check if we can use cached schedule
        if self._validate_cached_schedule():
            self.logger.debug("Using cached schedule")
            # Return a fresh copy of the cached schedule with updated times
            return self._refresh_schedule_times(self._cached_schedule.copy())
        
        # Build new schedule
        self.logger.debug("Building new schedule")
        schedule = []
        now = time.time()
        
        # Determine keystroke order based on order_obeyed setting
        if self._settings.order_obeyed:
            # Execute in file order (top to bottom)
            self.logger.debug("Using file order for keystrokes (order_obeyed=True)")
            keystrokes_to_schedule = [(idx, ks) for idx, ks in enumerate(self._keystrokes) if ks.enabled]
        else:
            # Sort by delay (lowest to highest), preserving original indices for logging
            self.logger.debug("Sorting keystrokes by delay value (order_obeyed=False)")
            enabled_keystrokes = [(idx, ks) for idx, ks in enumerate(self._keystrokes) if ks.enabled]
            keystrokes_to_schedule = sorted(enabled_keystrokes, key=lambda x: x[1].delay)
            
            # Log the reordering for debugging
            if len(keystrokes_to_schedule) > 1:
                delay_order = [f"{ks.key}({ks.delay}s)" for _, ks in keystrokes_to_schedule]
                self.logger.debug(f"Keystroke execution order by delay: {' -> '.join(delay_order)}")
        
        # Schedule keystrokes with stagger times based on determined order
        for schedule_idx, (original_idx, keystroke) in enumerate(keystrokes_to_schedule):
            initial_time = now + (schedule_idx * self._settings.start_time_stagger)
            heapq.heappush(schedule, (initial_time, keystroke))
            self.logger.debug(f"Scheduled keystroke {keystroke.key} (original pos {original_idx}, delay {keystroke.delay}s) "
                            f"to start at {initial_time - now:.2f}s from now")
        
        # Cache the schedule
        self._cached_schedule = [(time_offset, ks) for time_offset, ks in schedule]
        self._schedule_cache_hash = self._get_schedule_hash()
        self._schedule_validation_time = time.time()
        
        execution_order = "file order" if self._settings.order_obeyed else "delay-sorted order"
        self.logger.info(f"Built and cached schedule heap with {len(schedule)} keystrokes in {execution_order}")
        return schedule

    def _refresh_schedule_times(self, schedule: List[tuple]) -> List[tuple]:
        """Refresh the timing in a cached schedule for current execution."""
        now = time.time()
        refreshed_schedule = []
        
        # Extract keystrokes from cached schedule and reapply order_obeyed logic
        cached_keystrokes = [keystroke for _, keystroke in schedule]
        
        # Determine keystroke order based on current order_obeyed setting
        if self._settings.order_obeyed:
            # Maintain original file order - find original indices
            keystroke_order = []
            for keystroke in cached_keystrokes:
                for idx, original_ks in enumerate(self._keystrokes):
                    if original_ks is keystroke:
                        keystroke_order.append((idx, keystroke))
                        break
            keystroke_order.sort(key=lambda x: x[0])  # Sort by original index
        else:
            # Sort by delay (lowest to highest)
            keystroke_order = [(0, ks) for ks in cached_keystrokes]  # Index doesn't matter for delay sort
            keystroke_order.sort(key=lambda x: x[1].delay)
        
        # Apply new timing based on determined order
        for schedule_idx, (_, keystroke) in enumerate(keystroke_order):
            new_time = now + (schedule_idx * self._settings.start_time_stagger)
            refreshed_schedule.append((new_time, keystroke))
        
        # Re-heapify since we changed the times
        heapq.heapify(refreshed_schedule)
        
        execution_order = "file order" if self._settings.order_obeyed else "delay-sorted order"
        self.logger.debug(f"Refreshed {len(refreshed_schedule)} schedule times using {execution_order}")
        return refreshed_schedule
    
    def _execute_keystroke(self, keystroke: KeystrokeConfig) -> bool:
        """Execute a single keystroke."""
        try:
            self.logger.debug(f"Executing keystroke: {keystroke.key}")
            
            # Update statistics
            self._stats.total_keystrokes += 1
            
            # Send the keystroke
            success = self.keystroke_sender.send_keystroke(keystroke.key)
            
            if success:
                self._stats.successful_keystrokes += 1
                self._stats.last_execution_time = time.time()
                self.logger.debug(f"Successfully executed keystroke: {keystroke.key}")
            else:
                self._stats.failed_keystrokes += 1
                error_msg = f"Failed to execute keystroke: {keystroke.key}"
                self._stats.add_error(error_msg)
                self.logger.warning(error_msg)
            
            return success
            
        except Exception as e:
            self._stats.failed_keystrokes += 1
            error_msg = f"Exception executing keystroke {keystroke.key}: {e}"
            self._stats.add_error(error_msg)
            self.logger.error(error_msg)
            return False 