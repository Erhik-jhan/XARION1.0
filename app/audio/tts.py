# app/audio/tts.py

import os
import time
import uuid
import subprocess
import importlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from app.core.config import Config
from app.core.state import State


# =========================================================
# MOTORES TTS DISPONIBLES
# =========================================================

class TTSEngine:
    """Motores TTS soportados por XARION-1.0."""
    SYSTEM = "system"         # pyttsx3 / espeak / say
    EDGE = "edge"             # edge-tts (Microsoft)
    PIPER = "piper"           # Piper (local, rápido)
    COQUI = "coqui"           # Coqui TTS (local, neural)
    ELEVENLABS = "elevenlabs" # API online
    CUSTOM = "custom"         # motor personalizado registrado


# =========================================================
# VOCES POR DEFECTO
# =========================================================

DEFAULT_VOICES: Dict[str, Dict[str, str]] = {
    TTSEngine.SYSTEM:     {"es": "spanish", "en": "english", "default": "default"},
    TTSEngine.EDGE:       {"es": "es-ES-AlvaroNeural", "en": "en-US-GuyNeural", "default": "es-ES-AlvaroNeural"},
    TTSEngine.PIPER:      {"es": "es_ES-mls_10246-low", "en": "en_US-lessac-medium", "default": "es_ES-mls_10246-low"},
    TTSEngine.COQUI:      {"es": "tts_models/es/css10/vits", "en": "tts_models/en/ljspeech/vits", "default": "tts_models/es/css10/vits"},
    TTSEngine.ELEVENLABS: {"es": "21m00Tcm4TlvDq8ikWAM", "en": "21m00Tcm4TlvDq8ikWAM", "default": "21m00Tcm4TlvDq8ikWAM"},
}


# =========================================================
# CONTROLADOR TTS
# =========================================================

