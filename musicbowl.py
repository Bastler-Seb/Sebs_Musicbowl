#!/usr/bin/env python3
"""
Sebs_Musicbowl - Simple Terminal Music Player (Legacy Entry Point)

This file maintains backward compatibility with the original musicbowl.py interface.
It now delegates to the modular architecture defined in main.py.

For new development, use main.py or import the modules directly.

Usage:
    python musicbowl.py [filepath]

    If no filepath is provided, you will be prompted to enter one.

Controls while playing:
    SPACE   - Pause / Resume
    s       - Stop (return to selection)
    Left    - Stop (return to selection)
    q       - Quit
    +       - Increase volume
    -       - Decrease volume

File Selector Controls:
    Up/Down arrows   - Navigate items
    Enter/Right      - Select directory or file
    Left             - Go up one directory
    ESC              - Open settings dialog
    q                - Quit selector
"""

import sys
import os

# Delegate to the new modular main.py
if __name__ == '__main__':
    # Add the current directory to the path so imports work
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import and run the new main
    from main import main
    main()
