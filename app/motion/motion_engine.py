# app/motion/motion_engine.py

import math
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State, AudioFeatures, MotionState


# =========================================================
# MODOS DEL MOTOR DE MOVIMIENTO
# =========================================================

class MotionMode(Enum):
    """Modos operativos del motor de movimiento."""
    DISABLED = "disabled"        # sin procesamiento
    IDLE = "idle"                # reposo suave
    VOICE = "voice"              # reactivo a voz
    RHYTHM = "rhythm"            # reactivo a ritmo
    GESTURE = "gesture"          # gestos programados
    COMBINED = "combined"        # combinación de todos
    PRECISE = "precise"          # alta fidelidad, baja latencia


# =========================================================
# PERFILES POR MODO
# =========================================================

MOTION_MODE_PROFILES: Dict[MotionMode, Dict[str, float]] = {
    MotionMode.DISABLED: {"idle": 0.0, "voice": 0.0, "rhythm": 0.0, "gesture": 0.0, "smoothing": 0.0},
    MotionMode.IDLE:     {"idle": 1.0, "voice": 0.0, "rhythm": 0.0, "gesture": 0.0, "smoothing": 0.20},
    MotionMode.VOICE:    {"idle": 0.4, "voice": 1.0, "rhythm": 0.3, "gesture": 0.0, "smoothing": 0.18},
    MotionMode.RHYTHM:   {"idle": 0.3, "voice": 0.5, "rhythm": 1.0, "gesture": 0.0, "smoothing": 0.15},
    MotionMode.GESTURE:  {"idle": 0.4, "voice": 0.3, "rhythm": 0.3, "gesture": 1.0, "smoothing": 0.20},
    MotionMode.COMBINED: {"idle": 0.5, "voice": 0.8, "rhythm": 0.7, "gesture": 0.6, "smoothing": 0.17},
    MotionMode.PRECISE:  {"idle": 0.4, "voice": 1.0, "rhythm": 1.0, "gesture": 0.7, "smoothing": 0.10},
}


# =========================================================
# MOTOR DE MOVIMIENTO
# =========================================================

