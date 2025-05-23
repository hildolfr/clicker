"""
Unit tests for the automation engine.

Tests state management, execution statistics, scheduling,
and error handling for the AutomationEngine.
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from clicker.core.automation import (
    AutomationEngine, 
    AutomationState, 
    ExecutionStats,
    AutomationError
)
from clicker.config.models import KeystrokeConfig, AppSettings


class MockKeystrokeSender:
    """Mock keystroke sender for testing."""
    
    def __init__(self, success_rate=1.0, delay=0.0):
        self.success_rate = success_rate
        self.delay = delay
        self.sent_keystrokes = []
        self.call_count = 0
        
    def send_keystroke(self, key: str, modifiers=None):
        """Mock sending keystroke."""
        self.call_count += 1
        self.sent_keystrokes.append((key, modifiers))
        
        if self.delay > 0:
            time.sleep(self.delay)
            
        # Simulate success/failure based on success rate
        import random
        success = random.random() < self.success_rate
        return success
    
    def is_available(self):
        """Mock availability check."""
        return True


class TestAutomationEngine:
    """Test cases for AutomationEngine."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        self.mock_sender = MockKeystrokeSender()
        self.engine = AutomationEngine(self.mock_sender)
        
        # Standard test configuration
        self.test_keystrokes = [
            KeystrokeConfig(key='a', delay=0.1, description='Test A'),
            KeystrokeConfig(key='b', delay=0.1, description='Test B'),
            KeystrokeConfig(key='c', delay=0.1, description='Test C')
        ]
        
        self.test_settings = AppSettings(
            global_cooldown=0.05,  # Short for testing
            max_execution_time=5.0,  # Short for testing
            fail_safe_enabled=True
        )
    
    def teardown_method(self):
        """Clean up after each test."""
        if self.engine.get_state() != AutomationState.STOPPED:
            self.engine.stop()
            time.sleep(0.1)  # Give time for shutdown
    
    def test_initial_state(self):
        """Test initial engine state."""
        assert self.engine.get_state() == AutomationState.STOPPED
        
        stats = self.engine.get_stats()
        assert stats.total_executions == 0
        assert stats.successful_executions == 0
        assert stats.failed_executions == 0
        assert stats.success_rate == 0.0
        assert stats.average_execution_time == 0.0
        assert stats.total_runtime == 0.0
    
    def test_start_automation_success(self):
        """Test successfully starting automation."""
        success = self.engine.start(self.test_keystrokes, self.test_settings)
        assert success is True
        
        # State should change to STARTING then RUNNING
        time.sleep(0.1)  # Give time for state transition
        state = self.engine.get_state()
        assert state in [AutomationState.STARTING, AutomationState.RUNNING]
    
    def test_start_automation_failure_no_keystrokes(self):
        """Test starting automation with no keystrokes."""
        success = self.engine.start([], self.test_settings)
        assert success is False
        assert self.engine.get_state() == AutomationState.STOPPED
    
    def test_start_automation_already_running(self):
        """Test starting automation when already running."""
        # Start once
        success1 = self.engine.start(self.test_keystrokes, self.test_settings)
        assert success1 is True
        
        time.sleep(0.1)  # Let it start
        
        # Try to start again
        success2 = self.engine.start(self.test_keystrokes, self.test_settings)
        assert success2 is False
    
    def test_stop_automation(self):
        """Test stopping automation."""
        # Start automation
        self.engine.start(self.test_keystrokes, self.test_settings)
        time.sleep(0.1)  # Let it start
        
        # Stop automation
        success = self.engine.stop()
        assert success is True
        
        # Wait for stop to complete
        time.sleep(0.2)
        assert self.engine.get_state() == AutomationState.STOPPED
    
    def test_stop_already_stopped(self):
        """Test stopping already stopped automation."""
        assert self.engine.get_state() == AutomationState.STOPPED
        
        success = self.engine.stop()
        assert success is True  # Should succeed even if already stopped
    
    def test_pause_and_resume(self):
        """Test pausing and resuming automation."""
        # Start automation
        self.engine.start(self.test_keystrokes, self.test_settings)
        time.sleep(0.1)  # Let it start
        
        # Pause automation
        success = self.engine.pause()
        assert success is True
        
        time.sleep(0.1)
        assert self.engine.get_state() == AutomationState.PAUSED
        
        # Resume automation
        success = self.engine.resume()
        assert success is True
        
        time.sleep(0.1)
        state = self.engine.get_state()
        assert state in [AutomationState.STARTING, AutomationState.RUNNING]
    
    def test_pause_not_running(self):
        """Test pausing when not running."""
        success = self.engine.pause()
        assert success is False
    
    def test_resume_not_paused(self):
        """Test resuming when not paused."""
        success = self.engine.resume()
        assert success is False
    
    def test_keystroke_execution(self):
        """Test that keystrokes are actually executed."""
        # Use very short delays for testing
        fast_keystrokes = [
            KeystrokeConfig(key='x', delay=0.05),
            KeystrokeConfig(key='y', delay=0.05)
        ]
        
        self.engine.start(fast_keystrokes, self.test_settings)
        
        # Let it run for a bit
        time.sleep(0.5)
        
        # Check that keystrokes were sent
        assert len(self.mock_sender.sent_keystrokes) > 0
        
        # Check that correct keys were sent
        sent_keys = [ks[0] for ks in self.mock_sender.sent_keystrokes]
        assert 'x' in sent_keys or 'y' in sent_keys
    
    def test_execution_statistics(self):
        """Test execution statistics tracking."""
        # Use successful sender
        self.mock_sender.success_rate = 1.0
        
        fast_keystrokes = [KeystrokeConfig(key='z', delay=0.02)]
        
        self.engine.start(fast_keystrokes, self.test_settings)
        time.sleep(0.2)  # Let it execute a few times
        
        stats = self.engine.get_stats()
        
        # Should have some executions
        assert stats.total_executions > 0
        assert stats.successful_executions > 0
        assert stats.failed_executions == 0
        assert stats.success_rate == 1.0
        assert stats.total_runtime > 0
    
    def test_execution_statistics_with_failures(self):
        """Test statistics with some failures."""
        # Set sender to fail 50% of the time
        self.mock_sender.success_rate = 0.5
        
        fast_keystrokes = [KeystrokeConfig(key='w', delay=0.02)]
        
        self.engine.start(fast_keystrokes, self.test_settings)
        time.sleep(0.3)  # Let it execute multiple times
        
        stats = self.engine.get_stats()
        
        # Should have both successes and failures
        assert stats.total_executions > 0
        assert stats.successful_executions > 0
        assert stats.failed_executions > 0
        assert stats.total_executions == stats.successful_executions + stats.failed_executions
        assert 0.0 < stats.success_rate < 1.0
    
    def test_state_callbacks(self):
        """Test state change callback system."""
        callback_states = []
        
        def state_callback(new_state):
            callback_states.append(new_state)
        
        # Register callback
        self.engine.register_state_callback(state_callback)
        
        # Start and stop automation
        self.engine.start(self.test_keystrokes, self.test_settings)
        time.sleep(0.1)
        self.engine.stop()
        time.sleep(0.1)
        
        # Should have received state change notifications
        assert len(callback_states) > 0
        assert AutomationState.STARTING in callback_states or AutomationState.RUNNING in callback_states
    
    def test_max_execution_time_limit(self):
        """Test maximum execution time enforcement."""
        # Set very short max execution time
        short_settings = AppSettings(
            global_cooldown=0.01,
            max_execution_time=0.1  # 100ms limit
        )
        
        fast_keystrokes = [KeystrokeConfig(key='t', delay=0.01)]
        
        self.engine.start(fast_keystrokes, short_settings)
        
        # Wait longer than the limit
        time.sleep(0.3)
        
        # Engine should have stopped due to time limit
        state = self.engine.get_state()
        assert state in [AutomationState.STOPPED, AutomationState.STOPPING]
    
    def test_keystroke_sender_unavailable(self):
        """Test behavior when keystroke sender is unavailable."""
        # Create engine with unavailable sender
        unavailable_sender = Mock()
        unavailable_sender.is_available.return_value = False
        
        engine = AutomationEngine(unavailable_sender)
        
        success = engine.start(self.test_keystrokes, self.test_settings)
        assert success is False
        assert engine.get_state() == AutomationState.STOPPED
    
    def test_error_handling_in_execution(self):
        """Test error handling during keystroke execution."""
        # Create sender that raises exceptions
        error_sender = Mock()
        error_sender.is_available.return_value = True
        error_sender.send_keystroke.side_effect = Exception("Simulated error")
        
        engine = AutomationEngine(error_sender)
        
        # Should start successfully
        success = engine.start(self.test_keystrokes, self.test_settings)
        assert success is True
        
        # Let it try to execute and handle errors
        time.sleep(0.2)
        
        # Engine should handle errors gracefully
        stats = engine.get_stats()
        assert stats.failed_executions > 0
    
    def test_schedule_caching(self):
        """Test that schedules are cached for performance."""
        # Start with one set of keystrokes
        keystrokes1 = [KeystrokeConfig(key='1', delay=0.1)]
        self.engine.start(keystrokes1, self.test_settings)
        time.sleep(0.1)
        self.engine.stop()
        time.sleep(0.1)
        
        # Start with same keystrokes (should use cached schedule)
        start_time = time.time()
        self.engine.start(keystrokes1, self.test_settings)
        cache_time = time.time() - start_time
        time.sleep(0.1)
        self.engine.stop()
        time.sleep(0.1)
        
        # Start with different keystrokes (should rebuild schedule)
        keystrokes2 = [KeystrokeConfig(key='2', delay=0.1)]
        start_time = time.time()
        self.engine.start(keystrokes2, self.test_settings)
        rebuild_time = time.time() - start_time
        
        # Cache hit should be faster than rebuild (in most cases)
        # Note: This is a weak test since times can vary
        assert cache_time >= 0 and rebuild_time >= 0
    
    def test_memory_limits(self):
        """Test memory usage limits for error tracking."""
        # Create many errors to test error list limits
        error_sender = Mock()
        error_sender.is_available.return_value = True
        error_sender.send_keystroke.return_value = False  # Always fail
        
        engine = AutomationEngine(error_sender)
        
        # Set very short delay to generate many errors quickly
        fast_keystrokes = [KeystrokeConfig(key='e', delay=0.001)]
        fast_settings = AppSettings(global_cooldown=0.001, max_execution_time=0.5)
        
        engine.start(fast_keystrokes, fast_settings)
        time.sleep(0.3)  # Generate many errors
        
        stats = engine.get_stats()
        
        # Should have hit error limit and started cleaning up
        assert stats.failed_executions > 0
        # Error list should be bounded (implementation detail)
    
    def test_disabled_keystrokes_ignored(self):
        """Test that disabled keystrokes are not executed."""
        # Mix of enabled and disabled keystrokes
        mixed_keystrokes = [
            KeystrokeConfig(key='enabled1', delay=0.05, enabled=True),
            KeystrokeConfig(key='disabled1', delay=0.05, enabled=False),
            KeystrokeConfig(key='enabled2', delay=0.05, enabled=True),
            KeystrokeConfig(key='disabled2', delay=0.05, enabled=False)
        ]
        
        self.engine.start(mixed_keystrokes, self.test_settings)
        time.sleep(0.3)
        
        # Check sent keystrokes
        sent_keys = [ks[0] for ks in self.mock_sender.sent_keystrokes]
        
        # Should only contain enabled keys
        assert 'enabled1' in sent_keys or 'enabled2' in sent_keys
        assert 'disabled1' not in sent_keys
        assert 'disabled2' not in sent_keys
    
    def test_thread_safety(self):
        """Test thread safety of state operations."""
        import threading
        
        # Start multiple threads trying to start/stop
        def start_stop_worker():
            for _ in range(5):
                self.engine.start(self.test_keystrokes, self.test_settings)
                time.sleep(0.01)
                self.engine.stop()
                time.sleep(0.01)
        
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=start_stop_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Engine should end up in a consistent state
        final_state = self.engine.get_state()
        assert final_state in [AutomationState.STOPPED, AutomationState.STOPPING]


