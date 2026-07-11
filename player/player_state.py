"""
Player State Module

Defines the data structures and enums for player state management.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from pathlib import Path


class PlaybackStatus(Enum):
    """Enum representing the current playback status."""
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    FINISHED = auto()
    ERROR = auto()


@dataclass
class PlayerState:
    """Immutable state of the player at a point in time."""
    
    # Current file being played
    current_file: Optional[Path] = None
    
    # Current playback status
    status: PlaybackStatus = PlaybackStatus.STOPPED
    
    # Current volume (0.0 to 1.0)
    volume: float = 0.7
    
    # Current position in seconds (if available)
    position: float = 0.0
    
    # Duration in seconds (if available)
    duration: float = 0.0
    
    # Error message if status is ERROR
    error_message: Optional[str] = None
    
    def is_playing(self) -> bool:
        """Check if the player is currently playing."""
        return self.status == PlaybackStatus.PLAYING
    
    def is_paused(self) -> bool:
        """Check if the player is currently paused."""
        return self.status == PlaybackStatus.PAUSED
    
    def is_stopped(self) -> bool:
        """Check if the player is stopped (not playing and not paused)."""
        return self.status in (PlaybackStatus.STOPPED, PlaybackStatus.FINISHED)
    
    def has_error(self) -> bool:
        """Check if there's an error state."""
        return self.status == PlaybackStatus.ERROR
