#!/usr/bin/env python3
"""
Sebs_Musicbowl - Simple Terminal Music Player

A minimal Python terminal program that plays music from a specified filepath.
Uses pygame for audio playback.

Usage:
    python musicbowl.py [filepath]
    
    If no filepath is provided, you will be prompted to enter one.

Controls while playing:
    p   - Pause / Resume
    s   - Stop
    q   - Quit
    +   - Increase volume
    -   - Decrease volume
    h   - Show help

File Selector Controls:
    ↑/↓ arrows   - Navigate items
    →/Enter      - Enter directory or select file
    ←/ESC        - Go up one directory
    q            - Quit selector
"""

import sys
import os
import argparse
import pygame
import threading

# Try to import readchar for single-key input
try:
    import readchar
    USE_READCHAR = True
except ImportError:
    USE_READCHAR = False

# Audio file extensions to look for
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.mp4', '.opus']


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def is_audio_file(filepath):
    """Check if a file is an audio file based on extension."""
    return any(filepath.lower().endswith(ext) for ext in AUDIO_EXTENSIONS)


def get_directory_contents(directory):
    """Get list of directories and audio files in a directory."""
    items = []
    try:
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isdir(full_path) and not item.startswith('.'):
                items.append({'name': item, 'path': full_path, 'type': 'dir'})
            elif os.path.isfile(full_path) and is_audio_file(item):
                items.append({'name': item, 'path': full_path, 'type': 'file'})
    except PermissionError:
        pass
    # Sort: directories first, then files, both alphabetically
    dirs = [i for i in items if i['type'] == 'dir']
    files = [i for i in items if i['type'] == 'file']
    dirs.sort(key=lambda x: x['name'].lower())
    files.sort(key=lambda x: x['name'].lower())
    return dirs + files


def select_file_ui(start_dir=None):
    """Terminal UI for selecting an audio file with directory tree navigation."""
    if start_dir is None:
        start_dir = os.getcwd()
    
    if not os.path.isdir(start_dir):
        start_dir = os.path.dirname(start_dir)
    
    current_dir = start_dir
    selected_index = 0
    
    while True:
        # Get items in current directory
        items = get_directory_contents(current_dir)
        
        # Display directory tree
        clear_screen()
        print("=" * 50)
        print("  Sebs_Musicbowl - File Selector")
        print("=" * 50)
        print(f"\nCurrent: {current_dir}")
        print("-" * 50)
        
        if not items:
            print("  (No audio files or directories found)")
        else:
            for i, item in enumerate(items):
                prefix = "  > " if i == selected_index else "     "
                suffix = "/" if item['type'] == 'dir' else ""
                print(f"{prefix}{item['name']}{suffix}")
        
        print("-" * 50)
        print("Controls: ↑/↓ - navigate, →/Enter - enter/select, ←/ESC - go up, q - quit")
        
        # Get key press
        try:
            if USE_READCHAR:
                key = readchar.readchar()
            else:
                try:
                    import msvcrt
                    key = msvcrt.getch().decode('utf-8', errors='ignore')
                except:
                    key = None
        except KeyboardInterrupt:
            return None
        
        if key is None:
            import time
            time.sleep(0.1)
            continue
        
        # Handle keys - check readchar keys first if available
        if USE_READCHAR:
            # readchar returns key objects
            if key == readchar.key.UP:
                selected_index = max(0, selected_index - 1)
            elif key == readchar.key.DOWN:
                selected_index = min(len(items) - 1 if items else 0, selected_index + 1)
            elif key == readchar.key.RIGHT:
                if items and items[selected_index]['type'] == 'dir':
                    current_dir = items[selected_index]['path']
                    selected_index = 0
            elif key == readchar.key.LEFT:
                current_dir = os.path.dirname(current_dir)
                selected_index = 0
            elif key == readchar.key.ENTER:
                if items and selected_index < len(items):
                    if items[selected_index]['type'] == 'dir':
                        current_dir = items[selected_index]['path']
                        selected_index = 0
                    else:
                        return items[selected_index]['path']
            elif key == readchar.key.ESC:
                current_dir = os.path.dirname(current_dir)
                selected_index = 0
            elif key == 'q':
                return None
            elif key == '\x03':  # Ctrl+C
                return None
        else:
            # Non-readchar mode (msvcrt or fallback)
            if key == 'q':
                return None
            elif key == '\x1b':  # ESC or start of arrow sequence
                try:
                    import msvcrt
                    import time
                    time.sleep(0.05)
                    if msvcrt.kbhit():
                        next_key = msvcrt.getch()
                        if next_key == b'[':  # Arrow key
                            next_next = msvcrt.getch()
                            if next_next == b'A':  # Up
                                selected_index = max(0, selected_index - 1)
                            elif next_next == b'B':  # Down
                                selected_index = min(len(items) - 1, selected_index + 1)
                            elif next_next == b'C':  # Right
                                if items and items[selected_index]['type'] == 'dir':
                                    current_dir = items[selected_index]['path']
                                    selected_index = 0
                            elif next_next == b'D':  # Left
                                current_dir = os.path.dirname(current_dir)
                                selected_index = 0
                        else:
                            # Just ESC
                            current_dir = os.path.dirname(current_dir)
                            selected_index = 0
                    else:
                        # Just ESC
                        current_dir = os.path.dirname(current_dir)
                        selected_index = 0
                except:
                    current_dir = os.path.dirname(current_dir)
                    selected_index = 0
            elif key in ('\r', '\n'):  # Enter
                if items and selected_index < len(items):
                    if items[selected_index]['type'] == 'dir':
                        current_dir = items[selected_index]['path']
                        selected_index = 0
                    else:
                        return items[selected_index]['path']
            elif key == '\x03':  # Ctrl+C
                return None
            elif key == '\x08' or key == '\x7f':  # Backspace/Delete
                current_dir = os.path.dirname(current_dir)
                selected_index = 0
            elif key.isdigit() and items and int(key) <= len(items):
                # Numeric selection
                selected_item = items[int(key) - 1] if int(key) > 0 else items[0]
                if selected_item['type'] == 'dir':
                    current_dir = selected_item['path']
                    selected_index = 0
                else:
                    return selected_item['path']


