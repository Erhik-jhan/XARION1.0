# app/interface/settings.py

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
from enum import Enum

from app.core.config import Config
from app.core.state import State


# =========================================================
# PERFILES DE CONFIGURACIÓN
# =========================================================

class SettingsProfile(Enum):
    """Perfiles de configuración predefinidos."""
    DEFAULT = "default"
    PERFORMANCE = "performance"     # máximo rendimiento
    QUALITY = "quality"             # máxima calidad
    LOW_END = "low_end"             # equipos modestos
    STREAMING = "streaming"         # para grabación en vivo
    DEBUG = "debug"                 # modo desarrollo


# =========================================================
# ESQUEMA DE CONFIGURACIÓN
# =========================================================

DEFAULT_SETTINGS: Dict[str, Any] = {
    "general": {
        "language": "es",
        "theme": "dark",
        "autosave": True,
        "autosave_interval": 60.0,
    },
    "render": {
        "fps": 30,
        "width": 1280,
        "height": 720,
        "background_color": [0, 0, 0, 255],
        "antialiasing": True,
        "quality": "high",
    },
    "avatar": {
        "default_path": "",
        "default_format": "",
        "scale": 1.0,
        "auto_blink": True,
        "auto_idle": True,
    },
    "audio": {
        "tts_engine": "edge",
        "tts_voice": "es-ES-AlvaroNeural",
        "tts_rate": 1.0,
        "tts_pitch": 1.0,
        "tts_volume": 1.0,
        "sample_rate": 22050,
        "channels": 1,
        "output_format": "wav",
    },
    "motion": {
        "mode": "combined",
        "intensity": 1.0,
        "smoothing": 0.15,
        "idle_enabled": True,
        "voice_reactive": True,
        "rhythm_reactive": True,
    },
    "gestures": {
        "auto_detect": True,
        "default_variant": "base",
        "talking_variant": "normal",
        "question_variant": "neutral",
    },
    "recording": {
        "codec": "mp4v",
        "extension": ".mp4",
        "include_audio": True,
        "fps": 30,
        "resolution": [1280, 720],
    },
    "performance": {
        "max_cpu": 90,
        "max_memory_mb": 2048,
        "multithreading": True,
        "gpu_acceleration": False,
    },
    "debug": {
        "enabled": False,
        "log_level": "info",
        "show_fps": False,
        "show_signals": False,
    },
}


# =========================================================
# PERFILES PREDEFINIDOS
# =========================================================

PROFILE_PRESETS: Dict[SettingsProfile, Dict[str, Any]] = {
    SettingsProfile.PERFORMANCE: {
        "render": {"fps": 60, "quality": "medium", "antialiasing": False},
        "motion": {"smoothing": 0.10, "intensity": 1.2},
        "performance": {"multithreading": True, "gpu_acceleration": True},
    },
    SettingsProfile.QUALITY: {
        "render": {"fps": 30, "quality": "high", "antialiasing": True},
        "motion": {"smoothing": 0.20, "intensity": 1.0},
    },
    SettingsProfile.LOW_END: {
        "render": {"fps": 24, "quality": "low", "antialiasing": False, "resolution": [854, 480]},
        "performance": {"multithreading": False, "gpu_acceleration": False, "max_memory_mb": 1024},
    },
    SettingsProfile.STREAMING: {
        "render": {"fps": 30, "quality": "high"},
        "recording": {"include_audio": True, "fps": 30},
        "performance": {"multithreading": True},
    },
    SettingsProfile.DEBUG: {
        "debug": {"enabled": True, "log_level": "debug", "show_fps": True, "show_signals": True},
    },
}


# =========================================================
# CONTROLADOR DE CONFIGURACIÓN
# =========================================================

