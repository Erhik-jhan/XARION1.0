# app/core/state.py

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import time


# =========================================================
# ENUMS
# =========================================================

class EngineState(Enum):
    """Estado general del motor XARION."""
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    TALKING = "talking"
    RECORDING = "recording"
    ERROR = "error"
    STOPPED = "stopped"


class AvatarState(Enum):
    """Estado del avatar."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    VISIBLE = "visible"
    HIDDEN = "hidden"
    ERROR = "error"


class AudioState(Enum):
    """Estado del audio."""
    EMPTY = "empty"
    LOADING = "loading"
    READY = "ready"
    PLAYING = "playing"
    PAUSED = "paused"
    FINISHED = "finished"
    ERROR = "error"


class MotionState(Enum):
    """Estado del motor de movimiento."""
    DISABLED = "disabled"
    IDLE = "idle"
    ACTIVE = "active"
    VOICE_DRIVEN = "voice_driven"
    GESTURE = "gesture"


class GestureType(Enum):
    """Gestos disponibles en XARION 1.0."""
    NEUTRAL = "neutral"
    QUESTION = "question"
    TALKING = "talking"


class RecordingState(Enum):
    """Estado de la grabación."""
    INACTIVE = "inactive"
    PREPARING = "preparing"
    RECORDING = "recording"
    PAUSING = "pausing"
    FINISHING = "finishing"
    SAVED = "saved"
    ERROR = "error"


# =========================================================
# SUB-ESTADOS (componentes del avatar)
# =========================================================

@dataclass
class EyesState:
    """Estado de los ojos del avatar."""
    look_x: float = 0.0                  # -1.0 a 1.0
    look_y: float = 0.0                  # -1.0 a 1.0
    pupil_dilation: float = 1.0          # 0.5 a 1.5
    openness: float = 1.0                # 0.0 (cerrado) a 1.0 (abierto)
    glow_intensity: float = 1.0          # intensidad del brillo verde
    color: tuple = (0, 255, 100)         # color RGB del brillo


@dataclass
class BlinkState:
    """Estado del parpadeo."""
    enabled: bool = True
    interval_min: float = 2.0
    interval_max: float = 6.0
    next_blink_time: float = 0.0
    is_blinking: bool = False
    blink_progress: float = 0.0          # 0.0 a 1.0
    blink_duration: float = 0.15
    double_blink_chance: float = 0.1


@dataclass
class MouthState:
    """Estado de la boca (sincronización labial)."""
    openness: float = 0.0                # 0.0 cerrada, 1.0 abierta
    smile: float = 0.5                   # 0.0 triste, 1.0 sonrisa
    viseme: str = "neutral"              # fonema actual
    glow_intensity: float = 1.0
    color: tuple = (0, 255, 100)


@dataclass
class HeadMotionState:
    """Estado del movimiento de la cabeza."""
    rotation_x: float = 0.0              # pitch (arriba/abajo)
    rotation_y: float = 0.0              # yaw (izquierda/derecha)
    rotation_z: float = 0.0              # roll (inclinación)
    tilt_offset: float = 0.0
    nod_speed: float = 1.0
    follow_audio: bool = True
    follow_target: bool = False
    target_position: Dict[str, float] = field(
        default_factory=lambda: {"x": 0.0, "y": 0.0}
    )


@dataclass
class BodyMotionState:
    """Estado del movimiento corporal."""
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    scale: float = 1.0
    breathing_phase: float = 0.0
    breathing_amplitude: float = 0.02
    sway_phase: float = 0.0


@dataclass
class AntennaState:
    """Estado de la antena superior (detalle característico)."""
    glow_intensity: float = 1.0
    pulse_phase: float = 0.0
    pulse_speed: float = 1.5
    color: tuple = (0, 255, 100)


@dataclass
class AvatarComponents:
    """Agrupa todos los componentes animables del avatar."""
    eyes: EyesState = field(default_factory=EyesState)
    blink: BlinkState = field(default_factory=BlinkState)
    mouth: MouthState = field(default_factory=MouthState)
    head: HeadMotionState = field(default_factory=HeadMotionState)
    body: BodyMotionState = field(default_factory=BodyMotionState)
    antenna: AntennaState = field(default_factory=AntennaState)


# =========================================================
# AUDIO
# =========================================================

@dataclass
class AudioFeatures:
    """Características extraídas del audio por el analyzer."""
    rms: float = 0.0                     # volumen RMS
    db: float = -60.0                    # decibelios
    pitch: float = 0.0                   # frecuencia fundamental (Hz)
    spectral_centroid: float = 0.0       # "brillo" del sonido
    zero_crossing_rate: float = 0.0
    beat_detected: bool = False
    beat_strength: float = 0.0
    rhythm_bpm: float = 0.0
    is_speech: bool = False
    phoneme: str = "neutral"
    energy_band_low: float = 0.0
    energy_band_mid: float = 0.0
    energy_band_high: float = 0.0


@dataclass
class AudioStateData:
    """Estado completo del módulo de audio."""
    state: AudioState = AudioState.EMPTY
    file_path: Optional[str] = None
    duration: float = 0.0
    current_time: float = 0.0
    sample_rate: int = 22050
    channels: int = 1
    volume: float = 1.0
    muted: bool = False
    features: AudioFeatures = field(default_factory=AudioFeatures)
    waveform: List[float] = field(default_factory=list)
    tts_text: str = ""
    tts_voice: str = "default"
    tts_language: str = "es"


# =========================================================
# MOTION
# =========================================================

@dataclass
class MotionStateData:
    """Estado del motor de movimiento."""
    state: MotionState = MotionState.IDLE
    smoothing_factor: float = 0.15
    idle_enabled: bool = True
    voice_driven_enabled: bool = True
    intensity: float = 1.0
    last_voice_amplitude: float = 0.0
    last_beat_time: float = 0.0
    frames_processed: int = 0


# =========================================================
# GESTOS
# =========================================================

@dataclass
class GestureState:
    """Estado de los gestos."""
    current: GestureType = GestureType.NEUTRAL
    previous: GestureType = GestureType.NEUTRAL
    transition_progress: float = 1.0
    transition_duration: float = 0.5
    auto_detect: bool = True
    intensity: float = 1.0
    last_change_time: float = 0.0


# =========================================================
# GRABACIÓN / OUTPUT
# =========================================================

@dataclass
class RecordingStateData:
    """Estado del sistema de grabación de video."""
    state: RecordingState = RecordingState.INACTIVE
    output_path: Optional[str] = None
    frame_count: int = 0
    fps: int = 30
    duration: float = 0.0
    start_time: Optional[float] = None
    is_paused: bool = False
    include_audio: bool = True
    resolution: tuple = (1280, 720)


# =========================================================
# ESTADO PRINCIPAL
# =========================================================

@dataclass
class State:
    """
    Estado global completo de XARION-1.0.
    Agrupa motor, avatar, audio, movimiento, gestos y grabación.
    """

    # --- Motor general ---
    engine_state: EngineState = EngineState.IDLE
    is_running: bool = False
    last_error: Optional[str] = None
    error_history: List[str] = field(default_factory=list)

    # --- Avatar ---
    avatar_state: AvatarState = AvatarState.UNLOADED
    avatar_path: Optional[str] = None
    avatar_format: Optional[str] = None       # vrm, live2d, png, glb...
    avatar_loaded: bool = False
    avatar_components: AvatarComponents = field(default_factory=AvatarComponents)
    avatar_position: Dict[str, float] = field(
        default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0}
    )
    avatar_rotation: Dict[str, float] = field(
        default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0}
    )
    avatar_scale: float = 1.0

    # --- Audio ---
    audio: AudioStateData = field(default_factory=AudioStateData)

    # --- Motion ---
    motion: MotionStateData = field(default_factory=MotionStateData)

    # --- Gestos ---
    gesture: GestureState = field(default_factory=GestureState)

    # --- Grabación ---
    recording: RecordingStateData = field(default_factory=RecordingStateData)

    # --- Control de flujo ---
    frame_index: int = 0
    target_fps: int = 30
    delta_time: float = 0.0
    elapsed_time: float = 0.0

    # --- Metadatos ---
    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)

    # =====================================================
    # MÉTODOS
    # =====================================================

    def update_timestamp(self):
        self.last_update = time.time()

    def tick(self, delta_time: float):
        """Avanza un frame del motor."""
        self.frame_index += 1
        self.delta_time = delta_time
        self.elapsed_time += delta_time
        self.update_timestamp()

    # --- Errores ---
    def set_error(self, message: str):
        self.engine_state = EngineState.ERROR
        self.last_error = message
        self.error_history.append(f"[{time.time():.2f}] {message}")
        self.update_timestamp()

    def reset_error(self):
        self.last_error = None
        if self.engine_state == EngineState.ERROR:
            self.engine_state = EngineState.IDLE
        self.update_timestamp()

    # --- Avatar ---
    def set_avatar_loaded(self, path: str, fmt: str = "unknown"):
        self.avatar_loaded = True
        self.avatar_path = path
        self.avatar_format = fmt
        self.avatar_state = AvatarState.LOADED
        self.update_timestamp()

    def unload_avatar(self):
        self.avatar_loaded = False
        self.avatar_path = None
        self.avatar_format = None
        self.avatar_state = AvatarState.UNLOADED
        self.avatar_components = AvatarComponents()
        self.update_timestamp()

    # --- Audio ---
    def start_audio(self, path: Optional[str] = None, duration: float = 0.0):
        self.audio.state = AudioState.PLAYING
        if path:
            self.audio.file_path = path
        self.audio.duration = duration
        self.audio.current_time = 0.0
        self.update_timestamp()

    def pause_audio(self):
        if self.audio.state == AudioState.PLAYING:
            self.audio.state = AudioState.PAUSED
            self.update_timestamp()

    def stop_audio(self):
        self.audio.state = AudioState.FINISHED
        self.audio.current_time = 0.0
        self.update_timestamp()

    # --- Motion ---
    def set_motion_state(self, state: MotionState):
        self.motion.state = state
        self.update_timestamp()

    # --- Gestos ---
    def change_gesture(self, gesture: GestureType, duration: float = 0.5):
        if gesture == self.gesture.current:
            return
        self.gesture.previous = self.gesture.current
        self.gesture.current = gesture
        self.gesture.transition_progress = 0.0
        self.gesture.transition_duration = duration
        self.gesture.last_change_time = time.time()
        self.update_timestamp()

    # --- Grabación ---
    def start_recording(self, output_path: str, fps: int = 30):
        self.recording.state = RecordingState.RECORDING
        self.recording.output_path = output_path
        self.recording.fps = fps
        self.recording.frame_count = 0
        self.recording.start_time = time.time()
        self.recording.is_paused = False
        self.engine_state = EngineState.RECORDING
        self.update_timestamp()

    def stop_recording(self) -> float:
        duration = 0.0
        if self.recording.start_time is not None:
            duration = time.time() - self.recording.start_time
        self.recording.duration = duration
        self.recording.state = RecordingState.SAVED
        self.recording.start_time = None
        self.engine_state = EngineState.READY
        self.update_timestamp()
        return duration

    def increment_frame(self):
        if self.recording.state == RecordingState.RECORDING:
            self.recording.frame_count += 1

    # --- Serialización ---
    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine": {
                "state": self.engine_state.value,
                "is_running": self.is_running,
                "last_error": self.last_error,
                "error_history": self.error_history,
            },
            "avatar": {
                "state": self.avatar_state.value,
                "path": self.avatar_path,
                "format": self.avatar_format,
                "loaded": self.avatar_loaded,
                "position": self.avatar_position,
                "rotation": self.avatar_rotation,
                "scale": self.avatar_scale,
                "components": {
                    "eyes": vars(self.avatar_components.eyes),
                    "blink": vars(self.avatar_components.blink),
                    "mouth": vars(self.avatar_components.mouth),
                    "head": vars(self.avatar_components.head),
                    "body": vars(self.avatar_components.body),
                    "antenna": vars(self.avatar_components.antenna),
                },
            },
            "audio": {
                "state": self.audio.state.value,
                "file_path": self.audio.file_path,
                "duration": self.audio.duration,
                "current_time": self.audio.current_time,
                "volume": self.audio.volume,
                "muted": self.audio.muted,
                "features": vars(self.audio.features),
                "tts_text": self.audio.tts_text,
                "tts_voice": self.audio.tts_voice,
                "tts_language": self.audio.tts_language,
            },
            "motion": {
                "state": self.motion.state.value,
                "smoothing_factor": self.motion.smoothing_factor,
                "idle_enabled": self.motion.idle_enabled,
                "voice_driven_enabled": self.motion.voice_driven_enabled,
                "intensity": self.motion.intensity,
            },
            "gesture": {
                "current": self.gesture.current.value,
                "previous": self.gesture.previous.value,
                "transition_progress": self.gesture.transition_progress,
                "auto_detect": self.gesture.auto_detect,
            },
            "recording": {
                "state": self.recording.state.value,
                "output_path": self.recording.output_path,
                "frame_count": self.recording.frame_count,
                "fps": self.recording.fps,
                "duration": self.recording.duration,
                "resolution": self.recording.resolution,
            },
            "timing": {
                "frame_index": self.frame_index,
                "target_fps": self.target_fps,
                "delta_time": self.delta_time,
                "elapsed_time": self.elapsed_time,
                "start_time": self.start_time,
                "last_update": self.last_update,
            },
        }

    def reset(self):
        """Reinicia el estado completo a valores por defecto."""
        self.__init__()