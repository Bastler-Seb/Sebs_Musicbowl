"""
File Utilities Module

Provides utilities for file operations, audio file detection, directory scanning, and metadata extraction.
"""

import os
import sys
from typing import Optional, TypedDict


# Type aliases
FileItem = dict[str, str]
KeyName = str

# Metadata type definition
class AudioMetadata(TypedDict, total=False):
    """TypedDict for audio file metadata."""
    artist: str
    title: str
    album: str
    year: str
    genre: str


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


def extract_audio_metadata(filepath: str) -> Optional[AudioMetadata]:
    """Extract metadata from an audio file.
    
    Args:
        filepath: Path to the audio file.
        
    Returns:
        AudioMetadata dict with artist, title, album, year, genre,
        or None if metadata cannot be extracted or file is not valid.
        
    Note:
        Requires the 'mutagen' library to be installed.
        Install with: pip install mutagen
    """
    if not validate_audio_filepath(filepath):
        return None
    
    try:
        from mutagen import File
        from mutagen.id3 import ID3, ID3NoHeaderError
        from mutagen.mp4 import MP4
        from mutagen.flac import FLAC
        from mutagen.oggopus import OggOpus
        from mutagen.oggvorbis import OggVorbis
    except ImportError:
        print("Warning: 'mutagen' library is required for metadata extraction.", file=sys.stderr)
        print("Install with: pip install mutagen", file=sys.stderr)
        return None
    
    metadata: AudioMetadata = {}
    
    try:
        audio_file = File(filepath)
        
        if audio_file is None:
            return None
        
        # Handle ID3 tags (MP3)
        if filepath.lower().endswith('.mp3'):
            try:
                audio_file = File(filepath)  # Use File() to get the audio object
                tags = ID3(filepath)
                metadata['artist'] = str(tags.get('TPE1', ['Unknown Artist'])[0]) if tags.get('TPE1') else 'Unknown Artist'
                metadata['title'] = str(tags.get('TIT2', ['Unknown Title'])[0]) if tags.get('TIT2') else 'Unknown Title'
                metadata['album'] = str(tags.get('TALB', ['Unknown Album'])[0]) if tags.get('TALB') else 'Unknown Album'
                metadata['year'] = str(tags.get('TDRC', ['Unknown Year'])[0]) if tags.get('TDRC') else 'Unknown Year'
                metadata['genre'] = str(tags.get('TCON', ['Unknown Genre'])[0]) if tags.get('TCON') else 'Unknown Genre'
                
            except ID3NoHeaderError:
                # No ID3 tags found
                pass
        
        # Handle MP4/M4A tags
        elif filepath.lower().endswith(('.m4a', '.mp4')):
            audio_file = File(filepath)
            tags = MP4(filepath)
            metadata['artist'] = str(tags.get('\xa9ART', ['Unknown Artist'])[0]) if tags.get('\xa9ART') else 'Unknown Artist'
            metadata['title'] = str(tags.get('\xa9nam', ['Unknown Title'])[0]) if tags.get('\xa9nam') else 'Unknown Title'
            metadata['album'] = str(tags.get('\xa9alb', ['Unknown Album'])[0]) if tags.get('\xa9alb') else 'Unknown Album'
            metadata['year'] = str(tags.get('\xa9day', ['Unknown Year'])[0]) if tags.get('\xa9day') else 'Unknown Year'
            metadata['genre'] = str(tags.get('\xa9gen', ['Unknown Genre'])[0]) if tags.get('\xa9gen') else 'Unknown Genre'
        
        # Handle FLAC tags
        elif filepath.lower().endswith('.flac'):
            audio_file = File(filepath)
            tags = FLAC(filepath)
            metadata['artist'] = str(tags.get('artist', ['Unknown Artist'])[0]) if tags.get('artist') else 'Unknown Artist'
            metadata['title'] = str(tags.get('title', ['Unknown Title'])[0]) if tags.get('title') else 'Unknown Title'
            metadata['album'] = str(tags.get('album', ['Unknown Album'])[0]) if tags.get('album') else 'Unknown Album'
            metadata['year'] = str(tags.get('date', ['Unknown Year'])[0]) if tags.get('date') else 'Unknown Year'
            metadata['genre'] = str(tags.get('genre', ['Unknown Genre'])[0]) if tags.get('genre') else 'Unknown Genre'
        
        # Handle OGG tags (Vorbis and Opus)
        elif filepath.lower().endswith(('.ogg', '.opus')):
            try:
                tags = OggVorbis(filepath)
            except:
                tags = OggOpus(filepath)
            
            metadata['artist'] = str(tags.get('artist', ['Unknown Artist'])[0]) if tags.get('artist') else 'Unknown Artist'
            metadata['title'] = str(tags.get('title', ['Unknown Title'])[0]) if tags.get('title') else 'Unknown Title'
            metadata['album'] = str(tags.get('album', ['Unknown Album'])[0]) if tags.get('album') else 'Unknown Album'
            metadata['year'] = str(tags.get('date', ['Unknown Year'])[0]) if tags.get('date') else 'Unknown Year'
            metadata['genre'] = str(tags.get('genre', ['Unknown Genre'])[0]) if tags.get('genre') else 'Unknown Genre'
        
        # Handle WAV files (limited tagging support)
        elif filepath.lower().endswith('.wav'):
            # WAV files don't commonly have metadata, but we try with mutagen
            if hasattr(audio_file, 'tags'):
                tags = audio_file.tags
                metadata['artist'] = str(tags.get('artist', ['Unknown Artist'])[0]) if tags and tags.get('artist') else 'Unknown Artist'
                metadata['title'] = str(tags.get('title', ['Unknown Title'])[0]) if tags and tags.get('title') else 'Unknown Title'
                metadata['album'] = str(tags.get('album', ['Unknown Album'])[0]) if tags and tags.get('album') else 'Unknown Album'
                metadata['year'] = str(tags.get('date', ['Unknown Year'])[0]) if tags and tags.get('date') else 'Unknown Year'
                metadata['genre'] = str(tags.get('genre', ['Unknown Genre'])[0]) if tags and tags.get('genre') else 'Unknown Genre'
        
        # Handle AAC files
        elif filepath.lower().endswith('.aac'):
            if hasattr(audio_file, 'tags'):
                tags = audio_file.tags
                metadata['artist'] = str(tags.get('artist', ['Unknown Artist'])[0]) if tags and tags.get('artist') else 'Unknown Artist'
                metadata['title'] = str(tags.get('title', ['Unknown Title'])[0]) if tags and tags.get('title') else 'Unknown Title'
                metadata['album'] = str(tags.get('album', ['Unknown Album'])[0]) if tags and tags.get('album') else 'Unknown Album'
                metadata['year'] = str(tags.get('date', ['Unknown Year'])[0]) if tags and tags.get('date') else 'Unknown Year'
                metadata['genre'] = str(tags.get('genre', ['Unknown Genre'])[0]) if tags and tags.get('genre') else 'Unknown Genre'
        
        # Generic fallback for any audio file
        if not metadata and hasattr(audio_file, 'tags'):
            tags = audio_file.tags
            if tags:
                metadata['artist'] = str(tags.get('artist', ['Unknown Artist'])[0]) if tags.get('artist') else 'Unknown Artist'
                metadata['title'] = str(tags.get('title', ['Unknown Title'])[0]) if tags.get('title') else 'Unknown Title'
                metadata['album'] = str(tags.get('album', ['Unknown Album'])[0]) if tags.get('album') else 'Unknown Album'
                metadata['year'] = str(tags.get('date', ['Unknown Year'])[0]) if tags.get('date') else 'Unknown Year'
                metadata['genre'] = str(tags.get('genre', ['Unknown Genre'])[0]) if tags.get('genre') else 'Unknown Genre'
        
        # Return metadata dict with defaults if no real metadata found
        if not metadata:
            # Return default metadata structure
            return {
                'artist': 'Unknown Artist',
                'title': 'Unknown Title', 
                'album': 'Unknown Album',
                'year': 'Unknown Year',
                'genre': 'Unknown Genre'
            }
        return metadata
        
    except Exception as e:
        print(f"Warning: Could not extract metadata from {filepath!r}: {e}", file=sys.stderr)
        return None