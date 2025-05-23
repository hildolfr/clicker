"""
Enhanced input validation utilities for the Clicker application.

This module provides comprehensive validation functions for file paths, 
user inputs, and security-sensitive data.
"""

import re
import os
from pathlib import Path
from typing import Optional, Set, List
import unicodedata


class ValidationError(Exception):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None):
        super().__init__(message)
        self.field = field
        self.value = value


class InputValidator:
    """Comprehensive input validation utilities."""
    
    # Reserved Windows filenames
    WINDOWS_RESERVED_NAMES: Set[str] = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
        'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
        'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    # Dangerous characters for filenames
    DANGEROUS_FILENAME_CHARS: Set[str] = {
        '<', '>', ':', '"', '|', '?', '*', '/', '\\', '\x00'
    }
    
    # Control characters (ASCII 0-31 except allowed ones)
    ALLOWED_CONTROL_CHARS: Set[str] = {'\t', '\n', '\r'}
    
    @staticmethod
    def validate_filename(filename: str, max_length: int = 255, allow_unicode: bool = True) -> str:
        """
        Validate and sanitize a filename.
        
        Args:
            filename: The filename to validate
            max_length: Maximum allowed length
            allow_unicode: Whether to allow Unicode characters
            
        Returns:
            Sanitized filename
            
        Raises:
            ValidationError: If the filename is invalid
        """
        if not isinstance(filename, str):
            raise ValidationError("Filename must be a string", "filename", str(type(filename)))
        
        if not filename or not filename.strip():
            raise ValidationError("Filename cannot be empty", "filename", filename)
        
        filename = filename.strip()
        
        # Length check
        if len(filename) > max_length:
            raise ValidationError(
                f"Filename cannot exceed {max_length} characters", 
                "filename", 
                f"{filename[:50]}..." if len(filename) > 50 else filename
            )
        
        # Check for reserved names
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in InputValidator.WINDOWS_RESERVED_NAMES:
            raise ValidationError(
                f"Filename '{filename}' uses a reserved system name", 
                "filename", 
                filename
            )
        
        # Check for dangerous characters
        dangerous_found = [char for char in filename if char in InputValidator.DANGEROUS_FILENAME_CHARS]
        if dangerous_found:
            raise ValidationError(
                f"Filename contains dangerous characters: {dangerous_found}", 
                "filename", 
                filename
            )
        
        # Check for control characters
        control_chars = [char for char in filename 
                        if ord(char) < 32 and char not in InputValidator.ALLOWED_CONTROL_CHARS]
        if control_chars:
            raise ValidationError(
                f"Filename contains invalid control characters", 
                "filename", 
                filename
            )
        
        # Unicode normalization and validation
        if allow_unicode:
            try:
                filename = unicodedata.normalize('NFC', filename)
            except Exception:
                raise ValidationError("Filename contains invalid Unicode characters", "filename", filename)
        else:
            # Check for non-ASCII characters
            if not filename.isascii():
                raise ValidationError("Filename contains non-ASCII characters", "filename", filename)
        
        # Additional safety checks
        if filename.startswith('.') and len(filename) > 1:
            # Hidden files are allowed but logged
            pass
        
        if filename.endswith('.'):
            raise ValidationError("Filename cannot end with a period", "filename", filename)
        
        if '  ' in filename:  # Multiple consecutive spaces
            raise ValidationError("Filename cannot contain multiple consecutive spaces", "filename", filename)
        
        return filename
    
    @staticmethod
    def validate_file_path(file_path: str, must_exist: bool = False, must_be_file: bool = True) -> Path:
        """
        Validate a file path for security and accessibility.
        
        Args:
            file_path: The file path to validate
            must_exist: Whether the path must exist
            must_be_file: Whether the path must be a file (vs directory)
            
        Returns:
            Resolved Path object
            
        Raises:
            ValidationError: If the path is invalid or unsafe
        """
        if not isinstance(file_path, (str, Path)):
            raise ValidationError("File path must be a string or Path", "file_path", str(type(file_path)))
        
        try:
            path = Path(file_path)
        except Exception as e:
            raise ValidationError(f"Invalid path format: {e}", "file_path", str(file_path))
        
        # Convert to absolute path for security checks
        try:
            resolved_path = path.resolve()
        except (OSError, RuntimeError) as e:
            raise ValidationError(f"Cannot resolve path: {e}", "file_path", str(file_path))
        
        # Check path length (Windows limitation)
        if len(str(resolved_path)) > 260:
            raise ValidationError("Path too long (Windows limit: 260 characters)", "file_path", str(file_path))
        
        # Security check: prevent directory traversal
        if '..' in str(path):
            raise ValidationError("Path contains directory traversal", "file_path", str(file_path))
        
        # Validate each component of the path
        for part in path.parts:
            if part in ('', '.', '..'):
                continue
            try:
                InputValidator.validate_filename(part, allow_unicode=True)
            except ValidationError as e:
                raise ValidationError(f"Invalid path component '{part}': {e}", "file_path", str(file_path))
        
        # Existence checks
        if must_exist and not resolved_path.exists():
            raise ValidationError("Path does not exist", "file_path", str(file_path))
        
        if must_exist and must_be_file and not resolved_path.is_file():
            raise ValidationError("Path is not a file", "file_path", str(file_path))
        
        if must_exist and not must_be_file and not resolved_path.is_dir():
            raise ValidationError("Path is not a directory", "file_path", str(file_path))
        
        return resolved_path
    
    @staticmethod
    def validate_string_input(
        value: str, 
        field_name: str,
        max_length: int,
        allow_empty: bool = False,
        pattern: Optional[str] = None,
        whitelist_chars: Optional[Set[str]] = None
    ) -> str:
        """
        Validate a string input with comprehensive checks.
        
        Args:
            value: The string to validate
            field_name: Name of the field for error messages
            max_length: Maximum allowed length
            allow_empty: Whether empty strings are allowed
            pattern: Optional regex pattern to match
            whitelist_chars: Optional set of allowed characters
            
        Returns:
            Validated and sanitized string
            
        Raises:
            ValidationError: If the string is invalid
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string", field_name, str(type(value)))
        
        # Empty check
        if not allow_empty and (not value or not value.strip()):
            raise ValidationError(f"{field_name} cannot be empty", field_name, value)
        
        value = value.strip()
        
        # Length check
        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} cannot exceed {max_length} characters", 
                field_name, 
                f"{value[:50]}..." if len(value) > 50 else value
            )
        
        # Control character check
        control_chars = [char for char in value 
                        if ord(char) < 32 and char not in InputValidator.ALLOWED_CONTROL_CHARS]
        if control_chars:
            raise ValidationError(
                f"{field_name} contains invalid control characters", 
                field_name, 
                value
            )
        
        # Pattern validation
        if pattern and not re.match(pattern, value):
            raise ValidationError(
                f"{field_name} does not match required format", 
                field_name, 
                value
            )
        
        # Character whitelist validation
        if whitelist_chars:
            invalid_chars = [char for char in value if char not in whitelist_chars]
            if invalid_chars:
                raise ValidationError(
                    f"{field_name} contains invalid characters: {invalid_chars[:10]}", 
                    field_name, 
                    value
                )
        
        return value
    
    @staticmethod
    def validate_numeric_input(
        value: float, 
        field_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        allow_integer_only: bool = False
    ) -> float:
        """
        Validate a numeric input.
        
        Args:
            value: The numeric value to validate
            field_name: Name of the field for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_integer_only: Whether only integers are allowed
            
        Returns:
            Validated numeric value
            
        Raises:
            ValidationError: If the value is invalid
        """
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field_name} must be numeric", field_name, str(value))
        
        if allow_integer_only and not isinstance(value, int):
            raise ValidationError(f"{field_name} must be an integer", field_name, str(value))
        
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"{field_name} cannot be less than {min_value}", 
                field_name, 
                str(value)
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{field_name} cannot be greater than {max_value}", 
                field_name, 
                str(value)
            )
        
        return value
    
    @staticmethod
    def sanitize_for_log(value: str, max_length: int = 100) -> str:
        """
        Sanitize a string for safe logging.
        
        Args:
            value: The string to sanitize
            max_length: Maximum length for the output
            
        Returns:
            Sanitized string safe for logging
        """
        if not isinstance(value, str):
            return str(value)[:max_length]
        
        # Remove control characters except newlines and tabs
        sanitized = ''.join(char if ord(char) >= 32 or char in '\n\t' else '?' for char in value)
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length-3] + "..."
        
        return sanitized
    
    @staticmethod
    def validate_json_data_size(data: str, max_size: int = 10000) -> bool:
        """
        Validate JSON data size to prevent DoS attacks.
        
        Args:
            data: The JSON string data
            max_size: Maximum allowed size in characters
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If the data is too large
        """
        if len(data) > max_size:
            raise ValidationError(
                f"JSON data too large ({len(data)} chars, max {max_size})", 
                "json_data", 
                f"{data[:100]}..." if len(data) > 100 else data
            )
        
        return True
    
    @staticmethod
    def is_safe_for_shell(value: str) -> bool:
        """
        Check if a string is safe to use in shell commands.
        
        Args:
            value: The string to check
            
        Returns:
            True if safe for shell use
        """
        # Characters that could be dangerous in shell context
        dangerous_shell_chars = {
            ';', '&', '|', '`', '$', '(', ')', '<', '>', '"', "'", 
            '\\', '\n', '\r', '\t'
        }
        
        return not any(char in dangerous_shell_chars for char in value)


# Convenience functions for common validations
def validate_profile_name(name: str) -> str:
    """Validate a profile name."""
    return InputValidator.validate_string_input(
        name, 
        "profile_name", 
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\s]+$'
    )


def validate_keystroke_key(key: str) -> str:
    """Validate a keystroke key string."""
    return InputValidator.validate_string_input(
        key,
        "keystroke_key",
        max_length=50,
        pattern=r'^[a-zA-Z0-9\-]+$'
    )


def validate_config_file_path(path: str) -> Path:
    """Validate a configuration file path."""
    return InputValidator.validate_file_path(
        path,
        must_exist=False,
        must_be_file=True
    )


def validate_update_channel(channel: str) -> str:
    """Validate an update channel string."""
    valid_channels = {'stable', 'beta', 'dev'}
    validated = InputValidator.validate_string_input(
        channel,
        "update_channel",
        max_length=20
    ).lower()
    
    if validated not in valid_channels:
        raise ValidationError(
            f"Invalid update channel: {channel}",
            "update_channel",
            channel
        )
    
    return validated 