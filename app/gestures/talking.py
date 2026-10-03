# app/gestures/talking.py

import math
import random
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State, GestureType, AudioFeatures


# =========================================================
# SUB-GESTOS DE HABLA
# =========================================================

class TalkingVariant(Enum):
    """Variantes del gesto de habla."""
    NORMAL = "normal"            # conversación normal
    ENTHUSIASTIC = "enthusiastic"  # entusiasmo
    CALM = "calm"                # explicación calmada
    EXCITED = "excited"          # emoción alta
    SERIOUS = "serious"          # seriedad
    FRIENDLY = "friendly"        # amistoso


# =========================================================
# PERFILES POR VARIANTE
# =========================================================

TALKING_VARIANTS: Dict[TalkingVariant, Dict[str, float]] = {
    TalkingVariant.NORMAL:       {"head_amp": 0.035, "head_speed": 1.4, "body_amp": 0.020, "body_speed": 1.1, "mouth_boost": 0.35, "smile": 0.55, "antenna_glow": 1.20, "antenna_speed": 1.80, "nod_chance": 0.15},
    TalkingVariant.ENTHUSIASTIC: {"head_amp": 0.060, "head_speed": 1.9, "body_amp": 0.035, "body_speed": 1.5, "mouth_boost": 0.55, "smile": 0.75, "antenna_glow": 1.60, "antenna_speed": 2.40, "nod_chance": 0.30},
    TalkingVariant.CALM:         {"head_amp": 0.020, "head_speed": 1.0, "body_amp": 0.010, "body_speed": 0.8, "mouth_boost": 0.25, "smile": 0.55, "antenna_glow": 1.00, "antenna_speed": 1.40, "nod_chance": 0.10},
    TalkingVariant.EXCITED:      {"head_amp": 0.080, "head_speed": 2.4, "body_amp": 0.050, "body_speed": 2.0, "mouth_boost": 0.75, "smile": 0.85, "antenna_glow": 1.90, "antenna_speed": 3.00, "nod_chance": 0.40},
    TalkingVariant.SERIOUS:      {"head_amp": 0.025, "head_speed": 1.2, "body_amp": 0.012, "body_speed": 0.9, "mouth_boost": 0.30, "smile": 0.40, "antenna_glow": 1.10, "antenna_speed": 1.50, "nod_chance": 0.20},
    TalkingVariant.FRIENDLY:     {"head_amp": 0.045, "head_speed": 1.6, "body_amp": 0.025, "body_speed": 1.3, "mouth_boost": 0.45, "smile": 0.80, "antenna_glow": 1.40, "antenna_speed": 2.10, "nod_chance": 0.25},
}


# =========================================================
# CONTROLADOR DE GESTO DE HABLA
# =========================================================

