import pygame

# Available screen resolutions
RESOLUTIONS = [
    (800, 600),    # 4:3
    (1024, 768),   # 4:3
    (1280, 720),   # 16:9
    (1366, 768),   # 16:9
    (1600, 900),   # 16:9
    (1920, 1080),  # 16:9 Full HD
]

# Screen modes (language‑independent identifiers; UI labels via i18n window.mode.*)
WINDOW_MODES = [
    "windowed",
    "fullscreen",
    "borderless"
]

# Default screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Game settings
FPS = 60

# Languages
LANGUAGES = [
    "Español (Uruguay)",
    "English",
    "Português",
    "Deutsch",
    "Italiano"
]

# Button dimensions
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_SPACING = 20

# Font settings
FONT_SIZE = 32
SMALL_FONT_SIZE = 24
