"""
Improved Automation Engine
Replaces the monolithic automation_worker function with a clean, testable class
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Protocol
import threading
import time
import heapq
import logging
from enum import Enum
import random
from contextlib import contextmanager

class AutomationState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"

@dataclass
class ExecutionStats:
    """Statistics about automation execution"""
    total_keystrokes: int = 0
    successful_keystrokes: int = 0
    failed_keystrokes: int = 0
    execution_start_time: Optional[float] = None
    last_execution_time: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_keystrokes == 0:
            return 0.0
        return self.successful_keystrokes / self.total_keystrokes
    
    @property
    def runtime(self) -> float:
        if not self.execution_start_time:
            return 0.0
        end_time = self.last_execution_time or time.time()
        return end_time - self.execution_start_time

@dataclass
class ScheduledKeystroke:
    """A keystroke scheduled for execution"""
    execution_time: float
    keystroke_id: str
    key: str
    delay: float
    priority: int = 0
    
    def __lt__(self, other):
        # For heapq - earlier execution time has higher priority
        return self.execution_time < other.execution_time

class KeystrokeSender(ABC):
    """Abstract interface for sending keystrokes"""
    
    @abstractmethod
    def send_keystroke(self, key: str, modifiers: List[str] = None) -> bool:
        """Send a keystroke with optional modifiers"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the keystroke sender is available"""
        pass

class WindowsApiKeystrokeSender(KeystrokeSender):
    """Windows API-based keystroke sender"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Import your existing Windows API functions here
        
    def send_keystroke(self, key: str, modifiers: List[str] = None) -> bool:
        """Send keystroke using Windows API"""
        try:
            # Use your existing send_key_combination function
            # This would import from your existing code
            return True  # Placeholder
        except Exception as e:
            self.logger.error(f"Failed to send keystroke {key}: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Windows API is available"""
        try:
            import ctypes
            return hasattr(ctypes, 'windll')
        except ImportError:
            return False

