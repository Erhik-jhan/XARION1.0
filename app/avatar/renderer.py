# app/avatar/renderer.py

import time
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from app.core.config import Config
from app.core.state import State, AvatarState


class AvatarRenderer:
    """
    Renderizador oficial del avatar de XARION-1.0.
    Dibuja el avatar en un canvas y aplica todas las transformaciones:
    ojos, parpadeo, boca, cabeza, cuerpo, antena.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.canvas = None
        self.surface = None
        self.width = self.config.WINDOW_WIDTH
        self.height = self.config.WINDOW_HEIGHT
        self.background = self.config.BACKGROUND_COLOR
        self.render_mode = "2d"           # "2d" | "3d" | "web"
        self.layers: Dict[str, Any] = {}
        self.initialized = False
        self.frames_rendered = 0
        self.last_render_time = 0.0

    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def initialize(self):
        """Inicializa el renderizador y crea el canvas."""
        try:
            self._setup_canvas()
            self.initialized = True
        except Exception as e:
            print(f"[AvatarRenderer] Error al inicializar: {e}")
            self.initialized = False

    def _setup_canvas(self):
        """Crea la superficie/canvas de renderizado."""
        # Modo 2D nativo (sin dependencias externas obligatorias)
        self.canvas = {
            "width": self.width,
            "height": self.height,
            "background": self.background,
            "mode": self.render_mode,
        }
        self.layers = {
            "background": None,
            "body": None,
            "head": None,
            "antenna": None,
            "eyes": None,
            "blink": None,
            "mouth": None,
            "overlay": None,
        }

    # =====================================================
    # CARGA DE CAPAS
    # =====================================================

    def load_layers(self, avatar_data: Dict[str, Any]) -> bool:
        """
        Carga las capas del avatar a partir de los datos del loader.
        Soporta PNG por capas, Live2D, VRM, GLB, custom.
        """
        if not avatar_data or not avatar_data.get("raw"):
            return False

        raw = avatar_data["raw"]
        fmt = raw.get("type", "unknown")

        try:
            if fmt == "png_layers":
                self._load_png_layers(raw)
            elif fmt == "live2d":
                self._load_live2d_layers(raw)
            elif fmt in ("vrm", "gltf", "fbx"):
                self._load_3d_layers(raw)
            elif fmt == "custom":
                self._load_custom_layers(raw)
            else:
                return False
            return True
        except Exception as e:
            print(f"[AvatarRenderer] Error al cargar capas: {e}")
            return False

    def _load_png_layers(self, raw: Dict[str, Any]):
        """Carga capas PNG (body, eyes, mouth, head, antenna)."""
        for name, path in raw.get("layers", {}).items():
            self.layers[name] = {"type": "image", "path": path, "loaded": True}

    def _load_live2d_layers(self, raw: Dict[str, Any]):
        """Carga el modelo Live2D y prepara sus partes."""
        model = raw.get("model_data", {})
        self.layers["live2d_model"] = {
            "type": "live2d",
            "data": model,
            "loaded": True,
        }

    def _load_3d_layers(self, raw: Dict[str, Any]):
        """Carga el modelo 3D (VRM/GLTF/FBX)."""
        self.layers["3d_model"] = {
            "type": "3d",
            "file": raw.get("file"),
            "loaded": True,
        }

    def _load_custom_layers(self, raw: Dict[str, Any]):
        """Carga un avatar definido por JSON personalizado."""
        data = raw.get("data", {})
        for part_name, part_data in data.get("parts", {}).items():
            self.layers[part_name] = {
                "type": "custom",
                "data": part_data,
                "loaded": True,
            }

    # =====================================================
    # RENDER PRINCIPAL
    # =====================================================

    def render(self, delta: float, state: State):
        """
        Renderiza un frame completo del avatar aplicando el estado actual.
        """
        if not self.initialized or not state.avatar_loaded:
            return

        start = time.time()

        # 1. Limpiar canvas
        self._clear()

        # 2. Dibujar capas base
        self._draw_background()
        self._draw_body(state)
        self._draw_head(state)
        self._draw_antenna(state)

        # 3. Dibujar partes animables
        self._draw_eyes(state)
        self._draw_blink(state)
        self._draw_mouth(state)

        # 4. Overlay / efectos
        self._draw_overlay(state)

        self.frames_rendered += 1
        self.last_render_time = time.time() - start

    # =====================================================
    # DIBUJO POR COMPONENTE
    # =====================================================

    def _clear(self):
        """Limpia el canvas antes de dibujar."""
        # En modo 2D nativo, se rellenaría con el color de fondo
        pass

    def _draw_background(self):
        """Dibuja el fondo del canvas."""
        pass

    def _draw_body(self, state: State):
        """Dibuja el cuerpo aplicando posición, rotación y escala."""
        body = state.avatar_components.body
        transform = {
            "x": body.position_x + state.avatar_position.get("x", 0.0),
            "y": body.position_y + state.avatar_position.get("y", 0.0),
            "z": body.position_z + state.avatar_position.get("z", 0.0),
            "rx": body.rotation_x,
            "ry": body.rotation_y,
            "rz": body.rotation_z,
            "scale": body.scale * state.avatar_scale,
        }
        self._apply_transform("body", transform)

    def _draw_head(self, state: State):
        """Dibuja la cabeza con su rotación (pitch, yaw, roll)."""
        head = state.avatar_components.head
        transform = {
            "rx": head.rotation_x,
            "ry": head.rotation_y,
            "rz": head.rotation_z,
            "tilt": head.tilt_offset,
        }
        self._apply_transform("head", transform)

    def _draw_antenna(self, state: State):
        """Dibuja la antena con su pulso luminoso."""
        ant = state.avatar_components.antenna
        params = {
            "glow": ant.glow_intensity,
            "phase": ant.pulse_phase,
            "color": ant.color,
        }
        self._apply_transform("antenna", params)

    def _draw_eyes(self, state: State):
        """Dibuja los ojos con dirección de mirada y brillo."""
        eyes = state.avatar_components.eyes
        params = {
            "look_x": eyes.look_x,
            "look_y": eyes.look_y,
            "openness": eyes.openness,
            "glow": eyes.glow_intensity,
            "dilation": eyes.pupil_dilation,
            "color": eyes.color,
        }
        self._apply_transform("eyes", params)

    def _draw_blink(self, state: State):
        """Dibuja el efecto de parpadeo encima de los ojos."""
        blink = state.avatar_components.blink
        if blink.is_blinking:
            params = {
                "progress": blink.blink_progress,
                "openness": 1.0 - blink.blink_progress,
            }
            self._apply_transform("blink", params)

    def _draw_mouth(self, state: State):
        """Dibuja la boca con apertura, sonrisa y brillo."""
        mouth = state.avatar_components.mouth
        params = {
            "openness": mouth.openness,
            "smile": mouth.smile,
            "viseme": mouth.viseme,
            "glow": mouth.glow_intensity,
            "color": mouth.color,
        }
        self._apply_transform("mouth", params)

    def _draw_overlay(self, state: State):
        """Dibuja efectos adicionales (grabación, glow global, etc.)."""
        if state.recording.state.value == "recording":
            self._apply_transform("overlay", {"recording": True})

    # =====================================================
    # TRANSFORMACIONES
    # =====================================================

    def _apply_transform(self, layer_name: str, params: Dict[str, Any]):
        """
        Aplica una transformación a una capa del avatar.
        En modo nativo guarda los parámetros; los backends reales
        (PIL, Three.js, Live2D) los consumen para dibujar.
        """
        if layer_name not in self.layers:
            self.layers[layer_name] = {}
        self.layers[layer_name]["transform"] = params

    # =====================================================
    # EXPORTACIÓN DE FRAME
    # =====================================================

    def get_frame(self) -> Optional[Any]:
        """Devuelve el frame actual renderizado (para grabación)."""
        return {
            "canvas": self.canvas,
            "layers": self.layers,
            "frame_index": self.frames_rendered,
            "timestamp": time.time(),
        }

    # =====================================================
    # CONTROL
    # =====================================================

    def resize(self, width: int, height: int):
        """Redimensiona el canvas de renderizado."""
        self.width = width
        self.height = height
        if self.canvas:
            self.canvas["width"] = width
            self.canvas["height"] = height

    def set_background(self, color: Tuple[int, int, int, int]):
        """Cambia el color de fondo del render."""
        self.background = color
        if self.canvas:
            self.canvas["background"] = color

    def get_stats(self) -> Dict[str, Any]:
        """Devuelve estadísticas del renderizador."""
        return {
            "initialized": self.initialized,
            "frames_rendered": self.frames_rendered,
            "last_render_time": self.last_render_time,
            "resolution": (self.width, self.height),
            "mode": self.render_mode,
            "layers_loaded": [k for k, v in self.layers.items() if v],
        }

    def shutdown(self):
        """Libera recursos del renderizador."""
        self.layers = {}
        self.canvas = None
        self.initialized = False