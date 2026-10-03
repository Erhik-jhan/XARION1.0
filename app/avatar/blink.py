# app/avatar/blink.py

import random
import time
from typing import Optional, Dict, Any

from app.core.config import Config
from app.core.state import State, BlinkState


class BlinkController:
    """
    Controlador de parpadeo del avatar XARION-1.0.
    Gestiona parpadeos automáticos, dobles, y manuales con curva suave.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Configuración base ---
        self.enabled = True
        self.interval_min = self.config.BLINK_INTERVAL_MIN
        self.interval_max = self.config.BLINK_INTERVAL_MAX
        self.blink_duration = 0.15
        self.double_blink_chance = 0.10
        self.double_blink_delay = 0.10

        # --- Estado interno ---
        self.is_blinking = False
        self.blink_progress = 0.0
        self.blink_start_time = 0.0
        self.next_blink_time = 0.0

        # --- Cola de parpadeos (para dobles) ---
        self.pending_blinks = 0

        # --- Estadísticas ---
        self.blink_count = 0
        self.last_blink_time = 0.0
        self.updates = 0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Programa el primer parpadeo."""
        now = time.time()
        self.next_blink_time = now + self._random_interval()
        self.blink_start_time = 0.0
        self.is_blinking = False
        self.blink_progress = 0.0
        self.pending_blinks = 0

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """
        Actualiza el estado de parpadeo cada frame.
        Aplica el progreso del parpadeo y lo volca al estado global.
        """
        now = time.time()
        self.updates += 1

        if not self.enabled:
            self._write_to_state(state)
            return

        # 1. Si está parpadeando, avanzar progreso
        if self.is_blinking:
            self._advance_blink(now)

        # 2. Si no, comprobar si toca parpadear
        elif now >= self.next_blink_time:
            self._trigger_blink(now)

        # 3. Volcar al estado global
        self._write_to_state(state)

    def _advance_blink(self, now: float):
        """Avanza la animación del parpadeo actual."""
        elapsed = now - self.blink_start_time
        progress = elapsed / self.blink_duration

        if progress >= 1.0:
            # Parpadeo terminado
            self.is_blinking = False
            self.blink_progress = 0.0
            self.blink_count += 1
            self.last_blink_time = now

            # ¿Doble parpadeo?
            if self.pending_blinks > 0:
                self.pending_blinks -= 1
                self.blink_start_time = now + self.double_blink_delay
                self.is_blinking = True
                self.blink_progress = 0.0
            else:
                self.next_blink_time = now + self._random_interval()
        else:
            # Curva suave (abrir-cerrar-abrir)
            self.blink_progress = self._blink_curve(progress)

    def _trigger_blink(self, now: float):
        """Inicia un nuevo parpadeo."""
        self.is_blinking = True
        self.blink_progress = 0.0
        self.blink_start_time = now

        # ¿Programar doble parpadeo?
        if random.random() < self.double_blink_chance:
            self.pending_blinks = 1

    def _blink_curve(self, t: float) -> float:
        """
        Curva de parpadeo: 0 → 1 → 0.
        Usa una función senoidal para suavidad natural.
        """
        if t <= 0.5:
            # Cerrar
            return self._ease_in_out(t * 2.0)
        else:
            # Abrir
            return self._ease_in_out((1.0 - t) * 2.0)

    def _write_to_state(self, state: State):
        """Escribe los valores internos en el estado global."""
        blink = state.avatar_components.blink
        blink.enabled = self.enabled
        blink.interval_min = self.interval_min
        blink.interval_max = self.interval_max
        blink.is_blinking = self.is_blinking
        blink.blink_progress = self.blink_progress
        blink.blink_duration = self.blink_duration
        blink.next_blink_time = self.next_blink_time
        blink.double_blink_chance = self.double_blink_chance

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def blink_now(self):
        """Fuerza un parpadeo inmediato."""
        if not self.is_blinking:
            self._trigger_blink(time.time())

    def double_blink(self):
        """Fuerza un doble parpadeo inmediato."""
        self.pending_blinks = 1
        self.blink_now()

    def enable(self, enabled: bool = True):
        """Activa o desactiva el parpadeo automático."""
        self.enabled = enabled
        if enabled:
            self.next_blink_time = time.time() + self._random_interval()

    def set_interval(self, min_s: float, max_s: float):
        """Ajusta el rango de intervalo entre parpadeos."""
        self.interval_min = max(0.1, min_s)
        self.interval_max = max(self.interval_min, max_s)

    def set_duration(self, duration: float):
        """Ajusta la duración de cada parpadeo."""
        self.blink_duration = max(0.05, duration)

    def set_double_chance(self, chance: float):
        """Ajusta la probabilidad de doble parpadeo (0.0 a 1.0)."""
        self.double_blink_chance = max(0.0, min(1.0, chance))

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_state(self) -> BlinkState:
        """Devuelve el estado actual del parpadeo."""
        return BlinkState(
            enabled=self.enabled,
            interval_min=self.interval_min,
            interval_max=self.interval_max,
            next_blink_time=self.next_blink_time,
            is_blinking=self.is_blinking,
            blink_progress=self.blink_progress,
            blink_duration=self.blink_duration,
            double_blink_chance=self.double_blink_chance,
        )

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "enabled": self.enabled,
            "is_blinking": self.is_blinking,
            "progress": round(self.blink_progress, 3),
            "blink_count": self.blink_count,
            "next_blink_in": round(max(0.0, self.next_blink_time - time.time()), 2),
            "interval": (self.interval_min, self.interval_max),
            "duration": self.blink_duration,
            "double_chance": self.double_blink_chance,
            "updates": self.updates,
        }

    # =====================================================
    # UTILIDADES
    # =====================================================

    def _random_interval(self) -> float:
        """Devuelve un intervalo aleatorio entre min y max."""
        return random.uniform(self.interval_min, self.interval_max)

    @staticmethod
    def _ease_in_out(t: float) -> float:
        """Función de easing suave (senoidal)."""
        t = max(0.0, min(1.0, t))
        return 0.5 * (1.0 - math.cos(math.pi * t))


import math  # import al final para evitar colisión en algunos linters