# app/avatar/body_motion.py

import math
import random
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State, BodyMotionState, AudioFeatures


# =========================================================
# MODOS DE CUERPO
# =========================================================

class BodyMotionMode(Enum):
    """Modos de comportamiento del cuerpo."""
    IDLE = "idle"              # reposo con respiración y balanceo
    TALKING = "talking"        # reactivo a la voz
    LISTENING = "listening"    # ligera inclinación hacia adelante
    THINKING = "thinking"      # leve balanceo lateral
    EMPHASIS = "emphasis"      # énfasis al hablar
    EXCITED = "excited"        # energía alta
    TIRED = "tired"            # movimiento lento
    SURPRISED = "surprised"    # reacción rápida
    RECORDING = "recording"    # modo grabación (movimiento contenido)


# =========================================================
# PERFILES POR MODO
# =========================================================

BODY_MODE_PROFILES: Dict[BodyMotionMode, Dict[str, float]] = {
    BodyMotionMode.IDLE:      {"breathe_amp": 0.020, "breathe_speed": 0.9, "sway_amp": 0.008, "sway_speed": 0.5, "bounce_amp": 0.000, "lean": 0.00, "energy": 0.4},
    BodyMotionMode.TALKING:   {"breathe_amp": 0.025, "breathe_speed": 1.2, "sway_amp": 0.015, "sway_speed": 1.1, "bounce_amp": 0.010, "lean": 0.02, "energy": 0.9},
    BodyMotionMode.LISTENING: {"breathe_amp": 0.018, "breathe_speed": 0.8, "sway_amp": 0.005, "sway_speed": 0.4, "bounce_amp": 0.000, "lean": 0.05, "energy": 0.3},
    BodyMotionMode.THINKING:  {"breathe_amp": 0.020, "breathe_speed": 0.7, "sway_amp": 0.012, "sway_speed": 0.6, "bounce_amp": 0.000, "lean": -0.02, "energy": 0.4},
    BodyMotionMode.EMPHASIS:  {"breathe_amp": 0.030, "breathe_speed": 1.4, "sway_amp": 0.020, "sway_speed": 1.6, "bounce_amp": 0.018, "lean": 0.03, "energy": 1.2},
    BodyMotionMode.EXCITED:   {"breathe_amp": 0.035, "breathe_speed": 2.0, "sway_amp": 0.030, "sway_speed": 2.2, "bounce_amp": 0.030, "lean": 0.02, "energy": 1.6},
    BodyMotionMode.TIRED:     {"breathe_amp": 0.015, "breathe_speed": 0.5, "sway_amp": 0.004, "sway_speed": 0.3, "bounce_amp": 0.000, "lean": 0.06, "energy": 0.2},
    BodyMotionMode.SURPRISED: {"breathe_amp": 0.040, "breathe_speed": 2.5, "sway_amp": 0.010, "sway_speed": 2.5, "bounce_amp": 0.035, "lean": -0.05, "energy": 1.8},
    BodyMotionMode.RECORDING: {"breathe_amp": 0.018, "breathe_speed": 0.9, "sway_amp": 0.006, "sway_speed": 0.5, "bounce_amp": 0.000, "lean": 0.01, "energy": 0.5},
}


# =========================================================
# CONTROLADOR DE CUERPO
# =========================================================