class AutomationEngine:
    """Main automation engine with improved architecture"""
    
    def __init__(self, 
                 keystroke_sender: KeystrokeSender,
                 state_callback: Optional[Callable[[AutomationState], None]] = None):
        self.keystroke_sender = keystroke_sender
        self.state_callback = state_callback
        
        # State management
        self._state = AutomationState.STOPPED
        self._execution_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # Configuration
        self.global_cooldown = 1.5
        self.max_execution_time = 3600.0
        self.fail_safe_enabled = True
        
        # Execution data
        self._schedule: List[ScheduledKeystroke] = []
        self._keystrokes_config: List = []  # Will be KeystrokeConfig from config manager
        self._stats = ExecutionStats()
        
        # Thread safety
        self._lock = threading.RLock()
        
        self.logger = logging.getLogger(__name__)
    
    @property
    def state(self) -> AutomationState:
        """Get current automation state"""
        with self._lock:
            return self._state
    
    @property
    def stats(self) -> ExecutionStats:
        """Get execution statistics"""
        with self._lock:
            return self._stats
    
    @property
    def is_running(self) -> bool:
        """Check if automation is currently running"""
        return self._state in [AutomationState.RUNNING, AutomationState.STARTING]
    
    def configure(self, 
                  keystrokes_config: List,
                  global_cooldown: float = 1.5,
                  max_execution_time: float = 3600.0,
                  fail_safe_enabled: bool = True):
        """Configure the automation engine"""
        with self._lock:
            if self.is_running:
                raise RuntimeError("Cannot configure while automation is running")
            
            self._keystrokes_config = keystrokes_config
            self.global_cooldown = global_cooldown
            self.max_execution_time = max_execution_time
            self.fail_safe_enabled = fail_safe_enabled
            
            self.logger.info(f"Configured with {len(keystrokes_config)} keystrokes")
    
    def start(self, order_obeyed: bool = False, start_time_stagger: float = 1.7) -> bool:
        """Start automation"""
        with self._lock:
            if self.is_running:
                self.logger.warning("Automation is already running")
                return False
            
            if not self._keystrokes_config:
                self.logger.error("No keystrokes configured")
                return False
            
            if not self.keystroke_sender.is_available():
                self.logger.error("Keystroke sender is not available")
                return False
            
            # Reset state
            self._stop_event.clear()
            self._pause_event.clear()
            self._stats = ExecutionStats()
            self._stats.execution_start_time = time.time()
            
            # Create initial schedule
            self._create_schedule(order_obeyed, start_time_stagger)
            
            # Change state and start thread
            self._set_state(AutomationState.STARTING)
            
            self._execution_thread = threading.Thread(
                target=self._execution_loop,
                name="AutomationEngine",
                daemon=True
            )
            self._execution_thread.start()
            
            self.logger.info("Automation started")
            return True
    
    def stop(self, timeout: float = 5.0) -> bool:
        """Stop automation"""
        with self._lock:
            if not self.is_running:
                return True
            
            self._set_state(AutomationState.STOPPING)
            self._stop_event.set()
        
        # Wait for thread to finish (outside lock to avoid deadlock)
        if self._execution_thread and self._execution_thread.is_alive():
            self._execution_thread.join(timeout=timeout)
            
            if self._execution_thread.is_alive():
                self.logger.warning("Automation thread did not stop in time")
                return False
        
        with self._lock:
            self._set_state(AutomationState.STOPPED)
            self.logger.info("Automation stopped")
            return True
    
    def pause(self):
        """Pause automation"""
        with self._lock:
            if self._state == AutomationState.RUNNING:
                self._set_state(AutomationState.PAUSED)
                self._pause_event.set()
                self.logger.info("Automation paused")
    
    def resume(self):
        """Resume automation"""
        with self._lock:
            if self._state == AutomationState.PAUSED:
                self._set_state(AutomationState.RUNNING)
                self._pause_event.clear()
                self.logger.info("Automation resumed")
    
    def _set_state(self, new_state: AutomationState):
        """Change state and notify callback"""
        old_state = self._state
        self._state = new_state
        
        if self.state_callback and old_state != new_state:
            try:
                self.state_callback(new_state)
            except Exception as e:
                self.logger.error(f"Error in state callback: {e}")
    
    def _create_schedule(self, order_obeyed: bool, start_time_stagger: float):
        """Create initial execution schedule"""
        self._schedule = []
        now = time.time()
        
        if order_obeyed:
            # Execute in file order with staggered start times
            for idx, keystroke_config in enumerate(self._keystrokes_config):
                execution_time = now + (idx * start_time_stagger)
                scheduled = ScheduledKeystroke(
                    execution_time=execution_time,
                    keystroke_id=f"keystroke_{idx}",
                    key=keystroke_config.key,
                    delay=keystroke_config.delay,
                    priority=idx
                )
                heapq.heappush(self._schedule, scheduled)
        else:
            # Group by delay and randomize within groups
            delay_groups = {}
            for idx, keystroke_config in enumerate(self._keystrokes_config):
                delay = keystroke_config.delay
                if delay not in delay_groups:
                    delay_groups[delay] = []
                delay_groups[delay].append((idx, keystroke_config))
            
            # Schedule by delay order with randomization within groups
            current_offset = 0
            for delay in sorted(delay_groups.keys()):
                group = delay_groups[delay]
                random.shuffle(group)  # Randomize within group
                
                for idx, keystroke_config in group:
                    execution_time = now + (current_offset * start_time_stagger)
                    scheduled = ScheduledKeystroke(
                        execution_time=execution_time,
                        keystroke_id=f"keystroke_{idx}",
                        key=keystroke_config.key,
                        delay=keystroke_config.delay,
                        priority=current_offset
                    )
                    heapq.heappush(self._schedule, scheduled)
                    current_offset += 1
        
        self.logger.info(f"Created schedule with {len(self._schedule)} keystrokes")
    
    def _execution_loop(self):
        """Main execution loop"""
        try:
            self._set_state(AutomationState.RUNNING)
            last_execution_time = 0
            
            while not self._stop_event.is_set():
                # Check for pause
                if self._pause_event.is_set():
                    self._pause_event.wait()
                    continue
                
                # Check maximum execution time
                if (time.time() - self._stats.execution_start_time) > self.max_execution_time:
                    self.logger.warning("Maximum execution time reached")
                    break
                
                # Get next keystroke
                with self._lock:
                    if not self._schedule:
                        self.logger.info("No more keystrokes scheduled")
                        break
                    
                    next_keystroke = heapq.heappop(self._schedule)
                
                # Wait for execution time
                wait_time = next_keystroke.execution_time - time.time()
                if wait_time > 0:
                    if self._stop_event.wait(wait_time):
                        # Stop event was set during wait
                        break
                
                # Apply global cooldown
                current_time = time.time()
                cooldown_time = last_execution_time + self.global_cooldown
                if cooldown_time > current_time:
                    additional_wait = cooldown_time - current_time
                    if self._stop_event.wait(additional_wait):
                        break
                
                # Execute keystroke
                success = self._execute_keystroke(next_keystroke)
                
                # Update statistics
                with self._lock:
                    self._stats.total_keystrokes += 1
                    if success:
                        self._stats.successful_keystrokes += 1
                        last_execution_time = time.time()
                        self._stats.last_execution_time = last_execution_time
                    else:
                        self._stats.failed_keystrokes += 1
                
                # Schedule next execution of this keystroke
                if success:  # Only reschedule if current execution succeeded
                    next_time = time.time() + next_keystroke.delay
                    next_execution = ScheduledKeystroke(
                        execution_time=next_time,
                        keystroke_id=next_keystroke.keystroke_id,
                        key=next_keystroke.key,
                        delay=next_keystroke.delay,
                        priority=next_keystroke.priority
                    )
                    
                    with self._lock:
                        heapq.heappush(self._schedule, next_execution)
                
                # Fail-safe check
                if self.fail_safe_enabled and self._stats.success_rate < 0.5 and self._stats.total_keystrokes > 10:
                    self.logger.error("Too many failed keystrokes, stopping for safety")
                    break
        
        except Exception as e:
            self.logger.error(f"Error in execution loop: {e}")
        
        finally:
            with self._lock:
                self._set_state(AutomationState.STOPPED)
                self.logger.info(f"Execution finished. Stats: {self._stats}")
    
    def _execute_keystroke(self, keystroke: ScheduledKeystroke) -> bool:
        """Execute a single keystroke"""
        try:
            self.logger.debug(f"Executing keystroke: {keystroke.key}")
            
            # Parse modifiers (implement your existing parse_keystroke logic)
            modifiers, key = self._parse_keystroke(keystroke.key)
            
            # Send the keystroke
            success = self.keystroke_sender.send_keystroke(key, modifiers)
            
            if success:
                self.logger.debug(f"Successfully sent keystroke: {keystroke.key}")
            else:
                self.logger.warning(f"Failed to send keystroke: {keystroke.key}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing keystroke {keystroke.key}: {e}")
            return False
    
    def _parse_keystroke(self, key_str: str) -> tuple:
        """Parse keystroke string into modifiers and key"""
        # Implement your existing parse_keystroke logic here
        if '-' not in key_str:
            return [], key_str
        
        parts = key_str.split('-')
        key = parts[-1]
        
        modifier_map = {'S': 'shift', 'C': 'ctrl', 'A': 'alt'}
        modifiers = []
        
        for part in parts[:-1]:
            if part in modifier_map:
                modifiers.append(modifier_map[part])
        
        return modifiers, key

# Usage example:
if __name__ == "__main__":
    # Create keystroke sender
    sender = WindowsApiKeystrokeSender()
    
    # Create automation engine
    def state_changed(new_state):
        print(f"Automation state changed to: {new_state}")
    
    engine = AutomationEngine(sender, state_changed)
    
    # Configure with some test keystrokes
    from types import SimpleNamespace
    test_keystrokes = [
        SimpleNamespace(key="1", delay=2.0),
        SimpleNamespace(key="2", delay=2.0),
        SimpleNamespace(key="3", delay=2.0),
    ]
    
    engine.configure(test_keystrokes, global_cooldown=1.0)
    
    # Start automation
    if engine.start(order_obeyed=True, start_time_stagger=1.0):
        print("Automation started successfully")
        
        # Let it run for a bit
        time.sleep(10)
        
        # Stop automation
        engine.stop()
        print(f"Final stats: {engine.stats}")
    else:
        print("Failed to start automation") 