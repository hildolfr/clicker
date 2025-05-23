# Architecture Overview

Technical overview of Clicker's architecture and design patterns.

## 🏗️ Architecture Overview

Clicker follows a clean, modular architecture with clear separation of concerns and dependency injection patterns.

### Core Principles

- **Dependency Injection**: Components receive their dependencies through constructors
- **Event-Driven Architecture**: Loose coupling through event system
- **Single Responsibility**: Each module has a focused purpose  
- **Clean Architecture**: Business logic separated from UI and system concerns
- **Testability**: Designed for easy unit and integration testing

## 📦 Module Structure

```
clicker/
├── app.py              # Main application orchestrator
├── __init__.py         # Package initialization
├── core/               # Core business logic
│   ├── automation.py   # Automation engine
│   ├── keystrokes.py   # Keystroke sending
│   └── events.py       # Event system
├── config/             # Configuration management
│   ├── manager.py      # Configuration manager
│   ├── models.py       # Data models
│   └── enums.py        # Enumerations
├── ui/                 # User interface
│   ├── gui/            # GUI components
│   └── indicators/     # Visual indicators
├── system/             # System integration
│   ├── hotkeys.py      # Global hotkey management
│   ├── admin.py        # Administrator checks
│   ├── singleton.py    # Single instance management
│   └── windows_api.py  # Windows API utilities
├── utils/              # Utility modules
│   ├── exceptions.py   # Custom exceptions
│   ├── file_watcher.py # File monitoring
│   └── updater.py      # Auto-update system
├── plugins/            # Plugin system
└── cli/                # Command-line interface
    └── profile_manager.py
```

## 🎛️ Core Components

### Application Layer (app.py)

The main `ClickerApp` class orchestrates all components:

```python
class ClickerApp:
    def __init__(self, config_dir: Optional[Path] = None):
        # Core dependencies
        self.config_manager = ConfigManager(config_dir)
        self.event_system = EventSystem()
        self.keystroke_sender = WindowsKeystrokeSender()
        self.automation_engine = AutomationEngine(self.keystroke_sender)
        
        # System utilities
        self.admin_checker = AdminChecker()
        self.singleton_manager = SingletonManager()
        self.hotkey_manager = HotkeyManager(self.event_system)
```

**Responsibilities:**
- Dependency injection and wiring
- Application lifecycle management
- Startup and shutdown sequences
- Error handling and recovery

### Configuration Layer (config/)

Centralized configuration management with validation:

```python
class ConfigManager:
    def __init__(self, config_dir: Path = None):
        self._settings: AppSettings
        self._keystrokes: List[KeystrokeConfig]
        self._change_callbacks: List[Callable]
```

**Key Features:**
- Type-safe configuration models
- Automatic validation and migration
- Change notification system
- Backup and recovery

### Core Business Logic (core/)

#### Automation Engine

```python
class AutomationEngine:
    def __init__(self, keystroke_sender: KeystrokeSender):
        self.state = AutomationState.STOPPED
        self.scheduler = AsyncScheduler()
        self.executor = ThreadPoolExecutor()
```

**Responsibilities:**
- Keystroke scheduling and execution
- State management (stopped, running, paused)
- Performance optimization
- Error handling and recovery

#### Event System

```python
class EventSystem:
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]]
        self._event_queue: Queue[AutomationEvent]
```

**Features:**
- Decoupled component communication
- Type-safe event handling
- Asynchronous event processing
- Weak reference management

## 🔄 Data Flow

### Startup Sequence

1. **Initialize Core Components**
   ```
   ConfigManager → EventSystem → KeystrokeSender → AutomationEngine
   ```

2. **Load Configuration**
   ```
   settings.json → AppSettings → Validation → Configuration Manager
   keystrokes.txt → KeystrokeConfig[] → Validation → Automation Engine
   ```

3. **Initialize UI & System Integration**
   ```
   Qt Application → System Tray → Visual Indicators → Hotkey Manager
   ```

4. **Start Event Loop**
   ```
   Qt Event Loop → File Watching → Auto-Updates → User Interaction
   ```

### Automation Flow

1. **Trigger** (Hotkey or UI)
2. **State Change** (AutomationEngine)
3. **Event Emission** (EventSystem)
4. **UI Update** (Visual indicators, system tray)
5. **Keystroke Scheduling** (Scheduler)
6. **Keystroke Execution** (KeystrokeSender)
7. **Event Logging** (EventSystem)

## 🔌 Plugin Architecture

### Plugin Discovery

