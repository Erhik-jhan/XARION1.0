# app/motion/__init__.py

"""
Modulo de movimiento de XARION 1.0.

Expone los controllers y utilidades para generar movimiento
natural en el avatar:

- MotionEngine             -> motor central que combina senales
- MotionMode               -> modos de movimiento (idle, voice, rhythm, etc.)
- MOTION_MODE_PROFILES     -> perfiles por modo
- SmoothingController      -> suavizado avanzado (lerp, spring, etc.)
- SmoothingType            -> tipos de suavizado
- IdleMotionController     -> movimiento en reposo
- IdleMode                 -> modos de reposo
- IDLE_MODE_PROFILES       -> perfiles por modo de reposo
- VoiceMotionController    -> movimiento reactivo a la voz
- VoiceMotionMode          -> modos de reaccion a voz
- VOICE_MODE_PROFILES      -> perfiles por modo de voz
"""

from app.motion.motion_engine import (
    MotionEngine,
    MotionMode,
    MOTION_MODE_PROFILES,
)
from app.motion.smoothing import (
    SmoothingController,
    SmoothingType,
)
from app.motion.idle_motion import (
    IdleMotionController,
    IdleMode,
    IDLE_MODE_PROFILES,
)
from app.motion.voice_motion import (
    VoiceMotionController,
    VoiceMotionMode,
    VOICE_MODE_PROFILES,
)

__all__ = [
    "MotionEngine",
    "MotionMode",
    "MOTION_MODE_PROFILES",
    "SmoothingController",
    "SmoothingType",
    "IdleMotionController",
    "IdleMode",
    "IDLE_MODE_PROFILES",
    "VoiceMotionController",
    "VoiceMotionMode",
    "VOICE_MODE_PROFILES",
]