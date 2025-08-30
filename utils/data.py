import csv
import os

# Idioma actual (ES por defecto)
CURRENT_LANGUAGE = 'ES'
LANG_FILES = {
    'ES': 'all_countries.csv',
    'EN': 'all_countries_EN.csv',
    'DE': 'all_countries_DE.csv',
    'IT': 'all_countries_IT.csv',
    'PT': 'all_countries_PT.csv',  # Portugués (Brasil)
}

# Activar para diagnosticar coincidencias inesperadas
DEBUG_MATCHING = False  # Desactivado: poner True solo para investigar coincidencias

class Country:
    # Excepción para Santo Tomé y Príncipe en modo bandera: aceptar 'santotomeyprincipe' como nombre válido (cubierto vía normalización)

    def check_name_match(self, answer):
        from utils.text_utils import are_strings_similar, normalize_text
        # Normalización inicial
        from utils.text_utils import normalize_text
        has_spanish_accents = any(c in answer.lower() for c in 'áéíóúüñ')
        if CURRENT_LANGUAGE == 'EN' and has_spanish_accents:
            if DEBUG_MATCHING:
                print(f"[DEBUG] EN rechaza por acentos directos: '{answer}'")
            return False
        # Igualdad / sin espacios directa primero
        if are_strings_similar(answer, self.name):
            if DEBUG_MATCHING and CURRENT_LANGUAGE == 'EN':
                print(f"[DEBUG] Aceptado (igualdad/espacios) '{answer}' como '{self.name}' (EN)")
            return True
        answer_norm = normalize_text(answer)
        # (El chequeo explícito sin espacios ya está cubierto por are_strings_similar)
        # Normalizado base
        a_low = answer_norm
        name_norm = normalize_text(self.name)
        if DEBUG_MATCHING and CURRENT_LANGUAGE == 'EN':
            print(f"[DEBUG] Evaluando '{answer}' -> norm='{a_low}' contra '{self.name}' norm='{name_norm}' (ISO {self.iso_code})")

        # Alias por idioma (sin cruzar idiomas). Se evalúan solo para el idioma activo.
        # Claves: CURRENT_LANGUAGE; dentro ISO -> lista de alias aceptados para ese idioma.
        LANGUAGE_ALIASES = {
            'EN': {
                # Variantes comunes sin guiones o con espacios diferentes
                'TL': ['timor leste', 'timor-leste', 'east timor'],
                'CI': ['ivory coast', 'cote divoire', 'cote d ivoire'],
                'CD': ['dr congo', 'democratic republic of the congo'],
                'CG': ['republic of the congo', 'congo brazzaville'],
                'BO': ['plurinational state of bolivia'],
                'GB': ['uk', 'united kingdom'],
                'US': ['usa', 'united states', 'united states of america'],
                'AE': ['uae', 'united arab emirates'],
                'VA': ['vatican', 'holy see'],
                'KR': ['south korea'],
                'KP': ['north korea'],
                'LA': ['laos'],
                'FM': ['micronesia'],
                'MM': ['burma'],
                'CV': ['cape verde'],
                'SZ': ['swaziland'],
                'CZ': ['czech republic'],
                'MK': ['macedonia'],
                'PS': ['palestinian territories', 'state of palestine'],
            },
            'ES': {
                # ya cubiertas más abajo algunas variantes; aquí añadir ISO-coherentes si necesario
                'US': ['estados unidos', 'eeuu'],
            },
        }
        if CURRENT_LANGUAGE in LANGUAGE_ALIASES:
            iso_aliases = LANGUAGE_ALIASES[CURRENT_LANGUAGE].get(self.iso_code, [])
            norm_aliases = [normalize_text(a).replace(' ', '') for a in iso_aliases]
            if a_low.replace(' ', '') in norm_aliases:
                if DEBUG_MATCHING and CURRENT_LANGUAGE == 'EN':
                    print(f"[DEBUG] Aceptado alias EN '{answer}' para '{self.name}'")
                return True

        # Rechazar frases españolas muy típicas en EN (evitar que se agreguen al futuro como alias por error)
        if CURRENT_LANGUAGE == 'EN':
            spanish_phrases = {'estados unidos', 'reino unido', 'corea del sur', 'corea del norte', 'españa'}
            if a_low in spanish_phrases:
                if DEBUG_MATCHING:
                    print(f"[DEBUG] Rechazado frase ES '{answer}' en EN")
                return False

        # Excepciones solo en español
        if CURRENT_LANGUAGE == 'ES':
            if self.name == 'Bolivia' and a_low in ['la paz', 'sucre']:
                return True
            if self.name == 'Sudáfrica' and a_low in ['pretoria', 'ciudad del cabo', 'bloemfontein']:
                return True
            if self.name == 'Sri Lanka' and a_low in ['sjk', 'kotte', 'sri jayawardenapura kotte']:
                return True
            if self.name == 'Estados Unidos' and a_low in ['washington', 'washington dc', 'washington d c']:
                return True
            if self.name == 'México' and a_low in ['cdmx', 'ciudad de mexico']:
                return True
            if self.name == 'Panamá' and a_low in ['panama', 'ciudad de panama']:
                return True
            if self.name == 'Palestina' and a_low in ['ramallah', 'jerusalen']:
                return True
            if self.name == 'Ciudad del Vaticano' and a_low in ['vaticano', 'ciudad del vaticano']:
                return True

    # No se aceptan nombres de otros idiomas: se elimina lógica cross-language previa.

        # Abreviaturas
        if any(normalize_text(abbr) == answer_norm or normalize_text(abbr).replace(' ', '') == answer_norm.replace(' ', '') for abbr in self.abbreviations):
            if DEBUG_MATCHING and CURRENT_LANGUAGE == 'EN':
                print(f"[DEBUG] Aceptado por abreviatura '{answer}' -> '{self.name}'")
            return True
        if DEBUG_MATCHING and CURRENT_LANGUAGE == 'EN':
            print(f"[DEBUG] NO coincide '{answer}' con '{self.name}' (sin alias/abbr)")
        return False
    def __init__(self, name, capital, continent, iso_code, abbreviations=None):
        self.name = name
        self.capital = capital
        self.continent = continent
        self.iso_code = iso_code
        self.flag_url = f"https://flagcdn.com/w320/{iso_code.lower()}.png"
        self.abbreviations = abbreviations or []

    def __str__(self):
        return f"{self.name} (Capital: {self.capital}, Continente: {self.continent})"



