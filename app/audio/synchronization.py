# app/audio/synchronization.py

import math
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State, AudioFeatures


# =========================================================
# MODOS DE SINCRONIZACIÓN
# =========================================================

class SyncMode(Enum):
    """Modos de sincronización audio-avatar."""
    NONE = "none"               # sin sincronización
    LIPSYNC = "lipsync"         # solo boca
    FULL = "full"               # boca + cabeza + cuerpo
    EXPRESSIVE = "expressive"   # todo + gestos
    PRECISE = "precise"         # alta precisión, baja latencia


# =========================================================
# PERFILES DE SINCRONIZACIÓN
# =========================================================

SYNC_PROFILES: Dict[SyncMode, Dict[str, float]] = {
    SyncMode.NONE:       {"lip_weight": 0.0, "head_weight": 0.0, "body_weight": 0.0, "latency": 0.0, "smoothing": 0.0},
    SyncMode.LIPSYNC:    {"lip_weight": 1.0, "head_weight": 0.0, "body_weight": 0.0, "latency": 0.03, "smoothing": 0.20},
    SyncMode.FULL:       {"lip_weight": 1.0, "head_weight": 0.5, "body_weight": 0.4, "latency": 0.05, "smoothing": 0.18},
    SyncMode.EXPRESSIVE: {"lip_weight": 1.0, "head_weight": 0.7, "body_weight": 0.6, "latency": 0.06, "smoothing": 0.15},
    SyncMode.PRECISE:    {"lip_weight": 1.0, "head_weight": 0.3, "body_weight": 0.2, "latency": 0.01, "smoothing": 0.10},
}


# =========================================================
# CONTROLADOR DE SINCRONIZACIÓN
# =========================================================

