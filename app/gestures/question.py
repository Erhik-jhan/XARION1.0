# app/gestures/question.py

import math
import random
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State, GestureType


# =========================================================
# SUB-GESTOS DE PREGUNTA
# =========================================================

class QuestionVariant(Enum):
    """Variantes del gesto de pregunta."""
    NEUTRAL = "neutral"              # pregunta neutral
    CURIOUS = "curious"              # curiosidad
    SURPRISED = "surprised"          # sorpresa
    CONFUSED = "confused"            # confusión
    INTRIGUED = "intrigued"          # intriga
    SKEPTICAL = "skeptical"          # escepticismo


# =========================================================
# PERFILES POR VARIANTE
# =========================================================

QUESTION_VARIANTS: Dict[QuestionVariant, Dict[str, float]] = {
    QuestionVariant.NEUTRAL:    {"head_pitch": -0.06, "head_yaw": 0.00, "head_roll": 0.08, "body_lean": 0.00, "smile": 0.50, "eyes_open": 1.05, "antenna_glow": 1.30, "antenna_speed": 2.00, "brow_raise": 0.20},
    QuestionVariant.CURIOUS:    {"head_pitch": -0.10, "head_yaw": 0.06, "head_roll": 0.12, "body_lean": 0.04, "smile": 0.60, "eyes_open": 1.10, "antenna_glow": 1.50, "antenna_speed": 2.30, "brow_raise": 0.35},
    QuestionVariant.SURPRISED:  {"head_pitch": -0.16, "head_yaw": 0.00, "head_roll": 0.05, "body_lean": -0.03, "smile": 0.55, "eyes_open": 1.20, "antenna_glow": 1.80, "antenna_speed": 2.80, "brow_raise": 0.70},
    QuestionVariant.CONFUSED:   {"head_pitch": -0.04, "head_yaw": -0.10, "head_roll": 0.16, "body_lean": -0.02, "smile": 0.35, "eyes_open": 0.92, "antenna_glow": 0.85, "antenna_speed": 1.40, "brow_raise": 0.25},
    QuestionVariant.INTRIGUED:  {"head_pitch": -0.08, "head_yaw": 0.08, "head_roll": 0.10, "body_lean": 0.05, "smile": 0.65, "eyes_open": 1.05, "antenna_glow": 1.40, "antenna_speed": 2.10, "brow_raise": 0.40},
    QuestionVariant.SKEPTICAL:  {"head_pitch": 0.00, "head_yaw": -0.08, "head_roll": 0.05, "body_lean": -0.02, "smile": 0.40, "eyes_open": 0.95, "antenna_glow": 0.90, "antenna_speed": 1.60, "brow_raise": 0.55},
}


# =========================================================
# CONTROLADOR DE GESTO DE PREGUNTA
# =========================================================

