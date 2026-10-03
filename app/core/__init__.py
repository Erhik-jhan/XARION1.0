# app/core/__init__.py

"""
Nucleo de XARION 1.0.

Expone las clases principales del core:

- Config           -> configuracion global del sistema
- State            -> estado global (avatar, audio, motion, gestos, grabacion)
- EngineState      -> enum de estados del motor
- AvatarState      -> enum de estados del avatar
- AudioState       -> enum de estados del audio
- MotionState      -> enum de estados del movimiento
- GestureType      -> enum de gestos disponibles
- RecordingState   -> enum de estados de grabacion
- XarionEngine     -> motor principal que orquesta el pipeline
"""

from app.core.config import Config
from app.core.state import (
    State,
    EngineState,
    AvatarState,
    AudioState,
    MotionState,
    GestureType,
    RecordingState,
    EyesState,
    BlinkState,
    MouthState,
    HeadMotionState,
    BodyMotionState,
    AntennaState,
    AvatarComponents,
    AudioFeatures,
    AudioStateData,
    MotionStateData,
    GestureState,
    RecordingStateData,
)
from app.core.engine import XarionEngine

__all__ = [
    "Config",
    "State",
    "EngineState",
    "AvatarState",
    "AudioState",
    "MotionState",
    "GestureType",
    "RecordingState",
    "EyesState",
    "BlinkState",
    "MouthState",
    "HeadMotionState",
    "BodyMotionState",
    "AntennaState",
    "AvatarComponents",
    "AudioFeatures",
    "AudioStateData",
    "MotionStateData",
    "GestureState",
    "RecordingStateData",
    "XarionEngine",
]