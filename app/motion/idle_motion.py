# app/motion/idle_motion.py

import math
import random
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State


# =========================================================
# MODOS DE REPOSO
# =========================================================

class IdleMode(Enum):
    """Modos de reposo disponibles."""
    CALM = "calm"               # tranquilo, movimientos lentos
    CURIOUS = "curious"         # curioso, gira ligeramente la cabeza
    SLEEPY = "sleepy"           # somnoliento, movimientos mínimos
    ENERGETIC = "energetic"     # enérgico, más movimiento
    FOCUSED = "focused"         # concentrado, casi inmóvil
    BREATHING = "breathing"     # solo respiración


# =========================================================
# PERFILES POR MODO
# =========================================================

IDLE_MODE_PROFILES: Dict[IdleMode, Dict[str, float]] = {
    IdleMode.CALM:      {"breath_amp": 0.020, "breath_speed": 0.9, "head_amp": 0.010, "head_speed": 0.4, "sway_amp": 0.008, "sway_speed": 0.5, "blink_rate": 1.0, "micro_amp": 0.002},
    IdleMode.CURIOUS:   {"breath_amp": 0.022, "breath_speed": 1.0, "head_amp": 0.030, "head_speed": 0.7, "sway_amp": 0.010, "sway_speed": 0.6, "blink_rate": 1.2, "micro_amp": 0.003},
    IdleMode.SLEEPY:    {"breath_amp": 0.012, "breath_speed": 0.5, "head_amp": 0.005, "head_speed": 0.2, "sway_amp": 0.004, "sway_speed": 0.3, "blink_rate": 0.6, "micro_amp": 0.001},
    IdleMode.ENERGETIC: {"breath_amp": 0.030, "breath_speed": 1.6, "head_amp": 0.025, "head_speed": 1.2, "sway_amp": 0.018, "sway_speed": 1.0, "blink_rate": 1.4, "micro_amp": 0.004},
    IdleMode.FOCUSED:   {"breath_amp": 0.015, "breath_speed": 0.8, "head_amp": 0.003, "head_speed": 0.2, "sway_amp": 0.002, "sway_speed": 0.2, "blink_rate": 0.8, "micro_amp": 0.001},
    IdleMode.BREATHING: {"breath_amp": 0.025, "breath_speed": 0.9, "head_amp": 0.000, "head_speed": 0.0, "sway_amp": 0.000, "sway_speed": 0.0, "blink_rate": 1.0, "micro_amp": 0.000},
}


# =========================================================
# CONTROLADOR DE REPOSO
# =========================================================

