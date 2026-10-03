# app/avatar/head_motion.py

import math
import random
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State, HeadMotionState, AudioFeatures


# =========================================================
# TIPOS DE MOVIMIENTO DE CABEZA
# =========================================================

class HeadMotionMode(Enum):
    """Modos de comportamiento de la cabeza."""
    IDLE = "idle"              # reposo con micro-movimientos
    TALKING = "talking"        # reactivo a la voz
    LISTENING = "listening"    # leve inclinación hacia el interlocutor
    THINKING = "thinking"      # mirada arriba, leve inclinación
    NODDING = "nodding"        # asentimiento
    SHAKING = "shaking"        # negación
    LOOKING = "looking"        # siguiendo un objetivo
    SURPRISED = "surprised"    # sobresalto


# =========================================================
# PERFILES DE MODO
# =========================================================

HEAD_MODE_PROFILES: Dict[HeadMotionMode, Dict[str, float]] = {
    HeadMotionMode.IDLE:       {"amplitude": 0.03, "speed": 0.6, "pitch": 0.00, "yaw": 0.00, "roll": 0.00},
    HeadMotionMode.TALKING:    {"amplitude": 0.08, "speed": 1.6, "pitch": 0.02, "yaw": 0.03, "roll": 0.02},
    HeadMotionMode.LISTENING:  {"amplitude": 0.02, "speed": 0.4, "pitch": 0.06, "yaw": 0.00, "roll": 0.03},
    HeadMotionMode.THINKING:   {"amplitude": 0.02, "speed": 0.3, "pitch": -0.10, "yaw": 0.06, "roll": 0.04},
    HeadMotionMode.NODDING:    {"amplitude": 0.18, "speed": 2.5, "pitch": 0.00, "yaw": 0.00, "roll": 0.00},
    HeadMotionMode.SHAKING:    {"amplitude": 0.15, "speed": 3.0, "pitch": 0.00, "yaw": 0.00, "roll": 0.00},
    HeadMotionMode.LOOKING:    {"amplitude": 0.04, "speed": 1.0, "pitch": 0.00, "yaw": 0.00, "roll": 0.00},
    HeadMotionMode.SURPRISED:  {"amplitude": 0.05, "speed": 2.0, "pitch": -0.15, "yaw": 0.00, "roll": 0.00},
}


# =========================================================
# CONTROLADOR DE CABEZA
# =========================================================

