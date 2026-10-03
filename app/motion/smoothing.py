# app/motion/smoothing.py

import math
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State


# =========================================================
# TIPOS DE SUAVIZADO
# =========================================================

class SmoothingType(Enum):
    """Tipos de suavizado disponibles."""
    LERP = "lerp"                 # interpolación lineal
    EASE_IN = "ease_in"           # aceleración
    EASE_OUT = "ease_out"         # desaceleración
    EASE_IN_OUT = "ease_in_out"   # suave en ambos extremos
    EXPONENTIAL = "exponential"   # exponencial (por defecto)
    SPRING = "spring"             # muelle (rebote suave)
    CRITICAL_DAMP = "critical_damp"  # amortiguado crítico


# =========================================================
# CONTROLADOR DE SUAVIZADO
# =========================================================

class SmoothingController:
    """
    Controlador de suavizado de XARION-1.0.
    Aplica interpolación avanzada a los valores de movimiento
    del avatar, evitando saltos bruscos y añadiendo naturalidad.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Tipo de suavizado por defecto ---
        self.type: SmoothingType = SmoothingType.EXPONENTIAL
        self.factor: float = self.config.SMOOTHING_FACTOR

        # --- Velocidades diferenciadas ---
        self.position_factor: float = 0.14
        self.rotation_factor: float = 0.12
        self.scale_factor: float = 0.10
        self.eye_factor: float = 0.20
        self.mouth_factor: float = 0.22
        self.blink_factor: float = 0.35

        # --- Parámetros de muelle ---
        self.spring_stiffness: float = 120.0
        self.spring_damping: float = 14.0
        self.spring_mass: float = 1.0

        # --- Estado interno del muelle ---
        self._spring_state: Dict[str, Dict[str, float]] = {}

        # --- Límites de velocidad ---
        self.max_velocity: float = 5.0
        self.max_acceleration: float = 15.0

        # --- Historial (para diagnóstico) ---
        self.history_size: int = 32
        self.history: Dict[str, List[float]] = {}

        # --- Estadísticas ---
        self.updates: int = 0
        self.last_update: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el estado interno."""
        self._spring_state.clear()
        self.history.clear()
        self.last_update = time.time()

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """
        Suaviza directamente los valores del estado global.
        Aplica el tipo de suavizado configurado a cada componente.
        """
        self.updates += 1

        # Suavizar cabeza
        head = state.avatar_components.head
        head.rotation_x = self.smooth_value(
            "head.rx", head.rotation_x, self.rotation_factor, delta
        )
        head.rotation_y = self.smooth_value(
            "head.ry", head.rotation_y, self.rotation_factor, delta
        )
        head.rotation_z = self.smooth_value(
            "head.rz", head.rotation_z, self.rotation_factor, delta
        )

        # Suavizar cuerpo
        body = state.avatar_components.body
        body.position_x = self.smooth_value(
            "body.px", body.position_x, self.position_factor, delta
        )
        body.position_y = self.smooth_value(
            "body.py", body.position_y, self.position_factor, delta
        )
        body.position_z = self.smooth_value(
            "body.pz", body.position_z, self.position_factor, delta
        )
        body.rotation_x = self.smooth_value(
            "body.rx", body.rotation_x, self.rotation_factor, delta
        )
        body.rotation_y = self.smooth_value(
            "body.ry", body.rotation_y, self.rotation_factor, delta
        )
        body.rotation_z = self.smooth_value(
            "body.rz", body.rotation_z, self.rotation_factor, delta
        )
        body.scale = self.smooth_value(
            "body.scale", body.scale, self.scale_factor, delta
        )

        # Suavizar ojos
        eyes = state.avatar_components.eyes
        eyes.look_x = self.smooth_value(
            "eyes.lx", eyes.look_x, self.eye_factor, delta
        )
        eyes.look_y = self.smooth_value(
            "eyes.ly", eyes.look_y, self.eye_factor, delta
        )

        # Suavizar boca
        mouth = state.avatar_components.mouth
        mouth.openness = self.smooth_value(
            "mouth.open", mouth.openness, self.mouth_factor, delta
        )

        self.last_update = time.time()

    # =====================================================
    # SUAVIZADO GENÉRICO
    # =====================================================

    def smooth_value(
        self,
        key: str,
        current: float,
        factor: Optional[float] = None,
        delta: float = 0.016,
    ) -> float:
        """Aplica suavizado a un valor concreto según el tipo activo."""
        factor = factor if factor is not None else self.factor

        if self.type == SmoothingType.LERP:
            result = self._lerp(current, factor)
        elif self.type == SmoothingType.EASE_IN:
            result = self._ease_in(current, factor)
        elif self.type == SmoothingType.EASE_OUT:
            result = self._ease_out(current, factor)
        elif self.type == SmoothingType.EASE_IN_OUT:
            result = self._ease_in_out(current, factor)
        elif self.type == SmoothingType.SPRING:
            result = self._spring(key, current, delta)
        elif self.type == SmoothingType.CRITICAL_DAMP:
            result = self._critical_damp(key, current, delta)
        else:
            result = self._exponential(current, factor)

        self._push_history(key, result)
        return result

    # =====================================================
    # ALGORITMOS DE SUAVIZADO
    # =====================================================

    @staticmethod
    def _lerp(current: float, factor: float) -> float:
        """Interpolación lineal simple (no conserva estado)."""
        return current

    @staticmethod
    def _ease_in(current: float, factor: float) -> float:
        """Ease-in (aceleración)."""
        return current * factor * factor

    @staticmethod
    def _ease_out(current: float, factor: float) -> float:
        """Ease-out (desaceleración)."""
        return current * (1.0 - (1.0 - factor) ** 2)

    @staticmethod
    def _ease_in_out(current: float, factor: float) -> float:
        """Ease-in-out (senoidal)."""
        return current * 0.5 * (1.0 - math.cos(math.pi * factor))

    @staticmethod
    def _exponential(current: float, factor: float) -> float:
        """Suavizado exponencial clásico."""
        return current + (0.0 - current) * factor

    def _spring(self, key: str, target: float, delta: float) -> float:
        """Suavizado con muelle físico (rebote amortiguado)."""
        st = self._spring_state.setdefault(key, {"pos": target, "vel": 0.0})

        force = (target - st["pos"]) * self.spring_stiffness
        damping = st["vel"] * self.spring_damping
        accel = (force - damping) / max(1e-6, self.spring_mass)

        st["vel"] += accel * delta
        st["pos"] += st["vel"] * delta

        # Límite de velocidad
        st["vel"] = self._clamp(st["vel"], -self.max_velocity, self.max_velocity)

        return st["pos"]

    def _critical_damp(self, key: str, target: float, delta: float) -> float:
        """Suavizado amortiguado crítico (sin overshoot)."""
        st = self._spring_state.setdefault(key, {"pos": target, "vel": 0.0})
        omega = math.sqrt(self.spring_stiffness)
        exp_term = math.exp(-omega * delta)
        st["pos"] = target + (st["pos"] - target + st["vel"] * delta) * exp_term
        st["vel"] = (st["vel"] - omega * (st["pos"] - target)) * exp_term
        return st["pos"]

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def set_type(self, s_type: SmoothingType):
        """Cambia el tipo de suavizado activo."""
        self.type = s_type

    def set_factor(self, factor: float):
        """Ajusta el factor global de suavizado."""
        self.factor = self._clamp(factor, 0.01, 1.0)

    def set_factors(
        self,
        position: Optional[float] = None,
        rotation: Optional[float] = None,
        scale: Optional[float] = None,
        eye: Optional[float] = None,
        mouth: Optional[float] = None,
        blink: Optional[float] = None,
    ):
        """Ajusta los factores por componente."""
        if position is not None:
            self.position_factor = self._clamp(position, 0.01, 1.0)
        if rotation is not None:
            self.rotation_factor = self._clamp(rotation, 0.01, 1.0)
        if scale is not None:
            self.scale_factor = self._clamp(scale, 0.01, 1.0)
        if eye is not None:
            self.eye_factor = self._clamp(eye, 0.01, 1.0)
        if mouth is not None:
            self.mouth_factor = self._clamp(mouth, 0.01, 1.0)
        if blink is not None:
            self.blink_factor = self._clamp(blink, 0.01, 1.0)

    def set_spring_params(
        self,
        stiffness: Optional[float] = None,
        damping: Optional[float] = None,
        mass: Optional[float] = None,
    ):
        """Ajusta los parámetros del muelle."""
        if stiffness is not None:
            self.spring_stiffness = max(1.0, stiffness)
        if damping is not None:
            self.spring_damping = max(0.0, damping)
        if mass is not None:
            self.spring_mass = max(0.01, mass)

    def set_velocity_limits(self, max_velocity: Optional[float] = None,
                            max_acceleration: Optional[float] = None):
        """Ajusta los límites de velocidad y aceleración."""
        if max_velocity is not None:
            self.max_velocity = max(0.1, max_velocity)
        if max_acceleration is not None:
            self.max_acceleration = max(0.1, max_acceleration)

    def reset(self):
        """Reinicia el estado interno."""
        self._spring_state.clear()
        self.history.clear()

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_history(self, key: str) -> List[float]:
        """Devuelve el historial de un valor concreto."""
        return list(self.history.get(key, []))

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "type": self.type.value,
            "factor": round(self.factor, 4),
            "factors": {
                "position": self.position_factor,
                "rotation": self.rotation_factor,
                "scale": self.scale_factor,
                "eye": self.eye_factor,
                "mouth": self.mouth_factor,
                "blink": self.blink_factor,
            },
            "spring": {
                "stiffness": self.spring_stiffness,
                "damping": self.spring_damping,
                "mass": self.spring_mass,
            },
            "velocity_limits": {
                "max_velocity": self.max_velocity,
                "max_acceleration": self.max_acceleration,
            },
            "tracked_keys": len(self._spring_state),
            "updates": self.updates,
        }

    def get_available_types(self) -> List[str]:
        """Lista los tipos de suavizado disponibles."""
        return [t.value for t in SmoothingType]

    # =====================================================
    # UTILIDADES
    # =====================================================

    def _push_history(self, key: str, value: float):
        """Guarda un valor en el historial del key."""
        hist = self.history.setdefault(key, [])
        hist.append(value)
        if len(hist) > self.history_size:
            hist.pop(0)

    @staticmethod
    def _clamp(value: float, min_v: float, max_v: float) -> float:
        """Limita un valor entre un mínimo y un máximo."""
        return max(min_v, min(max_v, value))