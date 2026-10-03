# app/avatar/eyes.py

import math
import random
import time
from typing import Optional, Dict, Any, Tuple

from app.core.config import Config
from app.core.state import State, EyesState


class EyesController:
    """
    Controlador de los ojos del avatar XARION-1.0.
    Gestiona mirada, apertura, dilatación, brillo y micro-movimientos.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Estado interno ---
        self.look_x = 0.0
        self.look_y = 0.0
        self.target_look_x = 0.0
        self.target_look_y = 0.0

        self.openness = 1.0
        self.target_openness = 1.0

        self.pupil_dilation = 1.0
        self.target_dilation = 1.0

        self.glow_intensity = 1.0
        self.color: Tuple[int, int, int] = (0, 255, 100)

        # --- Micro-movimientos (saccades) ---
        self.saccade_enabled = True
        self.saccade_interval_min = 0.8
        self.saccade_interval_max = 2.5
        self.next_saccade_time = 0.0
        self.saccade_amplitude = 0.15

        # --- Suavizado ---
        self.smoothing = 0.18

        # --- Seguimiento ---
        self.follow_target = False
        self.target_position: Dict[str, float] = {"x": 0.0, "y": 0.0}

        # --- Estadísticas ---
        self.updates = 0
        self.last_update = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa los tiempos internos."""
        now = time.time()
        self.next_saccade_time = now + random.uniform(
            self.saccade_interval_min, self.saccade_interval_max
        )
        self.last_update = now

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """
        Actualiza el estado de los ojos cada frame.
        Lee el estado global y aplica suavizado + micro-movimientos.
        """
        now = time.time()
        self.updates += 1

        # 1. Seguimiento de objetivo (si está activo)
        if self.follow_target:
            self._update_follow_target(delta)

        # 2. Micro-movimientos (saccades)
        if self.saccade_enabled:
            self._update_saccades(now)

        # 3. Suavizado hacia objetivos
        self.look_x = self._smooth(self.look_x, self.target_look_x, self.smoothing)
        self.look_y = self._smooth(self.look_y, self.target_look_y, self.smoothing)
        self.openness = self._smooth(self.openness, self.target_openness, self.smoothing)
        self.pupil_dilation = self._smooth(
            self.pupil_dilation, self.target_dilation, self.smoothing
        )

        # 4. Limitar valores
        self.look_x = self._clamp(self.look_x, -1.0, 1.0)
        self.look_y = self._clamp(self.look_y, -1.0, 1.0)
        self.openness = self._clamp(self.openness, 0.0, 1.0)
        self.pupil_dilation = self._clamp(self.pupil_dilation, 0.5, 1.5)

        # 5. Volcar al estado global
        self._write_to_state(state)
        self.last_update = now

    def _update_follow_target(self, delta: float):
        """Mueve la mirada hacia la posición objetivo."""
        self.target_look_x = self._clamp(self.target_position.get("x", 0.0), -1.0, 1.0)
        self.target_look_y = self._clamp(self.target_position.get("y", 0.0), -1.0, 1.0)

    def _update_saccades(self, now: float):
        """Genera micro-movimientos oculares automáticos."""
        if now < self.next_saccade_time:
            return

        # Nuevo objetivo de mirada aleatorio
        self.target_look_x = random.uniform(-self.saccade_amplitude, self.saccade_amplitude)
        self.target_look_y = random.uniform(-self.saccade_amplitude / 2, self.saccade_amplitude / 2)

        # Programar el siguiente
        self.next_saccade_time = now + random.uniform(
            self.saccade_interval_min, self.saccade_interval_max
        )

    def _write_to_state(self, state: State):
        """Escribe los valores internos en el estado global."""
        eyes = state.avatar_components.eyes
        eyes.look_x = self.look_x
        eyes.look_y = self.look_y
        eyes.openness = self.openness
        eyes.pupil_dilation = self.pupil_dilation
        eyes.glow_intensity = self.glow_intensity
        eyes.color = self.color

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def look_at(self, x: float, y: float):
        """Mueve la mirada a una posición normalizada (-1.0 a 1.0)."""
        self.target_look_x = self._clamp(x, -1.0, 1.0)
        self.target_look_y = self._clamp(y, -1.0, 1.0)

    def look_at_center(self):
        """Devuelve la mirada al centro."""
        self.target_look_x = 0.0
        self.target_look_y = 0.0

    def set_openness(self, value: float):
        """Ajusta la apertura de los ojos (0.0 cerrado, 1.0 abierto)."""
        self.target_openness = self._clamp(value, 0.0, 1.0)

    def set_dilation(self, value: float):
        """Ajusta la dilatación de la pupila (0.5 a 1.5)."""
        self.target_dilation = self._clamp(value, 0.5, 1.5)

    def set_glow(self, intensity: float):
        """Ajusta la intensidad del brillo verde."""
        self.glow_intensity = self._clamp(intensity, 0.0, 2.0)

    def set_color(self, r: int, g: int, b: int):
        """Cambia el color de los ojos."""
        self.color = (
            int(self._clamp(r, 0, 255)),
            int(self._clamp(g, 0, 255)),
            int(self._clamp(b, 0, 255)),
        )

    def enable_follow(self, enabled: bool = True):
        """Activa o desactiva el seguimiento de un objetivo."""
        self.follow_target = enabled

    def set_target_position(self, x: float, y: float):
        """Define la posición objetivo a seguir (normalizada)."""
        self.target_position = {"x": x, "y": y}

    def enable_saccades(self, enabled: bool = True):
        """Activa o desactiva los micro-movimientos automáticos."""
        self.saccade_enabled = enabled

    def set_smoothing(self, value: float):
        """Ajusta el factor de suavizado (0.0 a 1.0)."""
        self.smoothing = self._clamp(value, 0.01, 1.0)

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_state(self) -> EyesState:
        """Devuelve el estado actual de los ojos."""
        return EyesState(
            look_x=self.look_x,
            look_y=self.look_y,
            pupil_dilation=self.pupil_dilation,
            openness=self.openness,
            glow_intensity=self.glow_intensity,
            color=self.color,
        )

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "look": (round(self.look_x, 3), round(self.look_y, 3)),
            "target": (round(self.target_look_x, 3), round(self.target_look_y, 3)),
            "openness": round(self.openness, 3),
            "dilation": round(self.pupil_dilation, 3),
            "glow": round(self.glow_intensity, 3),
            "color": self.color,
            "follow_target": self.follow_target,
            "saccades_enabled": self.saccade_enabled,
            "updates": self.updates,
        }

    # =====================================================
    # UTILIDADES
    # =====================================================

    @staticmethod
    def _clamp(value: float, min_v: float, max_v: float) -> float:
        """Limita un valor entre un mínimo y un máximo."""
        return max(min_v, min(max_v, value))

    @staticmethod
    def _smooth(current: float, target: float, factor: float) -> float:
        """Interpolación lineal exponencial suave hacia el objetivo."""
        return current + (target - current) * factor