class HeadMotionController:
    """
    Controlador avanzado del movimiento de cabeza de XARION-1.0.
    Gestiona pitch, yaw, roll, seguimiento, nodding, shaking,
    reacción a voz y micro-movimientos automáticos.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Rotaciones objetivo (radianes) ---
        self.rotation_x = 0.0            # pitch: arriba/abajo
        self.rotation_y = 0.0            # yaw: izquierda/derecha
        self.rotation_z = 0.0            # roll: inclinación lateral

        self.target_rotation_x = 0.0
        self.target_rotation_y = 0.0
        self.target_rotation_z = 0.0

        self.tilt_offset = 0.0
        self.target_tilt = 0.0

        # --- Modo actual ---
        self.mode: HeadMotionMode = HeadMotionMode.IDLE
        self.previous_mode: HeadMotionMode = HeadMotionMode.IDLE
        self.mode_blend = 1.0
        self.mode_blend_speed = 3.0

        # --- Fases de oscilación ---
        self.pitch_phase = 0.0
        self.yaw_phase = 0.0
        self.roll_phase = 0.0

        # --- Seguimiento ---
        self.follow_target = False
        self.target_position: Dict[str, float] = {"x": 0.0, "y": 0.0}
        self.follow_strength = 0.6

        # --- Reacción a voz ---
        self.voice_reactive = True
        self.voice_amplitude_scale = 0.15
        self.voice_amp_smoothing = 0.15
        self.last_voice_amplitude = 0.0

        # --- Micro-movimientos ---
        self.micro_motion_enabled = True
        self.micro_motion_amplitude = 0.015
        self.micro_motion_speed = 0.8

        # --- Nodding / Shaking ---
        self._nod_active = False
        self._nod_progress = 0.0
        self._nod_duration = 0.6
        self._nod_count = 1

        self._shake_active = False
        self._shake_progress = 0.0
        self._shake_duration = 0.6
        self._shake_count = 2

        # --- Suavizado ---
        self.smoothing = 0.12
        self.rot_limit_x = 0.35          # ±20°
        self.rot_limit_y = 0.50          # ±28°
        self.rot_limit_z = 0.30          # ±17°

        # --- Estadísticas ---
        self.updates = 0
        self.mode_changes = 0
        self.last_update = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el estado interno de la cabeza."""
        self.rotation_x = self.rotation_y = self.rotation_z = 0.0
        self.target_rotation_x = self.target_rotation_y = self.target_rotation_z = 0.0
        self.pitch_phase = random.uniform(0.0, math.tau)
        self.yaw_phase = random.uniform(0.0, math.tau)
        self.roll_phase = random.uniform(0.0, math.tau)
        self.last_update = time.time()

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """Actualiza la cabeza cada frame."""
        self.updates += 1

        # 1. Blending entre modos
        self._update_mode_blend(delta)

        # 2. Reacción a la voz
        if self.voice_reactive and state.audio.state.value == "playing":
            self._react_to_voice(state.audio.features, delta)

        # 3. Seguimiento de objetivo
        if self.follow_target:
            self._update_follow()

        # 4. Oscilación base según modo
        self._apply_mode_oscillation(delta)

        # 5. Nodding / Shaking activos
        if self._nod_active:
            self._update_nod(delta)
        if self._shake_active:
            self._update_shake(delta)

        # 6. Micro-movimientos
        if self.micro_motion_enabled:
            self._apply_micro_motion(delta)

        # 7. Suavizado hacia objetivos
        self.rotation_x = self._smooth(self.rotation_x, self.target_rotation_x, self.smoothing)
        self.rotation_y = self._smooth(self.rotation_y, self.target_rotation_y, self.smoothing)
        self.rotation_z = self._smooth(self.rotation_z, self.target_rotation_z, self.smoothing)
        self.tilt_offset = self._smooth(self.tilt_offset, self.target_tilt, self.smoothing)

        # 8. Límites
        self.rotation_x = self._clamp(self.rotation_x, -self.rot_limit_x, self.rot_limit_x)
        self.rotation_y = self._clamp(self.rotation_y, -self.rot_limit_y, self.rot_limit_y)
        self.rotation_z = self._clamp(self.rotation_z, -self.rot_limit_z, self.rot_limit_z)

        # 9. Volcar al estado global
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
        """Ajusta la cabeza según la amplitud de voz."""
        if features is None:
            return

        rms = self._clamp(features.rms * 4.0, 0.0, 1.0)
        self.last_voice_amplitude = self._smooth(
            self.last_voice_amplitude, rms, self.voice_amp_smoothing
        )

        # Movimiento reactivo a la voz
        amp = self.last_voice_amplitude * self.voice_amplitude_scale
        self.target_rotation_x += math.sin(self.pitch_phase) * amp
        self.target_rotation_y += math.cos(self.yaw_phase) * amp * 0.7

        # Si hay beat fuerte, pequeño cabeceo
        if features.beat_detected and features.beat_strength > 0.5:
            self.target_rotation_x -= features.beat_strength * 0.05

    # =====================================================
    # SEGUIMIENTO
    # =====================================================

    def _update_follow(self):
        """Ajusta la rotación hacia el objetivo."""
        tx = self._clamp(self.target_position.get("x", 0.0), -1.0, 1.0)
        ty = self._clamp(self.target_position.get("y", 0.0), -1.0, 1.0)

        self.target_rotation_y = tx * self.rot_limit_y * self.follow_strength
        self.target_rotation_x = -ty * self.rot_limit_x * self.follow_strength

    # =====================================================
    # OSCILACIÓN BASE POR MODO
    # =====================================================

    def _apply_mode_oscillation(self, delta: float):
        """Aplica oscilación suave según el modo actual."""
        profile = HEAD_MODE_PROFILES.get(self.mode, HEAD_MODE_PROFILES[HeadMotionMode.IDLE])

        speed = profile["speed"]
        amp = profile["amplitude"]

        # Avanzar fases
        self.pitch_phase += delta * speed * 1.1
        self.yaw_phase += delta * speed * 0.9
        self.roll_phase += delta * speed * 0.7

        # Oscilación base
        self.target_rotation_x += math.sin(self.pitch_phase) * amp
        self.target_rotation_y += math.sin(self.yaw_phase) * amp
        self.target_rotation_z += math.sin(self.roll_phase) * amp * 0.5

        # Offset fijo del modo
        self.target_rotation_x += profile["pitch"]
        self.target_rotation_y += profile["yaw"]
        self.target_rotation_z += profile["roll"]

    # =====================================================
    # NODDING
    # =====================================================

    def _update_nod(self, delta: float):
        """Asentimiento con la cabeza."""
        self._nod_progress += delta / self._nod_duration
        t = self._nod_progress

        if t >= 1.0:
            self._nod_active = False
            self._nod_progress = 0.0
            return

        amp = HEAD_MODE_PROFILES[HeadMotionMode.NODDING]["amplitude"]
        cycle = t * self._nod_count
        self.target_rotation_x = math.sin(cycle * math.tau) * amp

    # =====================================================
    # SHAKING
    # =====================================================

    def _update_shake(self, delta: float):
        """Negación con la cabeza."""
        self._shake_progress += delta / self._shake_duration
        t = self._shake_progress

        if t >= 1.0:
            self._shake_active = False
            self._shake_progress = 0.0
            return

        amp = HEAD_MODE_PROFILES[HeadMotionMode.SHAKING]["amplitude"]
        cycle = t * self._shake_count
        self.target_rotation_y = math.sin(cycle * math.tau) * amp

    # =====================================================
    # MICRO-MOVIMIENTOS
    # =====================================================

    def _apply_micro_motion(self, delta: float):
        """Añade micro-vibraciones orgánicas."""
        t = time.time() * self.micro_motion_speed
        a = self.micro_motion_amplitude

        self.target_rotation_x += math.sin(t * 1.7) * a
        self.target_rotation_y += math.sin(t * 1.3 + 1.1) * a
        self.target_rotation_z += math.sin(t * 0.9 + 2.2) * a * 0.6

    # =====================================================
    # ESCRITURA AL ESTADO
    # =====================================================

    def _write_to_state(self, state: State):
        """Escribe los valores internos en el estado global."""
        head = state.avatar_components.head
        head.rotation_x = self.rotation_x
        head.rotation_y = self.rotation_y
        head.rotation_z = self.rotation_z
        head.tilt_offset = self.tilt_offset
        head.nod_speed = HEAD_MODE_PROFILES[self.mode]["speed"]
        head.follow_audio = self.voice_reactive
        head.follow_target = self.follow_target
        head.target_position = dict(self.target_position)

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def set_mode(self, mode: HeadMotionMode):
        """Cambia el modo de movimiento de la cabeza."""
        if mode == self.mode:
            return
        self.previous_mode = self.mode
        self.mode = mode
        self.mode_blend = 0.0
        self.mode_changes += 1

    def nod(self, count: int = 1, duration: float = 0.6):
        """Inicia un asentimiento."""
        self._nod_active = True
        self._nod_progress = 0.0
        self._nod_count = max(1, count)
        self._nod_duration = max(0.2, duration)

    def shake(self, count: int = 2, duration: float = 0.6):
        """Inicia una negación con la cabeza."""
        self._shake_active = True
        self._shake_progress = 0.0
        self._shake_count = max(1, count)
        self._shake_duration = max(0.2, duration)

    def look_at(self, x: float, y: float):
        """Define la posición objetivo de la mirada (normalizada)."""
        self.target_position = {
            "x": self._clamp(x, -1.0, 1.0),
            "y": self._clamp(y, -1.0, 1.0),
        }

    def enable_follow(self, enabled: bool = True, strength: float = 0.6):
        """Activa o desactiva el seguimiento de objetivo."""
        self.follow_target = enabled
        self.follow_strength = self._clamp(strength, 0.0, 1.0)

    def set_rotation(self, x: float, y: float, z: float, instant: bool = False):
        """Fija rotaciones concretas (radianes)."""
        x = self._clamp(x, -self.rot_limit_x, self.rot_limit_x)
        y = self._clamp(y, -self.rot_limit_y, self.rot_limit_y)
        z = self._clamp(z, -self.rot_limit_z, self.rot_limit_z)
        if instant:
            self.rotation_x, self.rotation_y, self.rotation_z = x, y, z
        self.target_rotation_x, self.target_rotation_y, self.target_rotation_z = x, y, z

    def set_tilt(self, offset: float):
        """Ajusta la inclinación adicional (roll base)."""
        self.target_tilt = self._clamp(offset, -0.3, 0.3)

    def set_smoothing(self, value: float):
        """Ajusta el suavizado (0.01 a 1.0)."""
        self.smoothing = self._clamp(value, 0.01, 1.0)

    def enable_voice_reactive(self, enabled: bool = True, scale: float = 0.15):
        """Activa o desactiva la reacción a la voz."""
        self.voice_reactive = enabled
        self.voice_amplitude_scale = self._clamp(scale, 0.0, 1.0)

    def enable_micro_motion(self, enabled: bool = True, amplitude: float = 0.015):
        """Activa o desactiva los micro-movimientos orgánicos."""
        self.micro_motion_enabled = enabled
        self.micro_motion_amplitude = self._clamp(amplitude, 0.0, 0.1)

    def reset(self):
        """Reinicia la cabeza a reposo."""
        self.rotation_x = self.rotation_y = self.rotation_z = 0.0
        self.target_rotation_x = self.target_rotation_y = self.target_rotation_z = 0.0
        self.tilt_offset = 0.0
        self.target_tilt = 0.0
        self.mode = HeadMotionMode.IDLE
        self._nod_active = False
        self._shake_active = False

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_state(self) -> HeadMotionState:
        """Devuelve el estado actual de la cabeza."""
        return HeadMotionState(
            rotation_x=self.rotation_x,
            rotation_y=self.rotation_y,
            rotation_z=self.rotation_z,
            tilt_offset=self.tilt_offset,
            nod_speed=HEAD_MODE_PROFILES[self.mode]["speed"],
            follow_audio=self.voice_reactive,
            follow_target=self.follow_target,
            target_position=dict(self.target_position),
        )

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "mode": self.mode.value,
            "previous_mode": self.previous_mode.value,
            "mode_blend": round(self.mode_blend, 3),
            "rotation": (
                round(self.rotation_x, 4),
                round(self.rotation_y, 4),
                round(self.rotation_z, 4),
            ),
            "target_rotation": (
                round(self.target_rotation_x, 4),
                round(self.target_rotation_y, 4),
                round(self.target_rotation_z, 4),
            ),
            "tilt": round(self.tilt_offset, 4),
            "follow_target": self.follow_target,
            "voice_reactive": self.voice_reactive,
            "last_voice_amplitude": round(self.last_voice_amplitude, 4),
            "nodding": self._nod_active,
            "shaking": self._shake_active,
            "mode_changes": self.mode_changes,
            "updates": self.updates,
        }

    def get_available_modes(self) -> List[str]:
        """Lista los modos disponibles."""
        return [m.value for m in HeadMotionMode]

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