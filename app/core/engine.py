# app/core/engine.py

import time
from typing import Optional, Callable, Any, Dict
from pathlib import Path

from app.core.config import Config
from app.core.state import (
    State,
    EngineState,
    AvatarState,
    AudioState,
    MotionState,
    RecordingState,
    GestureType,
)


class XarionEngine:
    """
    Motor principal de XARION-1.0.
    Orquesta el pipeline completo: avatar → audio → motion → render → output.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.config.ensure_directories()

        self.state = State()
        self.state.target_fps = self.config.FPS

        # --- Callbacks de módulos (se inyectan luego) ---
        self._callbacks: Dict[str, Callable] = {}

        # --- Módulos (se inicializan externamente) ---
        self.avatar_loader = None
        self.avatar_renderer = None
        self.audio_tts = None
        self.audio_analyzer = None
        self.motion_engine = None
        self.recorder = None
        self.video_exporter = None

        # --- Control de bucle ---
        self._last_frame_time: float = 0.0
        self._running: bool = False

    # =====================================================
    # REGISTRO DE MÓDULOS
    # =====================================================

    def register(self, name: str, module: Any):
        """Registra un módulo del pipeline (avatar, audio, motion, etc.)."""
        setattr(self, name, module)
        self.state.update_timestamp()

    def on(self, event: str, callback: Callable):
        """Registra un callback para un evento del motor."""
        self._callbacks[event] = callback

    def emit(self, event: str, *args, **kwargs):
        """Dispara un evento registrado."""
        if event in self._callbacks:
            try:
                self._callbacks[event](*args, **kwargs)
            except Exception as e:
                self.state.set_error(f"Error en evento '{event}': {e}")

    # =====================================================
    # CICLO DE VIDA
    # =====================================================

    def initialize(self):
        """Inicializa el motor y carga el avatar."""
        self.state.engine_state = EngineState.LOADING
        self.state.update_timestamp()

        try:
            self._load_avatar()
            self._initialize_modules()
            self.state.engine_state = EngineState.READY
            self.state.is_running = True
            self.state.update_timestamp()
        except Exception as e:
            self.state.set_error(f"Error en initialize: {e}")

    def _load_avatar(self):
        """Carga el avatar usando el loader registrado."""
        if self.avatar_loader is None:
            self.state.set_error("avatar_loader no registrado")
            return

        self.state.avatar_state = AvatarState.LOADING
        result = self.avatar_loader.load()

        if result and result.get("success"):
            self.state.set_avatar_loaded(
                path=result.get("path", ""),
                fmt=result.get("format", "unknown"),
            )
            self.state.avatar_state = AvatarState.LOADED
        else:
            self.state.avatar_state = AvatarState.ERROR
            self.state.set_error("No se pudo cargar el avatar")

    def _initialize_modules(self):
        """Inicializa los módulos que lo requieran."""
        for name in [
            "avatar_renderer",
            "audio_analyzer",
            "motion_engine",
        ]:
            module = getattr(self, name, None)
            if module is not None and hasattr(module, "initialize"):
                module.initialize()

    # =====================================================
    # BUCLE PRINCIPAL
    # =====================================================

    def start(self):
        """Inicia el bucle principal del motor."""
        if not self.state.is_running:
            self.initialize()
        self._running = True
        self._last_frame_time = time.time()
        self.loop()

    def loop(self):
        """Bucle principal del motor."""
        while self._running:
            now = time.time()
            delta = now - self._last_frame_time

            # Control de FPS
            if delta < (1.0 / self.state.target_fps):
                time.sleep(max(0.0, (1.0 / self.state.target_fps) - delta))
                continue

            self._last_frame_time = now
            self._tick(delta)

    def _tick(self, delta: float):
        """Ejecuta un frame del pipeline."""
        self.state.tick(delta)

        try:
            # 1. Audio → Analizar
            self._update_audio()

            # 2. Motion → Actualizar
            self._update_motion(delta)

            # 3. Avatar → Renderizar
            self._render_avatar(delta)

            # 4. Output → Grabar frame
            self._record_frame()
        except Exception as e:
            self.state.set_error(f"Error en tick: {e}")

    def stop(self):
        """Detiene el motor."""
        self._running = False
        self.state.is_running = False
        self.state.engine_state = EngineState.STOPPED
        self.state.update_timestamp()

    # =====================================================
    # PIPELINE
    # =====================================================

    def _update_audio(self):
        """Ejecuta el análisis de audio si hay audio activo."""
        if self.state.audio.state == AudioState.PLAYING and self.audio_analyzer:
            features = self.audio_analyzer.analyze()
            if features:
                self.state.audio.features = features

    def _update_motion(self, delta: float):
        """Actualiza el motor de movimiento."""
        if self.state.motion.state != MotionState.DISABLED and self.motion_engine:
            self.motion_engine.update(delta, self.state)

    def _render_avatar(self, delta: float):
        """Renderiza el frame del avatar."""
        if self.avatar_renderer and self.state.avatar_loaded:
            self.avatar_renderer.render(delta, self.state)

    def _record_frame(self):
        """Graba el frame actual si está activa la grabación."""
        if self.state.recording.state == RecordingState.RECORDING:
            if self.recorder:
                self.recorder.capture_frame()
            self.state.increment_frame()

    # =====================================================
    # ACCIONES DE ALTO NIVEL
    # =====================================================

    def speak(self, text: str, voice: Optional[str] = None):
        """Genera voz con TTS y ejecuta el pipeline de habla."""
        if self.audio_tts is None:
            self.state.set_error("audio_tts no registrado")
            return

        self.state.engine_state = EngineState.TALKING
        self.state.audio.tts_text = text
        if voice:
            self.state.audio.tts_voice = voice

        result = self.audio_tts.synthesize(text, voice=voice)
        if result and result.get("success"):
            self.state.audio.file_path = result.get("path")
            self.state.audio.duration = result.get("duration", 0.0)
            self.state.start_audio(
                path=result.get("path"),
                duration=result.get("duration", 0.0),
            )
            self.state.change_gesture(GestureType.TALKING)
        else:
            self.state.set_error("Error al generar TTS")

    def set_gesture(self, gesture: GestureType):
        """Cambia el gesto actual del avatar."""
        self.state.change_gesture(gesture)

    def start_recording(self, output_path: str):
        """Inicia la grabación de video."""
        self.state.start_recording(output_path, fps=self.state.target_fps)

    def stop_recording(self) -> float:
        """Detiene la grabación."""
        duration = self.state.stop_recording()
        if self.recorder:
            self.recorder.finalize()
        return duration

    def export_video(self, output_path: str) -> bool:
        """Exporta el video final."""
        if self.video_exporter is None:
            self.state.set_error("video_exporter no registrado")
            return False
        return self.video_exporter.export(output_path)

    # =====================================================
    # INFORMACIÓN
    # =====================================================

    def status(self) -> Dict[str, Any]:
        """Devuelve el estado actual del motor."""
        return {
            "engine_state": self.state.engine_state.value,
            "avatar_state": self.state.avatar_state.value,
            "audio_state": self.state.audio.state.value,
            "motion_state": self.state.motion.state.value,
            "recording_state": self.state.recording.state.value,
            "frame_index": self.state.frame_index,
            "elapsed_time": self.state.elapsed_time,
            "fps": self.state.target_fps,
            "last_error": self.state.last_error,
        }