COUNTRIES = {}
CAPITALS = {}
COUNTRIES_BY_CONTINENT = {}

def _abbreviations_for(name: str):
    if CURRENT_LANGUAGE != 'ES':  # Abreviaturas solo definidas para español por ahora
        return []
    mapping = {
        'Estados Unidos': ['usa', 'eeuu'],
        'Reino Unido': ['uk', 'ru'],
        'Países Bajos': ['holanda'],
        'Nueva Zelanda': ['nz'],
        'Papúa Nueva Guinea': ['png'],
        'República Democrática del Congo': ['rdc'],
        'Antigua y Barbuda': ['ab'],
        'Ciudad del Vaticano': ['vaticano'],
        'Santo Tomé y Príncipe': ['santotome', 'stp'],
        'Bosnia y Herzegovina': ['bh'],
        'Corea del Sur': ['cs'],
        'Corea del Norte': ['cn'],
        'Emiratos Árabes Unidos': ['eau', 'uae'],
        'República Centroafricana': ['rc'],
        'Islas Salomón': ['is'],
        'Islas Marshall': ['im'],
    # Guinea-Bisáu (dataset usa guion). Se mantiene variante sin guion por seguridad.
    'Guinea-Bisáu': ['gb'],
    'Guinea Bisáu': ['gb'],
        'Timor Oriental': ['to'],
        'Trinidad y Tobago': ['tt'],
        'Macedonia del Norte': ['mn'],
        'Sudán del Sur': ['ss'],
        'Sri Lanka': ['sl'],
    # Nuevos alias solicitados
    'Catar': ['qatar'],
    'Irak': ['iraq'],
    'El Salvador': ['es'],
    'Costa Rica': ['cr'],
    'San Marino': ['sm'],
    'San Vicente y las Granadinas': ['svg'],
    'Sierra Leona': ['sl'],  # comparte 'sl' con Sri Lanka
    'Burkina Faso': ['bf'],
    'República Dominicana': ['rd'],
    'Guinea Ecuatorial': ['ge'],  # posible confusión con Georgia (sin abreviatura)
    'San Cristóbal y Nieves': ['scn'],
    'Costa de Marfil': ['cdm'],
    'Arabia Saudita': ['as'],
    'Cabo Verde': ['cv'],
    }
    return mapping.get(name, [])

def load_countries_for_language(lang: str):
    global COUNTRIES, CAPITALS, COUNTRIES_BY_CONTINENT, CURRENT_LANGUAGE
    if lang not in LANG_FILES:
        print(f"[ADVERTENCIA] Idioma {lang} no soportado, usando ES")
        lang = 'ES'
    CURRENT_LANGUAGE = lang
    COUNTRIES = {}
    CAPITALS = {}
    COUNTRIES_BY_CONTINENT = {}
    filename = LANG_FILES[lang]
    csv_path = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].startswith('#'):
                    continue
                if len(row) < 4:
                    print(f"[ADVERTENCIA] Fila incompleta en {filename}: {row}")
                    continue
                name, capital, continent, iso_code = row[:4]
                abbrs = _abbreviations_for(name)
                COUNTRIES[name] = Country(name, capital, continent, iso_code, abbrs)
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo de países para idioma {lang}: {filename}")
    # Build derived structures
    CAPITALS = {country.capital: country.name for country in COUNTRIES.values()}
    COUNTRIES_BY_CONTINENT = {}
    for country in COUNTRIES.values():
        if country.continent not in COUNTRIES_BY_CONTINENT:
            COUNTRIES_BY_CONTINENT[country.continent] = []
        COUNTRIES_BY_CONTINENT[country.continent].append(country.name)
    return COUNTRIES

def set_language(lang: str):
    load_countries_for_language(lang)

# Carga inicial español
load_countries_for_language('ES')


def get_country_by_capital(capital):
    """Obtiene el país dado una capital, considerando el idioma actual."""
    c = capital.lower().strip()
    # Excepciones por idioma
    if CURRENT_LANGUAGE == 'ES':
        # Aceptar variantes de Washington para Estados Unidos
        if c in ["washington", "washington dc", "washington d.c."]:
            return "Estados Unidos"
    elif CURRENT_LANGUAGE == 'EN':
        # En inglés aceptar 'Washington' igual (USA dataset tiene United States)
        if c in ["washington", "washington dc", "washington d.c."]:
            return "United States"
    return CAPITALS.get(capital)

def get_capital_by_country(country):
    """Obtiene la capital dado un país"""
    return COUNTRIES.get(country).capital if country in COUNTRIES else None

def get_countries_in_continent(continent):
    """Obtiene la lista de países en un continente"""
    return COUNTRIES_BY_CONTINENT.get(continent, [])

def get_flag_url(country):
    """Obtiene la URL de la bandera de un país"""
    return COUNTRIES.get(country).flag_url if country in COUNTRIES else None

def get_all_continents():
    """Obtiene la lista de todos los continentes"""
    return list(COUNTRIES_BY_CONTINENT.keys())