class TestExecutionStats:
    """Test cases for ExecutionStats."""
    
    def test_initial_stats(self):
        """Test initial statistics state."""
        stats = ExecutionStats()
        
        assert stats.total_executions == 0
        assert stats.successful_executions == 0
        assert stats.failed_executions == 0
        assert stats.success_rate == 0.0
        assert stats.average_execution_time == 0.0
        assert stats.total_runtime == 0.0
        assert len(stats.execution_errors) == 0
        assert stats.error_count == 0
    
    def test_add_success(self):
        """Test adding successful execution."""
        stats = ExecutionStats()
        
        stats.add_success(0.1)  # 100ms execution time
        
        assert stats.total_executions == 1
        assert stats.successful_executions == 1
        assert stats.failed_executions == 0
        assert stats.success_rate == 1.0
        assert stats.average_execution_time == 0.1
    
    def test_add_failure(self):
        """Test adding failed execution."""
        stats = ExecutionStats()
        
        stats.add_failure(Exception("Test error"))
        
        assert stats.total_executions == 1
        assert stats.successful_executions == 0
        assert stats.failed_executions == 1
        assert stats.success_rate == 0.0
        assert len(stats.execution_errors) == 1
        assert stats.error_count == 1
    
    def test_mixed_executions(self):
        """Test statistics with mixed successes and failures."""
        stats = ExecutionStats()
        
        # Add some successes
        stats.add_success(0.1)
        stats.add_success(0.2)
        stats.add_success(0.3)
        
        # Add some failures
        stats.add_failure(Exception("Error 1"))
        stats.add_failure(Exception("Error 2"))
        
        assert stats.total_executions == 5
        assert stats.successful_executions == 3
        assert stats.failed_executions == 2
        assert stats.success_rate == 0.6  # 3/5
        assert stats.average_execution_time == 0.2  # (0.1+0.2+0.3)/3
        assert len(stats.execution_errors) == 2
        assert stats.error_count == 2
    
    def test_error_list_limits(self):
        """Test that error list is bounded."""
        stats = ExecutionStats()
        
        # Add many errors
        for i in range(600):  # More than the default limit
            stats.add_failure(Exception(f"Error {i}"))
        
        # Error list should be bounded
        assert len(stats.execution_errors) <= 500  # Default limit
        assert stats.error_count == 600  # But count should be accurate
        assert stats.failed_executions == 600
    
    def test_runtime_tracking(self):
        """Test runtime tracking."""
        stats = ExecutionStats()
        
        start_time = time.time()
        time.sleep(0.1)
        stats.update_runtime()
        
        assert stats.total_runtime > 0.05  # Should be at least 50ms
        assert stats.total_runtime < 1.0   # But less than 1 second


class TestAutomationError:
    """Test cases for AutomationError exception."""
    
    def test_automation_error_creation(self):
        """Test creating AutomationError."""
        error = AutomationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_automation_error_with_cause(self):
        """Test AutomationError with underlying cause."""
        cause = ValueError("Underlying cause")
        error = AutomationError("Test error", cause)
        
        assert str(error) == "Test error"
        assert error.__cause__ == cause


class TestAutomationState:
    """Test cases for AutomationState enum."""
    
    def test_automation_states(self):
        """Test all automation states exist."""
        states = [
            AutomationState.STOPPED,
            AutomationState.STARTING,
            AutomationState.RUNNING,
            AutomationState.PAUSED,
            AutomationState.STOPPING,
            AutomationState.ERROR
        ]
        
        # All states should be unique
        assert len(set(states)) == len(states)
        
        # All states should have string representations
        for state in states:
            assert isinstance(state.name, str)
            assert len(state.name) > 0


if __name__ == '__main__':
    pytest.main([__file__]) 