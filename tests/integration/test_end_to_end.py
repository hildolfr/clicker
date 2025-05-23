"""
End-to-end integration tests for the Clicker application.

Tests complete workflows including configuration loading,
automation execution, and system integration.
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch
from clicker.app import ClickerApp
from clicker.config.manager import ConfigManager
from clicker.config.models import AppSettings, KeystrokeConfig, ProfileConfig
from clicker.core.automation import AutomationEngine, AutomationState
from clicker.core.keystrokes import WindowsKeystrokeSender


class TestConfigurationIntegration:
    """Integration tests for configuration management."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        self.config_manager = ConfigManager(self.config_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_configuration_file_creation(self):
        """Test automatic creation of configuration files."""
        # Initially, config files shouldn't exist
        settings_file = self.config_dir / "settings.json"
        keystrokes_file = self.config_dir / "keystrokes.txt"
        
        assert not settings_file.exists()
        assert not keystrokes_file.exists()
        
        # Load configuration (should create default files)
        success = self.config_manager.load_configuration()
        assert success is True
        
        # Files should now exist
        assert settings_file.exists()
        assert keystrokes_file.exists()
        
        # Files should contain valid data
        with open(settings_file, 'r') as f:
            settings_data = json.load(f)
            assert 'toggle_key' in settings_data
            assert 'global_cooldown' in settings_data
        
        with open(keystrokes_file, 'r') as f:
            content = f.read()
            assert len(content) > 0  # Should have at least comments
    
    def test_settings_persistence(self):
        """Test settings save and reload."""
        # Create custom settings
        custom_settings = AppSettings(
            toggle_key='F5',
            global_cooldown=2.5,
            high_performance_mode=True,
            thread_pool_size=4
        )
        
        # Save settings
        success = self.config_manager.save_settings(custom_settings)
        assert success is True
        
        # Create new config manager (simulates app restart)
        new_config_manager = ConfigManager(self.config_dir)
        success = new_config_manager.load_configuration()
        assert success is True
        
        # Verify settings were loaded correctly
        loaded_settings = new_config_manager.get_settings()
        assert loaded_settings.toggle_key == 'F5'
        assert loaded_settings.global_cooldown == 2.5
        assert loaded_settings.high_performance_mode is True
        assert loaded_settings.thread_pool_size == 4
    
    def test_keystrokes_persistence(self):
        """Test keystrokes save and reload."""
        # Create custom keystrokes
        custom_keystrokes = [
            KeystrokeConfig(key='1', delay=1.0, description='Heal'),
            KeystrokeConfig(key='2', delay=1.5, description='Attack'),
            KeystrokeConfig(key='C-s', delay=3.0, description='Save')
        ]
        
        # Save keystrokes
        success = self.config_manager.save_keystrokes(custom_keystrokes)
        assert success is True
        
        # Create new config manager
        new_config_manager = ConfigManager(self.config_dir)
        success = new_config_manager.load_configuration()
        assert success is True
        
        # Verify keystrokes were loaded correctly
        loaded_keystrokes = new_config_manager.get_keystrokes()
        assert len(loaded_keystrokes) == 3
        assert loaded_keystrokes[0].key == '1'
        assert loaded_keystrokes[0].description == 'Heal'
        assert loaded_keystrokes[1].key == '2'
        assert loaded_keystrokes[1].description == 'Attack'
        assert loaded_keystrokes[2].key == 'C-s'
        assert loaded_keystrokes[2].description == 'Save'
    
    def test_profile_workflow(self):
        """Test complete profile creation, save, and load workflow."""
        # Create a profile
        settings = AppSettings(toggle_key='F3', global_cooldown=1.0)
        keystrokes = [
            KeystrokeConfig(key='q', delay=1.0, description='Quick action'),
            KeystrokeConfig(key='e', delay=2.0, description='Use item')
        ]
        
        profile = ProfileConfig(
            name="Test Gaming Profile",
            description="Profile for testing",
            settings=settings,
            keystrokes=keystrokes,
            tags=['test', 'gaming'],
            author="TestUser",
            version="1.0.0"
        )
        
        # Save profile
        profile_path = self.config_dir / "test_profile.json"
        with open(profile_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
        
        # Load profile
        with open(profile_path, 'r') as f:
            profile_data = json.load(f)
        
        loaded_profile = ProfileConfig.from_dict(profile_data)
        
        # Verify profile loaded correctly
        assert loaded_profile.name == "Test Gaming Profile"
        assert loaded_profile.description == "Profile for testing"
        assert loaded_profile.settings.toggle_key == 'F3'
        assert loaded_profile.settings.global_cooldown == 1.0
        assert len(loaded_profile.keystrokes) == 2
        assert loaded_profile.keystrokes[0].key == 'q'
        assert loaded_profile.keystrokes[1].key == 'e'
        assert loaded_profile.tags == ['test', 'gaming']
        assert loaded_profile.author == "TestUser"
        assert loaded_profile.version == "1.0.0"
    
    def test_configuration_validation_errors(self):
        """Test handling of invalid configuration files."""
        # Create invalid settings file
        settings_file = self.config_dir / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(settings_file, 'w') as f:
            f.write('{"invalid_json": }')  # Invalid JSON
        
        # Should handle invalid JSON gracefully
        success = self.config_manager.load_configuration()
        # Should create valid defaults despite invalid file
        assert success is True
        
        # Should have fallback settings
        settings = self.config_manager.get_settings()
        assert isinstance(settings, AppSettings)
    
    def test_backup_and_restore(self):
        """Test configuration backup and restore functionality."""
        # Create initial configuration
        original_settings = AppSettings(toggle_key='F4', global_cooldown=3.0)
        self.config_manager.save_settings(original_settings)
        
        # Modify configuration
        modified_settings = AppSettings(toggle_key='F6', global_cooldown=1.0)
        self.config_manager.save_settings(modified_settings)
        
        # Check that backup was created
        backup_dir = self.config_dir / "backups"
        assert backup_dir.exists()
        
        backup_files = list(backup_dir.glob("settings_*.json"))
        assert len(backup_files) > 0


class TestAutomationIntegration:
    """Integration tests for automation functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.mock_sender = Mock()
        self.mock_sender.is_available.return_value = True
        self.mock_sender.send_keystroke.return_value = True
        
        self.engine = AutomationEngine(self.mock_sender)
    
    def teardown_method(self):
        """Clean up after each test."""
        if self.engine.get_state() != AutomationState.STOPPED:
            self.engine.stop()
            time.sleep(0.1)
    
    def test_automation_full_cycle(self):
        """Test complete automation lifecycle."""
        # Create test configuration
        keystrokes = [
            KeystrokeConfig(key='1', delay=0.1, description='Action 1'),
            KeystrokeConfig(key='2', delay=0.1, description='Action 2'),
            KeystrokeConfig(key='3', delay=0.1, description='Action 3')
        ]
        
        settings = AppSettings(
            global_cooldown=0.05,
            max_execution_time=2.0
        )
        
        # Start automation
        success = self.engine.start(keystrokes, settings)
        assert success is True
        
        # Let it run briefly
        time.sleep(0.3)
        
        # Check that it's running
        state = self.engine.get_state()
        assert state in [AutomationState.STARTING, AutomationState.RUNNING]
        
        # Check that keystrokes were sent
        assert self.mock_sender.send_keystroke.called
        
        # Get statistics
        stats = self.engine.get_stats()
        assert stats.total_executions > 0
        assert stats.total_runtime > 0
        
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
        
        # Stop automation
        success = self.engine.stop()
        assert success is True
        
        time.sleep(0.2)
        assert self.engine.get_state() == AutomationState.STOPPED
    
    def test_automation_with_failures(self):
        """Test automation handling of keystroke failures."""
        # Set up sender to fail sometimes
        call_count = 0
        def failing_send_keystroke(key, modifiers=None):
            nonlocal call_count
            call_count += 1
            # Fail every 3rd call
            return call_count % 3 != 0
        
        self.mock_sender.send_keystroke.side_effect = failing_send_keystroke
        
        keystrokes = [KeystrokeConfig(key='x', delay=0.05)]
        settings = AppSettings(global_cooldown=0.02, max_execution_time=0.5)
        
        # Start automation
        self.engine.start(keystrokes, settings)
        time.sleep(0.3)
        
        # Should have both successes and failures
        stats = self.engine.get_stats()
        assert stats.total_executions > 0
        assert stats.successful_executions > 0
        assert stats.failed_executions > 0
        assert 0.0 < stats.success_rate < 1.0
    
    def test_automation_timeout(self):
        """Test automation timeout enforcement."""
        keystrokes = [KeystrokeConfig(key='t', delay=0.01)]
        settings = AppSettings(
            global_cooldown=0.01,
            max_execution_time=0.2  # Very short timeout
        )
        
        # Start automation
        self.engine.start(keystrokes, settings)
        
        # Wait longer than timeout
        time.sleep(0.5)
        
        # Should have stopped due to timeout
        state = self.engine.get_state()
        assert state in [AutomationState.STOPPED, AutomationState.STOPPING]
    
    def test_automation_state_callbacks(self):
        """Test state change callback integration."""
        state_changes = []
        
        def callback(new_state):
            state_changes.append(new_state)
        
        self.engine.register_state_callback(callback)
        
        keystrokes = [KeystrokeConfig(key='s', delay=0.1)]
        settings = AppSettings(global_cooldown=0.05, max_execution_time=1.0)
        
        # Execute start/stop cycle
        self.engine.start(keystrokes, settings)
        time.sleep(0.2)
        self.engine.stop()
        time.sleep(0.2)
        
        # Should have received multiple state change notifications
        assert len(state_changes) > 0
        assert AutomationState.STARTING in state_changes or AutomationState.RUNNING in state_changes


class TestApplicationIntegration:
    """Integration tests for the complete application."""
    
    @patch('clicker.system.singleton.SingletonManager.acquire_lock')
    @patch('clicker.system.admin.AdminChecker.is_admin')
    @patch('clicker.core.keystrokes.WindowsKeystrokeSender.is_available')
    def test_app_initialization(self, mock_is_available, mock_is_admin, mock_acquire_lock):
        """Test complete application initialization."""
        # Mock system dependencies
        mock_acquire_lock.return_value = True
        mock_is_admin.return_value = True
        mock_is_available.return_value = True
        
        # Create temporary config directory
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Create application
            app = ClickerApp(config_dir=config_dir)
            
            # Verify components are initialized
            assert app.config_manager is not None
            assert app.automation_engine is not None
            assert app.admin_checker is not None
            assert app.singleton_manager is not None
    
    @patch('clicker.system.singleton.SingletonManager.acquire_lock')
    @patch('clicker.system.admin.AdminChecker.is_admin')
    @patch('PyQt5.QtWidgets.QApplication')
    def test_app_startup_sequence(self, mock_qapp, mock_is_admin, mock_acquire_lock):
        """Test application startup sequence without Qt event loop."""
        # Mock system dependencies
        mock_acquire_lock.return_value = True
        mock_is_admin.return_value = True
        
        # Mock Qt application
        mock_qapp_instance = Mock()
        mock_qapp.return_value = mock_qapp_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Create application
            app = ClickerApp(config_dir=config_dir)
            
            # Test individual startup components
            app._setup_logging()
            app._check_singleton()
            app._initialize_qt()
            app._load_configuration()
            app._check_admin_privileges()
            
            # Verify configuration was loaded
            assert app.config_manager.get_settings() is not None
            assert app.config_manager.get_keystrokes() is not None


class TestSystemIntegration:
    """Integration tests for system-level functionality."""
    
    def test_keystroke_sender_integration(self):
        """Test Windows keystroke sender integration."""
        # Only run on Windows
        import platform
        if platform.system() != 'Windows':
            pytest.skip("Windows-specific test")
        
        sender = WindowsKeystrokeSender()
        
        # Test availability
        available = sender.is_available()
        assert isinstance(available, bool)
        
        if available:
            # Test simple keystroke (should not fail)
            # Note: This might actually send a keystroke to the system
            # so we use a safe key that won't cause issues
            success = sender.send_keystroke('f24')  # F24 is rarely used
            assert isinstance(success, bool)
    
    @patch('clicker.system.admin.ctypes.windll.shell32.IsUserAnAdmin')
    def test_admin_checker_integration(self, mock_is_admin):
        """Test admin privilege checking integration."""
        from clicker.system.admin import AdminChecker
        
        # Mock admin check
        mock_is_admin.return_value = 1  # Admin
        
        admin_checker = AdminChecker()
        is_admin = admin_checker.is_admin()
        assert is_admin is True
        
        # Mock non-admin
        mock_is_admin.return_value = 0  # Not admin
        is_admin = admin_checker.is_admin()
        assert is_admin is False
    
    def test_file_watcher_integration(self):
        """Test file watching integration."""
        from clicker.utils.file_watcher import FileWatcher
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write("initial content")
        
        try:
            # Set up file watcher
            watcher = FileWatcher()
            changes_detected = []
            
            def on_change():
                changes_detected.append(True)
            
            watcher.watch_file(temp_path, on_change)
            
            # Modify file
            time.sleep(0.1)  # Give watcher time to start
            with open(temp_path, 'w') as f:
                f.write("modified content")
            
            # Wait for change detection
            time.sleep(0.5)
            
            # Should have detected change
            assert len(changes_detected) > 0
            
        finally:
            # Clean up
            temp_path.unlink(missing_ok=True)


class TestErrorRecovery:
    """Integration tests for error recovery scenarios."""
    
    def test_configuration_corruption_recovery(self):
        """Test recovery from corrupted configuration files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            config_manager = ConfigManager(config_dir)
            
            # Create corrupted settings file
            settings_file = config_dir / "settings.json"
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_file, 'w') as f:
                f.write("corrupted json data {")
            
            # Should recover gracefully
            success = config_manager.load_configuration()
            assert success is True
            
            # Should have created valid defaults
            settings = config_manager.get_settings()
            assert isinstance(settings, AppSettings)
            assert settings.toggle_key == '~'  # Default value
    
    def test_automation_error_recovery(self):
        """Test automation recovery from errors."""
        # Create sender that fails initially then recovers
        failure_count = 0
        
        def recovering_send_keystroke(key, modifiers=None):
            nonlocal failure_count
            failure_count += 1
            # Fail first 5 attempts, then succeed
            return failure_count > 5
        
        mock_sender = Mock()
        mock_sender.is_available.return_value = True
        mock_sender.send_keystroke.side_effect = recovering_send_keystroke
        
        engine = AutomationEngine(mock_sender)
        
        try:
            keystrokes = [KeystrokeConfig(key='r', delay=0.05)]
            settings = AppSettings(global_cooldown=0.02, max_execution_time=1.0)
            
            # Start automation
            engine.start(keystrokes, settings)
            time.sleep(0.5)
            
            # Should have both failures and successes
            stats = engine.get_stats()
            assert stats.total_executions > 0
            assert stats.failed_executions > 0  # Initial failures
            assert stats.successful_executions > 0  # Recovery successes
            
        finally:
            engine.stop()
            time.sleep(0.1)


