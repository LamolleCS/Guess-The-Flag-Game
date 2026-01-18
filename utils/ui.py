"""Componentes de interfaz de usuario modernos.

Contiene widgets reutilizables con diseño moderno:
botones con gradientes, sombras y animaciones suaves.
Efectos RGB, neón y partículas.
"""
import pygame
import math
import random
import time as time_module
from typing import List, Optional, Tuple

from utils.constants import (
    FONT_SIZE, SMALL_FONT_SIZE, BUTTON_HEIGHT, BUTTON_BORDER_RADIUS,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WHITE, BLACK, 
    PRIMARY, PRIMARY_LIGHT, PRIMARY_DARK,
    SECONDARY, SECONDARY_LIGHT,
    SUCCESS, SUCCESS_LIGHT, ERROR, ERROR_LIGHT,
    BG_GRADIENT_TOP, BG_GRADIENT_BOTTOM, BG_CARD, BG_CARD_HOVER,
    BTN_BG, BTN_BG_HOVER, BTN_BORDER, BTN_TEXT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DARK,
    ACCENT, ACCENT_LIGHT,
    NEON_PINK, NEON_BLUE, NEON_GREEN, NEON_PURPLE, NEON_CYAN
)
from utils import fonts
from utils import sounds


# =============================================================================
# VARIABLES GLOBALES DE TIEMPO PARA ANIMACIONES
# =============================================================================
_global_time: float = 0.0
_stars_cache: Optional[List[dict]] = None
_stars_cache_size: Tuple[int, int] = (0, 0)


def update_global_time(dt: float = 1/60) -> None:
    """Actualiza el tiempo global para animaciones."""
    global _global_time
    _global_time += dt


def get_global_time() -> float:
    """Obtiene el tiempo global actual."""
    return _global_time


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    """Convierte HSV a RGB."""
    if s == 0.0:
        return (int(v * 255), int(v * 255), int(v * 255))
    
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    
    if i == 0: r, g, b = v, t, p
    elif i == 1: r, g, b = q, v, p
    elif i == 2: r, g, b = p, v, t
    elif i == 3: r, g, b = p, q, v
    elif i == 4: r, g, b = t, p, v
    else: r, g, b = v, p, q
    
    return (int(r * 255), int(g * 255), int(b * 255))


def get_rainbow_color(offset: float = 0.0, speed: float = 0.5) -> Tuple[int, int, int]:
    """Obtiene un color arcoíris animado."""
    hue = (_global_time * speed + offset) % 1.0
    return hsv_to_rgb(hue, 0.9, 1.0)


# =============================================================================
# UTILIDADES DE DIBUJO
# =============================================================================

def draw_rounded_rect(
    surface: pygame.Surface,
    color: Tuple[int, int, int],
    rect: pygame.Rect,
    radius: int,
    width: int = 0
) -> None:
    """Dibuja un rectángulo con bordes redondeados."""
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)


def draw_gradient_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color_top: Tuple[int, int, int],
    color_bottom: Tuple[int, int, int],
    radius: int = 0
) -> None:
    """Dibuja un rectángulo con gradiente vertical.
    
    Args:
        surface: Superficie donde dibujar.
        rect: Rectángulo a dibujar.
        color_top: Color superior.
        color_bottom: Color inferior.
        radius: Radio de las esquinas.
    """
    # Crear superficie temporal para el gradiente
    gradient_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    
    for y in range(rect.height):
        ratio = y / max(1, rect.height - 1)
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
        pygame.draw.line(gradient_surf, (r, g, b), (0, y), (rect.width, y))
    
    # Aplicar máscara redondeada si es necesario
    if radius > 0:
        mask_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(mask_surf, (255, 255, 255), 
                        pygame.Rect(0, 0, rect.width, rect.height), 
                        border_radius=radius)
        gradient_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    
    surface.blit(gradient_surf, rect.topleft)


