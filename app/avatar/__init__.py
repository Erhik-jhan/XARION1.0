# app/avatar/__init__.py

"""
Modulo de avatar de XARION 1.0.

Expone los controllers y utilidades para construir y animar
el avatar del sistema:

- AvatarLoader              -> carga de modelos (VRM, Live2D, PNG, custom)
- AvatarRenderer            -> renderizado por capas
- EyesController            -> control de ojos (mirada, apertura, brillo)
- BlinkController           -> control de parpadeo automatico y manual
- MouthController           -> control de boca y visemas
- Viseme                    -> enum de visemas disponibles
- PHONEME_TO_VISEME         -> mapeo de fonemas a visemas
- VISEME_PROFILES           -> perfiles de apertura/sonrisa/ancho por visema
- HeadMotionController      -> movimiento de cabeza (pitch, yaw, roll)
- HeadMotionMode            -> modos de cabeza
- BodyMotionController      -> movimiento corporal (posicion, rotacion, escala)
- BodyMotionMode            -> modos de cuerpo
"""

from app.avatar.loader import AvatarLoader
from app.avatar.renderer import AvatarRenderer
from app.avatar.eyes import EyesController
from app.avatar.blink import BlinkController
from app.avatar.mouth import (
    MouthController,
    Viseme,
    PHONEME_TO_VISEME,
    VISEME_PROFILES,
)
from app.avatar.head_motion import (
    HeadMotionController,
    HeadMotionMode,
    HEAD_MODE_PROFILES,
)
from app.avatar.body_motion import (
    BodyMotionController,
    BodyMotionMode,
    BODY_MODE_PROFILES,
)

__all__ = [
    "AvatarLoader",
    "AvatarRenderer",
    "EyesController",
    "BlinkController",
    "MouthController",
    "Viseme",
    "PHONEME_TO_VISEME",
    "VISEME_PROFILES",
    "HeadMotionController",
    "HeadMotionMode",
    "HEAD_MODE_PROFILES",
    "BodyMotionController",
    "BodyMotionMode",
    "BODY_MODE_PROFILES",
]