class BodyMotionController:
    """
    Controlador avanzado del movimiento corporal de XARION-1.0.
    Gestiona respiración, balanceo, rebote, inclinación, posición,
    rotación, escala y reacción al audio.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Posición ---
        self.position_x = 0.0
        self.position_y = 0.0
        self.position_z = 0.0

        self.target_position_x = 0.0
        self.target_position_y = 0.0
        self.target_position_z = 0.0

        # --- Rotación ---
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0

        self.target_rotation_x = 0.0
        self.target_rotation_y = 0.0
        self.target_rotation_z = 0.0

        # --- Escala ---
        self.scale = 1.0
        self.target_scale = 1.0

        # --- Modo ---
        self.mode: BodyMotionMode = BodyMotionMode.IDLE
        self.previous_mode: BodyMotionMode = BodyMotionMode.IDLE
        self.mode_blend = 1.0
        self.mode_blend_speed = 2.5

        # --- Fases ---
        self.breathe_phase = 0.0
        self.sway_phase = 0.0
        self.bounce_phase = 0.0
        self.extra_phase = 0.0

        # --- Respiración ---
        self.breathing_amplitude = BODY_MODE_PROFILES[BodyMotionMode.IDLE]["breathe_amp"]
        self.breathing_speed = BODY_MODE_PROFILES[BodyMotionMode.IDLE]["breathe_speed"]

        # --- Balanceo ---
        self.sway_amplitude = BODY_MODE_PROFILES[BodyMotionMode.IDLE]["sway_amp"]
        self.sway_speed = BODY_MODE_PROFILES[BodyMotionMode.IDLE]["sway_speed"]

        # --- Rebote ---
        self.bounce_amplitude = 0.0

        # --- Inclinación base ---
        self.lean_offset = 0.0
        self.target_lean = 0.0

        # --- Reacción a voz ---
        self.voice_reactive = True
        self.voice_amplitude_scale = 0.20
        self.voice_smoothing = 0.18
        self.last_voice_amplitude = 0.0

        # --- Reacción a beats ---
        self.beat_reactive = True
        self.beat_punch = 0.0
        self.beat_decay = 6.0

        # --- Micro-movimientos ---
        self.micro_motion_enabled = True
        self.micro_motion_amplitude = 0.003
        self.micro_motion_speed = 1.2

        # --- Suavizado ---
        self.position_smoothing = 0.14
        self.rotation_smoothing = 0.14
        self.scale_smoothing = 0.10

        # --- Límites ---
        self.pos_limit_x = 0.15
        self.pos_limit_y = 0.10
        self.pos_limit_z = 0.10
        self.rot_limit_x = 0.10
        self.rot_limit_y = 0.15
        self.rot_limit_z = 0.10
        self.scale_min = 0.85
        self.scale_max = 1.15

        # --- Estadísticas ---
        self.updates = 0
        self.mode_changes = 0
        self.last_update = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el estado interno del cuerpo."""
        self.breathe_phase = random.uniform(0.0, math.tau)
        self.sway_phase = random.uniform(0.0, math.tau)
        self.bounce_phase = random.uniform(0.0, math.tau)
        self.extra_phase = random.uniform(0.0, math.tau)
        self.last_update = time.time()

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """Actualiza el cuerpo cada frame."""
        self.updates += 1

        # 1. Blending de modo
        self._update_mode_blend(delta)

        # 2. Reacción al audio
        if self.voice_reactive and state.audio.state.value == "playing":
            self._react_to_voice(state.audio.features, delta)

        # 3. Reacción a beats
        if self.beat_reactive:
            self._update_beat_punch(delta)

        # 4. Oscilación base del modo
        self._apply_mode_oscillation(delta)

        # 5. Micro-movimientos
        if self.micro_motion_enabled:
            self._apply_micro_motion(delta)

        # 6. Suavizado
        self.position_x = self._smooth(self.position_x, self.target_position_x, self.position_smoothing)
        self.position_y = self._smooth(self.position_y, self.target_position_y, self.position_smoothing)
        self.position_z = self._smooth(self.position_z, self.target_position_z, self.position_smoothing)

        self.rotation_x = self._smooth(self.rotation_x, self.target_rotation_x, self.rotation_smoothing)
        self.rotation_y = self._smooth(self.rotation_y, self.target_rotation_y, self.rotation_smoothing)
        self.rotation_z = self._smooth(self.rotation_z, self.target_rotation_z, self.rotation_smoothing)

        self.scale = self._smooth(self.scale, self.target_scale, self.scale_smoothing)
        self.lean_offset = self._smooth(self.lean_offset, self.target_lean, self.rotation_smoothing)

        # 7. Límites
        self._apply_limits()

        # 8. Volcar al estado global
        self._write_to_state(state)
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
    # REACCIÓN A VOZ
    # =====================================================

    def _react_to_voice(self, features: AudioFeatures, delta: float):
        """Ajusta el cuerpo según la amplitud de voz."""
        if features is None:
            return

        rms = self._clamp(features.rms * 4.0, 0.0, 1.0)
        self.last_voice_amplitude = self._smooth(
            self.last_voice_amplitude, rms, self.voice_smoothing
        )

        # Rebote sutil reactivo a la voz
        amp = self.last_voice_amplitude * self.voice_amplitude_scale
        self.target_position_y += math.sin(self.bounce_phase) * amp * 0.5
        self.target_rotation_z += math.sin(self.sway_phase) * amp * 0.4

    # =====================================================
    # BEAT PUNCH
    # =====================================================

    def _update_beat_punch(self, delta: float):
        """Golpe de beat que decae con el tiempo."""
        if self.beat_punch > 0.0:
            self.beat_punch = max(0.0, self.beat_punch - delta * self.beat_decay)
        self.target_position_y += self.beat_punch * 0.02
        self.target_scale += self.beat_punch * 0.01

    def trigger_beat(self, strength: float = 1.0):
        """Dispara un golpe de beat manualmente."""
        self.beat_punch = self._clamp(strength, 0.0, 1.0)

    # =====================================================
    # OSCILACIÓN BASE
    # =====================================================

    def _apply_mode_oscillation(self, delta: float):
        """Aplica respiración, balanceo y rebote según el modo."""
        profile = BODY_MODE_PROFILES.get(self.mode, BODY_MODE_PROFILES[BodyMotionMode.IDLE])

        # Actualizar parámetros según modo
        self.breathing_amplitude = profile["breathe_amp"]
        self.breathing_speed = profile["breathe_speed"]
        self.sway_amplitude = profile["sway_amp"]
        self.sway_speed = profile["sway_speed"]
        self.bounce_amplitude = profile["bounce_amp"]
        self.target_lean = profile["lean"]

        # Avanzar fases
        self.breathe_phase += delta * self.breathing_speed * math.tau
        self.sway_phase += delta * self.sway_speed * math.tau
        self.bounce_phase += delta * self.breathing_speed * 1.5 * math.tau

        # Respiración (movimiento vertical suave)
        breathe = math.sin(self.breathe_phase) * self.breathing_amplitude
        self.target_position_y += breathe

        # Balanceo lateral (movimiento horizontal)
        sway = math.sin(self.sway_phase) * self.sway_amplitude
        self.target_position_x += sway
        self.target_rotation_z += sway * 0.5

        # Rebote (micro-salto suave)
        bounce = abs(math.sin(self.bounce_phase)) * self.bounce_amplitude
        self.target_position_y += bounce

        # Inclinación acumulada
        self.target_rotation_x += self.lean_offset * 0.3

    # =====================================================
    # MICRO-MOVIMIENTOS
    # =====================================================

    def _apply_micro_motion(self, delta: float):
        """Añade micro-vibraciones orgánicas."""
        t = time.time() * self.micro_motion_speed
        a = self.micro_motion_amplitude

        self.target_position_x += math.sin(t * 1.4) * a
        self.target_position_y += math.sin(t * 1.1 + 0.8) * a * 0.7
        self.target_rotation_z += math.sin(t * 0.9 + 1.7) * a * 2.0

    # =====================================================
    # LÍMITES
    # =====================================================

    def _apply_limits(self):
        """Aplica límites a posición, rotación y escala."""
        self.position_x = self._clamp(self.position_x, -self.pos_limit_x, self.pos_limit_x)
        self.position_y = self._clamp(self.position_y, -self.pos_limit_y, self.pos_limit_y)
        self.position_z = self._clamp(self.position_z, -self.pos_limit_z, self.pos_limit_z)

        self.rotation_x = self._clamp(self.rotation_x, -self.rot_limit_x, self.rot_limit_x)
        self.rotation_y = self._clamp(self.rotation_y, -self.rot_limit_y, self.rot_limit_y)
        self.rotation_z = self._clamp(self.rotation_z, -self.rot_limit_z, self.rot_limit_z)

        self.scale = self._clamp(self.scale, self.scale_min, self.scale_max)

    # =====================================================
    # ESCRITURA AL ESTADO
    # =====================================================

    def _write_to_state(self, state: State):
        """Escribe los valores internos en el estado global."""
        body = state.avatar_components.body
        body.position_x = self.position_x
        body.position_y = self.position_y
        body.position_z = self.position_z
        body.rotation_x = self.rotation_x
        body.rotation_y = self.rotation_y
        body.rotation_z = self.rotation_z
        body.scale = self.scale
        body.breathing_phase = self.breathe_phase
        body.breathing_amplitude = self.breathing_amplitude
        body.sway_phase = self.sway_phase

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def set_mode(self, mode: BodyMotionMode):
        """Cambia el modo de movimiento corporal."""
        if mode == self.mode:
            return
        self.previous_mode = self.mode
        self.mode = mode
        self.mode_blend = 0.0
        self.mode_changes += 1

    def set_position(self, x: float, y: float, z: float = 0.0, instant: bool = False):
        """Fija la posición del cuerpo."""
        x = self._clamp(x, -self.pos_limit_x, self.pos_limit_x)
        y = self._clamp(y, -self.pos_limit_y, self.pos_limit_y)
        z = self._clamp(z, -self.pos_limit_z, self.pos_limit_z)
        if instant:
            self.position_x, self.position_y, self.position_z = x, y, z
        self.target_position_x, self.target_position_y, self.target_position_z = x, y, z

    def set_rotation(self, x: float, y: float, z: float, instant: bool = False):
        """Fija la rotación del cuerpo."""
        x = self._clamp(x, -self.rot_limit_x, self.rot_limit_x)
        y = self._clamp(y, -self.rot_limit_y, self.rot_limit_y)
        z = self._clamp(z, -self.rot_limit_z, self.rot_limit_z)
        if instant:
            self.rotation_x, self.rotation_y, self.rotation_z = x, y, z
        self.target_rotation_x, self.target_rotation_y, self.target_rotation_z = x, y, z

    def set_scale(self, value: float, instant: bool = False):
        """Ajusta la escala del cuerpo."""
        value = self._clamp(value, self.scale_min, self.scale_max)
        if instant:
            self.scale = value
        self.target_scale = value

    def set_lean(self, value: float):
        """Ajusta la inclinación base hacia adelante/atrás."""
        self.target_lean = self._clamp(value, -self.rot_limit_x, self.rot_limit_x)

    def set_smoothing(self, position: Optional[float] = None,
                      rotation: Optional[float] = None,
                      scale: Optional[float] = None):
        """Ajusta factores de suavizado."""
        if position is not None:
            self.position_smoothing = self._clamp(position, 0.01, 1.0)
        if rotation is not None:
            self.rotation_smoothing = self._clamp(rotation, 0.01, 1.0)
        if scale is not None:
            self.scale_smoothing = self._clamp(scale, 0.01, 1.0)

    def enable_voice_reactive(self, enabled: bool = True, scale: float = 0.20):
        """Activa o desactiva la reacción a la voz."""
        self.voice_reactive = enabled
        self.voice_amplitude_scale = self._clamp(scale, 0.0, 1.0)

    def enable_beat_reactive(self, enabled: bool = True):
        """Activa o desactiva la reacción a beats."""
        self.beat_reactive = enabled

    def enable_micro_motion(self, enabled: bool = True, amplitude: float = 0.003):
        """Activa o desactiva los micro-movimientos."""
        self.micro_motion_enabled = enabled
        self.micro_motion_amplitude = self._clamp(amplitude, 0.0, 0.02)

    def reset(self):
        """Reinicia el cuerpo a reposo."""
        self.position_x = self.position_y = self.position_z = 0.0
        self.target_position_x = self.target_position_y = self.target_position_z = 0.0
        self.rotation_x = self.rotation_y = self.rotation_z = 0.0
        self.target_rotation_x = self.target_rotation_y = self.target_rotation_z = 0.0
        self.scale = 1.0
        self.target_scale = 1.0
        self.lean_offset = 0.0
        self.target_lean = 0.0
        self.beat_punch = 0.0
        self.mode = BodyMotionMode.IDLE

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_state(self) -> BodyMotionState:
        """Devuelve el estado actual del cuerpo."""
        return BodyMotionState(
            position_x=self.position_x,
            position_y=self.position_y,
            position_z=self.position_z,
            rotation_x=self.rotation_x,
            rotation_y=self.rotation_y,
            rotation_z=self.rotation_z,
            scale=self.scale,
            breathing_phase=self.breathe_phase,
            breathing_amplitude=self.breathing_amplitude,
            sway_phase=self.sway_phase,
        )

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "mode": self.mode.value,
            "previous_mode": self.previous_mode.value,
            "mode_blend": round(self.mode_blend, 3),
            "position": (
                round(self.position_x, 4),
                round(self.position_y, 4),
                round(self.position_z, 4),
            ),
            "rotation": (
                round(self.rotation_x, 4),
                round(self.rotation_y, 4),
                round(self.rotation_z, 4),
            ),
            "scale": round(self.scale, 4),
            "lean": round(self.lean_offset, 4),
            "breathing": {
                "amplitude": round(self.breathing_amplitude, 4),
                "phase": round(self.breathe_phase, 3),
            },
            "voice_reactive": self.voice_reactive,
            "last_voice_amplitude": round(self.last_voice_amplitude, 4),
            "beat_punch": round(self.beat_punch, 3),
            "mode_changes": self.mode_changes,
            "updates": self.updates,
        }

    def get_available_modes(self) -> List[str]:
        """Lista los modos disponibles."""
        return [m.value for m in BodyMotionMode]

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