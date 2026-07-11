"""
Pygame Player Implementation

Concrete implementation of PlayerInterface using pygame for audio playback.
"""

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
    
    def __init__(self):
        """Initialize the pygame player."""
        super().__init__()
        self._initialized: bool = False
        self._current_file: Optional[Path] = None
        self._volume: float = self.DEFAULT_VOLUME
        self._paused: bool = False
        self._playing: bool = False
        self._state: PlayerState = PlayerState()
        
        # Initialize pygame mixer
        self._initialize_pygame()
    
    def _initialize_pygame(self) -> None:
        """Initialize pygame and pygame.mixer."""
        if not self._initialized:
            try:
                pygame.init()
                pygame.mixer.init()
                self._initialized = True
            except pygame.error as e:
                # Create error state
                self._state = PlayerState(
                    status=PlaybackStatus.ERROR,
                    error_message=str(e)
                )
                raise
    
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
            
            # Load and play the file
            pygame.mixer.music.load(filepath_str)
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.play()
            
            self._current_file = file_path
            self._playing = True
            self._paused = False
            
            # Update state
            self._state = PlayerState(
                current_file=file_path,
                status=PlaybackStatus.PLAYING,
                volume=self._volume,
                position=0.0,
                duration=0.0  # Pygame doesn't easily provide duration
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
        if not self._initialized or not self._playing:
            return False
            
        try:
            pygame.mixer.music.pause()
            self._paused = True
            self._playing = False
            
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
        if not self._initialized or not self._paused:
            return False
            
        try:
            pygame.mixer.music.unpause()
            self._paused = False
            self._playing = True
            
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
        if not self._initialized:
            return False
            
        try:
            pygame.mixer.music.stop()
            self._playing = False
            self._paused = False
            
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
        
        if self._initialized:
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
        if self._initialized:
            busy = pygame.mixer.music.get_busy()
            if busy and not self._paused:
                self._state.status = PlaybackStatus.PLAYING
                self._playing = True
            elif self._paused:
                self._state.status = PlaybackStatus.PAUSED
            elif not busy and self._state.status != PlaybackStatus.STOPPED:
                self._state.status = PlaybackStatus.FINISHED
                self._playing = False
        
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
        # This would require reloading the file and seeking, which isn't straightforward
        # For now, return False to indicate not supported
        return False
    
    def get_position(self) -> float:
        """
        Get the current playback position in seconds.
        
        Returns:
            Current position in seconds, or 0.0 if not available.
        """
        # Pygame doesn't provide a direct way to get position
        # This is a limitation of the pygame backend
        return 0.0
    
    def get_duration(self) -> float:
        """
        Get the duration of the current track in seconds.
        
        Returns:
            Duration in seconds, or 0.0 if not available.
        """
        # Pygame doesn't provide an easy way to get duration
        # This is a limitation of the pygame backend
        return 0.0
    
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
        if self._initialized:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                pygame.quit()
                self._initialized = False
            except pygame.error:
                pass
        
        self._playing = False
        self._paused = False
        self._current_file = None
        self._state = PlayerState()
