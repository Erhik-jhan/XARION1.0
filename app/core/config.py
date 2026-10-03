# app/core/config.py

import os
from pathlib import Path

class Config:
    """
    Configuración global de XARION-1.0.
    Define rutas base, parámetros de renderizado y ajustes generales.
    """

    # --- Información del proyecto ---
    PROJECT_NAME = "XARION"
    VERSION = "1.0"

    # --- Rutas base ---
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    ASSETS_DIR = BASE_DIR / "assets"
    CONFIG_DIR = BASE_DIR / "config"
    OUTPUT_DIR = BASE_DIR / "output"
    DOCS_DIR = BASE_DIR / "docs"
    TESTS_DIR = BASE_DIR / "tests"
    SCRIPTS_DIR = BASE_DIR / "scripts"

    # --- Subrutas de assets ---
    AVATAR_DIR = ASSETS_DIR / "avatar"
    VOICES_DIR = ASSETS_DIR / "voices"
    ANIMATIONS_DIR = ASSETS_DIR / "animations"
    SOUNDS_DIR = ASSETS_DIR / "sounds"

    # --- Archivos de configuración ---
    SETTINGS_FILE = CONFIG_DIR / "settings.json"
    STATE_FILE = CONFIG_DIR / "state.json"

    # --- Parámetros de renderizado ---
    FPS = 30
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    BACKGROUND_COLOR = (0, 0, 0, 255)

    # --- Parámetros de audio ---
    SAMPLE_RATE = 22050
    AUDIO_CHANNELS = 1
    AUDIO_CHUNK_SIZE = 1024

    # --- Parámetros de movimiento ---
    BLINK_INTERVAL_MIN = 2.0
    BLINK_INTERVAL_MAX = 6.0
    SMOOTHING_FACTOR = 0.15
    IDLE_MOTION_AMPLITUDE = 0.02

    # --- Parámetros de grabación ---
    VIDEO_CODEC = "mp4v"
    VIDEO_EXTENSION = ".mp4"

    @classmethod
    def ensure_directories(cls):
        """Crea los directorios necesarios si no existen."""
        for directory in [
            cls.OUTPUT_DIR,
            cls.CONFIG_DIR,
            cls.AVATAR_DIR,
            cls.VOICES_DIR,
            cls.ANIMATIONS_DIR,
            cls.SOUNDS_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def to_dict(cls):
        """Devuelve la configuración como diccionario."""
        return {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(cls).items()
            if not key.startswith("_") and not callable(value)
        }