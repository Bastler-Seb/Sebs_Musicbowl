"""
Player Interface Module

Defines the abstract interface for audio playback controllers.
This allows different implementations (pygame, vlc, etc.) and different
UI frontends (terminal, GUI, etc.) to work together.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Callable, Any
from enum import Enum

from .player_state import PlayerState, PlaybackStatus
from .playlist import PlaylistManager


class PlayerCommand(Enum):
    """Commands that can be sent to the player."""
    PLAY = "play"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    TOGGLE_PAUSE = "toggle_pause"
    SET_VOLUME = "set_volume"
    INCREASE_VOLUME = "increase_volume"
    DECREASE_VOLUME = "decrease_volume"
    SEEK = "seek"
    NEXT = "next"
    PREVIOUS = "previous"
    PLAYLIST_NEXT = "playlist_next"
    PLAYLIST_PREVIOUS = "playlist_previous"
    PLAYLIST_CLEAR = "playlist_clear"


class PlayerInterface(ABC):
    """
    Abstract base class for audio players.
    
    This interface defines the contract between the UI and the audio backend.
    Any implementation (pygame, vlc, gstreamer, etc.) must implement these methods.
    """
    
    def __init__(self):
        """Initialize the player interface."""
        self._state_change_callbacks: list[Callable[[PlayerState], None]] = []
    
    @abstractmethod
    def play(self, file_path: Path) -> bool:
        """
        Start playing the specified audio file.
        
        Args:
            file_path: Path to the audio file to play.
            
        Returns:
            True if playback started successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    def pause(self) -> bool:
        """
        Pause the current playback.
        
        Returns:
            True if pause was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def resume(self) -> bool:
        """
        Resume paused playback.
        
        Returns:
            True if resume was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        Stop the current playback.
        
        Returns:
            True if stop was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def toggle_pause(self) -> bool:
        """
        Toggle between pause and resume.
        
        Returns:
            True if toggle was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def set_volume(self, volume: float) -> bool:
        """
        Set the volume level.
        
        Args:
            volume: Volume level (0.0 to 1.0).
            
        Returns:
            True if volume was set successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_volume(self) -> float:
        """
        Get the current volume level.
        
        Returns:
            Current volume level (0.0 to 1.0).
        """
        pass
    
    @abstractmethod
    def increase_volume(self, step: float = 0.1) -> float:
        """
        Increase the volume by a step.
        
        Args:
            step: Amount to increase volume by (default 0.1).
            
        Returns:
            The new volume level.
        """
        pass
    
    @abstractmethod
    def decrease_volume(self, step: float = 0.1) -> float:
        """
        Decrease the volume by a step.
        
        Args:
            step: Amount to decrease volume by (default 0.1).
            
        Returns:
            The new volume level.
        """
        pass
    
    @abstractmethod
    def get_state(self) -> PlayerState:
        """
        Get the current player state.
        
        Returns:
            The current PlayerState object.
        """
        pass
    
    @abstractmethod
    def seek(self, position: float) -> bool:
        """
        Seek to a specific position in the current track.
        
        Args:
            position: Position in seconds.
            
        Returns:
            True if seek was successful, False otherwise.
            
        Note:
            This may not be supported by all backends.
        """
        pass
    
    @abstractmethod
    def get_position(self) -> float:
        """
        Get the current playback position in seconds.
        
        Returns:
            Current position in seconds, or 0.0 if not available.
        """
        pass
    
    @abstractmethod
    def get_duration(self) -> float:
        """
        Get the duration of the current track in seconds.
        
        Returns:
            Duration in seconds, or 0.0 if not available.
        """
        pass
    
    @abstractmethod
    def is_playing(self) -> bool:
        """
        Check if the player is currently playing.
        
        Returns:
            True if playing, False otherwise.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up resources used by the player.
        
        This should be called when the player is no longer needed.
        """
        pass

    @abstractmethod
    def get_playlist_manager(self) -> "PlaylistManager":
        """
        Get the playlist manager instance.
        
        Returns:
            The PlaylistManager instance.
        """
        pass
    
    @abstractmethod
    def play_playlist(self, directory: str, start_file: Optional[Path] = None) -> bool:
        """
        Load a directory as a playlist and start playing from a specific file.
        
        Args:
            directory: Path to the directory containing audio files.
            start_file: Optional file to start playing from.
            
        Returns:
            True if playlist was loaded and playback started successfully.
        """
        pass
    
    @abstractmethod
    def append_to_playlist(self, directory: str, start_file: Optional[Path] = None) -> bool:
        """
        Append all audio files from a directory to the current playlist.
        
        Args:
            directory: Path to the directory containing audio files.
            start_file: Optional file to append and set as current.
            
        Returns:
            True if files were appended successfully.
        """
        pass
    
    @abstractmethod
    def next_track(self) -> bool:
        """
        Skip to the next track in the playlist.
        
        Returns:
            True if there was a next track and it was loaded successfully.
        """
        pass
    
    @abstractmethod
    def previous_track(self) -> bool:
        """
        Go to the previous track in the playlist.
        
        Returns:
            True if there was a previous track and it was loaded successfully.
        """
        pass
    
    @abstractmethod
    def clear_playlist(self) -> None:
        """Clear the current playlist."""
        pass
    
    def on_state_change(self, callback: Callable[[PlayerState], None]) -> None:
        """
        Register a callback to be called when the player state changes.
        
        Args:
            callback: Function to call with the new PlayerState.
        """
        self._state_change_callbacks.append(callback)
    
    def _notify_state_change(self, state: PlayerState) -> None:
        """
        Notify all registered callbacks of a state change.
        
        Args:
            state: The new PlayerState.
        """
        for callback in self._state_change_callbacks:
            try:
                callback(state)
            except Exception:
                # Don't let callback errors affect the player
                pass