class SynchronizationController:
    """
    Controlador de sincronización audio-avatar de XARION-1.0.
    Alinea la reproducción del audio con el renderizado del avatar,
    compensa latencia, distribuye pesos por componente y genera
    señales normalizadas para boca, cabeza y cuerpo.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Modo activo ---
        self.mode: SyncMode = SyncMode.FULL
        self.profile: Dict[str, float] = SYNC_PROFILES[self.mode].copy()

        # --- Compensación de latencia ---
        self.latency_compensation: float = self.profile["latency"]
        self.buffer_size: int = 8
        self.audio_buffer: List[Tuple[float, AudioFeatures]] = []

        # --- Reloj ---
        self.audio_clock: float = 0.0
        self.avatar_clock: float = 0.0
        self.clock_offset: float = 0.0
        self.drift: float = 0.0
        self.drift_smoothing: float = 0.15

        # --- Estado ---
        self.synced: bool = False
        self.last_sync_time: float = 0.0
        self.lost_sync_threshold: float = 0.5

        # --- Señales suavizadas ---
        self.lip_signal: float = 0.0
        self.head_signal: float = 0.0
        self.body_signal: float = 0.0

        # --- Suavizado ---
        self.smoothing: float = self.profile["smoothing"]

        # --- Pesos ---
        self.lip_weight: float = self.profile["lip_weight"]
        self.head_weight: float = self.profile["head_weight"]
        self.body_weight: float = self.profile["body_weight"]

        # --- Estadísticas ---
        self.updates: int = 0
        self.sync_events: int = 0
        self.last_update: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Reinicia el estado interno del controlador."""
        self.audio_buffer.clear()
        self.audio_clock = 0.0
        self.avatar_clock = 0.0
        self.clock_offset = 0.0
        self.drift = 0.0
        self.synced = False
        self.lip_signal = 0.0
        self.head_signal = 0.0
        self.body_signal = 0.0
        self.last_update = time.time()

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """Actualiza la sincronización cada frame."""
        self.updates += 1
        now = time.time()

        # 1. Avanzar relojes
        self.avatar_clock += delta
        if state.audio.state.value == "playing":
            self.audio_clock = state.audio.current_time + self.latency_compensation

        # 2. Detectar desincronización
        self._update_drift(delta)

        # 3. Obtener features compensadas
        features = self._get_compensated_features()

        # 4. Generar señales para cada componente
        if features is not None:
            self._generate_signals(features, delta)
        else:
            self._decay_signals(delta)

        # 5. Volcar al estado global
        self._write_to_state(state)

        self.last_update = now

    # =====================================================
    # BUFFER Y COMPENSACIÓN
    # =====================================================

    def push_features(self, timestamp: float, features: AudioFeatures):
        """Añade features al buffer con su timestamp de audio."""
        self.audio_buffer.append((timestamp, features))
        if len(self.audio_buffer) > self.buffer_size:
            self.audio_buffer.pop(0)

    def _get_compensated_features(self) -> Optional[AudioFeatures]:
        """Devuelve las features compensadas por latencia."""
        if not self.audio_buffer:
            return None

        target_time = self.audio_clock
        closest = None
        min_diff = float("inf")

        for ts, feat in self.audio_buffer:
            diff = abs(ts - target_time)
            if diff < min_diff:
                min_diff = diff
                closest = feat

        return closest

    # =====================================================
    # DRIFT Y SINCRONIZACIÓN
    # =====================================================

    def _update_drift(self, delta: float):
        """Calcula la deriva entre el reloj de audio y el de avatar."""
        expected_offset = self.audio_clock - self.avatar_clock
        self.clock_offset = self._smooth(
            self.clock_offset, expected_offset, self.drift_smoothing
        )
        self.drift = abs(self.clock_offset)

        if self.drift < self.lost_sync_threshold:
            if not self.synced:
                self.synced = True
                self.last_sync_time = time.time()
                self.sync_events += 1
        else:
            self.synced = False

    # =====================================================
    # GENERACIÓN DE SEÑALES
    # =====================================================

    def _generate_signals(self, features: AudioFeatures, delta: float):
        """Genera señales normalizadas para cada componente."""
        # Señal de boca (apertura + energía)
        rms = self._clamp(features.rms * 4.0, 0.0, 1.0)
        lip_target = rms * self.lip_weight
        self.lip_signal = self._smooth(self.lip_signal, lip_target, self.smoothing)

        # Señal de cabeza (reacciona a pitch y centroide)
        head_target = 0.0
        if features.pitch > 0:
            pitch_norm = self._clamp(features.pitch / 400.0, 0.0, 1.0)
            head_target = pitch_norm * 0.6 + features.beat_strength * 0.4
        self.head_signal = self._smooth(
            self.head_signal, head_target * self.head_weight, self.smoothing
        )

        # Señal de cuerpo (reacciona a beats y energía)
        body_target = (
            features.beat_strength * 0.7 +
            self._clamp(features.energy_band_low, 0.0, 1.0) * 0.3
        )
        self.body_signal = self._smooth(
            self.body_signal, body_target * self.body_weight, self.smoothing
        )

    def _decay_signals(self, delta: float):
        """Decae las señales cuando no hay audio."""
        decay = max(0.0, 1.0 - delta * 4.0)
        self.lip_signal *= decay
        self.head_signal *= decay
        self.body_signal *= decay

    # =====================================================
    # ESCRITURA AL ESTADO
    # =====================================================

    def _write_to_state(self, state: State):
        """Aplica las señales al estado global del avatar."""
        # Boca: apertura directa
        if self.lip_weight > 0.0:
            target_open = self.lip_signal
            mouth = state.avatar_components.mouth
            mouth.openness = max(mouth.openness * 0.4, target_open)

        # Cabeza: modulación sutil
        if self.head_weight > 0.0:
            head = state.avatar_components.head
            head.target_position["x"] = self._clamp(
                head.target_position.get("x", 0.0) + (self.head_signal - 0.5) * 0.1,
                -1.0, 1.0
            )

        # Cuerpo: rebote sutil
        if self.body_weight > 0.0:
            body = state.avatar_components.body
            body.breathing_amplitude = max(
                0.015, body.breathing_amplitude + self.body_signal * 0.01
            )

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def set_mode(self, mode: SyncMode):
        """Cambia el modo de sincronización."""
        self.mode = mode
        self.profile = SYNC_PROFILES[mode].copy()
        self.latency_compensation = self.profile["latency"]
        self.smoothing = self.profile["smoothing"]
        self.lip_weight = self.profile["lip_weight"]
        self.head_weight = self.profile["head_weight"]
        self.body_weight = self.profile["body_weight"]

    def set_latency(self, latency: float):
        """Ajusta la compensación de latencia en segundos."""
        self.latency_compensation = max(0.0, min(0.5, latency))

    def set_weights(self, lip: Optional[float] = None,
                    head: Optional[float] = None,
                    body: Optional[float] = None):
        """Ajusta los pesos de cada componente."""
        if lip is not None:
            self.lip_weight = self._clamp(lip, 0.0, 1.5)
        if head is not None:
            self.head_weight = self._clamp(head, 0.0, 1.5)
        if body is not None:
            self.body_weight = self._clamp(body, 0.0, 1.5)

    def set_smoothing(self, value: float):
        """Ajusta el suavizado global de las señales."""
        self.smoothing = self._clamp(value, 0.01, 1.0)

    def reset(self):
        """Reinicia el controlador."""
        self.initialize()

    # =====================================================
    # CONSULTAS
    # =====================================================

    def is_synced(self) -> bool:
        """Indica si el audio y el avatar están sincronizados."""
        return self.synced

    def get_signals(self) -> Dict[str, float]:
        """Devuelve las señales actuales por componente."""
        return {
            "lip": round(self.lip_signal, 4),
            "head": round(self.head_signal, 4),
            "body": round(self.body_signal, 4),
        }

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "mode": self.mode.value,
            "synced": self.synced,
            "drift": round(self.drift, 4),
            "clock_offset": round(self.clock_offset, 4),
            "audio_clock": round(self.audio_clock, 3),
            "avatar_clock": round(self.avatar_clock, 3),
            "latency": self.latency_compensation,
            "weights": {
                "lip": self.lip_weight,
                "head": self.head_weight,
                "body": self.body_weight,
            },
            "signals": self.get_signals(),
            "buffer_size": len(self.audio_buffer),
            "sync_events": self.sync_events,
            "updates": self.updates,
        }

    def get_available_modes(self) -> List[str]:
        """Lista los modos de sincronización disponibles."""
        return [m.value for m in SyncMode]

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