"""Pantalla principal del juego.

Implementa la lógica de los modos de juego:
- Adivinar banderas
- Adivinar capitales (por país o por capital)
"""
import random
import math
from typing import Dict, List, Optional, Tuple, Any

import pygame

from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SPACING,
    FONT_SIZE, SMALL_FONT_SIZE, FPS,
    WHITE, BLACK, GRAY, RED, GREEN, BLUE,
    KEY_REPEAT_DELAY, KEY_REPEAT_INTERVAL,
    PRIMARY, PRIMARY_LIGHT, SECONDARY, TEXT_PRIMARY, TEXT_SECONDARY,
    BG_CARD, SUCCESS, ERROR, WARNING,
    NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_PURPLE
)
from utils.ui import (
    Button, draw_animated_background, draw_rounded_rect, draw_shadow,
    update_global_time, get_global_time, hsv_to_rgb, draw_neon_glow
)
from utils.effects import (
    get_flag_glow_color, draw_flag_with_glow,
    trigger_confetti, update_confetti, draw_confetti,
    trigger_success_flash, trigger_skip_flash,
    update_screen_flash, draw_screen_flash
)
from utils import sounds
import utils.data as data_module
from utils.flag_manager import FlagManager
from utils.text_utils import are_strings_similar
from utils.i18n import tr
from utils import fonts


