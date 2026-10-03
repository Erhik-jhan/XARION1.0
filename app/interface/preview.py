# app/interface/preview.py

import time
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from app.core.config import Config
from app.core.state import State, EngineState


# =========================================================
# MODOS DE VISTA PREVIA
# =========================================================

class PreviewMode(Enum):
    """Modos de vista previa."""
    NORMAL = "normal"           # renderizado estándar
    WIREFRAME = "wireframe"     # solo estructura
    DEBUG = "debug"             # overlay de datos
    GRID = "grid"               # con rejilla de referencia
    OVERLAY = "overlay"         # capa semitransparente
    COMPACT = "compact"         # mini preview


# =========================================================
# OVERLAYS DISPONIBLES
# =========================================================

class OverlayType(Enum):
    """Tipos de overlay informativos."""
    FPS = "fps"
    FRAME = "frame"
    STATE = "state"
    SIGNALS = "signals"
    BOUNDS = "bounds"
    GRID = "grid"
    TIMER = "timer"
    RECORDING = "recording"


# =========================================================
# CONTROLADOR DE VISTA PREVIA
# =========================================================

class PreviewController:
    """
    Controlador de vista previa de XARION-1.0.
    Gestiona el canvas de previsualización, el modo de vista,
    los overlays informativos y los snapshots del estado.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # --- Modo de vista ---
        self.mode: PreviewMode = PreviewMode.NORMAL
        self.mode_previous: PreviewMode = PreviewMode.NORMAL

        # --- Overlays activos ---
        self.overlays: List[OverlayType] = [
            OverlayType.FPS,
            OverlayType.RECORDING,
        ]

        # --- Canvas ---
        self.width: int = self.config.WINDOW_WIDTH
        self.height: int = self.config.WINDOW_HEIGHT
        self.scale: float = 1.0
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0

        # --- Composición ---
        self.background_color: Tuple[int, int, int, int] = (0, 0, 0, 255)
        self.grid_enabled: bool = False
        self.grid_size: int = 32
        self.grid_color: Tuple[int, int, int, int] = (40, 40, 40, 180)

        # --- Datos de overlay ---
        self.overlay_data: Dict[str, Any] = {}

        # --- Snapshot ---
        self.last_snapshot: Optional[Dict[str, Any]] = None
        self.snapshot_interval: float = 0.5
        self.last_snapshot_time: float = 0.0

        # --- Estado interno ---
        self.enabled: bool = True
        self.visible: bool = True
        self.paused: bool = False

        # --- Estadísticas ---
        self.updates: int = 0
        self.snapshots: int = 0
        self.last_update: float = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el controlador de vista previa."""
        self.updates = 0
        self.snapshots = 0
        self.last_snapshot_time = 0.0
        self.overlay_data.clear()
        self.last_update = time.time()

    # =====================================================
    # ACTUALIZACIÓN POR FRAME
    # =====================================================

    def update(self, delta: float, state: State):
        """Actualiza el estado de la vista previa cada frame."""
        if not self.enabled or not self.visible or self.paused:
            return

        self.updates += 1
        now = time.time()

        # 1. Actualizar datos de overlay
        self._update_overlay_data(state)

        # 2. Capturar snapshot si toca
        if now - self.last_snapshot_time >= self.snapshot_interval:
            self._capture_snapshot(state)
            self.last_snapshot_time = now

        self.last_update = now

    # =====================================================
    # OVERLAYS
    # =====================================================

    def _update_overlay_data(self, state: State):
        """Actualiza los datos que consumen los overlays."""
        self.overlay_data = {
            "fps": state.target_fps,
            "frame": state.frame_index,
            "elapsed": round(state.elapsed_time, 2),
            "engine_state": state.engine_state.value,
            "avatar_state": state.avatar_state.value,
            "audio_state": state.audio.state.value,
            "motion_state": state.motion.state.value,
            "recording_state": state.recording.state.value,
            "is_recording": state.recording.state.value == "recording",
            "gesture": state.gesture.current.value,
            "signals": {
                "rms": round(state.audio.features.rms, 4),
                "pitch": round(state.audio.features.pitch, 2),
                "energy_low": round(state.audio.features.energy_band_low, 3),
                "energy_mid": round(state.audio.features.energy_band_mid, 3),
                "energy_high": round(state.audio.features.energy_band_high, 3),
                "beat": state.audio.features.beat_detected,
            },
            "avatar": {
                "head": (
                    round(state.avatar_components.head.rotation_x, 4),
                    round(state.avatar_components.head.rotation_y, 4),
                    round(state.avatar_components.head.rotation_z, 4),
                ),
                "body": (
                    round(state.avatar_components.body.position_x, 4),
                    round(state.avatar_components.body.position_y, 4),
                ),
                "eyes": (
                    round(state.avatar_components.eyes.look_x, 4),
                    round(state.avatar_components.eyes.look_y, 4),
                ),
                "mouth": round(state.avatar_components.mouth.openness, 4),
            },
            "resolution": (self.width, self.height),
            "scale": self.scale,
        }

    def add_overlay(self, overlay: OverlayType):
        """Añade un overlay activo."""
        if overlay not in self.overlays:
            self.overlays.append(overlay)

    def remove_overlay(self, overlay: OverlayType):
        """Quita un overlay activo."""
        if overlay in self.overlays:
            self.overlays.remove(overlay)

    def toggle_overlay(self, overlay: OverlayType):
        """Alterna un overlay."""
        if overlay in self.overlays:
            self.overlays.remove(overlay)
        else:
            self.overlays.append(overlay)

    def clear_overlays(self):
        """Elimina todos los overlays."""
        self.overlays.clear()

    def set_overlays(self, overlays: List[OverlayType]):
        """Reemplaza la lista de overlays."""
        self.overlays = list(overlays)

    # =====================================================
    # SNAPSHOTS
    # =====================================================

    def _capture_snapshot(self, state: State):
        """Captura un snapshot del estado actual."""
        self.last_snapshot = {
            "frame": state.frame_index,
            "elapsed": state.elapsed_time,
            "timestamp": time.time(),
            "engine_state": state.engine_state.value,
            "avatar_state": state.avatar_state.value,
            "signals": dict(self.overlay_data.get("signals", {})),
            "avatar": dict(self.overlay_data.get("avatar", {})),
        }
        self.snapshots += 1

    def get_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """Devuelve el último snapshot capturado."""
        return self.last_snapshot

    def set_snapshot_interval(self, interval: float):
        """Ajusta el intervalo entre snapshots."""
        self.snapshot_interval = max(0.05, interval)

    # =====================================================
    # MODOS DE VISTA
    # =====================================================

    def set_mode(self, mode: PreviewMode):
        """Cambia el modo de vista previa."""
        if mode == self.mode:
            return
        self.mode_previous = self.mode
        self.mode = mode

        # Ajustar flags según modo
        if mode == PreviewMode.GRID:
            self.grid_enabled = True
        elif mode == PreviewMode.DEBUG:
            self.set_overlays([
                OverlayType.FPS, OverlayType.FRAME, OverlayType.STATE,
                OverlayType.SIGNALS, OverlayType.BOUNDS, OverlayType.RECORDING,
            ])
        elif mode == PreviewMode.WIREFRAME:
            self.grid_enabled = True
            self.add_overlay(OverlayType.BOUNDS)
        elif mode == PreviewMode.NORMAL:
            self.grid_enabled = False
        elif mode == PreviewMode.COMPACT:
            self.set_overlays([OverlayType.FPS])

    def cycle_mode(self):
        """Cicla al siguiente modo de vista."""
        modes = list(PreviewMode)
        idx = modes.index(self.mode)
        self.set_mode(modes[(idx + 1) % len(modes)])

    # =====================================================
    # CANVAS
    # =====================================================

    def set_resolution(self, width: int, height: int):
        """Ajusta la resolución de la vista previa."""
        self.width = max(160, int(width))
        self.height = max(90, int(height))

    def set_scale(self, scale: float):
        """Ajusta el factor de escala del contenido."""
        self.scale = max(0.1, min(4.0, scale))

    def set_offset(self, x: float, y: float):
        """Ajusta el desplazamiento del contenido."""
        self.offset_x = x
        self.offset_y = y

    def reset_view(self):
        """Reinicia escala y offset."""
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

    def set_background(self, color: Tuple[int, int, int, int]):
        """Ajusta el color de fondo."""
        self.background_color = color

    def set_grid(self, enabled: bool, size: Optional[int] = None,
                 color: Optional[Tuple[int, int, int, int]] = None):
        """Activa o desactiva la rejilla."""
        self.grid_enabled = enabled
        if size is not None:
            self.grid_size = max(4, size)
        if color is not None:
            self.grid_color = color

    # =====================================================
    # VISIBILIDAD Y ESTADO
    # =====================================================

    def show(self):
        """Muestra la vista previa."""
        self.visible = True

    def hide(self):
        """Oculta la vista previa."""
        self.visible = False

    def toggle_visibility(self):
        """Alterna visibilidad."""
        self.visible = not self.visible

    def enable(self, enabled: bool = True):
        """Activa o desactiva el controlador."""
        self.enabled = enabled

    def pause(self):
        """Pausa la actualización."""
        self.paused = True

    def resume(self):
        """Reanuda la actualización."""
        self.paused = False

    def reset(self):
        """Reinicia el controlador."""
        self.initialize()
        self.mode = PreviewMode.NORMAL
        self.overlays = [OverlayType.FPS, OverlayType.RECORDING]
        self.reset_view()

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_overlay_data(self) -> Dict[str, Any]:
        """Devuelve los datos actuales de overlay."""
        return dict(self.overlay_data)

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "enabled": self.enabled,
            "visible": self.visible,
            "paused": self.paused,
            "mode": self.mode.value,
            "previous_mode": self.mode_previous.value,
            "overlays": [o.value for o in self.overlays],
            "canvas": {
                "width": self.width,
                "height": self.height,
                "scale": self.scale,
                "offset": (self.offset_x, self.offset_y),
                "background": self.background_color,
            },
            "grid": {
                "enabled": self.grid_enabled,
                "size": self.grid_size,
            },
            "snapshots": {
                "count": self.snapshots,
                "interval": self.snapshot_interval,
            },
            "updates": self.updates,
        }

    def get_available_modes(self) -> List[str]:
        """Lista los modos de vista disponibles."""
        return [m.value for m in PreviewMode]

    def get_available_overlays(self) -> List[str]:
        """Lista los overlays disponibles."""
        return [o.value for o in OverlayType]