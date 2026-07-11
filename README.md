# Sebs_Musicbowl
A simple terminal-based music player written in Python.

## Version 0.1

A minimal terminal music player that plays audio files from a specified filepath.

### Features
- Play MP3, WAV, OGG, FLAC, AAC, M4A, OPUS, and other supported audio formats
- Interactive keyboard controls while playing
- Volume adjustment
- Pause/Resume functionality
- Terminal file selector UI with navigation
- Recursive directory scanning for audio files
- Settings dialog with persistent default directory configuration

### Requirements
- Python 3.x
- pygame library
- readchar library (recommended for single-key input)

### Installation
```bash
pip install pygame readchar
```

### Usage
```bash
# Play a file directly
python musicbowl.py /path/to/your/music.mp3

# Or run without arguments to be prompted for a file
python musicbowl.py
```

### Player Controls
- **SPACE** - Pause / Resume
- **s** - Stop
- **q** - Quit
- **+** - Increase volume
- **-** - Decrease volume

### File Selector Controls
- **↑/↓** - Navigate items
- **Enter/→** - Select directory or file
- **←** - Go up one directory
- **ESC** - Open settings dialog
- **q** - Quit selector

### Settings
- Press **ESC** in the file selector to open the settings dialog
- Configure your default opening directory for the file browser
- Settings are saved in `~/.sebs_musicbowl/config.json`
- Default opening directory is `/home` when no settings exist
