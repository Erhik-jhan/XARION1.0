# app/gestures/neutral.py

import math
import random
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State, GestureType


# =========================================================
# SUB-GESTOS NEUTRALES
# =========================================================

class NeutralVariant(Enum):
    """Variantes del gesto neutral."""
    BASE = "base"                # neutral puro
    ATTENTIVE = "attentive"      # atento (ligera inclinación)
    RELAXED = "relaxed"          # relajado
    FRIENDLY = "friendly"        # amistoso (ligera sonrisa)
    PROFESSIONAL = "professional"  # postura formal
    CONTEMPLATIVE = "contemplative"  # pensativo


# =========================================================
# PERFILES POR VARIANTE
# =========================================================

NEUTRAL_VARIANTS: Dict[NeutralVariant, Dict[str, float]] = {
    NeutralVariant.BASE:           {"head_pitch": 0.00, "head_yaw": 0.00, "head_roll": 0.00, "body_lean": 0.00, "smile": 0.50, "eyes_open": 1.00, "antenna_glow": 1.00, "antenna_speed": 1.20},
    NeutralVariant.ATTENTIVE:      {"head_pitch": 0.06, "head_yaw": 0.00, "head_roll": 0.03, "body_lean": 0.04, "smile": 0.55, "eyes_open": 1.05, "antenna_glow": 1.20, "antenna_speed": 1.60},
    NeutralVariant.RELAXED:        {"head_pitch": 0.02, "head_yaw": 0.02, "head_roll": 0.05, "body_lean": -0.02, "smile": 0.60, "eyes_open": 0.95, "antenna_glow": 0.85, "antenna_speed": 0.90},
    NeutralVariant.FRIENDLY:       {"head_pitch": 0.00, "head_yaw": 0.00, "head_roll": 0.04, "body_lean": 0.00, "smile": 0.75, "eyes_open": 1.00, "antenna_glow": 1.30, "antenna_speed": 1.40},
    NeutralVariant.PROFESSIONAL:   {"head_pitch": 0.00, "head_yaw": 0.00, "head_roll": 0.00, "body_lean": 0.02, "smile": 0.45, "eyes_open": 1.00, "antenna_glow": 0.95, "antenna_speed": 1.10},
    NeutralVariant.CONTEMPLATIVE:  {"head_pitch": -0.05, "head_yaw": 0.04, "head_roll": 0.06, "body_lean": -0.03, "smile": 0.40, "eyes_open": 0.90, "antenna_glow": 0.75, "antenna_speed": 0.70},
}


# =========================================================
# CONTROLADOR DE GESTO NEUTRAL
# =========================================================