class TestPerformance:
    """Integration tests for performance characteristics."""
    
    def test_large_keystroke_configuration(self):
        """Test handling of large keystroke configurations."""
        # Create large number of keystrokes
        large_keystrokes = []
        for i in range(100):  # 100 keystrokes
            large_keystrokes.append(
                KeystrokeConfig(
                    key=f'f{(i % 12) + 1}',  # F1-F12
                    delay=0.1,
                    description=f'Action {i}',
                    tags=[f'tag{i // 10}', f'category{i // 20}']
                )
            )
        
        mock_sender = Mock()
        mock_sender.is_available.return_value = True
        mock_sender.send_keystroke.return_value = True
        
        engine = AutomationEngine(mock_sender)
        
        try:
            settings = AppSettings(global_cooldown=0.01, max_execution_time=1.0)
            
            # Should handle large configuration
            start_time = time.time()
            success = engine.start(large_keystrokes, settings)
            startup_time = time.time() - start_time
            
            assert success is True
            assert startup_time < 5.0  # Should start within 5 seconds
            
            # Let it run briefly
            time.sleep(0.2)
            
            # Should be executing
            state = engine.get_state()
            assert state in [AutomationState.STARTING, AutomationState.RUNNING]
            
        finally:
            engine.stop()
            time.sleep(0.1)
    
    def test_high_frequency_automation(self):
        """Test high-frequency automation performance."""
        mock_sender = Mock()
        mock_sender.is_available.return_value = True
        mock_sender.send_keystroke.return_value = True
        
        engine = AutomationEngine(mock_sender)
        
        try:
            # Very fast keystrokes
            fast_keystrokes = [KeystrokeConfig(key='space', delay=0.01)]
            fast_settings = AppSettings(
                global_cooldown=0.005,  # 5ms cooldown
                max_execution_time=0.5,
                high_performance_mode=True
            )
            
            engine.start(fast_keystrokes, fast_settings)
            time.sleep(0.3)
            
            stats = engine.get_stats()
            
            # Should achieve high execution rate
            executions_per_second = stats.total_executions / stats.total_runtime
            assert executions_per_second > 10  # At least 10 executions per second
            
        finally:
            engine.stop()
            time.sleep(0.1)


if __name__ == '__main__':
    pytest.main([__file__]) 