class MotionEngine:
    """
    Motor central de movimiento de XARION-1.0.
    Coordina los movimientos del avatar a partir de:
    - Estado de reposo (idle)
    - Análisis de voz (audio features)
    - Ritmo (beats/BPM)
    - Gestos programados
    Combina estas fuentes según el modo activo y distribuye
    la señal resultante a cabeza, cuerpo y boca.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Modo activo ---
        self.mode: MotionMode = MotionMode.COMBINED
        self.previous_mode: MotionMode = MotionMode.COMBINED
        self.mode_blend: float = 1.0
        self.mode_blend_speed: float = 2.5
        self.profile: Dict[str, float] = MOTION_MODE_PROFILES[self.mode].copy()

        # --- Señales por fuente (0.0 a 1.0) ---
        self.idle_signal: float = 0.0
        self.voice_signal: float = 0.0
        self.rhythm_signal: float = 0.0
        self.gesture_signal: float = 0.0

        # --- Señal combinada ---
        self.combined_signal: float = 0.0
        self.signal_smoothing: float = self.profile["smoothing"]

        # --- Distribución ---
        self.head_weight: float = 0.4
        self.body_weight: float = 0.35
        self.mouth_weight: float = 0.25

        # --- Intensidad global ---
        self.intensity: float = 1.0
        self.intensity_min: float = 0.0
        self.intensity_max: float = 2.0

        # --- Reposo ---
        self.idle_phase: float = 0.0
        self.idle_speed: float = 0.6
        self.idle_amplitude: float = 0.02

        # --- Reacción a voz ---
        self.voice_amplitude_scale: float = 0.6
        self.last_voice_amplitude: float = 0.0
        self.voice_smoothing: float = 0.18

        # --- Reacción a ritmo ---
        self.rhythm_punch: float = 0.0
        self.rhythm_decay: float = 5.0
        self.last_beat_time: float = 0.0

        # --- Gestos ---
        self.gesture_intensity: float = 1.0
        self.gesture_decay: float = 3.0

        # --- Backend externo ---
        self.smoothing_controller = None
        self.idle_controller = None
        self.voice_controller = None

        # --- Estadísticas ---
        self.updates: int = 0
        self.mode_changes: int = 0
        self.last_update: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el estado interno del motor."""
        self.idle_phase = 0.0
        self.last_voice_amplitude = 0.0
        self.rhythm_punch = 0.0
        self.last_beat_time = 0.0
        self.combined_signal = 0.0
        self.last_update = time.time()

    def register(self, name: str, module: Any):
        """Registra submódulos (smoothing, idle, voice)."""
        if name == "smoothing":
            self.smoothing_controller = module
        elif name == "idle":
            self.idle_controller = module
        elif name == "voice":
            self.voice_controller = module

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """Actualiza el motor de movimiento cada frame."""
        self.updates += 1

        # 1. Blending entre modos
        self._update_mode_blend(delta)

        # 2. Actualizar señales por fuente
        self._update_idle_signal(delta)
        self._update_voice_signal(state.audio.features, delta)
        self._update_rhythm_signal(state.audio.features, delta)
        self._update_gesture_signal(delta)

        # 3. Combinar señales según pesos del modo
        self._combine_signals(delta)

        # 4. Distribuir a componentes
        self._distribute_to_components(state)

        # 5. Delegar a submódulos si están registrados
        self._delegate_to_submodules(delta, state)

        self.last_update = time.time()

    # =====================================================
    # BLENDING DE MODOS
    # =====================================================

    def _update_mode_blend(self, delta: float):
        """Suaviza la transición entre modos."""
        if self.mode_blend < 1.0:
            self.mode_blend = min(1.0, self.mode_blend + delta * self.mode_blend_speed)
            if self.mode_blend >= 1.0:
                self.previous_mode = self.mode

    # =====================================================
    # SEÑALES POR FUENTE
    # =====================================================

    def _update_idle_signal(self, delta: float):
        """Actualiza la señal de reposo (idle)."""
        self.idle_phase += delta * self.idle_speed * math.tau
        idle = (math.sin(self.idle_phase) + 1.0) * 0.5
        self.idle_signal = self._clamp(idle * self.idle_amplitude * 20.0, 0.0, 1.0)

    def _update_voice_signal(self, features: Optional[AudioFeatures], delta: float):
        """Actualiza la señal reactiva a voz."""
        if features is None:
            target = 0.0
        else:
            rms = self._clamp(features.rms * 4.0, 0.0, 1.0)
            pitch_norm = self._clamp(features.pitch / 400.0, 0.0, 1.0)
            target = rms * 0.7 + pitch_norm * 0.3

        self.last_voice_amplitude = self._smooth(
            self.last_voice_amplitude, target, self.voice_smoothing
        )
        self.voice_signal = self._clamp(
            self.last_voice_amplitude * self.voice_amplitude_scale, 0.0, 1.0
        )

    def _update_rhythm_signal(self, features: Optional[AudioFeatures], delta: float):
        """Actualiza la señal reactiva al ritmo."""
        if features is not None and features.beat_detected:
            self.rhythm_punch = max(self.rhythm_punch, features.beat_strength)
            self.last_beat_time = time.time()

        if self.rhythm_punch > 0.0:
            self.rhythm_punch = max(0.0, self.rhythm_punch - delta * self.rhythm_decay)

        bpm_norm = 0.0
        if features is not None and features.rhythm_bpm > 0:
            bpm_norm = self._clamp(features.rhythm_bpm / 180.0, 0.0, 1.0)

        self.rhythm_signal = self._clamp(
            self.rhythm_punch * 0.7 + bpm_norm * 0.3, 0.0, 1.0
        )

    def _update_gesture_signal(self, delta: float):
        """Actualiza la señal de gestos."""
        if self.gesture_signal > 0.0:
            self.gesture_signal = max(
                0.0, self.gesture_signal - delta * self.gesture_decay
            )

    # =====================================================
    # COMBINACIÓN DE SEÑALES
    # =====================================================

    def _combine_signals(self, delta: float):
        """Combina todas las señales según los pesos del modo."""
        profile = MOTION_MODE_PROFILES.get(self.mode, MOTION_MODE_PROFILES[MotionMode.COMBINED])

        weighted = (
            self.idle_signal * profile["idle"] +
            self.voice_signal * profile["voice"] +
            self.rhythm_signal * profile["rhythm"] +
            self.gesture_signal * profile["gesture"]
        )

        total_weight = (
            profile["idle"] + profile["voice"] +
            profile["rhythm"] + profile["gesture"]
        )

        if total_weight > 0:
            weighted /= total_weight

        # Aplicar blending entre modos
        prev_profile = MOTION_MODE_PROFILES.get(
            self.previous_mode, MOTION_MODE_PROFILES[MotionMode.IDLE]
        )
        prev_weighted = (
            self.idle_signal * prev_profile["idle"] +
            self.voice_signal * prev_profile["voice"] +
            self.rhythm_signal * prev_profile["rhythm"] +
            self.gesture_signal * prev_profile["gesture"]
        )
        prev_total = (
            prev_profile["idle"] + prev_profile["voice"] +
            prev_profile["rhythm"] + prev_profile["gesture"]
        )
        if prev_total > 0:
            prev_weighted /= prev_total

        blended = prev_weighted * (1.0 - self.mode_blend) + weighted * self.mode_blend
        blended *= self.intensity

        # Suavizado final
        self.signal_smoothing = profile.get("smoothing", 0.18)
        self.combined_signal = self._smooth(
            self.combined_signal, blended, self.signal_smoothing
        )

    # =====================================================
    # DISTRIBUCIÓN A COMPONENTES
    # =====================================================

    def _distribute_to_components(self, state: State):
        """Distribuye la señal combinada a cabeza, cuerpo y boca."""
        s = self.combined_signal

        # Cabeza: pequeño pitch reactivo
        if self.head_weight > 0.0:
            head = state.avatar_components.head
            head_amp = s * self.head_weight * 0.05
            head.target_position["x"] = self._clamp(
                head.target_position.get("x", 0.0) + head_amp * 0.3, -1.0, 1.0
            )

        # Cuerpo: rebote sutil
        if self.body_weight > 0.0:
            body = state.avatar_components.body
            body.breathing_amplitude = max(
                0.015, body.breathing_amplitude + s * self.body_weight * 0.008
            )

        # Boca: pequeña apertura cuando no hay lipsync
        if self.mouth_weight > 0.0:
            mouth = state.avatar_components.mouth
            mouth.openness = max(mouth.openness, s * self.mouth_weight * 0.5)

    # =====================================================
    # SUBMÓDULOS
    # =====================================================

    def _delegate_to_submodules(self, delta: float, state: State):
        """Delega a submódulos registrados."""
        if self.idle_controller is not None and self.mode in (
            MotionMode.IDLE, MotionMode.COMBINED, MotionMode.PRECISE
        ):
            if hasattr(self.idle_controller, "update"):
                self.idle_controller.update(delta, state)

        if self.voice_controller is not None and self.mode in (
            MotionMode.VOICE, MotionMode.COMBINED, MotionMode.PRECISE
        ):
            if hasattr(self.voice_controller, "update"):
                self.voice_controller.update(delta, state)

        if self.smoothing_controller is not None:
            if hasattr(self.smoothing_controller, "update"):
                self.smoothing_controller.update(delta, state)

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def set_mode(self, mode: MotionMode):
        """Cambia el modo del motor."""
        if mode == self.mode:
            return
        self.previous_mode = self.mode
        self.mode = mode
        self.mode_blend = 0.0
        self.mode_changes += 1

    def set_intensity(self, intensity: float):
        """Ajusta la intensidad global del movimiento."""
        self.intensity = self._clamp(
            intensity, self.intensity_min, self.intensity_max
        )

    def set_weights(self, head: Optional[float] = None,
                    body: Optional[float] = None,
                    mouth: Optional[float] = None):
        """Ajusta los pesos de distribución."""
        if head is not None:
            self.head_weight = self._clamp(head, 0.0, 1.0)
        if body is not None:
            self.body_weight = self._clamp(body, 0.0, 1.0)
        if mouth is not None:
            self.mouth_weight = self._clamp(mouth, 0.0, 1.0)

    def trigger_gesture(self, intensity: float = 1.0):
        """Dispara un gesto manual."""
        self.gesture_signal = self._clamp(intensity, 0.0, 1.0)

    def set_idle_params(self, speed: Optional[float] = None,
                        amplitude: Optional[float] = None):
        """Ajusta los parámetros de reposo."""
        if speed is not None:
            self.idle_speed = max(0.1, speed)
        if amplitude is not None:
            self.idle_amplitude = self._clamp(amplitude, 0.0, 0.2)

    def set_voice_params(self, scale: Optional[float] = None,
                         smoothing: Optional[float] = None):
        """Ajusta los parámetros de reacción a voz."""
        if scale is not None:
            self.voice_amplitude_scale = self._clamp(scale, 0.0, 1.0)
        if smoothing is not None:
            self.voice_smoothing = self._clamp(smoothing, 0.01, 1.0)

    def reset(self):
        """Reinicia el motor."""
        self.initialize()
        self.mode = MotionMode.COMBINED
        self.previous_mode = MotionMode.COMBINED
        self.mode_blend = 1.0

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_signals(self) -> Dict[str, float]:
        """Devuelve todas las señales internas."""
        return {
            "idle": round(self.idle_signal, 4),
            "voice": round(self.voice_signal, 4),
            "rhythm": round(self.rhythm_signal, 4),
            "gesture": round(self.gesture_signal, 4),
            "combined": round(self.combined_signal, 4),
        }

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del motor."""
        return {
            "mode": self.mode.value,
            "previous_mode": self.previous_mode.value,
            "mode_blend": round(self.mode_blend, 3),
            "intensity": round(self.intensity, 3),
            "signals": self.get_signals(),
            "weights": {
                "head": self.head_weight,
                "body": self.body_weight,
                "mouth": self.mouth_weight,
            },
            "voice_amplitude": round(self.last_voice_amplitude, 4),
            "rhythm_punch": round(self.rhythm_punch, 4),
            "mode_changes": self.mode_changes,
            "updates": self.updates,
        }

    def get_available_modes(self) -> List[str]:
        """Lista los modos disponibles."""
        return [m.value for m in MotionMode]

    # =====================================================
    # UTILIDADES
    # =====================================================

    @staticmethod
    def _clamp(value: float, min_v: float, max_v: float) -> float:
        """Limita un valor entre un mínimo y un máximo."""
        return max(min_v, min(max_v, value))

    @staticmethod
    def _smooth(current: float, target: float, factor: float) -> float:
        """Interpolación exponencial suave."""
        return current + (target - current) * factor