```python
class PluginManager:
    def discover_plugins(self) -> List[Plugin]:
        # Scan plugin directories
        # Load plugin modules
        # Instantiate plugin classes
        # Register with event system
```

### Plugin Lifecycle

1. **Discovery** - Scan plugin directories
2. **Loading** - Import plugin modules
3. **Instantiation** - Create plugin objects
4. **Initialization** - Call plugin.initialize()
5. **Configuration** - Apply plugin settings
6. **Event Registration** - Subscribe to events
7. **Runtime** - Handle events and provide services
8. **Cleanup** - Unsubscribe and cleanup resources

## 🏛️ Design Patterns

### Dependency Injection

Components receive dependencies through constructors rather than creating them:

```python
class AutomationEngine:
    def __init__(self, keystroke_sender: KeystrokeSender):
        self.keystroke_sender = keystroke_sender  # Injected dependency
```

**Benefits:**
- Easier testing with mocks
- Loose coupling between components
- Clear dependency relationships

### Observer Pattern (Event System)

Components communicate through events rather than direct calls:

```python
# Publisher
self.event_system.emit(EventType.AUTOMATION_STARTED, data)

# Subscriber  
self.event_system.subscribe(EventType.AUTOMATION_STARTED, self.handle_start)
```

**Benefits:**
- Decoupled components
- Easy to add new features
- Plugin-friendly architecture

### Strategy Pattern (Keystroke Senders)

Multiple implementations of keystroke sending:

```python
class KeystrokeSender(Protocol):
    def send_keystroke(self, key: str) -> bool: ...

class WindowsKeystrokeSender(KeystrokeSender): ...
class SendKeysKeystrokeSender(KeystrokeSender): ...
```

### State Pattern (Automation States)

Automation engine behavior changes based on state:

```python
class AutomationState(Enum):
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
```

## 🔒 Error Handling Strategy

### Exception Hierarchy

```python
class ClickerError(Exception): ...
class ConfigurationError(ClickerError): ...
class AutomationError(ClickerError): ...
class UpdateError(ClickerError): ...
```

### Error Recovery

1. **Graceful Degradation** - Continue with reduced functionality
2. **Automatic Retry** - Retry failed operations with backoff
3. **State Reset** - Return to known good state on critical errors
4. **User Notification** - Inform user of issues and solutions

### Logging Strategy

```python
# Structured logging with context
self.logger.error(f"Failed to send keystroke '{key}': {error}", extra={
    'key': key,
    'error_type': type(error).__name__,
    'automation_state': self.state.name
})
```

## 🧪 Testing Architecture

### Test Structure

```
tests/
├── unit/               # Unit tests for individual components
├── integration/        # Integration tests for component interaction
├── conftest.py        # Shared test fixtures
└── test_*.py          # Test modules
```

### Testing Patterns

**Dependency Injection for Testing:**
```python
def test_automation_engine():
    mock_sender = Mock(spec=KeystrokeSender)
    engine = AutomationEngine(mock_sender)
    # Test with mock
```

**Event System Testing:**
```python
def test_event_handling():
    event_system = EventSystem()
    handler = Mock()
    event_system.subscribe(EventType.TEST, handler)
    event_system.emit_simple(EventType.TEST, "source", {})
    handler.assert_called_once()
```

## 📈 Performance Considerations

### Threading Model

- **Main Thread**: Qt event loop and UI
- **Worker Threads**: Keystroke execution
- **Background Thread**: File watching and updates

### Memory Management

- **Configuration Caching**: Settings cached in memory
- **Event Queue**: Bounded queue to prevent memory leaks
- **Weak References**: Plugin system uses weak references

### Optimization Techniques

- **Lazy Loading**: Components loaded on demand
- **Connection Pooling**: Reuse system resources
- **Batch Operations**: Group similar operations
- **Efficient Scheduling**: Optimized timer management

## 🔧 Extension Points

### Adding New Features

1. **Create Module** in appropriate package
2. **Define Interface** if needed
3. **Implement Logic** following patterns
4. **Add Configuration** if needed
5. **Emit Events** for notifications
6. **Add Tests** for functionality
7. **Update Documentation**

### Plugin Development

Plugins can extend:
- **Event Handling** - React to automation events
- **Configuration** - Add custom settings
- **UI Elements** - Add indicators or controls
- **Automation Logic** - Custom keystroke behaviors

## 📚 References

- **Configuration Models**: `clicker/config/models.py`
- **Event Types**: `clicker/core/events.py`
- **API Documentation**: `docs/API.md`
- **Plugin Guide**: `docs/dev/plugins.md` 