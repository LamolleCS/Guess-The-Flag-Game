"""Constantes globales del juego.

Define dimensiones de pantalla, colores, configuraciones de fuentes,
y otros valores inmutables utilizados en todo el proyecto.
"""
from typing import Final, Tuple, List

# =============================================================================
# PANTALLA Y RESOLUCIONES
# =============================================================================

# Resoluciones disponibles (ancho, alto)
RESOLUTIONS: Final[List[Tuple[int, int]]] = [
    (800, 600),     # 4:3
    (1024, 768),    # 4:3
    (1280, 720),    # 16:9 HD
    (1366, 768),    # 16:9
    (1600, 900),    # 16:9
    (1920, 1080),   # 16:9 Full HD
]

# Modos de ventana (identificadores internos; etiquetas UI via i18n window.mode.*)
WINDOW_MODES: Final[List[str]] = [
    "windowed",
    "fullscreen",
    "borderless",
]

# Dimensiones por defecto
SCREEN_WIDTH: Final[int] = 1280
SCREEN_HEIGHT: Final[int] = 720

# =============================================================================
# PALETA DE COLORES MODERNA
# =============================================================================

# Tipo para colores RGB/RGBA
ColorRGB = Tuple[int, int, int]
ColorRGBA = Tuple[int, int, int, int]

# Colores base
WHITE: Final[ColorRGB] = (255, 255, 255)
BLACK: Final[ColorRGB] = (0, 0, 0)
TRANSPARENT: Final[ColorRGBA] = (0, 0, 0, 0)

# Grises modernos
GRAY: Final[ColorRGB] = (128, 128, 128)
LIGHT_GRAY: Final[ColorRGB] = (240, 240, 245)
DARK_GRAY: Final[ColorRGB] = (45, 52, 64)
SLATE_GRAY: Final[ColorRGB] = (100, 116, 139)

# Colores primarios del tema
PRIMARY: Final[ColorRGB] = (99, 102, 241)       # Indigo vibrante
PRIMARY_LIGHT: Final[ColorRGB] = (129, 140, 248)
PRIMARY_DARK: Final[ColorRGB] = (67, 56, 202)

SECONDARY: Final[ColorRGB] = (236, 72, 153)     # Rosa/Magenta
SECONDARY_LIGHT: Final[ColorRGB] = (244, 114, 182)
SECONDARY_DARK: Final[ColorRGB] = (219, 39, 119)

# Colores de acento
ACCENT: Final[ColorRGB] = (14, 165, 233)        # Cyan brillante
ACCENT_LIGHT: Final[ColorRGB] = (56, 189, 248)
ACCENT_DARK: Final[ColorRGB] = (2, 132, 199)

# Colores de estado
SUCCESS: Final[ColorRGB] = (34, 197, 94)        # Verde esmeralda
SUCCESS_LIGHT: Final[ColorRGB] = (74, 222, 128)
SUCCESS_DARK: Final[ColorRGB] = (22, 163, 74)

ERROR: Final[ColorRGB] = (239, 68, 68)          # Rojo coral
ERROR_LIGHT: Final[ColorRGB] = (248, 113, 113)
ERROR_DARK: Final[ColorRGB] = (220, 38, 38)

WARNING: Final[ColorRGB] = (245, 158, 11)       # Ámbar
WARNING_LIGHT: Final[ColorRGB] = (251, 191, 36)

INFO: Final[ColorRGB] = (59, 130, 246)          # Azul info
INFO_LIGHT: Final[ColorRGB] = (96, 165, 250)

# Aliases para compatibilidad
RED: Final[ColorRGB] = ERROR
GREEN: Final[ColorRGB] = SUCCESS
BLUE: Final[ColorRGB] = INFO
YELLOW: Final[ColorRGB] = WARNING

