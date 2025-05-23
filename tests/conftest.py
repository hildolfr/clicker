"""
Pytest configuration and fixtures for Clicker tests.

Provides common test fixtures, mock helpers, and test configuration.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock
from clicker.config.models import AppSettings, KeystrokeConfig, ProfileConfig


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def default_settings():
    """Create default AppSettings for testing."""
    return AppSettings(
        toggle_key='~',
        global_cooldown=1.5,
        high_performance_mode=False,
        thread_pool_size=2
    )


@pytest.fixture
def test_keystrokes():
    """Create test keystroke configurations."""
    return [
        KeystrokeConfig(key='a', delay=1.0, description='Action A'),
        KeystrokeConfig(key='b', delay=2.0, description='Action B'),
        KeystrokeConfig(key='C-s', delay=3.0, description='Save action')
    ]


@pytest.fixture
def gaming_profile(default_settings, test_keystrokes):
    """Create a gaming profile for testing."""
    gaming_settings = AppSettings(
        toggle_key='F1',
        global_cooldown=0.5,
        high_performance_mode=True,
        emergency_stop_key='ctrl+alt+q'
    )
    
    gaming_keystrokes = [
        KeystrokeConfig(key='1', delay=1.0, description='Health potion', tags=['healing']),
        KeystrokeConfig(key='2', delay=1.5, description='Mana potion', tags=['mana']),
        KeystrokeConfig(key='q', delay=0.8, description='Quick attack', tags=['combat']),
        KeystrokeConfig(key='e', delay=2.0, description='Special ability', tags=['combat'])
    ]
    
    return ProfileConfig(
        name="Gaming Profile",
        description="Optimized for gaming",
        settings=gaming_settings,
        keystrokes=gaming_keystrokes,
        tags=['gaming', 'rpg'],
        author="TestUser",
        version="1.0.0"
    )


@pytest.fixture
def mock_keystroke_sender():
    """Create a mock keystroke sender for testing."""
    mock = Mock()
    mock.is_available.return_value = True
    mock.send_keystroke.return_value = True
    mock.sent_keystrokes = []
    
    def track_keystrokes(key, modifiers=None):
        mock.sent_keystrokes.append((key, modifiers))
        return True
    
    mock.send_keystroke.side_effect = track_keystrokes
    return mock


@pytest.fixture
def config_files(temp_config_dir, default_settings, test_keystrokes):
    """Create configuration files in temp directory."""
    # Create settings file
    settings_file = temp_config_dir / "settings.json"
    with open(settings_file, 'w') as f:
        json.dump(default_settings.to_dict(), f, indent=2)
    
    # Create keystrokes file
    keystrokes_file = temp_config_dir / "keystrokes.txt"
    with open(keystrokes_file, 'w') as f:
        f.write("# Test keystrokes configuration\n")
        for ks in test_keystrokes:
            f.write(f"{ks.to_string()}\n")
    
    return {
        'settings_file': settings_file,
        'keystrokes_file': keystrokes_file,
        'config_dir': temp_config_dir
    }


@pytest.fixture
def corrupted_config_files(temp_config_dir):
    """Create corrupted configuration files for error testing."""
    # Corrupted settings file
    settings_file = temp_config_dir / "settings.json"
    with open(settings_file, 'w') as f:
        f.write('{"invalid": json data')
    
    # Corrupted keystrokes file
    keystrokes_file = temp_config_dir / "keystrokes.txt"
    with open(keystrokes_file, 'w') as f:
        f.write('invalid keystroke format\n')
        f.write('another bad line without delay\n')
    
    return {
        'settings_file': settings_file,
        'keystrokes_file': keystrokes_file,
        'config_dir': temp_config_dir
    }


@pytest.fixture
def sample_profile_file(temp_config_dir, gaming_profile):
    """Create a sample profile file."""
    profile_file = temp_config_dir / "gaming.profile"
    with open(profile_file, 'w') as f:
        json.dump(gaming_profile.to_dict(), f, indent=2)
    
    return profile_file


class MockQApplication:
    """Mock PyQt5 QApplication for testing."""
    
    def __init__(self, *args, **kwargs):
        self.exec_called = False
        self.quit_called = False
        
    def exec_(self):
        self.exec_called = True
        return 0
    
    def quit(self):
        self.quit_called = True
    
    def setQuitOnLastWindowClosed(self, value):
        pass
    
    def processEvents(self):
        pass


@pytest.fixture
def mock_qt_app():
    """Mock Qt application for GUI testing."""
    return MockQApplication()


class ValidationTestCases:
    """Common test cases for validation testing."""
    
    @staticmethod
    def get_invalid_keys():
        """Get list of invalid key formats."""
        return [
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
    
    @staticmethod
    def get_valid_keys():
        """Get list of valid key formats."""
        return [
            'a', 'z', '1', '9',  # Single alphanumeric
            'f1', 'f12', 'f24',  # Function keys
            'space', 'enter', 'tab', 'escape',  # Special keys
            'C-a', 'S-f1', 'A-space',  # Single modifiers
            'C-S-a', 'C-A-f1', 'S-A-space',  # Dual modifiers
        ]
    
    @staticmethod
    def get_invalid_delays():
        """Get list of invalid delay values."""
        return [-1.0, 0.0, 0.05, 3601.0, 'invalid']
    
    @staticmethod
    def get_valid_delays():
        """Get list of valid delay values."""
        return [0.1, 1.0, 1.5, 100.0, 3600.0]


@pytest.fixture
def validation_cases():
    """Provide validation test cases."""
    return ValidationTestCases


# Performance test fixtures
@pytest.fixture
def large_keystroke_list():
    """Create a large list of keystrokes for performance testing."""
    keystrokes = []
    for i in range(100):
        keystrokes.append(KeystrokeConfig(
            key=f'f{(i % 12) + 1}',
            delay=0.1,
            description=f'Action {i}',
            tags=[f'tag{i // 10}', f'category{i // 20}']
        ))
    return keystrokes


@pytest.fixture
def high_performance_settings():
    """Create high-performance settings for testing."""
    return AppSettings(
        global_cooldown=0.01,
        high_performance_mode=True,
        thread_pool_size=4,
        memory_limit_mb=200
    )


# Mock system fixtures
@pytest.fixture
def mock_admin_checker():
    """Mock admin checker for testing."""
    mock = Mock()
    mock.is_admin.return_value = True
    mock.request_admin_privileges.return_value = True
    return mock


@pytest.fixture
def mock_singleton_manager():
    """Mock singleton manager for testing."""
    mock = Mock()
    mock.acquire_lock.return_value = True
    mock.release_lock.return_value = None
    return mock


@pytest.fixture
def mock_file_watcher():
    """Mock file watcher for testing."""
    mock = Mock()
    mock.watch_file.return_value = None
    mock.stop_watching.return_value = None
    return mock


# Test data generators
def generate_test_keystrokes(count=10, key_prefix='test', delay_range=(0.1, 3.0)):
    """Generate test keystrokes with specified parameters."""
    import random
    keystrokes = []
    
    for i in range(count):
        delay = random.uniform(delay_range[0], delay_range[1])
        keystrokes.append(KeystrokeConfig(
            key=f'{key_prefix}{i}',
            delay=delay,
            description=f'Test action {i}',
            enabled=random.choice([True, False, True]),  # Bias toward enabled
            priority=random.randint(0, 10),
            tags=[f'tag{i}', f'group{i // 5}']
        ))
    
    return keystrokes


def generate_test_profiles(count=5):
    """Generate test profiles with various configurations."""
    profiles = []
    
    for i in range(count):
        settings = AppSettings(
            toggle_key=f'F{i+1}',
            global_cooldown=1.0 + i * 0.5,
            high_performance_mode=(i % 2 == 0)
        )
        
        keystrokes = generate_test_keystrokes(
            count=5 + i,
            key_prefix=f'profile{i}',
            delay_range=(0.5, 2.0)
        )
        
        profile = ProfileConfig(
            name=f"Test Profile {i}",
            description=f"Test profile for scenario {i}",
            settings=settings,
            keystrokes=keystrokes,
            tags=[f'test', f'scenario{i}'],
            author=f"TestUser{i}",
            version=f"1.{i}.0"
        )
        
        profiles.append(profile)
    
    return profiles


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "windows_only: marks tests as Windows-specific"
    )
    config.addinivalue_line(
        "markers", "requires_admin: marks tests that require admin privileges"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to performance tests
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.slow)
        
        # Add Windows marker to Windows-specific tests
        if "windows" in item.name.lower() or "admin" in item.name.lower():
            item.add_marker(pytest.mark.windows_only)


# Helper functions for tests
def assert_config_valid(config_obj, config_type):
    """Assert that a configuration object is valid."""
    assert config_obj is not None
    assert isinstance(config_obj, config_type)
    
    if hasattr(config_obj, 'validate'):
        config_obj.validate()  # Should not raise


def assert_keystrokes_equal(ks1, ks2):
    """Assert that two keystrokes are equal."""
    assert ks1.key == ks2.key
    assert ks1.delay == ks2.delay
    assert ks1.enabled == ks2.enabled
    assert ks1.description == ks2.description
    assert ks1.tags == ks2.tags
    assert ks1.priority == ks2.priority
    assert ks1.max_failures == ks2.max_failures


def assert_settings_equal(s1, s2):
    """Assert that two settings objects are equal."""
    assert s1.toggle_key == s2.toggle_key
    assert s1.global_cooldown == s2.global_cooldown
    assert s1.high_performance_mode == s2.high_performance_mode
    assert s1.thread_pool_size == s2.thread_pool_size
    # Add more assertions as needed


def create_temp_config_with_data(temp_dir, settings=None, keystrokes=None):
    """Create temporary configuration files with specified data."""
    if settings is None:
        settings = AppSettings()
    
    if keystrokes is None:
        keystrokes = [KeystrokeConfig(key='a', delay=1.0, description='Default test')]
    
    # Create settings file
    settings_file = temp_dir / "settings.json"
    with open(settings_file, 'w') as f:
        json.dump(settings.to_dict(), f, indent=2)
    
    # Create keystrokes file
    keystrokes_file = temp_dir / "keystrokes.txt"
    with open(keystrokes_file, 'w') as f:
        f.write("# Generated test keystrokes\n")
        for ks in keystrokes:
            f.write(f"{ks.to_string()}\n")
    
    return {
        'settings_file': settings_file,
        'keystrokes_file': keystrokes_file,
        'settings': settings,
        'keystrokes': keystrokes
    } 