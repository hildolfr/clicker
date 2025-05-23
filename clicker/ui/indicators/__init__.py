"""
Visual Indicators for Clicker Application.

Provides visual feedback about automation status.
"""

from .base import VisualIndicator
from .gdi_indicator import GDIIndicator
from .pygame_indicator import PygameIndicator
from .manager import IndicatorManager

__all__ = [
    'VisualIndicator',
    'GDIIndicator', 
    'PygameIndicator',
    'IndicatorManager'
] 