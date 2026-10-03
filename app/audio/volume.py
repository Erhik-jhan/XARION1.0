# app/audio/volume.py

import math
import time
import wave
import importlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from app.core.config import Config
from app.core.state import State


# =========================================================
# CONTROLADOR DE VOLUMEN
# =========================================================

class VolumeController:
    """
    Controlador de volumen de XARION-1.0.
    Gestiona volumen maestro, mute, fading, normalización,
    medición RMS/pico y limitador suave.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Niveles ---
        self.master_volume: float = 1.0       # 0.0 a 1.0
        self.current_volume: float = 1.0      # volumen efectivo actual
        self.target_volume: float = 1.0       # objetivo (para fade)
        self.peak_volume: float = 1.0

        # --- Mute ---
        self.muted: bool = False
        self.mute_previous_volume: float = 1.0

        # --- Fade ---
        self.fade_active: bool = False
        self.fade_start_volume: float = 1.0
        self.fade_target_volume: float = 1.0
        self.fade_duration: float = 0.5
        self.fade_elapsed: float = 0.0
        self.fade_curve: str = "linear"       # linear | ease_in | ease_out | ease_in_out

        # --- Medición ---
        self.current_rms: float = 0.0
        self.current_peak: float = 0.0
        self.smoothed_rms: float = 0.0
        self.smoothed_peak: float = 0.0
        self.rms_smoothing: float = 0.20
        self.peak_decay: float = 0.02
        self.db_floor: float = -60.0

        # --- Limitador suave ---
        self.limiter_enabled: bool = True
        self.limiter_threshold: float = 0.95
        self.limiter_ratio: float = 4.0
        self.limiter_knee: float = 0.05

        # --- Normalización ---
        self.normalization_enabled: bool = False
        self.normalization_target_db: float = -3.0
        self.normalization_max_gain: float = 4.0

        # --- Historial ---
        self.history_size: int = 64
        self.rms_history: List[float] = []
        self.peak_history: List[float] = []

        # --- Backend ---
        self._np = None
        self._load_backend()

        # --- Estadísticas ---
        self.updates: int = 0
        self.clipped_samples: int = 0
        self.last_update: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el estado del controlador."""
        self.current_volume = self.master_volume
        self.target_volume = self.master_volume
        self.fade_active = False
        self.rms_history.clear()
        self.peak_history.clear()
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

    def update(self, delta: float, chunk: Optional[Any] = None):
        """Actualiza el controlador cada frame."""
        self.updates += 1

        # 1. Fade si está activo
        if self.fade_active:
            self._update_fade(delta)

        # 2. Medición de chunk
        if chunk is not None and len(chunk) > 0:
            self._measure(chunk)

        # 3. Decaimiento del peak
        self.current_peak = max(0.0, self.current_peak - self.peak_decay * delta)
        self.smoothed_peak = self._smooth(
            self.smoothed_peak, self.current_peak, self.rms_smoothing
        )

        # 4. Historiales
        self._push_history(self.rms_history, self.smoothed_rms)
        self._push_history(self.peak_history, self.smoothed_peak)

        self.last_update = time.time()

    def _update_fade(self, delta: float):
        """Actualiza la interpolación del fade actual."""
        self.fade_elapsed += delta
        t = min(1.0, self.fade_elapsed / max(1e-6, self.fade_duration))
        t = self._apply_curve(t, self.fade_curve)

        self.current_volume = self.fade_start_volume + (
            self.fade_target_volume - self.fade_start_volume
        ) * t

        if self.fade_elapsed >= self.fade_duration:
            self.fade_active = False
            self.current_volume = self.fade_target_volume

    def _measure(self, chunk: Any):
        """Mide RMS y pico del chunk actual."""
        rms, peak = self._compute_rms_peak(chunk)
        self.current_rms = rms
        self.current_peak = max(self.current_peak, peak)
        self.smoothed_rms = self._smooth(self.smoothed_rms, rms, self.rms_smoothing)

    # =====================================================
    # APLICACIÓN DE VOLUMEN
    # =====================================================

    def apply(self, chunk: Any) -> Any:
        """Aplica volumen, mute, limitador y normalización a un chunk."""
        if chunk is None or len(chunk) == 0:
            return chunk

        gain = self.get_effective_volume()

        if self._np is not None:
            arr = self._np.asarray(chunk, dtype=self._np.float32).copy()

            # Normalización
            if self.normalization_enabled:
                arr = self._apply_normalization(arr)

            # Volumen
            arr *= gain

            # Limitador
            if self.limiter_enabled:
                arr, clipped = self._apply_limiter(arr)
                self.clipped_samples += clipped

            return arr

        # Fallback puro Python
        if self.normalization_enabled:
            chunk = self._apply_normalization_list(chunk)
        chunk = [x * gain for x in chunk]
        if self.limiter_enabled:
            chunk = [self._soft_limit(x) for x in chunk]
        return chunk

    # =====================================================
    # FADE
    # =====================================================

    def fade_to(self, target: float, duration: float = 0.5, curve: str = "linear"):
        """Inicia un fade hacia un volumen objetivo."""
        self.fade_start_volume = self.current_volume
        self.fade_target_volume = self._clamp(target, 0.0, 1.0)
        self.fade_duration = max(0.01, duration)
        self.fade_elapsed = 0.0
        self.fade_curve = curve
        self.fade_active = True

    def fade_in(self, duration: float = 0.5):
        """Fade de 0 al volumen maestro."""
        self.current_volume = 0.0
        self.fade_to(self.master_volume, duration, curve="ease_in")

    def fade_out(self, duration: float = 0.5, stop_at: float = 0.0):
        """Fade del volumen actual a `stop_at`."""
        self.fade_to(stop_at, duration, curve="ease_out")

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def set_master_volume(self, volume: float):
        """Establece el volumen maestro (0.0 a 1.0)."""
        self.master_volume = self._clamp(volume, 0.0, 1.0)
        if not self.muted and not self.fade_active:
            self.current_volume = self.master_volume
            self.target_volume = self.master_volume

    def set_volume(self, volume: float):
        """Establece el volumen actual directamente."""
        self.current_volume = self._clamp(volume, 0.0, 1.0)

    def set_db(self, db: float):
        """Ajusta el volumen a partir de un valor en decibelios."""
        linear = 10.0 ** (db / 20.0)
        self.set_master_volume(linear)

    def get_db(self) -> float:
        """Devuelve el volumen actual en decibelios."""
        vol = max(1e-6, self.current_volume)
        return 20.0 * math.log10(vol)

    def mute(self):
        """Silencia la salida."""
        if not self.muted:
            self.mute_previous_volume = self.master_volume
            self.muted = True
            self.current_volume = 0.0

    def unmute(self):
        """Restaura el volumen tras un mute."""
        if self.muted:
            self.muted = False
            self.master_volume = self.mute_previous_volume
            self.current_volume = self.master_volume

    def toggle_mute(self):
        """Alterna entre mute y unmute."""
        if self.muted:
            self.unmute()
        else:
            self.mute()

    def enable_limiter(self, enabled: bool = True,
                       threshold: float = 0.95,
                       ratio: float = 4.0):
        """Activa o desactiva el limitador suave."""
        self.limiter_enabled = enabled
        self.limiter_threshold = self._clamp(threshold, 0.1, 1.0)
        self.limiter_ratio = max(1.0, ratio)

    def enable_normalization(self, enabled: bool = True,
                             target_db: float = -3.0,
                             max_gain: float = 4.0):
        """Activa o desactiva la normalización."""
        self.normalization_enabled = enabled
        self.normalization_target_db = target_db
        self.normalization_max_gain = max(1.0, max_gain)

    def set_smoothing(self, rms: Optional[float] = None,
                      peak_decay: Optional[float] = None):
        """Ajusta los factores de suavizado."""
        if rms is not None:
            self.rms_smoothing = self._clamp(rms, 0.01, 1.0)
        if peak_decay is not None:
            self.peak_decay = max(0.0, peak_decay)

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_effective_volume(self) -> float:
        """Devuelve el volumen efectivo actual (0.0 si está mute)."""
        if self.muted:
            return 0.0
        return self.current_volume

    def get_level(self) -> float:
        """Devuelve el nivel RMS suavizado (0.0 a 1.0)."""
        return self.smoothed_rms

    def get_level_db(self) -> float:
        """Devuelve el nivel RMS en decibelios."""
        rms = max(1e-6, self.smoothed_rms)
        db = 20.0 * math.log10(rms)
        return max(self.db_floor, db)

    def get_peak(self) -> float:
        """Devuelve el pico suavizado (0.0 a 1.0)."""
        return self.smoothed_peak

    def get_history(self) -> Dict[str, List[float]]:
        """Devuelve el historial de niveles."""
        return {
            "rms": list(self.rms_history),
            "peak": list(self.peak_history),
        }

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "master_volume": round(self.master_volume, 4),
            "current_volume": round(self.current_volume, 4),
            "target_volume": round(self.target_volume, 4),
            "effective_volume": round(self.get_effective_volume(), 4),
            "db": round(self.get_db(), 2),
            "muted": self.muted,
            "fade_active": self.fade_active,
            "fade_progress": (
                round(self.fade_elapsed / self.fade_duration, 3)
                if self.fade_active and self.fade_duration > 0
                else 1.0
            ),
            "rms": round(self.smoothed_rms, 5),
            "rms_db": round(self.get_level_db(), 2),
            "peak": round(self.smoothed_peak, 5),
            "limiter": {
                "enabled": self.limiter_enabled,
                "threshold": self.limiter_threshold,
                "ratio": self.limiter_ratio,
                "clipped_samples": self.clipped_samples,
            },
            "normalization": {
                "enabled": self.normalization_enabled,
                "target_db": self.normalization_target_db,
                "max_gain": self.normalization_max_gain,
            },
            "updates": self.updates,
        }

    # =====================================================
    # INTERNOS
    # =====================================================

    def _compute_rms_peak(self, chunk: Any) -> Tuple[float, float]:
        """Calcula RMS y pico absoluto del chunk."""
        if self._np is not None:
            arr = self._np.asarray(chunk, dtype=self._np.float32)
            if arr.size == 0:
                return 0.0, 0.0
            rms = float(self._np.sqrt(self._np.mean(arr * arr)))
            peak = float(self._np.max(self._np.abs(arr)))
            return rms, peak

        if len(chunk) == 0:
            return 0.0, 0.0
        sq = 0.0
        peak = 0.0
        for x in chunk:
            fx = float(x)
            sq += fx * fx
            if abs(fx) > peak:
                peak = abs(fx)
        return math.sqrt(sq / len(chunk)), peak

    def _apply_limiter(self, arr: Any) -> Tuple[Any, int]:
        """Aplica un limitador suave (soft-knee) sobre un array numpy."""
        threshold = self.limiter_threshold
        knee = self.limiter_knee
        ratio = self.limiter_ratio
        knee_end = threshold + knee

        abs_arr = self._np.abs(arr)
        out = arr.copy()

        mask_soft = (abs_arr > threshold) & (abs_arr <= knee_end)
        if self._np.any(mask_soft):
            over = abs_arr[mask_soft] - threshold
            compressed = threshold + over / ratio
            out[mask_soft] = self._np.sign(arr[mask_soft]) * compressed

        mask_hard = abs_arr > knee_end
        clipped = int(self._np.sum(mask_hard))
        if clipped > 0:
            over = abs_arr[mask_hard] - knee_end
            compressed = knee_end + over / (ratio * 2.0)
            compressed = self._np.minimum(compressed, 1.0)
            out[mask_hard] = self._np.sign(arr[mask_hard]) * compressed

        return out, clipped

    def _apply_normalization(self, arr: Any) -> Any:
        """Normaliza el chunk hacia un objetivo de dB."""
        current_peak = float(self._np.max(self._np.abs(arr)))
        if current_peak < 1e-6:
            return arr

        target_linear = 10.0 ** (self.normalization_target_db / 20.0)
        gain = target_linear / current_peak
        gain = min(gain, self.normalization_max_gain)
        return arr * gain

    def _apply_normalization_list(self, chunk: List[float]) -> List[float]:
        """Normalización en modo puro Python."""
        current_peak = max((abs(float(x)) for x in chunk), default=0.0)
        if current_peak < 1e-6:
            return chunk
        target_linear = 10.0 ** (self.normalization_target_db / 20.0)
        gain = min(target_linear / current_peak, self.normalization_max_gain)
        return [x * gain for x in chunk]

    def _soft_limit(self, x: float) -> float:
        """Limitador suave simple para modo puro Python."""
        threshold = self.limiter_threshold
        if abs(x) <= threshold:
            return x
        sign = 1.0 if x >= 0 else -1.0
        over = abs(x) - threshold
        compressed = threshold + over / self.limiter_ratio
        return sign * min(compressed, 1.0)

    def _push_history(self, history: List[float], value: float):
        """Añade un valor al historial limitando su tamaño."""
        history.append(value)
        if len(history) > self.history_size:
            history.pop(0)

    @staticmethod
    def _apply_curve(t: float, curve: str) -> float:
        """Aplica una curva de easing al progreso."""
        t = max(0.0, min(1.0, t))
        if curve == "ease_in":
            return t * t
        if curve == "ease_out":
            return 1.0 - (1.0 - t) ** 2
        if curve == "ease_in_out":
            return 0.5 * (1.0 - math.cos(math.pi * t))
        return t

    @staticmethod
    def _clamp(value: float, min_v: float, max_v: float) -> float:
        """Limita un valor entre un mínimo y un máximo."""
        return max(min_v, min(max_v, value))

    @staticmethod
    def _smooth(current: float, target: float, factor: float) -> float:
        """Interpolación exponencial suave."""
        return current + (target - current) * factor