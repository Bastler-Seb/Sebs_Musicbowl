# Sebs_Musicbowl
A modular terminal-based music player written in Python.

## Version 1.0

A terminal music player with a clean, modular architecture. Supports multiple audio formats with interactive keyboard controls, playlist management, and a file selector interface.

### Architecture
The player features a modular design that separates concerns:
- **`main.py`** - Primary entry point with dependency injection
- **`player/`** - Player backend with interface and Pygame implementation
- **`ui/`** - User interface with terminal implementation
- **`utils/`** - Helper utilities for input, settings, and file operations
- **`musicbowl.py`** - Legacy entry point (delegates to `main.py` for backward compatibility)

### Features
- Play MP3, WAV, OGG, FLAC, AAC, M4A, OPUS, and other pygame-supported audio formats
- Interactive keyboard controls while playing
- Volume adjustment with configurable steps
- Pause/Resume functionality
- Terminal file selector UI with directory navigation
- Recursive directory scanning for audio files
- Playlist management with next/previous track navigation
- Settings dialog with persistent configuration
- Modular design allows swapping UI or player implementations

### Requirements
- Python 3.7+
- pygame library
- readchar library (for single-key input)

### Installation
```bash
# Install dependencies
pip install pygame readchar
```

### Usage
```bash
# Play a file directly using main.py (recommended)
python main.py /path/to/your/music.mp3

# Or run without arguments to open the file selector
python main.py

# Legacy entry point (backward compatible)
python musicbowl.py [filepath]
```

### Player Controls (while playing)
- **SPACE** - Pause / Resume
- **s** - Stop (return to selection)
- **n** - Next track in playlist
- **p** - Previous track in playlist
- **c** - Clear playlist
- **Left Arrow** - Stop (return to selection)
- **q** - Quit
- **+** - Increase volume
- **-** - Decrease volume

### File Selector Controls
- **↑/↓** - Navigate items
- **Enter/→** - Load directory as playlist and play from selected file
- **←** - Go up one directory
- **ESC** - Open settings dialog
- **q** - Quit selector

### Settings
- Press **ESC** in the file selector to open the settings dialog
- Configure your default opening directory for the file browser
- Settings are saved in `~/.sebs_musicbowl/config.json`
- Default opening directory is `/home` when no settings exist

### Project Structure
```
Sebs_Musicbowl/
├── main.py              # Main entry point with DI container
├── musicbowl.py         # Legacy entry point (backward compatible)
├── player/
│   ├── __init__.py
│   ├── player_interface.py   # Abstract player interface
│   ├── player_state.py       # Player state enum
│   ├── playlist.py           # Playlist management
│   └── pygame_player.py      # Pygame implementation
├── ui/
│   ├── __init__.py
│   ├── ui_interface.py       # Abstract UI interface
│   └── terminal_ui.py        # Terminal UI implementation
└── utils/
    ├── __init__.py
    ├── file_utils.py         # File scanning utilities
    ├── input_utils.py        # Input handling
    └── settings.py           # Configuration management
```

