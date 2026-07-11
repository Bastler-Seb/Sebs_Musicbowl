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
"""

import sys
import os
import argparse
import pygame
import time
import select
import tty
import termios

# Platform-specific imports
try:
    import msvcrt
    WINDOWS = True
except ImportError:
    WINDOWS = False


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
    print("=" * 50 + "\n")


def get_file_path():
    """Get the music file path from user input."""
    while True:
        filepath = input("Enter the path to the music file: ").strip()
        if os.path.exists(filepath):
            return filepath
        print(f"Error: File not found at '{filepath}'")
        print("Please enter a valid file path.")


def get_key_press():
    """Check if a key was pressed and return it, otherwise return None."""
    if WINDOWS:
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8', errors='ignore')
        return None
    else:
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            return sys.stdin.read(1)
        return None


def play_music(filepath):
    """Play the music file with interactive controls."""
    # Initialize pygame mixer
    pygame.mixer.init()
    
    # Setup terminal for Unix systems
    old_settings = None
    if not WINDOWS:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(fd)
    
    try:
        # Load the music file
        pygame.mixer.music.load(filepath)
        
        # Set initial volume (0.0 to 1.0)
        volume = 0.7
        pygame.mixer.music.set_volume(volume)
        
        # Start playback
        pygame.mixer.music.play()
        
        clear_screen()
        print(f"\nNow Playing: {os.path.basename(filepath)}")
        print(f"Volume: {int(volume * 100)}%")
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
            key = get_key_press()
            
            if key:
                if key == 'p':
                    if paused:
                        pygame.mixer.music.unpause()
                        paused = False
                        print("\nResumed")
                    else:
                        pygame.mixer.music.pause()
                        paused = True
                        print("\nPaused")
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
                    print(f"\nVolume: {int(volume * 100)}%")
                elif key == '-':
                    volume = max(0.0, volume - 0.1)
                    pygame.mixer.music.set_volume(volume)
                    print(f"\nVolume: {int(volume * 100)}%")
                elif key.lower() == 'h':
                    clear_screen()
                    print(f"\nNow Playing: {os.path.basename(filepath)}")
                    print(f"Volume: {int(volume * 100)}%")
                    print_controls()
            
    except pygame.error as e:
        print(f"\nError loading file: {e}")
        print("Please ensure the file is a supported audio format (MP3, WAV, OGG).")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        # Restore terminal settings for Unix
        if not WINDOWS and old_settings is not None:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
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