def draw_shadow(
    surface: pygame.Surface,
    rect: pygame.Rect,
    radius: int = 8,
    offset: int = 4,
    alpha: int = 40
) -> None:
    """Dibuja una sombra suave debajo de un rectángulo.
    
    Args:
        surface: Superficie donde dibujar.
        rect: Rectángulo base.
        radius: Radio de las esquinas.
        offset: Desplazamiento de la sombra.
        alpha: Transparencia de la sombra.
    """
    shadow_surf = pygame.Surface((rect.width + offset*2, rect.height + offset*2), pygame.SRCALPHA)
    shadow_rect = pygame.Rect(offset, offset, rect.width, rect.height)
    pygame.draw.rect(shadow_surf, (0, 0, 0, alpha), shadow_rect, border_radius=radius)
    surface.blit(shadow_surf, (rect.x - offset//2, rect.y + offset//2))


def draw_background_gradient(surface: pygame.Surface) -> None:
    """Dibuja un fondo con gradiente moderno."""
    width = surface.get_width()
    height = surface.get_height()
    
    for y in range(height):
        ratio = y / max(1, height - 1)
        r = int(BG_GRADIENT_TOP[0] + (BG_GRADIENT_BOTTOM[0] - BG_GRADIENT_TOP[0]) * ratio)
        g = int(BG_GRADIENT_TOP[1] + (BG_GRADIENT_BOTTOM[1] - BG_GRADIENT_TOP[1]) * ratio)
        b = int(BG_GRADIENT_TOP[2] + (BG_GRADIENT_BOTTOM[2] - BG_GRADIENT_TOP[2]) * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))


def _create_stars(width: int, height: int, num_stars: int = 150) -> List[dict]:
    """Crea un campo de estrellas."""
    import random
    stars = []
    for _ in range(num_stars):
        stars.append({
            'x': random.randint(0, width),
            'y': random.randint(0, height),
            'size': random.uniform(0.5, 2.5),
            'brightness': random.uniform(0.3, 1.0),
            'twinkle_speed': random.uniform(1, 4),
            'twinkle_offset': random.uniform(0, math.pi * 2),
            'color_offset': random.uniform(0, 1),
        })
    return stars


# Partículas flotantes globales
_floating_particles: Optional[List[dict]] = None

def _create_floating_particles(width: int, height: int, count: int = 30) -> List[dict]:
    """Crea partículas flotantes para el fondo."""
    import random
    particles = []
    for _ in range(count):
        particles.append({
            'x': random.uniform(0, width),
            'y': random.uniform(0, height),
            'vx': random.uniform(-0.3, 0.3),
            'vy': random.uniform(-0.5, -0.1),
            'size': random.uniform(3, 8),
            'hue_offset': random.uniform(0, 1),
            'alpha_offset': random.uniform(0, math.pi * 2),
            'width': width,
            'height': height,
        })
    return particles


def _update_floating_particles(particles: List[dict]) -> None:
    """Actualiza las posiciones de las partículas flotantes."""
    for p in particles:
        p['x'] += p['vx']
        p['y'] += p['vy']
        
        # Wrap around
        if p['y'] < -p['size']:
            p['y'] = p['height'] + p['size']
            p['x'] = random.uniform(0, p['width'])
        if p['x'] < -p['size']:
            p['x'] = p['width'] + p['size']
        elif p['x'] > p['width'] + p['size']:
            p['x'] = -p['size']


def draw_floating_particles(surface: pygame.Surface, particles: List[dict]) -> None:
    """Dibuja partículas flotantes con efecto RGB."""
    t = _global_time
    for p in particles:
        # Color RGB animado
        hue = (t * 0.2 + p['hue_offset']) % 1.0
        color = hsv_to_rgb(hue, 0.7, 1.0)
        
        # Alpha pulsante
        alpha = int(40 + 30 * math.sin(t * 2 + p['alpha_offset']))
        
        size = int(p['size'])
        if size > 0:
            # Dibujar partícula con glow
            particle_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            
            # Glow exterior
            for i in range(size * 2, 0, -2):
                glow_alpha = int(alpha * (i / (size * 2)) * 0.5)
                pygame.draw.circle(particle_surf, (*color, glow_alpha), (size * 2, size * 2), i)
            
            # Centro brillante
            pygame.draw.circle(particle_surf, (*color, min(255, alpha * 2)), (size * 2, size * 2), size // 2)
            
            surface.blit(particle_surf, (int(p['x']) - size * 2, int(p['y']) - size * 2))


def draw_stars(surface: pygame.Surface, stars: List[dict]) -> None:
    """Dibuja estrellas con efecto de centelleo y colores."""
    t = _global_time
    for star in stars:
        # Efecto de centelleo
        twinkle = (math.sin(t * star['twinkle_speed'] + star['twinkle_offset']) + 1) / 2
        brightness = star['brightness'] * (0.5 + twinkle * 0.5)
        
        # Color con tinte arcoíris sutil
        base_color = int(180 * brightness)
        hue_shift = (t * 0.1 + star['color_offset']) % 1.0
        r = int(base_color + 40 * math.sin(hue_shift * math.pi * 2))
        g = int(base_color + 40 * math.sin((hue_shift + 0.33) * math.pi * 2))
        b = int(base_color + 75 * brightness)  # Más azul
        
        color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        size = max(1, int(star['size'] * (0.8 + twinkle * 0.4)))
        
        if size <= 1:
            surface.set_at((int(star['x']), int(star['y'])), color)
        else:
            # Estrella con glow pequeño
            pygame.draw.circle(surface, color, (int(star['x']), int(star['y'])), size)
            if brightness > 0.7 and size > 1:
                glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*color, int(50 * twinkle)), (size * 2, size * 2), size * 2)
                surface.blit(glow_surf, (int(star['x']) - size * 2, int(star['y']) - size * 2))


