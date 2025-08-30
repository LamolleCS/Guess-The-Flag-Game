import pygame
from utils.constants import FONT_SIZE, SMALL_FONT_SIZE

# Centralized font management to avoid scattered Font(None, size) calls
# Lazy-loaded surfaces; if custom font path needed later, adjust here.

_default_path = None  # pygame default

class FontRegistry:
    def __init__(self):
        self._cache = {}

    def get(self, size: int) -> pygame.font.Font:
        key = (size, _default_path)
        font = self._cache.get(key)
        if font is None:
            font = pygame.font.Font(_default_path, size)
            self._cache[key] = font
        return font

registry = FontRegistry()

# Convenience getters

def main_font():
    return registry.get(FONT_SIZE)

def small_font():
    return registry.get(SMALL_FONT_SIZE)
