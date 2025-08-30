import pygame
import random
from utils.constants import *
from utils.ui import Button
import utils.data as data_module
from utils.flag_manager import FlagManager
from utils.text_utils import are_strings_similar
from utils.i18n import tr
from utils import fonts


class GameScreen:
    # Almacén persistente en memoria mientras el programa esté activo
    PERSISTENT_PROGRESS = {}

    def __init__(self, game):
        # Referencias básicas
        self.game = game
        self.screen = game.screen

        # Modo / región
        self.game_mode: str | None = None
        self.quiz_type: str | None = None
        self.region_mode: str | None = None
        self.selected_continent: str | None = None

        # Coordenadas base para botones (valores iniciales; se recalculan en draw responsivo)
        center_x = SCREEN_WIDTH // 2 - BUTTON_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 - BUTTON_HEIGHT - BUTTON_SPACING

        # Botones región
        self.global_button = Button(center_x, start_y - BUTTON_HEIGHT - BUTTON_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT, tr('region.global'))
        self.continent_button = Button(center_x, start_y, BUTTON_WIDTH, BUTTON_HEIGHT, tr('region.by_continent'))

        # Botones continentes
        from utils.data import get_all_continents
        self.continent_buttons: list[Button] = []
        self.continents = get_all_continents()
        for i, cont in enumerate(self.continents):
            btn_y = start_y + i * (BUTTON_HEIGHT + BUTTON_SPACING)
            self.continent_buttons.append(Button(center_x, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT, cont))

        # Botones selección de modo
        self.flags_button = Button(center_x, start_y, BUTTON_WIDTH, BUTTON_HEIGHT, tr('mode.flags'))
        self.capitals_button = Button(center_x, start_y + BUTTON_HEIGHT + BUTTON_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT, tr('mode.capitals'))

        # Botón volver
        self.back_button = Button(20, 20, 100, 40, tr('common.back'), SMALL_FONT_SIZE)

        # Botones sub-modo capitales
        self.by_country_button = Button(center_x, start_y, BUTTON_WIDTH, BUTTON_HEIGHT, tr('capitals.by_country'))
        self.by_capital_button = Button(center_x, start_y + BUTTON_HEIGHT + BUTTON_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT, tr('capitals.by_capital'))

        # Saltear
        self.skip_button = Button(0, 0, 120, 40, tr('common.skip'), SMALL_FONT_SIZE)

        # Input
        self.input_text = ""
        self.input_rect = pygame.Rect((SCREEN_WIDTH - 300) // 2, SCREEN_HEIGHT - 100, 300, 40)
        self.input_active = False
        self.font = fonts.main_font()
        self.input_scroll_offset = 0

        # Estado de juego variables dinámicas
        self.flag_manager = FlagManager()
        self.current_country: str | None = None
        self.current_capital: str | None = None
        self.message = ""
        self.message_color = BLACK
        self.message_timer = 0
        self._message_surface = None  # cache superficie mensaje base
        self.score = 0
        self.countries_left: list[str] = []
        self.total_countries = 0
        self.failed_countries: list[str] = []
        self.max_score = 0

        # Selección de texto (CTRL+A)
        self.selection_all = False

        # Fuentes adicionales y repetición de teclas
        self.message_font = fonts.small_font()
        self.small_font = fonts.small_font()
        pygame.key.set_repeat(320, 25)
        self._enter_skip_guard = False
        self._esc_hold_guard = False

        # Cronómetro
        self.chrono_start = None
        self.chrono_elapsed = 0
        self.chrono_running = False
        self.round_phase = 'full'

        # Caches internos
        self._render_cache: dict = {}
        self._highlight_cache: dict = {}
        self._prompt_cache: dict = {}
        self._frame_ticks = 0
        self._debug = False

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
        """Cachea superficies de prompts que combinan un valor dinámico (país/capital)."""
        key = (kind, dynamic_value)
        surf = self._prompt_cache.get(key)
        if surf is None:
            if kind == 'country':
                text = tr('prompt.country', country=dynamic_value)
            elif kind == 'capital':
                text = tr('prompt.capital', capital=dynamic_value)
            else:
                text = dynamic_value  # fallback
            surf = self.font.render(text, True, BLACK)
            self._prompt_cache[key] = surf
        return surf

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
                    self.show_message(tr('msg.correct'), GREEN)
                else:
                    self.failed_countries.append(self.current_country)
                    self.show_message(tr('msg.wrong_capital', answer=country_obj.capital), RED)
                self.select_new_country()
            elif self.quiz_type == "capital":
                correct = country_obj.check_name_match(user_input)
                if correct:
                    self.score += 1
                    self._save_progress()
                    self.show_message(tr('msg.correct'), GREEN)
                else:
                    self.failed_countries.append(self.current_country)
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
                user_input_lower = user_input.lower()
                if user_input_lower in [abbr.lower() for abbr in country_obj.abbreviations]:
                    self.show_message(tr('msg.correct_full_name', country=self.current_country), GREEN)
                else:
                    # Cualquier variante (sin tildes, sin espacios, abreviada) se considera correcto
                    self.show_message(tr('msg.correct'), GREEN)
                self.select_new_country()
            else:
                self.failed_countries.append(self.current_country)
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
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                self.message = ""
                self._message_surface = None

    def draw(self):
        width = self.screen.get_width()
        height = self.screen.get_height()
        self.screen.fill(WHITE)

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
            title = self._render(self.message_font, tr('region.choose_mode'), BLACK)
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
            title = self._render(self.message_font, tr('region.choose_continent'), BLACK)
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
                txt = self._render(self.small_font, f"{flags_prog[0]}/{flags_prog[1]}", BLACK)
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
                txt2 = self._render(self.small_font, combined, BLACK)
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
                t = self._render(self.small_font, f"{prog_country[0]}/{prog_country[1]}", BLACK)
                r = t.get_rect()
                r.midleft = (self.by_country_button.rect.right + int(width * 0.01), self.by_country_button.rect.centery)
                self.screen.blit(t, r)
            if prog_capital:
                t2 = self._render(self.small_font, f"{prog_capital[0]}/{prog_capital[1]}", BLACK)
                r2 = t2.get_rect()
                r2.midleft = (self.by_capital_button.rect.right + int(width * 0.01), self.by_capital_button.rect.centery)
                self.screen.blit(t2, r2)
        else:
            # Puntaje
            score_text = self._render(self.font, f"{tr('label.score')}: {self.score}/{self.total_countries}", BLACK)
            self.screen.blit(score_text, (20, int(height * 0.09)))
            # Estado final del juego (no hay país actual)
            if self.current_country is None:
                if self.message:
                    # Mensaje final centrado
                    message_surface = self._render(self.message_font, self.message, self.message_color)
                    message_rect = message_surface.get_rect(center=(width // 2, height // 2))
                    self.screen.blit(message_surface, message_rect)
                # Instrucción para volver
                hint = self._render(self.small_font, tr('common.back') + ' (ESC)', BLACK)
                hint_rect = hint.get_rect(center=(width // 2, height // 2 + 50))
                self.screen.blit(hint, hint_rect)
            elif self.game_mode == "flags" and self.current_country:
                # Bandera
                max_flag_width = int(width * 0.45)
                max_flag_height = int(height * 0.28)
                flag = self.flag_manager.get_scaled_flag(self.current_country, (max_flag_width, max_flag_height))
                if flag:
                    flag_rect = flag.get_rect()
                    flag_rect.center = (width // 2, height // 2 - int(height * 0.08))
                    self.screen.blit(flag, flag_rect)

                # Input
                input_width = int(width * 0.32)
                input_height = int(height * 0.07)
                input_x = (width - input_width) // 2
                input_y = int(height * 0.75)
                self.input_rect = pygame.Rect(input_x, input_y, input_width, input_height)
                pygame.draw.rect(self.screen, GRAY if self.input_active else BLACK, self.input_rect, 2)
                original_clip = self.screen.get_clip()
                input_clip_rect = self.input_rect.inflate(-10, -10)
                self.screen.set_clip(input_clip_rect)
                # Highlight si selección total
                if self.selection_all and self.input_text:
                    self.screen.blit(self._get_highlight_surface((input_clip_rect.width, input_clip_rect.height)), input_clip_rect.topleft)
                text_surface = self.font.render(self.input_text, True, BLACK)
                y_pos = input_clip_rect.y + (input_clip_rect.height - text_surface.get_height()) // 2
                x_pos = input_clip_rect.x - self.input_scroll_offset
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

                instruction = self._render(self.message_font, tr('input.country_instruction'), BLACK)
                instruction_rect = instruction.get_rect(center=(width // 2, input_y - int(height * 0.04)))
                self.screen.blit(instruction, instruction_rect)
            elif self.game_mode == "capitals" and self.quiz_type and self.current_country:
                input_width = int(width * 0.32)
                input_height = int(height * 0.07)
                input_x = (width - input_width) // 2
                input_y = int(height * 0.75)
                self.input_rect = pygame.Rect(input_x, input_y, input_width, input_height)
                pygame.draw.rect(self.screen, GRAY if self.input_active else BLACK, self.input_rect, 2)
                original_clip = self.screen.get_clip()
                input_clip_rect = self.input_rect.inflate(-10, -10)
                self.screen.set_clip(input_clip_rect)
                if self.selection_all and self.input_text:
                    self.screen.blit(self._get_highlight_surface((input_clip_rect.width, input_clip_rect.height)), input_clip_rect.topleft)
                text_surface = self.font.render(self.input_text, True, BLACK)
                y_pos = input_clip_rect.y + (input_clip_rect.height - text_surface.get_height()) // 2
                x_pos = input_clip_rect.x - self.input_scroll_offset
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
                instruction_surface = self._render(self.message_font, instruction, BLACK)
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

        # Cronómetro
        if self.game_mode and self.current_country and self.chrono_running:
            mins = self.chrono_elapsed // 60
            secs = self.chrono_elapsed % 60
            chrono_text = self.small_font.render(f"{mins:02d} : {secs:02d}", True, BLACK)
            self.screen.blit(chrono_text, (width // 2 - chrono_text.get_width() // 2, 20))

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
                surf = self._render(self.small_font, line, BLACK)
                self.screen.blit(surf, (5, y0))
                y0 += surf.get_height() + 2
        pygame.display.flip()
        self.game.clock.tick(FPS)
