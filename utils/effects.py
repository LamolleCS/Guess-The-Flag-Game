"""Sistema de efectos visuales espectaculares.

Incluye:
- Efectos RGB animados
- Partículas brillantes
- Halos de luz
- Sombras dinámicas
- Efectos de neón
"""
import pygame
import math
import random
from typing import Tuple, List, Optional

from utils.constants import (
    RGB_COLORS, NEON_PINK, NEON_BLUE, NEON_GREEN, 
    NEON_PURPLE, NEON_CYAN, NEON_ORANGE,
    PRIMARY, SECONDARY, ACCENT, SUCCESS
)


class RGBEffect:
    """Generador de colores RGB que ciclan suavemente."""
    
    def __init__(self, speed: float = 0.02):
        self.hue = 0.0
        self.speed = speed
    
    def update(self) -> None:
        """Actualiza el ciclo de color."""
        self.hue = (self.hue + self.speed) % 1.0
    
    def get_color(self, offset: float = 0.0) -> Tuple[int, int, int]:
        """Obtiene el color actual con offset opcional."""
        h = (self.hue + offset) % 1.0
        return self._hsv_to_rgb(h, 1.0, 1.0)
    
    def get_color_soft(self, offset: float = 0.0, saturation: float = 0.7) -> Tuple[int, int, int]:
        """Obtiene un color más suave/pastel."""
        h = (self.hue + offset) % 1.0
        return self._hsv_to_rgb(h, saturation, 1.0)
    
    @staticmethod
    def _hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
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


class Particle:
    """Partícula individual para efectos."""
    
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-3, -1)
        self.life = 1.0
        self.decay = random.uniform(0.01, 0.03)
        self.size = random.uniform(2, 5)
    
    def update(self) -> bool:
        """Actualiza la partícula. Retorna False si murió."""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05  # Gravedad
        self.life -= self.decay
        return self.life > 0
    
    def draw(self, surface: pygame.Surface) -> None:
        """Dibuja la partícula."""
        if self.life <= 0:
            return
        alpha = int(255 * self.life)
        size = int(self.size * self.life)
        if size < 1:
            return
        
        # Crear superficie con alpha
        particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, (*self.color, alpha), (size, size), size)
        surface.blit(particle_surf, (int(self.x - size), int(self.y - size)))


class ParticleSystem:
    """Sistema de partículas para efectos especiales."""
    
    def __init__(self, max_particles: int = 100):
        self.particles: List[Particle] = []
        self.max_particles = max_particles
    
    def emit(self, x: float, y: float, color: Tuple[int, int, int], count: int = 5) -> None:
        """Emite partículas en una posición."""
        for _ in range(count):
            if len(self.particles) < self.max_particles:
                self.particles.append(Particle(x, y, color))
    
    def update(self) -> None:
        """Actualiza todas las partículas."""
        self.particles = [p for p in self.particles if p.update()]
    
    def draw(self, surface: pygame.Surface) -> None:
        """Dibuja todas las partículas."""
        for particle in self.particles:
            particle.draw(surface)


def draw_glow(
    surface: pygame.Surface,
    center: Tuple[int, int],
    radius: int,
    color: Tuple[int, int, int],
    intensity: float = 1.0
) -> None:
    """Dibuja un efecto de brillo/glow."""
    glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    
    for i in range(radius, 0, -2):
        alpha = int((i / radius) * 60 * intensity)
        pygame.draw.circle(
            glow_surf, 
            (*color, alpha), 
            (radius * 2, radius * 2), 
            i * 2
        )
    
    surface.blit(glow_surf, (center[0] - radius * 2, center[1] - radius * 2))


