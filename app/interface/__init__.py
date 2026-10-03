# app/interface/__init__.py

"""
Modulo de interfaz de XARION 1.0.

Expone los controllers de control, configuracion y vista previa:

- ControlsController    -> acciones de control (play, speak, record, export...)
- ControlAction         -> enum de acciones disponibles
- SettingsController    -> carga, guardado y perfiles de configuracion
- SettingsProfile       -> perfiles (default, performance, quality, low_end...)
- DEFAULT_SETTINGS      -> valores por defecto
- PROFILE_PRESETS       -> perfiles predefinidos
- PreviewController     -> vista previa con modos y overlays
- PreviewMode           -> modos de vista previa
- OverlayType           -> overlays disponibles
"""

from app.interface.controls import (
    ControlsController,
    ControlAction,
)
from app.interface.settings import (
    SettingsController,
    SettingsProfile,
    DEFAULT_SETTINGS,
    PROFILE_PRESETS,
)
from app.interface.preview import (
    PreviewController,
    PreviewMode,
    OverlayType,
)

__all__ = [
    "ControlsController",
    "ControlAction",
    "SettingsController",
    "SettingsProfile",
    "DEFAULT_SETTINGS",
    "PROFILE_PRESETS",
    "PreviewController",
    "PreviewMode",
    "OverlayType",
]