"""
Unit tests for configuration models.

Tests all validation rules, serialization, and edge cases for
KeystrokeConfig, AppSettings, and ProfileConfig.
"""

import pytest
import re
from datetime import datetime, timezone
from clicker.config.models import KeystrokeConfig, AppSettings, ProfileConfig
from clicker.config.enums import IndicatorType, KeystrokeMethod


class TestKeystrokeConfig:
    """Test cases for KeystrokeConfig."""
    
    def test_valid_keystroke_creation(self):
        """Test creating valid keystroke configurations."""
        # Basic keystroke
        ks = KeystrokeConfig(key='a', delay=1.5)
        assert ks.key == 'a'
        assert ks.delay == 1.5
        assert ks.enabled is True
        assert ks.description == ""
        assert ks.tags == []
        assert ks.priority == 0
        assert ks.max_failures == 3
        
        # Full keystroke with all fields
        ks = KeystrokeConfig(
            key='C-S-a',
            delay=2.0,
            enabled=False,
            description='Complex keystroke',
            tags=['test', 'complex'],
            priority=5,
            max_failures=5
        )
        assert ks.key == 'C-S-a'
        assert ks.delay == 2.0
        assert ks.enabled is False
        assert ks.description == 'Complex keystroke'
        assert ks.tags == ['test', 'complex']
        assert ks.priority == 5
        assert ks.max_failures == 5
    
    def test_key_validation(self):
        """Test key format validation."""
        # Valid keys
        valid_keys = [
            'a', 'z', '1', '9',  # Single alphanumeric
            'f1', 'f12', 'f24',  # Function keys
            'space', 'enter', 'tab', 'escape',  # Special keys
            'C-a', 'S-f1', 'A-space',  # Single modifiers
            'C-S-a', 'C-A-f1', 'S-A-space',  # Dual modifiers
            'C-S-A-a'  # Triple modifiers (if supported)
        ]
        
        for key in valid_keys:
            ks = KeystrokeConfig(key=key, delay=1.0)
            assert ks.key == key
        
        # Invalid keys
        invalid_keys = [
            '',  # Empty
            '   ',  # Whitespace only
            'CC-a',  # Duplicate modifier
            'S-S-a',  # Duplicate modifier
            'X-a',  # Invalid modifier
            'invalid_key',  # Invalid key name
            'C-invalid',  # Valid modifier, invalid key
            'a-C',  # Wrong order
            '\x00key',  # Control character
        ]
        
        for key in invalid_keys:
            with pytest.raises(ValueError, match="Invalid key format|Key|empty|control"):
                KeystrokeConfig(key=key, delay=1.0)
    
    def test_delay_validation(self):
        """Test delay value validation."""
        # Valid delays
        valid_delays = [0.1, 1.0, 1.5, 100.0, 3600.0]
        for delay in valid_delays:
            ks = KeystrokeConfig(key='a', delay=delay)
            assert ks.delay == delay
        
        # Invalid delays
        invalid_delays = [-1.0, 0.0, 0.05, 3601.0, 'invalid']
        for delay in invalid_delays:
            with pytest.raises(ValueError, match="Delay"):
                KeystrokeConfig(key='a', delay=delay)
    
    def test_description_validation(self):
        """Test description validation."""
        # Valid descriptions
        ks = KeystrokeConfig(key='a', delay=1.0, description='Valid description')
        assert ks.description == 'Valid description'
        
        # Empty description is valid
        ks = KeystrokeConfig(key='a', delay=1.0, description='')
        assert ks.description == ''
        
        # Long description
        long_desc = 'a' * 500
        ks = KeystrokeConfig(key='a', delay=1.0, description=long_desc)
        assert ks.description == long_desc
        
        # Too long description
        too_long = 'a' * 501
        with pytest.raises(ValueError, match="Description.*exceed"):
            KeystrokeConfig(key='a', delay=1.0, description=too_long)
        
        # Control characters in description
        with pytest.raises(ValueError, match="control characters"):
            KeystrokeConfig(key='a', delay=1.0, description='Test\x00invalid')
    
    def test_tags_validation(self):
        """Test tags validation."""
        # Valid tags
        ks = KeystrokeConfig(key='a', delay=1.0, tags=['tag1', 'tag2'])
        assert ks.tags == ['tag1', 'tag2']
        
        # Empty tags list
        ks = KeystrokeConfig(key='a', delay=1.0, tags=[])
        assert ks.tags == []
        
        # Maximum tags
        max_tags = ['tag' + str(i) for i in range(20)]
        ks = KeystrokeConfig(key='a', delay=1.0, tags=max_tags)
        assert len(ks.tags) == 20
        
        # Too many tags
        too_many_tags = ['tag' + str(i) for i in range(21)]
        with pytest.raises(ValueError, match="Cannot have more than.*tags"):
            KeystrokeConfig(key='a', delay=1.0, tags=too_many_tags)
        
        # Invalid tag types
        with pytest.raises(ValueError, match="Tag.*must be a string"):
            KeystrokeConfig(key='a', delay=1.0, tags=[123])
        
        # Empty tag
        with pytest.raises(ValueError, match="Tag.*cannot be empty"):
            KeystrokeConfig(key='a', delay=1.0, tags=[''])
        
        # Duplicate tags
        with pytest.raises(ValueError, match="Duplicate tag"):
            KeystrokeConfig(key='a', delay=1.0, tags=['tag1', 'tag1'])
        
        # Case-insensitive duplicate
        with pytest.raises(ValueError, match="Duplicate tag"):
            KeystrokeConfig(key='a', delay=1.0, tags=['TAG1', 'tag1'])
    
    def test_priority_validation(self):
        """Test priority validation."""
        # Valid priorities
        for priority in range(0, 11):
            ks = KeystrokeConfig(key='a', delay=1.0, priority=priority)
            assert ks.priority == priority
        
        # Invalid priorities
        with pytest.raises(ValueError, match="Priority must be between"):
            KeystrokeConfig(key='a', delay=1.0, priority=-1)
        
        with pytest.raises(ValueError, match="Priority must be between"):
            KeystrokeConfig(key='a', delay=1.0, priority=11)
        
        with pytest.raises(ValueError, match="Priority must be an integer"):
            KeystrokeConfig(key='a', delay=1.0, priority=1.5)
    
    def test_max_failures_validation(self):
        """Test max_failures validation."""
        # Valid max_failures
        for max_failures in range(1, 11):
            ks = KeystrokeConfig(key='a', delay=1.0, max_failures=max_failures)
            assert ks.max_failures == max_failures
        
        # Invalid max_failures
        with pytest.raises(ValueError, match="max_failures must be between"):
            KeystrokeConfig(key='a', delay=1.0, max_failures=0)
        
        with pytest.raises(ValueError, match="max_failures must be between"):
            KeystrokeConfig(key='a', delay=1.0, max_failures=11)
    
    def test_from_string(self):
        """Test parsing from string format."""
        # Basic format
        ks = KeystrokeConfig.from_string('a 1.5')
        assert ks.key == 'a'
        assert ks.delay == 1.5
        assert ks.description == ''
        
        # With description
        ks = KeystrokeConfig.from_string('a 1.5 Test description')
        assert ks.key == 'a'
        assert ks.delay == 1.5
        assert ks.description == 'Test description'
        
        # Comment line
        assert KeystrokeConfig.from_string('# Comment') is None
        
        # Empty line
        assert KeystrokeConfig.from_string('') is None
        assert KeystrokeConfig.from_string('   ') is None
        
        # Invalid formats
        with pytest.raises(ValueError, match="Invalid keystroke format"):
            KeystrokeConfig.from_string('invalid')
        
        with pytest.raises(ValueError, match="Invalid delay value"):
            KeystrokeConfig.from_string('a invalid')
    
    def test_to_string(self):
        """Test conversion to string format."""
        # Without description
        ks = KeystrokeConfig(key='a', delay=1.5)
        assert ks.to_string() == 'a 1.5'
        
        # With description
        ks = KeystrokeConfig(key='a', delay=1.5, description='Test description')
        assert ks.to_string() == 'a 1.5 Test description'


