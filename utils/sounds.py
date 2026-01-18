"""Sistema de efectos de sonido.

Genera y reproduce efectos de sonido sintéticos estilo retro/Minecraft.
"""
import pygame
import numpy as np
import os
from typing import Optional, Dict

# Cache de sonidos generados
_sound_cache: Dict[str, pygame.mixer.Sound] = {}
_sounds_enabled: bool = True
_sound_volume: float = 0.5


def init_sounds() -> None:
    """Inicializa el sistema de sonidos."""
    global _sound_cache
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        _generate_all_sounds()
    except Exception as e:
        print(f"[SOUNDS] No se pudo inicializar: {e}")


def set_sound_volume(volume: float) -> None:
    """Establece el volumen de los efectos (0.0 a 1.0)."""
    global _sound_volume
    _sound_volume = max(0.0, min(1.0, volume))


def set_sounds_enabled(enabled: bool) -> None:
    """Habilita o deshabilita los efectos de sonido."""
    global _sounds_enabled
    _sounds_enabled = enabled


def _generate_sound(frequency: float, duration: float, 
                    wave_type: str = 'square', 
                    volume: float = 0.3,
                    fade_out: bool = True) -> Optional[pygame.mixer.Sound]:
    """Genera un sonido sintético.
    
    Args:
        frequency: Frecuencia en Hz.
        duration: Duración en segundos.
        wave_type: Tipo de onda ('sine', 'square', 'triangle', 'sawtooth').
        volume: Volumen base (0.0 a 1.0).
        fade_out: Si aplicar fade out al final.
    
    Returns:
        Objeto Sound de pygame o None si falla.
    """
    try:
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        # Generar forma de onda
        if wave_type == 'sine':
            wave = np.sin(2 * np.pi * frequency * t)
        elif wave_type == 'square':
            wave = np.sign(np.sin(2 * np.pi * frequency * t))
        elif wave_type == 'triangle':
            wave = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
        elif wave_type == 'sawtooth':
            wave = 2 * (t * frequency - np.floor(t * frequency + 0.5))
        else:
            wave = np.sin(2 * np.pi * frequency * t)
        
        # Aplicar envolvente para evitar clicks
        attack = int(0.005 * sample_rate)  # 5ms attack
        release = int(0.02 * sample_rate)  # 20ms release
        
        envelope = np.ones(n_samples)
        envelope[:attack] = np.linspace(0, 1, attack)
        
        if fade_out:
            fade_samples = int(n_samples * 0.3)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        else:
            envelope[-release:] = np.linspace(1, 0, release)
        
        wave = wave * envelope * volume
        
        # Convertir a formato de audio
        wave = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        
        sound = pygame.sndarray.make_sound(stereo)
        return sound
    except Exception as e:
        print(f"[SOUNDS] Error generando sonido: {e}")
        return None


def _generate_hover_sound() -> Optional[pygame.mixer.Sound]:
    """Genera sonido de hover suave estilo Minecraft."""
    try:
        sample_rate = 44100
        duration = 0.05
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        # Tono agudo suave con frecuencia que sube
        freq_start = 800
        freq_end = 1200
        freq = np.linspace(freq_start, freq_end, n_samples)
        
        wave = np.sin(2 * np.pi * freq * t / sample_rate * np.arange(n_samples))
        
        # Envolvente suave
        envelope = np.exp(-t * 30)  # Decay exponencial rápido
        wave = wave * envelope * 0.15
        
        wave = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return _generate_sound(1000, 0.04, 'sine', 0.12, True)


def _generate_click_sound() -> Optional[pygame.mixer.Sound]:
    """Genera sonido de click satisfactorio."""
    try:
        sample_rate = 44100
        duration = 0.08
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        # Click con frecuencia descendente
        freq = 600 * np.exp(-t * 20)
        wave = np.sin(2 * np.pi * freq * t)
        
        # Segundo armónico para más cuerpo
        wave += 0.3 * np.sin(2 * np.pi * freq * 2 * t)
        
        # Envolvente de percusión
        envelope = np.exp(-t * 25)
        wave = wave * envelope * 0.25
        
        wave = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return _generate_sound(500, 0.06, 'square', 0.2, True)


def _generate_success_sound() -> Optional[pygame.mixer.Sound]:
    """Genera sonido de éxito/acierto."""
    try:
        sample_rate = 44100
        duration = 0.2
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        # Dos tonos ascendentes (acorde mayor)
        freq1 = 523  # C5
        freq2 = 659  # E5
        
        # Primera nota
        wave1 = np.sin(2 * np.pi * freq1 * t) * np.exp(-t * 8)
        # Segunda nota con delay
        delay = int(0.08 * sample_rate)
        wave2 = np.zeros(n_samples)
        wave2[delay:] = np.sin(2 * np.pi * freq2 * t[:-delay]) * np.exp(-t[:-delay] * 10)
        
        wave = (wave1 + wave2) * 0.2
        
        wave = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return _generate_sound(700, 0.15, 'sine', 0.2, True)


def _generate_error_sound() -> Optional[pygame.mixer.Sound]:
    """Genera sonido de error/fallo."""
    try:
        sample_rate = 44100
        duration = 0.25
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        # Tono descendente con vibrato
        freq = 350 * np.exp(-t * 3)
        vibrato = 1 + 0.02 * np.sin(2 * np.pi * 15 * t)
        wave = np.sin(2 * np.pi * freq * vibrato * t)
        
        # Añadir algo de ruido para textura
        noise = np.random.randn(n_samples) * 0.05
        wave = wave + noise
        
        envelope = np.exp(-t * 6)
        wave = wave * envelope * 0.2
        
        wave = np.clip(wave * 32767, -32767, 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return _generate_sound(250, 0.2, 'sawtooth', 0.15, True)


def _generate_skip_sound() -> Optional[pygame.mixer.Sound]:
    """Genera sonido de skip/saltar."""
    try:
        sample_rate = 44100
        duration = 0.12
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        # Tono descendente rápido
        freq = 500 * np.exp(-t * 15)
        wave = np.sin(2 * np.pi * freq * t)
        
        # Segundo tono más grave
        wave += 0.5 * np.sin(2 * np.pi * freq * 0.5 * t)
        
        envelope = np.exp(-t * 12)
        wave = wave * envelope * 0.18
        
        wave = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return _generate_sound(400, 0.1, 'square', 0.15, True)


def _generate_all_sounds() -> None:
    """Pre-genera todos los sonidos del juego."""
    global _sound_cache
    
    _sound_cache['hover'] = _generate_hover_sound()
    _sound_cache['click'] = _generate_click_sound()
    _sound_cache['success'] = _generate_success_sound()
    _sound_cache['error'] = _generate_error_sound()
    _sound_cache['skip'] = _generate_skip_sound()


def play_sound(sound_name: str) -> None:
    """Reproduce un efecto de sonido.
    
    Args:
        sound_name: Nombre del sonido ('hover', 'click', 'success', 'error', 'skip').
    """
    if not _sounds_enabled:
        return
    
    sound = _sound_cache.get(sound_name)
    if sound:
        try:
            sound.set_volume(_sound_volume)
            sound.play()
        except Exception:
            pass


# Funciones de conveniencia
def play_hover() -> None:
    """Reproduce sonido de hover."""
    play_sound('hover')


def play_click() -> None:
    """Reproduce sonido de click."""
    play_sound('click')


def play_success() -> None:
    """Reproduce sonido de éxito."""
    play_sound('success')


def play_error() -> None:
    """Reproduce sonido de error."""
    play_sound('error')


def play_skip() -> None:
    """Reproduce sonido de skip."""
    play_sound('skip')