class GameScreen:
    """Pantalla principal del juego de geografía.
    
    Implementa:
    - Selección de región (global/continente)
    - Selección de modo (banderas/capitales)
    - Lógica de preguntas y respuestas
    - Sistema de puntuación y rondas extra
    - Persistencia de progreso en memoria
    
    Attributes:
        game: Referencia al juego principal.
        game_mode: Modo actual ('flags' o 'capitals').
        quiz_type: Tipo de quiz para capitales ('country' o 'capital').
        score: Puntuación actual.
        countries_left: Países restantes en la ronda.
    """
    # Almacén persistente de progreso (en memoria mientras el programa esté activo)
    PERSISTENT_PROGRESS: Dict[str, Dict[str, Any]] = {}

    def __init__(self, game) -> None:
        """Inicializa la pantalla de juego.
        
        Args:
            game: Referencia a la instancia principal del juego.
        """
        # Referencias básicas
        self.game = game
        self.screen = game.screen

        # Estado del juego
        self.game_mode: Optional[str] = None
        self.quiz_type: Optional[str] = None
        self.region_mode: Optional[str] = None
        self.selected_continent: Optional[str] = None

        # Coordenadas base para botones
        center_x = SCREEN_WIDTH // 2 - BUTTON_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 - BUTTON_HEIGHT - BUTTON_SPACING

        # Crear botones de región
        self._create_region_buttons(center_x, start_y)
        
        # Crear botones de continente
        self._create_continent_buttons(center_x, start_y)
        
        # Crear botones de modo
        self._create_mode_buttons(center_x, start_y)
        
        # Botón volver y saltear con estilos modernos
        self.back_button = Button(20, 20, 100, 40, tr('common.back'), SMALL_FONT_SIZE, style=Button.STYLE_GHOST)
        self.skip_button = Button(0, 0, 120, 40, tr('common.skip'), SMALL_FONT_SIZE, style=Button.STYLE_SECONDARY)

        # Configuración de input
        self._setup_input()
        
        # Estado dinámico del juego
        self._init_game_state()
        
        # Fuentes y configuración de teclado
        self.message_font = fonts.small_font()
        self.small_font = fonts.small_font()
        pygame.key.set_repeat(KEY_REPEAT_DELAY, KEY_REPEAT_INTERVAL)
        
        # Cachés de renderizado
        self._init_caches()
    
    # =========================================================================
    # MÉTODOS DE INICIALIZACIÓN
    # =========================================================================
    
    def _create_region_buttons(self, center_x: int, start_y: int) -> None:
        """Crea los botones de selección de región."""
        # Crear botones de región con estilos modernos
        self.global_button = Button(
            center_x, start_y - BUTTON_HEIGHT - BUTTON_SPACING,
            BUTTON_WIDTH, BUTTON_HEIGHT, tr('region.global'),
            style=Button.STYLE_PRIMARY
        )
        self.continent_button = Button(
            center_x, start_y,
            BUTTON_WIDTH, BUTTON_HEIGHT, tr('region.by_continent'),
            style=Button.STYLE_SECONDARY
        )
    
    def _create_continent_buttons(self, center_x: int, start_y: int) -> None:
        """Crea los botones de selección de continente."""
        from utils.data import get_all_continents
        self.continent_buttons: List[Button] = []
        self.continents = get_all_continents()
        for i, cont in enumerate(self.continents):
            btn_y = start_y + i * (BUTTON_HEIGHT + BUTTON_SPACING)
            self.continent_buttons.append(
                Button(center_x, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT, cont, style=Button.STYLE_SECONDARY)
            )
    
    def _create_mode_buttons(self, center_x: int, start_y: int) -> None:
        """Crea los botones de selección de modo."""
        self.flags_button = Button(
            center_x, start_y,
            BUTTON_WIDTH, BUTTON_HEIGHT, tr('mode.flags'),
            style=Button.STYLE_PRIMARY
        )
        self.capitals_button = Button(
            center_x, start_y + BUTTON_HEIGHT + BUTTON_SPACING,
            BUTTON_WIDTH, BUTTON_HEIGHT, tr('mode.capitals'),
            style=Button.STYLE_SECONDARY
        )
        self.by_country_button = Button(
            center_x, start_y,
            BUTTON_WIDTH, BUTTON_HEIGHT, tr('capitals.by_country'),
            style=Button.STYLE_PRIMARY
        )
        self.by_capital_button = Button(
            center_x, start_y + BUTTON_HEIGHT + BUTTON_SPACING,
            BUTTON_WIDTH, BUTTON_HEIGHT, tr('capitals.by_capital'),
            style=Button.STYLE_SECONDARY
        )
    
    def _setup_input(self) -> None:
        """Configura el campo de entrada de texto."""
        self.input_text: str = ""
        self.input_rect = pygame.Rect(
            (SCREEN_WIDTH - 300) // 2, SCREEN_HEIGHT - 100, 300, 40
        )
        self.input_active: bool = False
        self.font = fonts.main_font()
        self.input_scroll_offset: int = 0
        self.selection_all: bool = False
        self._enter_skip_guard: bool = False
        self._esc_hold_guard: bool = False
    
    def _init_game_state(self) -> None:
        """Inicializa el estado del juego."""
        self.flag_manager = FlagManager()
        self.current_country: Optional[str] = None
        self.current_capital: Optional[str] = None
        self.message: str = ""
        self.message_color = BLACK
        self.message_timer: int = 0
        self._message_surface: Optional[pygame.Surface] = None
        self.score: int = 0
        self.countries_left: List[str] = []
        self.total_countries: int = 0
        self.failed_countries: List[str] = []
        self.max_score: int = 0
        self.chrono_start: Optional[int] = None
        self.chrono_elapsed: int = 0
        self.chrono_running: bool = False
        self.round_phase: str = 'full'
    
    def _init_caches(self) -> None:
        """Inicializa los cachés de renderizado."""
        self._render_cache: Dict[Tuple, pygame.Surface] = {}
        self._highlight_cache: Dict[Tuple[int, int], pygame.Surface] = {}
        self._prompt_cache: Dict[Tuple[str, str], pygame.Surface] = {}
        self._frame_ticks: int = 0
        self._debug: bool = False
    
    # =========================================================================
    # MÉTODOS DE CACHÉ Y RENDERIZADO
    # =========================================================================

    def _render(self, font, text, color=BLACK):
        """Devuelve una superficie de texto cacheada para evitar renderizado repetido.
        No se usa para mensajes con fade (que ya tienen su propio cache)."""
        key = (id(font), text, color)
        surf = self._render_cache.get(key)
        if surf is None:
            surf = font.render(text, True, color)
            self._render_cache[key] = surf
        return surf

    def _get_highlight_surface(self, size):
        """Superficie reutilizable semi-transparente para selección completa en input."""
        key = size
        surf = self._highlight_cache.get(key)
        if surf is None:
            w, h = size
            surf = pygame.Surface((w, h))
            surf.fill((180, 210, 255))
            surf.set_alpha(160)
            self._highlight_cache[key] = surf
        return surf

    def _get_prompt_surface(self, kind: str, dynamic_value: str):
        """Cachea superficies de prompts que combinan un valor dinámico (país/capital).
        
        Renderiza una tarjeta elegante con el texto.
        """
        key = (kind, dynamic_value)
        surf = self._prompt_cache.get(key)
        if surf is None:
            if kind == 'country':
                label = tr('prompt.country_label', country=dynamic_value) if hasattr(tr, '__call__') else "País:"
                label = "Pais"
                value = dynamic_value
            elif kind == 'capital':
                label = "Capital"
                value = dynamic_value
            else:
                label = ""
                value = dynamic_value
            
            # Fuentes
            label_font = fonts.registry.get(20)
            value_font = fonts.registry.get(42)
            
            # Renderizar textos
            label_surf = label_font.render(label, True, TEXT_SECONDARY)
            value_surf = value_font.render(value, True, TEXT_PRIMARY)
            
            # Calcular dimensiones de la tarjeta
            padding_x = 40
            padding_y = 20
            card_width = max(label_surf.get_width(), value_surf.get_width()) + padding_x * 2
            card_height = label_surf.get_height() + value_surf.get_height() + padding_y * 3
            
            # Crear superficie de la tarjeta
            surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
            
            # Fondo de la tarjeta con gradiente sutil
            card_rect = pygame.Rect(0, 0, card_width, card_height)
            
            # Fondo oscuro semi-transparente
            pygame.draw.rect(surf, (25, 25, 50, 220), card_rect, border_radius=16)
            
            # Borde con glow
            pygame.draw.rect(surf, (80, 80, 140), card_rect, 2, border_radius=16)
            
            # Línea decorativa superior
            line_y = padding_y + label_surf.get_height() + 8
            pygame.draw.line(surf, (60, 60, 100), 
                           (padding_x // 2, line_y), 
                           (card_width - padding_x // 2, line_y), 1)
            
            # Posicionar textos centrados
            label_x = (card_width - label_surf.get_width()) // 2
            value_x = (card_width - value_surf.get_width()) // 2
            
            # Dibujar label
            surf.blit(label_surf, (label_x, padding_y))
            
            # Dibujar valor con sombra
            shadow_color = (20, 20, 40)
            shadow_surf = value_font.render(value, True, shadow_color)
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                surf.blit(shadow_surf, (value_x + dx, line_y + padding_y + dy))
            surf.blit(value_surf, (value_x, line_y + padding_y))
            
            self._prompt_cache[key] = surf
        return surf

    def _draw_rgb_rotating_border(self, rect: pygame.Rect, t: float, thickness: int = 2) -> None:
        """Dibuja un borde RGB que gira uniformemente alrededor del rectángulo.
        
        El color fluye continuamente por todo el perímetro como si fuera una serpiente RGB.
        """
        # Calcular el perímetro total
        perimeter = 2 * (rect.width + rect.height)
        
        # Velocidad de rotación del gradiente
        speed = 0.4
        time_offset = t * speed
        
        # Dibujar cada píxel del borde con el color correspondiente
        # El hue se calcula basado en la posición relativa en el perímetro
        
        # Borde superior (izquierda a derecha)
        for x in range(rect.width):
            pos_in_perimeter = x
            hue = (time_offset + pos_in_perimeter / perimeter) % 1.0
            color = hsv_to_rgb(hue, 1.0, 1.0)
            for dy in range(thickness):
                self.screen.set_at((rect.x + x, rect.y + dy), color)
        
        # Borde derecho (arriba a abajo)
        for y in range(rect.height):
            pos_in_perimeter = rect.width + y
            hue = (time_offset + pos_in_perimeter / perimeter) % 1.0
            color = hsv_to_rgb(hue, 1.0, 1.0)
            for dx in range(thickness):
                self.screen.set_at((rect.right - 1 - dx, rect.y + y), color)
        
        # Borde inferior (derecha a izquierda)
        for x in range(rect.width):
            pos_in_perimeter = rect.width + rect.height + x
            hue = (time_offset + pos_in_perimeter / perimeter) % 1.0
            color = hsv_to_rgb(hue, 1.0, 1.0)
            for dy in range(thickness):
                self.screen.set_at((rect.right - 1 - x, rect.bottom - 1 - dy), color)
        
        # Borde izquierdo (abajo a arriba)
        for y in range(rect.height):
            pos_in_perimeter = 2 * rect.width + rect.height + y
            hue = (time_offset + pos_in_perimeter / perimeter) % 1.0
            color = hsv_to_rgb(hue, 1.0, 1.0)
            for dx in range(thickness):
                self.screen.set_at((rect.x + dx, rect.bottom - 1 - y), color)

    def _draw_modern_timer(self, width: int, height: int, t: float) -> None:
        """Dibuja un cronómetro minimalista y elegante.
        
        Args:
            width: Ancho de la pantalla.
            height: Alto de la pantalla.
            t: Tiempo global para animaciones.
        """
        mins = self.chrono_elapsed // 60
        secs = self.chrono_elapsed % 60
        
        # Fuente para el timer (más grande)
        time_font = fonts.registry.get(32)
        
        # Formato del tiempo
        time_str = f"{mins:02d}:{secs:02d}"
        
        # Determinar color según tiempo transcurrido (más sutil)
        if self.chrono_elapsed < 60:
            text_color = TEXT_SECONDARY
        elif self.chrono_elapsed < 180:
            text_color = (200, 200, 150)  # Ligeramente amarillento
        else:
            text_color = (200, 150, 150)  # Ligeramente rojizo
        
        # Renderizar tiempo
        time_surf = time_font.render(time_str, True, text_color)
        time_rect = time_surf.get_rect(center=(width // 2, 35))
        
        # Fondo pill semi-transparente
        padding_x = 20
        padding_y = 10
        pill_rect = time_rect.inflate(padding_x * 2, padding_y * 2)
        
        pill_surf = pygame.Surface((pill_rect.width, pill_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(pill_surf, (20, 20, 35, 150), 
                        pygame.Rect(0, 0, pill_rect.width, pill_rect.height), 
                        border_radius=pill_rect.height // 2)
        pygame.draw.rect(pill_surf, (60, 60, 80, 100), 
                        pygame.Rect(0, 0, pill_rect.width, pill_rect.height), 
                        1, border_radius=pill_rect.height // 2)
        
        self.screen.blit(pill_surf, pill_rect.topleft)
        self.screen.blit(time_surf, time_rect)

    def _draw_modern_score(self, width: int, height: int, t: float) -> None:
        """Dibuja el puntaje con diseño moderno en la esquina superior derecha.
        
        Args:
            width: Ancho de la pantalla.
            height: Alto de la pantalla.
            t: Tiempo global para animaciones.
        """
        # Fuentes (más grandes)
        label_font = fonts.registry.get(16)
        score_font = fonts.registry.get(32)
        
        # Calcular porcentaje de progreso
        progress = self.score / max(1, self.total_countries)
        
        # Dimensiones de la tarjeta (más grande)
        card_width = 170
        card_height = 70
        card_x = width - card_width - 20  # Esquina superior derecha
        card_y = 15
        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        
        # Color de acento basado en progreso
        if progress >= 1.0:
            accent_color = NEON_GREEN
        elif progress >= 0.7:
            accent_color = NEON_CYAN
        elif progress >= 0.4:
            accent_color = (255, 200, 50)  # Amarillo
        else:
            accent_color = NEON_PURPLE
        
        # Fondo de la tarjeta semi-transparente
        card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (20, 20, 40, 180), 
                        pygame.Rect(0, 0, card_width, card_height), border_radius=10)
        
        # Borde sutil
        pygame.draw.rect(card_surf, (60, 60, 90, 150), 
                        pygame.Rect(0, 0, card_width, card_height), 1, border_radius=10)
        
        self.screen.blit(card_surf, card_rect.topleft)
        
        # Etiqueta "Puntaje"
        label_text = tr('label.score')
        label_surf = label_font.render(label_text, True, TEXT_SECONDARY)
        label_rect = label_surf.get_rect(midtop=(card_rect.centerx, card_rect.y + 5))
        self.screen.blit(label_surf, label_rect)
        
        # Puntaje principal
        score_str = f"{self.score}/{self.total_countries}"
        score_surf = score_font.render(score_str, True, accent_color)
        score_rect = score_surf.get_rect(center=(card_rect.centerx, card_rect.centery + 2))
        self.screen.blit(score_surf, score_rect)
        
        # Barra de progreso
        bar_width = card_width - 16
        bar_height = 5
        bar_x = card_rect.x + 8
        bar_y = card_rect.bottom - 10
        
        # Fondo de la barra
        pygame.draw.rect(self.screen, (30, 30, 50), 
                        pygame.Rect(bar_x, bar_y, bar_width, bar_height), border_radius=2)
        
        # Progreso
        if progress > 0:
            filled_width = int(bar_width * progress)
            if filled_width > 0:
                pygame.draw.rect(self.screen, accent_color, 
                               pygame.Rect(bar_x, bar_y, filled_width, bar_height), border_radius=2)

    def navigate_back(self):
        """
        Maneja retroceso jerárquico entre submenús interconectados.

        Orden de niveles (más profundo a más superficial):
        1. Juego en curso (banderas o capitales ya iniciado)
        2. Selección de sub-modo de capitales (quiz_type)
        3. Selección de modo de juego (banderas / capitales)
        4. Selección de continente (cuando region_mode == 'continente' y aún no elegido continente)
        5. Selección de región (global vs continente)
        6. Menú principal (cambio de pantalla)
        """
        # Si hay una partida en curso (hay país actual) salimos al nivel de selección anterior
        if (self.current_country is not None) or (
            self.game_mode and getattr(self, 'round_phase', 'full') == 'retry' and (self.countries_left or self.failed_countries)
        ):
            # Guardar progreso antes de salir del juego activo
            self._save_progress()
            # Si estamos en capitales con quiz_type definido, primero retroceder a seleccionar quiz_type
            if self.game_mode == 'capitals' and self.quiz_type:
                self.current_country = None
                self.countries_left = []
                self.quiz_type = None
                self.chrono_running = False
                if hasattr(self.game, 'play_menu_music'):
                    self.game.play_menu_music()
                return
            # Si estamos en banderas (o capitals sin quiz_type por diseño no ocurre) retroceder a selección de modo
            self.current_country = None
            self.countries_left = []
            self.chrono_running = False
            self.game_mode = None
            if hasattr(self.game, 'play_menu_music'):
                self.game.play_menu_music()
            return
        # Si estábamos eligiendo quiz_type (capitals) y queremos volver a modos
        if self.game_mode == 'capitals' and self.quiz_type is None:
            self.game_mode = None
            if hasattr(self.game, 'play_menu_music') and self.current_country is None:
                self.game.play_menu_music()
            return
        # Si estamos en selección de modo de juego, volver a selección de continente o global
        if self.game_mode is None and self.region_mode is not None:
            # Si era por continente y ya se había elegido uno, retroceder a lista de continentes
            if self.region_mode == 'continente' and self.selected_continent is not None:
                self.selected_continent = None
                return
            # Volver a elección global / continente
            self.region_mode = None
            self.selected_continent = None
            if hasattr(self.game, 'play_menu_music') and self.current_country is None:
                self.game.play_menu_music()
            return
        # Último paso: volver al menú principal
        self.game.change_screen("menu")

    # ---------------- Progreso en memoria -----------------
    def _progress_key(self):
        if not self.game_mode:
            return None
        parts = [self.region_mode or 'global']
        if self.region_mode == 'continente':
            parts.append(self.selected_continent or '')
        parts.append(self.game_mode)
        if self.game_mode == 'capitals':
            parts.append(self.quiz_type or '')
        return '|'.join(parts)

    def _save_progress(self):
        key = self._progress_key()
        if not key or self.total_countries == 0:
            return
        # Evitar guardar una partida recién iniciada (sin aciertos) salvo que estemos en ronda de fallados
        if self.score <= 0 and self.round_phase != 'retry':
            return
        GameScreen.PERSISTENT_PROGRESS[key] = {
            'countries_left': self.countries_left.copy(),
            'failed_countries': self.failed_countries.copy(),
            'score': self.score,
            'total': self.total_countries,
            'current_country': self.current_country,
            'current_capital': self.current_capital,
            'chrono_elapsed': self.chrono_elapsed,
            'chrono_running': self.chrono_running,
            'round_phase': self.round_phase,
        }

    def _clear_progress(self):
        """Elimina el progreso persistente actual (se usa tras finalizar completamente un juego)."""
        key = self._progress_key()
        if key and key in GameScreen.PERSISTENT_PROGRESS:
            del GameScreen.PERSISTENT_PROGRESS[key]

    def _get_mode_progress(self, mode: str):
        """Devuelve (score,total) para el modo dado ("flags" o "capitals") en la región/continente actual.
        Para capitals revisa ambos sub-modos y elige el de mayor avance (score/total)."""
        if self.region_mode is None:
            return None
        base_parts = [self.region_mode or 'global']
        if self.region_mode == 'continente':
            base_parts.append(self.selected_continent or '')
        base_parts.append(mode)
        base_prefix = '|'.join(base_parts)
        best = None
        for key, state in GameScreen.PERSISTENT_PROGRESS.items():
            if not key.startswith(base_prefix):
                continue
            total = state.get('total', 0) or 0
            score = state.get('score', 0) or 0
            if total <= 0 or score <= 0:
                continue  # ignorar sin progreso real
            ratio = score / total if total else 0
            if not best or ratio > best[2]:
                best = (score, total, ratio)
        if best:
            return best[0], best[1]
        return None

    def _get_capitals_sub_progress(self, sub: str):
        """Devuelve (score,total) para sub-modo de capitals ('country' o 'capital') en contexto actual."""
        if self.region_mode is None:
            return None
        parts = [self.region_mode or 'global']
        if self.region_mode == 'continente':
            parts.append(self.selected_continent or '')
        parts.extend(['capitals', sub])
        key = '|'.join(parts)
        state = GameScreen.PERSISTENT_PROGRESS.get(key)
        if state and state.get('score', 0) > 0 and state.get('total', 0) > 0:
            return state['score'], state['total']
        return None

    def _load_progress(self):
        key = self._progress_key()
        if not key:
            return False
        state = GameScreen.PERSISTENT_PROGRESS.get(key)
        if not state:
            return False
        self.countries_left = state['countries_left'].copy()
        self.failed_countries = state['failed_countries'].copy()
        self.score = state['score']
        self.total_countries = state['total']
        self.current_country = state['current_country']
        self.current_capital = state['current_capital']
        self.chrono_elapsed = state.get('chrono_elapsed', 0)
        self.chrono_running = state.get('chrono_running', False)
        self.round_phase = state.get('round_phase', 'full')
        # Si estamos en ronda de fallados y aún no empezó (sin país actual) reanudar mostrando mensaje y seleccionando
        if self.round_phase == 'retry' and self.current_country is None and self.countries_left:
            # Mostrar mensaje informativo otra vez
            try:
                self.show_message(tr('msg.round_extra'), BLUE)
            except Exception:
                pass
            # Seleccionar inmediatamente uno (sin esperar temporizador)
            self.select_new_country()
        if self.chrono_running:
            self.chrono_start = pygame.time.get_ticks() - self.chrono_elapsed * 1000
        return True

    def handle_events(self):
        # Cachear tick de frame al inicio (si se usa repetidamente en futuro)
        self._frame_ticks = pygame.time.get_ticks()
        if self.chrono_running and self.chrono_start is not None:
            now = self._frame_ticks
            self.chrono_elapsed = int((now - self.chrono_start) / 1000)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.quit()
                return
            # Evento de temporizador para comenzar la ronda extra (USEREVENT + 1)
            if event.type == pygame.USEREVENT + 1:
                # Detener este temporizador y seleccionar el primer país de la nueva ronda
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                self.select_new_country()
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, 'button', 1) in (4, 5):
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if not self._esc_hold_guard:  # Solo una acción por pulsación
                    self._esc_hold_guard = True
                    self.navigate_back()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                # Toggle debug overlay
                self._debug = not self._debug
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                self._esc_hold_guard = False
            if self.back_button.handle_event(event):
                self.navigate_back()
                return
            if self.region_mode is None:
                if self.global_button.handle_event(event):
                    self.region_mode = 'global'
                elif self.continent_button.handle_event(event):
                    self.region_mode = 'continente'
            elif self.region_mode == 'continente' and self.selected_continent is None:
                for i, btn in enumerate(self.continent_buttons):
                    if btn.handle_event(event):
                        self.selected_continent = self.continents[i]
                        break
            elif not self.game_mode:
                if self.flags_button.handle_event(event):
                    self.game_mode = "flags"
                    # Intentar reanudar progreso
                    if self._load_progress():
                        # Al reanudar partida asegurarse de cambiar a música de juego
                        if hasattr(self.game, 'play_game_music'):
                            self.game.play_game_music()
                    else:
                        self.start_new_game()
                elif self.capitals_button.handle_event(event):
                    self.game_mode = "capitals"
            elif self.game_mode == "capitals" and not self.quiz_type:
                if self.by_country_button.handle_event(event):
                    self.quiz_type = "country"
                    if self._load_progress():
                        if hasattr(self.game, 'play_game_music'):
                            self.game.play_game_music()
                    else:
                        self.start_new_game()
                elif self.by_capital_button.handle_event(event):
                    self.quiz_type = "capital"
                    if self._load_progress():
                        if hasattr(self.game, 'play_game_music'):
                            self.game.play_game_music()
                    else:
                        self.start_new_game()
            else:
                if self.skip_button.handle_event(event):
                    if self.current_country:
                        self.failed_countries.append(self.current_country)
                        # Efecto visual y sonido de skip
                        trigger_skip_flash()
                        sounds.play_skip()
                        # Mensaje detallado según modo
                        if self.game_mode == 'flags':
                            msg = tr('msg.skipped_flag', country=self.current_country)
                        elif self.game_mode == 'capitals':
                            if self.quiz_type == 'country':  # Mostramos capital correcta de ese país
                                country_obj = data_module.COUNTRIES[self.current_country]
                                msg = tr('msg.skipped_capital_country', country=self.current_country, capital=country_obj.capital)
                            else:  # quiz_type == 'capital' se preguntaba país dado capital
                                country_obj = data_module.COUNTRIES[self.current_country]
                                msg = tr('msg.skipped_capital_name', country=self.current_country, capital=country_obj.capital)
                        else:
                            msg = tr('msg.skipped_flag', country=self.current_country)
                        self.show_message(msg, RED)
                        self.select_new_country()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.input_active = self.input_rect.collidepoint(event.pos)
                    # Cualquier click limpia selección completa
                    if self.input_active:
                        self.selection_all = False
                if event.type == pygame.KEYDOWN and self.input_active:
                    mods = pygame.key.get_mods()
                    # CTRL + A => seleccionar todo
                    if event.key == pygame.K_a and (mods & pygame.KMOD_CTRL):
                        if self.input_text:
                            self.selection_all = True
                        return
                    if event.key == pygame.K_RETURN:
                        if not self._enter_skip_guard and self.current_country:
                            self._enter_skip_guard = True
                            self.failed_countries.append(self.current_country)
                            # Efecto visual y sonido de skip
                            trigger_skip_flash()
                            sounds.play_skip()
                            if self.game_mode == 'flags':
                                msg = tr('msg.skipped_flag', country=self.current_country)
                            elif self.game_mode == 'capitals':
                                if self.quiz_type == 'country':
                                    country_obj = data_module.COUNTRIES[self.current_country]
                                    msg = tr('msg.skipped_capital_country', country=self.current_country, capital=country_obj.capital)
                                else:
                                    country_obj = data_module.COUNTRIES[self.current_country]
                                    msg = tr('msg.skipped_capital_name', country=self.current_country, capital=country_obj.capital)
                            else:
                                msg = tr('msg.skipped_flag', country=self.current_country)
                            self.show_message(msg, RED)
                            self.select_new_country()
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        if self.input_text:
                            if self.selection_all:
                                self.input_text = ""
                                self.selection_all = False
                            else:
                                self.input_text = self.input_text[:-1]
                    else:
                        if event.unicode and event.unicode.isprintable():
                            if self.selection_all:
                                # Reemplaza todo el contenido
                                self.input_text = event.unicode
                                self.selection_all = False
                            else:
                                self.input_text += event.unicode
                    inner_width = self.input_rect.width - 12
                    rendered = self.font.render(self.input_text, True, BLACK)
                    self.input_scroll_offset = max(0, rendered.get_width() - inner_width)
                    # Chequeo automático sin Enter
                    self.auto_check_current()
                elif event.type == pygame.KEYUP and self.input_active and event.key == pygame.K_RETURN:
                    self._enter_skip_guard = False

    def start_new_game(self, retry_failed: bool = False):
        # Al iniciar realmente una partida (no sólo navegando menús) cambiar a música de juego
        if hasattr(self.game, 'play_game_music') and not retry_failed:
            self.game.play_game_music()
        self.chrono_start = pygame.time.get_ticks()
        self.chrono_elapsed = 0
        self.chrono_running = True
        # Limpiar cualquier mensaje previo al comenzar una nueva partida
        self.message = ""
        self.message_timer = 0
        from utils.data import get_countries_in_continent
        if retry_failed and self.failed_countries:
            self.countries_left = self.failed_countries.copy()
            self.failed_countries = []
            self.round_phase = 'retry'
        else:
            if self.region_mode == 'continente' and self.selected_continent:
                self.countries_left = list(get_countries_in_continent(self.selected_continent))
            else:
                self.countries_left = list(data_module.COUNTRIES.keys())
            self.failed_countries = []
            self.round_phase = 'full'
            # Se eliminó la visualización de máximo según requerimiento
        self.total_countries = len(self.countries_left)
        self.score = 0
        self.select_new_country()

    def select_new_country(self):
        # Si aún quedan países en la lista actual, continuar
        if self.countries_left:
            # Selección O(1) sin remove lineal: swap-pop
            idx = random.randrange(len(self.countries_left))
            self.current_country = self.countries_left[idx]
            last = self.countries_left[-1]
            self.countries_left[idx] = last
            self.countries_left.pop()
            self.input_text = ""
            self.input_scroll_offset = 0
            self.selection_all = False
            if self.game_mode == "capitals" and self.quiz_type == "capital":
                self.current_capital = data_module.COUNTRIES[self.current_country].capital
            else:
                self.current_capital = None
            return

        # No quedan en la lista actual. ¿Hubo fallos esta ronda?
        if self.failed_countries:
            # Preparar nueva ronda solo con fallados
            remaining = len(self.failed_countries)
            self.countries_left = self.failed_countries.copy()
            self.failed_countries = []
            self.score = 0  # Reiniciar contador para la ronda de pendientes
            self.total_countries = remaining
            self.round_phase = 'retry'
            # Limpiar current_country para que se interprete como estado de espera antes del primer país de la ronda retry
            self.current_country = None
            self.show_message(tr('msg.round_extra'), BLUE)
            pygame.time.set_timer(pygame.USEREVENT + 1, 1200)
            return

        # No quedan fallos: juego completo
        self.chrono_running = False
        # Actualizar récord si esta última ronda superó el máximo previo
        if self.score > self.max_score:
            self.max_score = self.score
        # Si se completó de una (sin fallos nunca) mostrar congrats especial
        if self.score == self.total_countries and self.total_countries > 0:
            self.show_message(tr('msg.congrats_all'), GREEN)
        else:
            # Mensaje de finalización estándar (todas completadas, con errores intermedios)
            self.show_message(
                tr('msg.congrats_completed', score=self.score, total=self.total_countries, max_score=self.max_score, time=self.chrono_elapsed),
                GREEN,
            )
        self.current_country = None
        self.current_capital = None
        self.round_phase = 'full'
        # Extender duración del mensaje final para que sea visible (si ya se asignó)
        if hasattr(self, 'message_timer') and self.message:
            self.message_timer = 600  # ~10s
        # Borrar progreso para que al re-entrar se inicie desde cero
        self._clear_progress()

    def show_message(self, text, color):
        self.message = text
        self.message_color = color
        # Cache superficie base (sin alpha variable)
        self._message_surface = self.message_font.render(self.message, True, self.message_color)
        # Duración base distinta según tipo (éxito vs error / info)
        if color == GREEN:
            self.message_timer = 48   # ~0.8s a 60 FPS
            self.message_fade_cutoff = 0.3  # Fade solo en el último 30% (desaparece rápido)
            # ¡Disparar confetti de celebración!
            trigger_confetti(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3, 50)
        elif color == RED:
            self.message_timer = 180  # 3s
            self.message_fade_cutoff = 0.25
        else:  # Azul u otros informativos
            self.message_timer = 150
            self.message_fade_cutoff = 0.25
        self.message_fade_total = self.message_timer

    def check_answer(self):
        if not self.current_country:
            return
        user_input = self.input_text.strip()
        country_obj = data_module.COUNTRIES[self.current_country]
        if self.game_mode == "capitals":
            if self.quiz_type == "country":
                correct = are_strings_similar(user_input, country_obj.capital)
                if correct:
                    self.score += 1
                    self._save_progress()
                    trigger_success_flash()  # Efecto verde sutil
                    sounds.play_success()
                    self.show_message(tr('msg.correct'), GREEN)
                else:
                    self.failed_countries.append(self.current_country)
                    sounds.play_error()
                    self.show_message(tr('msg.wrong_capital', answer=country_obj.capital), RED)
                self.select_new_country()
            elif self.quiz_type == "capital":
                correct = country_obj.check_name_match(user_input)
                if correct:
                    self.score += 1
                    self._save_progress()
                    trigger_success_flash()  # Efecto verde sutil
                    sounds.play_success()
                    self.show_message(tr('msg.correct'), GREEN)
                else:
                    self.failed_countries.append(self.current_country)
                    sounds.play_error()
                    abbrs = country_obj.abbreviations
                    msg = tr('msg.wrong_country', answer=self.current_country)
                    if abbrs:
                        msg += f" (abreviaturas: {', '.join(abbrs)})"
                    self.show_message(msg, RED)
                self.select_new_country()
        else:
            if country_obj.check_name_match(user_input):
                self.score += 1
                self._save_progress()
                trigger_success_flash()  # Efecto verde sutil
                sounds.play_success()
                user_input_lower = user_input.lower()
                if user_input_lower in [abbr.lower() for abbr in country_obj.abbreviations]:
                    self.show_message(tr('msg.correct_full_name', country=self.current_country), GREEN)
                else:
                    # Cualquier variante (sin tildes, sin espacios, abreviada) se considera correcto
                    self.show_message(tr('msg.correct'), GREEN)
                self.select_new_country()
            else:
                self.failed_countries.append(self.current_country)
                sounds.play_error()
                abreviaturas = country_obj.abbreviations
                mensaje_error = tr('msg.wrong_country', answer=self.current_country)
                if abreviaturas:
                    mensaje_error += f" (abreviaturas: {', '.join(abreviaturas)})"
                self.show_message(mensaje_error, RED)
                self.select_new_country()

    def auto_check_current(self):
        """Chequea automáticamente si lo escrito ya coincide con la respuesta correcta.
        No marca errores; solo valida éxitos para mantener fluidez."""
        if not self.current_country:
            return
        texto = self.input_text.strip()
        if not texto:
            return
        country_obj = data_module.COUNTRIES[self.current_country]
        if self.game_mode == "capitals":
            if self.quiz_type == "country":
                if are_strings_similar(texto, country_obj.capital):
                    self.score += 1
                    self._save_progress()
                    self.show_message(tr('msg.correct'), GREEN)
                    self.select_new_country()
            elif self.quiz_type == "capital":
                if country_obj.check_name_match(texto):
                    self.score += 1
                    self._save_progress()
                    texto_lower = texto.lower()
                    if texto_lower in [a.lower() for a in country_obj.abbreviations]:
                        self.show_message(tr('msg.correct_full_name', country=self.current_country), GREEN)
                    else:
                        self.show_message(tr('msg.correct'), GREEN)
                    self.select_new_country()
        else:
            if country_obj.check_name_match(texto):
                self.score += 1
                self._save_progress()
                texto_lower = texto.lower()
                if texto_lower in [a.lower() for a in country_obj.abbreviations]:
                    self.show_message(tr('msg.correct_full_name', country=self.current_country), GREEN)
                else:
                    self.show_message(tr('msg.correct'), GREEN)
                self.select_new_country()

    def update(self):
        # Actualizar tiempo global para animaciones
        update_global_time(1/60)
        
        # Actualizar sistema de confetti
        update_confetti()
        
        # Actualizar animaciones de botones
        self.back_button.update()
        self.skip_button.update()
        self.global_button.update()
        self.continent_button.update()
        self.flags_button.update()
        self.capitals_button.update()
        self.by_country_button.update()
        self.by_capital_button.update()
        for btn in self.continent_buttons:
            btn.update()
        
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                self.message = ""
                self._message_surface = None

    def draw(self):
        width = self.screen.get_width()
        height = self.screen.get_height()
        t = get_global_time()
        
        # Fondo animado con estrellas
        draw_animated_background(self.screen)

        # Botón volver
        self.back_button.rect = pygame.Rect(20, 20, int(width * 0.08), int(height * 0.05))
        self.back_button.draw(self.screen)

        if self.region_mode is None:
            button_width = int(width * 0.25)
            button_height = int(height * 0.09)
            spacing = int(height * 0.04)
            center_x = (width - button_width) // 2
            start_y = height // 2 - button_height - spacing // 2
            self.global_button.rect = pygame.Rect(center_x, start_y - button_height - spacing, button_width, button_height)
            self.continent_button.rect = pygame.Rect(center_x, start_y, button_width, button_height)
            self.global_button.draw(self.screen)
            self.continent_button.draw(self.screen)
            title = self._render(self.message_font, tr('region.choose_mode'), TEXT_PRIMARY)
            title_rect = title.get_rect(center=(width // 2, start_y - button_height - spacing * 2))
            self.screen.blit(title, title_rect)
        elif self.region_mode == 'continente' and self.selected_continent is None:
            button_width = int(width * 0.25)
            button_height = int(height * 0.09)
            spacing = int(height * 0.04)
            center_x = (width - button_width) // 2
            start_y = height // 2 - (button_height * len(self.continents) + spacing * (len(self.continents) - 1)) // 2
            for i, btn in enumerate(self.continent_buttons):
                btn.rect = pygame.Rect(center_x, start_y + i * (button_height + spacing), button_width, button_height)
                btn.draw(self.screen)
            title = self._render(self.message_font, tr('region.choose_continent'), TEXT_PRIMARY)
            title_rect = title.get_rect(center=(width // 2, start_y - button_height - spacing))
            self.screen.blit(title, title_rect)
        elif not self.game_mode:
            button_width = int(width * 0.25)
            button_height = int(height * 0.09)
            spacing = int(height * 0.04)
            center_x = (width - button_width) // 2
            start_y = height // 2 - button_height - spacing // 2
            self.flags_button.rect = pygame.Rect(center_x, start_y, button_width, button_height)
            self.capitals_button.rect = pygame.Rect(center_x, start_y + button_height + spacing, button_width, button_height)
            self.flags_button.draw(self.screen)
            self.capitals_button.draw(self.screen)
            flags_prog = self._get_mode_progress('flags')
            # Progresos específicos de sub-modos de capitals
            capitals_country = self._get_capitals_sub_progress('country')
            capitals_capital = self._get_capitals_sub_progress('capital')
            if flags_prog:
                txt = self._render(self.small_font, f"{flags_prog[0]}/{flags_prog[1]}", TEXT_SECONDARY)
                rect = txt.get_rect()
                rect.midleft = (self.flags_button.rect.right + int(width * 0.01), self.flags_button.rect.centery)
                self.screen.blit(txt, rect)
            # Mostrar ambos sub-modos si existen (en una misma línea)
            if capitals_country or capitals_capital:
                parts_text = []
                if capitals_country:
                    parts_text.append(f"{tr('capitals.by_country')}: {capitals_country[0]}/{capitals_country[1]}")
                if capitals_capital:
                    parts_text.append(f"{tr('capitals.by_capital')}: {capitals_capital[0]}/{capitals_capital[1]}")
                combined = "  ".join(parts_text)
                txt2 = self._render(self.small_font, combined, TEXT_SECONDARY)
                rect2 = txt2.get_rect()
                rect2.midleft = (self.capitals_button.rect.right + int(width * 0.01), self.capitals_button.rect.centery)
                self.screen.blit(txt2, rect2)
        elif self.game_mode == "capitals" and not self.quiz_type:
            button_width = int(width * 0.25)
            button_height = int(height * 0.09)
            spacing = int(height * 0.04)
            center_x = (width - button_width) // 2
            start_y = height // 2 - button_height - spacing // 2
            self.by_country_button.rect = pygame.Rect(center_x, start_y, button_width, button_height)
            self.by_capital_button.rect = pygame.Rect(center_x, start_y + button_height + spacing, button_width, button_height)
            self.by_country_button.draw(self.screen)
            self.by_capital_button.draw(self.screen)
            # Progreso por sub-modo (a la derecha)
            def get_capitals_sub_progress(sub):
                parts = [self.region_mode or 'global']
                if self.region_mode == 'continente':
                    parts.append(self.selected_continent or '')
                parts.extend(['capitals', sub])
                key = '|'.join(parts)
                state = GameScreen.PERSISTENT_PROGRESS.get(key)
                if state and state.get('score', 0) > 0 and state.get('total', 0) > 0:
                    return state['score'], state['total']
                return None
            prog_country = get_capitals_sub_progress('country')
            prog_capital = get_capitals_sub_progress('capital')
            if prog_country:
                t = self._render(self.small_font, f"{prog_country[0]}/{prog_country[1]}", TEXT_SECONDARY)
                r = t.get_rect()
                r.midleft = (self.by_country_button.rect.right + int(width * 0.01), self.by_country_button.rect.centery)
                self.screen.blit(t, r)
            if prog_capital:
                t2 = self._render(self.small_font, f"{prog_capital[0]}/{prog_capital[1]}", TEXT_SECONDARY)
                r2 = t2.get_rect()
                r2.midleft = (self.by_capital_button.rect.right + int(width * 0.01), self.by_capital_button.rect.centery)
                self.screen.blit(t2, r2)
        else:
            # Puntaje con diseño moderno estilo tarjeta
            self._draw_modern_score(width, height, t)
            
            # Estado final del juego (no hay país actual)
            if self.current_country is None:
                if self.message:
                    # Mensaje final centrado
                    message_surface = self._render(self.message_font, self.message, self.message_color)
                    message_rect = message_surface.get_rect(center=(width // 2, height // 2))
                    self.screen.blit(message_surface, message_rect)
                # Instrucción para volver
                hint = self._render(self.small_font, tr('common.back') + ' (ESC)', TEXT_SECONDARY)
                hint_rect = hint.get_rect(center=(width // 2, height // 2 + 50))
                self.screen.blit(hint, hint_rect)
            elif self.game_mode == "flags" and self.current_country:
                # Bandera con efecto de glow especial según el país
                max_flag_width = int(width * 0.45)
                max_flag_height = int(height * 0.28)
                flag = self.flag_manager.get_scaled_flag(self.current_country, (max_flag_width, max_flag_height))
                if flag:
                    flag_center = (width // 2, height // 2 - int(height * 0.08))
                    # Usar el efecto especial de glow según el país
                    draw_flag_with_glow(
                        self.screen, flag, flag_center, 
                        self.current_country, t, glow_intensity=1.0
                    )

                # Input con estilo moderno y efectos mejorados
                input_width = int(width * 0.38)
                input_height = int(height * 0.08)
                input_x = (width - input_width) // 2
                input_y = int(height * 0.73)
                self.input_rect = pygame.Rect(input_x, input_y, input_width, input_height)
                
                # Glow del input según estado
                input_glow_color = NEON_CYAN if self.input_active else (80, 80, 140)
                glow_intensity = 0.5 if self.input_active else 0.2
                glow_intensity += 0.08 * math.sin(t * 3)
                
                # Glow más ajustado al tamaño del input
                glow_size = 8 if self.input_active else 4
                glow_surf = pygame.Surface(
                    (self.input_rect.width + glow_size * 2, self.input_rect.height + glow_size * 2), 
                    pygame.SRCALPHA
                )
                for i in range(glow_size, 0, -1):
                    alpha = int((i / glow_size) * 50 * glow_intensity)
                    inflated = pygame.Rect(glow_size - i, glow_size - i,
                                          self.input_rect.width + i * 2, self.input_rect.height + i * 2)
                    pygame.draw.rect(glow_surf, (*input_glow_color, alpha), inflated, border_radius=12)
                self.screen.blit(glow_surf, (self.input_rect.x - glow_size, self.input_rect.y - glow_size))
                
                # Fondo del input
                draw_shadow(self.screen, self.input_rect, radius=12)
                draw_rounded_rect(self.screen, BG_CARD, self.input_rect, 12)
                
                # Borde animado RGB uniforme giratorio
                if self.input_active:
                    self._draw_rgb_rotating_border(self.input_rect, t, 2)
                else:
                    pygame.draw.rect(self.screen, (60, 60, 100), self.input_rect, 2, border_radius=12)
                
                original_clip = self.screen.get_clip()
                input_clip_rect = self.input_rect.inflate(-16, -8)
                self.screen.set_clip(input_clip_rect)
                # Highlight si selección total
                if self.selection_all and self.input_text:
                    self.screen.blit(self._get_highlight_surface((input_clip_rect.width, input_clip_rect.height)), input_clip_rect.topleft)
                
                # Texto del input - centrado vertical y horizontalmente si hay poco texto
                text_surface = self.font.render(self.input_text, True, TEXT_PRIMARY)
                text_width = text_surface.get_width()
                text_height = text_surface.get_height()
                y_pos = input_clip_rect.y + (input_clip_rect.height - text_height) // 2
                
                # Centrar horizontalmente si el texto cabe, sino alinear a la izquierda con scroll
                if text_width < input_clip_rect.width - 10:
                    x_pos = input_clip_rect.x + (input_clip_rect.width - text_width) // 2 - self.input_scroll_offset
                else:
                    x_pos = input_clip_rect.x + 5 - self.input_scroll_offset
                
                self.screen.blit(text_surface, (x_pos, y_pos))
                self.screen.set_clip(original_clip)

                # Botón saltear
                skip_x = input_x + (input_width - self.skip_button.rect.width) // 2
                skip_y = input_y + input_height + 20
                self.skip_button.rect.topleft = (skip_x, skip_y)
                self.skip_button.draw(self.screen)

                if self.message and self.message_timer > 0 and self._message_surface is not None:
                    ratio = self.message_timer / max(1, getattr(self, 'message_fade_total', self.message_timer))
                    cutoff = getattr(self, 'message_fade_cutoff', 0.25)
                    alpha_ratio = (ratio / cutoff) if ratio < cutoff else 1.0
                    base_surface = self._message_surface
                    # Crear copia con alpha sólo si no es opaco
                    if alpha_ratio < 1.0:
                        message_surface = base_surface.convert_alpha()
                        message_surface.set_alpha(int(255 * alpha_ratio))
                    else:
                        message_surface = base_surface
                    msg_y = self.skip_button.rect.bottom + int(height * 0.02)
                    if msg_y + message_surface.get_height() > height - 10:
                        msg_y = height - 10 - message_surface.get_height()
                    message_rect = message_surface.get_rect(center=(width // 2, msg_y + message_surface.get_height() // 2))
                    self.screen.blit(message_surface, message_rect)

                instruction = self._render(self.message_font, tr('input.country_instruction'), TEXT_PRIMARY)
                instruction_rect = instruction.get_rect(center=(width // 2, input_y - int(height * 0.04)))
                self.screen.blit(instruction, instruction_rect)
            elif self.game_mode == "capitals" and self.quiz_type and self.current_country:
                # Input con estilo moderno para capitales
                input_width = int(width * 0.38)
                input_height = int(height * 0.08)
                input_x = (width - input_width) // 2
                input_y = int(height * 0.73)
                self.input_rect = pygame.Rect(input_x, input_y, input_width, input_height)
                
                # Glow del input según estado
                input_glow_color = NEON_PINK if self.input_active else (80, 80, 140)
                glow_intensity = 0.5 if self.input_active else 0.2
                glow_intensity += 0.08 * math.sin(t * 3)
                
                # Glow más ajustado al tamaño del input
                glow_size = 8 if self.input_active else 4
                glow_surf = pygame.Surface(
                    (self.input_rect.width + glow_size * 2, self.input_rect.height + glow_size * 2), 
                    pygame.SRCALPHA
                )
                for i in range(glow_size, 0, -1):
                    alpha = int((i / glow_size) * 50 * glow_intensity)
                    inflated = pygame.Rect(glow_size - i, glow_size - i,
                                          self.input_rect.width + i * 2, self.input_rect.height + i * 2)
                    pygame.draw.rect(glow_surf, (*input_glow_color, alpha), inflated, border_radius=12)
                self.screen.blit(glow_surf, (self.input_rect.x - glow_size, self.input_rect.y - glow_size))
                
                # Fondo del input
                draw_shadow(self.screen, self.input_rect, radius=12)
                draw_rounded_rect(self.screen, BG_CARD, self.input_rect, 12)
                
                # Borde animado RGB uniforme giratorio
                if self.input_active:
                    self._draw_rgb_rotating_border(self.input_rect, t, 2)
                else:
                    pygame.draw.rect(self.screen, (60, 60, 100), self.input_rect, 2, border_radius=12)
                
                original_clip = self.screen.get_clip()
                input_clip_rect = self.input_rect.inflate(-16, -8)
                self.screen.set_clip(input_clip_rect)
                if self.selection_all and self.input_text:
                    self.screen.blit(self._get_highlight_surface((input_clip_rect.width, input_clip_rect.height)), input_clip_rect.topleft)
                
                # Texto centrado vertical y horizontalmente
                text_surface = self.font.render(self.input_text, True, TEXT_PRIMARY)
                text_width = text_surface.get_width()
                text_height = text_surface.get_height()
                y_pos = input_clip_rect.y + (input_clip_rect.height - text_height) // 2
                
                if text_width < input_clip_rect.width - 10:
                    x_pos = input_clip_rect.x + (input_clip_rect.width - text_width) // 2 - self.input_scroll_offset
                else:
                    x_pos = input_clip_rect.x + 5 - self.input_scroll_offset
                
                self.screen.blit(text_surface, (x_pos, y_pos))
                self.screen.set_clip(original_clip)
                if self.quiz_type == "country":
                    prompt_surface = self._get_prompt_surface('country', self.current_country)
                    instruction = tr('input.capital_instruction')
                else:
                    prompt_surface = self._get_prompt_surface('capital', self.current_capital)
                    instruction = tr('input.country_from_capital_instruction')
                prompt_rect = prompt_surface.get_rect(center=(width // 2, int(height * 0.35)))
                self.screen.blit(prompt_surface, prompt_rect)
                instruction_surface = self._render(self.message_font, instruction, TEXT_PRIMARY)
                instruction_rect = instruction_surface.get_rect(center=(width // 2, input_y - int(height * 0.04)))
                self.screen.blit(instruction_surface, instruction_rect)
                if self.message and self.message_timer > 0 and self._message_surface is not None:
                    ratio = self.message_timer / max(1, getattr(self, 'message_fade_total', self.message_timer))
                    cutoff = getattr(self, 'message_fade_cutoff', 0.25)
                    alpha_ratio = (ratio / cutoff) if ratio < cutoff else 1.0
                    base_surface = self._message_surface
                    if alpha_ratio < 1.0:
                        message_surface = base_surface.convert_alpha()
                        message_surface.set_alpha(int(255 * alpha_ratio))
                    else:
                        message_surface = base_surface
                    msg_y = self.input_rect.bottom + int(height * 0.02)
                    if msg_y + message_surface.get_height() > height - 10:
                        msg_y = height - 10 - message_surface.get_height()
                    message_rect = message_surface.get_rect(center=(width // 2, msg_y + message_surface.get_height() // 2))
                    self.screen.blit(message_surface, message_rect)

        # Cronómetro con diseño moderno estilo tarjeta
        if self.game_mode and self.current_country and self.chrono_running:
            self._draw_modern_timer(width, height, t)

        # Debug overlay (dibujar antes del flip)
        if self._debug:
            fps = self.game.clock.get_fps()
            stats = self.flag_manager.stats()
            dbg_lines = [
                f"FPS: {fps:.1f}",
                f"Flags cached: {stats['flags_cached']}",
                f"Scaled cached: {stats['scaled_cached']}",
                f"Round: {self.round_phase}",
                f"Score: {self.score}/{self.total_countries}",
            ]
            y0 = 5
            for line in dbg_lines:
                surf = self._render(self.small_font, line, TEXT_SECONDARY)
                self.screen.blit(surf, (5, y0))
                y0 += surf.get_height() + 2
        
        # Dibujar confetti encima de todo
        draw_confetti(self.screen)
        
        # Actualizar y dibujar flash de pantalla
        update_screen_flash()
        draw_screen_flash(self.screen)
        
        pygame.display.flip()
        self.game.clock.tick(FPS)