class TestAppSettings:
    """Test cases for AppSettings."""
    
    def test_default_settings(self):
        """Test default settings creation."""
        settings = AppSettings()
        assert settings.toggle_key == '~'
        assert settings.start_time_stagger == 1.7
        assert settings.order_obeyed is False
        assert settings.global_cooldown == 1.5
        assert settings.indicator_type == IndicatorType.GDI
        assert settings.show_notifications is True
        assert settings.minimize_to_tray is True
        assert settings.keystroke_method == KeystrokeMethod.WINDOWS_API
        assert settings.high_performance_mode is False
        assert settings.logging_enabled is True
        assert settings.fail_safe_enabled is True
        assert settings.max_execution_time == 3600.0
        assert settings.emergency_stop_key == 'ctrl+shift+esc'
        assert settings.check_updates_on_startup is True
        assert settings.auto_install_updates is False
        assert settings.update_channel == 'stable'
        assert settings.thread_pool_size == 2
        assert settings.memory_limit_mb == 100
        assert settings.log_retention_days == 7
        assert settings.config_backup_count == 5
    
    def test_custom_settings(self):
        """Test creating custom settings."""
        settings = AppSettings(
            toggle_key='F1',
            global_cooldown=2.0,
            high_performance_mode=True,
            thread_pool_size=4
        )
        assert settings.toggle_key == 'F1'
        assert settings.global_cooldown == 2.0
        assert settings.high_performance_mode is True
        assert settings.thread_pool_size == 4
    
    def test_toggle_key_validation(self):
        """Test toggle key validation."""
        # Valid toggle keys
        valid_keys = ['~', 'F1', 'ctrl+a', 'alt+f1']
        for key in valid_keys:
            settings = AppSettings(toggle_key=key)
            assert settings.toggle_key == key
        
        # Invalid toggle keys
        with pytest.raises(ValueError, match="toggle_key cannot be empty"):
            AppSettings(toggle_key='')
        
        with pytest.raises(ValueError, match="toggle_key.*control characters"):
            AppSettings(toggle_key='test\x00')
        
        with pytest.raises(ValueError, match="toggle_key.*conflicts"):
            AppSettings(toggle_key='ctrl+alt+del')
    
    def test_timing_validation(self):
        """Test timing settings validation."""
        # Valid timing
        settings = AppSettings(
            start_time_stagger=30.0,
            global_cooldown=5.0,
            max_execution_time=7200.0
        )
        assert settings.start_time_stagger == 30.0
        assert settings.global_cooldown == 5.0
        assert settings.max_execution_time == 7200.0
        
        # Invalid start_time_stagger
        with pytest.raises(ValueError, match="start_time_stagger"):
            AppSettings(start_time_stagger=-1.0)
        
        with pytest.raises(ValueError, match="start_time_stagger"):
            AppSettings(start_time_stagger=61.0)
        
        # Invalid global_cooldown
        with pytest.raises(ValueError, match="global_cooldown"):
            AppSettings(global_cooldown=0.05)
        
        with pytest.raises(ValueError, match="global_cooldown"):
            AppSettings(global_cooldown=301.0)
        
        # Invalid max_execution_time
        with pytest.raises(ValueError, match="max_execution_time"):
            AppSettings(max_execution_time=0.5)
        
        with pytest.raises(ValueError, match="max_execution_time"):
            AppSettings(max_execution_time=86401.0)
    
    def test_emergency_stop_key_validation(self):
        """Test emergency stop key validation."""
        # Valid emergency keys
        valid_keys = ['ctrl+shift+esc', 'ctrl+alt+q', 'shift+alt+x']
        for key in valid_keys:
            settings = AppSettings(emergency_stop_key=key)
            assert settings.emergency_stop_key == key.lower()
        
        # Invalid emergency keys (no modifiers)
        with pytest.raises(ValueError, match="emergency_stop_key should include modifier"):
            AppSettings(emergency_stop_key='q')
        
        with pytest.raises(ValueError, match="emergency_stop_key should include modifier"):
            AppSettings(emergency_stop_key='f1')
    
    def test_update_channel_validation(self):
        """Test update channel validation."""
        # Valid channels
        for channel in ['stable', 'beta', 'dev']:
            settings = AppSettings(update_channel=channel)
            assert settings.update_channel == channel
        
        # Case insensitive
        settings = AppSettings(update_channel='STABLE')
        assert settings.update_channel == 'stable'
        
        # Invalid channel
        with pytest.raises(ValueError, match="update_channel must be one of"):
            AppSettings(update_channel='invalid')
    
    def test_performance_settings_validation(self):
        """Test performance settings validation."""
        # Valid settings
        settings = AppSettings(
            thread_pool_size=5,
            memory_limit_mb=500
        )
        assert settings.thread_pool_size == 5
        assert settings.memory_limit_mb == 500
        
        # Invalid thread pool size
        with pytest.raises(ValueError, match="thread_pool_size must be between"):
            AppSettings(thread_pool_size=0)
        
        with pytest.raises(ValueError, match="thread_pool_size must be between"):
            AppSettings(thread_pool_size=11)
        
        # Invalid memory limit
        with pytest.raises(ValueError, match="memory_limit_mb must be between"):
            AppSettings(memory_limit_mb=5)
        
        with pytest.raises(ValueError, match="memory_limit_mb must be between"):
            AppSettings(memory_limit_mb=1001)
    
    def test_to_dict_from_dict(self):
        """Test serialization to/from dictionary."""
        # Create settings with custom values
        original = AppSettings(
            toggle_key='F2',
            global_cooldown=2.5,
            indicator_type=IndicatorType.PYGAME,
            high_performance_mode=True
        )
        
        # Convert to dict
        settings_dict = original.to_dict()
        assert isinstance(settings_dict, dict)
        assert settings_dict['toggle_key'] == 'F2'
        assert settings_dict['global_cooldown'] == 2.5
        assert settings_dict['indicator_type'] == 'pygame'
        assert settings_dict['high_performance_mode'] is True
        
        # Convert back from dict
        restored = AppSettings.from_dict(settings_dict)
        assert restored.toggle_key == original.toggle_key
        assert restored.global_cooldown == original.global_cooldown
        assert restored.indicator_type == original.indicator_type
        assert restored.high_performance_mode == original.high_performance_mode
    
    def test_from_dict_validation(self):
        """Test from_dict validation and security."""
        # Valid data
        valid_data = {
            'toggle_key': 'F1',
            'global_cooldown': 1.0
        }
        settings = AppSettings.from_dict(valid_data)
        assert settings.toggle_key == 'F1'
        
        # Invalid data type
        with pytest.raises(ValueError, match="Input data must be a dictionary"):
            AppSettings.from_dict("not a dict")
        
        # Unknown fields (should be filtered out)
        data_with_unknown = {
            'toggle_key': 'F1',
            'unknown_field': 'should be ignored',
            'malicious_field': 'injection attempt'
        }
        settings = AppSettings.from_dict(data_with_unknown)
        assert settings.toggle_key == 'F1'
        assert not hasattr(settings, 'unknown_field')
        assert not hasattr(settings, 'malicious_field')