def print_controls():
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


def get_file_path():
    """Get the music file path from user input."""
    while True:
        filepath = input("Enter the path to the music file: ").strip()
        if os.path.exists(filepath):
            return filepath
        print(f"Error: File not found at '{filepath}'")
        print("Please enter a valid file path.")


class KeyListener:
    """Background thread to listen for single key presses."""
    def __init__(self):
        self.key_pressed = None
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
    
    def _listen(self):
        """Listen for key presses in a loop."""
        while self.running:
            try:
                if USE_READCHAR:
                    self.key_pressed = readchar.readchar()
                else:
                    # Fallback: use msvcrt on Windows or standard input
                    try:
                        import msvcrt
                        if msvcrt.kbhit():
                            self.key_pressed = msvcrt.getch().decode('utf-8', errors='ignore')
                        else:
                            import time
                            time.sleep(0.1)
                            continue
                    except:
                        import time
                        time.sleep(0.1)
            except:
                pass
    
    def get_key(self):
        """Get the last pressed key and clear it."""
        key = self.key_pressed
        self.key_pressed = None
        return key
    
    def stop(self):
        """Stop the listener thread."""
        self.running = False
        self.thread.join(timeout=0.1)


def play_music(filepath):
    """Play the music file with interactive controls."""
    # Initialize pygame mixer
    pygame.mixer.init()
    
    # Start key listener
    key_listener = KeyListener()
    
    try:
        # Load the music file
        pygame.mixer.music.load(filepath)
        
        # Set initial volume (0.0 to 1.0)
        volume = 0.7
        pygame.mixer.music.set_volume(volume)
        
        # Start playback
        pygame.mixer.music.play()
        
        clear_screen()
        print(f"Now Playing: {os.path.basename(filepath)}")
        print(f"Volume: {int(volume * 100)}%")
        print(f"Status: Playing")
        print_controls()
        
        # Main control loop
        running = True
        paused = False
        
        while running:
            # Check if song finished naturally (not paused)
            if not pygame.mixer.music.get_busy() and not paused:
                print("\nTrack finished.")
                running = False
                break
            
            # Check for user input
            key = key_listener.get_key()
            
            if key:
                if key == 'p':
                    if paused:
                        pygame.mixer.music.unpause()
                        paused = False
                    else:
                        pygame.mixer.music.pause()
                        paused = True
                    clear_screen()
                    print(f"Now Playing: {os.path.basename(filepath)}")
                    print(f"Volume: {int(volume * 100)}%")
                    print(f"Status: {'Paused' if paused else 'Playing'}")
                    print_controls()
                elif key == 's':
                    pygame.mixer.music.stop()
                    print("\nStopped")
                    running = False
                elif key == 'q':
                    pygame.mixer.music.stop()
                    running = False
                elif key == '+':
                    volume = min(1.0, volume + 0.1)
                    pygame.mixer.music.set_volume(volume)
                    clear_screen()
                    print(f"Now Playing: {os.path.basename(filepath)}")
                    print(f"Volume: {int(volume * 100)}%")
                    print(f"Status: {'Paused' if paused else 'Playing'}")
                    print_controls()
                elif key == '-':
                    volume = max(0.0, volume - 0.1)
                    pygame.mixer.music.set_volume(volume)
                    clear_screen()
                    print(f"Now Playing: {os.path.basename(filepath)}")
                    print(f"Volume: {int(volume * 100)}%")
                    print(f"Status: {'Paused' if paused else 'Playing'}")
                    print_controls()
                elif key.lower() == 'h':
                    clear_screen()
                    print(f"Now Playing: {os.path.basename(filepath)}")
                    print(f"Volume: {int(volume * 100)}%")
                    print(f"Status: {'Paused' if paused else 'Playing'}")
                    print_controls()
            
            # Small delay to prevent CPU overload
            import time
            time.sleep(0.05)
    
    except pygame.error as e:
        print(f"\nError loading file: {e}")
        print("Please ensure the file is a supported audio format (MP3, WAV, OGG).")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        key_listener.stop()
        pygame.mixer.quit()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Sebs_Musicbowl - Simple Terminal Music Player'
    )
    parser.add_argument(
        'filepath',
        nargs='?',
        help='Path to the music file to play'
    )
    
    args = parser.parse_args()
    
    # Get file path
    if args.filepath:
        filepath = args.filepath
        if not os.path.exists(filepath):
            print(f"Error: File not found at '{filepath}'")
            sys.exit(1)
    else:
        # Use file selector UI
        filepath = select_file_ui()
        if filepath is None:
            print("\nNo file selected. Exiting.")
            sys.exit(0)
    
    # Play the music
    play_music(filepath)


if __name__ == '__main__':
    main()
