import unicodedata
import re

def normalize_text(text):
    """
    Normaliza un texto:
    - Convierte a minúsculas
    - Elimina tildes y caracteres especiales
    - Elimina espacios extra
    - Convierte espacios múltiples en uno solo
    """
    # Convertir a minúsculas
    text = text.lower()
    
    # Normalizar caracteres Unicode (quitar tildes)
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    
    # Eliminar caracteres especiales y espacios extra
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Normalizar espacios
    text = ' '.join(text.split())
    
    return text

def levenshtein_distance(s1, s2):
    """
    Calcula la distancia de Levenshtein entre dos cadenas.
    Esta es la cantidad mínima de operaciones de edición necesarias
    para transformar una cadena en otra.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def are_strings_similar(str1, str2, max_distance=2):
    """Determina si dos strings representan lo mismo tras normalización.

    Reglas:
    1. Igualdad exacta post-normalización.
    2. Si no, aceptar también si al quitar todos los espacios coinciden (permite
       escribir nombres compuestos sin espacios: 'caboverde', 'costarica').
    3. No hay tolerancia de letras diferentes (sin Levenshtein). Diferencias de
       caracteres no espaciales siguen siendo error (ej: 'botsuan' != 'botswana').

    max_distance queda obsoleto (compatibilidad de firma).
    """
    norm1 = normalize_text(str1)
    norm2 = normalize_text(str2)
    if norm1 == norm2:
        return True
    # Comparar ignorando espacios por completo
    if norm1.replace(" ", "") == norm2.replace(" ", ""):
        return True
    return False