# Cache del fondo para no recalcularlo cada frame
_bg_cache: Optional[pygame.Surface] = None
_bg_cache_size: Tuple[int, int] = (0, 0)

def get_cached_background(width: int, height: int) -> pygame.Surface:
    """Obtiene el fondo cacheado o lo genera si es necesario."""
    global _bg_cache, _bg_cache_size, _stars_cache, _stars_cache_size
    
    if _bg_cache is None or _bg_cache_size != (width, height):
        _bg_cache = pygame.Surface((width, height))
        draw_background_gradient(_bg_cache)
        _bg_cache_size = (width, height)
        # Regenerar estrellas también
        _stars_cache = _create_stars(width, height)
        _stars_cache_size = (width, height)
    
    return _bg_cache


def draw_animated_background(surface: pygame.Surface) -> None:
    """Dibuja el fondo con estrellas y partículas animadas."""
    global _stars_cache, _stars_cache_size, _floating_particles
    
    width = surface.get_width()
    height = surface.get_height()
    
    # Dibujar fondo base
    bg = get_cached_background(width, height)
    surface.blit(bg, (0, 0))
    
    # Asegurar que las estrellas existan
    if _stars_cache is None or _stars_cache_size != (width, height):
        _stars_cache = _create_stars(width, height)
        _stars_cache_size = (width, height)
    
    # Asegurar que las partículas flotantes existan
    if _floating_particles is None or len(_floating_particles) == 0:
        _floating_particles = _create_floating_particles(width, height)
    
    # Dibujar estrellas animadas
    draw_stars(surface, _stars_cache)
    
    # Actualizar y dibujar partículas flotantes
    _update_floating_particles(_floating_particles)
    draw_floating_particles(surface, _floating_particles)