def draw_neon_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: Tuple[int, int, int],
    radius: int = 8,
    glow_size: int = 15,
    intensity: float = 1.0
) -> None:
    """Dibuja un rectángulo con efecto neón."""
    # Crear superficie para el glow
    glow_rect = rect.inflate(glow_size * 2, glow_size * 2)
    glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
    
    # Múltiples capas de glow
    for i in range(glow_size, 0, -2):
        alpha = int((i / glow_size) * 40 * intensity)
        inflated = pygame.Rect(
            glow_size - i, glow_size - i,
            rect.width + i * 2, rect.height + i * 2
        )
        pygame.draw.rect(glow_surf, (*color, alpha), inflated, border_radius=radius + i//2)
    
    surface.blit(glow_surf, glow_rect.topleft)
    
    # Rectángulo principal
    pygame.draw.rect(surface, color, rect, 2, border_radius=radius)


def draw_neon_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    pos: Tuple[int, int],
    color: Tuple[int, int, int],
    glow_size: int = 10
) -> pygame.Rect:
    """Dibuja texto con efecto neón."""
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=pos)
    
    # Glow del texto
    for i in range(glow_size, 0, -2):
        alpha = int((i / glow_size) * 50)
        glow_surf = font.render(text, True, color)
        glow_surf.set_alpha(alpha)
        offset = i // 2
        for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
            surface.blit(glow_surf, (text_rect.x + dx, text_rect.y + dy))
    
    # Texto principal
    surface.blit(text_surf, text_rect)
    return text_rect


def draw_animated_border(
    surface: pygame.Surface,
    rect: pygame.Rect,
    rgb_effect: RGBEffect,
    time: float,
    thickness: int = 3,
    segments: int = 20
) -> None:
    """Dibuja un borde animado con colores RGB que fluyen."""
    perimeter = 2 * (rect.width + rect.height)
    segment_length = perimeter / segments
    
    for i in range(segments):
        # Calcular posición en el perímetro
        pos = (i * segment_length + time * 100) % perimeter
        
        # Color con offset basado en posición
        color = rgb_effect.get_color(i / segments)
        
        # Convertir posición en coordenadas
        if pos < rect.width:
            x1, y1 = rect.left + pos, rect.top
            x2, y2 = rect.left + min(pos + segment_length, rect.width), rect.top
        elif pos < rect.width + rect.height:
            p = pos - rect.width
            x1, y1 = rect.right, rect.top + p
            x2, y2 = rect.right, rect.top + min(p + segment_length, rect.height)
        elif pos < 2 * rect.width + rect.height:
            p = pos - rect.width - rect.height
            x1, y1 = rect.right - p, rect.bottom
            x2, y2 = rect.right - min(p + segment_length, rect.width), rect.bottom
        else:
            p = pos - 2 * rect.width - rect.height
            x1, y1 = rect.left, rect.bottom - p
            x2, y2 = rect.left, rect.bottom - min(p + segment_length, rect.height)
        
        pygame.draw.line(surface, color, (int(x1), int(y1)), (int(x2), int(y2)), thickness)


def draw_pulse_circle(
    surface: pygame.Surface,
    center: Tuple[int, int],
    base_radius: int,
    color: Tuple[int, int, int],
    time: float,
    pulse_amount: float = 0.2
) -> None:
    """Dibuja un círculo que pulsa."""
    pulse = math.sin(time * 3) * pulse_amount
    radius = int(base_radius * (1 + pulse))
    
    # Glow
    draw_glow(surface, center, radius, color, 0.5 + pulse * 0.5)
    
    # Círculo
    pygame.draw.circle(surface, color, center, radius, 2)


