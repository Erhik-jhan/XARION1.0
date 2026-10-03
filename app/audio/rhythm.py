# app/audio/rhythm.py

import math
import time
import importlib
from collections import deque
from typing import Optional, Dict, Any, List, Tuple

from app.core.config import Config
from app.core.state import State, AudioFeatures


# =========================================================
# CONTROLADOR DE RITMO
# =========================================================

class RhythmController:
    """
    Controlador de ritmo de XARION-1.0.
    Detecta beats, estima BPM, mantiene un historial temporal,
    predice el siguiente beat y genera eventos de intensidad
    para el motor de movimiento.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Detección de beats ---
        self.beat_threshold: float = 1.35
        self.beat_min_interval: float = 0.15
        self.beat_max_interval: float = 2.0
        self.beat_decay: float = 6.0

        # --- Historial de energía (ventana deslizante) ---
        self.energy_window_size: int = 43
        self.energy_history: deque = deque(maxlen=self.energy_window_size)
        self.beat_times: deque = deque(maxlen=32)
        self.beat_strengths: deque = deque(maxlen=32)

        # --- BPM ---
        self.bpm: float = 0.0
        self.bpm_smoothed: float = 0.0
        self.bpm_smoothing: float = 0.20
        self.bpm_min: float = 40.0
        self.bpm_max: float = 220.0

        # --- Predicción ---
        self.prediction_enabled: bool = True
        self.next_beat_time: float = 0.0
        self.prediction_confidence: float = 0.0

        # --- Estado de beat ---
        self.last_beat_time: float = 0.0
        self.last_beat_strength: float = 0.0
        self.beat_punch: float = 0.0
        self.total_beats: int = 0

        # --- Downbeat / acento ---
        self.beats_per_bar: int = 4
        self.beat_counter: int = 0
        self.downbeat_detected: bool = False
        self.downbeat_strength: float = 0.0

        # --- Intensidad rítmica ---
        self.energy_level: float = 0.0
        self.energy_smoothed: float = 0.0
        self.energy_smoothing: float = 0.20

        # --- Backend ---
        self._np = None
        self._load_backend()

        # --- Estadísticas ---
        self.updates: int = 0
        self.last_update: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Reinicia el estado interno del controlador."""
        self.energy_history.clear()
        self.beat_times.clear()
        self.beat_strengths.clear()
        self.bpm = 0.0
        self.bpm_smoothed = 0.0
        self.last_beat_time = 0.0
        self.beat_counter = 0
        self.beat_punch = 0.0
        self.last_update = time.time()

    def _load_backend(self):
        """Carga numpy si está disponible."""
        try:
            self._np = importlib.import_module("numpy")
        except Exception:
            self._np = None

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, features: Optional[AudioFeatures] = None):
        """Actualiza el estado rítmico con las features del analyzer."""
        self.updates += 1

        if features is not None:
            self._process_features(features)

        # Decaimiento del punch
        if self.beat_punch > 0.0:
            self.beat_punch = max(0.0, self.beat_punch - delta * self.beat_decay)

        # Suavizado de la energía
        self.energy_smoothed = self._smooth(
            self.energy_smoothed, self.energy_level, self.energy_smoothing
        )

        self.last_update = time.time()

    def _process_features(self, features: AudioFeatures):
        """Procesa las features del analyzer para extraer información rítmica."""
        # Energía
        self.energy_level = self._clamp(features.rms * 4.0, 0.0, 1.0)
        self.energy_history.append(self.energy_level)

        # Beat detectado por el analyzer
        if features.beat_detected:
            self._register_beat(features.beat_strength)

        # BPM propuesto por el analyzer
        if features.rhythm_bpm > 0:
            self._update_bpm(features.rhythm_bpm)

    # =====================================================
    # DETECCIÓN DE BEATS
    # =====================================================

    def _register_beat(self, strength: float):
        """Registra un beat detectado."""
        now = time.time()

        # Filtro de intervalo mínimo
        if self.last_beat_time > 0:
            interval = now - self.last_beat_time
            if interval < self.beat_min_interval:
                return
            if interval > self.beat_max_interval:
                # Reinicia el contador si hay un hueco grande
                self.beat_counter = 0

        self.last_beat_time = now
        self.last_beat_strength = self._clamp(strength, 0.0, 1.0)
        self.beat_punch = self.last_beat_strength
        self.total_beats += 1

        self.beat_times.append(now)
        self.beat_strengths.append(self.last_beat_strength)

        # Downbeat (acento cada N beats)
        self.beat_counter += 1
        if self.beat_counter >= self.beats_per_bar:
            self.beat_counter = 0
            self.downbeat_detected = True
            self.downbeat_strength = self.last_beat_strength
        else:
            self.downbeat_detected = False
            self.downbeat_strength = 0.0

        # Actualizar predicción
        self._update_prediction()

    def _update_prediction(self):
        """Actualiza el tiempo del siguiente beat previsto."""
        if not self.prediction_enabled:
            return
        if self.bpm_smoothed <= 0.0:
            self.next_beat_time = 0.0
            self.prediction_confidence = 0.0
            return

        interval = 60.0 / self.bpm_smoothed
        self.next_beat_time = self.last_beat_time + interval
        # Confianza basada en cuántos beats recientes tenemos
        self.prediction_confidence = self._clamp(
            len(self.beat_times) / 8.0, 0.0, 1.0
        )

    # =====================================================
    # BPM
    # =====================================================

    def _update_bpm(self, new_bpm: float):
        """Actualiza el BPM con validación y suavizado."""
        if not (self.bpm_min <= new_bpm <= self.bpm_max):
            return

        if self.bpm <= 0.0:
            self.bpm = new_bpm
            self.bpm_smoothed = new_bpm
        else:
            self.bpm = new_bpm
            self.bpm_smoothed = self._smooth(
                self.bpm_smoothed, new_bpm, self.bpm_smoothing
            )

    # =====================================================
    # CONSULTAS RÍTMICAS
    # =====================================================

    def is_beat_now(self, tolerance: float = 0.05) -> bool:
        """Indica si estamos en la ventana de un beat previsto."""
        if self.next_beat_time <= 0.0:
            return False
        return abs(time.time() - self.next_beat_time) <= tolerance

    def time_to_next_beat(self) -> float:
        """Devuelve el tiempo restante hasta el siguiente beat previsto."""
        if self.next_beat_time <= 0.0:
            return -1.0
        return max(0.0, self.next_beat_time - time.time())

    def get_rhythm_intensity(self) -> float:
        """Intensidad rítmica actual combinando energía y punch."""
        return self._clamp(
            self.energy_smoothed * 0.6 + self.beat_punch * 0.4, 0.0, 1.0
        )

    def get_beat_punch(self) -> float:
        """Golpe actual de beat (decae con el tiempo)."""
        return self.beat_punch

    def get_energy_level(self) -> float:
        """Nivel de energía suavizado (0.0 a 1.0)."""
        return self.energy_smoothed

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def set_beat_threshold(self, threshold: float):
        """Ajusta el umbral relativo de beats."""
        self.beat_threshold = max(1.0, threshold)

    def set_min_interval(self, seconds: float):
        """Ajusta el intervalo mínimo entre beats."""
        self.beat_min_interval = max(0.05, seconds)

    def set_bpm_range(self, bpm_min: float, bpm_max: float):
        """Ajusta el rango válido de BPM."""
        self.bpm_min = max(20.0, bpm_min)
        self.bpm_max = max(self.bpm_min + 1.0, bpm_max)

    def set_beats_per_bar(self, beats: int):
        """Ajusta los beats por compás para detectar downbeats."""
        self.beats_per_bar = max(1, int(beats))
        self.beat_counter = 0

    def enable_prediction(self, enabled: bool = True):
        """Activa o desactiva la predicción del siguiente beat."""
        self.prediction_enabled = enabled
        if not enabled:
            self.next_beat_time = 0.0
            self.prediction_confidence = 0.0

    def set_smoothing(self, bpm: Optional[float] = None,
                      energy: Optional[float] = None):
        """Ajusta factores de suavizado."""
        if bpm is not None:
            self.bpm_smoothing = self._clamp(bpm, 0.01, 1.0)
        if energy is not None:
            self.energy_smoothing = self._clamp(energy, 0.01, 1.0)

    def reset(self):
        """Reinicia el controlador."""
        self.initialize()

    # =====================================================
    # INFORMACIÓN
    # =====================================================

    def get_history(self) -> Dict[str, List[float]]:
        """Devuelve el historial de energía y beats."""
        return {
            "energy": list(self.energy_history),
            "beat_strengths": list(self.beat_strengths),
            "beat_times": list(self.beat_times),
        }

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "bpm": round(self.bpm, 2),
            "bpm_smoothed": round(self.bpm_smoothed, 2),
            "total_beats": self.total_beats,
            "last_beat_strength": round(self.last_beat_strength, 3),
            "beat_punch": round(self.beat_punch, 3),
            "energy_level": round(self.energy_smoothed, 3),
            "rhythm_intensity": round(self.get_rhythm_intensity(), 3),
            "downbeat": self.downbeat_detected,
            "downbeat_strength": round(self.downbeat_strength, 3),
            "beat_counter": self.beat_counter,
            "beats_per_bar": self.beats_per_bar,
            "prediction": {
                "enabled": self.prediction_enabled,
                "next_beat_time": round(self.next_beat_time, 3),
                "time_to_next": round(self.time_to_next_beat(), 3),
                "confidence": round(self.prediction_confidence, 3),
            },
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
        """Interpolación exponencial suave."""
        return current + (target - current) * factor