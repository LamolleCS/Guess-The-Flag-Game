import pygame
from utils.constants import *
from utils.ui import Button
from utils.i18n import tr


class SettingsScreen:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen

        # Estado volumen (sincronizado con volumen global si disponible)
        if hasattr(game, 'get_music_volume'):
            try:
                self.volume_value = int(game.get_music_volume() * 100)
            except Exception:
                self.volume_value = 100
        else:
            self.volume_value = 100
        self.volume_dragging = False
        self.volume_selected = False
        self.volume_step = 5

        # Resoluciones y modos
        self.resolutions = RESOLUTIONS
        self.current_resolution_idx = 0
        self.window_modes = WINDOW_MODES  # ids: windowed/fullscreen/borderless
        self.current_mode_idx = 0

        # Botones
        self.back_button = Button(20, 20, 100, 40, tr('common.back'), SMALL_FONT_SIZE)
        self.apply_button = Button(700, 20, 100, 40, tr('settings.apply'), SMALL_FONT_SIZE)
        self.res_left_button = Button(0, 0, 30, 30, "<", SMALL_FONT_SIZE)
        self.res_right_button = Button(0, 0, 30, 30, ">", SMALL_FONT_SIZE)
        self.mode_left_button = Button(0, 0, 30, 30, "<", SMALL_FONT_SIZE)
        self.mode_right_button = Button(0, 0, 30, 30, ">", SMALL_FONT_SIZE)

        # Fuentes
        self.font = pygame.font.Font(None, FONT_SIZE)
        self.small_font = pygame.font.Font(None, SMALL_FONT_SIZE)

        # Flags de cambios
        self.pending_changes = False

        # Geometría inicial slider
        self.volume_rect = pygame.Rect(0, 0, 0, 0)
        self.slider_rect = pygame.Rect(0, 0, 0, 0)
        self.res_y = 0
        self.mode_y = 0

    # -------------------- Eventos --------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.quit()
            if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, 'button', 1) in (4, 5):
                continue  # Ignorar scroll
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.change_screen("menu")
                continue

            if self.back_button.handle_event(event):
                self.game.change_screen("menu")
                continue
            if self.apply_button.handle_event(event) and self.pending_changes:
                self.apply_display_changes()
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.volume_rect.collidepoint(event.pos):
                    self.volume_selected = True
                    self.volume_dragging = True
                    self.update_volume_from_mouse(event.pos[0])
                else:
                    self.volume_selected = False
            elif event.type == pygame.MOUSEBUTTONUP:
                self.volume_dragging = False
            elif event.type == pygame.MOUSEMOTION and self.volume_dragging:
                self.update_volume_from_mouse(event.pos[0])
            elif event.type == pygame.KEYDOWN and self.volume_selected:
                if event.key == pygame.K_LEFT:
                    self.volume_value = max(0, self.volume_value - self.volume_step)
                elif event.key == pygame.K_RIGHT:
                    self.volume_value = min(100, self.volume_value + self.volume_step)
                elif event.key == pygame.K_ESCAPE:
                    self.volume_selected = False
                if hasattr(self.game, 'set_music_volume'):
                    self.game.set_music_volume(self.volume_value / 100.0)

            # Navegación resolución
            if self.res_left_button.handle_event(event):
                self.current_resolution_idx = (self.current_resolution_idx - 1) % len(self.resolutions)
                self.pending_changes = True
            elif self.res_right_button.handle_event(event):
                self.current_resolution_idx = (self.current_resolution_idx + 1) % len(self.resolutions)
                self.pending_changes = True

            # Navegación modo pantalla
            if self.mode_left_button.handle_event(event):
                self.current_mode_idx = (self.current_mode_idx - 1) % len(self.window_modes)
                self.pending_changes = True
            elif self.mode_right_button.handle_event(event):
                self.current_mode_idx = (self.current_mode_idx + 1) % len(self.window_modes)
                self.pending_changes = True

    # -------------------- Lógica --------------------
    def update_volume_from_mouse(self, mouse_x: int):
        relative_x = mouse_x - self.volume_rect.x
        self.volume_value = (relative_x / max(1, self.volume_rect.width)) * 100
        self.volume_value = max(0, min(100, self.volume_value))
        if hasattr(self.game, 'set_music_volume'):
            self.game.set_music_volume(self.volume_value / 100.0)

    def update(self):
        width = self.screen.get_width()
        height = self.screen.get_height()
        # Slider volumen
        self.volume_width = int(width * 0.6)
        self.volume_height = max(20, int(height * 0.025))
        self.volume_x = (width - self.volume_width) // 2
        self.volume_y = int(height * 0.18)
        self.volume_rect = pygame.Rect(self.volume_x, self.volume_y, self.volume_width, self.volume_height)
        self.slider_width = max(10, int(self.volume_width * 0.015))
        slider_center_x = self.volume_x + int(self.volume_width * (self.volume_value / 100))
        self.slider_rect = pygame.Rect(slider_center_x - self.slider_width // 2, self.volume_y - 5, self.slider_width, self.volume_height + 10)

        # Posiciones base de textos de resolución / modo
        self.res_y = int(height * 0.38)
        self.mode_y = int(height * 0.56)

        # Colocar flechas
        res_text = f"{tr('settings.resolution')}: {self.resolutions[self.current_resolution_idx][0]}x{self.resolutions[self.current_resolution_idx][1]}"
        res_label = self.font.render(res_text, True, BLACK)
        res_rect = res_label.get_rect(center=(width//2, self.res_y + 15))
        flecha_sep = 60
        self.res_left_button.rect.topleft = (res_rect.left - flecha_sep, self.res_y)
        self.res_right_button.rect.topleft = (res_rect.right + flecha_sep - self.res_right_button.rect.width, self.res_y)

        mode_key = self.window_modes[self.current_mode_idx]
        mode_label_txt = tr(f'window.mode.{mode_key}')
        mode_text = f"{tr('settings.screen_mode')}: {mode_label_txt}"
        mode_label = self.font.render(mode_text, True, BLACK)
        mode_rect = mode_label.get_rect(center=(width//2, self.mode_y + 15))
        self.mode_left_button.rect.topleft = (mode_rect.left - flecha_sep, self.mode_y)
        self.mode_right_button.rect.topleft = (mode_rect.right + flecha_sep - self.mode_right_button.rect.width, self.mode_y)

        self.apply_button.is_visible = self.pending_changes

    def apply_display_changes(self):
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

    # -------------------- Dibujo --------------------
    def draw(self):
        width = self.screen.get_width()
        height = self.screen.get_height()
        self.screen.fill(WHITE)

        # Botones superiores
        self.back_button.draw(self.screen)
        if self.pending_changes:
            self.apply_button.draw(self.screen)

        # Título
        title = self.font.render(tr('settings.title'), True, BLACK)
        title_rect = title.get_rect(centerx=width//2, y=int(height*0.06))
        self.screen.blit(title, title_rect)

        # Volumen
        volume_label = self.font.render(f"{tr('settings.volume')}: {int(self.volume_value)}%", True, BLACK)
        self.screen.blit(volume_label, (self.volume_x, self.volume_y - int(self.volume_height*2)))
        pygame.draw.rect(self.screen, BLACK, self.volume_rect, 2)
        filled_rect = pygame.Rect(
            self.volume_x,
            self.volume_y,
            int(self.volume_width * (self.volume_value / 100)),
            self.volume_height
        )
        pygame.draw.rect(self.screen, BLACK, filled_rect)
        slider_color = GRAY if self.volume_selected else BLACK
        pygame.draw.rect(self.screen, slider_color, self.slider_rect)
        if self.volume_selected:
            selected_rect = self.volume_rect.inflate(4, 4)
            pygame.draw.rect(self.screen, GRAY, selected_rect, 2)

        # Resolución
        res_text = f"{tr('settings.resolution')}: {self.resolutions[self.current_resolution_idx][0]}x{self.resolutions[self.current_resolution_idx][1]}"
        res_label = self.font.render(res_text, True, BLACK)
        res_rect = res_label.get_rect(center=(width//2, self.res_y + 15))
        self.screen.blit(res_label, res_rect)
        self.res_left_button.draw(self.screen)
        self.res_right_button.draw(self.screen)

        # Modo pantalla
        mode_key = self.window_modes[self.current_mode_idx]
        mode_label_txt = tr(f'window.mode.{mode_key}')
        mode_text = f"{tr('settings.screen_mode')}: {mode_label_txt}"
        mode_label = self.font.render(mode_text, True, BLACK)
        mode_rect = mode_label.get_rect(center=(width//2, self.mode_y + 15))
        self.screen.blit(mode_label, mode_rect)
        self.mode_left_button.draw(self.screen)
        self.mode_right_button.draw(self.screen)

        # Hint aplicar
        if self.pending_changes:
            hint_text = tr('settings.apply_hint', apply=tr('settings.apply'))
            hint_label = self.small_font.render(hint_text, True, GRAY)
            hint_rect = hint_label.get_rect(center=(width//2, int(height*0.92)))
            self.screen.blit(hint_label, hint_rect)

    def refresh_texts(self):
        self.back_button.text = tr('common.back')
        self.apply_button.text = tr('settings.apply')
