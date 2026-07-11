"""
Input Utilities Module

Provides cross-platform key reading functionality for terminal applications.
"""

import os
import sys
from typing import Optional


# Type alias
KeyName = str


def _read_key_readchar() -> Optional[KeyName]:
    """Read key using readchar library."""
    try:
        import readchar
    except (ImportError, ModuleNotFoundError):
        return None

    try:
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
    except OSError:
        return None


def _read_key_msvcrt() -> Optional[KeyName]:
    """Read key using msvcrt (Windows)."""
    try:
        import msvcrt
    except (ImportError, ModuleNotFoundError):
        return None

    try:
        if not msvcrt.kbhit():
            return None

        raw = msvcrt.getch()
        if raw in (b'\xe0', b'\x00'):
            # Arrow or function key
            next_raw = msvcrt.getch()
            if next_raw == b'H':
                return 'up'
            elif next_raw == b'P':
                return 'down'
            elif next_raw == b'K':
                return 'left'
            elif next_raw == b'M':
                return 'right'
            return None
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
    except OSError:
        return None


def _read_key_termios() -> Optional[KeyName]:
    """Read key using termios (Unix-like systems)."""
    try:
        import tty
        import termios
        import select as select_module
    except (ImportError, ModuleNotFoundError):
        return None

    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
    except (termios.error, OSError):
        return None

    try:
        tty.setraw(fd)
        sys.stdin.flush()
        r, _, _ = select_module.select([sys.stdin], [], [], 0.05)
        if not r:
            return None

        ch = sys.stdin.read(1)
        if ch == '\x1b':
            # Escape sequence
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
    except (OSError, AttributeError):
        return None
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except (termios.error, OSError):
            pass


def read_key() -> Optional[KeyName]:
    """Read a single key press for player controls.
    
    Tries multiple methods in order of preference:
    1. readchar (cross-platform, if installed)
    2. msvcrt (Windows)
    3. termios (Unix-like systems)
    
    Returns:
        String representing the key ('up', 'down', 'left', 'right', 'enter',
        'esc', 'tab', ' ', or lowercase character) or None if no key pressed.
        
    Raises:
        KeyboardInterrupt: If Ctrl+C is pressed.
    """
    # Try readchar first (best cross-platform support)
    result = _read_key_readchar()
    if result is not None:
        return result

    # Try msvcrt (Windows)
    result = _read_key_msvcrt()
    if result is not None:
        return result

    # Try termios (Unix-like systems)
    return _read_key_termios()
