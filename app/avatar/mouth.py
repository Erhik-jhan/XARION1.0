# app/avatar/mouth.py

import math
import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State, MouthState, AudioFeatures


# =========================================================
# VISEMAS
# =========================================================

class Viseme(Enum):
    """Visemas básicos para sincronización labial de XARION."""
    SILENCE = "silence"      # boca cerrada / reposo
    A = "A"                  # abierta grande
    E = "E"                  # semiabierta horizontal
    I = "I"                  # estirada
    O = "O"                  # redonda
    U = "U"                  # pequeña redonda
    M = "M"                  # cerrada con labios juntos
    F = "F"                  # labio inferior contra dientes
    S = "S"                  # sibilante estrecha
    L = "L"                  # lengua visible
    R = "R"                  # semiabierta con lengua
    TH = "TH"                # lengua entre dientes
    NEUTRAL = "neutral"      # sin clasificar


# Mapeo fonema → visema (español básico)
PHONEME_TO_VISEME: Dict[str, Viseme] = {
    "a": Viseme.A, "á": Viseme.A,
    "e": Viseme.E, "é": Viseme.E,
    "i": Viseme.I, "í": Viseme.I, "y": Viseme.I,
    "o": Viseme.O, "ó": Viseme.O,
    "u": Viseme.U, "ú": Viseme.U, "ü": Viseme.U,
    "m": Viseme.M, "b": Viseme.M, "p": Viseme.M,
    "f": Viseme.F, "v": Viseme.F,
    "s": Viseme.S, "z": Viseme.S, "c": Viseme.S,
    "l": Viseme.L,
    "r": Viseme.R, "rr": Viseme.R,
    "t": Viseme.TH, "d": Viseme.TH,
    "n": Viseme.NEUTRAL, "ñ": Viseme.NEUTRAL,
    "k": Viseme.NEUTRAL, "g": Viseme.NEUTRAL, "j": Viseme.NEUTRAL,
    " ": Viseme.SILENCE,
}


# =========================================================
# PERFILES DE VISEMA (apertura, sonrisa, ancho)
# =========================================================

VISEME_PROFILES: Dict[Viseme, Dict[str, float]] = {
    Viseme.SILENCE:  {"openness": 0.00, "smile": 0.50, "width": 0.50},
    Viseme.A:        {"openness": 0.95, "smile": 0.40, "width": 0.70},
    Viseme.E:        {"openness": 0.55, "smile": 0.60, "width": 0.80},
    Viseme.I:        {"openness": 0.35, "smile": 0.70, "width": 0.90},
    Viseme.O:        {"openness": 0.75, "smile": 0.45, "width": 0.40},
    Viseme.U:        {"openness": 0.45, "smile": 0.40, "width": 0.30},
    Viseme.M:        {"openness": 0.00, "smile": 0.55, "width": 0.50},
    Viseme.F:        {"openness": 0.20, "smile": 0.55, "width": 0.60},
    Viseme.S:        {"openness": 0.15, "smile": 0.65, "width": 0.70},
    Viseme.L:        {"openness": 0.40, "smile": 0.55, "width": 0.60},
    Viseme.R:        {"openness": 0.35, "smile": 0.55, "width": 0.55},
    Viseme.TH:       {"openness": 0.25, "smile": 0.55, "width": 0.65},
    Viseme.NEUTRAL:  {"openness": 0.20, "smile": 0.55, "width": 0.55},
}


# =========================================================
# CONTROLADOR DE BOCA
# =========================================================

