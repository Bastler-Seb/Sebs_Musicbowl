"""
UI Module

This module provides the user interface abstractions for the music player.
It separates the UI logic from the audio playback logic, allowing different
UI implementations (terminal, GUI, web, etc.) to be used interchangeably.
"""

from .ui_interface import UIInterface
from .terminal_ui import TerminalUI

__all__ = ['UIInterface', 'TerminalUI']
