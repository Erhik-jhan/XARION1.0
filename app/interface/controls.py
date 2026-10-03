# app/interface/controls.py

import time
from typing import Optional, Dict, Any, List, Callable
from enum import Enum

from app.core.config import Config
from app.core.state import (
    State,
    EngineState,
    GestureType,
    RecordingState,
)


# =========================================================
# TIPOS DE CONTROL
# =========================================================

class ControlAction(Enum):
    """Acciones de control disponibles."""
    PLAY = "play"
    PAUSE = "pause"
    STOP = "stop"
    RESTART = "restart"
    SPEAK = "speak"
    SET_GESTURE = "set_gesture"
    START_RECORDING = "start_recording"
    STOP_RECORDING = "stop_recording"
    EXPORT_VIDEO = "export_video"
    MUTE = "mute"
    UNMUTE = "unmute"
    SET_VOLUME = "set_volume"
    LOAD_AVATAR = "load_avatar"
    UNLOAD_AVATAR = "unload_avatar"
    SET_MODE = "set_mode"


# =========================================================
# CONTROLADOR DE INTERFAZ
# =========================================================

class ControlsController:
    """
    Controlador de interfaz de XARION-1.0.
    Expone una API de acciones que la UI o la CLI pueden invocar
    para controlar el motor, el avatar, el audio, los gestos y
    la grabación. Cada acción se traduce a llamadas al engine.
    """

    def __init__(self, config: Optional[Config] = None, engine: Optional[Any] = None):
        self.config = config or Config()
        self.engine = engine

        # --- Estado del controlador ---
        self.last_action: Optional[ControlAction] = None
        self.last_action_time: float = 0.0
        self.action_history: List[Dict[str, Any]] = []
        self.max_history: int = 64

        # --- Callbacks ---
        self.callbacks: Dict[ControlAction, Callable] = {}

        # --- Bloqueos ---
        self.locked: bool = False
        self.lock_reason: Optional[str] = None

        # --- Estadísticas ---
        self.total_actions: int = 0
        self.total_failures: int = 0
        self.last_error: Optional[str] = None

    # =====================================================
    # REGISTRO
    # =====================================================

    def attach_engine(self, engine: Any):
        """Vincula el motor a este controlador."""
        self.engine = engine

    def register_callback(self, action: ControlAction, callback: Callable):
        """Registra un callback para una acción concreta."""
        self.callbacks[action] = callback

    # =====================================================
    # API PRINCIPAL
    # =====================================================

    def execute(self, action: ControlAction, **kwargs) -> Dict[str, Any]:
        """Ejecuta una acción de control y devuelve su resultado."""
        if self.locked:
            return self._fail(f"Controlador bloqueado: {self.lock_reason}")

        start = time.time()
        result: Dict[str, Any]

        try:
            if action == ControlAction.PLAY:
                result = self._play(**kwargs)
            elif action == ControlAction.PAUSE:
                result = self._pause(**kwargs)
            elif action == ControlAction.STOP:
                result = self._stop(**kwargs)
            elif action == ControlAction.RESTART:
                result = self._restart(**kwargs)
            elif action == ControlAction.SPEAK:
                result = self._speak(**kwargs)
            elif action == ControlAction.SET_GESTURE:
                result = self._set_gesture(**kwargs)
            elif action == ControlAction.START_RECORDING:
                result = self._start_recording(**kwargs)
            elif action == ControlAction.STOP_RECORDING:
                result = self._stop_recording(**kwargs)
            elif action == ControlAction.EXPORT_VIDEO:
                result = self._export_video(**kwargs)
            elif action == ControlAction.MUTE:
                result = self._mute(**kwargs)
            elif action == ControlAction.UNMUTE:
                result = self._unmute(**kwargs)
            elif action == ControlAction.SET_VOLUME:
                result = self._set_volume(**kwargs)
            elif action == ControlAction.LOAD_AVATAR:
                result = self._load_avatar(**kwargs)
            elif action == ControlAction.UNLOAD_AVATAR:
                result = self._unload_avatar(**kwargs)
            elif action == ControlAction.SET_MODE:
                result = self._set_mode(**kwargs)
            else:
                result = self._fail(f"Acción desconocida: {action}")
        except Exception as e:
            result = self._fail(f"Excepción ejecutando {action.value}: {e}")

        elapsed = time.time() - start

        # Registrar
        self.last_action = action
        self.last_action_time = time.time()
        self.total_actions += 1
        if not result.get("success"):
            self.total_failures += 1
            self.last_error = result.get("error")

        entry = {
            "action": action.value,
            "success": result.get("success", False),
            "elapsed": round(elapsed, 4),
            "timestamp": time.time(),
            "params": {k: v for k, v in kwargs.items() if isinstance(v, (str, int, float, bool, type(None)))},
        }
        self._push_history(entry)

        # Callback
        if action in self.callbacks:
            try:
                self.callbacks[action](result)
            except Exception:
                pass

        return result

    # =====================================================
    # ACCIONES
    # =====================================================

    def _play(self, **kwargs) -> Dict[str, Any]:
        if self.engine is None:
            return self._fail("Motor no vinculado")
        if hasattr(self.engine, "start"):
            self.engine.start()
        return self._ok("Reproducción iniciada")

    def _pause(self, **kwargs) -> Dict[str, Any]:
        if self.engine is None:
            return self._fail("Motor no vinculado")
        if hasattr(self.engine, "state"):
            self.engine.state.is_playing = False
            self.engine.state.update_timestamp()
        return self._ok("Reproducción pausada")

    def _stop(self, **kwargs) -> Dict[str, Any]:
        if self.engine is None:
            return self._fail("Motor no vinculado")
        if hasattr(self.engine, "stop"):
            self.engine.stop()
        return self._ok("Motor detenido")

    def _restart(self, **kwargs) -> Dict[str, Any]:
        if self.engine is None:
            return self._fail("Motor no vinculado")
        if hasattr(self.engine, "stop"):
            self.engine.stop()
        if hasattr(self.engine, "state"):
            self.engine.state.reset()
        if hasattr(self.engine, "start"):
            self.engine.start()
        return self._ok("Motor reiniciado")

    def _speak(self, text: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if not text:
            return self._fail("Texto no proporcionado")
        if self.engine is None:
            return self._fail("Motor no vinculado")
        if hasattr(self.engine, "speak"):
            self.engine.speak(text, **kwargs)
            return self._ok("Síntesis iniciada", text=text)
        return self._fail("El motor no soporta speak()")

    def _set_gesture(self, gesture: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if not gesture:
            return self._fail("Gesto no especificado")
        try:
            gesture_type = GestureType(gesture)
        except ValueError:
            return self._fail(f"Gesto inválido: {gesture}")
        if self.engine is None:
            return self._fail("Motor no vinculado")
        if hasattr(self.engine, "set_gesture"):
            self.engine.set_gesture(gesture_type)
            return self._ok("Gesto cambiado", gesture=gesture)
        return self._fail("El motor no soporta set_gesture()")

    def _start_recording(self, output_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if self.engine is None:
            return self._fail("Motor no vinculado")
        if not output_path:
            output_path = str(self.config.OUTPUT_DIR / f"xarion_{int(time.time())}.mp4")
        if hasattr(self.engine, "start_recording"):
            self.engine.start_recording(output_path)
            return self._ok("Grabación iniciada", path=output_path)
        return self._fail("El motor no soporta start_recording()")

    def _stop_recording(self, **kwargs) -> Dict[str, Any]:
        if self.engine is None:
            return self._fail("Motor no vinculado")
        if hasattr(self.engine, "stop_recording"):
            duration = self.engine.stop_recording()
            return self._ok("Grabación detenida", duration=duration)
        return self._fail("El motor no soporta stop_recording()")

    def _export_video(self, output_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if self.engine is None:
            return self._fail("Motor no vinculado")
        if not output_path:
            return self._fail("Ruta de exportación requerida")
        if hasattr(self.engine, "export_video"):
            ok = self.engine.export_video(output_path)
            if ok:
                return self._ok("Video exportado", path=output_path)
            return self._fail("Fallo al exportar video")
        return self._fail("El motor no soporta export_video()")

    def _mute(self, **kwargs) -> Dict[str, Any]:
        if self.engine is None or not hasattr(self.engine, "state"):
            return self._fail("Motor no vinculado")
        self.engine.state.audio.muted = True
        return self._ok("Audio silenciado")

    def _unmute(self, **kwargs) -> Dict[str, Any]:
        if self.engine is None or not hasattr(self.engine, "state"):
            return self._fail("Motor no vinculado")
        self.engine.state.audio.muted = False
        return self._ok("Audio restaurado")

    def _set_volume(self, volume: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        if volume is None:
            return self._fail("Volumen no especificado")
        volume = max(0.0, min(1.0, volume))
        if self.engine is None or not hasattr(self.engine, "state"):
            return self._fail("Motor no vinculado")
        self.engine.state.audio.volume = volume
        return self._ok("Volumen ajustado", volume=volume)

    def _load_avatar(self, path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if self.engine is None:
            return self._fail("Motor no vinculado")
        if not hasattr(self.engine, "avatar_loader") or self.engine.avatar_loader is None:
            return self._fail("avatar_loader no registrado")
        result = self.engine.avatar_loader.load(path)
        if result.get("success"):
            self.engine.state.set_avatar_loaded(
                result.get("path", ""), result.get("format", "unknown")
            )
            return self._ok("Avatar cargado", result=result)
        return self._fail(result.get("error", "Fallo al cargar avatar"))

    def _unload_avatar(self, **kwargs) -> Dict[str, Any]:
        if self.engine is None or not hasattr(self.engine, "state"):
            return self._fail("Motor no vinculado")
        self.engine.state.unload_avatar()
        return self._ok("Avatar descargado")

    def _set_mode(self, mode: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if not mode:
            return self._fail("Modo no especificado")
        if self.engine is None or not hasattr(self.engine, "motion_engine"):
            return self._fail("motion_engine no registrado")
        motion_engine = self.engine.motion_engine
        if motion_engine is None or not hasattr(motion_engine, "set_mode"):
            return self._fail("motion_engine no soporta set_mode()")
        try:
            from app.motion.motion_engine import MotionMode
            motion_engine.set_mode(MotionMode(mode))
            return self._ok("Modo cambiado", mode=mode)
        except Exception as e:
            return self._fail(f"Modo inválido: {e}")

    # =====================================================
    # BLOQUEOS
    # =====================================================

    def lock(self, reason: str = "operación en curso"):
        """Bloquea temporalmente el controlador."""
        self.locked = True
        self.lock_reason = reason

    def unlock(self):
        """Desbloquea el controlador."""
        self.locked = False
        self.lock_reason = None

    # =====================================================
    # CONSULTAS
    # =====================================================

    def get_history(self) -> List[Dict[str, Any]]:
        """Devuelve el historial de acciones."""
        return list(self.action_history)

    def get_last_action(self) -> Optional[Dict[str, Any]]:
        """Devuelve la última acción ejecutada."""
        return self.action_history[-1] if self.action_history else None

    def get_info(self) -> Dict[str, Any]:
        """Devuelve información completa del controlador."""
        return {
            "engine_attached": self.engine is not None,
            "locked": self.locked,
            "lock_reason": self.lock_reason,
            "total_actions": self.total_actions,
            "total_failures": self.total_failures,
            "last_action": self.last_action.value if self.last_action else None,
            "last_action_time": self.last_action_time,
            "last_error": self.last_error,
            "callbacks_registered": [a.value for a in self.callbacks.keys()],
        }

    def get_available_actions(self) -> List[str]:
        """Lista las acciones disponibles."""
        return [a.value for a in ControlAction]

    # =====================================================
    # UTILIDADES
    # =====================================================

    def _ok(self, message: str, **extra) -> Dict[str, Any]:
        return {"success": True, "message": message, **extra}

    def _fail(self, message: str) -> Dict[str, Any]:
        return {"success": False, "error": message}

    def _push_history(self, entry: Dict[str, Any]):
        self.action_history.append(entry)
        if len(self.action_history) > self.max_history:
            self.action_history.pop(0)