# Colores de fondo - Modo Oscuro Premium
BG_GRADIENT_TOP: Final[ColorRGB] = (10, 10, 25)         # Azul muy oscuro
BG_GRADIENT_BOTTOM: Final[ColorRGB] = (20, 15, 40)      # Púrpura oscuro
BG_CARD: Final[ColorRGB] = (25, 25, 45)                 # Card oscuro
BG_CARD_HOVER: Final[ColorRGB] = (35, 35, 60)           # Hover en tarjetas

# Colores de texto (para fondo oscuro)
TEXT_PRIMARY: Final[ColorRGB] = (255, 255, 255)         # Blanco puro
TEXT_SECONDARY: Final[ColorRGB] = (180, 180, 200)       # Gris claro
TEXT_MUTED: Final[ColorRGB] = (120, 120, 150)           # Gris medio
TEXT_DARK: Final[ColorRGB] = (20, 20, 35)               # Para fondos claros

# Colores de botón (modo oscuro)
BTN_BG: Final[ColorRGB] = (40, 40, 70)              # Fondo oscuro
BTN_BG_HOVER: Final[ColorRGB] = (60, 60, 100)       # Hover
BTN_BORDER: Final[ColorRGB] = (80, 80, 140)         # Borde
BTN_TEXT: Final[ColorRGB] = TEXT_PRIMARY

# Colores RGB para efectos
RGB_COLORS: Final[List[ColorRGB]] = [
    (255, 0, 0),      # Rojo
    (255, 127, 0),    # Naranja
    (255, 255, 0),    # Amarillo
    (0, 255, 0),      # Verde
    (0, 255, 255),    # Cyan
    (0, 127, 255),    # Azul claro
    (127, 0, 255),    # Violeta
    (255, 0, 255),    # Magenta
]

# Colores de neón para efectos especiales
NEON_PINK: Final[ColorRGB] = (255, 20, 147)
NEON_BLUE: Final[ColorRGB] = (0, 191, 255)
NEON_GREEN: Final[ColorRGB] = (57, 255, 20)
NEON_PURPLE: Final[ColorRGB] = (138, 43, 226)
NEON_ORANGE: Final[ColorRGB] = (255, 165, 0)
NEON_CYAN: Final[ColorRGB] = (0, 255, 255)

# =============================================================================
# CONFIGURACIÓN DEL JUEGO
# =============================================================================

FPS: Final[int] = 60
MESSAGE_DURATION_SUCCESS: Final[int] = 48    # ~0.8s a 60 FPS
MESSAGE_DURATION_ERROR: Final[int] = 180     # 3s
MESSAGE_DURATION_INFO: Final[int] = 150      # 2.5s
MESSAGE_FADE_CUTOFF: Final[float] = 0.25     # Fade en el último 25%

# =============================================================================
# IDIOMAS SOPORTADOS
# =============================================================================

LANGUAGES: Final[List[str]] = [
    "Español (Uruguay)",
    "English",
    "Português",
    "Deutsch",
    "Italiano",
]

# Mapeo de etiquetas a códigos ISO
LANG_CODES: Final[dict] = {
    "Español (Uruguay)": "ES",
    "English": "EN",
    "Português": "PT",
    "Deutsch": "DE",
    "Italiano": "IT",
}

# =============================================================================
# DIMENSIONES DE UI
# =============================================================================

BUTTON_WIDTH: Final[int] = 200
BUTTON_HEIGHT: Final[int] = 50
BUTTON_SPACING: Final[int] = 20
BUTTON_BORDER_RADIUS: Final[int] = 8  # Para bordes redondeados

# =============================================================================
# TIPOGRAFÍA
# =============================================================================

FONT_SIZE: Final[int] = 32
SMALL_FONT_SIZE: Final[int] = 24
TITLE_FONT_SIZE: Final[int] = 64
MENU_TITLE_FONT_SIZE: Final[int] = 72  # Título grande para el menú principal

# =============================================================================
# INPUT
# =============================================================================

INPUT_PADDING: Final[int] = 10
KEY_REPEAT_DELAY: Final[int] = 320  # ms antes de repetir
KEY_REPEAT_INTERVAL: Final[int] = 25  # ms entre repeticiones
