"""Punto de entrada principal del juego Adivina la Bandera.

Este módulo contiene la clase Game que gestiona el ciclo principal,
la navegación entre pantallas y el sistema de audio.
"""
import os
import sys
from typing import Optional

import pygame

from screens.menu import MenuScreen
from screens.settings import SettingsScreen
from screens.game import GameScreen
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from utils import sounds


class Game:
    """Clase principal que gestiona el juego.
    
    Responsabilidades:
    - Inicialización de pygame y la ventana
    - Ciclo principal del juego
    - Navegación entre pantallas
    - Sistema de audio y música
    
    Attributes:
        screen: Superficie principal de renderizado.
        clock: Reloj para control de FPS.
        current_screen: Pantalla actualmente activa.
        running: Flag del ciclo principal.
    """
    
    # Constantes de audio
    MUSIC_START_OFFSET: float = 60.0  # Offset para música de menú
    MUSIC_FADE_MS: int = 2000  # Duración del fade en ms
    
    def __init__(self) -> None:
        """Inicializa el juego y sus componentes."""
        pygame.init()
        self._init_audio()
        self._set_window_icon()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        from utils.i18n import tr
        pygame.display.set_caption(tr('game.title'))
        self.clock = pygame.time.Clock()
        self.current_screen = MenuScreen(self)
        self.running = True
        
        # Estado de pantalla
        self._is_fullscreen: bool = False
        self._windowed_size: tuple = (SCREEN_WIDTH, SCREEN_HEIGHT)

        # Estado de audio
        self._music_volume: float = 0.75
        self._muted: bool = False
        self._pre_mute_volume: float = self._music_volume

        # Rutas de música
        self._music_start_offset = self.MUSIC_START_OFFSET
        self._music_fade_ms = self.MUSIC_FADE_MS
        self._menu_music_path = self._find_menu_music()
        self._game_music_path = self._find_game_music()
        self._current_music_type: str = 'menu'
        self._music_loaded: bool = False

        # Estado de hotkey debug
        self._debug_last_q: bool = False

        # Cargar y reproducir música de menú
        self._load_and_play(
            self._menu_music_path, 
            start_offset=self._music_start_offset, 
            fade_ms=self._music_fade_ms
        )
    
    def _init_audio(self) -> None:
        """Inicializa el sistema de audio."""
        try:
            pygame.mixer.init()
            # Inicializar sistema de efectos de sonido
            sounds.init_sounds()
        except Exception as e:
            print(f"[ADVERTENCIA] No se pudo inicializar el mixer: {e}")

    def _set_window_icon(self) -> None:
        """Establece el icono de la ventana."""
        try:
            icon_path = os.path.join(
                os.path.dirname(__file__), "assets", "flags", "uk_icon.png"
            )
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        except Exception as e:
            print(f"[ADVERTENCIA] No se pudo cargar el icono: {e}")

    # =========================================================================
    # SISTEMA DE MÚSICA
    # =========================================================================
    
    def _load_and_play(
        self, 
        path: str, 
        start_offset: float = 0.0, 
        fade_ms: int = 1000
    ) -> None:
        """Carga y reproduce una pista de música.
        
        Args:
            path: Ruta al archivo de audio.
            start_offset: Segundos donde comenzar la reproducción.
            fade_ms: Duración del fade-in en milisegundos.
        """
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

    def play_menu_music(self) -> None:
        """Cambia a la música del menú."""
        if self._current_music_type == 'menu':
            return
        self._fadeout_music(400)
        self._current_music_type = 'menu'
        self._load_and_play(
            self._menu_music_path, 
            start_offset=self._music_start_offset, 
            fade_ms=self._music_fade_ms
        )

    def play_game_music(self) -> None:
        """Cambia a la música del juego."""
        if self._current_music_type == 'game':
            return
        self._fadeout_music(400)
        self._current_music_type = 'game'
        self._load_and_play(self._game_music_path, start_offset=0.0, fade_ms=1200)
    
    def _fadeout_music(self, duration_ms: int) -> None:
        """Hace fadeout de la música actual."""
        try:
            pygame.mixer.music.fadeout(duration_ms)
        except Exception:
            pass

    def _find_menu_music(self) -> str:
        """Busca el track de música para el menú.
        
        Busca archivos que contengan 'daft', 'around', 'world' en el nombre.
        Prioriza formatos: .ogg > .mp3 > .wav
        
        Returns:
            Ruta al archivo de música o fallback.
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
            self._handle_global_keys()
            self.current_screen.handle_events()
            self.current_screen.update()
            self.current_screen.draw()
            pygame.display.flip()
    
    def _handle_global_keys(self):
        """Maneja teclas globales como F11 y CTRL+SHIFT+M."""
        try:
            keys = pygame.key.get_pressed()
            mods = pygame.key.get_mods()
            
            # F11 para toggle fullscreen
            for event in pygame.event.get(pygame.KEYDOWN):
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                pygame.event.post(event)  # Re-post para que lo procese la pantalla
            
            # CTRL+SHIFT+M para toggle mute
            m_now = keys[pygame.K_m]
            if (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT) and m_now and not self._debug_last_q:
                self.toggle_mute()
                estado = 'MUTE' if self._muted else f"UNMUTE (vol={self._music_volume:.2f})"
                print(f"[DEBUG] CTRL+SHIFT+M -> {estado}")
            self._debug_last_q = m_now
        except Exception:
            pass
    
    def toggle_fullscreen(self):
        """Alterna entre modo ventana y pantalla completa."""
        if self._is_fullscreen:
            # Volver a ventana
            self.screen = pygame.display.set_mode(self._windowed_size)
            self._is_fullscreen = False
        else:
            # Ir a fullscreen 1920x1080
            self.screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
            self._is_fullscreen = True
        
        # Actualizar pantalla actual
        self.current_screen.screen = self.screen

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
