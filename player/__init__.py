"""
Player Module

This module provides the audio playback functionality with a clean abstraction
that allows different UI implementations (terminal, GUI, etc.) to control playback.
"""

from .player_interface import PlayerInterface
from .pygame_player import PygamePlayer
from .player_state import PlayerState, PlaybackStatus
from .playlist import PlaylistManager

__all__ = ['PlayerInterface', 'PygamePlayer', 'PlayerState', 'PlaybackStatus', 'PlaylistManager']