class NeutralGesture:
    """
    Gesto neutral de XARION-1.0.
    Es el gesto base al que vuelve el avatar entre interacciones.
    Define pose base de cabeza, cuerpo, ojos, boca y antena
    con múltiples variantes y transiciones suaves.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Identificación ---
        self.gesture_type: GestureType = GestureType.NEUTRAL
        self.variant: NeutralVariant = NeutralVariant.BASE
        self.profile: Dict[str, float] = NEUTRAL_VARIANTS[self.variant].copy()

        # --- Estado ---
        self.active: bool = False
        self.transition: float = 1.0
        self.transition_speed: float = 2.0
        self.intensity: float = 1.0
        self.priority: int = 0

        # --- Pose objetivo ---
        self.target_head_pitch: float = 0.0
        self.target_head_yaw: float = 0.0
        self.target_head_roll: float = 0.0
        self.target_body_lean: float = 0.0
        self.target_smile: float = 0.50
        self.target_eyes_open: float = 1.00
        self.target_antenna_glow: float = 1.00
        self.target_antenna_speed: float = 1.20

        # --- Pose actual ---
        self.current_head_pitch: float = 0.0
        self.current_head_yaw: float = 0.0
        self.current_head_roll: float = 0.0
        self.current_body_lean: float = 0.0
        self.current_smile: float = 0.50
        self.current_eyes_open: float = 1.00
        self.current_antenna_glow: float = 1.00

        # --- Suavizado ---
        self.smoothing: float = 0.14

        # --- Micro-vida (respiración del gesto) ---
        self.micro_phase: float = 0.0
        self.micro_amplitude: float = 0.005

        # --- Estadísticas ---
        self.updates: int = 0
        self.activations: int = 0
        self.last_update: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el gesto neutral."""
        self.active = True
        self.transition = 0.0
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

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """Actualiza el gesto neutral cada frame."""
        if not self.active:
            return

        self.updates += 1

        # 1. Progreso de la transición
        if self.transition < 1.0:
            self.transition = min(1.0, self.transition + delta * self.transition_speed)

        # 2. Micro-vida
        self.micro_phase += delta * 1.2

        # 3. Suavizado hacia objetivos
        self._smooth_pose(delta)

        # 4. Aplicar al estado
        self._apply_to_state(state)

        self.last_update = time.time()

    def _smooth_pose(self, delta: float):
        """Suaviza la pose actual hacia la objetivo."""
        self.current_head_pitch = self._smooth(
            self.current_head_pitch, self.target_head_pitch, self.smoothing
        )
        self.current_head_yaw = self._smooth(
            self.current_head_yaw, self.target_head_yaw, self.smoothing
        )
        self.current_head_roll = self._smooth(
            self.current_head_roll, self.target_head_roll, self.smoothing
        )
        self.current_body_lean = self._smooth(
            self.current_body_lean, self.target_body_lean, self.smoothing
        )
        self.current_smile = self._smooth(
            self.current_smile, self.target_smile, self.smoothing
        )
        self.current_eyes_open = self._smooth(
            self.current_eyes_open, self.target_eyes_open, self.smoothing
        )
        self.current_antenna_glow = self._smooth(
            self.current_antenna_glow, self.target_antenna_glow, self.smoothing
        )

    def _apply_to_state(self, state: State):
        """Aplica la pose neutral al estado global."""
        t = self.transition * self.intensity
        micro = math.sin(self.micro_phase) * self.micro_amplitude

        # Cabeza
        head = state.avatar_components.head
        head.rotation_x += self.current_head_pitch * t + micro
        head.rotation_y += self.current_head_yaw * t
        head.rotation_z += self.current_head_roll * t + micro * 0.5

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

        # Antena
        antenna = state.avatar_components.antenna
        antenna.glow_intensity = self._clamp(
            antenna.glow_intensity * (1.0 - t) + self.current_antenna_glow * t, 0.0, 2.0
        )

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def activate(self):
        """Activa el gesto neutral."""
        self.active = True
        self.transition = 0.0
        self.activations += 1

    def deactivate(self):
        """Desactiva el gesto neutral."""
        self.active = False

    def set_variant(self, variant: NeutralVariant):
        """Cambia la variante del gesto neutral."""
        if variant == self.variant:
            return
        self.variant = variant
        self.profile = NEUTRAL_VARIANTS[variant].copy()
        self._apply_profile_to_target()
        self.transition = 0.0

    def set_intensity(self, intensity: float):
        """Ajusta la intensidad del gesto (0.0 a 1.0)."""
        self.intensity = self._clamp(intensity, 0.0, 1.0)

    def set_smoothing(self, factor: float):
        """Ajusta el suavizado del gesto."""
        self.smoothing = self._clamp(factor, 0.01, 1.0)

    def set_transition_speed(self, speed: float):
        """Ajusta la velocidad de transición."""
        self.transition_speed = max(0.1, speed)

    def override_pose(
        self,
        head_pitch: Optional[float] = None,
        head_yaw: Optional[float] = None,
        head_roll: Optional[float] = None,
        body_lean: Optional[float] = None,
        smile: Optional[float] = None,
        eyes_open: Optional[float] = None,
        antenna_glow: Optional[float] = None,
    ):
        """Sobrescribe partes concretas de la pose neutral."""
        if head_pitch is not None:
            self.target_head_pitch = head_pitch
        if head_yaw is not None:
            self.target_head_yaw = head_yaw
        if head_roll is not None:
            self.target_head_roll = head_roll
        if body_lean is not None:
            self.target_body_lean = body_lean
        if smile is not None:
            self.target_smile = self._clamp(smile, 0.0, 1.0)
        if eyes_open is not None:
            self.target_eyes_open = self._clamp(eyes_open, 0.0, 1.2)
        if antenna_glow is not None:
            self.target_antenna_glow = self._clamp(antenna_glow, 0.0, 2.0)

    def reset(self):
        """Reinicia el gesto neutral."""
        self.variant = NeutralVariant.BASE
        self.profile = NEUTRAL_VARIANTS[self.variant].copy()
        self._apply_profile_to_target()
        self.transition = 1.0
        self.active = True

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_type(self) -> GestureType:
        """Devuelve el tipo de gesto."""
        return self.gesture_type

    def is_active(self) -> bool:
        """Indica si el gesto está activo."""
        return self.active

    def get_pose(self) -> Dict[str, float]:
        """Devuelve la pose actual del gesto."""
        return {
            "head_pitch": round(self.current_head_pitch, 4),
            "head_yaw": round(self.current_head_yaw, 4),
            "head_roll": round(self.current_head_roll, 4),
            "body_lean": round(self.current_body_lean, 4),
            "smile": round(self.current_smile, 4),
            "eyes_open": round(self.current_eyes_open, 4),
            "antenna_glow": round(self.current_antenna_glow, 4),
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
            "pose": self.get_pose(),
            "target_pose": {
                "head_pitch": self.target_head_pitch,
                "head_yaw": self.target_head_yaw,
                "head_roll": self.target_head_roll,
                "body_lean": self.target_body_lean,
                "smile": self.target_smile,
                "eyes_open": self.target_eyes_open,
                "antenna_glow": self.target_antenna_glow,
            },
            "activations": self.activations,
            "updates": self.updates,
        }

    def get_available_variants(self) -> List[str]:
        """Lista las variantes disponibles."""
        return [v.value for v in NeutralVariant]

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