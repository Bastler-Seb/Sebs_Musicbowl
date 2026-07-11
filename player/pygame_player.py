"""
Pygame Player Implementation

Concrete implementation of PlayerInterface using pygame for audio playback.
"""

import time

import pygame
from pathlib import Path
from typing import Optional

from .player_interface import PlayerInterface
from .player_state import PlayerState, PlaybackStatus


class PygamePlayer(PlayerInterface):
    """
    Pygame-based implementation of the PlayerInterface.
    
    This class handles audio playback using pygame's mixer module.
    """
    
    DEFAULT_VOLUME: float = 0.7
    VOLUME_MIN: float = 0.0
    VOLUME_MAX: float = 1.0
    VOLUME_STEP: float = 0.1
    
    # Class-level flag to track if pygame is initialized
    _pygame_initialized: bool = False
    
    def __init__(self):
        """Initialize the pygame player."""
        super().__init__()
        self._current_file: Optional[Path] = None
        self._volume: float = self.DEFAULT_VOLUME
        self._paused: bool = False
        self._playing: bool = False
        self._state: PlayerState = PlayerState()
        self._start_time: float = 0.0
        self._pause_time: float = 0.0
        self._duration: float = 0.0
        
        # Initialize pygame mixer (only once per class)
        self._initialize_pygame()
    
    def _initialize_pygame(self) -> None:
        """Initialize pygame and pygame.mixer if not already done."""
        if not PygamePlayer._pygame_initialized:
            try:
                pygame.init()
                pygame.mixer.init()
                PygamePlayer._pygame_initialized = True
            except pygame.error as e:
                # Create error state
                self._state = PlayerState(
                    status=PlaybackStatus.ERROR,
                    error_message=str(e)
                )
                raise
    
    def _get_audio_duration(self, filepath: str) -> float:
        """Get the duration of an audio file in seconds."""
        try:
            # Try using pygame's Sound class to get duration
            sound = pygame.mixer.Sound(filepath)
            duration = sound.get_length()
            sound = None  # Clean up
            return duration
        except Exception:
            # If Sound fails, return 0
            return 0.0
    
    def play(self, file_path: Path) -> bool:
        """
        Start playing the specified audio file.
        
        Args:
            file_path: Path to the audio file to play.
            
        Returns:
            True if playback started successfully, False otherwise.
        """
        try:
            # Convert to string for pygame
            filepath_str = str(file_path)
            
            # Stop current playback
            self.stop()
            
            # Try to get duration using pygame's Sound class
            self._duration = self._get_audio_duration(filepath_str)
            
            # Load and play the file
            pygame.mixer.music.load(filepath_str)
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.play()
            
            self._current_file = file_path
            self._playing = True
            self._paused = False
            self._start_time = time.time()
            
            # Update state
            self._state = PlayerState(
                current_file=file_path,
                status=PlaybackStatus.PLAYING,
                volume=self._volume,
                position=0.0,
                duration=self._duration
            )
            self._notify_state_change(self._state)
            
            return True
            
        except pygame.error as e:
            self._state = PlayerState(
                status=PlaybackStatus.ERROR,
                error_message=str(e)
            )
            self._notify_state_change(self._state)
            return False
    
    def pause(self) -> bool:
        """
        Pause the current playback.
        
        Returns:
            True if pause was successful, False otherwise.
        """
        if not PygamePlayer._pygame_initialized or not self._playing:
            return False
            
        try:
            # Update position before pausing (while still playing)
            self._state.position = self.get_position()
            pygame.mixer.music.pause()
            self._paused = True
            self._playing = False
            self._pause_time = time.time()
            self._state.status = PlaybackStatus.PAUSED
            self._notify_state_change(self._state)
            return True
        except pygame.error:
            return False
    
    def resume(self) -> bool:
        """
        Resume paused playback.
        
        Returns:
            True if resume was successful, False otherwise.
        """
        if not PygamePlayer._pygame_initialized or not self._paused:
            return False
            
        try:
            pygame.mixer.music.unpause()
            self._paused = False
            self._playing = True
            # Adjust start time by the duration of the pause
            self._start_time = self._start_time + (time.time() - self._pause_time)
            
            self._state.status = PlaybackStatus.PLAYING
            self._notify_state_change(self._state)
            return True
        except pygame.error:
            return False
    
    def stop(self) -> bool:
        """
        Stop the current playback.
        
        Returns:
            True if stop was successful, False otherwise.
        """
        if not PygamePlayer._pygame_initialized:
            return False
            
        try:
            pygame.mixer.music.stop()
            self._playing = False
            self._paused = False
            self._start_time = 0.0
            self._pause_time = 0.0
            
            self._state.status = PlaybackStatus.STOPPED
            self._state.position = 0.0
            self._notify_state_change(self._state)
            return True
        except pygame.error:
            return False
    
    def toggle_pause(self) -> bool:
        """
        Toggle between pause and resume.
        
        Returns:
            True if toggle was successful, False otherwise.
        """
        if self._paused:
            return self.resume()
        elif self._playing:
            return self.pause()
        return False
    
    def set_volume(self, volume: float) -> bool:
        """
        Set the volume level.
        
        Args:
            volume: Volume level (0.0 to 1.0).
            
        Returns:
            True if volume was set successfully, False otherwise.
        """
        volume = max(self.VOLUME_MIN, min(self.VOLUME_MAX, volume))
        self._volume = volume
        
        if PygamePlayer._pygame_initialized:
            try:
                pygame.mixer.music.set_volume(volume)
            except pygame.error:
                return False
        
        self._state.volume = volume
        self._notify_state_change(self._state)
        return True
    
    def get_volume(self) -> float:
        """
        Get the current volume level.
        
        Returns:
            Current volume level (0.0 to 1.0).
        """
        return self._volume
    
    def increase_volume(self, step: float = 0.1) -> float:
        """
        Increase the volume by a step.
        
        Args:
            step: Amount to increase volume by (default 0.1).
            
        Returns:
            The new volume level.
        """
        new_volume = min(self.VOLUME_MAX, self._volume + step)
        self.set_volume(new_volume)
        return new_volume
    
    def decrease_volume(self, step: float = 0.1) -> float:
        """
        Decrease the volume by a step.
        
        Args:
            step: Amount to decrease volume by (default 0.1).
            
        Returns:
            The new volume level.
        """
        new_volume = max(self.VOLUME_MIN, self._volume - step)
        self.set_volume(new_volume)
        return new_volume
    
    def get_state(self) -> PlayerState:
        """
        Get the current player state.
        
        Returns:
            The current PlayerState object.
        """
        # Update playing status based on pygame
        if PygamePlayer._pygame_initialized:
            busy = pygame.mixer.music.get_busy()
            if busy and not self._paused:
                self._state.status = PlaybackStatus.PLAYING
                self._playing = True
            elif self._paused:
                self._state.status = PlaybackStatus.PAUSED
            elif not busy and self._state.status != PlaybackStatus.STOPPED:
                self._state.status = PlaybackStatus.FINISHED
                self._playing = False
        
        # Update position from tracking
        self._state.position = self.get_position()
        self._state.duration = self._duration
        
        return self._state
    
    def seek(self, position: float) -> bool:
        """
        Seek to a specific position in the current track.
        
        Note: Pygame doesn't natively support seeking in all formats.
        This is a limitation of the pygame backend.
        
        Args:
            position: Position in seconds.
            
        Returns:
            True if seek was successful, False otherwise.
        """
        # Pygame doesn't have a reliable seek function for pygame.mixer.music
        return False
    
    def get_position(self) -> float:
        """
        Get the current playback position in seconds.
        
        Returns:
            Current position in seconds, or 0.0 if not available.
        """
        if self._playing and not self._paused and self._start_time > 0:
            elapsed = time.time() - self._start_time
            # Clamp to duration if we have one
            if self._duration > 0:
                return min(elapsed, self._duration)
            return elapsed
        elif self._paused:
            # When paused, return the stored position from the state
            return self._state.position
        return 0.0
    
    def get_duration(self) -> float:
        """
        Get the duration of the current track in seconds.
        
        Returns:
            Duration in seconds, or 0.0 if not available.
        """
        return self._duration
    
    def is_playing(self) -> bool:
        """
        Check if the player is currently playing.
        
        Returns:
            True if playing, False otherwise.
        """
        return self._playing and not self._paused
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the player.
        """
        if PygamePlayer._pygame_initialized:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                pygame.quit()
                PygamePlayer._pygame_initialized = False
            except pygame.error:
                pass
        
        self._playing = False
        self._paused = False
        self._current_file = None
        self._state = PlayerState()
