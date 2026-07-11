"""
File Utilities Module

Provides utilities for file operations, audio file detection, and directory scanning.
"""

import os
import sys
from typing import Optional, TypedDict


# Type aliases
FileItem = dict[str, str]
KeyName = str

# Constants
AUDIO_EXTENSIONS: frozenset[str] = frozenset({
    '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.mp4', '.opus'
})


def clear_screen() -> None:
    """Clear the terminal screen safely without shell injection."""
    if os.name == 'nt':
        # Windows: use os.system with hardcoded safe command
        os.system('cls')
    else:
        # Unix-like systems: write ANSI escape code directly
        sys.stdout.write('\033[H\033[J')
        sys.stdout.flush()


def is_audio_file(filename: str) -> bool:
    """Check if a file is an audio file based on extension.
    
    Args:
        filename: The filename to check (case-insensitive).
        
    Returns:
        True if the file has an audio extension, False otherwise.
    """
    return filename.lower().endswith(tuple(AUDIO_EXTENSIONS))


def validate_audio_filepath(filepath: str) -> bool:
    """Validate that a filepath exists, is a file, and has an audio extension.
    
    Args:
        filepath: Path to validate.
        
    Returns:
        True if valid audio file, False otherwise.
    """
    if not os.path.exists(filepath):
        return False
    if not os.path.isfile(filepath):
        return False
    return is_audio_file(filepath)


def get_directory_contents(directory: str) -> list[FileItem]:
    """Get sorted list of directories and audio files in a directory.
    
    Args:
        directory: Path to directory to scan.
        
    Returns:
        List of dicts with 'name', 'path', and 'type' ('dir' or 'file') keys.
        Directories are listed first, then files, both sorted alphabetically.
    """
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
    except OSError as e:
        print(f"Warning: Could not read directory {directory!r}: {e}", file=sys.stderr)
        return []

    # Sort directories first, then files
    dirs = [i for i in items if i['type'] == 'dir']
    files = [i for i in items if i['type'] == 'file']
    dirs.sort(key=lambda x: x['name'].lower())
    files.sort(key=lambda x: x['name'].lower())
    return dirs + files
