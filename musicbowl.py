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


def play_music(filepath):
    """Play the music file with interactive controls."""
    # Initialize pygame mixer
    pygame.mixer.init()
    
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
            if not pygame.mixer.music.get_busy() and not paused:
                # Song finished playing
                print("\nTrack finished.")
                running = False
                break
                
            # Check for user input
            try:
                # Use non-blocking input check
                import msvcrt  # Windows
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8')
            except ImportError:
                # Unix-based systems
                import sys
                import select
                import tty
                import termios
                
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(sys.stdin.fileno())
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                    if rlist:
                        key = sys.stdin.read(1)
                    else:
                        key = None
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            if key:
                if key == 'p':
                    if paused:
                        pygame.mixer.music.unpause()
                        paused = False
                        print("Resumed")
                    else:
                        pygame.mixer.music.pause()
                        paused = True
                        print("Paused")
                elif key == 's':
                    pygame.mixer.music.stop()
                    print("Stopped")
                    running = False
                elif key == 'q':
                    pygame.mixer.music.stop()
                    running = False
                elif key == '+':
                    volume = min(1.0, volume + 0.1)
                    pygame.mixer.music.set_volume(volume)
                    print(f"Volume: {int(volume * 100)}%")
                elif key == '-':
                    volume = max(0.0, volume - 0.1)
                    pygame.mixer.music.set_volume(volume)
                    print(f"Volume: {int(volume * 100)}%")
                elif key.lower() == 'h':
                    clear_screen()
                    print(f"\nNow Playing: {os.path.basename(filepath)}")
                    print(f"Volume: {int(volume * 100)}%")
                    print_controls()
            
            # Small delay to prevent CPU overload
            time.sleep(0.1)
            
    except pygame.error as e:
        print(f"Error loading file: {e}")
        print("Please ensure the file is a supported audio format (MP3, WAV, OGG).")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
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