class MouthController:
    """
    Controlador avanzado de la boca del avatar XARION-1.0.
    Gestiona visemas, coarticulación, sonrisa dinámica,
    intensidad de glow y sincronización con audio.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Estado actual ---
        self.openness = 0.0
        self.target_openness = 0.0

        self.smile = 0.55
        self.target_smile = 0.55

        self.width = 0.55
        self.target_width = 0.55

        self.glow_intensity = 1.0
        self.target_glow = 1.0

        self.color: Tuple[int, int, int] = (0, 255, 100)

        # --- Visema ---
        self.current_viseme: Viseme = Viseme.SILENCE
        self.target_viseme: Viseme = Viseme.SILENCE
        self.viseme_transition = 0.0
        self.viseme_transition_duration = 0.08

        # --- Coarticulación ---
        self.coarticulation_enabled = True
        self.coarticulation_window = 3
        self.recent_visemes: List[Viseme] = []
        self.coarticulation_weight = 0.25

        # --- Modo ---
        self.mode = "auto"       # "auto" | "audio" | "text" | "manual"
        self.audio_reactive = True

        # --- Suavizado ---
        self.smoothing = 0.22
        self.glow_smoothing = 0.12
        self.smile_smoothing = 0.08

        # --- Reposo ---
        self.rest_smile = 0.55
        self.rest_openness = 0.0
        self.idle_breath_amplitude = 0.01
        self.breath_phase = 0.0

        # --- Estadísticas ---
        self.updates = 0
        self.viseme_changes = 0
        self.last_update = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el estado interno de la boca."""
        self._apply_viseme_profile(Viseme.SILENCE, instant=True)
        self.breath_phase = 0.0
        self.last_update = time.time()

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """
        Actualiza la boca cada frame según el estado global y el audio.
        """
        self.updates += 1

        # 1. Reaccionar al audio si está activo
        if self.audio_reactive and state.audio.state.value == "playing":
            self._react_to_audio(state.audio.features)

        # 2. Aplicar coarticulación si hay transición de visema
        if self.coarticulation_enabled:
            self._apply_coarticulation()

        # 3. Respiración sutil en reposo
        self._apply_idle_breath(delta)

        # 4. Suavizado hacia objetivos
        self.openness = self._smooth(self.openness, self.target_openness, self.smoothing)
        self.smile = self._smooth(self.smile, self.target_smile, self.smile_smoothing)
        self.width = self._smooth(self.width, self.target_width, self.smoothing)
        self.glow_intensity = self._smooth(
            self.glow_intensity, self.target_glow, self.glow_smoothing
        )

        # 5. Limitar
        self.openness = self._clamp(self.openness, 0.0, 1.0)
        self.smile = self._clamp(self.smile, 0.0, 1.0)
        self.width = self._clamp(self.width, 0.2, 1.0)
        self.glow_intensity = self._clamp(self.glow_intensity, 0.0, 2.0)

        # 6. Volcar al estado global
        self._write_to_state(state)
        self.last_update = time.time()

    def _react_to_audio(self, features: AudioFeatures):
        """Ajusta la boca según las features del audio."""
        if features is None:
            return

        # Apertura basada en RMS normalizado
        rms_norm = self._clamp(features.rms * 4.0, 0.0, 1.0)
        self.target_openness = max(self.target_openness * 0.4, rms_norm)

        # Glow reactivo a energía
        energy = (features.energy_band_low + features.energy_band_mid) * 0.5
        self.target_glow = 1.0 + self._clamp(energy * 2.0, 0.0, 0.8)

        # Visema si el analyzer detecta fonema
        if features.phoneme and features.phoneme != "neutral":
            new_viseme = PHONEME_TO_VISEME.get(
                features.phoneme.lower(), Viseme.NEUTRAL
            )
            self.set_viseme(new_viseme)

    def _apply_coarticulation(self):
        """Mezcla el visema actual con los vecinos recientes."""
        if not self.recent_visemes:
            return

        weights = []
        total_weight = 0.0
        blended_open = 0.0
        blended_smile = 0.0
        blended_width = 0.0

        for i, v in enumerate(self.recent_visemes[-self.coarticulation_window:]):
            w = self.coarticulation_weight ** (len(self.recent_visemes) - i)
            profile = VISEME_PROFILES.get(v, VISEME_PROFILES[Viseme.NEUTRAL])
            blended_open += profile["openness"] * w
            blended_smile += profile["smile"] * w
            blended_width += profile["width"] * w
            total_weight += w
            weights.append(w)

        if total_weight > 0:
            self.target_openness = blended_open / total_weight
            self.target_smile = blended_smile / total_weight
            self.target_width = blended_width / total_weight

    def _apply_idle_breath(self, delta: float):
        """Añade micro-respiración cuando la boca está en reposo."""
        if self.target_openness > 0.05:
            return
        self.breath_phase += delta * 1.5
        breath = math.sin(self.breath_phase) * self.idle_breath_amplitude
        self.target_openness = max(0.0, self.rest_openness + breath)

    def _write_to_state(self, state: State):
        """Escribe los valores internos en el estado global."""
        mouth = state.avatar_components.mouth
        mouth.openness = self.openness
        mouth.smile = self.smile
        mouth.viseme = self.current_viseme.value
        mouth.glow_intensity = self.glow_intensity
        mouth.color = self.color

    # =====================================================
    # API PÚBLICA
    # =====================================================

    def set_viseme(self, viseme: Viseme, duration: float = 0.08):
        """Cambia el visema actual aplicando su perfil."""
        if viseme == self.current_viseme:
            return

        self.target_viseme = viseme
        self.viseme_transition = 0.0
        self.viseme_transition_duration = max(0.03, duration)
        self.viseme_changes += 1

        self.recent_visemes.append(viseme)
        if len(self.recent_visemes) > 8:
            self.recent_visemes.pop(0)

        self._apply_viseme_profile(viseme)

    def set_phoneme(self, phoneme: str):
        """Convierte un fonema a visema y lo aplica."""
        v = PHONEME_TO_VISEME.get(phoneme.lower(), Viseme.NEUTRAL)
        self.set_viseme(v)

    def set_text(self, text: str):
        """Convierte un texto completo en una secuencia de visemas."""
        if not text:
            return
        self.recent_visemes.clear()
        for ch in text.lower():
            if ch in PHONEME_TO_VISEME:
                self.recent_visemes.append(PHONEME_TO_VISEME[ch])

    def _apply_viseme_profile(self, viseme: Viseme, instant: bool = False):
        """Aplica el perfil del visema a los objetivos."""
        profile = VISEME_PROFILES.get(viseme, VISEME_PROFILES[Viseme.NEUTRAL])

        if instant:
            self.openness = profile["openness"]
            self.smile = profile["smile"]
            self.width = profile["width"]
            self.target_openness = self.openness
            self.target_smile = self.smile
            self.target_width = self.width
        else:
            self.target_openness = profile["openness"]
            self.target_smile = profile["smile"]
            self.target_width = profile["width"]

    def set_openness(self, value: float):
        """Ajusta manualmente la apertura."""
        self.target_openness = self._clamp(value, 0.0, 1.0)

    def set_smile(self, value: float):
        """Ajusta manualmente la sonrisa."""
        self.target_smile = self._clamp(value, 0.0, 1.0)

    def set_width(self, value: float):
        """Ajusta manualmente el ancho de la boca."""
        self.target_width = self._clamp(value, 0.2, 1.0)

    def set_glow(self, intensity: float):
        """Ajusta la intensidad del brillo verde."""
        self.target_glow = self._clamp(intensity, 0.0, 2.0)

    def set_color(self, r: int, g: int, b: int):
        """Cambia el color de la boca."""
        self.color = (
            int(self._clamp(r, 0, 255)),
            int(self._clamp(g, 0, 255)),
            int(self._clamp(b, 0, 255)),
        )

    def set_mode(self, mode: str):
        """Cambia el modo: auto, audio, text, manual."""
        if mode in ("auto", "audio", "text", "manual"):
            self.mode = mode
            self.audio_reactive = mode in ("auto", "audio")

    def set_smoothing(self, value: float):
        """Ajusta el suavizado de la apertura."""
        self.smoothing = self._clamp(value, 0.02, 1.0)

    def enable_coarticulation(self, enabled: bool = True):
        """Activa o desactiva la coarticulación."""
        self.coarticulation_enabled = enabled

    def reset(self):
        """Reinicia la boca a reposo."""
        self.recent_visemes.clear()
        self.set_viseme(Viseme.SILENCE, duration=0.1)
        self.target_smile = self.rest_smile
        self.target_glow = 1.0

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_state(self) -> MouthState:
        """Devuelve el estado actual de la boca."""
        return MouthState(
            openness=self.openness,
            smile=self.smile,
            viseme=self.current_viseme.value,
            glow_intensity=self.glow_intensity,
            color=self.color,
        )

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "openness": round(self.openness, 3),
            "target_openness": round(self.target_openness, 3),
            "smile": round(self.smile, 3),
            "width": round(self.width, 3),
            "glow": round(self.glow_intensity, 3),
            "color": self.color,
            "viseme": self.current_viseme.value,
            "target_viseme": self.target_viseme.value,
            "mode": self.mode,
            "audio_reactive": self.audio_reactive,
            "coarticulation": self.coarticulation_enabled,
            "viseme_changes": self.viseme_changes,
            "updates": self.updates,
        }

    def get_available_visemes(self) -> List[str]:
        """Lista los visemas disponibles."""
        return [v.value for v in Viseme]

    def get_viseme_profile(self, viseme: Viseme) -> Dict[str, float]:
        """Devuelve el perfil de un visema concreto."""
        return VISEME_PROFILES.get(viseme, VISEME_PROFILES[Viseme.NEUTRAL]).copy()

    # =====================================================
    # UTILIDADES
    # =====================================================

    @staticmethod
    def _clamp(value: float, min_v: float, max_v: float) -> float:
        """Limita un valor entre un mínimo y un máximo."""
        return max(min_v, min(max_v, value))

    @staticmethod
    def _smooth(current: float, target: float, factor: float) -> float:
        """Interpolación exponencial suave hacia el objetivo."""
        return current + (target - current) * factor