class IdleMotionController:
    """
    Controlador de movimiento en reposo de XARION-1.0.
    Genera movimiento orgánico constante cuando el avatar
    no está hablando: respiración, balanceo, micro-mirada,
    pequeños giros de cabeza, parpadeo natural y micro-vibración.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Modo activo ---
        self.mode: IdleMode = IdleMode.CALM
        self.profile: Dict[str, float] = IDLE_MODE_PROFILES[self.mode].copy()

        # --- Fases internas ---
        self.breath_phase: float = 0.0
        self.head_phase_x: float = 0.0
        self.head_phase_y: float = 0.0
        self.sway_phase: float = 0.0
        self.micro_phase: float = 0.0

        # --- Look aleatorio de reposo ---
        self.look_target_x: float = 0.0
        self.look_target_y: float = 0.0
        self.next_look_time: float = 0.0
        self.look_interval_min: float = 2.0
        self.look_interval_max: float = 5.0
        self.look_amplitude: float = 0.15

        # --- Blink trigger ---
        self.blink_callback = None

        # --- Parámetros actuales ---
        self.breath_amp: float = self.profile["breath_amp"]
        self.breath_speed: float = self.profile["breath_speed"]
        self.head_amp: float = self.profile["head_amp"]
        self.head_speed: float = self.profile["head_speed"]
        self.sway_amp: float = self.profile["sway_amp"]
        self.sway_speed: float = self.profile["sway_speed"]
        self.micro_amp: float = self.profile["micro_amp"]
        self.blink_rate: float = self.profile["blink_rate"]

        # --- Intensidad global ---
        self.intensity: float = 1.0

        # --- Backends ---
        self.blink_controller = None
        self.eyes_controller = None

        # --- Estado ---
        self.enabled: bool = True
        self.suspended: bool = False

        # --- Estadísticas ---
        self.updates: int = 0
        self.look_changes: int = 0
        self.last_update: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa fases y programa el primer look aleatorio."""
        self.breath_phase = random.uniform(0.0, math.tau)
        self.head_phase_x = random.uniform(0.0, math.tau)
        self.head_phase_y = random.uniform(0.0, math.tau)
        self.sway_phase = random.uniform(0.0, math.tau)
        self.micro_phase = random.uniform(0.0, math.tau)
        self._schedule_next_look()
        self.last_update = time.time()

    def register(self, name: str, module: Any):
        """Registra submódulos (blink, eyes)."""
        if name == "blink":
            self.blink_controller = module
        elif name == "eyes":
            self.eyes_controller = module

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """Actualiza el movimiento de reposo cada frame."""
        if not self.enabled or self.suspended:
            return

        self.updates += 1
        now = time.time()

        # 1. Avanzar fases
        self._advance_phases(delta)

        # 2. Aplicar respiración
        self._apply_breathing(state)

        # 3. Aplicar balanceo y micro-movimiento
        self._apply_body_sway(state)

        # 4. Aplicar movimiento sutil de cabeza
        self._apply_head_motion(state)

        # 5. Actualizar mirada aleatoria
        self._update_random_look(now, state)

        # 6. Disparar parpadeo natural
        self._maybe_blink(now)

        self.last_update = now

    # =====================================================
    # FASES
    # =====================================================

    def _advance_phases(self, delta: float):
        """Avanza todas las fases internas."""
        self.breath_phase += delta * self.breath_speed * math.tau
        self.head_phase_x += delta * self.head_speed * math.tau * 0.7
        self.head_phase_y += delta * self.head_speed * math.tau * 0.5
        self.sway_phase += delta * self.sway_speed * math.tau
        self.micro_phase += delta * 4.0 * math.tau

    # =====================================================
    # RESPIRACIÓN
    # =====================================================

    def _apply_breathing(self, state: State):
        """Aplica respiración al cuerpo del avatar."""
        breath = math.sin(self.breath_phase) * self.breath_amp * self.intensity
        body = state.avatar_components.body

        body.breathing_phase = self.breath_phase
        body.breathing_amplitude = self.breath_amp * self.intensity
        body.position_y += breath

    # =====================================================
    # BALANCEO CORPORAL
    # =====================================================

    def _apply_body_sway(self, state: State):
        """Aplica balanceo lateral y micro-vibración al cuerpo."""
        body = state.avatar_components.body

        sway = math.sin(self.sway_phase) * self.sway_amp * self.intensity
        body.position_x += sway
        body.rotation_z += sway * 0.3

        if self.micro_amp > 0.0:
            micro_x = math.sin(self.micro_phase * 1.7) * self.micro_amp * self.intensity
            micro_y = math.sin(self.micro_phase * 1.3 + 1.1) * self.micro_amp * self.intensity
            body.position_x += micro_x
            body.position_y += micro_y

        body.sway_phase = self.sway_phase

    # =====================================================
    # MOVIMIENTO DE CABEZA
    # =====================================================

    def _apply_head_motion(self, state: State):
        """Aplica micro-movimiento natural a la cabeza."""
        if self.head_amp <= 0.0:
            return

        head = state.avatar_components.head

        rx = math.sin(self.head_phase_x) * self.head_amp * self.intensity
        ry = math.sin(self.head_phase_y) * self.head_amp * self.intensity
        rz = math.sin(self.head_phase_x * 0.5) * self.head_amp * 0.5 * self.intensity

        head.rotation_x += rx
        head.rotation_y += ry
        head.rotation_z += rz

    # =====================================================
    # MIRADA ALEATORIA
    # =====================================================

    def _update_random_look(self, now: float, state: State):
        """Programa y aplica cambios sutiles de mirada."""
        if now >= self.next_look_time:
            self._schedule_next_look()
            self.look_target_x = random.uniform(
                -self.look_amplitude, self.look_amplitude
            )
            self.look_target_y = random.uniform(
                -self.look_amplitude * 0.5, self.look_amplitude * 0.5
            )
            self.look_changes += 1

        # Aplicar a ojos si tenemos controlador
        if self.eyes_controller is not None:
            if hasattr(self.eyes_controller, "set_target_position"):
                self.eyes_controller.set_target_position(
                    self.look_target_x, self.look_target_y
                )
        else:
            # Aplicar directamente al estado
            eyes = state.avatar_components.eyes
            eyes.look_x += (self.look_target_x - eyes.look_x) * 0.05
            eyes.look_y += (self.look_target_y - eyes.look_y) * 0.05

    def _schedule_next_look(self):
        """Programa el siguiente cambio de mirada."""
        interval = random.uniform(self.look_interval_min, self.look_interval_max)
        self.next_look_time = time.time() + interval

    # =====================================================
    # PARPADEO
    # =====================================================

    def _maybe_blink(self, now: float):
        """Dispara parpadeos naturales si el blink_controller lo permite."""
        if self.blink_controller is None:
            return

        # Ajustar intervalo según blink_rate
        if hasattr(self.blink_controller, "set_interval"):
            base_min = self.config.BLINK_INTERVAL_MIN / max(0.1, self.blink_rate)
            base_max = self.config.BLINK_INTERVAL_MAX / max(0.1, self.blink_rate)
            self.blink_controller.set_interval(base_min, base_max)

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def set_mode(self, mode: IdleMode):
        """Cambia el modo de reposo."""
        if mode == self.mode:
            return
        self.mode = mode
        self.profile = IDLE_MODE_PROFILES[mode].copy()
        self._apply_profile()

    def _apply_profile(self):
        """Aplica el perfil actual a los parámetros internos."""
        self.breath_amp = self.profile["breath_amp"]
        self.breath_speed = self.profile["breath_speed"]
        self.head_amp = self.profile["head_amp"]
        self.head_speed = self.profile["head_speed"]
        self.sway_amp = self.profile["sway_amp"]
        self.sway_speed = self.profile["sway_speed"]
        self.micro_amp = self.profile["micro_amp"]
        self.blink_rate = self.profile["blink_rate"]

    def set_intensity(self, intensity: float):
        """Ajusta la intensidad global del reposo."""
        self.intensity = self._clamp(intensity, 0.0, 2.0)

    def set_look_interval(self, min_s: float, max_s: float):
        """Ajusta el rango de intervalos entre cambios de mirada."""
        self.look_interval_min = max(0.5, min_s)
        self.look_interval_max = max(self.look_interval_min, max_s)

    def set_look_amplitude(self, amplitude: float):
        """Ajusta la amplitud de la mirada aleatoria."""
        self.look_amplitude = self._clamp(amplitude, 0.0, 1.0)

    def enable(self, enabled: bool = True):
        """Activa o desactiva el reposo."""
        self.enabled = enabled

    def suspend(self):
        """Suspende temporalmente el reposo (por ejemplo, al hablar)."""
        self.suspended = True

    def resume(self):
        """Reanuda el reposo."""
        self.suspended = False

    def reset(self):
        """Reinicia el controlador."""
        self.initialize()

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "mode": self.mode.value,
            "enabled": self.enabled,
            "suspended": self.suspended,
            "intensity": round(self.intensity, 3),
            "phases": {
                "breath": round(self.breath_phase, 3),
                "head_x": round(self.head_phase_x, 3),
                "head_y": round(self.head_phase_y, 3),
                "sway": round(self.sway_phase, 3),
            },
            "params": {
                "breath_amp": self.breath_amp,
                "breath_speed": self.breath_speed,
                "head_amp": self.head_amp,
                "head_speed": self.head_speed,
                "sway_amp": self.sway_amp,
                "sway_speed": self.sway_speed,
                "micro_amp": self.micro_amp,
                "blink_rate": self.blink_rate,
            },
            "look": {
                "target_x": round(self.look_target_x, 3),
                "target_y": round(self.look_target_y, 3),
                "amplitude": self.look_amplitude,
                "changes": self.look_changes,
            },
            "updates": self.updates,
        }

    def get_available_modes(self) -> List[str]:
        """Lista los modos de reposo disponibles."""
        return [m.value for m in IdleMode]

    # =====================================================
    # UTILIDADES
    # =====================================================

    @staticmethod
    def _clamp(value: float, min_v: float, max_v: float) -> float:
        """Limita un valor entre un mínimo y un máximo."""
        return max(min_v, min(max_v, value))