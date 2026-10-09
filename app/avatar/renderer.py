# app/avatar/renderer.py

import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QColor

from app.core.config import Config
from app.core.state import State


class AvatarRenderer:
    """
    Renderizador por capas de XARION 1.0.

    Reglas:
    - Idle: dibuja body.png
    - Hablando: head.png + ojos + cejas + boca (boca parpadea cada 0.05s)
    - Parpadeo: eyes_closed.png
    - Fondo: background.png siempre al fondo
    """

    MOUTH_TOGGLE_INTERVAL = 0.5  # 500 milisegundos por transicion

    def __init__(self, config: Optional[Config] = None, layers_dir: Optional[Path] = None):
        self.config = config or Config()
        self.layers_dir = layers_dir or (self.config.AVATAR_DIR / "layers")

        self.layers: Dict[str, QPixmap] = {}
        self.base_size: Optional[Tuple[int, int]] = None
        self.loaded = False

        # Estado
        self.talking = False
        self.blink_closed = False
        self.celebrating = False
        self._mouth_visible = True
        self._last_mouth_toggle = 0.0

        # Transformaciones (por si luego animamos)
        self.head_offset_x = 0.0
        self.head_offset_y = 0.0
        self.head_rotation = 0.0
        self.eye_offset_x = 0.0
        self.eye_offset_y = 0.0
        self.body_offset_x = 0.0
        self.body_offset_y = 0.0

        # Estadisticas
        self.frames_rendered = 0
        self.last_render_time = 0.0

    # =====================================================
    # CARGA
    # =====================================================

    def load(self) -> bool:
        all_layers = [
            "background", "body", "head", "head_empty",
            "eye_left", "eye_right", "eyes_closed",
            "brow_left", "brow_right", "mouth",
            "glow", "arm_left", "arm_right",
        ]
        if not self.layers_dir.exists():
            print(f"[AvatarRenderer] Carpeta no existe: {self.layers_dir}")
            return False

        for name in all_layers:
            path = self.layers_dir / f"{name}.png"
            if not path.exists():
                continue
            pix = QPixmap(str(path))
            if pix.isNull():
                continue
            self.layers[name] = pix
            if self.base_size is None:
                self.base_size = (pix.width(), pix.height())

        self.loaded = len(self.layers) > 0
        print(f"[AvatarRenderer] {len(self.layers)} capas cargadas ({self.base_size})")
        return self.loaded

    # =====================================================
    # SELECCION DE CAPAS
    # =====================================================

    def _current_layers(self) -> List[str]:
        """Devuelve el orden de capas segun el estado actual."""
        order: List[str] = []
        if "background" in self.layers:
            order.append("background")

        # Celebracion: pulgares arriba + ojos cerrados
        if self.celebrating and "eyes_closed" in self.layers:
            order.append("eyes_closed")
            return order

        # Blink: se antepone a todo
        if self.blink_closed and "eyes_closed" in self.layers:
            order.append("eyes_closed")
            return order

        if self.talking and "head" in self.layers:
            # Hablando: base vacia + cara encima
            order.append("head")
            if "eye_left" in self.layers:
                order.append("eye_left")
            if "eye_right" in self.layers:
                order.append("eye_right")
            if "brow_left" in self.layers:
                order.append("brow_left")
            if "brow_right" in self.layers:
                order.append("brow_right")
            if self._mouth_visible and "mouth" in self.layers:
                order.append("mouth")
            return order

        # Idle: body
        if "body" in self.layers:
            order.append("body")
        return order

    # =====================================================
    # RENDER
    # =====================================================

    def render(self, painter: QPainter, scale: float = 1.0):
        if not self.loaded:
            return

        start = time.time()

        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        painter.save()
        painter.scale(scale, scale)

        order = self._current_layers()
        for name in order:
            pix = self.layers.get(name)
            if pix is None:
                continue
            painter.drawPixmap(0, 0, pix)

        painter.restore()

        self.frames_rendered += 1
        self.last_render_time = time.time() - start

    # =====================================================
    # ACTUALIZACION
    # =====================================================

    def apply_state(self, state: State):
        """Traduce el estado del motor a modo de dibujo."""
        # Detectar si esta hablando
        audio_playing = state.audio.state.value == "playing"
        gesture_talking = state.gesture.current.value == "talking"
        self.talking = audio_playing or gesture_talking

        # Parpadeo desactivado en todos los modos.
        # eyes_closed.png tiene pulgares, no se debe usar para parpadear.
        self.blink_closed = False

        # Boca parpadeante mientras habla
        if self.talking:
            now = time.time()
            if now - self._last_mouth_toggle >= self.MOUTH_TOGGLE_INTERVAL:
                self._mouth_visible = not self._mouth_visible
                self._last_mouth_toggle = now
        else:
            self._mouth_visible = True
            self._last_mouth_toggle = 0.0

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_base_size(self) -> Tuple[int, int]:
        return self.base_size or (1678, 937)

    def get_info(self) -> Dict[str, Any]:
        return {
            "loaded": self.loaded,
            "layers_count": len(self.layers),
            "layers": list(self.layers.keys()),
            "base_size": self.base_size,
            "talking": self.talking,
            "blink_closed": self.blink_closed,
            "frames_rendered": self.frames_rendered,
            "last_render_time": self.last_render_time,
        }


def build_layers_directory(config: Optional[Config] = None) -> Path:
    cfg = config or Config()
    return cfg.AVATAR_DIR / "layers"
