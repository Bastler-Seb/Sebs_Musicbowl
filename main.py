#!/usr/bin/env python3
"""
Sebs_Musicbowl - Modular Music Player

This is the main entry point for the modularized music player.
It wires together the player backend and UI frontend using dependency injection.

To replace the terminal UI with a GUI:
1. Implement the UIInterface in a new class (e.g., PyQtUI, TkinterUI)
2. Replace TerminalUI with your new class in the main() function
3. The player logic remains unchanged

Usage:
    python main.py [filepath]
    
    If no filepath is provided, you will be prompted to select one.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import pygame

from player.pygame_player import PygamePlayer
from player.player_interface import PlayerInterface
from ui.terminal_ui import TerminalUI
from ui.ui_interface import UIInterface


def create_player() -> PlayerInterface:
    """
    Factory function to create the player instance.
    
    This can be modified to create different player implementations
    (e.g., VLC, GStreamer) without changing the UI code.
    
    Returns:
        A new PlayerInterface instance.
    """
    return PygamePlayer()


def create_ui() -> UIInterface:
    """
    Factory function to create the UI instance.
    
    To switch to a GUI, replace TerminalUI with your GUI implementation:
    
        return MyGUIPlayer()  # e.g., PyQtUI(), TkinterUI(), etc.
    
    Returns:
        A new UIInterface instance.
    """
    return TerminalUI()


def main() -> None:
    """Main entry point."""
    # Initialize pygame at the application level
    pygame.init()
    
    try:
        # Create player and UI instances
        player = create_player()
        ui = create_ui()
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description='Sebs_Musicbowl - Modular Music Player'
        )
        parser.add_argument(
            'filepath',
            nargs='?',
            help='Path to the music file to play'
        )
        
        args = parser.parse_args()
        
        # Determine starting file
        start_file: Optional[Path] = None
        if args.filepath:
            filepath_str = args.filepath
            if not os.path.exists(filepath_str):
                print(f"Error: File not found at '{filepath_str}'")
                sys.exit(1)
            if not os.path.isfile(filepath_str):
                print(f"Error: '{filepath_str}' is not a file")
                sys.exit(1)
            start_file = Path(filepath_str)
        
        # Run the UI with the player
        ui.run(player, start_file)
        
    finally:
        # Cleanup
        try:
            if 'player' in locals():
                player.cleanup()
        except Exception:
            pass
        try:
            pygame.quit()
        except Exception:
            pass


if __name__ == '__main__':
    main()
