# Clicker Test Suite

## Overview

Comprehensive test suite for the Clicker application with unit tests, integration tests, and performance benchmarks.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_config_models.py      # Configuration model tests
│   └── test_automation_engine.py  # Automation engine tests
├── integration/             # Integration and end-to-end tests
│   └── test_end_to_end.py         # Complete workflow tests
├── fixtures/                # Test data and fixtures
├── conftest.py             # Pytest configuration and fixtures
├── run_tests.py            # Test runner script
└── README.md               # This file
```

## Quick Start

### Running All Tests

```bash
# Run all tests
python tests/run_tests.py

# Run with coverage
python tests/run_tests.py --coverage

# Run with HTML coverage report
python tests/run_tests.py --coverage-html
```

### Running Specific Test Types

```bash
# Unit tests only
python tests/run_tests.py --unit

# Integration tests only
python tests/run_tests.py --integration

# Fast tests only (skip slow ones)
python tests/run_tests.py --fast

# Performance benchmarks
python tests/run_tests.py --benchmark
```

### Running Specific Tests

```bash
# Run tests matching a pattern
python tests/run_tests.py --test "test_config"

# Run a specific test file
python tests/run_tests.py --file tests/unit/test_config_models.py

# Run tests with verbose output
python tests/run_tests.py --verbose
```

## Test Categories

### Unit Tests

- **Configuration Models** (`test_config_models.py`)
  - KeystrokeConfig validation and serialization
  - AppSettings validation and type checking
  - ProfileConfig management and workflows
  - Edge cases and error handling

- **Automation Engine** (`test_automation_engine.py`)
  - State management and transitions
  - Execution statistics tracking
  - Error handling and recovery
  - Thread safety and performance

### Integration Tests

- **Configuration Integration** (`test_end_to_end.py`)
  - File creation and persistence
  - Settings and keystroke workflows
  - Profile save/load operations
  - Backup and restore functionality

- **Automation Integration**
  - Complete automation lifecycle
  - State callbacks and monitoring
  - Error recovery scenarios
  - Performance characteristics

- **System Integration**
  - Windows API integration
  - Admin privilege checking
  - File watching functionality

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.windows_only` - Windows-specific tests
- `@pytest.mark.requires_admin` - Tests requiring admin privileges

## Test Fixtures

### Common Fixtures

- `temp_config_dir` - Temporary directory for configuration files
- `default_settings` - Default AppSettings for testing
- `test_keystrokes` - Standard test keystroke configurations
- `gaming_profile` - Complete gaming profile for testing
- `mock_keystroke_sender` - Mock keystroke sender with tracking

### Configuration Fixtures

- `config_files` - Valid configuration files in temp directory
- `corrupted_config_files` - Corrupted files for error testing
- `sample_profile_file` - Sample profile file for loading tests

### Mock Fixtures

- `mock_qt_app` - Mock PyQt5 application
- `mock_admin_checker` - Mock admin privilege checker
- `mock_singleton_manager` - Mock singleton manager

## Coverage Requirements

Target coverage levels:
- **Overall**: >90%
- **Core modules**: >95%
- **Configuration**: >95%
- **Automation**: >90%
- **UI components**: >80%

## Adding New Tests

### Unit Test Template

```python
import pytest
from clicker.your_module import YourClass

class TestYourClass:
    """Test cases for YourClass."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.instance = YourClass()
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = self.instance.method()
        assert result == expected_value
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ExpectedError):
            self.instance.invalid_operation()
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with empty inputs
        # Test with maximum values
        # Test with invalid inputs
        pass
```

### Integration Test Template

```python
import pytest
import tempfile
from pathlib import Path

class TestYourIntegration:
    """Integration tests for your component."""
    
    def setup_method(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        # Set up test data
    
    def teardown_method(self):
        """Clean up after test."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self):
        """Test complete workflow end-to-end."""
        # Test full workflow
        # Verify all steps
        # Check final state
        pass
```

## Performance Testing

### Benchmarking

Performance tests use custom timing and can be run with:

```bash
python tests/run_tests.py --benchmark
```

### Performance Targets

- Configuration loading: <500ms for 1000 keystrokes
- Automation startup: <1s for any configuration
- Keystroke execution: >50/second in high-performance mode
- Memory usage: <100MB for normal operation

## Continuous Integration

### GitHub Actions

The test suite is designed to run in CI environments:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python tests/run_tests.py --coverage --junit-xml=results.xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Local Pre-commit

Run before committing:

```bash
# Quick test
python tests/run_tests.py --fast

# Full test suite
python tests/run_tests.py --coverage

# Check specific functionality
python tests/run_tests.py --test "your_feature"
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure the package is in Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Missing Dependencies**
   ```bash
   pip install pytest pytest-cov pytest-mock
   ```

3. **Windows-specific Test Failures**
   ```bash
   # Skip Windows tests on other platforms
   python tests/run_tests.py --no-windows
   ```

4. **Slow Test Performance**
   ```bash
   # Run only fast tests
   python tests/run_tests.py --fast
   ```

### Debug Mode

For debugging test failures:

```bash
# Verbose output with no capture
python -m pytest tests/ -v -s

# Stop on first failure
python -m pytest tests/ -x

# Drop into debugger on failure
python -m pytest tests/ --pdb
```

## Test Data

### Sample Configurations

Tests use realistic sample data:

- Gaming profiles with combat/healing keystrokes
- Productivity profiles with shortcuts and macros
- Edge case configurations with boundary values
- Invalid configurations for error testing

### Mock Data

Mock objects simulate:
- Windows API calls
- File system operations
- Network requests (for updates)
- User interactions

## Best Practices

### Writing Tests

1. **Clear Names**: Test names should describe what they test
2. **Arrange-Act-Assert**: Structure tests clearly
3. **One Concept**: Test one concept per test method
4. **Independent**: Tests should not depend on each other
5. **Fast**: Unit tests should complete quickly

### Test Organization

1. **Group Related Tests**: Use classes to group related tests
2. **Use Fixtures**: Reuse setup code with fixtures
3. **Mock External Dependencies**: Don't test external systems
4. **Test Error Paths**: Include negative test cases

### Maintenance

1. **Keep Tests Updated**: Update tests when code changes
2. **Remove Obsolete Tests**: Clean up tests for removed features
3. **Monitor Coverage**: Maintain high coverage levels
4. **Review Test Results**: Investigate and fix flaky tests

## Documentation

- [API Documentation](../docs/API.md)
- [Configuration Guide](../PROFILE_USAGE.md)
- [Development Guide](../README.md)

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain or improve coverage
4. Update documentation
5. Add integration tests for new workflows 