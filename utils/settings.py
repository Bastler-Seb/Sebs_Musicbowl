"""
Settings Module

Provides configuration management for the music player.
Handles loading and saving user preferences like default directory.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


# Settings file path
SETTINGS_DIR = Path.home() / ".sebs_musicbowl"
SETTINGS_FILE = SETTINGS_DIR / "config.json"


class Settings:
    """Manages application settings with persistent storage."""
    
    def __init__(self):
        """Initialize settings with default values."""
        self._settings: Dict[str, Any] = {
            'default_directory': None,
            'volume': 0.7,
            'last_played': None,
        }
        self._load()
    
    def _load(self) -> None:
        """Load settings from config file."""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Update existing settings with loaded values
                    for key, value in loaded_settings.items():
                        if key in self._settings:
                            self._settings[key] = value
        except (json.JSONDecodeError, IOError, PermissionError) as e:
            # If loading fails, use defaults
            print(f"Warning: Could not load settings: {e}")
    
    def _save(self) -> None:
        """Save settings to config file."""
        try:
            # Create settings directory if it doesn't exist
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            
            # Save settings
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
        except (IOError, PermissionError) as e:
            print(f"Warning: Could not save settings: {e}")
    
    def get_default_directory(self) -> Optional[str]:
        """Get the default directory for the file browser. Defaults to /home."""
        default_dir = self._settings.get('default_directory')
        # Validate that the directory exists
        if default_dir and os.path.isdir(default_dir):
            return default_dir
        # Default to /home
        return "/home"
    
    def set_default_directory(self, directory: str) -> None:
        """Set the default directory for the file browser."""
        if os.path.isdir(directory):
            self._settings['default_directory'] = directory
            self._save()
        else:
            print(f"Warning: Directory does not exist: {directory}")
    
    def get_volume(self) -> float:
        """Get the default volume."""
        return float(self._settings.get('volume', 0.7))
    
    def set_volume(self, volume: float) -> None:
        """Set the default volume."""
        self._settings['volume'] = max(0.0, min(1.0, volume))
        self._save()
    
    def get_last_played(self) -> Optional[str]:
        """Get the last played file."""
        return self._settings.get('last_played')
    
    def set_last_played(self, filepath: str) -> None:
        """Set the last played file."""
        self._settings['last_played'] = filepath
        self._save()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self._settings = {
            'default_directory': None,
            'volume': 0.7,
            'last_played': None,
        }
        self._save()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary."""
        return self._settings.copy()


# Global settings instance
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reset_settings_instance() -> None:
    """Reset the global settings instance (useful for testing)."""
    global _settings_instance
    _settings_instance = None
