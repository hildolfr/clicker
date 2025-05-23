# Contributing Guide

Guide for contributing to the Clicker project.

## 🚀 Getting Started

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/clicker.git
   cd clicker
   ```

2. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

3. **Verify installation**
   ```bash
   python main.py --version
   python -m pytest tests/ -v
   ```

### Development Environment

- **Python**: 3.11 or higher
- **OS**: Windows 10/11 (primary target)
- **IDE**: Any Python IDE (VS Code, PyCharm recommended)
- **Git**: Version control

## 🏗️ Project Structure

```
clicker/
├── clicker/           # Main application code
├── docs/              # Documentation
├── tests/             # Test suite
├── scripts/           # Build and utility scripts
├── main.py           # Application entry point
├── requirements.txt  # Dependencies
└── pyproject.toml   # Project configuration
```

## 🔧 Development Workflow

### 1. Issue Selection

- Check existing issues in the issue tracker
- Look for issues labeled `good first issue` for beginners
- Comment on issues you'd like to work on

### 2. Branch Creation

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Or bug fix branch
git checkout -b fix/issue-number-description
```

### 3. Development

- Follow the existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Test thoroughly on Windows

### 4. Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test files
python -m pytest tests/unit/test_config.py

# Run with coverage
python -m pytest --cov=clicker tests/
```

### 5. Documentation

- Update relevant documentation in `docs/`
- Add docstrings to new functions and classes
- Update API documentation if needed

### 6. Pull Request

```bash
# Commit changes
git add .
git commit -m "feat: add new feature description"

# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## 📝 Code Standards

### Python Style

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use descriptive variable and function names

```python
def send_keystroke(self, key: str, delay: float = 0.0) -> bool:
    """
    Send a keystroke with optional delay.
    
    Args:
        key: Key to send (e.g., 'a', 'ctrl+c')
        delay: Delay in seconds before sending
        
    Returns:
        True if keystroke sent successfully, False otherwise
    """
    pass
```

### Architecture Patterns

- Use dependency injection
- Follow event-driven patterns
- Implement proper error handling
- Add logging for debugging

### File Organization

- Group related functionality in modules
- Use clear, descriptive module names
- Keep files focused and reasonably sized
- Follow the existing package structure

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests
├── conftest.py       # Shared test fixtures
└── test_*.py         # Test modules
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock
from clicker.config.manager import ConfigManager

class TestConfigManager:
    def test_load_default_settings(self):
        """Test loading default settings."""
        config = ConfigManager()
        settings = config.settings
        
        assert settings.toggle_key == '~'
        assert settings.global_cooldown == 1.5
    
    def test_invalid_configuration(self):
        """Test handling of invalid configuration."""
        with pytest.raises(ConfigurationError):
            AppSettings(toggle_key='')
```

### Test Categories

- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test component interactions  
- **System Tests**: Test full application flows
- **Performance Tests**: Test performance characteristics

## 📋 Contribution Types

### Bug Fixes

1. **Identify the Issue**
   - Reproduce the bug
   - Understand the root cause
   - Check for existing fixes

2. **Fix Implementation**
   - Minimal changes to fix the issue
   - Add test cases for the bug
   - Ensure no regressions

3. **Testing**
   - Test the specific fix
   - Run full test suite
   - Manual testing if needed

### New Features

1. **Feature Design**
   - Discuss in issues before implementing
   - Consider backward compatibility
   - Plan testing strategy

2. **Implementation**
   - Follow existing patterns
   - Add comprehensive tests
   - Update documentation

3. **Integration**
   - Ensure feature works with existing code
   - Test edge cases
   - Performance considerations

### Documentation

- Fix typos and grammatical errors
- Add missing documentation
- Improve code examples
- Update API references

### Performance Improvements

- Profile before optimizing
- Measure improvements
- Ensure correctness maintained
- Add performance tests

## 🔍 Code Review Process

### Submitting PRs

1. **Clear Description**
   - Explain what the PR does
   - Reference related issues
   - List breaking changes

2. **Code Quality**
   - Follow style guidelines
   - Include tests
   - Update documentation

3. **Testing**
   - All tests pass
   - New functionality tested
   - Edge cases considered

### Review Criteria

- **Functionality**: Does it work as intended?
- **Code Quality**: Is it clean and maintainable?
- **Testing**: Are there adequate tests?
- **Documentation**: Is it properly documented?
- **Performance**: Any performance implications?

## 🐛 Bug Reports

### Good Bug Reports Include

1. **Clear Title** - Concise description of the issue
2. **Steps to Reproduce** - Detailed reproduction steps
3. **Expected Behavior** - What should happen
4. **Actual Behavior** - What actually happens
5. **Environment** - OS, Python version, Clicker version
6. **Logs** - Relevant error messages or logs

### Example Bug Report

```markdown
## Bug: Hotkeys stop working after system sleep

**Steps to Reproduce:**
1. Start Clicker with hotkey set to 'F1'
2. Put system to sleep
3. Wake system
4. Try pressing F1

**Expected:** Hotkey should still work
**Actual:** Hotkey doesn't respond

**Environment:**
- OS: Windows 11
- Python: 3.11.5
- Clicker: 2.1.0

**Logs:**
```
2024-01-01 10:00:00 - ERROR - Hotkey registration failed after wake
```

## 💡 Feature Requests

### Good Feature Requests Include

1. **Use Case** - Why is this needed?
2. **Description** - What should it do?
3. **Implementation Ideas** - How might it work?
4. **Alternatives** - Other ways to solve the problem?

## 🏆 Recognition

Contributors are recognized through:
- GitHub contributor list
- Release notes mentions
- Special recognition for major contributions

## 📞 Getting Help

### Development Questions

- **GitHub Discussions** - General development questions
- **Issues** - Bug reports and feature requests
- **Code Comments** - Ask questions in PR reviews

### Resources

- **Architecture Guide**: `docs/dev/architecture.md`
- **API Documentation**: `docs/API.md`
- **Configuration Guide**: `docs/configuration.md`

Thank you for contributing to Clicker! 🎉 