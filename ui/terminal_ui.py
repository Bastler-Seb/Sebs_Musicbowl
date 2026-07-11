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
        self._stdscr.timeout(50)
    
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
            # Controls hint at the top
            controls = "[Up/Down: Nav | Enter: Select | Left: Up | q: Quit]"
            self._stdscr.addstr(y, x, controls[:width])
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
                for i in range(self._scroll_position, 
                               min(self._scroll_position + max_items, len(self._items))):
                    prefix = "> " if i == self._selected_index else "  "
                    suffix = "/" if self._items[i]['type'] == 'dir' else ""
                    line = f"{prefix}{self._items[i]['name']}{suffix}"
                    try:
                        self._stdscr.addstr(y + (i - self._scroll_position), x, line[:width])
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
            
            # Now Playing
            if state.current_file:
                filename = os.path.basename(str(state.current_file))
                now_playing = f"Now Playing: {filename}"
                self._stdscr.addstr(y, pad_x, now_playing[:inner_width])
                y += 1
            else:
                self._stdscr.addstr(y, pad_x, "No file selected"[:inner_width])
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
            
            # Controls
            self._stdscr.addstr(y, pad_x, "Controls:", curses.A_UNDERLINE)
            y += 1
            self._stdscr.addstr(y, pad_x, "  p  - Pause / Resume"[:inner_width])
            y += 1
            self._stdscr.addstr(y, pad_x, "  s  - Stop"[:inner_width])
            y += 1
            self._stdscr.addstr(y, pad_x, "  +  - Increase volume"[:inner_width])
            y += 1
            self._stdscr.addstr(y, pad_x, "  -  - Decrease volume"[:inner_width])
            y += 1
            self._stdscr.addstr(y, pad_x, "  q  - Quit"[:inner_width])
            y += 1
            y += 1
            
            # Bottom separator
            self._stdscr.addstr(y, pad_x, "=" * min(inner_width, MIN_WIDTH))
        except curses.error:
            pass
    
    def _main_loop(self) -> None:
        """Main loop for the split-screen UI."""
        while True:
            self._display_split_screen()
            
            key = self._stdscr.getch()
            
            if key == -1:
                time.sleep(0.02)
                continue
            
            processed_key = self._map_key(key)
            if processed_key is None:
                continue
            
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
