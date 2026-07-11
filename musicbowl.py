#!/usr/bin/env python3
"""
Sebs_Musicbowl - Simple Terminal Music Player

A minimal Python terminal program that plays music from a specified filepath.
Uses pygame for audio playback.

Usage:
    python musicbowl.py [filepath]

    If no filepath is provided, you will be prompted to enter one.

Controls while playing:
    p       - Pause / Resume
    s       - Stop (return to selection)
    Left    - Stop (return to selection)
    q       - Quit
    +       - Increase volume
    -       - Decrease volume
    h       - Show help

File Selector Controls:
    Up/Down arrows   - Navigate items
    Enter/Right      - Select directory or file
    Left/ESC         - Go up one directory
    q                - Quit selector
"""

import argparse
import os
import sys
import time

import pygame

# Constants
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.mp4', '.opus'}
DEFAULT_VOLUME = 0.7
VOLUME_STEP = 0.1
SCROLL_STEP = 10


# Type aliases
FileItem = dict[str, str]


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def is_audio_file(filename: str) -> bool:
    """Check if a file is an audio file based on extension."""
    return filename.lower().endswith(tuple(AUDIO_EXTENSIONS))


def get_directory_contents(directory: str) -> list[FileItem]:
    """Get sorted list of directories and audio files in a directory."""
    items: list[FileItem] = []
    try:
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isdir(full_path):
                items.append({'name': item, 'path': full_path, 'type': 'dir'})
            elif os.path.isfile(full_path) and is_audio_file(item):
                items.append({'name': item, 'path': full_path, 'type': 'file'})
    except PermissionError:
        return []

    dirs = [i for i in items if i['type'] == 'dir']
    files = [i for i in items if i['type'] == 'file']
    dirs.sort(key=lambda x: x['name'].lower())
    files.sort(key=lambda x: x['name'].lower())
    return dirs + files


def read_key() -> str | None:
    """Read a single key press for player controls.
    
    Returns:
        String representing the key ('up', 'down', 'left', 'right', 'enter', 
        'esc', 'tab', ' ', or lowercase character) or None if no key pressed.
    """
    # Try readchar first (cross-platform)
    try:
        import readchar
        key = readchar.readchar()
        if key == readchar.key.UP:
            return 'up'
        elif key == readchar.key.DOWN:
            return 'down'
        elif key == readchar.key.LEFT:
            return 'left'
        elif key == readchar.key.RIGHT:
            return 'right'
        elif key == readchar.key.ENTER:
            return 'enter'
        elif key == readchar.key.ESC:
            return 'esc'
        elif isinstance(key, str):
            if key == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
            return key.lower()
        return None
    except (ImportError, ModuleNotFoundError, OSError):
        pass

    # Try msvcrt (Windows)
    try:
        import msvcrt
        if msvcrt.kbhit():
            raw = msvcrt.getch()
            if raw in (b'\xe0', b'\x00'):
                next_raw = msvcrt.getch()
                if next_raw == b'H':
                    return 'up'
                elif next_raw == b'P':
                    return 'down'
                elif next_raw == b'K':
                    return 'left'
                elif next_raw == b'M':
                    return 'right'
            elif raw in (b'\r', b'\n'):
                return 'enter'
            elif raw == b'\x1b':
                return 'esc'
            elif raw == b'\t':
                return 'tab'
            elif raw == b' ':
                return ' '
            elif raw == b'\x03':  # Ctrl+C
                raise KeyboardInterrupt
            else:
                try:
                    return raw.decode('utf-8', errors='ignore').lower()
                except (UnicodeDecodeError, ValueError):
                    return None
        return None
    except (ImportError, ModuleNotFoundError, OSError):
        pass

    # Try termios (Unix-like systems)
    try:
        import tty
        import termios
        import select as select_module
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdin.flush()
            r, _, _ = select_module.select([sys.stdin], [], [], 0.1)
            if r:
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    buf = ch
                    for _ in range(4):
                        r, _, _ = select_module.select([sys.stdin], [], [], 0.01)
                        if r:
                            buf += sys.stdin.read(1)
                            if buf == '\x1b[A':
                                return 'up'
                            elif buf == '\x1b[B':
                                return 'down'
                            elif buf == '\x1b[C':
                                return 'right'
                            elif buf == '\x1b[D':
                                return 'left'
                        else:
                            break
                    return 'esc' if len(buf) == 1 else None
                elif ch in ('\n', '\r'):
                    return 'enter'
                elif ch == '\t':
                    return 'tab'
                elif ch == ' ':
                    return ' '
                elif ch == '\x03':  # Ctrl+C
                    raise KeyboardInterrupt
                else:
                    return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except (ImportError, ModuleNotFoundError, OSError, AttributeError):
        pass

    return None


