"""
Utils Module

This module provides utility functions and shared resources for the music player.
"""

from .file_utils import AUDIO_EXTENSIONS, FileItem, get_directory_contents, is_audio_file, validate_audio_filepath, clear_screen
from .input_utils import read_key, KeyName
from .settings import Settings, get_settings, reset_settings_instance

__all__ = [
    'AUDIO_EXTENSIONS', 'FileItem', 'get_directory_contents', 'is_audio_file', 
    'validate_audio_filepath', 'clear_screen', 'read_key', 'KeyName',
    'Settings', 'get_settings', 'reset_settings_instance'
]