def get_flag_glow_color(country_name: str) -> Tuple[int, int, int]:
    """Obtiene un color de glow basado en el país."""
    # Colores según regiones/países conocidos
    country_colors = {
        # Países con rojo dominante
        'China': (255, 50, 50),
        'Japón': (255, 255, 255),
        'Canadá': (255, 50, 50),
        'Suiza': (255, 50, 50),
        'Turquía': (255, 50, 50),
        
        # Países con azul dominante
        'Francia': (0, 100, 255),
        'Reino Unido': (0, 50, 200),
        'Estados Unidos': (50, 50, 200),
        'Australia': (0, 50, 200),
        'Grecia': (0, 100, 255),
        
        # Países con verde dominante
        'Brasil': (0, 200, 100),
        'Italia': (0, 200, 100),
        'México': (0, 200, 100),
        'Irlanda': (0, 200, 100),
        'Arabia Saudita': (0, 200, 100),
        
        # Países con amarillo/dorado
        'España': (255, 200, 0),
        'Alemania': (255, 200, 0),
        'Colombia': (255, 200, 0),
        'Suecia': (255, 200, 0),
        
        # Países nórdicos - azul hielo
        'Noruega': (100, 150, 255),
        'Finlandia': (100, 150, 255),
        'Islandia': (100, 150, 255),
        'Dinamarca': (200, 50, 50),
        
        # Otros
        'Argentina': (100, 200, 255),
        'Uruguay': (100, 200, 255),
        'Rusia': (150, 100, 200),
        'India': (255, 150, 50),
    }
    
    # Si el país está en el diccionario, usar su color
    if country_name in country_colors:
        return country_colors[country_name]
    
    # Color por defecto basado en hash del nombre
    hash_val = sum(ord(c) for c in country_name)
    hue = (hash_val % 360) / 360.0
    return RGBEffect._hsv_to_rgb(hue, 0.8, 1.0)


def draw_flag_with_glow(
    surface: pygame.Surface,
    flag: pygame.Surface,
    pos: Tuple[int, int],
    country_name: str,
    time: float,
    glow_intensity: float = 1.0
) -> None:
    """Dibuja una bandera con efecto de glow basado en sus colores."""
    glow_color = get_flag_glow_color(country_name)
    
    # Efecto de pulso suave
    pulse = 0.7 + math.sin(time * 2) * 0.3
    
    flag_rect = flag.get_rect(center=pos)
    
    # Glow exterior
    glow_size = 25
    glow_surf = pygame.Surface(
        (flag_rect.width + glow_size * 2, flag_rect.height + glow_size * 2), 
        pygame.SRCALPHA
    )
    
    for i in range(glow_size, 0, -1):
        alpha = int((i / glow_size) * 40 * pulse * glow_intensity)
        inflated_rect = pygame.Rect(
            glow_size - i, glow_size - i,
            flag_rect.width + i * 2, flag_rect.height + i * 2
        )
        pygame.draw.rect(glow_surf, (*glow_color, alpha), inflated_rect, border_radius=5)
    
    surface.blit(glow_surf, (flag_rect.x - glow_size, flag_rect.y - glow_size))
    
    # Marco brillante
    frame_rect = flag_rect.inflate(6, 6)
    pygame.draw.rect(surface, glow_color, frame_rect, 3, border_radius=3)
    
    # Bandera
    surface.blit(flag, flag_rect)


def create_starfield(width: int, height: int, num_stars: int = 100) -> List[dict]:
    """Crea un campo de estrellas para el fondo."""
    stars = []
    for _ in range(num_stars):
        stars.append({
            'x': random.randint(0, width),
            'y': random.randint(0, height),
            'size': random.uniform(0.5, 2.5),
            'brightness': random.uniform(0.3, 1.0),
            'twinkle_speed': random.uniform(1, 4),
            'twinkle_offset': random.uniform(0, math.pi * 2),
        })
    return stars


def draw_starfield(
    surface: pygame.Surface, 
    stars: List[dict], 
    time: float
) -> None:
    """Dibuja el campo de estrellas con efecto de centelleo."""
    for star in stars:
        # Efecto de centelleo
        twinkle = (math.sin(time * star['twinkle_speed'] + star['twinkle_offset']) + 1) / 2
        brightness = star['brightness'] * (0.5 + twinkle * 0.5)
        
        color = (
            int(200 * brightness),
            int(200 * brightness),
            int(255 * brightness)
        )
        
        size = max(1, int(star['size'] * (0.8 + twinkle * 0.4)))
        
        if size <= 1:
            surface.set_at((int(star['x']), int(star['y'])), color)
        else:
            pygame.draw.circle(surface, color, (int(star['x']), int(star['y'])), size)


