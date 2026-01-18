"""Pantalla de configuración del juego.

Permite ajustar volumen, resolución y modo de pantalla.
"""
import pygame
import math
from typing import List, Tuple

from utils.constants import (
    RESOLUTIONS, WINDOW_MODES,
    FONT_SIZE, SMALL_FONT_SIZE, TITLE_FONT_SIZE,
    PRIMARY, PRIMARY_LIGHT, PRIMARY_DARK,
    SECONDARY, TEXT_PRIMARY, TEXT_SECONDARY,
    BG_CARD, SUCCESS, WHITE,
    NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_PURPLE
)
from utils.ui import (
    Button, draw_animated_background, draw_rounded_rect, draw_shadow,
    update_global_time, get_global_time, hsv_to_rgb, draw_neon_glow
)
from utils.i18n import tr
from utils import fonts


class SettingsScreen:
    """Pantalla de configuración del juego.
    
    Permite al usuario ajustar:
    - Volumen de música
    - Resolución de pantalla
    - Modo de ventana (ventana/pantalla completa/sin bordes)
    """
    
    def __init__(self, game) -> None:
        """Inicializa la pantalla de configuración.
        
        Args:
            game: Referencia a la instancia principal del juego.
        """
        self.game = game
        self.screen = game.screen

        # Estado de volumen
        self.volume_value: int = self._get_initial_volume()
        self.volume_dragging: bool = False
        self.volume_selected: bool = False
        self.volume_step: int = 5

        # Resoluciones y modos disponibles
        self.resolutions: List[Tuple[int, int]] = RESOLUTIONS
        self.current_resolution_idx: int = 0
        self.window_modes: List[str] = WINDOW_MODES
        self.current_mode_idx: int = 0

        # Crear botones
        self._create_buttons()

        # Fuentes modernas
        self.title_font = fonts.registry.get(TITLE_FONT_SIZE)
        self.font = fonts.registry.get(FONT_SIZE)
        self.small_font = fonts.registry.get(SMALL_FONT_SIZE)

        # Estado de cambios pendientes
        self.pending_changes: bool = False

        # Geometría del slider (se calcula en update)
        self.volume_rect = pygame.Rect(0, 0, 0, 0)
        self.slider_rect = pygame.Rect(0, 0, 0, 0)
        self.res_y: int = 0
        self.mode_y: int = 0
    
    def _get_initial_volume(self) -> int:
        """Obtiene el volumen inicial del juego."""
        if hasattr(self.game, 'get_music_volume'):
            try:
                return int(self.game.get_music_volume() * 100)
            except Exception:
                pass
        return 100
    
    def _create_buttons(self) -> None:
        """Crea los botones de la pantalla."""
        self.back_button = Button(20, 20, 120, 45, tr('common.back'), SMALL_FONT_SIZE, style=Button.STYLE_GHOST)
        self.apply_button = Button(700, 20, 120, 45, tr('settings.apply'), SMALL_FONT_SIZE, style=Button.STYLE_SUCCESS)
        self.res_left_button = Button(0, 0, 40, 40, "◀", SMALL_FONT_SIZE, style=Button.STYLE_SECONDARY)
        self.res_right_button = Button(0, 0, 40, 40, "▶", SMALL_FONT_SIZE, style=Button.STYLE_SECONDARY)
        self.mode_left_button = Button(0, 0, 40, 40, "◀", SMALL_FONT_SIZE, style=Button.STYLE_SECONDARY)
        self.mode_right_button = Button(0, 0, 40, 40, "▶", SMALL_FONT_SIZE, style=Button.STYLE_SECONDARY)

    # =========================================================================
    # MANEJO DE EVENTOS
    # =========================================================================
    
    def handle_events(self) -> None:
        """Procesa los eventos de entrada del usuario."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.quit()
                return
            
            # Ignorar scroll
            if event.type == pygame.MOUSEBUTTONDOWN:
                if getattr(event, 'button', 1) in (4, 5):
                    continue
            
            # ESC para volver al menú
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.change_screen("menu")
                continue

            # Botón volver
            if self.back_button.handle_event(event):
                self.game.change_screen("menu")
                continue
            
            # Botón aplicar
            if self.apply_button.handle_event(event) and self.pending_changes:
                self._apply_display_changes()
                continue

            # Eventos del slider de volumen
            self._handle_volume_events(event)
            
            # Navegación de resolución
            self._handle_resolution_events(event)
            
            # Navegación de modo de pantalla
            self._handle_mode_events(event)
    
    def _handle_volume_events(self, event: pygame.event.Event) -> None:
        """Procesa eventos relacionados con el slider de volumen."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.volume_rect.collidepoint(event.pos):
                self.volume_selected = True
                self.volume_dragging = True
                self._update_volume_from_mouse(event.pos[0])
            else:
                self.volume_selected = False
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.volume_dragging = False
        
        elif event.type == pygame.MOUSEMOTION and self.volume_dragging:
            self._update_volume_from_mouse(event.pos[0])
        
        elif event.type == pygame.KEYDOWN and self.volume_selected:
            if event.key == pygame.K_LEFT:
                self.volume_value = max(0, self.volume_value - self.volume_step)
                self._apply_volume()
            elif event.key == pygame.K_RIGHT:
                self.volume_value = min(100, self.volume_value + self.volume_step)
                self._apply_volume()
            elif event.key == pygame.K_ESCAPE:
                self.volume_selected = False
    
    def _handle_resolution_events(self, event: pygame.event.Event) -> None:
        """Procesa eventos de navegación de resolución."""
        if self.res_left_button.handle_event(event):
            self.current_resolution_idx = (
                self.current_resolution_idx - 1
            ) % len(self.resolutions)
            self.pending_changes = True
        elif self.res_right_button.handle_event(event):
            self.current_resolution_idx = (
                self.current_resolution_idx + 1
            ) % len(self.resolutions)
            self.pending_changes = True
    
    def _handle_mode_events(self, event: pygame.event.Event) -> None:
        """Procesa eventos de navegación de modo de pantalla."""
        if self.mode_left_button.handle_event(event):
            self.current_mode_idx = (
                self.current_mode_idx - 1
            ) % len(self.window_modes)
            self.pending_changes = True
        elif self.mode_right_button.handle_event(event):
            self.current_mode_idx = (
                self.current_mode_idx + 1
            ) % len(self.window_modes)
            self.pending_changes = True

    # =========================================================================
    # LÓGICA
    # =========================================================================
    
    def _update_volume_from_mouse(self, mouse_x: int) -> None:
        """Actualiza el volumen basándose en la posición del mouse."""
        relative_x = mouse_x - self.volume_rect.x
        self.volume_value = int(
            (relative_x / max(1, self.volume_rect.width)) * 100
        )
        self.volume_value = max(0, min(100, self.volume_value))
        self._apply_volume()
    
    def _apply_volume(self) -> None:
        """Aplica el volumen actual al juego."""
        if hasattr(self.game, 'set_music_volume'):
            self.game.set_music_volume(self.volume_value / 100.0)

    def update(self) -> None:
        """Actualiza el estado de la pantalla."""
        width = self.screen.get_width()
        height = self.screen.get_height()
        
        # Actualizar tiempo global
        update_global_time(1/60)
        
        # Actualizar animaciones de botones
        self.back_button.update()
        self.apply_button.update()
        self.res_left_button.update()
        self.res_right_button.update()
        self.mode_left_button.update()
        self.mode_right_button.update()
        
        # Slider volumen
        self.volume_width = int(width * 0.5)
        self.volume_height = max(12, int(height * 0.02))
        self.volume_x = (width - self.volume_width) // 2
        self.volume_y = int(height * 0.22)
        self.volume_rect = pygame.Rect(self.volume_x, self.volume_y, self.volume_width, self.volume_height)
        self.slider_width = max(20, int(height * 0.035))
        slider_center_x = self.volume_x + int(self.volume_width * (self.volume_value / 100))
        self.slider_rect = pygame.Rect(slider_center_x - self.slider_width // 2, self.volume_y - 8, self.slider_width, self.volume_height + 16)

        # Posiciones base de textos de resolución / modo
        self.res_y = int(height * 0.42)
        self.mode_y = int(height * 0.60)

        # Colocar flechas
        res_text = f"{self.resolutions[self.current_resolution_idx][0]}x{self.resolutions[self.current_resolution_idx][1]}"
        res_label = self.font.render(res_text, True, TEXT_PRIMARY)
        res_rect = res_label.get_rect(center=(width//2, self.res_y + 15))
        flecha_sep = 100
        self.res_left_button.rect.topleft = (res_rect.left - flecha_sep, self.res_y - 5)
        self.res_right_button.rect.topleft = (res_rect.right + flecha_sep - self.res_right_button.rect.width, self.res_y - 5)

        mode_key = self.window_modes[self.current_mode_idx]
        mode_label_txt = tr(f'window.mode.{mode_key}')
        mode_label = self.font.render(mode_label_txt, True, TEXT_PRIMARY)
        mode_rect = mode_label.get_rect(center=(width//2, self.mode_y + 15))
        self.mode_left_button.rect.topleft = (mode_rect.left - flecha_sep, self.mode_y - 5)
        self.mode_right_button.rect.topleft = (mode_rect.right + flecha_sep - self.mode_right_button.rect.width, self.mode_y - 5)

        self.apply_button.is_visible = self.pending_changes

    def _apply_display_changes(self) -> None:
        """Aplica los cambios de resolución y modo de pantalla."""
        resolution = self.resolutions[self.current_resolution_idx]
        mode = self.window_modes[self.current_mode_idx]
        
        flags = 0
        if mode == "fullscreen":
            flags = pygame.FULLSCREEN
        elif mode == "borderless":
            flags = pygame.FULLSCREEN | pygame.NOFRAME
        
        self.screen = pygame.display.set_mode(resolution, flags)
        self.game.screen = self.screen
        self.pending_changes = False

    # =========================================================================
    # DIBUJADO
    # =========================================================================
    
    def draw(self) -> None:
        """Dibuja la pantalla de configuración con efectos."""
        width = self.screen.get_width()
        height = self.screen.get_height()
        t = get_global_time()
        
        # Fondo animado con estrellas
        draw_animated_background(self.screen)

        # Botones superiores
        self.back_button.draw(self.screen)
        if self.pending_changes:
            self.apply_button.rect.x = width - 140
            self.apply_button.draw(self.screen)

        # Título con glow
        title_color = hsv_to_rgb((t * 0.05) % 1.0, 0.3, 1.0)
        title = self.title_font.render(tr('settings.title'), True, title_color)
        title_rect = title.get_rect(centerx=width//2, y=int(height*0.06))
        
        # Glow del título
        glow_surf = self.title_font.render(tr('settings.title'), True, NEON_CYAN)
        glow_surf.set_alpha(int(50 + 20 * math.sin(t * 2)))
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            self.screen.blit(glow_surf, (title_rect.x + dx, title_rect.y + dy))
        self.screen.blit(title, title_rect)

        # ===== SECCIÓN VOLUMEN =====
        section_width = int(width * 0.65)
        section_x = (width - section_width) // 2
        
        # Card de volumen con glow
        volume_card = pygame.Rect(section_x, int(height * 0.14), section_width, int(height * 0.16))
        draw_neon_glow(self.screen, volume_card, NEON_PURPLE, 0.3 + 0.1 * math.sin(t), 15)
        draw_shadow(self.screen, volume_card, radius=12)
        draw_rounded_rect(self.screen, BG_CARD, volume_card, 12)
        pygame.draw.rect(self.screen, NEON_PURPLE, volume_card, 1, border_radius=12)
        
        volume_label = self.font.render(f"🔊 {tr('settings.volume')}", True, TEXT_PRIMARY)
        self.screen.blit(volume_label, (volume_card.x + 20, volume_card.y + 15))
        
        # Valor de volumen con color según nivel
        vol_hue = 0.3 - (self.volume_value / 100) * 0.3  # Verde a rojo
        vol_color = hsv_to_rgb(vol_hue, 0.8, 1.0)
        vol_value_text = f"{int(self.volume_value)}%"
        vol_value = self.font.render(vol_value_text, True, vol_color)
        self.screen.blit(vol_value, (volume_card.right - vol_value.get_width() - 20, volume_card.y + 15))
        
        # Barra de fondo del slider
        track_color = (40, 40, 60)
        pygame.draw.rect(self.screen, track_color, self.volume_rect, border_radius=6)
        
        # Barra de progreso con gradiente RGB
        filled_width = int(self.volume_width * (self.volume_value / 100))
        if filled_width > 0:
            for x in range(filled_width):
                hue = (t * 0.2 + x / self.volume_width * 0.5) % 1.0
                color = hsv_to_rgb(hue, 0.8, 1.0)
                pygame.draw.line(self.screen, color, 
                               (self.volume_x + x, self.volume_y),
                               (self.volume_x + x, self.volume_y + self.volume_height - 1))
        
        # Handle del slider con glow
        handle_x = self.volume_x + int(self.volume_width * (self.volume_value / 100))
        handle_y = self.volume_y + self.volume_height // 2
        handle_radius = int(self.volume_height * 1.2)
        
        # Glow del handle
        handle_glow_color = hsv_to_rgb((t * 0.3) % 1.0, 0.8, 1.0)
        for i in range(handle_radius + 8, handle_radius, -1):
            alpha = int(80 * (1 - (i - handle_radius) / 8))
            glow_surf = pygame.Surface((i * 2, i * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*handle_glow_color, alpha), (i, i), i)
            self.screen.blit(glow_surf, (handle_x - i, handle_y - i))
        
        # Handle principal
        pygame.draw.circle(self.screen, handle_glow_color, (handle_x, handle_y), handle_radius)
        pygame.draw.circle(self.screen, (20, 20, 40), (handle_x, handle_y), handle_radius - 4)

        # ===== SECCIÓN RESOLUCIÓN =====
        res_card = pygame.Rect(section_x, int(height * 0.34), section_width, int(height * 0.14))
        draw_neon_glow(self.screen, res_card, NEON_CYAN, 0.3 + 0.1 * math.sin(t + 1), 15)
        draw_shadow(self.screen, res_card, radius=12)
        draw_rounded_rect(self.screen, BG_CARD, res_card, 12)
        pygame.draw.rect(self.screen, NEON_CYAN, res_card, 1, border_radius=12)
        
        res_title = self.font.render(f"🖥️ {tr('settings.resolution')}", True, TEXT_PRIMARY)
        self.screen.blit(res_title, (res_card.x + 20, res_card.y + 15))
        
        res_value = f"{self.resolutions[self.current_resolution_idx][0]}x{self.resolutions[self.current_resolution_idx][1]}"
        res_label = self.font.render(res_value, True, TEXT_SECONDARY)
        res_rect = res_label.get_rect(center=(width//2, res_card.centery + 15))
        self.screen.blit(res_label, res_rect)
        self.res_left_button.rect.centery = res_card.centery + 10
        self.res_right_button.rect.centery = res_card.centery + 10
        self.res_left_button.draw(self.screen)
        self.res_right_button.draw(self.screen)

        # ===== SECCIÓN MODO PANTALLA =====
        mode_card = pygame.Rect(section_x, int(height * 0.52), section_width, int(height * 0.14))
        draw_neon_glow(self.screen, mode_card, NEON_PINK, 0.3 + 0.1 * math.sin(t + 2), 15)
        draw_shadow(self.screen, mode_card, radius=12)
        draw_rounded_rect(self.screen, BG_CARD, mode_card, 12)
        pygame.draw.rect(self.screen, NEON_PINK, mode_card, 1, border_radius=12)
        
        mode_title = self.font.render(f"📺 {tr('settings.screen_mode')}", True, TEXT_PRIMARY)
        self.screen.blit(mode_title, (mode_card.x + 20, mode_card.y + 15))
        
        mode_key = self.window_modes[self.current_mode_idx]
        mode_label_txt = tr(f'window.mode.{mode_key}')
        mode_label = self.font.render(mode_label_txt, True, TEXT_SECONDARY)
        mode_rect = mode_label.get_rect(center=(width//2, mode_card.centery + 15))
        self.screen.blit(mode_label, mode_rect)
        self.mode_left_button.rect.centery = mode_card.centery + 10
        self.mode_right_button.rect.centery = mode_card.centery + 10
        self.mode_left_button.draw(self.screen)
        self.mode_right_button.draw(self.screen)

        # Hint aplicar con glow
        if self.pending_changes:
            hint_text = tr('settings.apply_hint', apply=tr('settings.apply'))
            hint_label = self.small_font.render(hint_text, True, NEON_GREEN)
            hint_rect = hint_label.get_rect(center=(width//2, int(height*0.90)))
            # Glow del hint
            glow_hint = self.small_font.render(hint_text, True, NEON_GREEN)
            glow_hint.set_alpha(int(50 + 30 * math.sin(t * 4)))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.screen.blit(glow_hint, (hint_rect.x + dx, hint_rect.y + dy))
            self.screen.blit(hint_label, hint_rect)

    def refresh_texts(self):
        self.back_button.text = tr('common.back')
        self.apply_button.text = tr('settings.apply')
