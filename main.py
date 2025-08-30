import os
import sys
import pygame
from screens.menu import MenuScreen
from screens.settings import SettingsScreen
from screens.game import GameScreen
from utils.constants import *


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception as e:
            print("[ADVERTENCIA] No se pudo inicializar el mixer de audio:", e)
        # Icono
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "flags", "uk_icon.png")
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        except Exception as e:
            print("[ADVERTENCIA] No se pudo cargar el icono de la ventana:", e)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Adiviná la Bandera")
        self.clock = pygame.time.Clock()
        self.current_screen = MenuScreen(self)
        self.running = True

        # Volumen y estado
        self._music_volume = 1.0
        self._muted = False
        self._pre_mute_volume = self._music_volume

        # Rutas música
        self._music_start_offset = 60.0  # offset menú
        self._music_fade_ms = 2000
        self._menu_music_path = self._find_menu_music()
        self._game_music_path = self._find_game_music()
        self._current_music_type = 'menu'
        self._music_loaded = False

        # Hotkey debug
        self._debug_last_q = False

        # Cargar y reproducir menú
        self._load_and_play(self._menu_music_path, start_offset=self._music_start_offset, fade_ms=self._music_fade_ms)

    # ---------------- Música -----------------
    def _load_and_play(self, path, start_offset=0.0, fade_ms=1000):
        if not os.path.exists(path):
            print(f"[INFO] Música no encontrada: {path}")
            return
        try:
            pygame.mixer.music.load(path)
            if start_offset > 0:
                # Intentar reproducir con offset directo
                try:
                    pygame.mixer.music.play(-1, start=start_offset, fade_ms=fade_ms)
                except Exception:
                    pygame.mixer.music.play(-1, fade_ms=fade_ms)
                    try:
                        pygame.mixer.music.set_pos(start_offset)
                    except Exception:
                        pass
            else:
                pygame.mixer.music.play(-1, fade_ms=fade_ms)
            pygame.mixer.music.set_volume(0.0 if self._muted else self._music_volume)
            self._music_loaded = True
        except Exception as e:
            print("[ADVERTENCIA] No se pudo reproducir la pista:", e)

    def play_menu_music(self):
        if self._current_music_type == 'menu':
            return
        try:
            pygame.mixer.music.fadeout(400)
        except Exception:
            pass
        self._current_music_type = 'menu'
        self._load_and_play(self._menu_music_path, start_offset=self._music_start_offset, fade_ms=self._music_fade_ms)

    def play_game_music(self):
        if self._current_music_type == 'game':
            return
        try:
            pygame.mixer.music.fadeout(400)
        except Exception:
            pass
        self._current_music_type = 'game'
        self._load_and_play(self._game_music_path, start_offset=0.0, fade_ms=1200)

    def _find_menu_music(self):
        """Busca el track de menú (Daft Punk - Around The World) en rutas estándar.

        Orden de búsqueda:
          1. Juego/assets/music/
          2. assets/music/ (carpeta raíz del repositorio)
          3. assets/ (directo en raíz, por si el usuario lo dejó suelto)

        Coincidencia flexible: nombre que contenga 'daft', 'around', 'world'.
        Extensiones preferidas: .ogg, luego .mp3, luego .wav.
        Devuelve ruta fallback a Juego/assets/music/menu_theme.ogg si no encuentra coincidencias.
        """
        base_game = os.path.dirname(__file__)  # .../Juego
        repo_root = os.path.abspath(os.path.join(base_game, '..'))
        search_dirs = [
            os.path.join(base_game, 'assets', 'music'),
            os.path.join(repo_root, 'assets', 'music'),
            os.path.join(repo_root, 'assets'),
        ]
        candidates = []
        for d in search_dirs:
            try:
                if not os.path.isdir(d):
                    continue
                for fname in os.listdir(d):
                    lower = fname.lower()
                    norm = ''.join(ch for ch in lower if ch.isalnum())
                    if all(k in norm for k in ('daft', 'around', 'world')):
                        candidates.append(os.path.join(d, fname))
            except Exception:
                continue
        if candidates:
            def score(p):
                ext = os.path.splitext(p)[1].lower()
                if ext == '.ogg':
                    return 0
                if ext == '.mp3':
                    return 1
                if ext == '.wav':
                    return 2
                return 3
            candidates.sort(key=score)
            chosen = candidates[0]
            print(f"[INFO] Música de menú seleccionada: {os.path.relpath(chosen, repo_root)}")
            return chosen
        # Fallback ensure directory exists
        fallback_dir = os.path.join(base_game, 'assets', 'music')
        os.makedirs(fallback_dir, exist_ok=True)
        return os.path.join(fallback_dir, 'menu_theme.ogg')

    def _find_game_music(self):
        """Busca una pista distinta para in-game.

        Estrategia: de los mismos directorios, tomar el primer archivo de audio que NO cumpla simultáneamente con ('daft','around','world').
        Preferencias de extensión: .ogg, .mp3, .wav
        Fallback: game_theme.ogg (se creará directorio si no existe).
        """
        base_game = os.path.dirname(__file__)
        repo_root = os.path.abspath(os.path.join(base_game, '..'))
        search_dirs = [
            os.path.join(base_game, 'assets', 'music'),
            os.path.join(repo_root, 'assets', 'music'),
            os.path.join(repo_root, 'assets'),
        ]
        game_candidates = []
        for d in search_dirs:
            try:
                if not os.path.isdir(d):
                    continue
                for fname in os.listdir(d):
                    lower = fname.lower()
                    ext = os.path.splitext(lower)[1]
                    if ext not in ('.ogg', '.mp3', '.wav'):
                        continue
                    norm = ''.join(ch for ch in lower if ch.isalnum())
                    # Excluir la de menú (contiene las tres palabras)
                    if all(k in norm for k in ('daft', 'around', 'world')):
                        continue
                    game_candidates.append(os.path.join(d, fname))
            except Exception:
                continue
        if game_candidates:
            def score(p):
                ext = os.path.splitext(p)[1].lower()
                if ext == '.ogg':
                    return 0
                if ext == '.mp3':
                    return 1
                if ext == '.wav':
                    return 2
                return 3
            game_candidates.sort(key=score)
            return game_candidates[0]
        fallback_dir = os.path.join(base_game, 'assets', 'music')
        os.makedirs(fallback_dir, exist_ok=True)
        return os.path.join(fallback_dir, 'game_theme.ogg')

    def stop_music(self):
        try:
            pygame.mixer.music.fadeout(400)
        except Exception:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def set_music_volume(self, value_0_to_1: float):
        self._music_volume = max(0.0, min(1.0, value_0_to_1))
        if self._muted:
            self._pre_mute_volume = self._music_volume
            return
        try:
            pygame.mixer.music.set_volume(self._music_volume)
        except Exception:
            pass

    def get_music_volume(self) -> float:
        return self._music_volume

    def toggle_mute(self):
        if not self._muted:
            self._pre_mute_volume = self._music_volume
            try:
                pygame.mixer.music.set_volume(0.0)
            except Exception:
                pass
            self._muted = True
        else:
            self._muted = False
            try:
                pygame.mixer.music.set_volume(self._pre_mute_volume)
            except Exception:
                pass

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.current_screen.handle_events()
            self.current_screen.update()
            self.current_screen.draw()
            pygame.display.flip()
            # Hotkey debug CTRL+Q toggle mute
            try:
                mods = pygame.key.get_mods()
                q_now = pygame.key.get_pressed()[pygame.K_q]
                if (mods & pygame.KMOD_CTRL) and q_now and not self._debug_last_q:
                    self.toggle_mute()
                    estado = 'MUTE' if self._muted else f"UNMUTE (vol={self._music_volume:.2f})"
                    print(f"[DEBUG] CTRL+Q -> {estado}")
                self._debug_last_q = q_now
            except Exception:
                pass

    def change_screen(self, screen_name, **kwargs):
        if screen_name == "menu":
            self.current_screen = MenuScreen(self)
            self.play_menu_music()
        elif screen_name == "settings":
            self.current_screen = SettingsScreen(self)
            self.play_menu_music()
        elif screen_name == "game":
            self.current_screen = GameScreen(self, **kwargs)
            # Mantener música de menú hasta que realmente comience la partida (start_new_game)
        
    def quit(self):
        self.running = False
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
