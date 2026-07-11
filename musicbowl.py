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


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


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
        clear_screen()
        print("=" * 50)
        print("  Sebs_Musicbowl - Terminal Music Player")
        print("=" * 50)
        filepath = get_file_path()
    
    # Play the music
    play_music(filepath)


if __name__ == '__main__':
    main()
