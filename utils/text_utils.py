"""Utilidades para procesamiento y comparación de texto.

Incluye normalización de texto, eliminación de acentos,
y algoritmos de comparación de strings.
"""
import re
import unicodedata
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=1024)
def normalize_text(text: str) -> str:
    """Normaliza un texto para comparaciones.
    
    Operaciones:
    - Convierte a minúsculas
    - Elimina tildes y diacríticos
    - Elimina caracteres especiales
    - Normaliza espacios múltiples
    
    Args:
        text: Texto a normalizar.
        
    Returns:
        Texto normalizado.
        
    Example:
        >>> normalize_text("República Democrática")
        'republica democratica'
    """
    # Convertir a minúsculas
    text = text.lower()
    
    # Normalizar caracteres Unicode (quitar tildes)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')
    
    # Eliminar caracteres especiales excepto letras, números y espacios
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Normalizar espacios múltiples a uno solo
    text = ' '.join(text.split())
    
    return text


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calcula la distancia de Levenshtein entre dos cadenas.
    
    La distancia de Levenshtein es el número mínimo de operaciones
    de edición (inserción, eliminación, sustitución) necesarias
    para transformar una cadena en otra.
    
    Args:
        s1: Primera cadena.
        s2: Segunda cadena.
        
    Returns:
        Número mínimo de ediciones necesarias.
        
    Example:
        >>> levenshtein_distance("kitten", "sitting")
        3
    """
    # Optimización: trabajar con la cadena más corta primero
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    # Usar solo dos filas para optimizar memoria
    previous_row = list(range(len(s2) + 1))
    
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Costos de cada operación
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def are_strings_similar(str1: str, str2: str, max_distance: int = 2) -> bool:
    """Determina si dos strings representan lo mismo tras normalización.
    
    Reglas de comparación:
    1. Igualdad exacta post-normalización
    2. Igualdad ignorando todos los espacios (permite escribir
       nombres compuestos sin espacios: 'caboverde', 'costarica')
    
    Args:
        str1: Primer string a comparar.
        str2: Segundo string a comparar.
        max_distance: Parámetro obsoleto (mantenido por compatibilidad).
        
    Returns:
        True si los strings se consideran equivalentes.
        
    Example:
        >>> are_strings_similar("Costa Rica", "costarica")
        True
        >>> are_strings_similar("España", "espana")
        True
    """
    norm1 = normalize_text(str1)
    norm2 = normalize_text(str2)
    
    # Comparación directa normalizada
    if norm1 == norm2:
        return True
    
    # Comparación ignorando espacios
    if norm1.replace(' ', '') == norm2.replace(' ', ''):
        return True
    
    return False


def extract_first_word(text: str) -> str:
    """Extrae la primera palabra de un texto.
    
    Args:
        text: Texto del cual extraer.
        
    Returns:
        Primera palabra o string vacío.
    """
    words = text.strip().split()
    return words[0] if words else ''


def truncate_text(text: str, max_length: int, suffix: str = '...') -> str:
    """Trunca un texto a una longitud máxima.
    
    Args:
        text: Texto a truncar.
        max_length: Longitud máxima incluyendo el sufijo.
        suffix: Sufijo a añadir si se trunca.
        
    Returns:
        Texto truncado con sufijo si excede la longitud.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