class QuestionGesture:
    """
    Gesto de pregunta de XARION-1.0.
    Inclina la cabeza, eleva el brillo de la antena y modifica
    ligeramente la expresión para comunicar pregunta o curiosidad.
    Incluye fase de mantenimiento y retorno automático al neutral.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Identificación ---
        self.gesture_type: GestureType = GestureType.QUESTION
        self.variant: QuestionVariant = QuestionVariant.NEUTRAL
        self.profile: Dict[str, float] = QUESTION_VARIANTS[self.variant].copy()

        # --- Estado ---
        self.active: bool = False
        self.transition: float = 1.0
        self.transition_speed: float = 2.5
        self.intensity: float = 1.0
        self.priority: int = 1

        # --- Fases del gesto ---
        self.phase: str = "idle"        # idle | enter | hold | exit
        self.hold_duration: float = 1.6
        self.hold_elapsed: float = 0.0
        self.auto_exit: bool = True

        # --- Pose objetivo ---
        self.target_head_pitch: float = 0.0
        self.target_head_yaw: float = 0.0
        self.target_head_roll: float = 0.0
        self.target_body_lean: float = 0.0
        self.target_smile: float = 0.50
        self.target_eyes_open: float = 1.00
        self.target_antenna_glow: float = 1.00
        self.target_antenna_speed: float = 1.20
        self.target_brow_raise: float = 0.0

        # --- Pose actual ---
        self.current_head_pitch: float = 0.0
        self.current_head_yaw: float = 0.0
        self.current_head_roll: float = 0.0
        self.current_body_lean: float = 0.0
        self.current_smile: float = 0.50
        self.current_eyes_open: float = 1.00
        self.current_antenna_glow: float = 1.00
        self.current_brow_raise: float = 0.0

        # --- Suavizado ---
        self.smoothing: float = 0.16

        # --- Micro-vida ---
        self.micro_phase: float = 0.0
        self.micro_amplitude: float = 0.008

        # --- Callbacks ---
        self.on_complete = None

        # --- Estadísticas ---
        self.updates: int = 0
        self.activations: int = 0
        self.completions: int = 0
        self.last_update: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el gesto de pregunta."""
        self.active = False
        self.phase = "idle"
        self.transition = 1.0
        self.micro_phase = random.uniform(0.0, math.tau)
        self._apply_profile_to_target()
        self.last_update = time.time()

    def _apply_profile_to_target(self):
        """Aplica el perfil de la variante a las poses objetivo."""
        self.target_head_pitch = self.profile["head_pitch"]
        self.target_head_yaw = self.profile["head_yaw"]
        self.target_head_roll = self.profile["head_roll"]
        self.target_body_lean = self.profile["body_lean"]
        self.target_smile = self.profile["smile"]
        self.target_eyes_open = self.profile["eyes_open"]
        self.target_antenna_glow = self.profile["antenna_glow"]
        self.target_antenna_speed = self.profile["antenna_speed"]
        self.target_brow_raise = self.profile.get("brow_raise", 0.0)

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """Actualiza el gesto de pregunta cada frame."""
        if not self.active:
            return

        self.updates += 1

        # 1. Actualizar fase
        self._update_phase(delta)

        # 2. Progreso de transición
        if self.transition < 1.0:
            self.transition = min(1.0, self.transition + delta * self.transition_speed)

        # 3. Micro-vida
        self.micro_phase += delta * 2.0

        # 4. Suavizar pose
        self._smooth_pose(delta)

        # 5. Aplicar al estado
        self._apply_to_state(state)

        self.last_update = time.time()

    # =====================================================
    # FASES
    # =====================================================

    def _update_phase(self, delta: float):
        """Gestiona la secuencia enter → hold → exit."""
        if self.phase == "enter":
            if self.transition >= 1.0:
                self.phase = "hold"
                self.hold_elapsed = 0.0

        elif self.phase == "hold":
            self.hold_elapsed += delta
            if self.auto_exit and self.hold_elapsed >= self.hold_duration:
                self._exit()

        elif self.phase == "exit":
            if self.transition >= 1.0:
                self._complete()

    def _exit(self):
        """Inicia la fase de salida."""
        self.phase = "exit"
        self.transition = 0.0
        self.intensity = 0.0

    def _complete(self):
        """Finaliza el gesto."""
        self.active = False
        self.phase = "idle"
        self.completions += 1
        if callable(self.on_complete):
            try:
                self.on_complete()
            except Exception:
                pass

    # =====================================================
    # SUAVIZADO
    # =====================================================

    def _smooth_pose(self, delta: float):
        """Suaviza la pose actual hacia la objetivo."""
        t = self.transition

        self.current_head_pitch = self._smooth(
            self.current_head_pitch, self.target_head_pitch * t, self.smoothing
        )
        self.current_head_yaw = self._smooth(
            self.current_head_yaw, self.target_head_yaw * t, self.smoothing
        )
        self.current_head_roll = self._smooth(
            self.current_head_roll, self.target_head_roll * t, self.smoothing
        )
        self.current_body_lean = self._smooth(
            self.current_body_lean, self.target_body_lean * t, self.smoothing
        )
        self.current_smile = self._smooth(
            self.current_smile, self.target_smile, self.smoothing
        )
        self.current_eyes_open = self._smooth(
            self.current_eyes_open, self.target_eyes_open, self.smoothing
        )
        self.current_antenna_glow = self._smooth(
            self.current_antenna_glow, self.target_antenna_glow * t, self.smoothing
        )
        self.current_brow_raise = self._smooth(
            self.current_brow_raise, self.target_brow_raise * t, self.smoothing
        )

    # =====================================================
    # APLICACIÓN AL ESTADO
    # =====================================================

    def _apply_to_state(self, state: State):
        """Aplica el gesto de pregunta al estado global."""
        t = self.transition * self.intensity
        micro = math.sin(self.micro_phase) * self.micro_amplitude * t

        # Cabeza
        head = state.avatar_components.head
        head.rotation_x += self.current_head_pitch * t + micro
        head.rotation_y += self.current_head_yaw * t
        head.rotation_z += self.current_head_roll * t + micro * 0.5
        head.tilt_offset += self.current_head_roll * t * 0.4

        # Cuerpo
        body = state.avatar_components.body
        body.rotation_x += self.current_body_lean * t

        # Boca (sonrisa)
        mouth = state.avatar_components.mouth
        mouth.smile = self._clamp(
            mouth.smile * (1.0 - t) + self.current_smile * t, 0.0, 1.0
        )

        # Ojos
        eyes = state.avatar_components.eyes
        eyes.openness = self._clamp(
            eyes.openness * (1.0 - t) + self.current_eyes_open * t, 0.0, 1.2
        )
        eyes.glow_intensity = self._clamp(
            eyes.glow_intensity * (1.0 - t) + (1.0 + self.current_brow_raise * 0.5) * t,
            0.0, 2.0,
        )

        # Antena
        antenna = state.avatar_components.antenna
        antenna.glow_intensity = self._clamp(
            antenna.glow_intensity * (1.0 - t) + self.current_antenna_glow * t,
            0.0, 2.5,
        )
        antenna.pulse_speed = self._clamp(
            antenna.pulse_speed * (1.0 - t) + self.target_antenna_speed * t,
            0.1, 5.0,
        )

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def activate(self, hold_duration: Optional[float] = None):
        """Activa el gesto de pregunta."""
        self.active = True
        self.phase = "enter"
        self.transition = 0.0
        self.hold_elapsed = 0.0
        self.intensity = 1.0
        if hold_duration is not None:
            self.hold_duration = max(0.1, hold_duration)
        self.activations += 1

    def deactivate(self):
        """Desactiva el gesto inmediatamente."""
        self.active = False
        self.phase = "idle"
        self.transition = 0.0

    def set_variant(self, variant: QuestionVariant):
        """Cambia la variante del gesto."""
        if variant == self.variant:
            return
        self.variant = variant
        self.profile = QUESTION_VARIANTS[variant].copy()
        self._apply_profile_to_target()

    def set_hold_duration(self, duration: float):
        """Ajusta la duración de la fase de mantenimiento."""
        self.hold_duration = max(0.1, duration)

    def set_intensity(self, intensity: float):
        """Ajusta la intensidad del gesto (0.0 a 1.0)."""
        self.intensity = self._clamp(intensity, 0.0, 1.0)

    def set_smoothing(self, factor: float):
        """Ajusta el suavizado."""
        self.smoothing = self._clamp(factor, 0.01, 1.0)

    def set_transition_speed(self, speed: float):
        """Ajusta la velocidad de transición."""
        self.transition_speed = max(0.1, speed)

    def set_auto_exit(self, auto: bool):
        """Activa o desactiva la salida automática."""
        self.auto_exit = auto

    def on_finish(self, callback):
        """Registra un callback a ejecutar al terminar el gesto."""
        self.on_complete = callback

    def reset(self):
        """Reinicia el gesto."""
        self.variant = QuestionVariant.NEUTRAL
        self.profile = QUESTION_VARIANTS[self.variant].copy()
        self._apply_profile_to_target()
        self.active = False
        self.phase = "idle"
        self.transition = 1.0

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_type(self) -> GestureType:
        """Devuelve el tipo de gesto."""
        return self.gesture_type

    def is_active(self) -> bool:
        """Indica si el gesto está activo."""
        return self.active

    def get_phase(self) -> str:
        """Devuelve la fase actual."""
        return self.phase

    def get_pose(self) -> Dict[str, float]:
        """Devuelve la pose actual."""
        return {
            "head_pitch": round(self.current_head_pitch, 4),
            "head_yaw": round(self.current_head_yaw, 4),
            "head_roll": round(self.current_head_roll, 4),
            "body_lean": round(self.current_body_lean, 4),
            "smile": round(self.current_smile, 4),
            "eyes_open": round(self.current_eyes_open, 4),
            "antenna_glow": round(self.current_antenna_glow, 4),
            "brow_raise": round(self.current_brow_raise, 4),
        }

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del gesto."""
        return {
            "type": self.gesture_type.value,
            "variant": self.variant.value,
            "active": self.active,
            "phase": self.phase,
            "transition": round(self.transition, 3),
            "intensity": round(self.intensity, 3),
            "priority": self.priority,
            "hold": {
                "duration": self.hold_duration,
                "elapsed": round(self.hold_elapsed, 3),
                "auto_exit": self.auto_exit,
            },
            "pose": self.get_pose(),
            "activations": self.activations,
            "completions": self.completions,
            "updates": self.updates,
        }

    def get_available_variants(self) -> List[str]:
        """Lista las variantes disponibles."""
        return [v.value for v in QuestionVariant]

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