class TTSController:
    """
    Controlador de síntesis de voz de XARION-1.0.
    Gestiona múltiples motores TTS, caché, voces, idiomas,
    velocidad, tono y exportación a WAV/MP3.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.config.ensure_directories()

        # --- Motor activo ---
        self.engine: str = TTSEngine.EDGE
        self.engine_instance: Any = None
        self.custom_engines: Dict[str, Any] = {}

        # --- Configuración de voz ---
        self.language: str = "es"
        self.voice: str = DEFAULT_VOICES[self.engine].get("es", "default")
        self.rate: float = 1.0
        self.pitch: float = 1.0
        self.volume: float = 1.0

        # --- Salida ---
        self.output_dir: Path = self.config.VOICES_DIR
        self.output_format: str = "wav"

        # --- Caché ---
        self.cache_enabled: bool = True
        self.cache: Dict[str, Dict[str, Any]] = {}

        # --- Estado interno ---
        self.last_result: Optional[Dict[str, Any]] = None
        self.last_text: str = ""
        self.last_error: Optional[str] = None
        self.total_synthesis: int = 0
        self.total_duration: float = 0.0
        self.total_failures: int = 0

        # --- Estadísticas ---
        self.last_synthesis_time: float = 0.0
        self.average_synthesis_time: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el motor TTS seleccionado."""
        try:
            self._load_engine(self.engine)
        except Exception as e:
            self.last_error = f"Error al inicializar TTS: {e}"

    def _load_engine(self, engine: str):
        """Carga el motor TTS solicitado."""
        if engine == TTSEngine.SYSTEM:
            self.engine_instance = self._init_system()
        elif engine == TTSEngine.EDGE:
            self.engine_instance = self._init_edge()
        elif engine == TTSEngine.PIPER:
            self.engine_instance = self._init_piper()
        elif engine == TTSEngine.COQUI:
            self.engine_instance = self._init_coqui()
        elif engine == TTSEngine.ELEVENLABS:
            self.engine_instance = self._init_elevenlabs()
        elif engine in self.custom_engines:
            self.engine_instance = self.custom_engines[engine]
        else:
            raise ValueError(f"Motor TTS desconocido: {engine}")

    # =====================================================
    # INICIALIZADORES DE MOTOR
    # =====================================================

    def _init_system(self) -> Dict[str, Any]:
        """Inicializa el motor TTS del sistema (pyttsx3)."""
        try:
            pyttsx3 = importlib.import_module("pyttsx3")
            engine = pyttsx3.init()
            return {"engine": engine, "type": "system", "ready": True}
        except Exception as e:
            return {"engine": None, "type": "system", "ready": False, "error": str(e)}

    def _init_edge(self) -> Dict[str, Any]:
        """Inicializa edge-tts (Microsoft)."""
        try:
            edge_tts = importlib.import_module("edge_tts")
            return {"module": edge_tts, "type": "edge", "ready": True}
        except Exception as e:
            return {"module": None, "type": "edge", "ready": False, "error": str(e)}

    def _init_piper(self) -> Dict[str, Any]:
        """Inicializa Piper (TTS local)."""
        try:
            piper = importlib.import_module("piper")
            return {"module": piper, "type": "piper", "ready": True}
        except Exception as e:
            return {"module": None, "type": "piper", "ready": False, "error": str(e)}

    def _init_coqui(self) -> Dict[str, Any]:
        """Inicializa Coqui TTS (neural local)."""
        try:
            TTS = importlib.import_module("TTS.api").TTS
            return {"module": TTS, "type": "coqui", "ready": True, "instance": None}
        except Exception as e:
            return {"module": None, "type": "coqui", "ready": False, "error": str(e)}

    def _init_elevenlabs(self) -> Dict[str, Any]:
        """Inicializa el cliente de ElevenLabs (import dinámico seguro)."""
        try:
            module = importlib.import_module("elevenlabs")
        except Exception as e:
            return {
                "module": None,
                "type": "elevenlabs",
                "ready": False,
                "error": f"elevenlabs no instalado: {e}",
            }

        api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        return {
            "module": module,
            "type": "elevenlabs",
            "ready": bool(api_key),
            "api_key": api_key,
        }

    # =====================================================
    # SÍNTESIS PRINCIPAL
    # =====================================================

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sintetiza un texto en audio.
        Devuelve dict con success, path, duration, engine, voice.
        """
        if not text or not text.strip():
            return self._fail("Texto vacío")

        start = time.time()

        if voice:
            self.voice = voice
        if language:
            self.language = language

        cache_key = self._make_cache_key(text, self.voice, self.language)
        if self.cache_enabled and cache_key in self.cache:
            cached = self.cache[cache_key].copy()
            cached["cached"] = True
            self.last_result = cached
            return cached

        output_file = self._resolve_output_path(output_path)

        try:
            result = self._dispatch_synthesis(text, output_file)
        except Exception as e:
            self.total_failures += 1
            return self._fail(f"Excepción en síntesis: {e}")

        elapsed = time.time() - start
        self.last_synthesis_time = elapsed
        self._update_average(elapsed)

        if result and result.get("success"):
            self.total_synthesis += 1
            self.total_duration += result.get("duration", 0.0)
            self.last_text = text
            if self.cache_enabled:
                self.cache[cache_key] = result.copy()
        else:
            self.total_failures += 1

        self.last_result = result
        return result

    def _dispatch_synthesis(self, text: str, output_file: Path) -> Dict[str, Any]:
        """Despacha la síntesis según el motor activo."""
        if self.engine_instance is None:
            return self._fail("Motor TTS no inicializado")

        engine_type = self.engine_instance.get("type", "")

        if engine_type == "system":
            return self._synthesize_system(text, output_file)
        elif engine_type == "edge":
            return self._synthesize_edge(text, output_file)
        elif engine_type == "piper":
            return self._synthesize_piper(text, output_file)
        elif engine_type == "coqui":
            return self._synthesize_coqui(text, output_file)
        elif engine_type == "elevenlabs":
            return self._synthesize_elevenlabs(text, output_file)

        return self._fail(f"Tipo de motor no soportado: {engine_type}")

    # =====================================================
    # MOTORES ESPECÍFICOS
    # =====================================================

    def _synthesize_system(self, text: str, output_file: Path) -> Dict[str, Any]:
        """Síntesis con pyttsx3."""
        engine_data = self.engine_instance
        if not engine_data.get("ready"):
            return self._fail("pyttsx3 no disponible")

        engine = engine_data["engine"]
        try:
            engine.setProperty("rate", int(200 * self.rate))
            engine.setProperty("volume", self.volume)
            engine.save_to_file(text, str(output_file))
            engine.runAndWait()
        except Exception as e:
            return self._fail(f"pyttsx3 error: {e}")

        if not output_file.exists():
            return self._fail("pyttsx3 no generó archivo")

        return self._success(output_file)

    def _synthesize_edge(self, text: str, output_file: Path) -> Dict[str, Any]:
        """Síntesis con edge-tts."""
        edge_tts = self.engine_instance.get("module")
        if edge_tts is None:
            return self._fail("edge-tts no disponible")

        import asyncio

        rate_pct = int((self.rate - 1.0) * 100)
        pitch_pct = int((self.pitch - 1.0) * 50)

        rate_str = f"{'+' if rate_pct >= 0 else ''}{rate_pct}%"
        pitch_str = f"{'+' if pitch_pct >= 0 else ''}{pitch_pct}Hz"

        async def _run():
            communicate = edge_tts.Communicate(
                text, self.voice, rate=rate_str, pitch=pitch_str
            )
            await communicate.save(str(output_file))

        try:
            asyncio.run(_run())
        except Exception as e:
            return self._fail(f"edge-tts error: {e}")

        if not output_file.exists():
            return self._fail("edge-tts no generó archivo")

        return self._success(output_file)

    def _synthesize_piper(self, text: str, output_file: Path) -> Dict[str, Any]:
        """Síntesis con Piper (invoca CLI)."""
        piper_path = os.environ.get("PIPER_BIN", "piper")
        model_path = os.environ.get("PIPER_MODEL", "")

        if not model_path:
            return self._fail("PIPER_MODEL no configurado")

        cmd = [
            piper_path,
            "--model", model_path,
            "--output_file", str(output_file),
        ]

        try:
            proc = subprocess.run(
                cmd, input=text.encode("utf-8"),
                capture_output=True, timeout=60,
            )
            if proc.returncode != 0:
                return self._fail(f"piper error: {proc.stderr.decode()}")
        except Exception as e:
            return self._fail(f"piper excepción: {e}")

        if not output_file.exists():
            return self._fail("piper no generó archivo")

        return self._success(output_file)

    def _synthesize_coqui(self, text: str, output_file: Path) -> Dict[str, Any]:
        """Síntesis con Coqui TTS."""
        TTS = self.engine_instance.get("module")
        if TTS is None:
            return self._fail("Coqui TTS no disponible")

        try:
            if self.engine_instance.get("instance") is None:
                self.engine_instance["instance"] = TTS(model_name=self.voice)
            tts = self.engine_instance["instance"]
            tts.tts_to_file(text=text, file_path=str(output_file))
        except Exception as e:
            return self._fail(f"coqui error: {e}")

        if not output_file.exists():
            return self._fail("coqui no generó archivo")

        return self._success(output_file)

    def _synthesize_elevenlabs(self, text: str, output_file: Path) -> Dict[str, Any]:
        """Síntesis con ElevenLabs (API online, import dinámico seguro)."""
        if not self.engine_instance.get("ready"):
            return self._fail("ElevenLabs no configurado (falta API key o librería)")

        api_key = self.engine_instance.get("api_key", "")

        try:
            # Import dinámico para evitar errores de Pylance si no está instalado
            client_module = importlib.import_module("elevenlabs.client")
            ElevenLabs = getattr(client_module, "ElevenLabs")
            client = ElevenLabs(api_key=api_key)
            audio = client.generate(
                text=text,
                voice=self.voice,
                model="eleven_multilingual_v2",
            )
            with open(output_file, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
        except Exception as e:
            return self._fail(f"elevenlabs error: {e}")

        if not output_file.exists():
            return self._fail("elevenlabs no generó archivo")

        return self._success(output_file)

    # =====================================================
    # CONSTRUCCIÓN DE RESULTADOS
    # =====================================================

    def _success(self, output_file: Path) -> Dict[str, Any]:
        """Construye un resultado exitoso con duración estimada."""
        duration = self._estimate_duration(output_file)
        return {
            "success": True,
            "path": str(output_file),
            "duration": duration,
            "engine": self.engine,
            "voice": self.voice,
            "language": self.language,
            "rate": self.rate,
            "pitch": self.pitch,
            "volume": self.volume,
            "text": self.last_text,
            "timestamp": time.time(),
        }

    def _fail(self, message: str) -> Dict[str, Any]:
        """Construye un resultado de error uniforme."""
        self.last_error = message
        return {
            "success": False,
            "error": message,
            "path": None,
            "duration": 0.0,
            "engine": self.engine,
            "voice": self.voice,
        }

    def _estimate_duration(self, path: Path) -> float:
        """Estima la duración del audio generado."""
        try:
            import wave
            with wave.open(str(path), "rb") as w:
                frames = w.getnframes()
                rate = w.getframerate()
                if rate > 0:
                    return frames / float(rate)
        except Exception:
            pass
        try:
            size = path.stat().st_size
            return max(0.0, (size - 44) / (22050 * 2))
        except Exception:
            return 0.0

    # =====================================================
    # UTILIDADES
    # =====================================================

    def _resolve_output_path(self, output_path: Optional[str]) -> Path:
        """Resuelve la ruta de salida del audio."""
        if output_path:
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            return p

        filename = f"tts_{uuid.uuid4().hex[:10]}.{self.output_format}"
        path = self.output_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _make_cache_key(self, text: str, voice: str, language: str) -> str:
        """Genera una clave de caché única."""
        raw = f"{text}|{voice}|{language}|{self.rate}|{self.pitch}|{self.engine}"
        return str(hash(raw))

    def _update_average(self, elapsed: float):
        """Actualiza el tiempo medio de síntesis."""
        n = max(1, self.total_synthesis)
        self.average_synthesis_time = (
            (self.average_synthesis_time * (n - 1) + elapsed) / n
        )

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def set_engine(self, engine: str, **kwargs):
        """Cambia el motor TTS activo."""
        self.engine = engine
        self.voice = kwargs.get("voice", DEFAULT_VOICES.get(engine, {}).get(self.language, "default"))
        self._load_engine(engine)

    def set_voice(self, voice: str):
        """Cambia la voz activa."""
        self.voice = voice

    def set_language(self, language: str):
        """Cambia el idioma y actualiza la voz por defecto."""
        self.language = language
        default = DEFAULT_VOICES.get(self.engine, {}).get(language)
        if default:
            self.voice = default

    def set_rate(self, rate: float):
        """Ajusta la velocidad (0.5 a 2.0)."""
        self.rate = max(0.5, min(2.0, rate))

    def set_pitch(self, pitch: float):
        """Ajusta el tono (0.5 a 2.0)."""
        self.pitch = max(0.5, min(2.0, pitch))

    def set_volume(self, volume: float):
        """Ajusta el volumen (0.0 a 1.0)."""
        self.volume = max(0.0, min(1.0, volume))

    def register_custom_engine(self, name: str, instance: Any):
        """Registra un motor TTS personalizado."""
        self.custom_engines[name] = {"instance": instance, "type": "custom", "ready": True}

    def enable_cache(self, enabled: bool = True):
        """Activa o desactiva la caché."""
        self.cache_enabled = enabled

    def clear_cache(self):
        """Limpia la caché de síntesis."""
        self.cache.clear()

    def clean_old_files(self, max_age_seconds: float = 3600.0):
        """Elimina archivos TTS antiguos del directorio de salida."""
        now = time.time()
        for file in self.output_dir.glob(f"tts_*.{self.output_format}"):
            try:
                if now - file.stat().st_mtime > max_age_seconds:
                    file.unlink()
            except Exception:
                pass

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_available_engines(self) -> List[str]:
        """Lista los motores disponibles."""
        return [e.value for e in TTSEngine] + list(self.custom_engines.keys())

    def get_available_voices(self) -> Dict[str, str]:
        """Devuelve las voces por defecto del motor activo."""
        return DEFAULT_VOICES.get(self.engine, {}).copy()

    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """Devuelve el último resultado de síntesis."""
        return self.last_result

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "engine": self.engine,
            "engine_ready": bool(self.engine_instance and self.engine_instance.get("ready", False)),
            "voice": self.voice,
            "language": self.language,
            "rate": self.rate,
            "pitch": self.pitch,
            "volume": self.volume,
            "output_dir": str(self.output_dir),
            "output_format": self.output_format,
            "cache_enabled": self.cache_enabled,
            "cache_size": len(self.cache),
            "total_synthesis": self.total_synthesis,
            "total_failures": self.total_failures,
            "total_duration": round(self.total_duration, 2),
            "last_synthesis_time": round(self.last_synthesis_time, 3),
            "average_synthesis_time": round(self.average_synthesis_time, 3),
            "last_error": self.last_error,
        }

    def speak(self, text: str, **kwargs) -> Dict[str, Any]:
        """Alias directo de `synthesize` para integración con el engine."""
        return self.synthesize(text, **kwargs)