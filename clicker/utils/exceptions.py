"""
Custom exception classes for the Clicker application.

This module provides a hierarchy of exceptions with clear error types
and helpful error messages for debugging and user feedback.
"""

from typing import Optional


class ClickerError(Exception):
    """Base exception for all Clicker-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(ClickerError):
    """Raised when there are configuration-related errors."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, line_number: Optional[int] = None):
        super().__init__(message, "CONFIG_ERROR")
        self.file_path = file_path
        self.line_number = line_number
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        if self.line_number:
            parts.append(f"Line: {self.line_number}")
        return " | ".join(parts)


class AutomationError(ClickerError):
    """Raised when automation operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(message, "AUTOMATION_ERROR")
        self.operation = operation
    
    def __str__(self) -> str:
        if self.operation:
            return f"{self.message} (Operation: {self.operation})"
        return self.message


class KeystrokeError(ClickerError):
    """Raised when keystroke operations fail."""
    
    def __init__(self, message: str, key: Optional[str] = None, error_type: Optional[str] = None):
        super().__init__(message, "KEYSTROKE_ERROR")
        self.key = key
        self.error_type = error_type
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.key:
            parts.append(f"Key: {self.key}")
        if self.error_type:
            parts.append(f"Type: {self.error_type}")
        return " | ".join(parts)


class SystemError(ClickerError):
    """Raised when system-level operations fail."""
    
    def __init__(self, message: str, system_call: Optional[str] = None, error_code: Optional[int] = None):
        super().__init__(message, "SYSTEM_ERROR")
        self.system_call = system_call
        self.system_error_code = error_code
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.system_call:
            parts.append(f"System call: {self.system_call}")
        if self.system_error_code:
            parts.append(f"Error code: {self.system_error_code}")
        return " | ".join(parts)


class ValidationError(ConfigurationError):
    """Raised when configuration validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None):
        super().__init__(message)
        self.field = field
        self.value = value
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.field:
            parts.append(f"Field: {self.field}")
        if self.value:
            parts.append(f"Value: {self.value}")
        return " | ".join(parts)


class ProfileError(ClickerError):
    """Raised when profile operations fail."""
    
    def __init__(self, message: str, profile_name: Optional[str] = None):
        super().__init__(message, "PROFILE_ERROR")
        self.profile_name = profile_name
    
    def __str__(self) -> str:
        if self.profile_name:
            return f"{self.message} (Profile: {self.profile_name})"
        return self.message


class UpdateError(ClickerError):
    """Raised when update operations fail."""
    
    def __init__(self, message: str, version: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message, "UPDATE_ERROR")
        self.version = version
        self.operation = operation
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.version:
            parts.append(f"Version: {self.version}")
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        return " | ".join(parts) 