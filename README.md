# Guess The Flag Game 🎮🏴

Un divertido juego de adivinanza de banderas desarrollado en Python con Pygame. ¡Pon a prueba tus conocimientos de geografía mundial!

## 🎯 Características

- **Interfaz gráfica intuitiva** con múltiples pantallas (menú, juego, configuraciones)
- **Sistema de música** con tracks diferentes para menú y juego
- **Soporte multiidioma** (español, inglés, alemán, italiano, portugués)
- **Control de volumen** y función de silencio (Ctrl+Q)
- **Base de datos extensa** de países y banderas
- **Diseño responsive** y experiencia de usuario fluida

## 🚀 Instalación

### Prerrequisitos
- Python 3.7 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/TU_USUARIO/Guess-The-Flag-Game.git
   cd Guess-The-Flag-Game
   ```

2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecuta el juego:**
   ```bash
   python main.py
   ```

## 🎮 Cómo jugar

1. **Inicia el juego** ejecutando `python main.py`
2. **Navega** por el menú principal usando el mouse
3. **Configura** el idioma y volumen en la pantalla de configuraciones
4. **Comienza** una nueva partida y adivina las banderas que aparecen
5. **Controles de audio:** Usa Ctrl+Q para silenciar/activar la música

## 📁 Estructura del proyecto

```
Guess-The-Flag-Game/
│
├── main.py                 # Archivo principal del juego
├── requirements.txt        # Dependencias del proyecto
├── README.md              # Documentación
├── .gitignore            # Archivos ignorados por Git
│
├── assets/               # Recursos multimedia
│   ├── flags/           # Imágenes de banderas
│   └── music/           # Archivos de audio (opcional)
│
├── screens/             # Pantallas del juego
│   ├── menu.py         # Pantalla del menú principal
│   ├── game.py         # Pantalla del juego
│   └── settings.py     # Pantalla de configuraciones
│
└── utils/              # Utilidades y helpers
    ├── constants.py    # Constantes del juego
    ├── data.py        # Manejo de datos
    ├── flag_manager.py # Gestión de banderas
    ├── fonts.py       # Manejo de fuentes
    ├── i18n.py        # Internacionalización
    ├── text_utils.py  # Utilidades de texto
    ├── ui.py          # Componentes de interfaz
    └── *.csv          # Datos de países en diferentes idiomas
```

## 🛠️ Tecnologías utilizadas

- **Python 3.x**
- **Pygame** - Motor de juego y gráficos
- **CSV** - Almacenamiento de datos de países

## 🌍 Idiomas soportados

- 🇪🇸 Español
- 🇺🇸 Inglés
- 🇩🇪 Alemán
- 🇮🇹 Italiano
- 🇵🇹 Portugués

## 🎵 Audio

El juego incluye soporte para música de fondo:
- Música de menú diferente a la de juego
- Control de volumen integrado
- Función de silencio rápido (Ctrl+Q)

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👨‍💻 Autor

- **Tu Nombre** - [Tu GitHub](https://github.com/TU_USUARIO)

## 🙏 Agradecimientos

- Pygame community por la excelente documentación
- Contribuidores de banderas y datos de países
- Comunidad open source por las herramientas utilizadas

---

¡Diviértete jugando y aprendiendo geografía! 🌍🎯
