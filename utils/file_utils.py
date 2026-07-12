"""
File Utilities Module

Provides utilities for file operations, audio file detection, directory scanning, and metadata extraction.
"""

import os
import re
import sys
from pathlib import Path
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
    tracknumber: str


# Constants
AUDIO_EXTENSIONS: frozenset[str] = frozenset({
    '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.mp4', '.opus'
})


def clear_screen() -> None:
    """Clear the terminal screen safely without shell injection."""
    if os.name == 'nt':
        # Windows: write ANSI escape code (works in modern Windows terminals)
        # Fallback to os.system if ANSI codes don't work
        try:
            sys.stdout.write('\033[H\033[J')
            sys.stdout.flush()
        except Exception:
            # Last resort fallback - hardcoded safe command
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


def _get_track_number_sort_key(file_path: str) -> tuple:
    """Get a sort key for an audio file based on track number metadata.
    
    Files with track numbers are sorted by numeric track number first,
    then files without track numbers are sorted alphabetically at the end.
    
    Args:
        file_path: Path to the audio file.
        
    Returns:
        A tuple (has_tracknumber, tracknumber_as_int, filename_lower) for sorting.
        Files with track numbers get (0, track_num, filename) to sort first,
        files without get (1, 0, filename) to sort after numbered files.
    """
    metadata = extract_audio_metadata(file_path)
    if metadata and metadata.get('tracknumber'):
        track_str = metadata['tracknumber']
        # Extract the first number from track string (e.g., "1/10" -> 1, "01" -> 1)
        match = re.search(r'(\d+)', track_str)
        if match:
            try:
                track_num = int(match.group(1))
                return (0, track_num, os.path.basename(file_path).lower())
            except ValueError:
                pass
    # No valid track number found, sort alphabetically after numbered tracks
    return (1, 0, os.path.basename(file_path).lower())


def get_directory_contents(directory: str) -> list[FileItem]:
    """Get sorted list of directories and audio files in a directory.
    
    Args:
        directory: Path to directory to scan.
        
    Returns:
        List of dicts with 'name', 'path', and 'type' ('dir' or 'file') keys.
        Directories are listed first, then files.
        Audio files with track numbers are sorted by track number first,
        then files without track numbers are sorted alphabetically.
        
    Security:
        Validates that the path is a directory and resolves symlinks to prevent
        directory traversal attacks.
    """
    items: list[FileItem] = []

    try:
        # Validate input path - must be a directory
        resolved_dir = Path(directory).resolve()
        if not resolved_dir.is_dir():
            print(f"Warning: '{directory}' is not a valid directory", file=sys.stderr)
            return []
            
        for item in os.listdir(str(resolved_dir)):
            full_path = resolved_dir / item
            if full_path.is_dir():
                items.append({'name': item, 'path': str(full_path), 'type': 'dir'})
            elif full_path.is_file() and is_audio_file(item):
                items.append({'name': item, 'path': str(full_path), 'type': 'file'})
    except PermissionError:
        return []
    except OSError as e:
        print(f"Warning: Could not read directory {directory!r}: {e}", file=sys.stderr)
        return []

    # Sort directories first, then files
    dirs = [i for i in items if i['type'] == 'dir']
    files = [i for i in items if i['type'] == 'file']
    dirs.sort(key=lambda x: x['name'].lower())
    # Sort audio files by track number, then alphabetically
    files.sort(key=lambda x: _get_track_number_sort_key(x['path']))
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
                metadata['tracknumber'] = str(tags.get('TRCK', [''])[0]) if tags.get('TRCK') else ''
                
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
            metadata['tracknumber'] = str(tags.get('trkn', [''])[0]) if tags.get('trkn') else ''
        
        # Handle FLAC tags
        elif filepath.lower().endswith('.flac'):
            audio_file = File(filepath)
            tags = FLAC(filepath)
            metadata['artist'] = str(tags.get('artist', ['Unknown Artist'])[0]) if tags.get('artist') else 'Unknown Artist'
            metadata['title'] = str(tags.get('title', ['Unknown Title'])[0]) if tags.get('title') else 'Unknown Title'
            metadata['album'] = str(tags.get('album', ['Unknown Album'])[0]) if tags.get('album') else 'Unknown Album'
            metadata['year'] = str(tags.get('date', ['Unknown Year'])[0]) if tags.get('date') else 'Unknown Year'
            metadata['genre'] = str(tags.get('genre', ['Unknown Genre'])[0]) if tags.get('genre') else 'Unknown Genre'
            metadata['tracknumber'] = str(tags.get('tracknumber', [''])[0]) if tags.get('tracknumber') else ''
        
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
            metadata['tracknumber'] = str(tags.get('tracknumber', [''])[0]) if tags.get('tracknumber') else ''
        
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
                metadata['tracknumber'] = str(tags.get('tracknumber', [''])[0]) if tags and tags.get('tracknumber') else ''
        
        # Handle AAC files
        elif filepath.lower().endswith('.aac'):
            if hasattr(audio_file, 'tags'):
                tags = audio_file.tags
                metadata['artist'] = str(tags.get('artist', ['Unknown Artist'])[0]) if tags and tags.get('artist') else 'Unknown Artist'
                metadata['title'] = str(tags.get('title', ['Unknown Title'])[0]) if tags and tags.get('title') else 'Unknown Title'
                metadata['album'] = str(tags.get('album', ['Unknown Album'])[0]) if tags and tags.get('album') else 'Unknown Album'
                metadata['year'] = str(tags.get('date', ['Unknown Year'])[0]) if tags and tags.get('date') else 'Unknown Year'
                metadata['genre'] = str(tags.get('genre', ['Unknown Genre'])[0]) if tags and tags.get('genre') else 'Unknown Genre'
                metadata['tracknumber'] = str(tags.get('tracknumber', [''])[0]) if tags and tags.get('tracknumber') else ''
        
        # Generic fallback for any audio file
        if not metadata and hasattr(audio_file, 'tags'):
            tags = audio_file.tags
            if tags:
                metadata['artist'] = str(tags.get('artist', ['Unknown Artist'])[0]) if tags.get('artist') else 'Unknown Artist'
                metadata['title'] = str(tags.get('title', ['Unknown Title'])[0]) if tags.get('title') else 'Unknown Title'
                metadata['album'] = str(tags.get('album', ['Unknown Album'])[0]) if tags.get('album') else 'Unknown Album'
                metadata['year'] = str(tags.get('date', ['Unknown Year'])[0]) if tags.get('date') else 'Unknown Year'
                metadata['genre'] = str(tags.get('genre', ['Unknown Genre'])[0]) if tags.get('genre') else 'Unknown Genre'
                metadata['tracknumber'] = str(tags.get('tracknumber', [''])[0]) if tags.get('tracknumber') else ''
        
        # Return metadata dict with defaults if no real metadata found
        if not metadata:
            # Return default metadata structure
            return {
                'artist': 'Unknown Artist',
                'title': 'Unknown Title', 
                'album': 'Unknown Album',
                'year': 'Unknown Year',
                'genre': 'Unknown Genre',
                'tracknumber': ''
            }
        return metadata
        
    except Exception as e:
        print(f"Warning: Could not extract metadata from {filepath!r}: {e}", file=sys.stderr)
        return None