"""
Terminal UI Implementation

Concrete implementation of UIInterface for terminal-based interaction.
This includes file selection with curses and playback controls.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

import pygame

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
SELECTOR_CONTROLS: str = "[CONTROLS: Up/Down navigate | Enter/Right select | Left/ESC up | PGUP/PGDN scroll | q quit]"


class TerminalUI(UIInterface):
    """
    Terminal-based implementation of the UIInterface.
    
    Handles file selection with curses and playback controls with key reading.
    """
    
    def __init__(self):
        """Initialize the terminal UI."""
        self._start_dir: Optional[str] = None
        self._current_player: Optional[PlayerInterface] = None
    
    def run(self, player: PlayerInterface, start_file: Optional[Path] = None) -> None:
        """
        Run the main terminal UI loop.
        
        Args:
            player: The player instance to control.
            start_file: Optional file to play immediately on start.
        """
        self._current_player = player
        
        # Main loop for continuous playback
        self._main_loop(start_file)
    
    def _play_file(self, file_path: Path) -> bool:
        """
        Play a file and handle the playback loop.
        
        Args:
            file_path: Path to the file to play.
            
        Returns:
            True if user wants to continue, False to quit.
        """
        if not validate_audio_filepath(str(file_path)):
            self.show_error(f"Error: Invalid audio file: {file_path}")
            return True
        
        # Play the file
        success = self._current_player.play(file_path)
        if not success:
            self.show_error(f"Error: Could not play file: {file_path}")
            return True
        
        # Display initial state
        state = self._current_player.get_state()
        self._display_playback_state(state)
        
        # Playback loop
        while True:
            # Check if song finished
            state = self._current_player.get_state()
            if not self._current_player.is_playing() and not state.is_paused():
                if state.status == PlaybackStatus.FINISHED:
                    self.show_message("\nTrack finished.")
                    return True
                elif state.status == PlaybackStatus.ERROR:
                    self.show_error(f"\nError: {state.error_message}")
                    return True
            
            # Check for user input
            key = read_key()
            
            if key is None:
                # No key pressed, small delay to prevent CPU overload
                time.sleep(0.05)
                continue
                
            if key == 'p':
                self._current_player.toggle_pause()
                state = self._current_player.get_state()
                self._display_playback_state(state)
            elif key in ('s', 'left'):
                self._current_player.stop()
                self.show_message("\nStopped")
                return True
            elif key == 'q':
                self._current_player.stop()
                return False
            elif key == '+':
                new_volume = self._current_player.increase_volume(VOLUME_STEP)
                state = self._current_player.get_state()
                state.volume = new_volume
                self._display_playback_state(state)
            elif key == '-':
                new_volume = self._current_player.decrease_volume(VOLUME_STEP)
                state = self._current_player.get_state()
                state.volume = new_volume
                self._display_playback_state(state)
    
    def _main_loop(self, start_file: Optional[Path] = None) -> None:
        """Main loop for continuous file selection and playback."""
        start_dir = self._start_dir if self._start_dir else os.getcwd()
        
        # If a start file is provided, play it first
        if start_file is not None:
            if not self._play_file(start_file):
                return  # User wants to quit
        
        # Main loop
        while True:
            filepath = self.select_file(start_dir)
            if filepath is None:
                self.show_message("\nNo file selected. Exiting.")
                break
            
            start_dir = os.path.dirname(filepath)
            if not self._play_file(Path(filepath)):
                break
    
    def select_file(self, start_dir: Optional[str] = None) -> Optional[str]:
        """
        Show a file selection dialog using curses.
        
        Args:
            start_dir: Starting directory for file selection.
            
        Returns:
            Path to the selected audio file, or None if cancelled.
        """
        import curses
        
        # Validate and set starting directory
        if start_dir is None:
            start_dir = os.getcwd()
        
        # Ensure we have a valid directory
        current_dir = start_dir
        while not os.path.isdir(current_dir):
            parent = os.path.dirname(current_dir)
            if parent == current_dir:
                current_dir = os.getcwd()
                break
            current_dir = parent
        
        selected_index = 0
        scroll_position = 0
        
        # Initialize curses
        stdscr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        stdscr.keypad(True)
        stdscr.timeout(100)
        curses.curs_set(0)
        
        try:
            while True:
                items = get_directory_contents(current_dir)
                
                # Clear and redraw screen
                stdscr.clear()
                height, width = stdscr.getmaxyx()
                
                try:
                    # Draw header
                    stdscr.addstr(0, 0, SELECTOR_CONTROLS[:width - 1])
                    separator = "-" * min(width, MIN_WIDTH)
                    stdscr.addstr(1, 0, separator)
                    stdscr.addstr(2, 0, f"Directory: {current_dir}"[:width - 1])
                    stdscr.addstr(3, 0, separator)
                    
                    # Draw items
                    if not items:
                        stdscr.addstr(5, 0, "(No audio files or directories found)")
                    else:
                        max_items = max(1, height - 6)
                        
                        # Adjust scroll position
                        if scroll_position + max_items > len(items):
                            scroll_position = max(0, len(items) - max_items)
                        if selected_index < scroll_position:
                            scroll_position = selected_index
                        if selected_index >= scroll_position + max_items:
                            scroll_position = selected_index - max_items + 1
                        
                        # Display visible items
                        for i in range(scroll_position, min(scroll_position + max_items, len(items))):
                            prefix = "> " if i == selected_index else "  "
                            suffix = "/" if items[i]['type'] == 'dir' else ""
                            line = f"{prefix}{items[i]['name']}{suffix}"
                            try:
                                stdscr.addstr(5 + (i - scroll_position), 0, line[:width - 1])
                            except curses.error:
                                truncated = f"{prefix}[unreadable]{suffix}"[:width - 1]
                                stdscr.addstr(5 + (i - scroll_position), 0, truncated)
                        
                        # Draw scroll indicator
                        scroll_indicator = f"[{scroll_position + 1}-{min(scroll_position + max_items, len(items))}/{len(items)}]"
                        stdscr.addstr(height - 1, 0, scroll_indicator[:width - 1])
                except curses.error:
                    pass
                
                stdscr.refresh()
                
                # Get and process key
                key = stdscr.getch()
                if key == -1:
                    time.sleep(0.05)
                    continue
                
                # Map curses key codes to string names
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
                
                processed_key = key_map.get(key)
                if processed_key is None and 32 <= key <= 126:
                    processed_key = chr(key).lower()
                
                # Handle key presses
                if processed_key == 'q':
                    return None
                elif processed_key == 'up' and items:
                    selected_index = max(0, selected_index - 1)
                elif processed_key == 'down' and items:
                    selected_index = min(len(items) - 1, selected_index + 1)
                elif processed_key == 'pageup' and items:
                    selected_index = max(0, selected_index - SCROLL_STEP)
                elif processed_key == 'pagedown' and items:
                    selected_index = min(len(items) - 1, selected_index + SCROLL_STEP)
                elif processed_key in ('left', 'esc'):
                    parent_dir = os.path.dirname(current_dir)
                    if parent_dir != current_dir:
                        current_dir = parent_dir
                    selected_index = 0
                    scroll_position = 0
                elif processed_key in ('enter', 'right') and items and selected_index < len(items):
                    if items[selected_index]['type'] == 'dir':
                        current_dir = items[selected_index]['path']
                        selected_index = 0
                        scroll_position = 0
                    else:
                        return items[selected_index]['path']
                elif isinstance(processed_key, str) and processed_key.isdigit() and items:
                    index = int(processed_key)
                    if 1 <= index <= len(items):
                        selected_item = items[index - 1]
                        if selected_item['type'] == 'dir':
                            current_dir = selected_item['path']
                            selected_index = 0
                            scroll_position = 0
                        else:
                            return selected_item['path']
        finally:
            curses.nocbreak()
            curses.echo()
            stdscr.keypad(False)
            curses.endwin()
    
    def display_state(self, state: PlayerState) -> None:
        """
        Display the current player state.
        
        Args:
            state: The current player state to display.
        """
        self._display_playback_state(state)
    
    def _display_playback_state(self, state: PlayerState) -> None:
        """Display the playback state with controls."""
        clear_screen()
        
        filename = str(state.current_file) if state.current_file else "Unknown"
        print(f"Now Playing: {os.path.basename(filename)}")
        print(f"Volume: {int(state.volume * 100)}%")
        
        if state.is_playing():
            status = "Playing"
        elif state.is_paused():
            status = "Paused"
        elif state.is_stopped():
            status = "Stopped"
        elif state.has_error():
            status = f"Error: {state.error_message}"
        else:
            status = "Unknown"
        
        print(f"Status: {status}")
        self._print_controls()
    
    def _print_controls(self) -> None:
        """Display the control instructions."""
        print("\n" + "=" * MIN_WIDTH)
        print("  Sebs_Musicbowl - Terminal Music Player")
        print("=" * MIN_WIDTH)
        print("\nControls:")
        print("  p  - Pause / Resume")
        print("  s  - Stop (return to selection)")
        print("  Left - Stop (return to selection)")
        print("  q  - Quit")
        print("  +  - Increase volume")
        print("  -  - Decrease volume")
        print("=" * MIN_WIDTH + "\n")
    
    def show_error(self, message: str) -> None:
        """
        Display an error message to the user.
        
        Args:
            message: The error message to display.
        """
        clear_screen()
        print(f"ERROR: {message}")
        print()
    
    def show_message(self, message: str) -> None:
        """
        Display a general message to the user.
        
        Args:
            message: The message to display.
        """
        print(message)
    
    def cleanup(self) -> None:
        """Clean up any resources used by the UI."""
        # Terminal UI doesn't have persistent resources to clean up
        pass
