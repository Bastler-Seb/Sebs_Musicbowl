# Sebs_Musicbowl
A simple terminal-based music player written in Python.

## Version 1.0 (Rewrite)

A minimal terminal music player that plays audio files from a specified filepath.

### Features
- Play MP3, WAV, OGG, FLAC, AAC, M4A, OPUS, and other supported audio formats
- Interactive keyboard controls while playing
- Volume adjustment
- Pause/Resume functionality
- Terminal file selector UI with navigation
- Recursive directory scanning for audio files

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
- **p** - Pause / Resume
- **s** - Stop
- **q** - Quit
- **+** - Increase volume
- **-** - Decrease volume
- **h** - Show help/controls

### File Selector Controls
- **↑/↓** - Navigate items
- **→/Enter** - Enter directory or select file
- **←/ESC** - Go up one directory
- **q** - Quit selector
