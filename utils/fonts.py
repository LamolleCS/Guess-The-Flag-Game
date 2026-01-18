"""Gestión centralizada de fuentes.

Provee un registro de fuentes cacheadas para evitar múltiples
instancias de Font con el mismo tamaño.
"""
import pygame
from typing import Dict, Optional, Tuple
from utils.constants import FONT_SIZE, SMALL_FONT_SIZE, TITLE_FONT_SIZE

# Ruta de fuente por defecto (None = fuente del sistema pygame)
_DEFAULT_FONT_PATH: Optional[str] = None


class FontRegistry:
    """Registro singleton de fuentes cacheadas.
    
    Evita crear múltiples instancias de la misma fuente,
    mejorando el rendimiento y uso de memoria.
    """
    
    def __init__(self) -> None:
        self._cache: Dict[Tuple[int, Optional[str]], pygame.font.Font] = {}
    
    def get(self, size: int, path: Optional[str] = None) -> pygame.font.Font:
        """Obtiene una fuente del cache o la crea si no existe.
        
        Args:
            size: Tamaño de la fuente en píxeles.
            path: Ruta al archivo de fuente (None para default).
            
        Returns:
            Instancia de pygame.font.Font.
        """
        if path is None:
            path = _DEFAULT_FONT_PATH
            
        key = (size, path)
        font = self._cache.get(key)
        
        if font is None:
            font = pygame.font.Font(path, size)
            self._cache[key] = font
            
        return font
    
    def clear(self) -> None:
        """Limpia el cache de fuentes."""
        self._cache.clear()
    
    def preload(self, sizes: list) -> None:
        """Precarga fuentes para los tamaños especificados.
        
        Args:
            sizes: Lista de tamaños a precargar.
        """
        for size in sizes:
            self.get(size)


# Instancia global del registro
registry = FontRegistry()


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

def main_font() -> pygame.font.Font:
    """Obtiene la fuente principal del juego."""
    return registry.get(FONT_SIZE)


def small_font() -> pygame.font.Font:
    """Obtiene la fuente pequeña para textos secundarios."""
    return registry.get(SMALL_FONT_SIZE)


def title_font() -> pygame.font.Font:
    """Obtiene la fuente para títulos."""
    return registry.get(TITLE_FONT_SIZE)


def custom_font(size: int) -> pygame.font.Font:
    """Obtiene una fuente de tamaño personalizado.
    
    Args:
        size: Tamaño de la fuente.
        
    Returns:
        Fuente del tamaño especificado.
    """
    return registry.get(size)
