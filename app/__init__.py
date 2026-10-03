# app/__init__.py

"""
XARION 1.0 - Paquete principal.

Estructura interna:

- core        -> motor, configuracion y estado global
- avatar      -> cargador, renderizador y controllers del avatar
- audio       -> TTS, analizador, volumen, ritmo y sincronizacion
- motion      -> motor de movimiento, suavizado, idle y voz
- gestures    -> gestos neutral, pregunta y habla
- interface   -> controles, ajustes y vista previa
- output      -> grabador y exportador de video
"""

__version__ = "1.0.0"
__project__ = "XARION"
__author__ = "XARION"
__license__ = "MIT"

__all__ = [
    "core",
    "avatar",
    "audio",
    "motion",
    "gestures",
    "interface",
    "output",
]