class TalkingGesture:
    """
    Gesto de habla de XARION-1.0.
    Reacciona al audio en tiempo real modulando cabeza, cuerpo
    y boca. Incluye nodding ocasional, variaciones de expresión
    y retorno suave al neutral al terminar de hablar.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Identificación ---
        self.gesture_type: GestureType = GestureType.TALKING
        self.variant: TalkingVariant = TalkingVariant.NORMAL
        self.profile: Dict[str, float] = TALKING_VARIANTS[self.variant].copy()

        # --- Estado ---
        self.active: bool = False
        self.transition: float = 1.0
        self.transition_speed: float = 3.0
        self.intensity: float = 1.0
        self.priority: int = 2

        # --- Amplitudes ---
        self.head_amp: float = self.profile["head_amp"]
        self.head_speed: float = self.profile["head_speed"]
        self.body_amp: float = self.profile["body_amp"]
        self.body_speed: float = self.profile["body_speed"]
        self.mouth_boost: float = self.profile["mouth_boost"]
        self.smile_target: float = self.profile["smile"]
        self.antenna_glow_target: float = self.profile["antenna_glow"]
        self.antenna_speed_target: float = self.profile["antenna_speed"]
        self.nod_chance: float = self.profile["nod_chance"]

        # --- Fases ---
        self.head_phase_x: float = 0.0
        self.head_phase_y: float = 0.0
        self.body_phase_x: float = 0.0
        self.body_phase_y: float = 0.0
        self.micro_phase: float = 0.0

        # --- Señales de audio suavizadas ---
        self.rms_smoothed: float = 0.0
        self.pitch_smoothed: float = 0.0
        self.energy_smoothed: float = 0.0
        self.beat_smoothed: float = 0.0
        self.rms_smoothing: float = 0.20
        self.pitch_smoothing: float = 0.22
        self.energy_smoothing: float = 0.22
        self.beat_smoothing: float = 0.30

        # --- Nodding ---
        self.nod_active: bool = False
        self.nod_progress: float = 0.0
        self.nod_duration: float = 0.5
        self.nod_count: int = 1
        self.nod_cooldown: float = 1.5
        self.last_nod_time: float = 0.0

        # --- Expresión ---
        self.current_smile: float = 0.55
        self.current_antenna_glow: float = 1.00
        self.smile_smoothing: float = 0.05
        self.antenna_smoothing: float = 0.05

        # --- Salida automática ---
        self.auto_exit: bool = True
        self.silence_threshold: float = 0.02
        self.silence_timeout: float = 0.8
        self.silence_elapsed: float = 0.0

        # --- Callbacks ---
        self.on_complete = None

        # --- Estadísticas ---
        self.updates: int = 0
        self.activations: int = 0
        self.completions: int = 0
        self.total_nods: int = 0
        self.last_update: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el gesto de habla."""
        self.active = False
        self.transition = 1.0
        self.head_phase_x = random.uniform(0.0, math.tau)
        self.head_phase_y = random.uniform(0.0, math.tau)
        self.body_phase_x = random.uniform(0.0, math.tau)
        self.body_phase_y = random.uniform(0.0, math.tau)
        self.micro_phase = random.uniform(0.0, math.tau)
        self._apply_profile()
        self.last_update = time.time()

    def _apply_profile(self):
        """Aplica el perfil de la variante a los parámetros internos."""
        self.head_amp = self.profile["head_amp"]
        self.head_speed = self.profile["head_speed"]
        self.body_amp = self.profile["body_amp"]
        self.body_speed = self.profile["body_speed"]
        self.mouth_boost = self.profile["mouth_boost"]
        self.smile_target = self.profile["smile"]
        self.antenna_glow_target = self.profile["antenna_glow"]
        self.antenna_speed_target = self.profile["antenna_speed"]
        self.nod_chance = self.profile["nod_chance"]

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """Actualiza el gesto de habla cada frame."""
        if not self.active:
            return

        self.updates += 1
        now = time.time()

        # 1. Progreso de transición
        if self.transition < 1.0:
            self.transition = min(1.0, self.transition + delta * self.transition_speed)

        # 2. Suavizar features de audio
        self._smooth_audio_features(state.audio.features, delta)

        # 3. Detectar silencio prolongado
        self._check_silence(state.audio.features, delta)

        # 4. Avanzar fases internas
        self._advance_phases(delta)

        # 5. Nodding ocasional
        self._maybe_nod(now)
        if self.nod_active:
            self._update_nod(delta)

        # 6. Suavizar expresión
        self.current_smile = self._smooth(
            self.current_smile, self.smile_target, self.smile_smoothing
        )
        self.current_antenna_glow = self._smooth(
            self.current_antenna_glow, self.antenna_glow_target, self.antenna_smoothing
        )

        # 7. Aplicar al estado
        self._apply_to_state(state)

        self.last_update = now

    # =====================================================
    # AUDIO
    # =====================================================

    def _smooth_audio_features(self, features: Optional[AudioFeatures], delta: float):
        """Suaviza las features de audio para modular el gesto."""
        if features is None:
            decay = max(0.0, 1.0 - delta * 3.0)
            self.rms_smoothed *= decay
            self.pitch_smoothed *= decay
            self.energy_smoothed *= decay
            self.beat_smoothed *= decay
            return

        rms = self._clamp(features.rms * 4.0, 0.0, 1.0)
        pitch_norm = self._clamp(features.pitch / 400.0, 0.0, 1.0)
        energy = self._clamp(
            (features.energy_band_low + features.energy_band_mid) * 0.5, 0.0, 1.0
        )
        beat = self._clamp(features.beat_strength, 0.0, 1.0)

        self.rms_smoothed = self._smooth(self.rms_smoothed, rms, self.rms_smoothing)
        self.pitch_smoothed = self._smooth(
            self.pitch_smoothed, pitch_norm, self.pitch_smoothing
        )
        self.energy_smoothed = self._smooth(
            self.energy_smoothed, energy, self.energy_smoothing
        )
        self.beat_smoothed = self._smooth(
            self.beat_smoothed, beat, self.beat_smoothing
        )

    def _check_silence(self, features: Optional[AudioFeatures], delta: float):
        """Sale automáticamente si hay silencio prolongado."""
        if not self.auto_exit:
            return
        is_silent = features is None or features.rms < self.silence_threshold

        if is_silent:
            self.silence_elapsed += delta
            if self.silence_elapsed >= self.silence_timeout:
                self._exit()
        else:
            self.silence_elapsed = 0.0

    def _exit(self):
        """Inicia la salida del gesto."""
        self.transition = max(0.0, self.transition - 0.05)
        if self.transition <= 0.01:
            self._complete()

    def _complete(self):
        """Finaliza el gesto."""
        self.active = False
        self.completions += 1
        if callable(self.on_complete):
            try:
                self.on_complete()
            except Exception:
                pass

    # =====================================================
    # FASES
    # =====================================================

    def _advance_phases(self, delta: float):
        """Avanza las fases internas moduladas por la voz."""
        speed_mod = 1.0 + self.rms_smoothed * 0.8

        self.head_phase_x += delta * self.head_speed * speed_mod * math.tau
        self.head_phase_y += delta * self.head_speed * speed_mod * math.tau * 0.7
        self.body_phase_x += delta * self.body_speed * speed_mod * math.tau
        self.body_phase_y += delta * self.body_speed * speed_mod * math.tau * 0.6
        self.micro_phase += delta * 3.0 * math.tau

    # =====================================================
    # NODDING
    # =====================================================

    def _maybe_nod(self, now: float):
        """Lanza un nodding ocasional."""
        if self.nod_active:
            return
        if now - self.last_nod_time < self.nod_cooldown:
            return
        if random.random() < self.nod_chance * 0.05:
            self._start_nod()

    def _start_nod(self):
        """Inicia un nodding."""
        self.nod_active = True
        self.nod_progress = 0.0
        self.nod_count = random.choice([1, 1, 2])
        self.total_nods += 1

    def _update_nod(self, delta: float):
        """Actualiza el progreso del nodding."""
        self.nod_progress += delta / max(0.01, self.nod_duration)
        if self.nod_progress >= 1.0:
            self.nod_active = False
            self.nod_progress = 0.0
            self.last_nod_time = time.time()

    # =====================================================
    # APLICACIÓN AL ESTADO
    # =====================================================

    def _apply_to_state(self, state: State):
        """Aplica el gesto de habla al estado global."""
        t = self.transition * self.intensity
        if t <= 0.0:
            return

        # Modulaciones combinadas
        mod = self._clamp(
            self.rms_smoothed * 0.7 +
            self.pitch_smoothed * 0.3 +
            self.energy_smoothed * 0.2,
            0.0, 2.0,
        )

        micro = math.sin(self.micro_phase) * 0.005 * t

        # Cabeza
        head = state.avatar_components.head
        rx = math.sin(self.head_phase_x) * self.head_amp * mod * t
        ry = math.sin(self.head_phase_y) * self.head_amp * mod * 0.8 * t
        rz = math.sin(self.head_phase_x * 0.5) * self.head_amp * 0.5 * t

        if self.nod_active:
            nod_curve = math.sin(self.nod_progress * self.nod_count * math.tau)
            rx += nod_curve * self.head_amp * 1.5 * t

        head.rotation_x += rx + micro
        head.rotation_y += ry
        head.rotation_z += rz + micro * 0.5

        # Cuerpo
        body = state.avatar_components.body
        px = math.sin(self.body_phase_x) * self.body_amp * mod * t
        py = math.sin(self.body_phase_y) * self.body_amp * 0.7 * mod * t
        body.position_x += px
        body.position_y += py
        body.rotation_z += px * 0.3

        # Boca
        mouth = state.avatar_components.mouth
        boost = self.rms_smoothed * self.mouth_boost * t
        mouth.openness = self._clamp(
            max(mouth.openness, boost), 0.0, 1.0
        )
        mouth.smile = self._clamp(
            mouth.smile * (1.0 - t) + self.current_smile * t, 0.0, 1.0
        )

        # Antena
        antenna = state.avatar_components.antenna
        antenna.glow_intensity = self._clamp(
            antenna.glow_intensity * (1.0 - t) + self.current_antenna_glow * t,
            0.0, 2.5,
        )
        antenna.pulse_speed = self._clamp(
            antenna.pulse_speed * (1.0 - t) + self.antenna_speed_target * t,
            0.1, 5.0,
        )

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def activate(self):
        """Activa el gesto de habla."""
        self.active = True
        self.transition = 0.0
        self.silence_elapsed = 0.0
        self.activations += 1

    def deactivate(self):
        """Desactiva el gesto de habla."""
        self.active = False
        self.transition = 0.0

    def set_variant(self, variant: TalkingVariant):
        """Cambia la variante del gesto."""
        if variant == self.variant:
            return
        self.variant = variant
        self.profile = TALKING_VARIANTS[variant].copy()
        self._apply_profile()

    def set_intensity(self, intensity: float):
        """Ajusta la intensidad del gesto (0.0 a 1.0)."""
        self.intensity = self._clamp(intensity, 0.0, 1.0)

    def set_auto_exit(self, enabled: bool, silence_timeout: Optional[float] = None,
                      silence_threshold: Optional[float] = None):
        """Configura la salida automática por silencio."""
        self.auto_exit = enabled
        if silence_timeout is not None:
            self.silence_timeout = max(0.1, silence_timeout)
        if silence_threshold is not None:
            self.silence_threshold = max(0.0, silence_threshold)

    def set_nod_chance(self, chance: float):
        """Ajusta la probabilidad de nodding."""
        self.nod_chance = self._clamp(chance, 0.0, 1.0)

    def set_smoothing(self, rms: Optional[float] = None,
                      pitch: Optional[float] = None,
                      energy: Optional[float] = None,
                      beat: Optional[float] = None):
        """Ajusta los factores de suavizado."""
        if rms is not None:
            self.rms_smoothing = self._clamp(rms, 0.01, 1.0)
        if pitch is not None:
            self.pitch_smoothing = self._clamp(pitch, 0.01, 1.0)
        if energy is not None:
            self.energy_smoothing = self._clamp(energy, 0.01, 1.0)
        if beat is not None:
            self.beat_smoothing = self._clamp(beat, 0.01, 1.0)

    def on_finish(self, callback):
        """Registra un callback al finalizar el gesto."""
        self.on_complete = callback

    def reset(self):
        """Reinicia el gesto."""
        self.variant = TalkingVariant.NORMAL
        self.profile = TALKING_VARIANTS[self.variant].copy()
        self._apply_profile()
        self.active = False
        self.transition = 1.0
        self.silence_elapsed = 0.0
        self.nod_active = False

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_type(self) -> GestureType:
        """Devuelve el tipo de gesto."""
        return self.gesture_type

    def is_active(self) -> bool:
        """Indica si el gesto está activo."""
        return self.active

    def get_signals(self) -> Dict[str, float]:
        """Devuelve las señales de audio suavizadas."""
        return {
            "rms": round(self.rms_smoothed, 4),
            "pitch": round(self.pitch_smoothed, 4),
            "energy": round(self.energy_smoothed, 4),
            "beat": round(self.beat_smoothed, 4),
        }

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del gesto."""
        return {
            "type": self.gesture_type.value,
            "variant": self.variant.value,
            "active": self.active,
            "transition": round(self.transition, 3),
            "intensity": round(self.intensity, 3),
            "priority": self.priority,
            "signals": self.get_signals(),
            "nodding": {
                "active": self.nod_active,
                "progress": round(self.nod_progress, 3),
                "total": self.total_nods,
            },
            "silence": {
                "auto_exit": self.auto_exit,
                "timeout": self.silence_timeout,
                "elapsed": round(self.silence_elapsed, 3),
                "threshold": self.silence_threshold,
            },
            "activations": self.activations,
            "completions": self.completions,
            "updates": self.updates,
        }

    def get_available_variants(self) -> List[str]:
        """Lista las variantes disponibles."""
        return [v.value for v in TalkingVariant]

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