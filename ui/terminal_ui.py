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
    validate_audio_filepath, clear_screen
)
from utils.input_utils import read_key


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
            # Set initial directory
            self._current_dir = self._start_dir if self._start_dir else os.getcwd()
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
        self._stdscr.timeout(50)  # Non-blocking with 50ms timeout
    
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
        self._draw_player_menu(split_pos, 0, height, width - split_pos)
        
        # Draw separator line
        if split_pos < width:
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
            # Header
            header = f" BROWSE: {self._current_dir[:width-12]} "
            self._stdscr.addstr(y, x, header[:width])
            y += 1
            
            # Separator
            self._stdscr.addstr(y, x, "-" * min(width, MIN_WIDTH))
            y += 1
            
            # Draw items
            if not self._items:
                self._stdscr.addstr(y, x, "(No audio files or directories found)"[:width-1])
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
                for i in range(self._scroll_position, 
                               min(self._scroll_position + max_items, len(self._items))):
                    prefix = "> " if i == self._selected_index else "  "
                    suffix = "/" if self._items[i]['type'] == 'dir' else ""
                    line = f"{prefix}{self._items[i]['name']}{suffix}"
                    try:
                        self._stdscr.addstr(y + (i - self._scroll_position), x, line[:width-1])
                    except curses.error:
                        pass
                
                # Scroll indicator
                scroll_indicator = f"[{self._scroll_position + 1}-{min(self._scroll_position + max_items, len(self._items))}/{len(self._items)}]"
                try:
                    self._stdscr.addstr(height - 1, x, scroll_indicator[:width-1])
                except curses.error:
                    pass
        except curses.error:
            pass
        
        # Controls hint at the top
        try:
            controls = "[Up/Down: Nav | Enter: Select | Left: Up | q: Quit]"
            self._stdscr.addstr(0, x, controls[:width-1])
        except curses.error:
            pass
    
    def _draw_player_menu(self, x: int, y: int, height: int, width: int) -> None:
        """Draw the player menu in the right panel."""
        if width <= 0 or self._current_player is None:
            return
        
        state = self._current_player.get_state()
        
        try:
            # Header
            self._stdscr.addstr(y, x, " " + "=" * (min(width-2, MIN_WIDTH)))
            y += 1
            title = "  Sebs_Musicbowl - Player  "
            self._stdscr.addstr(y, x, title[:width-1], curses.A_BOLD)
            y += 1
            self._stdscr.addstr(y, x, " " + "=" * (min(width-2, MIN_WIDTH)))
            y += 1
            y += 1
            
            # Now Playing
            if state.current_file:
                filename = os.path.basename(str(state.current_file))
                now_playing = f"Now Playing: {filename}"
                self._stdscr.addstr(y, x, now_playing[:width-2])
                y += 1
            else:
                self._stdscr.addstr(y, x, "No file selected"[:width-2])
                y += 1
            
            # Volume
            volume_pct = int(state.volume * 100)
            volume_str = f"Volume: {volume_pct}%"
            self._stdscr.addstr(y, x, volume_str[:width-2])
            y += 1
            
            # Status
            if state.is_playing():
                status = "Status: Playing"
            elif state.is_paused():
                status = "Status: Paused"
            elif state.is_stopped():
                status = "Status: Stopped"
            elif state.has_error():
                status = f"Status: Error"
            else:
                status = "Status: Unknown"
            
            attr = curses.A_BOLD if state.is_playing() else 0
            self._stdscr.addstr(y, x, status[:width-2], attr)
            y += 1
            y += 1
            
            # Player Controls Menu
            self._stdscr.addstr(y, x, "Controls:"[:width-2], curses.A_UNDERLINE)
            y += 1
            self._stdscr.addstr(y, x, "  p  - Pause / Resume"[:width-2])
            y += 1
            self._stdscr.addstr(y, x, "  s  - Stop"[:width-2])
            y += 1
            self._stdscr.addstr(y, x, "  +  - Increase volume"[:width-2])
            y += 1
            self._stdscr.addstr(y, x, "  -  - Decrease volume"[:width-2])
            y += 1
            self._stdscr.addstr(y, x, "  q  - Quit"[:width-2])
            y += 1
            y += 1
            
            # Separator at bottom
            self._stdscr.addstr(y, x, " " + "=" * (min(width-2, MIN_WIDTH)))
        except curses.error:
            pass
    
    def _main_loop(self) -> None:
        """Main loop for the split-screen UI."""
        while True:
            self._display_split_screen()
            
            # Get key with timeout
            key = self._stdscr.getch()
            
            if key == -1:
                # Timeout, update display and continue
                time.sleep(0.02)
                continue
            
            # Map curses key to string
            processed_key = self._map_key(key)
            
            if processed_key is None:
                continue
            
            # Handle navigation keys (work in both file browser and player)
            if processed_key == 'q':
                break
            elif processed_key == 'up':
                self._move_selection(-1)
            elif processed_key == 'down':
                self._move_selection(1)
            elif processed_key == 'pageup':
                self._move_selection(-SCROLL_STEP)
            elif processed_key == 'pagedown':
                self._move_selection(SCROLL_STEP)
            elif processed_key in ('left', 'esc'):
                self._go_up_directory()
            elif processed_key in ('enter', 'right'):
                self._select_item()
            elif processed_key.isdigit():
                self._select_by_number(int(processed_key))
            # Player control keys
            elif processed_key == 'p':
                self._current_player.toggle_pause()
            elif processed_key == 's':
                self._current_player.stop()
            elif processed_key == '+':
                self._current_player.increase_volume(VOLUME_STEP)
            elif processed_key == '-':
                self._current_player.decrease_volume(VOLUME_STEP)
    
    def _move_selection(self, delta: int) -> None:
        """Move the selection in the file tree by delta."""
        if not self._items:
            return
        
        self._selected_index = max(0, min(len(self._items) - 1, self._selected_index + delta))
        
        # Adjust scroll position if needed
        if self._selected_index < self._scroll_position:
            self._scroll_position = self._selected_index
        elif self._selected_index >= self._scroll_position + 20:
            self._scroll_position = self._selected_index - 19
    
    def _go_up_directory(self) -> None:
        """Go up one directory level."""
        parent_dir = os.path.dirname(self._current_dir)
        if parent_dir != self._current_dir:
            self._current_dir = parent_dir
            self._load_items()
    
    def _select_item(self) -> None:
        """Select the currently highlighted item."""
        if not self._items or self._selected_index >= len(self._items):
            return
        
        item = self._items[self._selected_index]
        if item['type'] == 'dir':
            self._current_dir = item['path']
            self._load_items()
        else:
            # Play the selected audio file
            self._current_player.stop()
            self._current_player.play(Path(item['path']))
    
    def _select_by_number(self, number: int) -> None:
        """Select an item by its number (1-9)."""
        if not self._items:
            return
        
        index = number - 1
        if 0 <= index < len(self._items):
            item = self._items[index]
            if item['type'] == 'dir':
                self._current_dir = item['path']
                self._load_items()
            else:
                self._current_player.stop()
                self._current_player.play(Path(item['path']))
    
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
            curses.KEY_UP: 'up',
            curses.KEY_DOWN: 'down',
            curses.KEY_LEFT: 'left',
            curses.KEY_RIGHT: 'right',
            curses.KEY_PPAGE: 'pageup',
            curses.KEY_NPAGE: 'pagedown',
        }
        
        result = key_map.get(key)
        if result is not None:
            return result
        
        if 32 <= key <= 126:
            return chr(key).lower()
        
        return None
    
    # Methods for UIInterface compliance
    def select_file(self, start_dir: Optional[str] = None) -> Optional[str]:
        """
        Show a file selection dialog.
        
        In this split-screen UI, this is not used as the file selector
        is always visible on the left. This method is kept for interface
        compatibility.
        
        Args:
            start_dir: Starting directory for file selection.
            
        Returns:
            Path to the selected audio file, or None if cancelled.
        """
        if start_dir is None:
            start_dir = os.getcwd()
        
        items = get_directory_contents(start_dir)
        audio_files = [i['path'] for i in items if i['type'] == 'file']
        if audio_files:
            return audio_files[0]
        return None
    
    def display_state(self, state: PlayerState) -> None:
        """
        Display the current player state.
        
        Args:
            state: The current player state to display.
        """
        pass
    
    def show_error(self, message: str) -> None:
        """
        Display an error message to the user.
        
        Args:
            message: The error message to display.
        """
        if self._stdscr:
            try:
                height, width = self._stdscr.getmaxyx()
                split_pos = self._get_split_position()
                error_msg = f"ERROR: {message}"
                self._stdscr.addstr(height - 1, split_pos + 1, error_msg[:width - split_pos - 2])
                self._stdscr.refresh()
                time.sleep(2)
            except Exception:
                pass
    
    def show_message(self, message: str) -> None:
        """
        Display a general message to the user.
        
        Args:
            message: The message to display.
        """
        if self._stdscr:
            try:
                height, width = self._stdscr.getmaxyx()
                split_pos = self._get_split_position()
                self._stdscr.addstr(height - 1, split_pos + 1, message[:width - split_pos - 2])
                self._stdscr.refresh()
            except Exception:
                pass
    
    def cleanup(self) -> None:
        """Clean up any resources used by the UI."""
        self._cleanup_curses()
