"""Pantalla del menú principal.

Provee navegación a las diferentes secciones del juego:
jugar, configuración, idioma y salir.
"""
import pygame
import math
import os
import urllib.request

from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, 
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SPACING,
    WHITE, LANG_CODES, TITLE_FONT_SIZE, MENU_TITLE_FONT_SIZE,
    TEXT_PRIMARY, TEXT_SECONDARY, PRIMARY_LIGHT,
    NEON_CYAN, NEON_PINK, NEON_PURPLE, NEON_GREEN, NEON_BLUE, BG_CARD
)
from utils.ui import (
    Button, ConfirmationDialog, DropdownMenu, 
    draw_animated_background, update_global_time, get_global_time,
    hsv_to_rgb, draw_neon_glow, draw_rounded_rect
)
from utils.i18n import tr, set_ui_language, current_language
from utils import fonts


# Mapeo de códigos de idioma a códigos de país para banderas
LANG_TO_FLAG_CODE = {
    'ES': 'uy',  # Uruguay para español
    'EN': 'us',  # Estados Unidos para inglés
    'PT': 'br',  # Brasil para portugués
    'DE': 'de',  # Alemania para alemán
    'IT': 'it',  # Italia para italiano
}


class MenuScreen:
    """Pantalla del menú principal del juego.
    
    Provee acceso a:
    - Iniciar juego
    - Configuración
    - Selección de idioma
    - Salir del juego
    """
    
    def __init__(self, game) -> None:
        """Inicializa la pantalla del menú.
        
        Args:
            game: Referencia a la instancia principal del juego.
        """
        self.game = game
        self.screen = game.screen
        
        # Calcular posiciones iniciales de botones
        center_x = SCREEN_WIDTH // 2 - BUTTON_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 - (BUTTON_HEIGHT * 2 + int(BUTTON_SPACING * 1.5))

        # Crear botones del menú con estilos modernos (sin emojis, usaremos iconos dibujados)
        self.play_button = Button(
            center_x, start_y, 
            BUTTON_WIDTH, BUTTON_HEIGHT, 
            tr('menu.play'),
            style=Button.STYLE_PRIMARY
        )
        self.settings_button = Button(
            center_x, start_y + BUTTON_HEIGHT + BUTTON_SPACING,
            BUTTON_WIDTH, BUTTON_HEIGHT, 
            tr('menu.settings'),
            style=Button.STYLE_SECONDARY
        )
        self.exit_button = Button(
            center_x, start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 2,
            BUTTON_WIDTH, BUTTON_HEIGHT, 
            tr('menu.exit'),
            style=Button.STYLE_DANGER
        )
        
        # Botón de idioma pequeño en esquina inferior izquierda (sin texto, usará bandera)
        self.language_button = Button(
            20, SCREEN_HEIGHT - 60,
            50, 50, 
            "",
            style=Button.STYLE_GHOST
        )

        # Configurar dropdown de idiomas
        self._setup_language_dropdown(center_x, start_y)
        self.show_language_dropdown = False
        self.confirmation_dialog = None
        
        # Fuentes para el título (más grande y destacado)
        self.title_font = fonts.registry.get(MENU_TITLE_FONT_SIZE)
        self.subtitle_font = fonts.registry.get(24)
        
        # Cargar banderas para animación del menú
        self._load_menu_flags()
        
        # Animación de banderas
        self.flag_animation_time = 0.0
        
        # Sistema de globo terráqueo para el fondo
        self._globe_rotation = 0.0
        self._globe_surface = None
        self._init_globe_background()
    
    def _init_globe_background(self) -> None:
        """Inicializa la superficie del globo terráqueo para el fondo."""
        # Crear globo terráqueo grande
        globe_size = max(SCREEN_WIDTH, SCREEN_HEIGHT)
        self._globe_base_size = int(globe_size * 0.7)  # 70% del tamaño de pantalla
    
    def _draw_globe_background(self, surface: pygame.Surface) -> None:
        """Dibuja un globo terráqueo rotatorio y difuminado en el fondo."""
        width = surface.get_width()
        height = surface.get_height()
        t = get_global_time()
        
        # Actualizar rotación lentamente
        rotation_speed = 0.015  # Muy lento para efecto sutil
        self._globe_rotation = (t * rotation_speed * 360) % 360
        
        # Crear superficie del globo con transparencia
        globe_size = int(min(width, height) * 0.85)
        globe_surf = pygame.Surface((globe_size, globe_size), pygame.SRCALPHA)
        
        center = globe_size // 2
        radius = center - 20
        
        # Color base del globo (azul muy oscuro)
        base_color = (15, 25, 45)
        glow_color = (30, 60, 100)
        
        # Dibujar círculo de fondo del globo
        pygame.draw.circle(globe_surf, (*base_color, 40), (center, center), radius)
        
        # Dibujar líneas de latitud (horizontales)
        num_latitudes = 7
        for i in range(num_latitudes):
            lat_offset = (i - num_latitudes // 2) * (radius * 0.9 / (num_latitudes // 2 + 1))
            if abs(lat_offset) < radius * 0.95:
                # Calcular el ancho de la elipse según la latitud
                lat_radius = math.sqrt(radius**2 - lat_offset**2) if abs(lat_offset) < radius else 0
                if lat_radius > 10:
                    alpha = int(25 * (1 - abs(lat_offset) / radius))
                    pygame.draw.ellipse(
                        globe_surf, (*glow_color, alpha),
                        (center - lat_radius, center + lat_offset - 2, lat_radius * 2, 4),
                        1
                    )
        
        # Dibujar líneas de longitud (verticales curvadas) - rotan con el tiempo
        num_longitudes = 8
        for i in range(num_longitudes):
            # Ángulo de cada meridiano, rotando con el tiempo
            angle = (i * 360 / num_longitudes + self._globe_rotation) % 360
            angle_rad = math.radians(angle)
            
            # Solo dibujar meridianos visibles (frente del globo)
            if -90 <= (angle % 360) - 180 <= 90 or angle % 360 < 90 or angle % 360 > 270:
                # Calcular la posición X del meridiano según la rotación
                x_offset = radius * 0.9 * math.sin(angle_rad)
                
                # Profundidad (para efecto 3D)
                depth = math.cos(angle_rad)
                alpha = int(30 * max(0, depth + 0.3))
                
                if alpha > 5:
                    # Dibujar el meridiano como una elipse vertical
                    meridian_width = max(2, int(abs(depth) * 8))
                    pygame.draw.ellipse(
                        globe_surf, (*glow_color, alpha),
                        (center + x_offset - meridian_width // 2, center - radius * 0.9, 
                         meridian_width, radius * 1.8),
                        1
                    )
        
        # Dibujar borde brillante del globo
        for i in range(5, 0, -1):
            alpha = int(15 * (i / 5))
            pygame.draw.circle(globe_surf, (*glow_color, alpha), (center, center), radius + i, 2)
        
        # Dibujar círculo principal del globo
        pygame.draw.circle(globe_surf, (*glow_color, 35), (center, center), radius, 2)
        
        # Aplicar desenfoque (blur) simulado con múltiples capas
        blur_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Posición centrada del globo
        globe_x = (width - globe_size) // 2
        globe_y = (height - globe_size) // 2 + int(height * 0.05)  # Ligeramente abajo del centro
        
        # Dibujar múltiples capas con offsets para simular blur
        blur_offsets = [(0, 0), (-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]
        for ox, oy in blur_offsets:
            blur_surf.blit(globe_surf, (globe_x + ox, globe_y + oy))
        
        # Dibujar en la superficie principal
        surface.blit(blur_surf, (0, 0))
    
    def _setup_language_dropdown(self, center_x: int, start_y: int) -> None:
        """Configura el menú desplegable de idiomas."""
        # Mapeo de etiquetas a códigos (usar constantes)
        self._lang_label_to_code = {
            'Español (Uruguay)': 'ES',
            'English': 'EN',
            'Português': 'PT',
            'Deutsch': 'DE',
            'Italiano': 'IT'
        }
        self._code_to_lang_label = {v: k for k, v in self._lang_label_to_code.items()}
        
        # Dropdown posicionado cerca del botón de idioma (esquina inferior izquierda)
        self.language_dropdown = DropdownMenu(
            20, 
            SCREEN_HEIGHT - 260,  # Arriba del botón de idioma
            180, 40, 
            list(self._lang_label_to_code.keys())
        )
        
        # Establecer idioma actual
        cur_code = current_language()
        if cur_code in self._code_to_lang_label:
            self.language_dropdown.selected_option = self._code_to_lang_label[cur_code]
    
    def _load_menu_flags(self) -> None:
        """Carga las banderas de Alemania y Uruguay para la animación del menú,
        y las banderas pequeñas para el selector de idioma."""
        self.flag_germany = None
        self.flag_uruguay = None
        self.lang_flags = {}  # Banderas pequeñas para selector de idioma
        
        # Determinar directorio de banderas
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        flags_dir = os.path.join(base_dir, 'assets', 'flags')
        os.makedirs(flags_dir, exist_ok=True)
        
        # URLs de banderas grandes para el título (flagcdn.com)
        title_flag_urls = {
            'germany': 'https://flagcdn.com/w160/de.png',
            'uruguay': 'https://flagcdn.com/w160/uy.png'
        }
        
        # Cargar banderas grandes del título
        for name, url in title_flag_urls.items():
            local_path = os.path.join(flags_dir, f"menu_{name}.png")
            
            try:
                if not os.path.exists(local_path):
                    urllib.request.urlretrieve(url, local_path)
                
                if os.path.exists(local_path):
                    flag_surf = pygame.image.load(local_path).convert_alpha()
                    flag_surf = pygame.transform.smoothscale(flag_surf, (80, 53))
                    if name == 'germany':
                        self.flag_germany = flag_surf
                    else:
                        self.flag_uruguay = flag_surf
            except Exception:
                pass
        
        # Cargar banderas pequeñas para el selector de idioma
        for lang_code, flag_code in LANG_TO_FLAG_CODE.items():
            local_path = os.path.join(flags_dir, f"lang_{flag_code}.png")
            url = f'https://flagcdn.com/w80/{flag_code}.png'
            
            try:
                if not os.path.exists(local_path):
                    urllib.request.urlretrieve(url, local_path)
                
                if os.path.exists(local_path):
                    flag_surf = pygame.image.load(local_path).convert_alpha()
                    flag_surf = pygame.transform.smoothscale(flag_surf, (32, 24))
                    self.lang_flags[lang_code] = flag_surf
            except Exception:
                pass
    
    def _draw_icon(self, surface: pygame.Surface, icon_type: str, 
                   center_x: int, center_y: int, size: int = 20, color=None) -> None:
        """Dibuja iconos vectoriales simples."""
        if color is None:
            color = TEXT_PRIMARY
        
        t = get_global_time()
        
        if icon_type == 'globe':
            # Globo terráqueo: círculo con líneas de meridianos
            radius = size // 2
            # Círculo principal
            pygame.draw.circle(surface, color, (center_x, center_y), radius, 2)
            # Ecuador
            pygame.draw.line(surface, color, 
                           (center_x - radius, center_y), 
                           (center_x + radius, center_y), 2)
            # Meridianos curvos (simplificados como elipses)
            ellipse_rect = pygame.Rect(center_x - radius//2, center_y - radius, 
                                       radius, radius * 2)
            pygame.draw.ellipse(surface, color, ellipse_rect, 1)
            
        elif icon_type == 'play':
            # Triángulo de play con globo
            # Círculo de fondo (globo)
            radius = size // 2
            pygame.draw.circle(surface, color, (center_x, center_y), radius, 2)
            # Triángulo de play pequeño
            tri_size = size // 3
            points = [
                (center_x - tri_size//2 + 2, center_y - tri_size),
                (center_x - tri_size//2 + 2, center_y + tri_size),
                (center_x + tri_size, center_y)
            ]
            pygame.draw.polygon(surface, color, points)
            
        elif icon_type == 'settings':
            # Engranaje: círculo con dientes
            radius = size // 2
            inner_radius = radius * 0.5
            # Círculo interior
            pygame.draw.circle(surface, color, (center_x, center_y), int(inner_radius), 2)
            # Dientes del engranaje
            num_teeth = 6
            for i in range(num_teeth):
                angle = (i / num_teeth) * math.pi * 2 + t * 0.5
                x1 = center_x + int(math.cos(angle) * inner_radius * 1.3)
                y1 = center_y + int(math.sin(angle) * inner_radius * 1.3)
                x2 = center_x + int(math.cos(angle) * radius)
                y2 = center_y + int(math.sin(angle) * radius)
                pygame.draw.line(surface, color, (x1, y1), (x2, y2), 3)
                
        elif icon_type == 'exit':
            # Puerta con flecha de salida
            door_width = size * 0.6
            door_height = size * 0.9
            door_x = center_x - door_width // 2
            door_y = center_y - door_height // 2
            # Marco de puerta
            pygame.draw.rect(surface, color, 
                           (int(door_x), int(door_y), int(door_width), int(door_height)), 2)
            # Flecha de salida
            arrow_x = center_x + size // 4
            pygame.draw.line(surface, color, 
                           (arrow_x - 5, center_y), (arrow_x + 5, center_y), 2)
            pygame.draw.line(surface, color,
                           (arrow_x + 2, center_y - 4), (arrow_x + 5, center_y), 2)
            pygame.draw.line(surface, color,
                           (arrow_x + 2, center_y + 4), (arrow_x + 5, center_y), 2)

    def handle_events(self) -> None:
        """Procesa los eventos de entrada del usuario."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.quit()
                return
            
            # Ignorar scroll en el menú
            if event.type == pygame.MOUSEBUTTONDOWN:
                if getattr(event, 'button', 1) in (4, 5):
                    continue
            
            # ESC para cerrar diálogos o volver
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.confirmation_dialog:
                    self.confirmation_dialog = None
                elif self.show_language_dropdown:
                    self.show_language_dropdown = False
                continue
            
            # Manejar diálogo de confirmación
            if self.confirmation_dialog:
                result = self.confirmation_dialog.handle_event(event)
                if result == "yes":
                    self.game.quit()
                elif result == "no":
                    self.confirmation_dialog = None
                continue
            
            # Manejar dropdown de idioma
            if self.show_language_dropdown:
                self._handle_language_dropdown(event)
                continue

            # Manejar botones del menú
            self._handle_menu_buttons(event)
    
    def _handle_language_dropdown(self, event: pygame.event.Event) -> None:
        """Procesa eventos del dropdown de idioma."""
        selected = self.language_dropdown.handle_event(event)
        if selected:
            lang_code = self._lang_label_to_code.get(selected, 'ES')
            old_lang = current_language()
            if lang_code != old_lang:
                set_ui_language(lang_code)
                self._refresh_button_texts()
                # Update window caption with new language
                pygame.display.set_caption(tr('game.title'))
                # Clear game progress since country names change with language
                from screens.game import GameScreen
                GameScreen.PERSISTENT_PROGRESS.clear()
            self.show_language_dropdown = False
            return
        
        # Cerrar si click fuera del dropdown
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.language_dropdown.rect.collidepoint(event.pos):
                self.show_language_dropdown = False
    
    def _handle_menu_buttons(self, event: pygame.event.Event) -> None:
        """Procesa eventos de los botones del menú."""
        if self.play_button.handle_event(event):
            self.game.change_screen("game")
        elif self.settings_button.handle_event(event):
            self.game.change_screen("settings")
        elif self.language_button.handle_event(event):
            self._open_language_dropdown()
        elif self.exit_button.handle_event(event):
            self.confirmation_dialog = ConfirmationDialog(
                self.screen, tr('confirm.exit')
            )
    
    def _open_language_dropdown(self) -> None:
        """Abre el dropdown de idioma."""
        self.show_language_dropdown = True
        fake_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, 
            {'pos': self.language_dropdown.rect.center, 'button': 1}
        )
        self.language_dropdown.handle_event(fake_event)
    
    def _refresh_button_texts(self) -> None:
        """Actualiza los textos de los botones con el idioma actual."""
        self.play_button.text = tr('menu.play')
        self.settings_button.text = tr('menu.settings')
        self.exit_button.text = tr('menu.exit')

    def update(self) -> None:
        """Actualiza el estado de la pantalla."""
        # Actualizar tiempo global para animaciones
        update_global_time(1/60)
        
        # Actualizar animación de banderas
        self.flag_animation_time += 1/60
        
        # Actualizar animaciones de botones
        self.play_button.update()
        self.settings_button.update()
        self.language_button.update()
        self.exit_button.update()

    def _draw_waving_flag(self, surface: pygame.Surface, flag: pygame.Surface, 
                          center_x: int, center_y: int, phase_offset: float = 0) -> None:
        """Dibuja una bandera con efecto de ondulación suave."""
        if flag is None:
            return
            
        t = self.flag_animation_time
        
        flag_width, flag_height = flag.get_size()
        
        # Efecto de flotación vertical suave
        float_offset = math.sin(t * 1.5 + phase_offset) * 6
        
        # Efecto de inclinación suave (como si ondulara)
        angle = math.sin(t * 2 + phase_offset) * 3
        
        # Rotar la bandera ligeramente
        rotated_flag = pygame.transform.rotate(flag, angle)
        
        # Glow suave detrás de la bandera
        glow_size = 8
        glow_surf = pygame.Surface(
            (rotated_flag.get_width() + glow_size * 2, rotated_flag.get_height() + glow_size * 2),
            pygame.SRCALPHA
        )
        
        # Color del glow que cambia suavemente
        glow_hue = (t * 0.15 + phase_offset / (2 * math.pi)) % 1.0
        glow_color = hsv_to_rgb(glow_hue, 0.6, 1.0)
        
        # Dibujar glow
        for i in range(glow_size, 0, -2):
            alpha = int(30 * (i / glow_size))
            glow_rect = pygame.Rect(
                glow_size - i, glow_size - i,
                rotated_flag.get_width() + i * 2, rotated_flag.get_height() + i * 2
            )
            pygame.draw.rect(glow_surf, (*glow_color, alpha), glow_rect, border_radius=4)
        
        # Posicionar
        dest_rect = rotated_flag.get_rect(center=(center_x, center_y + int(float_offset)))
        glow_rect = glow_surf.get_rect(center=dest_rect.center)
        
        # Dibujar glow y bandera
        surface.blit(glow_surf, glow_rect)
        surface.blit(rotated_flag, dest_rect)

    def draw(self) -> None:
        """Dibuja la pantalla del menú con efectos espectaculares."""
        width = self.screen.get_width()
        height = self.screen.get_height()
        t = get_global_time()
        
        # Fondo animado con estrellas
        draw_animated_background(self.screen)
        
        # Globo terráqueo rotatorio difuminado en el fondo
        self._draw_globe_background(self.screen)
        
        # === TÍTULO CON EFECTO NEÓN MEJORADO ===
        title_text = tr('game.title')
        
        # Color del título que cambia suavemente (más saturado)
        title_hue = (t * 0.08) % 1.0
        title_color = hsv_to_rgb(title_hue, 0.4, 1.0)
        
        title_surf = self.title_font.render(title_text, True, title_color)
        title_rect = title_surf.get_rect(centerx=width // 2, y=int(height * 0.06))
        
        # Glow del título más intenso
        glow_intensity = 0.7 + math.sin(t * 2) * 0.2
        for i in range(4):
            glow_color = hsv_to_rgb((title_hue + 0.08 * i) % 1.0, 0.9, 1.0)
            glow_surf = self.title_font.render(title_text, True, glow_color)
            glow_surf.set_alpha(int(50 * glow_intensity))
            offset = (4 - i) * 3
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                self.screen.blit(glow_surf, (title_rect.x + dx, title_rect.y + dy))
        
        self.screen.blit(title_surf, title_rect)
        
        # === BANDERAS ANIMADAS A LOS LADOS DEL TÍTULO ===
        flag_y = title_rect.centery
        flag_margin = 60  # Distancia desde el título
        
        # Bandera de Alemania (izquierda)
        if self.flag_germany:
            flag_x_left = title_rect.left - flag_margin - 40
            self._draw_waving_flag(self.screen, self.flag_germany, flag_x_left, flag_y, 0)
        
        # Bandera de Uruguay (derecha)
        if self.flag_uruguay:
            flag_x_right = title_rect.right + flag_margin + 40
            self._draw_waving_flag(self.screen, self.flag_uruguay, flag_x_right, flag_y, math.pi)
        
        # Subtítulo
        subtitle_text = tr('game.subtitle')
        subtitle_surf = self.subtitle_font.render(subtitle_text, True, TEXT_SECONDARY)
        subtitle_rect = subtitle_surf.get_rect(centerx=width // 2, y=title_rect.bottom + 15)
        self.screen.blit(subtitle_surf, subtitle_rect)
        
        # Línea decorativa animada RGB
        line_y = subtitle_rect.bottom + 25
        line_width = int(width * 0.4)
        line_start_x = width // 2 - line_width // 2
        
        # Dibujar línea con gradiente RGB
        for x in range(line_width):
            hue = (t * 0.3 + x / line_width) % 1.0
            color = hsv_to_rgb(hue, 0.8, 1.0)
            # Línea principal más gruesa
            pygame.draw.line(
                self.screen, color,
                (line_start_x + x, line_y),
                (line_start_x + x, line_y + 3)
            )
        
        # Glow de la línea
        line_rect = pygame.Rect(line_start_x, line_y - 5, line_width, 14)
        glow_surf = pygame.Surface((line_rect.width, line_rect.height), pygame.SRCALPHA)
        for i in range(6, 0, -1):
            alpha = int(25 * (i / 6) * glow_intensity)
            pygame.draw.rect(glow_surf, (*NEON_CYAN, alpha), 
                           pygame.Rect(0, 7 - i, line_rect.width, i * 2))
        self.screen.blit(glow_surf, line_rect.topleft)

        # Calcular posiciones responsivas para botones (ahora son 3 principales)
        button_width = int(width * 0.30)
        button_height = int(height * 0.09)
        spacing = int(height * 0.04)
        center_x = (width - button_width) // 2
        start_y = int(height * 0.40)

        # Actualizar posiciones de botones
        self._update_button_positions(
            center_x, start_y, button_width, button_height, spacing
        )

        # Dibujar botones principales (sin iconos)
        self.play_button.draw(self.screen)
        self.settings_button.draw(self.screen)
        self.exit_button.draw(self.screen)
        
        # Botón de idioma pequeño (esquina inferior izquierda)
        lang_btn_size = 50
        self.language_button.rect = pygame.Rect(20, height - lang_btn_size - 15, lang_btn_size, lang_btn_size)
        if not self.show_language_dropdown:
            self.language_button.draw(self.screen)
            # Dibujar bandera del idioma actual o globo si no hay bandera
            cur_lang = current_language()
            if cur_lang in self.lang_flags:
                flag = self.lang_flags[cur_lang]
                flag_rect = flag.get_rect(center=self.language_button.rect.center)
                self.screen.blit(flag, flag_rect)
            else:
                # Dibujar globo terráqueo si no hay bandera
                self._draw_icon(self.screen, 'globe',
                              self.language_button.rect.centerx,
                              self.language_button.rect.centery, 22)

        # Dibujar dropdown si está activo
        if self.show_language_dropdown:
            # Posicionar dropdown encima del botón de idioma
            self.language_dropdown.rect = pygame.Rect(
                20, height - lang_btn_size - 15 - 5 * 40 - 10, 
                180, 40
            )
            self.language_dropdown.update_option_rects()
            self.language_dropdown.draw(self.screen)

        # Dibujar diálogo de confirmación si existe
        if self.confirmation_dialog:
            self.confirmation_dialog.draw()
        
        # Footer con versión
        version_text = "v1.0.0"
        version_surf = self.subtitle_font.render(version_text, True, TEXT_SECONDARY)
        version_rect = version_surf.get_rect(bottomright=(width - 15, height - 10))
        self.screen.blit(version_surf, version_rect)
    
    def _update_button_positions(
        self, 
        center_x: int, 
        start_y: int, 
        button_width: int, 
        button_height: int, 
        spacing: int
    ) -> None:
        """Actualiza las posiciones de los botones para responsive design."""
        self.play_button.rect = pygame.Rect(
            center_x, start_y, button_width, button_height
        )
        self.settings_button.rect = pygame.Rect(
            center_x, start_y + button_height + spacing, 
            button_width, button_height
        )
        self.exit_button.rect = pygame.Rect(
            center_x, start_y + (button_height + spacing) * 2, 
            button_width, button_height
        )
