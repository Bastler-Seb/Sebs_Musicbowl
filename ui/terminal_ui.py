"""
Terminal UI Implementation

Concrete implementation of UIInterface for terminal-based interaction.
This includes a split-screen layout with file tree on the left and player on the right.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

import pygame
import curses

from player.player_interface import PlayerInterface
from player.player_state import PlayerState, PlaybackStatus
from .ui_interface import UIInterface

# Import utilities
from utils.file_utils import (
    AUDIO_EXTENSIONS, FileItem, get_directory_contents, 
    validate_audio_filepath, clear_screen, extract_audio_metadata
)
from utils.input_utils import read_key
from utils.settings import get_settings


# Constants
DEFAULT_VOLUME: float = 0.7
VOLUME_STEP: float = 0.1
VOLUME_MIN: float = 0.0
VOLUME_MAX: float = 1.0
SCROLL_STEP: int = 10
MIN_WIDTH: int = 50

# Split screen ratio (left: 60%, right: 40%)
SPLIT_RATIO: float = 0.6


class TerminalUI(UIInterface):
    """
    Terminal-based implementation of the UIInterface.
    
    Features a split-screen layout with file tree on the left and player on the right.
    Allows navigation in the file tree even while music is playing.
    """
    
    def __init__(self):
        """Initialize the terminal UI."""
        self._start_dir: Optional[str] = None
        self._current_player: Optional[PlayerInterface] = None
        self._stdscr: Optional[curses.window] = None
        self._current_dir: str = ""
        self._selected_index: int = 0
        self._scroll_position: int = 0
        self._items: list[FileItem] = []
        self._settings_dialog_active: bool = False
        self._settings_input: str = ""
        self._playlist_scroll_position: int = 0
        self._focus_on_playlist: bool = False
        self._playlist_selected_index: int = 0
    
    def run(self, player: PlayerInterface, start_file: Optional[Path] = None) -> None:
        """
        Run the main terminal UI loop with split-screen layout.
        
        Args:
            player: The player instance to control.
            start_file: Optional file to play immediately on start.
        """
        self._current_player = player
        
        # Setup curses
        self._setup_curses()
        
        try:
            # Set initial directory - use settings default if available
            settings = get_settings()
            default_dir = settings.get_default_directory()
            self._current_dir = self._start_dir if self._start_dir else default_dir
            self._load_items()
            
            # If a start file is provided, play it
            if start_file is not None:
                if validate_audio_filepath(str(start_file)):
                    self._current_player.play(start_file)
            
            # Main loop
            self._main_loop()
        finally:
            self._cleanup_curses()
    
    def _setup_curses(self) -> None:
        """Initialize curses for split-screen display."""
        self._stdscr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)
        self._stdscr.keypad(True)
        self._stdscr.timeout(50)
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    
    def _cleanup_curses(self) -> None:
        """Clean up curses resources."""
        if self._stdscr:
            curses.nocbreak()
            curses.echo()
            self._stdscr.keypad(False)
            curses.endwin()
            self._stdscr = None
    
    def _load_items(self) -> None:
        """Load directory contents into self._items."""
        self._items = get_directory_contents(self._current_dir)
        self._selected_index = 0
        self._scroll_position = 0
    
    def _get_split_position(self) -> int:
        """Get the column position for splitting the screen."""
        if self._stdscr is None:
            return 40
        height, width = self._stdscr.getmaxyx()
        return int(width * SPLIT_RATIO)
    
    def _display_split_screen(self) -> None:
        """Display the split screen with file tree on left and player on right."""
        if self._stdscr is None:
            return
        
        self._stdscr.erase()
        height, width = self._stdscr.getmaxyx()
        split_pos = self._get_split_position()
        
        # Draw left panel - File Tree
        self._draw_file_tree(0, 0, height, split_pos)
        
        # Draw right panel - Player Menu
        self._draw_player_menu(0, split_pos + 1, height, width - split_pos - 1)
        
        # Draw separator line
        if split_pos < width - 1:
            for y in range(height):
                try:
                    self._stdscr.addch(y, split_pos, curses.ACS_VLINE)
                except curses.error:
                    pass
        
        self._stdscr.refresh()
    
    def _draw_file_tree(self, y: int, x: int, height: int, width: int) -> None:
        """Draw the file tree browser in the left panel."""
        if width <= 0:
            return
        
        try:
            # Controls hint at the top - break after every | to adapt to window width
            focus_hint = "Playlist Focus" if self._focus_on_playlist else "File Tree Focus"
            controls_str = f"[Up/Down: Nav | Enter: Play | a: Append | Left: Up | TAB: Switch | ESC: Settings | q: Quit] [{focus_hint}]"
            
            # Split by | and display with line breaks as needed
            parts = controls_str.split(" | ")
            current_line = ""
            for part in parts:
                if not current_line:
                    test_line = part
                else:
                    test_line = f"{current_line} | {part}"
                
                if len(test_line) <= width:
                    current_line = test_line
                else:
                    if current_line:
                        self._stdscr.addstr(y, x, current_line[:width])
                        y += 1
                    current_line = part
            
            if current_line:
                self._stdscr.addstr(y, x, current_line[:width])
                y += 1
            
            # Header
            header = f" Directory: {self._current_dir[:width-12]}"
            self._stdscr.addstr(y, x, header[:width])
            y += 1
            
            # Separator
            self._stdscr.addstr(y, x, "-" * min(width, MIN_WIDTH))
            y += 1
            
            # Draw items
            if not self._items:
                self._stdscr.addstr(y, x, "(No audio files or directories found)"[:width])
            else:
                max_items = max(1, height - 4)
                
                # Adjust scroll position
                if self._scroll_position + max_items > len(self._items):
                    self._scroll_position = max(0, len(self._items) - max_items)
                if self._selected_index < self._scroll_position:
                    self._scroll_position = self._selected_index
                if self._selected_index >= self._scroll_position + max_items:
                    self._scroll_position = self._selected_index - max_items + 1
                
                # Display visible items
                attr = curses.A_DIM if self._focus_on_playlist else 0
                for i in range(self._scroll_position, 
                               min(self._scroll_position + max_items, len(self._items))):
                    prefix = "> " if i == self._selected_index else "  "
                    suffix = "/" if self._items[i]['type'] == 'dir' else ""
                    line = f"{prefix}{self._items[i]['name']}{suffix}"
                    try:
                        self._stdscr.addstr(y + (i - self._scroll_position), x, line[:width], attr)
                    except curses.error:
                        pass
                
                # Scroll indicator
                scroll_indicator = f"[{self._scroll_position + 1}-{min(self._scroll_position + max_items, len(self._items))}/{len(self._items)}]"
                try:
                    self._stdscr.addstr(height - 1, x, scroll_indicator[:width])
                except curses.error:
                    pass
        except curses.error:
            pass
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into MM:SS string."""
        if seconds < 0:
            seconds = 0
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def _draw_progress_bar(self, y: int, x: int, width: int, progress: float) -> None:
        """Draw a progress bar at the specified position."""
        if width < 10:
            return
        
        try:
            # Calculate bar width and position
            bar_width = width - 2  # Leave space for brackets
            filled_width = int(bar_width * progress)
            
            # Draw the progress bar
            bar = "[" + "#" * filled_width + "-" * (bar_width - filled_width) + "]"
            self._stdscr.addstr(y, x, bar[:width])
        except curses.error:
            pass
    
    def _draw_player_menu(self, y: int, x: int, height: int, width: int) -> None:
        """Draw the player menu in the right panel with padding."""
        if width <= 2 or self._current_player is None:
            return
        
        state = self._current_player.get_state()
        
        # Pad the right panel: leave 1 space on left edge
        pad_x = x + 1
        inner_width = width - 2
        if inner_width <= 0:
            return
        
        try:
            # Header
            self._stdscr.addstr(y, pad_x, "=" * min(inner_width, MIN_WIDTH))
            y += 1
            title = "Sebs_Musicbowl - Player"
            self._stdscr.addstr(y, pad_x, title[:inner_width], curses.A_BOLD)
            y += 1
            self._stdscr.addstr(y, pad_x, "=" * min(inner_width, MIN_WIDTH))
            y += 1
            y += 1
            
            # Controls - break after every | to adapt to window width
            focus_text = "Playlist" if self._focus_on_playlist else "File Tree"
            controls_str = f"Controls: SPACE: Pause | s: Stop | n: Next | p: Prev | c: Clear | a: Append | TAB: Focus({focus_text}) | +: Inc Vol | -: Dec Vol | q: Quit"
            
            # Split by | and display with line breaks as needed
            parts = controls_str.split(" | ")
            current_line = ""
            for part in parts:
                if not current_line:
                    test_line = part
                else:
                    test_line = f"{current_line} | {part}"
                
                if len(test_line) <= inner_width:
                    current_line = test_line
                else:
                    if current_line:
                        self._stdscr.addstr(y, pad_x, current_line[:inner_width], curses.A_UNDERLINE)
                        y += 1
                    current_line = part
            
            if current_line:
                self._stdscr.addstr(y, pad_x, current_line[:inner_width], curses.A_UNDERLINE)
                y += 1
            
            y += 1  # Add blank line after controls
            
            # Now Playing and Metadata
            if state.current_file:
                filename = os.path.basename(str(state.current_file))
                now_playing = f"Now Playing: {filename}"
                self._stdscr.addstr(y, pad_x, now_playing[:inner_width])
                y += 1
                
                # Extract and display metadata
                metadata = extract_audio_metadata(str(state.current_file))
                metadata_displayed = False
                if metadata:
                    # Display metadata fields if available and not default values
                    if metadata.get('title', 'Unknown Title') != 'Unknown Title':
                        title_str = f"Title: {metadata['title']}"
                        self._stdscr.addstr(y, pad_x, title_str[:inner_width])
                        y += 1
                        metadata_displayed = True
                    if metadata.get('artist', 'Unknown Artist') != 'Unknown Artist':
                        artist_str = f"Artist: {metadata['artist']}"
                        self._stdscr.addstr(y, pad_x, artist_str[:inner_width])
                        y += 1
                        metadata_displayed = True
                    if metadata.get('album', 'Unknown Album') != 'Unknown Album':
                        album_str = f"Album: {metadata['album']}"
                        self._stdscr.addstr(y, pad_x, album_str[:inner_width])
                        y += 1
                        metadata_displayed = True
                    if metadata.get('year', 'Unknown Year') != 'Unknown Year':
                        year_str = f"Year: {metadata['year']}"
                        self._stdscr.addstr(y, pad_x, year_str[:inner_width])
                        y += 1
                        metadata_displayed = True
                    if metadata.get('genre', 'Unknown Genre') != 'Unknown Genre':
                        genre_str = f"Genre: {metadata['genre']}"
                        self._stdscr.addstr(y, pad_x, genre_str[:inner_width])
                        y += 1
                        metadata_displayed = True
                    
                    # Add a separator after metadata if any was displayed
                    if metadata_displayed:
                        y += 1
            else:
                self._stdscr.addstr(y, pad_x, "No file selected"[:inner_width])
                y += 1
            
            # Progress Bar and Time
            if state.current_file and state.duration > 0:
                progress = state.position / state.duration if state.duration > 0 else 0.0
                progress = max(0.0, min(1.0, progress))
                
                # Draw progress bar
                self._draw_progress_bar(y, pad_x, inner_width, progress)
                y += 1
                
                # Draw time info: played_time / total_time
                played_time = self._format_time(state.position)
                total_time = self._format_time(state.duration)
                time_str = f"Time: {played_time} / {total_time}"
                self._stdscr.addstr(y, pad_x, time_str[:inner_width])
                y += 1
            
            # Volume
            volume_pct = int(state.volume * 100)
            volume_str = f"Volume: {volume_pct}%"
            self._stdscr.addstr(y, pad_x, volume_str[:inner_width])
            y += 1
            
            # Status
            if state.is_playing():
                status = "Status: Playing"
            elif state.is_paused():
                status = "Status: Paused"
            elif state.is_stopped():
                status = "Status: Stopped"
            elif state.has_error():
                status = "Status: Error"
            else:
                status = "Status: Unknown"
            
            attr = curses.A_BOLD if state.is_playing() else 0
            self._stdscr.addstr(y, pad_x, status[:inner_width], attr)
            y += 1
            y += 1
            
            # Playlist display
            if self._current_player:
                playlist_mgr = self._current_player.get_playlist_manager()
                if playlist_mgr.has_tracks:
                    # Calculate available height for playlist
                    # We need space for: separator line + tracks + separator line
                    available_height = height - y - 3  # -1 for top separator, -1 for bottom separator, -1 for margin
                    
                    # Separator line under status
                    self._stdscr.addstr(y, pad_x, "-" * min(inner_width, MIN_WIDTH))
                    y += 1
                    
                    # Calculate visible playlist items based on scroll position
                    total_tracks = len(playlist_mgr.tracks)
                    current_index = playlist_mgr.current_index
                    
                    # Ensure available_height is at least 1
                    available_height = max(1, available_height)
                    
                    # Calculate max scroll position
                    max_scroll = max(0, total_tracks - available_height)
                    
                    # Auto-scroll to keep selected track visible when playlist has focus
                    if self._focus_on_playlist and available_height > 0:
                        if self._playlist_selected_index < self._playlist_scroll_position:
                            self._playlist_scroll_position = self._playlist_selected_index
                        elif self._playlist_selected_index >= self._playlist_scroll_position + available_height:
                            self._playlist_scroll_position = self._playlist_selected_index - available_height + 1
                    
                    # Clamp scroll position to valid range
                    self._playlist_scroll_position = max(0, min(self._playlist_scroll_position, max_scroll))
                    
                    # Display visible tracks
                    for i in range(self._playlist_scroll_position, min(self._playlist_scroll_position + available_height, total_tracks)):
                        track = playlist_mgr.tracks[i]
                        
                        # Get metadata for the track
                        metadata = extract_audio_metadata(str(track))
                        if metadata:
                            title = metadata.get('title', 'Unknown Title')
                            artist = metadata.get('artist', 'Unknown Artist')
                            if title != 'Unknown Title' or artist != 'Unknown Artist':
                                display_text = f"{title} - {artist}"
                            else:
                                display_text = os.path.basename(str(track))
                        else:
                            display_text = os.path.basename(str(track))
                        
                        # Truncate if too long
                        display_text = display_text[:inner_width]
                        
                        # Add indicator for current track and/or selected track
                        if self._focus_on_playlist:
                            # When playlist has focus, show selection
                            if i == self._playlist_selected_index:
                                display_text = f"> {display_text}"
                                display_text = display_text[:inner_width]
                                self._stdscr.addstr(y, pad_x, display_text, curses.A_BOLD)
                            elif i == current_index:
                                # Current playing track but not selected
                                display_text = f"* {display_text}"
                                display_text = display_text[:inner_width]
                                self._stdscr.addstr(y, pad_x, display_text, curses.A_UNDERLINE)
                            else:
                                self._stdscr.addstr(y, pad_x, display_text)
                        else:
                            # When file tree has focus, just show current playing track
                            if i == current_index:
                                display_text = f"> {display_text}"
                                display_text = display_text[:inner_width]
                                self._stdscr.addstr(y, pad_x, display_text, curses.A_BOLD)
                            else:
                                self._stdscr.addstr(y, pad_x, display_text)
                        
                        y += 1
                    
                    # Add separator after playlist
                    self._stdscr.addstr(y, pad_x, "-" * min(inner_width, MIN_WIDTH))
                    y += 1
            
            # Bottom separator
            self._stdscr.addstr(y, pad_x, "=" * min(inner_width, MIN_WIDTH))
        except curses.error:
            pass
    
    def _open_settings(self) -> None:
        """Open the settings dialog."""
        self._settings_dialog_active = True
        self._settings_input = self._current_dir
        
    def _close_settings(self) -> None:
        """Close the settings dialog."""
        self._settings_dialog_active = False
        self._settings_input = ""
        # Hide cursor when closing settings
        if self._stdscr:
            curses.curs_set(0)
        
    def _save_settings(self) -> None:
        """Save the settings and close the dialog."""
        if self._settings_input.strip():
            settings = get_settings()
            # Expand tilde to home directory and resolve to absolute path
            try:
                expanded_path = os.path.expanduser(self._settings_input.strip())
                resolved_path = str(Path(expanded_path).resolve())
                if os.path.isdir(resolved_path):
                    settings.set_default_directory(resolved_path)
                    self._current_dir = resolved_path
                    self._load_items()
                    self.show_message("Settings saved!")
                else:
                    self.show_message(f"Directory does not exist: {resolved_path}")
            except (ValueError, OSError) as e:
                self.show_message(f"Invalid directory path: {e}")
        else:
            self.show_message("Path cannot be empty")
        self._close_settings()
        
    def _draw_settings_dialog(self) -> None:
        """Draw the settings dialog over the main UI."""
        if not self._settings_dialog_active or self._stdscr is None:
            return
            
        height, width = self._stdscr.getmaxyx()
        
        # Create a centered dialog box
        dialog_height = 7
        dialog_width = min(width - 4, 60)
        dialog_y = (height - dialog_height) // 2
        dialog_x = (width - dialog_width) // 2
        
        # Draw dialog box
        try:
            # Top border
            self._stdscr.addstr(dialog_y, dialog_x, "+" + "-" * (dialog_width - 2) + "+")
            
            # Middle lines
            for i in range(1, dialog_height - 1):
                self._stdscr.addstr(dialog_y + i, dialog_x, "|")
                self._stdscr.addstr(dialog_y + i, dialog_x + dialog_width - 1, "|")
            
            # Bottom border
            self._stdscr.addstr(dialog_y + dialog_height - 1, dialog_x, "+" + "-" * (dialog_width - 2) + "+")
            
            # Title
            title = " SETTINGS "
            self._stdscr.addstr(dialog_y, dialog_x + (dialog_width - len(title)) // 2, title, curses.A_BOLD)
            
            # Content
            settings = get_settings()
            current_default = settings.get_default_directory() or "Not set"
            
            self._stdscr.addstr(dialog_y + 2, dialog_x + 2, "Default Directory:")
            self._stdscr.addstr(dialog_y + 3, dialog_x + 2, current_default[:dialog_width-6])
            self._stdscr.addstr(dialog_y + 4, dialog_x + 2, "New Path: ")
            
            # Draw input cursor
            input_x = dialog_x + 10
            input_width = dialog_width - 12
            input_display = self._settings_input[:input_width]
            self._stdscr.addstr(dialog_y + 4, input_x, input_display)
            
            # Draw cursor and show it
            cursor_pos = min(len(self._settings_input), input_width)
            self._stdscr.move(dialog_y + 4, input_x + cursor_pos)
            curses.curs_set(1)
            
            # Instructions
            instructions = "[Enter: Save | ESC: Cancel]"
            self._stdscr.addstr(dialog_y + dialog_height - 2, dialog_x + 2, instructions[:dialog_width-4])
            
        except curses.error:
            curses.curs_set(0)
            pass
        
    def _handle_settings_input(self, key: str) -> None:
        """Handle key input in settings dialog."""
        if key == 'enter':
            self._save_settings()
        elif key == 'esc':
            self._close_settings()
        elif key == 'backspace':
            self._settings_input = self._settings_input[:-1]
        elif key == 'delete':
            # Remove character at cursor position
            if len(self._settings_input) > 0:
                self._settings_input = self._settings_input[:-1]
        elif key == 'left':
            # Handle cursor movement if needed
            pass
        elif key == 'right':
            # Handle cursor movement if needed
            pass
        elif len(key) == 1:
            self._settings_input += key
            
    def _main_loop(self) -> None:
        """Main loop for the split-screen UI."""
        while True:
            # Draw the UI
            self._display_split_screen()
            
            # Draw settings dialog if active
            if self._settings_dialog_active:
                self._draw_settings_dialog()
            
            key = self._stdscr.getch()
            
            if key == -1:
                time.sleep(0.02)
                continue
            
            # Handle mouse events first
            if key == curses.KEY_MOUSE:
                self._handle_mouse(key)
                continue
            
            processed_key = self._map_key(key)
            if processed_key is None:
                continue
            
            # If settings dialog is active, handle settings input
            if self._settings_dialog_active:
                self._handle_settings_input(processed_key)
                continue
            
            if processed_key == 'q':
                break
            elif processed_key == 'up':
                if self._focus_on_playlist:
                    self._move_playlist_selection(-1)
                else:
                    self._move_selection(-1)
            elif processed_key == 'down':
                if self._focus_on_playlist:
                    self._move_playlist_selection(1)
                else:
                    self._move_selection(1)
            elif processed_key == 'pageup':
                if self._focus_on_playlist:
                    self._move_playlist_selection(-SCROLL_STEP)
                else:
                    self._move_selection(-SCROLL_STEP)
            elif processed_key == 'pagedown':
                if self._focus_on_playlist:
                    self._move_playlist_selection(SCROLL_STEP)
                else:
                    self._move_selection(SCROLL_STEP)
            elif processed_key == 'left':
                self._go_up_directory()
            elif processed_key == 'esc':
                self._open_settings()
            elif processed_key in ('enter', 'right'):
                if self._focus_on_playlist:
                    self._select_playlist_track()
                else:
                    self._select_item()
            elif processed_key.isdigit():
                self._select_by_number(int(processed_key))
            elif processed_key == ' ':
                # If nothing is playing but we have a playlist, play from it
                state = self._current_player.get_state()
                if not state.is_playing() and not state.is_paused():
                    playlist_mgr = self._current_player.get_playlist_manager()
                    if playlist_mgr.has_tracks:
                        if self._focus_on_playlist:
                            # Play the selected track
                            selected_track = playlist_mgr.tracks[self._playlist_selected_index]
                            self._current_player.play(selected_track)
                        else:
                            # Play the first track in the playlist
                            self._current_player.play(playlist_mgr.tracks[0])
                    else:
                        self._current_player.toggle_pause()
                else:
                    self._current_player.toggle_pause()
            elif processed_key == 's':
                self._current_player.stop()
            elif processed_key == '+':
                self._current_player.increase_volume(VOLUME_STEP)
            elif processed_key == '-':
                self._current_player.decrease_volume(VOLUME_STEP)
            elif processed_key == 'tab':
                self._focus_on_playlist = not self._focus_on_playlist
                if self._focus_on_playlist:
                    self._reset_playlist_selection()
            elif processed_key == 'n':
                self._current_player.next_track()
            elif processed_key == 'p':
                self._current_player.previous_track()
            elif processed_key == 'c':
                self._current_player.clear_playlist()
                self._current_player.stop()
            elif processed_key == 'a':
                self._append_selected_to_playlist()
    
    def _move_selection(self, delta: int) -> None:
        """Move the selection in the file tree by delta."""
        if not self._items:
            return
        
        self._selected_index = max(0, min(len(self._items) - 1, self._selected_index + delta))
    
    def _scroll_playlist(self, delta: int) -> None:
        """Scroll the playlist display by delta."""
        if self._current_player:
            playlist_mgr = self._current_player.get_playlist_manager()
            if playlist_mgr.has_tracks:
                total_tracks = len(playlist_mgr.tracks)
                # We don't know the available height here, so just allow any positive value
                # The display logic will clamp it properly
                self._playlist_scroll_position = max(0, self._playlist_scroll_position + delta)
                # But ensure it doesn't go beyond the total number of tracks
                self._playlist_scroll_position = min(self._playlist_scroll_position, max(0, total_tracks - 1))
    
    def _move_playlist_selection(self, delta: int) -> None:
        """Move the selection in the playlist by delta."""
        if self._current_player:
            playlist_mgr = self._current_player.get_playlist_manager()
            if playlist_mgr.has_tracks:
                total_tracks = len(playlist_mgr.tracks)
                self._playlist_selected_index = max(0, min(total_tracks - 1, self._playlist_selected_index + delta))
    
    def _select_playlist_track(self) -> None:
        """Select the currently highlighted playlist track and start playing it."""
        if self._current_player:
            playlist_mgr = self._current_player.get_playlist_manager()
            if playlist_mgr.has_tracks and 0 <= self._playlist_selected_index < len(playlist_mgr.tracks):
                track = playlist_mgr.tracks[self._playlist_selected_index]
                self._current_player.play(track)
    
    def _reset_playlist_selection(self) -> None:
        """Reset the playlist selection to the current playing track."""
        if self._current_player:
            playlist_mgr = self._current_player.get_playlist_manager()
            if playlist_mgr.has_tracks:
                self._playlist_selected_index = playlist_mgr.current_index
    
    def _handle_mouse(self, key: int) -> bool:
        """Handle mouse events for playlist scrolling."""
        if key != curses.KEY_MOUSE:
            return False
        
        try:
            # Get mouse event
            mouse_id = curses.getmouse()
            if mouse_id is None:
                return True
            
            # Check if mouse is in the right panel (playlist area)
            split_pos = self._get_split_position()
            x_pos = mouse_id[1]  # x coordinate
            
            # Right panel starts at split_pos + 1 (after the separator line)
            if x_pos <= split_pos:
                # Mouse is in left panel (file tree), ignore
                return True
            
            # Mouse is in right panel - handle scrolling
            # mouse_id format: (id, x, y, z, bstate)
            _, x, y, _, bstate = mouse_id
            
            # Check for mouse wheel events (button 4 = scroll up, button 5 = scroll down)
            if bstate & curses.BUTTON4_PRESSED:
                self._scroll_playlist(-1)
                return True
            elif bstate & curses.BUTTON5_PRESSED:
                self._scroll_playlist(1)
                return True
            
            # Check for mouse click in playlist area to switch focus
            if bstate & curses.BUTTON1_PRESSED:
                self._focus_on_playlist = True
                return True
            
        except Exception:
            pass
        
        return True
        
        if self._stdscr:
            height, width = self._stdscr.getmaxyx()
            split_pos = self._get_split_position()
            max_items = max(1, height - 4)
            
            if self._selected_index < self._scroll_position:
                self._scroll_position = self._selected_index
            elif self._selected_index >= self._scroll_position + max_items:
                self._scroll_position = self._selected_index - max_items + 1
    
    def _go_up_directory(self) -> None:
        """Go up one directory level."""
        try:
            current_path = Path(self._current_dir)
            parent_path = current_path.parent.resolve()
            if str(parent_path) != str(current_path):
                self._current_dir = str(parent_path)
                self._load_items()
        except (ValueError, OSError):
            # If path resolution fails, stay in current directory
            pass
    
    def _select_item(self) -> None:
        """Select the currently highlighted item."""
        if not self._items or self._selected_index >= len(self._items):
            return
        
        item = self._items[self._selected_index]
        if item['type'] == 'dir':
            try:
                # Validate the directory path before changing
                dir_path = Path(item['path'])
                if dir_path.is_dir():
                    self._current_dir = str(dir_path.resolve())
                    self._load_items()
                else:
                    self.show_message(f"Not a valid directory: {item['path']}")
            except (ValueError, OSError):
                self.show_message(f"Invalid directory path: {item['path']}")
        else:
            # Load all audio files in the directory as a playlist and start from clicked file
            self._current_player.stop()
            self._current_player.clear_playlist()
            self._current_player.play_playlist(self._current_dir, Path(item['path']))
            # Reset playlist scroll position and selection when new playlist is loaded
            self._playlist_scroll_position = 0
            self._playlist_selected_index = 0
    
    def _append_selected_to_playlist(self) -> None:
        """Append the currently selected item (file or directory) to the playlist."""
        if not self._items or self._selected_index >= len(self._items):
            return
        
        item = self._items[self._selected_index]
        playlist_mgr = self._current_player.get_playlist_manager()
        old_count = len(playlist_mgr.tracks)
        
        if item['type'] == 'dir':
            # Append all audio files from the selected directory
            self._current_player.append_to_playlist(item['path'])
        else:
            # Append just the selected single audio file
            playlist_mgr.add_track(Path(item['path']))
        
        # If this was the first item added, set it as selected
        if old_count == 0:
            self._playlist_selected_index = 0
    
    def _select_by_number(self, number: int) -> None:
        """Select an item by its number (1-9)."""
        if not self._items:
            return
        
        index = number - 1
        if 0 <= index < len(self._items):
            item = self._items[index]
            if item['type'] == 'dir':
                try:
                    # Validate the directory path before changing
                    dir_path = Path(item['path'])
                    if dir_path.is_dir():
                        self._current_dir = str(dir_path.resolve())
                        self._load_items()
                    else:
                        self.show_message(f"Not a valid directory: {item['path']}")
                except (ValueError, OSError):
                    self.show_message(f"Invalid directory path: {item['path']}")
            else:
                # Load all audio files in the directory as a playlist and start from clicked file
                self._current_player.stop()
                self._current_player.clear_playlist()
                self._current_player.play_playlist(self._current_dir, Path(item['path']))
                # Reset playlist scroll position when new playlist is loaded
                self._playlist_scroll_position = 0
    
    def _map_key(self, key: int) -> Optional[str]:
        """Map curses key code to string name."""
        if key == -1:
            return None
        
        key_map = {
            27: 'esc',
            10: 'enter',
            13: 'enter',
            9: 'tab',
            32: ' ',
            127: 'backspace',  # Backspace key
            8: 'backspace',    # Alternative backspace
            curses.KEY_UP: 'up',
            curses.KEY_DOWN: 'down',
            curses.KEY_LEFT: 'left',
            curses.KEY_RIGHT: 'right',
            curses.KEY_PPAGE: 'pageup',
            curses.KEY_NPAGE: 'pagedown',
            curses.KEY_BACKSPACE: 'backspace',
            curses.KEY_DC: 'delete',
            curses.KEY_MOUSE: 'mouse',
        }
        
        # Handle Shift+Arrow keys (key codes may vary by terminal)
        # Common values: Shift+Up=393, Shift+Down=401
        if key == 393:
            return 'shift_up'
        elif key == 401:
            return 'shift_down'
        
        result = key_map.get(key)
        if result is not None:
            return result
        
        if 32 <= key <= 126:
            return chr(key).lower()
        
        return None
    
    def select_file(self, start_dir: Optional[str] = None) -> Optional[str]:
        """Select file for interface compatibility."""
        if start_dir is None:
            start_dir = os.getcwd()
        items = get_directory_contents(start_dir)
        audio_files = [i['path'] for i in items if i['type'] == 'file']
        if audio_files:
            return audio_files[0]
        return None
    
    def display_state(self, state: PlayerState) -> None:
        pass
    
    def show_error(self, message: str) -> None:
        if self._stdscr:
            try:
                height, width = self._stdscr.getmaxyx()
                split_pos = self._get_split_position()
                pad_x = split_pos + 2
                inner_width = width - split_pos - 3
                error_msg = f"ERROR: {message}"
                self._stdscr.addstr(height - 1, pad_x, error_msg[:inner_width])
                self._stdscr.refresh()
                time.sleep(2)
            except Exception:
                pass
    
    def show_message(self, message: str) -> None:
        if self._stdscr:
            try:
                height, width = self._stdscr.getmaxyx()
                split_pos = self._get_split_position()
                pad_x = split_pos + 2
                inner_width = width - split_pos - 3
                self._stdscr.addstr(height - 1, pad_x, message[:inner_width])
                self._stdscr.refresh()
            except Exception:
                pass
    
    def cleanup(self) -> None:
        self._cleanup_curses()