class SettingsController:
    """
    Controlador de configuración de XARION-1.0.
    Gestiona la carga, guardado, validación y aplicación de
    ajustes a todos los módulos del sistema, con perfiles
    predefinidos y persistencia en JSON.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.config.ensure_directories()

        # --- Datos ---
        self.settings: Dict[str, Any] = self._deep_copy(DEFAULT_SETTINGS)
        self.settings_path: Path = self.config.SETTINGS_FILE
        self.current_profile: SettingsProfile = SettingsProfile.DEFAULT

        # --- Historial ---
        self.history: List[Dict[str, Any]] = []
        self.max_history: int = 32
        self.dirty: bool = False
        self.last_save_time: float = 0.0
        self.last_load_time: float = 0.0

        # --- Autosave ---
        self.autosave_enabled: bool = True
        self.autosave_interval: float = 60.0
        self.last_autosave: float = 0.0

        # --- Validación ---
        self.validators: Dict[str, Any] = {}

        # --- Estadísticas ---
        self.total_changes: int = 0
        self.total_saves: int = 0
        self.total_loads: int = 0
        self.last_error: Optional[str] = None

    # =====================================================
    # CARGA Y GUARDADO
    # =====================================================

    def load(self, path: Optional[str] = None) -> bool:
        """Carga la configuración desde disco."""
        target = Path(path) if path else self.settings_path

        if not target.exists():
            self.settings = self._deep_copy(DEFAULT_SETTINGS)
            self.last_load_time = time.time()
            return False

        try:
            with open(target, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            merged = self._deep_merge(
                self._deep_copy(DEFAULT_SETTINGS), loaded
            )
            self.settings = merged
            self.settings_path = target
            self.dirty = False
            self.total_loads += 1
            self.last_load_time = time.time()
            return True
        except Exception as e:
            self.last_error = f"Error cargando settings: {e}"
            return False

    def save(self, path: Optional[str] = None) -> bool:
        """Guarda la configuración en disco."""
        target = Path(path) if path else self.settings_path
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            self.dirty = False
            self.total_saves += 1
            self.last_save_time = time.time()
            return True
        except Exception as e:
            self.last_error = f"Error guardando settings: {e}"
            return False

    def reset(self, section: Optional[str] = None):
        """Reinicia toda la configuración o solo una sección."""
        if section is None:
            self.settings = self._deep_copy(DEFAULT_SETTINGS)
        else:
            if section in DEFAULT_SETTINGS:
                self.settings[section] = self._deep_copy(DEFAULT_SETTINGS[section])
        self.dirty = True
        self._push_history("reset", section)

    # =====================================================
    # ACCESO A VALORES
    # =====================================================

    def get(self, path: str, default: Any = None) -> Any:
        """Obtiene un valor usando notación 'section.key.subkey'."""
        parts = path.split(".")
        node = self.settings
        for p in parts:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                return default
        return node

    def set(self, path: str, value: Any) -> bool:
        """Establece un valor usando notación 'section.key.subkey'."""
        parts = path.split(".")
        node = self.settings
        for p in parts[:-1]:
            if p not in node or not isinstance(node[p], dict):
                node[p] = {}
            node = node[p]
        node[parts[-1]] = value
        self.dirty = True
        self.total_changes += 1
        self._push_history("set", {"path": path, "value": value})
        return True

    def update(self, updates: Dict[str, Any]):
        """Aplica múltiples actualizaciones de una vez."""
        for path, value in updates.items():
            self.set(path, value)

    def delete(self, path: str) -> bool:
        """Elimina una clave de la configuración."""
        parts = path.split(".")
        node = self.settings
        for p in parts[:-1]:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                return False
        if isinstance(node, dict) and parts[-1] in node:
            del node[parts[-1]]
            self.dirty = True
            self._push_history("delete", {"path": path})
            return True
        return False

    # =====================================================
    # PERFILES
    # =====================================================

    def apply_profile(self, profile: SettingsProfile):
        """Aplica un perfil predefinido de configuración."""
        self.current_profile = profile
        if profile == SettingsProfile.DEFAULT:
            self.settings = self._deep_copy(DEFAULT_SETTINGS)
        else:
            preset = PROFILE_PRESETS.get(profile)
            if preset:
                self.settings = self._deep_merge(
                    self._deep_copy(DEFAULT_SETTINGS), preset
                )
        self.dirty = True
        self._push_history("apply_profile", {"profile": profile.value})

    def get_current_profile(self) -> SettingsProfile:
        """Devuelve el perfil activo."""
        return self.current_profile

    # =====================================================
    # APLICACIÓN A MÓDULOS
    # =====================================================

    def apply_to_engine(self, engine: Any):
        """Aplica la configuración actual al motor y sus módulos."""
        if engine is None:
            return

        # Config global
        if hasattr(engine, "config"):
            engine.config.FPS = self.get("render.fps", 30)
            engine.config.WINDOW_WIDTH = self.get("render.width", 1280)
            engine.config.WINDOW_HEIGHT = self.get("render.height", 720)
            engine.config.SAMPLE_RATE = self.get("audio.sample_rate", 22050)
            engine.config.AUDIO_CHANNELS = self.get("audio.channels", 1)
            engine.config.SMOOTHING_FACTOR = self.get("motion.smoothing", 0.15)

        # Avatar
        loader = getattr(engine, "avatar_loader", None)
        if loader is not None:
            default_path = self.get("avatar.default_path", "")
            if default_path and hasattr(loader, "load"):
                loader.load(default_path)

        # TTS
        tts = getattr(engine, "audio_tts", None)
        if tts is not None and hasattr(tts, "set_engine"):
            tts.set_engine(self.get("audio.tts_engine", "edge"))
            tts.set_voice(self.get("audio.tts_voice", ""))
            tts.set_rate(self.get("audio.tts_rate", 1.0))
            tts.set_pitch(self.get("audio.tts_pitch", 1.0))
            tts.set_volume(self.get("audio.tts_volume", 1.0))

        # Motion engine
        motion = getattr(engine, "motion_engine", None)
        if motion is not None and hasattr(motion, "set_intensity"):
            motion.set_intensity(self.get("motion.intensity", 1.0))

        # Recording
        state = getattr(engine, "state", None)
        if state is not None:
            state.recording.fps = self.get("recording.fps", 30)
            res = self.get("recording.resolution", [1280, 720])
            if isinstance(res, list) and len(res) == 2:
                state.recording.resolution = tuple(res)

    # =====================================================
    # AUTOSAVE
    # =====================================================

    def update(self, delta: float):
        """Actualiza autosave si está activo."""
        if not self.autosave_enabled or not self.dirty:
            return
        now = time.time()
        if now - self.last_autosave >= self.autosave_interval:
            self.save()
            self.last_autosave = now

    def enable_autosave(self, enabled: bool, interval: Optional[float] = None):
        """Activa o desactiva el autoguardado."""
        self.autosave_enabled = enabled
        if interval is not None:
            self.autosave_interval = max(5.0, interval)

    # =====================================================
    # IMPORT / EXPORT
    # =====================================================

    def export_to(self, path: str) -> bool:
        """Exporta la configuración a un archivo externo."""
        return self.save(path)

    def import_from(self, path: str) -> bool:
        """Importa una configuración desde un archivo externo."""
        return self.load(path)

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_all(self) -> Dict[str, Any]:
        """Devuelve toda la configuración."""
        return self._deep_copy(self.settings)

    def get_section(self, name: str) -> Dict[str, Any]:
        """Devuelve una sección completa."""
        return self._deep_copy(self.settings.get(name, {}))

    def get_history(self) -> List[Dict[str, Any]]:
        """Devuelve el historial de cambios."""
        return list(self.history)

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "path": str(self.settings_path),
            "profile": self.current_profile.value,
            "dirty": self.dirty,
            "autosave": {
                "enabled": self.autosave_enabled,
                "interval": self.autosave_interval,
            },
            "total_changes": self.total_changes,
            "total_saves": self.total_saves,
            "total_loads": self.total_loads,
            "last_save_time": self.last_save_time,
            "last_load_time": self.last_load_time,
            "last_error": self.last_error,
        }

    def get_available_profiles(self) -> List[str]:
        """Lista los perfiles disponibles."""
        return [p.value for p in SettingsProfile]

    # =====================================================
    # UTILIDADES INTERNAS
    # =====================================================

    def _push_history(self, action: str, data: Any):
        self.history.append({
            "action": action,
            "data": data,
            "timestamp": time.time(),
        })
        if len(self.history) > self.max_history:
            self.history.pop(0)

    @staticmethod
    def _deep_copy(obj: Any) -> Any:
        """Copia profunda segura de diccionarios/listas."""
        if isinstance(obj, dict):
            return {k: SettingsController._deep_copy(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [SettingsController._deep_copy(v) for v in obj]
        return obj

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Fusiona dos diccionarios recursivamente."""
        result = SettingsController._deep_copy(base)
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = SettingsController._deep_merge(result[k], v)
            else:
                result[k] = SettingsController._deep_copy(v)
        return result
    