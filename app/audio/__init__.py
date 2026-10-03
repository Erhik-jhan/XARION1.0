# app/audio/__init__.py

"""
Modulo de audio de XARION 1.0.

Expone los controllers y utilidades para sintesis de voz,
analisis de audio, control de volumen, ritmo y sincronizacion:

- TTSController              -> sintesis de voz multi-motor
- TTSEngine                  -> enum de motores TTS
- DEFAULT_VOICES             -> voces por defecto por motor e idioma
- AudioAnalyzer              -> extraccion de features (RMS, pitch, beats)
- VolumeController           -> volumen, mute, fade, limitador
- RhythmController           -> deteccion de beats, BPM, downbeats
- SynchronizationController  -> sincronizacion audio-avatar
- SyncMode                   -> modos de sincronizacion
"""

from app.audio.tts import (
    TTSController,
    TTSEngine,
    DEFAULT_VOICES,
)
from app.audio.audio_analyzer import AudioAnalyzer
from app.audio.volume import VolumeController
from app.audio.rhythm import RhythmController
from app.audio.synchronization import (
    SynchronizationController,
    SyncMode,
    SYNC_PROFILES,
)

__all__ = [
    "TTSController",
    "TTSEngine",
    "DEFAULT_VOICES",
    "AudioAnalyzer",
    "VolumeController",
    "RhythmController",
    "SynchronizationController",
    "SyncMode",
    "SYNC_PROFILES",
]