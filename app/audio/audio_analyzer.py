# app/audio/audio_analyzer.py

import math
import time
import wave
import importlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from app.core.config import Config
from app.core.state import State, AudioFeatures


# =========================================================
# ANALIZADOR DE AUDIO
# =========================================================

class AudioAnalyzer:
    """
    Analizador de audio de XARION-1.0.
    Extrae features en tiempo real desde un archivo o desde un
    stream: RMS, dB, pitch, centroide espectral, ZCR, bandas de
    energía, beats y detección de voz/fonema.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Fuente actual ---
        self.audio_path: Optional[str] = None
        self.audio_data: Optional[Any] = None
        self.sample_rate: int = self.config.SAMPLE_RATE
        self.channels: int = self.config.AUDIO_CHANNELS
        self.total_samples: int = 0
        self.duration: float = 0.0

        # --- Índice de lectura ---
        self.current_sample: int = 0
        self.current_time: float = 0.0
        self.chunk_size: int = self.config.AUDIO_CHUNK_SIZE

        # --- Features actuales ---
        self.features: AudioFeatures = AudioFeatures()

        # --- Detección de beats ---
        self.beat_history: List[float] = []
        self.beat_history_size: int = 43
        self.beat_threshold: float = 1.35
        self.last_beat_time: float = 0.0
        self.beat_min_interval: float = 0.15
        self.energy_history: List[float] = []

        # --- Detección de voz ---
        self.speech_rms_threshold: float = 0.02
        self.speech_pitch_min: float = 80.0
        self.speech_pitch_max: float = 400.0

        # --- Filtros de suavizado ---
        self.rms_smoothing: float = 0.20
        self.pitch_smoothing: float = 0.25
        self._smooth_rms: float = 0.0
        self._smooth_pitch: float = 0.0
        self._smooth_centroid: float = 0.0

        # --- Configuración de bandas ---
        self.band_low_max: float = 250.0
        self.band_mid_max: float = 2000.0
        self.band_high_max: float = 8000.0

        # --- Backend ---
        self.backend: str = "numpy"
        self._np = None
        self._librosa = None
        self._load_backend()

        # --- Estadísticas ---
        self.updates: int = 0
        self.last_update: float = 0.0
        self.total_beats: int = 0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el backend de análisis y limpia estado."""
        self._load_backend()
        self.beat_history.clear()
        self.energy_history.clear()
        self.current_sample = 0
        self.current_time = 0.0
        self.last_update = time.time()

    def _load_backend(self):
        """Carga numpy y librosa si están disponibles."""
        try:
            self._np = importlib.import_module("numpy")
        except Exception:
            self._np = None

        try:
            self._librosa = importlib.import_module("librosa")
            self.backend = "librosa"
        except Exception:
            self._librosa = None
            self.backend = "numpy" if self._np is not None else "basic"

    # =====================================================
    # CARGA DE AUDIO
    # =====================================================

    def load(self, path: str) -> bool:
        """Carga un archivo de audio WAV en memoria."""
        p = Path(path)
        if not p.exists():
            return False

        try:
            with wave.open(str(p), "rb") as w:
                self.channels = w.getnchannels()
                self.sample_rate = w.getframerate()
                self.total_samples = w.getnframes()
                self.duration = self.total_samples / float(self.sample_rate or 1)
                raw = w.readframes(self.total_samples)

            if self._np is not None:
                dtype = self._np.int16
                samples = self._np.frombuffer(raw, dtype=dtype).astype(self._np.float32)
                samples /= 32768.0
                if self.channels > 1:
                    samples = samples.reshape(-1, self.channels).mean(axis=1)
                self.audio_data = samples
            else:
                # Fallback: lista simple de ints
                self.audio_data = [
                    int.from_bytes(raw[i:i+2], "little", signed=True) / 32768.0
                    for i in range(0, len(raw), 2)
                ]

            self.audio_path = str(p)
            self.current_sample = 0
            self.current_time = 0.0
            return True

        except Exception as e:
            print(f"[AudioAnalyzer] Error al cargar {path}: {e}")
            return False

    def load_stream(self, samples: Any, sample_rate: int, channels: int = 1):
        """Carga audio directamente desde un array en memoria."""
        self.audio_data = samples
        self.sample_rate = sample_rate
        self.channels = channels
        if self._np is not None and hasattr(samples, "shape"):
            self.total_samples = samples.shape[0]
        else:
            self.total_samples = len(samples)
        self.duration = self.total_samples / float(sample_rate or 1)
        self.current_sample = 0
        self.current_time = 0.0

    # =====================================================
    # ANÁLISIS PRINCIPAL
    # =====================================================

    def analyze(self, chunk: Optional[Any] = None) -> AudioFeatures:
        """
        Analiza el siguiente chunk de audio y devuelve las features.
        Si `chunk` es None, lee desde la posición actual del audio cargado.
        """
        self.updates += 1
        self.last_update = time.time()

        if chunk is None:
            chunk = self._read_chunk()
            if chunk is None or len(chunk) == 0:
                return self.features

        # --- 1. RMS y dB ---
        rms = self._compute_rms(chunk)
        db = self._rms_to_db(rms)

        # --- 2. Zero crossing rate ---
        zcr = self._compute_zcr(chunk)

        # --- 3. Bandas de energía ---
        low, mid, high = self._compute_bands(chunk)

        # --- 4. Pitch ---
        pitch = self._compute_pitch(chunk)

        # --- 5. Centroide espectral ---
        centroid = self._compute_spectral_centroid(chunk)

        # --- 6. Beat detection ---
        beat_detected, beat_strength, bpm = self._detect_beat(rms)

        # --- 7. Detección de voz ---
        is_speech = (
            rms > self.speech_rms_threshold
            and self.speech_pitch_min <= pitch <= self.speech_pitch_max
        )

        # --- 8. Visema/fonema estimado ---
        phoneme = self._estimate_phoneme(rms, pitch, centroid, low, mid, high)

        # --- Suavizado ---
        self._smooth_rms = self._smooth(self._smooth_rms, rms, self.rms_smoothing)
        self._smooth_pitch = self._smooth(self._smooth_pitch, pitch, self.pitch_smoothing)
        self._smooth_centroid = self._smooth(self._smooth_centroid, centroid, self.pitch_smoothing)

        # --- Ensamblar features ---
        self.features = AudioFeatures(
            rms=self._smooth_rms,
            db=db,
            pitch=self._smooth_pitch,
            spectral_centroid=self._smooth_centroid,
            zero_crossing_rate=zcr,
            beat_detected=beat_detected,
            beat_strength=beat_strength,
            rhythm_bpm=bpm,
            is_speech=is_speech,
            phoneme=phoneme,
            energy_band_low=low,
            energy_band_mid=mid,
            energy_band_high=high,
        )

        return self.features

    # =====================================================
    # LECTURA DE CHUNKS
    # =====================================================

    def _read_chunk(self) -> Optional[Any]:
        """Lee el siguiente chunk desde audio_data."""
        if self.audio_data is None:
            return None

        if self.current_sample >= self.total_samples:
            return None

        end = min(self.current_sample + self.chunk_size, self.total_samples)

        if self._np is not None and hasattr(self.audio_data, "__getitem__"):
            chunk = self.audio_data[self.current_sample:end]
        else:
            chunk = self.audio_data[self.current_sample:end]

        self.current_sample = end
        self.current_time = self.current_sample / float(self.sample_rate or 1)

        return chunk

    # =====================================================
    # CÁLCULOS BÁSICOS
    # =====================================================

    def _compute_rms(self, chunk: Any) -> float:
        """Calcula el RMS de un chunk de audio."""
        if self._np is not None:
            arr = self._np.asarray(chunk, dtype=self._np.float32)
            if arr.size == 0:
                return 0.0
            return float(self._np.sqrt(self._np.mean(arr * arr)))
        # Fallback puro Python
        if len(chunk) == 0:
            return 0.0
        return math.sqrt(sum(float(x) * float(x) for x in chunk) / len(chunk))

    @staticmethod
    def _rms_to_db(rms: float) -> float:
        """Convierte RMS a decibelios."""
        if rms <= 1e-9:
            return -60.0
        return 20.0 * math.log10(rms)

    def _compute_zcr(self, chunk: Any) -> float:
        """Calcula la tasa de cruces por cero."""
        if self._np is not None:
            arr = self._np.asarray(chunk, dtype=self._np.float32)
            if arr.size < 2:
                return 0.0
            sign = self._np.sign(arr)
            sign[sign == 0] = 1
            return float(self._np.mean(self._np.abs(self._np.diff(sign)) / 2.0))
        if len(chunk) < 2:
            return 0.0
        crossings = 0
        prev = chunk[0]
        for x in chunk[1:]:
            if (prev >= 0) != (x >= 0):
                crossings += 1
            prev = x
        return crossings / float(len(chunk) - 1)

    # =====================================================
    # BANDAS DE ENERGÍA
    # =====================================================

    def _compute_bands(self, chunk: Any) -> Tuple[float, float, float]:
        """Calcula energía por bandas: low, mid, high."""
        if self._np is None:
            # Estimación básica por RMS
            rms = self._compute_rms(chunk)
            return rms * 0.5, rms * 0.35, rms * 0.15

        arr = self._np.asarray(chunk, dtype=self._np.float32)
        if arr.size < 8:
            return 0.0, 0.0, 0.0

        spectrum = self._np.abs(self._np.fft.rfft(arr))
        freqs = self._np.fft.rfftfreq(arr.size, d=1.0 / self.sample_rate)

        low_mask = freqs < self.band_low_max
        mid_mask = (freqs >= self.band_low_max) & (freqs < self.band_mid_max)
        high_mask = (freqs >= self.band_mid_max) & (freqs < self.band_high_max)

        total = self._np.sum(spectrum) + 1e-9
        low = float(self._np.sum(spectrum[low_mask]) / total)
        mid = float(self._np.sum(spectrum[mid_mask]) / total)
        high = float(self._np.sum(spectrum[high_mask]) / total)
        return low, mid, high

    # =====================================================
    # PITCH
    # =====================================================

    def _compute_pitch(self, chunk: Any) -> float:
        """Estima la frecuencia fundamental (pitch) con autocorrelación."""
        if self._np is None:
            return 0.0

        arr = self._np.asarray(chunk, dtype=self._np.float32)
        if arr.size < 256:
            return 0.0

        # Autocorrelación por FFT
        arr = arr - self._np.mean(arr)
        corr = self._np.fft.irfft(self._np.abs(self._np.fft.rfft(arr)) ** 2)

        min_lag = int(self.sample_rate / self.speech_pitch_max)
        max_lag = int(self.sample_rate / self.speech_pitch_min)
        if max_lag >= corr.size:
            max_lag = corr.size - 1

        if min_lag >= max_lag:
            return 0.0

        segment = corr[min_lag:max_lag]
        if segment.size == 0:
            return 0.0

        peak_index = int(self._np.argmax(segment)) + min_lag
        if peak_index <= 0:
            return 0.0

        return float(self.sample_rate / peak_index)

    # =====================================================
    # CENTROIDE ESPECTRAL
    # =====================================================

    def _compute_spectral_centroid(self, chunk: Any) -> float:
        """Calcula el centroide espectral (brillo del sonido)."""
        if self._np is None:
            return 0.0

        arr = self._np.asarray(chunk, dtype=self._np.float32)
        if arr.size < 8:
            return 0.0

        spectrum = self._np.abs(self._np.fft.rfft(arr))
        freqs = self._np.fft.rfftfreq(arr.size, d=1.0 / self.sample_rate)

        total = self._np.sum(spectrum) + 1e-9
        centroid = float(self._np.sum(freqs * spectrum) / total)
        return centroid

    # =====================================================
    # BEAT DETECTION
    # =====================================================

    def _detect_beat(self, rms: float) -> Tuple[bool, float, float]:
        """Detecta beats usando un umbral dinámico sobre el historial de energía."""
        self.energy_history.append(rms)
        if len(self.energy_history) > self.beat_history_size:
            self.energy_history.pop(0)

        if len(self.energy_history) < 8:
            return False, 0.0, 0.0

        local_avg = sum(self.energy_history) / len(self.energy_history)
        threshold = local_avg * self.beat_threshold

        now = time.time()
        beat_detected = False
        beat_strength = 0.0

        if rms > threshold and (now - self.last_beat_time) > self.beat_min_interval:
            beat_detected = True
            self.total_beats += 1
            self.last_beat_time = now
            beat_strength = min(1.0, rms / (threshold + 1e-9) - 1.0)
            self.beat_history.append(now)

        # BPM estimado
        bpm = 0.0
        if len(self.beat_history) >= 2:
            recent = self.beat_history[-8:]
            intervals = [recent[i+1] - recent[i] for i in range(len(recent) - 1)]
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                if avg_interval > 0:
                    bpm = 60.0 / avg_interval

        return beat_detected, beat_strength, bpm

    # =====================================================
    # ESTIMACIÓN DE FONEMA
    # =====================================================

    def _estimate_phoneme(
        self,
        rms: float,
        pitch: float,
        centroid: float,
        low: float,
        mid: float,
        high: float,
    ) -> str:
        """
        Estimación heurística del fonema dominante.
        No es un reconocedor real: es un mapeo de bajo nivel.
        """
        if rms < self.speech_rms_threshold:
            return "silence"

        # Vocales: pitch bajo-medio y centroide contenido
        if pitch > 0:
            if 80 <= pitch <= 180:
                if low > 0.5:
                    return "o"
                if high > 0.35:
                    return "a"
                return "u"
            elif 180 < pitch <= 260:
                if mid > 0.5:
                    return "e"
                return "a"
            elif 260 < pitch <= 400:
                return "i"

        # Consonantes sordas: alta energía en altas frecuencias
        if high > 0.45 and centroid > 3000:
            return "s"

        # Fricativas
        if centroid > 2200 and mid > 0.35:
            return "f"

        # Nasales
        if low > 0.55 and centroid < 1200:
            return "m"

        # Laterales / vibrantes
        if 1200 < centroid < 2200 and low > 0.3:
            return "l"

        return "neutral"

    # =====================================================
    # CONTROL DE REPRODUCCIÓN
    # =====================================================

    def reset_position(self):
        """Reinicia la posición de lectura al inicio."""
        self.current_sample = 0
        self.current_time = 0.0

    def seek(self, time_seconds: float):
        """Salta a un punto concreto del audio."""
        self.current_time = max(0.0, min(time_seconds, self.duration))
        self.current_sample = int(self.current_time * self.sample_rate)

    def is_finished(self) -> bool:
        """Indica si ya se procesó todo el audio."""
        return self.audio_data is None or self.current_sample >= self.total_samples

    def progress(self) -> float:
        """Progreso de lectura (0.0 a 1.0)."""
        if self.total_samples <= 0:
            return 0.0
        return min(1.0, self.current_sample / float(self.total_samples))

    # =====================================================
    # CONFIGURACIÓN
    # =====================================================

    def set_chunk_size(self, size: int):
        """Ajusta el tamaño de chunk de análisis."""
        self.chunk_size = max(64, int(size))

    def set_speech_threshold(self, rms_threshold: float):
        """Ajusta el umbral de RMS para considerar voz."""
        self.speech_rms_threshold = max(0.0, rms_threshold)

    def set_beat_threshold(self, threshold: float):
        """Ajusta el umbral relativo de detección de beats."""
        self.beat_threshold = max(1.0, threshold)

    def set_smoothing(self, rms: Optional[float] = None,
                      pitch: Optional[float] = None):
        """Ajusta factores de suavizado."""
        if rms is not None:
            self.rms_smoothing = max(0.0, min(1.0, rms))
        if pitch is not None:
            self.pitch_smoothing = max(0.0, min(1.0, pitch))

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_features(self) -> AudioFeatures:
        """Devuelve las features actuales."""
        return self.features

    def get_waveform(self, num_points: int = 512) -> List[float]:
        """Devuelve una versión reducida de la forma de onda para visualización."""
        if self.audio_data is None:
            return []

        if self._np is not None:
            arr = self._np.asarray(self.audio_data, dtype=self._np.float32)
            if arr.size == 0:
                return []
            step = max(1, arr.size // num_points)
            reduced = arr[::step][:num_points]
            return [float(x) for x in reduced]

        step = max(1, len(self.audio_data) // num_points)
        return [float(x) for x in self.audio_data[::step][:num_points]]

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del analizador."""
        return {
            "backend": self.backend,
            "audio_path": self.audio_path,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "duration": round(self.duration, 3),
            "current_time": round(self.current_time, 3),
            "progress": round(self.progress(), 4),
            "is_finished": self.is_finished(),
            "features": {
                "rms": round(self.features.rms, 5),
                "db": round(self.features.db, 2),
                "pitch": round(self.features.pitch, 2),
                "spectral_centroid": round(self.features.spectral_centroid, 2),
                "zcr": round(self.features.zero_crossing_rate, 5),
                "beat": self.features.beat_detected,
                "beat_strength": round(self.features.beat_strength, 3),
                "bpm": round(self.features.rhythm_bpm, 2),
                "is_speech": self.features.is_speech,
                "phoneme": self.features.phoneme,
                "bands": {
                    "low": round(self.features.energy_band_low, 3),
                    "mid": round(self.features.energy_band_mid, 3),
                    "high": round(self.features.energy_band_high, 3),
                },
            },
            "total_beats": self.total_beats,
            "updates": self.updates,
        }

    # =====================================================
    # UTILIDADES
    # =====================================================

    @staticmethod
    def _smooth(current: float, target: float, factor: float) -> float:
        """Interpolación exponencial suave."""
        return current + (target - current) * factor