def select_file_ui(start_dir: str | None = None) -> str | None:
    """Terminal UI for selecting an audio file with directory tree navigation.
    
    Args:
        start_dir: Initial directory to browse. Defaults to current working directory.
        
    Returns:
        Path to selected audio file, or None if user cancelled.
    """
    import curses

    # Validate and set starting directory
    if start_dir is None:
        start_dir = os.getcwd()

    if not os.path.isdir(start_dir):
        start_dir = os.path.dirname(start_dir)

    current_dir = start_dir
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
                controls = "[CONTROLS: Up/Down navigate | Enter select | Left/ESC up | PGUP/PGDN scroll | q quit]"
                stdscr.addstr(0, 0, controls[:width - 1])
                separator = "-" * min(width, 50)
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
            elif (isinstance(processed_key, str) and processed_key.isdigit() 
                  and items):
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


def print_controls() -> None:
    """Display the control instructions."""
    print("\n" + "=" * 50)
    print("  Sebs_Musicbowl - Terminal Music Player")
    print("=" * 50)
    print("\nControls:")
    print("  p  - Pause / Resume")
    print("  s  - Stop")
    print("  q  - Quit")
    print("  +  - Increase volume")
    print("  -  - Decrease volume")
    print("  h  - Show help")
    print("=" * 50 + "\n")



def refresh_display(filepath: str, volume: float, paused: bool) -> None:
    """Refresh the player display with current track info."""
    clear_screen()
    print(f"Now Playing: {os.path.basename(filepath)}")
    print(f"Volume: {int(volume * 100)}%")
    print(f"Status: {'Paused' if paused else 'Playing'}")
    print_controls()


def play_music(filepath: str) -> bool:
    """Play the music file with interactive controls.
    
    Args:
        filepath: Path to the audio file to play.
        
    Returns:
        True if user wants to continue selecting files, False to quit.
    """
    # Initialize pygame mixer
    pygame.mixer.init()

    try:
        # Load the music file
        pygame.mixer.music.load(filepath)

        # Set initial volume (0.0 to 1.0)
        volume = DEFAULT_VOLUME
        pygame.mixer.music.set_volume(volume)

        # Start playback
        pygame.mixer.music.play()

        refresh_display(filepath, volume, False)

        # Main control loop - check keys directly without background thread
        paused = False

        while True:
            # Check if song finished naturally (not paused)
            if not pygame.mixer.music.get_busy() and not paused:
                print("\nTrack finished.")
                return True

            # Check for user input directly
            key = read_key()

            if key == 'p':
                paused = not paused
                if paused:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
                refresh_display(filepath, volume, paused)
            elif key in ('s', 'left'):
                pygame.mixer.music.stop()
                print("\nStopped")
                return True
            elif key == 'q':
                pygame.mixer.music.stop()
                return False
            elif key == '+':
                volume = min(1.0, volume + VOLUME_STEP)
                pygame.mixer.music.set_volume(volume)
                refresh_display(filepath, volume, paused)
            elif key == '-':
                volume = max(0.0, volume - VOLUME_STEP)
                pygame.mixer.music.set_volume(volume)
                refresh_display(filepath, volume, paused)
            elif key == 'h':
                refresh_display(filepath, volume, paused)

            # Small delay to prevent CPU overload
            time.sleep(0.05)

    except pygame.error as e:
        print(f"\nError loading file: {e}")
        print("Please ensure the file is a supported audio format (MP3, WAV, OGG, etc.).")
        return True
    except KeyboardInterrupt:
        print("\nStopped by user.")
        return False
    finally:
        pygame.mixer.quit()


def main() -> None:
    """Main entry point."""
    # Initialize pygame
    pygame.init()
    
    try:
        parser = argparse.ArgumentParser(
            description='Sebs_Musicbowl - Simple Terminal Music Player'
        )
        parser.add_argument(
            'filepath',
            nargs='?',
            help='Path to the music file to play'
        )

        args = parser.parse_args()

        # Determine starting directory
        if args.filepath:
            if not os.path.exists(args.filepath):
                print(f"Error: File not found at '{args.filepath}'")
                sys.exit(1)
            start_dir = os.path.dirname(args.filepath)
            # Play the provided file first
            if not play_music(args.filepath):
                return
        else:
            start_dir = os.getcwd()

        # Main loop for continuous playback
        while True:
            filepath = select_file_ui(start_dir)
            if filepath is None:
                print("\nNo file selected. Exiting.")
                break
            
            start_dir = os.path.dirname(filepath)
            if not play_music(filepath):
                break
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
