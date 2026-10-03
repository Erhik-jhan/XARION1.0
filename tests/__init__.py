# tests/__init__.py

"""
Paquete de tests de XARION 1.0.

Contiene las pruebas unitarias de todos los modulos del sistema:

- test_core.py        -> Config, State, Engine
- test_avatar.py      -> Loader, Renderer, Eyes, Blink, Mouth, Head, Body
- test_audio.py       -> TTS, Analyzer, Volume, Rhythm, Sync
- test_motion.py      -> MotionEngine, Smoothing, Idle, Voice
- test_gestures.py    -> Neutral, Question, Talking
- test_interface.py   -> Controls, Settings, Preview
- test_output.py      -> Recorder, VideoExporter

Uso:
    python -m unittest discover tests/
    pytest tests/
"""

import os
import sys
from pathlib import Path

# ------------------------------------------------------------
# Asegurar que la raiz del proyecto este en el path
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ------------------------------------------------------------
# Metadata del paquete
# ------------------------------------------------------------
__version__ = "1.0.0"
__project__ = "XARION"
__all__ = [
    "test_core",
    "test_avatar",
    "test_audio",
    "test_motion",
    "test_gestures",
    "test_interface",
    "test_output",
]