def draw_neon_glow(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: Tuple[int, int, int],
    intensity: float = 1.0,
    glow_size: int = 20
) -> None:
    """Dibuja un efecto de glow neón alrededor de un rectángulo."""
    glow_surf = pygame.Surface(
        (rect.width + glow_size * 2, rect.height + glow_size * 2), 
        pygame.SRCALPHA
    )
    
    for i in range(glow_size, 0, -2):
        alpha = int((i / glow_size) * 50 * intensity)
        inflated = pygame.Rect(
            glow_size - i, glow_size - i,
            rect.width + i * 2, rect.height + i * 2
        )
        pygame.draw.rect(glow_surf, (*color, alpha), inflated, border_radius=8 + i // 2)
    
    surface.blit(glow_surf, (rect.x - glow_size, rect.y - glow_size))


def draw_rgb_border(
    surface: pygame.Surface,
    rect: pygame.Rect,
    thickness: int = 2,
    speed: float = 0.5
) -> None:
    """Dibuja un borde con efecto RGB animado."""
    t = _global_time * speed
    
    # Borde superior
    for x in range(rect.width):
        hue = (t + x / rect.width) % 1.0
        color = hsv_to_rgb(hue, 1.0, 1.0)
        for dy in range(thickness):
            if 0 <= rect.x + x < surface.get_width() and 0 <= rect.y + dy < surface.get_height():
                surface.set_at((rect.x + x, rect.y + dy), color)
    
    # Borde inferior
    for x in range(rect.width):
        hue = (t + 0.5 + x / rect.width) % 1.0
        color = hsv_to_rgb(hue, 1.0, 1.0)
        for dy in range(thickness):
            px, py = rect.x + x, rect.bottom - 1 - dy
            if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
                surface.set_at((px, py), color)
    
    # Borde izquierdo
    for y in range(rect.height):
        hue = (t + 0.75 + y / rect.height) % 1.0
        color = hsv_to_rgb(hue, 1.0, 1.0)
        for dx in range(thickness):
            px, py = rect.x + dx, rect.y + y
            if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
                surface.set_at((px, py), color)
    
    # Borde derecho
    for y in range(rect.height):
        hue = (t + 0.25 + y / rect.height) % 1.0
        color = hsv_to_rgb(hue, 1.0, 1.0)
        for dx in range(thickness):
            px, py = rect.right - 1 - dx, rect.y + y
            if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
                surface.set_at((px, py), color)


# =============================================================================
# COMPONENTE BOTÓN MODERNO CON EFECTOS RGB
# =============================================================================

class Button:
    """Botón moderno con efectos visuales espectaculares.
    
    Características:
    - Efectos RGB animados
    - Glow neón
    - Sombras dinámicas
    - Animaciones fluidas
    - Efectos de partículas en hover
    """
    
    # Estilos predefinidos
    STYLE_PRIMARY = 'primary'
    STYLE_SECONDARY = 'secondary'
    STYLE_SUCCESS = 'success'
    STYLE_DANGER = 'danger'
    STYLE_GHOST = 'ghost'
    STYLE_RGB = 'rgb'  # Nuevo estilo con efecto arcoíris

    def __init__(
        self, 
        x: int, 
        y: int, 
        width: int, 
        height: int, 
        text: str, 
        font_size: int = FONT_SIZE,
        style: str = STYLE_PRIMARY
    ) -> None:
        """Inicializa el botón moderno."""
        self.rect = pygame.Rect(x, y, width, height)
        self._text = text
        self.font = fonts.registry.get(font_size)
        self.is_hovered = False
        self.is_visible = True
        self.style = style
        
        # Animación hover
        self._hover_progress = 0.0  # 0 a 1
        self._hover_speed = 0.12
        
        # Tiempo de creación para animaciones
        self._creation_time = _global_time
        self._pulse_offset = hash(text) % 100 / 100.0  # Offset único por botón
        
        # Colores según estilo
        self._setup_colors()
        
        # Cache de texto
        self._text_surface: Optional[pygame.Surface] = None
        self._text_surface_hover: Optional[pygame.Surface] = None
        self._update_text_surface()
    
    def _setup_colors(self) -> None:
        """Configura los colores según el estilo."""
        styles = {
            self.STYLE_PRIMARY: {
                'bg': (30, 30, 80),
                'bg_hover': (50, 50, 120),
                'border': PRIMARY_LIGHT,
                'text': WHITE,
                'glow': NEON_BLUE,
                'glow_hover': NEON_CYAN,
            },
            self.STYLE_SECONDARY: {
                'bg': (60, 20, 60),
                'bg_hover': (90, 30, 90),
                'border': SECONDARY_LIGHT,
                'text': WHITE,
                'glow': NEON_PINK,
                'glow_hover': NEON_PURPLE,
            },
            self.STYLE_SUCCESS: {
                'bg': (20, 60, 30),
                'bg_hover': (30, 90, 45),
                'border': SUCCESS_LIGHT,
                'text': WHITE,
                'glow': NEON_GREEN,
                'glow_hover': (100, 255, 100),
            },
            self.STYLE_DANGER: {
                'bg': (80, 20, 20),
                'bg_hover': (120, 30, 30),
                'border': ERROR_LIGHT,
                'text': WHITE,
                'glow': (255, 80, 80),
                'glow_hover': (255, 120, 120),
            },
            self.STYLE_GHOST: {
                'bg': (20, 20, 40),
                'bg_hover': (40, 40, 80),
                'border': (80, 80, 140),
                'text': TEXT_PRIMARY,
                'glow': ACCENT_LIGHT,
                'glow_hover': NEON_CYAN,
            },
            self.STYLE_RGB: {
                'bg': (20, 20, 30),
                'bg_hover': (30, 30, 50),
                'border': WHITE,
                'text': WHITE,
                'glow': WHITE,  # Se sobrescribe con RGB
                'glow_hover': WHITE,
            },
        }
        
        colors = styles.get(self.style, styles[self.STYLE_PRIMARY])
        self.color_bg = colors['bg']
        self.color_bg_hover = colors['bg_hover']
        self.color_border = colors['border']
        self.color_text = colors['text']
        self.color_glow = colors['glow']
        self.color_glow_hover = colors['glow_hover']
    
    @property
    def text(self) -> str:
        return self._text
    
    @text.setter
    def text(self, value: str) -> None:
        if value != self._text:
            self._text = value
            self._update_text_surface()
    
    def _update_text_surface(self) -> None:
        """Regenera las superficies de texto."""
        self._text_surface = self.font.render(self._text, True, self.color_text)
        self._text_surface_hover = self.font.render(self._text, True, WHITE)

    def set_text(self, new_text: str) -> None:
        self.text = new_text

    def update(self) -> None:
        """Actualiza la animación del botón."""
        target = 1.0 if self.is_hovered else 0.0
        if self._hover_progress < target:
            self._hover_progress = min(self._hover_progress + self._hover_speed, target)
        elif self._hover_progress > target:
            self._hover_progress = max(self._hover_progress - self._hover_speed, target)

    def draw(self, screen: pygame.Surface) -> None:
        """Dibuja el botón con efectos espectaculares."""
        if not self.is_visible:
            return
        
        self.update()
        
        radius = BUTTON_BORDER_RADIUS + 2
        p = self._hover_progress
        t = _global_time
        
        # Pulso suave constante
        pulse = 0.85 + math.sin(t * 2 + self._pulse_offset * math.pi * 2) * 0.15
        
        # Color de glow (RGB animado si es el estilo RGB, o interpolado normalmente)
        if self.style == self.STYLE_RGB:
            glow_color = get_rainbow_color(self._pulse_offset, 0.3)
        else:
            glow_color = self._lerp_color(self.color_glow, self.color_glow_hover, p)
        
        # === GLOW EXTERIOR (ajustado para coincidir con el botón) ===
        # Glow más sutil y proporcional al tamaño del botón
        glow_intensity = (0.3 + p * 0.5) * pulse
        glow_size = int(6 + p * 6)  # Glow más pequeño y proporcional
        
        glow_surf = pygame.Surface(
            (self.rect.width + glow_size * 2, self.rect.height + glow_size * 2), 
            pygame.SRCALPHA
        )
        
        # Dibujar glow con el mismo radio del botón para que coincida
        for i in range(glow_size, 0, -1):
            alpha = int((i / glow_size) * 45 * glow_intensity)
            inflated = pygame.Rect(
                glow_size - i, glow_size - i,
                self.rect.width + i * 2, self.rect.height + i * 2
            )
            pygame.draw.rect(glow_surf, (*glow_color, alpha), inflated, border_radius=radius + i // 3)
        
        screen.blit(glow_surf, (self.rect.x - glow_size, self.rect.y - glow_size))
        
        # === SOMBRA (más sutil) ===
        shadow_offset = int(3 + p * 2)
        shadow_alpha = int(40 + p * 20)
        shadow_surf = pygame.Surface(
            (self.rect.width + shadow_offset * 2, self.rect.height + shadow_offset * 2), 
            pygame.SRCALPHA
        )
        shadow_rect = pygame.Rect(shadow_offset, shadow_offset + 2, self.rect.width, self.rect.height)
        pygame.draw.rect(shadow_surf, (0, 0, 0, shadow_alpha), shadow_rect, border_radius=radius)
        screen.blit(shadow_surf, (self.rect.x - shadow_offset // 2, self.rect.y))
        
        # === FONDO DEL BOTÓN ===
        bg_color = self._lerp_color(self.color_bg, self.color_bg_hover, p)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=radius)
        
        # === BORDE ANIMADO ===
        if self.style == self.STYLE_RGB or p > 0.5:
            # Borde RGB para botones RGB o cuando está muy hovereado
            self._draw_rgb_border(screen, self.rect, radius, 2 + int(p))
        else:
            # Borde normal con glow
            border_color = self._lerp_color(self.color_border, glow_color, p * 0.7)
            pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=radius)
        
        # === EFECTO DE BRILLO SUPERIOR ===
        highlight_rect = pygame.Rect(
            self.rect.x + 3, 
            self.rect.y + 3, 
            self.rect.width - 6, 
            self.rect.height // 3
        )
        highlight_alpha = int((30 + p * 25) * pulse)
        highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        
        # Gradiente de highlight
        for y in range(highlight_rect.height):
            alpha = int(highlight_alpha * (1 - y / highlight_rect.height))
            pygame.draw.line(highlight_surf, (255, 255, 255, alpha), (0, y), (highlight_rect.width, y))
        
        # Aplicar máscara redondeada
        mask = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255), mask.get_rect(), border_radius=radius - 2)
        highlight_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(highlight_surf, highlight_rect.topleft)
        
        # === TEXTO ===
        text_surf = self._text_surface
        if text_surf:
            text_rect = text_surf.get_rect(center=self.rect.center)
            # Efecto de elevación en hover
            text_rect.y -= int(p * 2)
            
            # Glow del texto si está hovereado
            if p > 0.3:
                text_glow = self.font.render(self._text, True, glow_color)
                text_glow.set_alpha(int(100 * p))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    screen.blit(text_glow, (text_rect.x + dx, text_rect.y + dy))
            
            screen.blit(text_surf, text_rect)
    
    def _draw_rgb_border(
        self, 
        surface: pygame.Surface, 
        rect: pygame.Rect, 
        radius: int,
        thickness: int
    ) -> None:
        """Dibuja un borde con efecto RGB fluido."""
        t = _global_time * 0.8
        
        # Crear superficie para el borde
        border_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Dibujar borde con colores que fluyen
        perimeter = 2 * (rect.width + rect.height)
        segments = 60
        
        for i in range(segments):
            progress = i / segments
            hue = (t + progress + self._pulse_offset) % 1.0
            color = hsv_to_rgb(hue, 1.0, 1.0)
            
            # Calcular posición en el borde
            pos = progress * perimeter
            
            if pos < rect.width:
                x, y = pos, 0
            elif pos < rect.width + rect.height:
                x, y = rect.width - 1, pos - rect.width
            elif pos < 2 * rect.width + rect.height:
                x, y = rect.width - 1 - (pos - rect.width - rect.height), rect.height - 1
            else:
                x, y = 0, rect.height - 1 - (pos - 2 * rect.width - rect.height)
            
            # Dibujar punto con glow
            pygame.draw.circle(border_surf, (*color, 255), (int(x), int(y)), thickness + 1)
        
        surface.blit(border_surf, rect.topleft)
        
        # Borde base más tenue
        pygame.draw.rect(surface, (50, 50, 80), rect, 1, border_radius=radius)
    
    def _lerp_color(
        self, 
        color1: Tuple[int, int, int], 
        color2: Tuple[int, int, int], 
        t: float
    ) -> Tuple[int, int, int]:
        """Interpola entre dos colores."""
        return (
            int(color1[0] + (color2[0] - color1[0]) * t),
            int(color1[1] + (color2[1] - color1[1]) * t),
            int(color1[2] + (color2[2] - color1[2]) * t),
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Procesa eventos y retorna True si fue click."""
        if not self.is_visible:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            was_hovered = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)
            # Reproducir sonido de hover al entrar
            if self.is_hovered and not was_hovered:
                sounds.play_hover()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                sounds.play_click()
                return True
        return False


# =============================================================================
# DIÁLOGO DE CONFIRMACIÓN MODERNO
# =============================================================================

class ConfirmationDialog:
    """Diálogo modal moderno con blur de fondo."""

    def __init__(self, screen: pygame.Surface, message: str) -> None:
        self.screen = screen
        self.message = message
        
        # Tamaño responsive
        sw, sh = screen.get_width(), screen.get_height()
        dialog_width = min(450, int(sw * 0.55))
        dialog_height = min(220, int(sh * 0.35))
        x = (sw - dialog_width) // 2
        y = (sh - dialog_height) // 2
        self.rect = pygame.Rect(x, y, dialog_width, dialog_height)
        
        # Botones
        btn_width = int(dialog_width * 0.28)
        btn_height = 45
        btn_y = y + dialog_height - btn_height - 25
        
        self.yes_button = Button(
            x + 40, btn_y, btn_width, btn_height, 
            "Sí", SMALL_FONT_SIZE, Button.STYLE_SUCCESS
        )
        self.no_button = Button(
            x + dialog_width - btn_width - 40, btn_y, btn_width, btn_height,
            "No", SMALL_FONT_SIZE, Button.STYLE_DANGER
        )
        
        self.font = fonts.main_font()
        
        # Animación de entrada
        self._animation_progress = 0.0

    def draw(self) -> None:
        """Dibuja el diálogo con efectos modernos."""
        sw, sh = self.screen.get_width(), self.screen.get_height()
        
        # Actualizar animación
        if self._animation_progress < 1.0:
            self._animation_progress = min(1.0, self._animation_progress + 0.1)
        
        p = self._animation_progress
        
        # Overlay oscuro con fade
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(180 * p)))
        self.screen.blit(overlay, (0, 0))
        
        # Calcular posición con animación de escala
        scale = 0.8 + 0.2 * p
        animated_width = int(self.rect.width * scale)
        animated_height = int(self.rect.height * scale)
        animated_x = self.rect.centerx - animated_width // 2
        animated_y = self.rect.centery - animated_height // 2
        animated_rect = pygame.Rect(animated_x, animated_y, animated_width, animated_height)
        
        # Sombra del diálogo
        draw_shadow(self.screen, animated_rect, 16, 10, int(60 * p))
        
        # Fondo del diálogo con gradiente
        dialog_surf = pygame.Surface((animated_width, animated_height), pygame.SRCALPHA)
        draw_gradient_rect(
            dialog_surf,
            pygame.Rect(0, 0, animated_width, animated_height),
            (45, 55, 72),  # Slate-700
            (30, 41, 59),  # Slate-800
            16
        )
        
        # Borde sutil
        pygame.draw.rect(dialog_surf, (71, 85, 105), 
                        pygame.Rect(0, 0, animated_width, animated_height),
                        2, border_radius=16)
        
        self.screen.blit(dialog_surf, animated_rect.topleft)
        
        # Mensaje
        text_surface = self.font.render(self.message, True, TEXT_PRIMARY)
        text_rect = text_surface.get_rect(center=(animated_rect.centerx, animated_rect.y + 70))
        self.screen.blit(text_surface, text_rect)
        
        # Actualizar posiciones de botones según animación
        btn_y = animated_rect.y + animated_height - 45 - 25
        self.yes_button.rect.y = btn_y
        self.yes_button.rect.x = animated_rect.x + 40
        self.no_button.rect.y = btn_y
        self.no_button.rect.x = animated_rect.x + animated_width - self.no_button.rect.width - 40
        
        # Dibujar botones
        self.yes_button.draw(self.screen)
        self.no_button.draw(self.screen)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if self.yes_button.handle_event(event):
            return "yes"
        if self.no_button.handle_event(event):
            return "no"
        return None


# =============================================================================
# MENÚ DESPLEGABLE MODERNO
# =============================================================================

class DropdownMenu:
    """Menú desplegable con diseño moderno."""

    def __init__(
        self, 
        x: int, 
        y: int, 
        width: int, 
        height: int, 
        options: List[str], 
        font_size: int = SMALL_FONT_SIZE
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.font = fonts.registry.get(font_size)
        self.is_open = False
        self.selected_option = options[0]
        self.option_rects: List[pygame.Rect] = []
        self.hovered_index = -1
        self.update_option_rects()

    def update_option_rects(self) -> None:
        self.option_rects = []
        if self.is_open:
            for i in range(len(self.options)):
                self.option_rects.append(
                    pygame.Rect(
                        self.rect.x,
                        self.rect.y + (i + 1) * self.rect.height,
                        self.rect.width,
                        self.rect.height
                    )
                )

    def draw(self, screen: pygame.Surface) -> None:
        """Dibuja el menú desplegable con estilo moderno."""
        radius = BUTTON_BORDER_RADIUS
        
        # Botón principal
        draw_shadow(screen, self.rect, radius, 3, 25)
        pygame.draw.rect(screen, BTN_BG, self.rect, border_radius=radius)
        pygame.draw.rect(screen, BTN_BORDER, self.rect, 2, border_radius=radius)
        
        # Texto seleccionado
        text_surface = self.font.render(self.selected_option, True, TEXT_PRIMARY)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
        # Indicador de dropdown (flecha)
        arrow_x = self.rect.right - 25
        arrow_y = self.rect.centery
        arrow_size = 6
        if self.is_open:
            # Flecha arriba
            points = [
                (arrow_x, arrow_y + arrow_size//2),
                (arrow_x - arrow_size, arrow_y + arrow_size//2 + arrow_size),
                (arrow_x + arrow_size, arrow_y + arrow_size//2 + arrow_size)
            ]
        else:
            # Flecha abajo
            points = [
                (arrow_x, arrow_y + arrow_size//2 + arrow_size),
                (arrow_x - arrow_size, arrow_y + arrow_size//2),
                (arrow_x + arrow_size, arrow_y + arrow_size//2)
            ]
        pygame.draw.polygon(screen, TEXT_SECONDARY, points)

        # Opciones desplegadas
        if self.is_open:
            # Contenedor de opciones
            options_height = len(self.options) * self.rect.height
            options_rect = pygame.Rect(
                self.rect.x, 
                self.rect.y + self.rect.height + 4,
                self.rect.width, 
                options_height
            )
            
            draw_shadow(screen, options_rect, radius, 4, 40)
            pygame.draw.rect(screen, BG_CARD, options_rect, border_radius=radius)
            pygame.draw.rect(screen, BTN_BORDER, options_rect, 1, border_radius=radius)
            
            for i, (option, option_rect) in enumerate(zip(self.options, self.option_rects)):
                # Ajustar rect
                actual_rect = pygame.Rect(
                    self.rect.x, 
                    self.rect.y + self.rect.height + 4 + i * self.rect.height,
                    self.rect.width, 
                    self.rect.height
                )
                
                # Hover
                is_hovered = actual_rect.collidepoint(pygame.mouse.get_pos())
                if is_hovered:
                    pygame.draw.rect(screen, BG_CARD_HOVER, actual_rect, border_radius=radius if i == 0 or i == len(self.options)-1 else 0)
                
                # Texto
                text_surface = self.font.render(option, True, TEXT_PRIMARY if is_hovered else TEXT_SECONDARY)
                text_rect = text_surface.get_rect(center=actual_rect.center)
                screen.blit(text_surface, text_rect)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.MOUSEBUTTONDOWN:
            button = getattr(event, 'button', 1)
            if button in (4, 5):
                return None
            if button not in (1, 2, 3):
                return None
                
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                self.update_option_rects()
                return None
            
            if self.is_open:
                for i in range(len(self.options)):
                    actual_rect = pygame.Rect(
                        self.rect.x, 
                        self.rect.y + self.rect.height + 4 + i * self.rect.height,
                        self.rect.width, 
                        self.rect.height
                    )
                    if actual_rect.collidepoint(event.pos):
                        self.selected_option = self.options[i]
                        self.is_open = False
                        self.update_option_rects()
                        return self.selected_option
                
                # Click fuera - cerrar
                self.is_open = False
                self.update_option_rects()
        
        return None


# =============================================================================
# CAMPO DE ENTRADA MODERNO
# =============================================================================

class InputField:
    """Campo de entrada de texto con diseño moderno."""
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        placeholder: str = "",
        font_size: int = FONT_SIZE
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.placeholder = placeholder
        self.font = fonts.registry.get(font_size)
        self.is_active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.scroll_offset = 0
        self.selection_all = False
    
    def draw(self, screen: pygame.Surface) -> None:
        """Dibuja el campo de entrada con estilo moderno."""
        radius = BUTTON_BORDER_RADIUS
        
        # Sombra interna
        inner_shadow = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(inner_shadow, (0, 0, 0, 30), 
                        pygame.Rect(0, 0, self.rect.width, self.rect.height),
                        border_radius=radius)
        
        # Fondo
        bg_color = BG_CARD if self.is_active else (40, 50, 65)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=radius)
        
        # Borde (más brillante si activo)
        border_color = ACCENT if self.is_active else BTN_BORDER
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=radius)
        
        # Glow cuando activo
        if self.is_active:
            glow_rect = self.rect.inflate(6, 6)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*ACCENT, 30), glow_surf.get_rect(), border_radius=radius + 3)
            screen.blit(glow_surf, glow_rect.topleft)
        
        # Área de texto con clip
        clip_rect = self.rect.inflate(-16, -8)
        original_clip = screen.get_clip()
        screen.set_clip(clip_rect)
        
        # Selección completa
        if self.selection_all and self.text:
            text_surf = self.font.render(self.text, True, TEXT_PRIMARY)
            sel_rect = pygame.Rect(
                clip_rect.x - self.scroll_offset,
                clip_rect.y,
                text_surf.get_width(),
                clip_rect.height
            )
            pygame.draw.rect(screen, (*PRIMARY, 100), sel_rect)
        
        # Texto o placeholder
        if self.text:
            text_surf = self.font.render(self.text, True, TEXT_PRIMARY)
        else:
            text_surf = self.font.render(self.placeholder, True, TEXT_MUTED)
        
        text_x = clip_rect.x - self.scroll_offset
        text_y = clip_rect.y + (clip_rect.height - text_surf.get_height()) // 2
        screen.blit(text_surf, (text_x, text_y))
        
        # Cursor parpadeante
        if self.is_active and self.cursor_visible and not self.selection_all:
            cursor_x = clip_rect.x + text_surf.get_width() - self.scroll_offset
            cursor_y1 = clip_rect.y + 4
            cursor_y2 = clip_rect.y + clip_rect.height - 4
            pygame.draw.line(screen, TEXT_PRIMARY, (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)
        
        screen.set_clip(original_clip)
    
    def update(self) -> None:
        """Actualiza la animación del cursor."""
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible


# Importar TEXT_MUTED que faltaba
from utils.constants import TEXT_MUTED