class TestProfileConfig:
    """Test cases for ProfileConfig."""
    
    def test_basic_profile_creation(self):
        """Test creating a basic profile."""
        profile = ProfileConfig(
            name="Test Profile",
            description="A test profile"
        )
        assert profile.name == "Test Profile"
        assert profile.description == "A test profile"
        assert isinstance(profile.settings, AppSettings)
        assert profile.keystrokes == []
        assert profile.tags == []
        assert profile.author == ""
        assert profile.version == "1.0"
    
    def test_full_profile_creation(self):
        """Test creating a profile with all fields."""
        settings = AppSettings(toggle_key='F2')
        keystrokes = [
            KeystrokeConfig(key='a', delay=1.0),
            KeystrokeConfig(key='b', delay=2.0)
        ]
        
        profile = ProfileConfig(
            name="Gaming Profile",
            description="Optimized for gaming",
            settings=settings,
            keystrokes=keystrokes,
            tags=['gaming', 'rpg'],
            author="TestUser",
            version="1.2.0",
            created_at="2024-01-01T12:00:00Z",
            modified_at="2024-01-02T12:00:00Z"
        )
        
        assert profile.name == "Gaming Profile"
        assert profile.description == "Optimized for gaming"
        assert profile.settings.toggle_key == 'F2'
        assert len(profile.keystrokes) == 2
        assert profile.tags == ['gaming', 'rpg']
        assert profile.author == "TestUser"
        assert profile.version == "1.2.0"
        assert profile.created_at == "2024-01-01T12:00:00Z"
        assert profile.modified_at == "2024-01-02T12:00:00Z"
    
    def test_name_validation(self):
        """Test profile name validation."""
        # Valid names
        valid_names = [
            "Gaming Profile",
            "Test-Profile_123",
            "Simple",
            "Profile with spaces"
        ]
        for name in valid_names:
            profile = ProfileConfig(name=name)
            assert profile.name == name
        
        # Invalid names
        with pytest.raises(ValueError, match="Profile name cannot be empty"):
            ProfileConfig(name="")
        
        with pytest.raises(ValueError, match="Profile name.*control characters"):
            ProfileConfig(name="Profile\x00")
        
        with pytest.raises(ValueError, match="Profile name.*invalid characters"):
            ProfileConfig(name="Profile@#$")
        
        with pytest.raises(ValueError, match="reserved system name"):
            ProfileConfig(name="con")
        
        # Too long name
        long_name = "a" * 101
        with pytest.raises(ValueError, match="Profile name.*exceed"):
            ProfileConfig(name=long_name)
    
    def test_version_validation(self):
        """Test version string validation."""
        # Valid versions
        valid_versions = [
            "1.0",
            "1.0.0",
            "2.5.3",
            "1.0.0-beta",
            "2.1.0-alpha1"
        ]
        for version in valid_versions:
            profile = ProfileConfig(name="Test", version=version)
            assert profile.version == version
        
        # Invalid versions
        invalid_versions = [
            "",
            "invalid",
            "1",
            "1.0.0.0",
            "1.0-",
            "v1.0"
        ]
        for version in invalid_versions:
            with pytest.raises(ValueError, match="Version.*semantic versioning"):
                ProfileConfig(name="Test", version=version)
    
    def test_keystroke_management(self):
        """Test keystroke management methods."""
        profile = ProfileConfig(name="Test")
        
        # Add keystroke
        ks1 = KeystrokeConfig(key='a', delay=1.0)
        profile.add_keystroke(ks1)
        assert len(profile.keystrokes) == 1
        assert profile.keystrokes[0] == ks1
        
        # Add another keystroke
        ks2 = KeystrokeConfig(key='b', delay=2.0)
        profile.add_keystroke(ks2)
        assert len(profile.keystrokes) == 2
        
        # Try to add duplicate key (should fail)
        ks_duplicate = KeystrokeConfig(key='a', delay=3.0)
        with pytest.raises(ValueError, match="already exists"):
            profile.add_keystroke(ks_duplicate)
        
        # Remove keystroke
        profile.remove_keystroke(0)
        assert len(profile.keystrokes) == 1
        assert profile.keystrokes[0] == ks2
        
        # Invalid removal
        with pytest.raises(IndexError):
            profile.remove_keystroke(5)
    
    def test_get_enabled_keystrokes(self):
        """Test getting only enabled keystrokes."""
        profile = ProfileConfig(name="Test")
        
        # Add mix of enabled and disabled keystrokes
        profile.add_keystroke(KeystrokeConfig(key='a', delay=1.0, enabled=True))
        profile.add_keystroke(KeystrokeConfig(key='b', delay=2.0, enabled=False))
        profile.add_keystroke(KeystrokeConfig(key='c', delay=3.0, enabled=True))
        
        enabled = profile.get_enabled_keystrokes()
        assert len(enabled) == 2
        assert enabled[0].key == 'a'
        assert enabled[1].key == 'c'
    
    def test_to_dict_from_dict(self):
        """Test profile serialization."""
        # Create profile with all data
        settings = AppSettings(toggle_key='F3', global_cooldown=1.0)
        keystrokes = [
            KeystrokeConfig(key='1', delay=1.0, description='Action 1'),
            KeystrokeConfig(key='2', delay=2.0, description='Action 2')
        ]
        
        original = ProfileConfig(
            name="Test Profile",
            description="Test description",
            settings=settings,
            keystrokes=keystrokes,
            tags=['test', 'automation'],
            author="TestUser",
            version="1.0.0"
        )
        
        # Convert to dict
        profile_dict = original.to_dict()
        assert profile_dict['name'] == "Test Profile"
        assert profile_dict['description'] == "Test description"
        assert isinstance(profile_dict['settings'], dict)
        assert len(profile_dict['keystrokes']) == 2
        assert profile_dict['tags'] == ['test', 'automation']
        assert profile_dict['author'] == "TestUser"
        assert profile_dict['version'] == "1.0.0"
        
        # Convert back from dict
        restored = ProfileConfig.from_dict(profile_dict)
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.settings.toggle_key == original.settings.toggle_key
        assert len(restored.keystrokes) == len(original.keystrokes)
        assert restored.keystrokes[0].key == original.keystrokes[0].key
        assert restored.tags == original.tags
        assert restored.author == original.author
        assert restored.version == original.version


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        # Unicode in description should work
        ks = KeystrokeConfig(
            key='a',
            delay=1.0,
            description='Test with émojis 🎮 and ünicode'
        )
        assert '🎮' in ks.description
        
        # Unicode in profile name should work (if valid characters)
        profile = ProfileConfig(
            name="Profile Test",  # Safe characters only
            description="Description with émojis 🎮"
        )
        assert '🎮' in profile.description
    
    def test_memory_limits(self):
        """Test memory and size limits."""
        # Large configuration data should be rejected
        with pytest.raises(ValueError, match="too large"):
            large_data = {'test_field': 'x' * 20000}
            AppSettings.from_dict(large_data)
        
        # Maximum number of keystrokes
        profile = ProfileConfig(name="Test")
        max_keystrokes = 1000
        
        # Should be able to add up to the limit
        for i in range(10):  # Just test a few, not the full 1000
            profile.add_keystroke(KeystrokeConfig(key=f'f{i+1}', delay=1.0))
        
        assert len(profile.keystrokes) == 10
    
    def test_boundary_values(self):
        """Test boundary values for numeric fields."""
        # Minimum delay
        ks = KeystrokeConfig(key='a', delay=0.1)
        assert ks.delay == 0.1
        
        # Maximum delay
        ks = KeystrokeConfig(key='a', delay=3600.0)
        assert ks.delay == 3600.0
        
        # Minimum/maximum settings values
        settings = AppSettings(
            start_time_stagger=0.0,  # Minimum
            global_cooldown=0.1,     # Minimum
            max_execution_time=1.0,  # Minimum
            thread_pool_size=1,      # Minimum
            memory_limit_mb=10       # Minimum
        )
        assert settings.start_time_stagger == 0.0
        assert settings.global_cooldown == 0.1
        assert settings.max_execution_time == 1.0
        assert settings.thread_pool_size == 1
        assert settings.memory_limit_mb == 10
    
    def test_type_coercion(self):
        """Test type coercion and conversion."""
        # Integer delay should be converted to float
        ks = KeystrokeConfig(key='a', delay=1)
        assert isinstance(ks.delay, (int, float))
        assert ks.delay == 1.0
        
        # String numbers in settings should fail (no automatic conversion)
        with pytest.raises((ValueError, TypeError)):
            AppSettings(global_cooldown="1.5")


if __name__ == '__main__':
    pytest.main([__file__]) 