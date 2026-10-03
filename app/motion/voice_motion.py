# app/motion/voice_motion.py

import math
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State, AudioFeatures


# =========================================================
# MODOS DE MOVIMIENTO POR VOZ
# =========================================================

class VoiceMotionMode(Enum):
    """Modos de reacción a la voz."""
    SUBTLE = "subtle"         # reacción sutil
    NATURAL = "natural"       # reacción natural
    EXPRESSIVE = "expressive" # reacción expresiva
    DRAMATIC = "dramatic"     # reacción dramática
    MINIMAL = "minimal"       # mínima reacción


# =========================================================
# PERFILES POR MODO
# =========================================================

VOICE_MODE_PROFILES: Dict[VoiceMotionMode, Dict[str, float]] = {
    VoiceMotionMode.SUBTLE:     {"head_amp": 0.020, "body_amp": 0.010, "mouth_boost": 0.20, "pitch_influence": 0.20, "energy_influence": 0.30, "smoothing": 0.18},
    VoiceMotionMode.NATURAL:    {"head_amp": 0.040, "body_amp": 0.020, "mouth_boost": 0.35, "pitch_influence": 0.35, "energy_influence": 0.50, "smoothing": 0.16},
    VoiceMotionMode.EXPRESSIVE: {"head_amp": 0.070, "body_amp": 0.035, "mouth_boost": 0.55, "pitch_influence": 0.55, "energy_influence": 0.70, "smoothing": 0.14},
    VoiceMotionMode.DRAMATIC:   {"head_amp": 0.110, "body_amp": 0.055, "mouth_boost": 0.75, "pitch_influence": 0.75, "energy_influence": 0.90, "smoothing": 0.12},
    VoiceMotionMode.MINIMAL:    {"head_amp": 0.010, "body_amp": 0.005, "mouth_boost": 0.10, "pitch_influence": 0.10, "energy_influence": 0.15, "smoothing": 0.22},
}


# =========================================================
# CONTROLADOR DE MOVIMIENTO POR VOZ
# =========================================================

