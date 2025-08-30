import os
import pygame
import urllib.request
from typing import Dict, Tuple, Optional
import utils.data as data_module


class FlagManager:
    """Administra la carga, descarga y escalado de banderas con caché.

    - Descarga imágenes si no están presentes localmente.
    - Cachea superficies originales y escaladas para evitar trabajo repetido.
    - Provee un placeholder si la bandera no está disponible.
    """

    def __init__(self) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        repo_root_candidate = os.path.abspath(os.path.join(base_dir, '..', 'assets', 'flags'))
        internal_candidate = os.path.join(base_dir, 'assets', 'flags')
        self.flags_dir: str = repo_root_candidate if os.path.isdir(repo_root_candidate) else internal_candidate
        self.flags_cache: Dict[str, pygame.Surface] = {}
        self.scaled_cache: Dict[Tuple[str, int, int], pygame.Surface] = {}
        self.placeholder: Optional[pygame.Surface] = None
        self._ensure_flags_directory()

    def _ensure_flags_directory(self) -> None:
        if not os.path.exists(self.flags_dir):
            os.makedirs(self.flags_dir, exist_ok=True)

    def clear_cache(self) -> None:
        self.flags_cache.clear()
        self.scaled_cache.clear()

    def trim_caches(self, max_flags: int = 300, max_scaled: int = 800) -> None:
        """Recorta las cachés si exceden un tamaño límite (FIFO simple).
        No afecta la lógica del juego; sólo control defensivo de memoria."""
        if len(self.flags_cache) > max_flags:
            # Eliminar los más antiguos según orden de inserción (dict conserva orden)
            exceso = len(self.flags_cache) - max_flags
            for k in list(self.flags_cache.keys())[:exceso]:
                del self.flags_cache[k]
        if len(self.scaled_cache) > max_scaled:
            exceso = len(self.scaled_cache) - max_scaled
            for k in list(self.scaled_cache.keys())[:exceso]:
                del self.scaled_cache[k]

    def stats(self) -> dict:
        """Devuelve métricas simples de caché para debug overlay."""
        return {
            'flags_cached': len(self.flags_cache),
            'scaled_cached': len(self.scaled_cache),
        }

    def verify_all_flags_present(self) -> dict:
        """Verifica qué banderas faltan en disco sin descargarlas (si todavía no fueron solicitadas).
        Retorna dict con listas 'missing' y 'present'."""
        present, missing = [], []
        for name, country in data_module.COUNTRIES.items():
            iso = country.iso_code.lower()
            path = os.path.join(self.flags_dir, f"{iso}.png")
            (present if os.path.exists(path) else missing).append(name)
        return {'present': present, 'missing': missing}

    def _download_flag(self, country_name: str) -> Optional[str]:
        country = data_module.COUNTRIES.get(country_name)
        if not country:
            return None
        iso = country.iso_code.lower()
        local_path = os.path.join(self.flags_dir, f"{iso}.png")
        if os.path.exists(local_path):
            return local_path
        # Descargar
        try:
            urllib.request.urlretrieve(country.flag_url, local_path)
            return local_path
        except Exception as e:
            print(f"[FLAG] Fallo descargando {country_name} ({iso}): {e}")
            return None

    def _get_placeholder(self) -> pygame.Surface:
        if self.placeholder is None:
            surf = pygame.Surface((160, 100), pygame.SRCALPHA)
            surf.fill((210, 210, 210))
            pygame.draw.rect(surf, (120, 120, 120), surf.get_rect(), 2)
            pygame.draw.line(surf, (200, 0, 0), (0, 0), (160, 100), 4)
            pygame.draw.line(surf, (200, 0, 0), (160, 0), (0, 100), 4)
            font = pygame.font.Font(None, 28)
            txt = font.render("NO FLAG", True, (60, 60, 60))
            surf.blit(txt, txt.get_rect(center=surf.get_rect().center))
            self.placeholder = surf
        return self.placeholder

    def get_flag(self, country_name: str) -> pygame.Surface:
        # Cache hit
        if country_name in self.flags_cache:
            return self.flags_cache[country_name]

        path = self._download_flag(country_name)
        if not path or not os.path.exists(path):
            img = self._get_placeholder()
            self.flags_cache[country_name] = img
            return img
        try:
            img = pygame.image.load(path).convert_alpha()
            self.flags_cache[country_name] = img
            return img
        except Exception as e:
            print(f"[FLAG] Error cargando imagen {path}: {e}")
            img = self._get_placeholder()
            self.flags_cache[country_name] = img
            return img

    def get_scaled_flag(self, country_name: str, max_size: Tuple[int, int]) -> Optional[pygame.Surface]:
        # Normalizamos tamaño máximo a enteros para la clave
        mw, mh = max_size
        key = (country_name, int(mw), int(mh))
        cached = self.scaled_cache.get(key)
        if cached:
            return cached
        img = self.get_flag(country_name)
        if not img:
            return None
        ow, oh = img.get_size()
        if ow == 0 or oh == 0:
            result = self._get_placeholder()
            self.scaled_cache[key] = result
            return result
        scale = min(mw / ow, mh / oh)
        nw, nh = int(ow * scale), int(oh * scale)
        scaled = pygame.transform.smoothscale(img, (nw, nh))
        self.scaled_cache[key] = scaled
        return scaled

    def preload_all_flags(self) -> None:
        for name in data_module.COUNTRIES.keys():
            self.get_flag(name)
