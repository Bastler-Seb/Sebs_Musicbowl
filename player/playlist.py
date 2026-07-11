"""
Playlist Module

Manages playlist functionality for the music player.
Handles loading audio files from a directory, tracking current position,
and advancing to the next track automatically.
"""

import os
from pathlib import Path
from typing import Optional, List


class PlaylistManager:
    """
    Manages a playlist of audio files and handles track navigation.
    
    This class maintains a list of audio files, the current track index,
    and provides methods to navigate through the playlist.
    """
    
    def __init__(self):
        """Initialize the playlist manager."""
        self._tracks: List[Path] = []
        self._current_index: int = -1
        self._shuffle: bool = False
        self._repeat: bool = False
        self._directory: Optional[str] = None
    
    def load_directory(self, directory: str, start_file: Optional[Path] = None) -> list[Path]:
        """
        Load all audio files from a directory into the playlist.
        
        Args:
            directory: Path to the directory to load audio files from.
            start_file: Optional file to start playing from.
            
        Returns:
            List of audio file paths in the playlist.
        """
        # Import here to avoid circular dependency
        from utils.file_utils import get_directory_contents, AUDIO_EXTENSIONS
        
        self._directory = directory
        self._tracks: List[Path] = []
        
        try:
            items = get_directory_contents(directory)
            # Only include audio files (not directories)
            audio_files: List[Path] = [Path(item['path']) for item in items if item['type'] == 'file']
            
            if audio_files:
                self._tracks = audio_files
                
                # If a start_file is provided, find its index and start from there
                if start_file:
                    start_file_str = str(start_file.resolve())
                    for i, track in enumerate(self._tracks):
                        if str(track.resolve()) == start_file_str:
                            self._current_index = i
                            break
                    else:
                        # Start file not found in directory, start from beginning
                        self._current_index = 0
                else:
                    self._current_index = 0
            
        except Exception as e:
            print(f"Warning: Could not load directory {directory!r}: {e}")
        
        return self._tracks
    
    def append_directory(self, directory: str, start_file: Optional[Path] = None) -> list[Path]:
        """
        Append all audio files from a directory to the playlist.
        
        Args:
            directory: Path to the directory to load audio files from.
            start_file: Optional file to start playing from (if provided, will be set as current).
            
        Returns:
            List of audio file paths that were added.
        """
        # Import here to avoid circular dependency
        from utils.file_utils import get_directory_contents, AUDIO_EXTENSIONS
        
        try:
            items = get_directory_contents(directory)
            # Only include audio files (not directories)
            audio_files: List[Path] = [Path(item['path']) for item in items if item['type'] == 'file']
            
            if audio_files:
                # Remember current index if we have existing tracks
                old_index = self._current_index
                old_count = len(self._tracks)
                
                # Add the new files
                self._tracks.extend(audio_files)
                
                # If a start_file is provided, find its index in the newly added files
                # and set it as current
                if start_file:
                    start_file_str = str(start_file.resolve())
                    for i, track in enumerate(audio_files):
                        if str(track.resolve()) == start_file_str:
                            self._current_index = old_count + i
                            break
                    else:
                        # Start file not found, keep current index
                        pass
                # If no start_file and we had no tracks before, start from beginning
                elif old_count == 0 and old_index == -1:
                    self._current_index = 0
            
            return audio_files
        except Exception as e:
            print(f"Warning: Could not load directory {directory!r}: {e}")
            return []
    
    def add_track(self, file_path: Path) -> None:
        """
        Add a single track to the playlist.
        
        Args:
            file_path: Path to the audio file to add.
        """
        self._tracks.append(file_path)
    
    def clear(self) -> None:
        """Clear the playlist."""
        self._tracks = []
        self._current_index = -1
        self._directory = None
    
    @property
    def tracks(self) -> List[Path]:
        """Get the list of tracks in the playlist."""
        return self._tracks
    
    @property
    def current_track(self) -> Optional[Path]:
        """Get the current track path, or None if no track is selected."""
        if 0 <= self._current_index < len(self._tracks):
            return self._tracks[self._current_index]
        return None
    
    @property
    def current_index(self) -> int:
        """Get the current track index."""
        return self._current_index
    
    @property
    def has_next(self) -> bool:
        """Check if there is a next track available."""
        return self._current_index < len(self._tracks) - 1
    
    @property
    def has_previous(self) -> bool:
        """Check if there is a previous track available."""
        return self._current_index > 0
    
    @property
    def has_tracks(self) -> bool:
        """Check if the playlist has any tracks."""
        return len(self._tracks) > 0
    
    @property
    def track_count(self) -> int:
        """Get the number of tracks in the playlist."""
        return len(self._tracks)
    
    def get_next_track(self) -> Optional[Path]:
        """
        Get the next track in the playlist.
        
        Returns:
            Path to the next track, or None if at the end.
        """
        if self._current_index < len(self._tracks) - 1:
            self._current_index += 1
            return self._tracks[self._current_index]
        elif self._repeat and self._tracks:
            # Repeat from beginning
            self._current_index = 0
            return self._tracks[self._current_index]
        return None
    
    def get_previous_track(self) -> Optional[Path]:
        """
        Get the previous track in the playlist.
        
        Returns:
            Path to the previous track, or None if at the beginning.
        """
        if self._current_index > 0:
            self._current_index -= 1
            return self._tracks[self._current_index]
        return None
    
    def go_to_index(self, index: int) -> Optional[Path]:
        """
        Go to a specific track index in the playlist.
        
        Args:
            index: The track index to go to.
            
        Returns:
            Path to the track at the specified index, or None if invalid.
        """
        if 0 <= index < len(self._tracks):
            self._current_index = index
            return self._tracks[self._current_index]
        return None
    
    def go_to_track(self, file_path: Path) -> Optional[Path]:
        """
        Go to a specific track in the playlist.
        
        Args:
            file_path: Path to the track to find and play.
            
        Returns:
            Path to the track if found, or None if not in playlist.
        """
        for i, track in enumerate(self._tracks):
            if str(track.resolve()) == str(file_path.resolve()):
                self._current_index = i
                return track
        return None
    
    @property
    def is_shuffled(self) -> bool:
        """Check if shuffle mode is enabled."""
        return self._shuffle
    
    @is_shuffled.setter
    def is_shuffled(self, value: bool) -> None:
        """Set shuffle mode."""
        self._shuffle = value
    
    @property
    def is_repeating(self) -> bool:
        """Check if repeat mode is enabled."""
        return self._repeat
    
    @is_repeating.setter
    def is_repeating(self, value: bool) -> None:
        """Set repeat mode."""
        self._repeat = value
    
    def shuffle_playlist(self) -> None:
        """Shuffle the playlist order."""
        import random
        if self._tracks:
            # Fisher-Yates shuffle
            shuffled = self._tracks.copy()
            random.shuffle(shuffled)
            self._tracks = shuffled
            self._current_index = 0
    
    def get_playlist_position(self) -> str:
        """
        Get a formatted string showing the current position in the playlist.
        
        Returns:
            String like "Track 3 of 10".
        """
        if self._current_index >= 0 and self._tracks:
            return f"Track {self._current_index + 1} of {len(self._tracks)}"
        return "No playlist"