class VoiceMotionController:
    """
    Controlador de movimiento reactivo a la voz de XARION-1.0.
    Convierte features del audio (RMS, pitch, energía, beat)
    en movimiento para cabeza, cuerpo y boca, con 5 modos
    de intensidad y suavizado adaptativo.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Modo activo ---
        self.mode: VoiceMotionMode = VoiceMotionMode.NATURAL
        self.profile: Dict[str, float] = VOICE_MODE_PROFILES[self.mode].copy()

        # --- Señales suavizadas ---
        self.rms_smoothed: float = 0.0
        self.pitch_smoothed: float = 0.0
        self.energy_smoothed: float = 0.0
        self.beat_smoothed: float = 0.0

        # --- Amplitudes por componente ---
        self.head_amplitude: float = self.profile["head_amp"]
        self.body_amplitude: float = self.profile["body_amp"]
        self.mouth_boost: float = self.profile["mouth_boost"]

        # --- Influencias ---
        self.pitch_influence: float = self.profile["pitch_influence"]
        self.energy_influence: float = self.profile["energy_influence"]

        # --- Fases internas ---
        self.head_phase_x: float = 0.0
        self.head_phase_y: float = 0.0
        self.body_phase_x: float = 0.0
        self.body_phase_y: float = 0.0

        # --- Velocidad de fases ---
        self.head_speed: float = 1.4
        self.body_speed: float = 1.0

        # --- Filtros ---
        self.rms_smoothing: float = self.profile["smoothing"]
        self.pitch_smoothing: float = 0.20
        self.energy_smoothing: float = 0.20
        self.beat_smoothing: float = 0.30

        # --- Ataque/liberación ---
        self.attack_time: float = 0.05
        self.release_time: float = 0.25

        # --- Estado ---
        self.enabled: bool = True
        self.suspended: bool = False
        self.intensity: float = 1.0

        # --- Backends ---
        self.head_controller = None
        self.body_controller = None
        self.mouth_controller = None

        # --- Estadísticas ---
        self.updates: int = 0
        self.peak_amplitude: float = 0.0
        self.last_update: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Reinicia el estado interno."""
        self.rms_smoothed = 0.0
        self.pitch_smoothed = 0.0
        self.energy_smoothed = 0.0
        self.beat_smoothed = 0.0
        self.head_phase_x = 0.0
        self.head_phase_y = 0.0
        self.body_phase_x = 0.0
        self.body_phase_y = 0.0
        self.peak_amplitude = 0.0
        self.last_update = time.time()

    def register(self, name: str, module: Any):
        """Registra submódulos de cabeza, cuerpo y boca."""
        if name == "head":
            self.head_controller = module
        elif name == "body":
            self.body_controller = module
        elif name == "mouth":
            self.mouth_controller = module

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """Actualiza el movimiento reactivo a voz cada frame."""
        if not self.enabled or self.suspended:
            return

        self.updates += 1

        features = state.audio.features
        if features is None:
            self._decay(delta)
            return

        # 1. Suavizar features
        self._smooth_features(features, delta)

        # 2. Calcular modulaciones
        head_mod = self._compute_head_modulation()
        body_mod = self._compute_body_modulation()
        mouth_mod = self._compute_mouth_modulation()

        # 3. Aplicar a cada componente
        self._apply_head_motion(head_mod, delta, state)
        self._apply_body_motion(body_mod, delta, state)
        self._apply_mouth_motion(mouth_mod, state)

        # 4. Delegar a submódulos si están registrados
        self._delegate(delta, state)

        self.last_update = time.time()

    # =====================================================
    # SUAVIZADO DE FEATURES
    # =====================================================

    def _smooth_features(self, features: AudioFeatures, delta: float):
        """Suaviza las features de audio con ataque/liberación."""
        rms = self._clamp(features.rms * 4.0, 0.0, 1.0)
        pitch_norm = self._clamp(features.pitch / 400.0, 0.0, 1.0)
        energy = self._clamp(
            (features.energy_band_low + features.energy_band_mid) * 0.5, 0.0, 1.0
        )
        beat = self._clamp(features.beat_strength, 0.0, 1.0)

        self.rms_smoothed = self._adaptive_smooth(
            self.rms_smoothed, rms, self.rms_smoothing, delta
        )
        self.pitch_smoothed = self._adaptive_smooth(
            self.pitch_smoothed, pitch_norm, self.pitch_smoothing, delta
        )
        self.energy_smoothed = self._adaptive_smooth(
            self.energy_smoothed, energy, self.energy_smoothing, delta
        )
        self.beat_smoothed = self._adaptive_smooth(
            self.beat_smoothed, beat, self.beat_smoothing, delta
        )

        self.peak_amplitude = max(self.peak_amplitude, self.rms_smoothed)

    def _adaptive_smooth(
        self, current: float, target: float, factor: float, delta: float
    ) -> float:
        """Suavizado adaptativo: ataque rápido, liberación suave."""
        if target > current:
            attack_factor = min(1.0, delta / max(1e-6, self.attack_time))
            factor = max(factor, attack_factor)
        else:
            release_factor = min(1.0, delta / max(1e-6, self.release_time))
            factor = min(factor, release_factor)
        return current + (target - current) * factor

    def _decay(self, delta: float):
        """Decae las señales cuando no hay audio."""
        decay = max(0.0, 1.0 - delta * 3.0)
        self.rms_smoothed *= decay
        self.pitch_smoothed *= decay
        self.energy_smoothed *= decay
        self.beat_smoothed *= decay

    # =====================================================
    # MODULACIONES
    # =====================================================

    def _compute_head_modulation(self) -> float:
        """Calcula la modulación de cabeza combinando señales."""
        base = self.rms_smoothed * self.energy_influence
        pitch = self.pitch_smoothed * self.pitch_influence
        beat = self.beat_smoothed * 0.3
        combined = base + pitch + beat
        return self._clamp(combined * self.intensity, 0.0, 2.0)

    def _compute_body_modulation(self) -> float:
        """Calcula la modulación de cuerpo."""
        base = self.rms_smoothed * 0.6
        energy = self.energy_smoothed * 0.4
        beat = self.beat_smoothed * 0.6
        combined = base + energy + beat
        return self._clamp(combined * self.intensity, 0.0, 2.0)

    def _compute_mouth_modulation(self) -> float:
        """Calcula la modulación de boca."""
        return self._clamp(
            self.rms_smoothed * self.mouth_boost * self.intensity, 0.0, 1.0
        )

    # =====================================================
    # APLICACIÓN A COMPONENTES
    # =====================================================

    def _apply_head_motion(self, mod: float, delta: float, state: State):
        """Aplica modulación a la cabeza."""
        # Avanzar fases con velocidad modulada por la señal
        speed_mod = 1.0 + self.rms_smoothed * 0.8
        self.head_phase_x += delta * self.head_speed * speed_mod * math.tau
        self.head_phase_y += delta * self.head_speed * speed_mod * math.tau * 0.7

        rx = math.sin(self.head_phase_x) * self.head_amplitude * mod
        ry = math.sin(self.head_phase_y) * self.head_amplitude * mod * 0.8
        rz = math.sin(self.head_phase_x * 0.5) * self.head_amplitude * mod * 0.4

        if self.head_controller is not None:
            if hasattr(self.head_controller, "set_rotation"):
                head = self.head_controller
                head.set_rotation(
                    head.rotation_x + rx,
                    head.rotation_y + ry,
                    head.rotation_z + rz,
                )
        else:
            head = state.avatar_components.head
            head.rotation_x += rx
            head.rotation_y += ry
            head.rotation_z += rz

    def _apply_body_motion(self, mod: float, delta: float, state: State):
        """Aplica modulación al cuerpo."""
        speed_mod = 1.0 + self.rms_smoothed * 0.6
        self.body_phase_x += delta * self.body_speed * speed_mod * math.tau
        self.body_phase_y += delta * self.body_speed * speed_mod * math.tau * 0.6

        px = math.sin(self.body_phase_x) * self.body_amplitude * mod
        py = math.sin(self.body_phase_y) * self.body_amplitude * mod * 0.7
        rz = math.sin(self.body_phase_x * 0.5) * self.body_amplitude * mod * 0.3

        if self.body_controller is not None:
            if hasattr(self.body_controller, "set_position"):
                body = self.body_controller
                body.set_position(
                    body.position_x + px,
                    body.position_y + py,
                    body.position_z,
                )
        else:
            body = state.avatar_components.body
            body.position_x += px
            body.position_y += py
            body.rotation_z += rz

    def _apply_mouth_motion(self, mod: float, state: State):
        """Aplica modulación a la boca."""
        if self.mouth_controller is not None:
            if hasattr(self.mouth_controller, "set_openness"):
                current = self.mouth_controller.openness
                self.mouth_controller.set_openness(max(current, mod))
        else:
            mouth = state.avatar_components.mouth
            mouth.openness = max(mouth.openness, mod)

    # =====================================================
    # DELEGACIÓN A SUBMÓDULOS
    # =====================================================

    def _delegate(self, delta: float, state: State):
        """Delega actualización a submódulos si aplica."""
        for module in (self.head_controller, self.body_controller, self.mouth_controller):
            if module is not None and hasattr(module, "update"):
                module.update(delta, state)

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def set_mode(self, mode: VoiceMotionMode):
        """Cambia el modo de reacción a voz."""
        if mode == self.mode:
            return
        self.mode = mode
        self.profile = VOICE_MODE_PROFILES[mode].copy()
        self._apply_profile()

    def _apply_profile(self):
        """Aplica el perfil a los parámetros internos."""
        self.head_amplitude = self.profile["head_amp"]
        self.body_amplitude = self.profile["body_amp"]
        self.mouth_boost = self.profile["mouth_boost"]
        self.pitch_influence = self.profile["pitch_influence"]
        self.energy_influence = self.profile["energy_influence"]
        self.rms_smoothing = self.profile["smoothing"]

    def set_intensity(self, intensity: float):
        """Ajusta la intensidad global."""
        self.intensity = self._clamp(intensity, 0.0, 2.0)

    def set_head_speed(self, speed: float):
        """Ajusta la velocidad de las fases de cabeza."""
        self.head_speed = max(0.1, speed)

    def set_body_speed(self, speed: float):
        """Ajusta la velocidad de las fases de cuerpo."""
        self.body_speed = max(0.1, speed)

    def set_attack_release(self, attack: Optional[float] = None,
                           release: Optional[float] = None):
        """Ajusta tiempos de ataque y liberación."""
        if attack is not None:
            self.attack_time = max(0.005, attack)
        if release is not None:
            self.release_time = max(0.01, release)

    def set_smoothing(self, rms: Optional[float] = None,
                      pitch: Optional[float] = None,
                      energy: Optional[float] = None,
                      beat: Optional[float] = None):
        """Ajusta los factores de suavizado."""
        if rms is not None:
            self.rms_smoothing = self._clamp(rms, 0.01, 1.0)
        if pitch is not None:
            self.pitch_smoothing = self._clamp(pitch, 0.01, 1.0)
        if energy is not None:
            self.energy_smoothing = self._clamp(energy, 0.01, 1.0)
        if beat is not None:
            self.beat_smoothing = self._clamp(beat, 0.01, 1.0)

    def enable(self, enabled: bool = True):
        """Activa o desactiva el controlador."""
        self.enabled = enabled

    def suspend(self):
        """Suspende la reacción a voz."""
        self.suspended = True

    def resume(self):
        """Reanuda la reacción a voz."""
        self.suspended = False

    def reset(self):
        """Reinicia el controlador."""
        self.initialize()

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_signals(self) -> Dict[str, float]:
        """Devuelve las señales suavizadas."""
        return {
            "rms": round(self.rms_smoothed, 4),
            "pitch": round(self.pitch_smoothed, 4),
            "energy": round(self.energy_smoothed, 4),
            "beat": round(self.beat_smoothed, 4),
        }

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "mode": self.mode.value,
            "enabled": self.enabled,
            "suspended": self.suspended,
            "intensity": round(self.intensity, 3),
            "signals": self.get_signals(),
            "amplitudes": {
                "head": self.head_amplitude,
                "body": self.body_amplitude,
                "mouth_boost": self.mouth_boost,
            },
            "influences": {
                "pitch": self.pitch_influence,
                "energy": self.energy_influence,
            },
            "speeds": {
                "head": self.head_speed,
                "body": self.body_speed,
            },
            "attack_release": {
                "attack": self.attack_time,
                "release": self.release_time,
            },
            "peak_amplitude": round(self.peak_amplitude, 4),
            "updates": self.updates,
        }

    def get_available_modes(self) -> List[str]:
        """Lista los modos disponibles."""
        return [m.value for m in VoiceMotionMode]

    # =====================================================
    # UTILIDADES
    # =====================================================

    @staticmethod
    def _clamp(value: float, min_v: float, max_v: float) -> float:
        """Limita un valor entre un mínimo y un máximo."""
        return max(min_v, min(max_v, value))