# Guess The Flag Game

A geography quiz game built with Python and Pygame featuring flag identification and capital city challenges. The game supports multiple languages and includes comprehensive scoring with retry rounds for missed countries.

## Features

- **Two Game Modes**
  - Flag identification: See a flag, type the country name
  - Capital cities: Two sub-modes for country ⟷ capital association
- **Region Selection**: Play globally or filter by continent (Africa, Asia, Europe, etc.)
- **Multilingual Support**: Spanish (Uruguay), English, Portuguese, German, and Italian
- **Smart Input Matching**: Accepts abbreviations, alternative names, and handles diacritics
- **Progress Persistence**: Resume incomplete games with automatic save states
- **Retry System**: Failed countries get a second round automatically
- **Audio System**: Background music with menu/game tracks and volume controls
- **Responsive Design**: Adapts to different screen resolutions

## Game Mechanics

### Scoring & Progress
- Real-time scoring with chronometer
- Failed countries are collected for retry rounds
- Progress is automatically saved and can be resumed
- Multiple continent-specific progress tracking

### Input System
- Auto-completion detection (no need to press Enter)
- Ctrl+A for select all
- Handles country name variations and abbreviations
- Supports special characters and accented letters

### Audio Controls
- Ctrl+Q: Quick mute/unmute toggle
- Automatic music switching between menu and gameplay
- Configurable volume settings

## Installation

### Requirements
- Python 3.7+
- Pygame 2.5.0+

### Setup
```bash
git clone https://github.com/LamolleCS/Guess-The-Flag-Game.git
cd Guess-The-Flag-Game
pip install -r requirements.txt
python main.py
```

## Project Structure

```
├── main.py                    # Entry point with Game class and audio management
├── screens/
│   ├── menu.py               # Main menu and settings navigation
│   ├── game.py               # Core game logic and UI rendering
│   └── settings.py           # Language and audio configuration
├── utils/
│   ├── constants.py          # Game constants and color definitions
│   ├── data.py               # Country data structures and continent mapping
│   ├── flag_manager.py       # Flag image loading and caching
│   ├── i18n.py               # Internationalization system
│   ├── text_utils.py         # String matching algorithms
│   ├── ui.py                 # Button and UI components
│   ├── fonts.py              # Font management
│   └── all_countries*.csv    # Country/capital data in multiple languages
└── assets/
    ├── flags/                # Country flag images (PNG format)
    └── music/                # Background music files (optional)
```

## Technical Implementation

### Flag Management
- Lazy loading with memory caching for flag images
- Dynamic scaling for different screen resolutions
- Efficient flag-to-country mapping system

### Data Handling
- CSV-based country database with language-specific variants
- Continent categorization with dynamic filtering
- Support for country name aliases and abbreviations

### Internationalization
- Template-based translation system (`tr()` function)
- Dynamic text rendering with proper encoding
- Language-specific country name handling

### Performance Features
- Surface caching for rendered text to reduce CPU usage
- Optimized country selection using swap-pop algorithm
- Clip-based input field rendering for long text

## Supported Languages

The game includes complete translations and country name databases for:
- **Español (Uruguay)** - Default language
- **English** - Full localization
- **Português** - Complete translation
- **Deutsch** - German language support  
- **Italiano** - Italian localization

## Contributing

Contributions are welcome. Areas of interest:
- Additional flag assets
- New language translations
- Performance optimizations
- UI/UX improvements

## Development

### Key Classes
- `Game`: Main application controller with audio management
- `GameScreen`: Core gameplay logic and UI rendering
- `FlagManager`: Flag image handling and caching
- `Country`: Data structure for country information

### Debug Features
- F3: Toggle debug overlay showing FPS and cache statistics
- Built-in progress tracking with persistent state management

---

Built with Python 3.x and Pygame. Supports Windows, macOS, and Linux.