# =============================================================================
# SISTEMA DE CONFETTI PARA CELEBRACIONES
# =============================================================================

class ConfettiParticle:
    """Partícula de confetti con rotación y colores brillantes."""
    
    CONFETTI_COLORS = [
        (255, 50, 100),   # Rosa
        (50, 255, 150),   # Verde
        (100, 150, 255),  # Azul
        (255, 200, 50),   # Amarillo
        (200, 100, 255),  # Púrpura
        (255, 150, 50),   # Naranja
        (50, 255, 255),   # Cyan
    ]
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.color = random.choice(self.CONFETTI_COLORS)
        self.vx = random.uniform(-6, 6)
        self.vy = random.uniform(-15, -8)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-10, 10)
        self.width = random.randint(6, 12)
        self.height = random.randint(3, 6)
        self.life = 1.0
        self.gravity = 0.35
        self.air_resistance = 0.99
        self.swing_offset = random.uniform(0, math.pi * 2)
        self.swing_speed = random.uniform(3, 6)
    
    def update(self, dt: float = 1.0) -> bool:
        """Actualiza el confetti. Retorna False si murió."""
        # Movimiento con swing
        swing = math.sin(self.life * self.swing_speed + self.swing_offset) * 2
        self.x += self.vx + swing
        self.y += self.vy
        
        # Física
        self.vy += self.gravity
        self.vx *= self.air_resistance
        self.rotation += self.rotation_speed
        
        # Decay más lento
        self.life -= 0.008
        
        return self.life > 0 and self.y < 800  # También muere si sale de pantalla
    
    def draw(self, surface: pygame.Surface) -> None:
        """Dibuja el confetti con rotación."""
        if self.life <= 0:
            return
        
        alpha = min(255, int(255 * self.life * 1.5))
        
        # Crear superficie rotada
        w, h = self.width, self.height
        conf_surf = pygame.Surface((w * 2, h * 2), pygame.SRCALPHA)
        
        # Dibujar rectángulo de confetti
        rect = pygame.Rect(w // 2, h // 2, w, h)
        color_with_alpha = (*self.color, alpha)
        pygame.draw.rect(conf_surf, color_with_alpha, rect)
        
        # Rotar
        rotated = pygame.transform.rotate(conf_surf, self.rotation)
        
        # Dibujar en posición
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


class ConfettiSystem:
    """Sistema de confetti para celebraciones."""
    
    def __init__(self, max_particles: int = 150):
        self.particles: List[ConfettiParticle] = []
        self.max_particles = max_particles
        self.active = False
    
    def burst(self, x: float, y: float, count: int = 50) -> None:
        """Emite una explosión de confetti."""
        self.active = True
        for _ in range(count):
            if len(self.particles) < self.max_particles:
                self.particles.append(ConfettiParticle(x, y))
    
    def burst_wide(self, screen_width: int, y: float, count: int = 80) -> None:
        """Emite confetti a lo ancho de la pantalla."""
        self.active = True
        for _ in range(count):
            if len(self.particles) < self.max_particles:
                x = random.randint(50, screen_width - 50)
                self.particles.append(ConfettiParticle(x, y))
    
    def update(self) -> None:
        """Actualiza todas las partículas."""
        self.particles = [p for p in self.particles if p.update()]
        if not self.particles:
            self.active = False
    
    def draw(self, surface: pygame.Surface) -> None:
        """Dibuja todas las partículas de confetti."""
        for particle in self.particles:
            particle.draw(surface)
    
    def clear(self) -> None:
        """Limpia todas las partículas."""
        self.particles.clear()
        self.active = False


# Sistema global de confetti
_confetti_system: Optional[ConfettiSystem] = None


def get_confetti_system() -> ConfettiSystem:
    """Obtiene el sistema de confetti global."""
    global _confetti_system
    if _confetti_system is None:
        _confetti_system = ConfettiSystem()
    return _confetti_system


def trigger_confetti(x: float, y: float, count: int = 40) -> None:
    """Dispara confetti desde una posición específica."""
    system = get_confetti_system()
    system.burst(x, y, count)


def trigger_confetti_wide(screen_width: int, y: float = 100, count: int = 60) -> None:
    """Dispara confetti a lo ancho de la pantalla."""
    system = get_confetti_system()
    system.burst_wide(screen_width, y, count)


def update_confetti() -> None:
    """Actualiza el sistema de confetti."""
    system = get_confetti_system()
    system.update()


def draw_confetti(surface: pygame.Surface) -> None:
    """Dibuja el confetti en la superficie."""
    system = get_confetti_system()
    system.draw(surface)


def is_confetti_active() -> bool:
    """Verifica si hay confetti activo."""
    system = get_confetti_system()
    return system.active


# =============================================================================
# SISTEMA DE FLASH DE PANTALLA (ÉXITO / ERROR / SKIP)
# =============================================================================

class ScreenFlash:
    """Efecto de flash en pantalla con degradado desde los bordes."""
    
    def __init__(self):
        self.active = False
        self.color = (0, 255, 0)
        self.alpha = 0.0
        self.max_alpha = 80  # Sutil
        self.decay_speed = 4.0  # Velocidad de desvanecimiento
    
    def trigger(self, color: Tuple[int, int, int], intensity: float = 1.0) -> None:
        """Dispara un flash con el color dado."""
        self.active = True
        self.color = color
        self.alpha = self.max_alpha * intensity
    
    def update(self, dt: float = 1/60) -> None:
        """Actualiza el flash."""
        if self.active:
            self.alpha -= self.decay_speed
            if self.alpha <= 0:
                self.alpha = 0
                self.active = False
    
    def draw(self, surface: pygame.Surface) -> None:
        """Dibuja el flash como un vignette desde los bordes."""
        if not self.active or self.alpha <= 0:
            return
        
        width, height = surface.get_size()
        flash_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Crear efecto vignette (más intenso en bordes, transparente en centro)
        max_dist = math.sqrt((width/2)**2 + (height/2)**2)
        center_x, center_y = width // 2, height // 2
        
        # Dibujar gradiente radial desde los bordes
        for i in range(20, 0, -1):
            # Calcular alpha que aumenta hacia los bordes
            ring_alpha = int(self.alpha * (i / 20) * 0.7)
            if ring_alpha <= 0:
                continue
            
            # Dibujar rectángulos con bordes redondeados
            margin = int((20 - i) * max(width, height) / 50)
            rect = pygame.Rect(margin, margin, width - margin*2, height - margin*2)
            
            if rect.width > 0 and rect.height > 0:
                pygame.draw.rect(flash_surf, (*self.color, ring_alpha), rect, 
                               width=max(2, (20-i)*3), border_radius=20)
        
        surface.blit(flash_surf, (0, 0))


# Sistema global de flash
_screen_flash: Optional[ScreenFlash] = None


def get_screen_flash() -> ScreenFlash:
    """Obtiene el sistema de flash global."""
    global _screen_flash
    if _screen_flash is None:
        _screen_flash = ScreenFlash()
    return _screen_flash


def trigger_success_flash() -> None:
    """Dispara un flash verde sutil para éxito."""
    flash = get_screen_flash()
    flash.trigger((0, 255, 100), intensity=0.8)


def trigger_error_flash() -> None:
    """Dispara un flash rojo para error."""
    flash = get_screen_flash()
    flash.trigger((255, 50, 50), intensity=1.0)


def trigger_skip_flash() -> None:
    """Dispara un flash rojo/naranja para skip."""
    flash = get_screen_flash()
    flash.trigger((255, 100, 50), intensity=0.9)


def update_screen_flash(dt: float = 1/60) -> None:
    """Actualiza el flash de pantalla."""
    flash = get_screen_flash()
    flash.update(dt)


def draw_screen_flash(surface: pygame.Surface) -> None:
    """Dibuja el flash de pantalla."""
    flash = get_screen_flash()
    flash.draw(surface)
