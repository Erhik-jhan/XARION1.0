# main.py

"""
XARION 1.0 — Punto de entrada principal.

Integra todos los módulos del sistema:
- core: motor, configuración, estado
- avatar: loader, renderer, ojos, parpadeo, boca, cabeza, cuerpo
- audio: TTS, analizador, volumen, ritmo, sincronización
- motion: motor de movimiento, suavizado, reposo, voz
- gestures: neutral, pregunta, habla
- interface: controles, ajustes, vista previa
- output: grabador, exportador de video

Uso:
    python main.py                    # ejecución por defecto
    python main.py --demo             # demo autoejecutable
    python main.py --text "Hola"      # sintetizar y animar
    python main.py --record out.mp4   # grabar a archivo
"""

import os
import sys
import time
import signal
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# ------------------------------------------------------------
# Asegurar que el paquete raíz esté en el path
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# ------------------------------------------------------------
# Imports del proyecto
# ------------------------------------------------------------
from app.core.config import Config
from app.core.state import (
    State,
    EngineState,
    GestureType,
    MotionState,
    AudioState,
    RecordingState,
)
from app.core.engine import XarionEngine

from app.avatar.loader import AvatarLoader
from app.avatar.renderer import AvatarRenderer
from app.avatar.eyes import EyesController
from app.avatar.blink import BlinkController
from app.avatar.mouth import MouthController
from app.avatar.head_motion import HeadMotionController
from app.avatar.body_motion import BodyMotionController

from app.audio.tts import TTSController
from app.audio.audio_analyzer import AudioAnalyzer
from app.audio.volume import VolumeController
from app.audio.rhythm import RhythmController
from app.audio.synchronization import SynchronizationController

from app.motion.motion_engine import MotionEngine
from app.motion.smoothing import SmoothingController
from app.motion.idle_motion import IdleMotionController
from app.motion.voice_motion import VoiceMotionController

from app.gestures.neutral import NeutralGesture
from app.gestures.question import QuestionGesture
from app.gestures.talking import TalkingGesture

from app.interface.controls import ControlsController
from app.interface.settings import SettingsController
from app.interface.preview import PreviewController

from app.output.recorder import Recorder
from app.output.video_export import VideoExporter


# ============================================================
# XARION APPLICATION
# ============================================================

class XarionApplication:
    """
    Aplicación principal de XARION-1.0.
    Construye todos los módulos, los conecta entre sí y
    expone los métodos de alto nivel: iniciar, hablar,
    grabar, exportar y detener.
    """

    def __init__(self, config: Optional[Config] = None):
        # --- Config y estado ---
        self.config = config or Config()
        self.config.ensure_directories()

        self.state = State()
        self.state.target_fps = self.config.FPS

        # --- Motor principal ---
        self.engine = XarionEngine(self.config)
        self.engine.state = self.state

        # --- Módulos ---
        self._build_modules()
        self._wire_modules()
        self._register_engine_modules()

        # --- Señales ---
        self._running = False
        self._setup_signal_handlers()

    # ========================================================
    # CONSTRUCCIÓN DE MÓDULOS
    # ========================================================

    def _build_modules(self):
        """Instancia todos los módulos del sistema."""
        # Core
        self.settings = SettingsController(self.config)

        # Avatar
        self.avatar_loader = AvatarLoader(self.config)
        self.avatar_renderer = AvatarRenderer(self.config)
        self.eyes = EyesController(self.config)
        self.blink = BlinkController(self.config)
        self.mouth = MouthController(self.config)
        self.head = HeadMotionController(self.config)
        self.body = BodyMotionController(self.config)

        # Audio
        self.tts = TTSController(self.config)
        self.analyzer = AudioAnalyzer(self.config)
        self.volume = VolumeController(self.config)
        self.rhythm = RhythmController(self.config)
        self.sync = SynchronizationController(self.config)

        # Motion
        self.motion_engine = MotionEngine(self.config)
        self.smoothing = SmoothingController(self.config)
        self.idle = IdleMotionController(self.config)
        self.voice_motion = VoiceMotionController(self.config)

        # Gestures
        self.gesture_neutral = NeutralGesture(self.config)
        self.gesture_question = QuestionGesture(self.config)
        self.gesture_talking = TalkingGesture(self.config)

        # Interface
        self.controls = ControlsController(self.config, engine=self.engine)
        self.preview = PreviewController(self.config)

        # Output
        self.recorder = Recorder(self.config)
        self.exporter = VideoExporter(self.config)

    # ========================================================
    # CONEXIONES ENTRE MÓDULOS
    # ========================================================

    def _wire_modules(self):
        """Conecta submódulos entre sí (registro de dependencias)."""
        # Motion engine recibe submódulos
        self.motion_engine.register("smoothing", self.smoothing)
        self.motion_engine.register("idle", self.idle)
        self.motion_engine.register("voice", self.voice_motion)

        # Voice motion recibe cabeza, cuerpo y boca
        self.voice_motion.register("head", self.head)
        self.voice_motion.register("body", self.body)
        self.voice_motion.register("mouth", self.mouth)

        # Idle motion recibe ojos y parpadeo
        self.idle.register("blink", self.blink)
        self.idle.register("eyes", self.eyes)

    def _register_engine_modules(self):
        """Registra módulos en el motor principal."""
        self.engine.register("avatar_loader", self.avatar_loader)
        self.engine.register("avatar_renderer", self.avatar_renderer)
        self.engine.register("audio_tts", self.tts)
        self.engine.register("audio_analyzer", self.analyzer)
        self.engine.register("motion_engine", self.motion_engine)
        self.engine.register("recorder", self.recorder)
        self.engine.register("video_exporter", self.exporter)

    # ========================================================
    # CICLO DE VIDA
    # ========================================================

    def initialize(self, settings_path: Optional[str] = None):
        """Inicializa todos los módulos del sistema."""
        print(f"[XARION] Inicializando {self.config.PROJECT_NAME} {self.config.VERSION}")

        # Cargar settings si existen
        if settings_path:
            self.settings.load(settings_path)
        else:
            self.settings.load()

        self.settings.apply_to_engine(self.engine)

        # Inicializar motores
        self.avatar_renderer.initialize()
        self.avatar_loader.load()
        self.tts.initialize()
        self.analyzer.initialize()
        self.volume.initialize()
        self.rhythm.initialize()
        self.sync.initialize()
        self.motion_engine.initialize()
        self.smoothing.initialize()
        self.idle.initialize()
        self.voice_motion.initialize()
        self.gesture_neutral.initialize()
        self.gesture_question.initialize()
        self.gesture_talking.initialize()
        self.controls.attach_engine(self.engine)
        self.preview.initialize()
        self.recorder.initialize()
        self.exporter.initialize()

        # Cargar capas del avatar si ya está cargado
        if self.avatar_loader.is_loaded():
            avatar_data = self.avatar_loader.avatar_data
            self.avatar_renderer.load_layers(avatar_data)
            self.state.set_avatar_loaded(
                path=avatar_data["path"],
                fmt=avatar_data["format"],
            )

        self.state.engine_state = EngineState.READY
        print("[XARION] Inicialización completa")

    def start(self):
        """Inicia el bucle principal del motor."""
        self._running = True
        self.engine.on("tick", self._on_engine_tick)
        self.engine.start()

    def stop(self):
        """Detiene la aplicación."""
        self._running = False
        try:
            self.engine.stop()
        except Exception:
            pass

    def run_forever(self):
        """Ejecuta hasta recibir una señal de parada."""
        self.start()
        try:
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    # ========================================================
    # EVENTOS
    # ========================================================

    def _on_engine_tick(self, delta: float):
        """Callback invocado cada tick del motor."""
        # Procesar audio
        if self.state.audio.state == AudioState.PLAYING:
            features = self.analyzer.analyze()
            if features:
                self.state.audio.features = features
                self.rhythm.update(delta, features)
                self.sync.push_features(self.state.audio.current_time, features)

        # Actualizar controllers de avatar
        self.eyes.update(delta, self.state)
        self.blink.update(delta, self.state)
        self.mouth.update(delta, self.state)
        self.head.update(delta, self.state)
        self.body.update(delta, self.state)

        # Motion
        self.motion_engine.update(delta, self.state)
        self.sync.update(delta, self.state)

        # Gestos
        self._update_gestures(delta)

        # Preview
        self.preview.update(delta, self.state)

        # Autosave
        self.settings.update(delta)

    def _update_gestures(self, delta: float):
        """Actualiza el gesto activo del avatar."""
        current = self.state.gesture.current

        # Desactivar todos
        if current != GestureType.NEUTRAL:
            self.gesture_neutral.deactivate()
        if current != GestureType.QUESTION:
            self.gesture_question.deactivate()
        if current != GestureType.TALKING:
            self.gesture_talking.deactivate()

        # Activar el correspondiente
        if current == GestureType.NEUTRAL:
            if not self.gesture_neutral.is_active():
                self.gesture_neutral.activate()
            self.gesture_neutral.update(delta, self.state)

        elif current == GestureType.QUESTION:
            self.gesture_question.update(delta, self.state)

        elif current == GestureType.TALKING:
            self.gesture_talking.update(delta, self.state)

    # ========================================================
    # ACCIONES DE ALTO NIVEL
    # ========================================================

    def speak(self, text: str, voice: Optional[str] = None) -> bool:
        """Genera voz y activa el gesto de habla."""
        result = self.tts.synthesize(text, voice=voice)
        if not result.get("success"):
            print(f"[XARION] Error TTS: {result.get('error')}")
            return False

        audio_path = result.get("path")
        duration = result.get("duration", 0.0)

        if not self.analyzer.load(audio_path):
            print(f"[XARION] No se pudo cargar audio: {audio_path}")
            return False

        self.state.audio.file_path = audio_path
        self.state.audio.duration = duration
        self.state.audio.current_time = 0.0
        self.state.audio.state = AudioState.PLAYING
        self.state.audio.tts_text = text

        # Cambiar gesto a habla
        self.state.change_gesture(GestureType.TALKING)
        self.gesture_talking.activate()

        # Suspender reposo
        self.idle.suspend()

        print(f"[XARION] Hablando: '{text[:40]}...' ({duration:.2f}s)")
        return True

    def ask(self, text: str) -> bool:
        """Simula pregunta: gesto de pregunta + texto opcional."""
        self.state.change_gesture(GestureType.QUESTION)
        self.gesture_question.activate(hold_duration=1.5)
        if text:
            self.speak(text)
        return True

    def set_gesture(self, gesture: GestureType):
        """Cambia el gesto activo."""
        self.state.change_gesture(gesture)

    def start_recording(self, output_path: Optional[str] = None):
        """Inicia la grabación de video."""
        if output_path is None:
            output_path = str(self.config.OUTPUT_DIR / f"xarion_{int(time.time())}.mp4")

        ok = self.recorder.start(output_path=output_path)
        if ok:
            self.state.start_recording(output_path, fps=self.state.target_fps)
            print(f"[XARION] Grabando en: {output_path}")
        else:
            print(f"[XARION] Error iniciando grabación: {self.recorder.last_error}")

    def stop_recording(self) -> Optional[str]:
        """Detiene la grabación y devuelve la ruta del archivo."""
        duration = self.recorder.stop()
        self.state.stop_recording()
        path = str(self.recorder.output_path) if self.recorder.output_path else None
        print(f"[XARION] Grabación detenida: {duration:.2f}s → {path}")
        return path

    def export_video(
        self,
        input_path: str,
        output_path: Optional[str] = None,
    ) -> bool:
        """Exporta un video a un formato final."""
        return self.exporter.export(input_path, output_path)

    # ========================================================
    # SEÑALES
    # ========================================================

    def _setup_signal_handlers(self):
        """Instala manejadores de señales para parada limpia."""
        def _handler(signum, frame):
            print("\n[XARION] Señal recibida, cerrando...")
            self.stop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _handler)
            except Exception:
                pass

    # ========================================================
    # DIAGNÓSTICO
    # ========================================================

    def status(self) -> Dict[str, Any]:
        """Devuelve un resumen del estado del sistema."""
        return {
            "engine": self.engine.status(),
            "state": self.state.to_dict(),
            "settings": self.settings.get_info(),
            "tts": self.tts.get_info(),
            "analyzer": self.analyzer.get_info(),
            "volume": self.volume.get_info(),
            "rhythm": self.rhythm.get_info(),
            "sync": self.sync.get_info(),
            "motion": self.motion_engine.get_info(),
            "smoothing": self.smoothing.get_info(),
            "idle": self.idle.get_info(),
            "voice_motion": self.voice_motion.get_info(),
            "gestures": {
                "neutral": self.gesture_neutral.get_info(),
                "question": self.gesture_question.get_info(),
                "talking": self.gesture_talking.get_info(),
            },
            "preview": self.preview.get_info(),
            "recorder": self.recorder.get_info(),
            "exporter": self.exporter.get_info(),
        }


# ============================================================
# CLI
# ============================================================

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xarion",
        description="XARION 1.0 — Avatar animado con voz y movimiento",
    )
    parser.add_argument("--text", type=str, default=None,
                        help="Texto para sintetizar y animar")
    parser.add_argument("--voice", type=str, default=None,
                        help="Voz TTS a usar")
    parser.add_argument("--gesture", type=str, default=None,
                        choices=["neutral", "question", "talking"],
                        help="Gesto a activar")
    parser.add_argument("--record", type=str, default=None,
                        help="Archivo de salida para grabar")
    parser.add_argument("--export", type=str, default=None,
                        help="Exportar un video existente")
    parser.add_argument("--input", type=str, default=None,
                        help="Video de entrada para exportar")
    parser.add_argument("--demo", action="store_true",
                        help="Ejecutar demo autoejecutable")
    parser.add_argument("--settings", type=str, default=None,
                        help="Ruta a archivo de settings JSON")
    parser.add_argument("--duration", type=float, default=0.0,
                        help="Duración máxima (segundos, 0 = infinito)")
    parser.add_argument("--status", action="store_true",
                        help="Mostrar estado y salir")
    return parser


def _run_demo(app: XarionApplication, duration: float = 12.0):
    """Ejecuta una demo autoejecutable."""
    print("[XARION] Demo iniciada")
    app.speak("Hola, soy XARION 1.0. Estoy listo para ayudarte.")
    time.sleep(3)
    app.ask("¿Qué necesitas?")
    time.sleep(2.5)
    app.speak("Puedo hablar, moverme y responder a tu voz.")
    time.sleep(3)
    app.set_gesture(GestureType.NEUTRAL)
    time.sleep(3)
    print("[XARION] Demo completada")


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    # --- Crear aplicación ---
    app = XarionApplication(Config())

    try:
        # --- Inicializar ---
        app.initialize(settings_path=args.settings)

        # --- Modo status ---
        if args.status:
            import json
            print(json.dumps(app.status(), indent=2, ensure_ascii=False, default=str))
            return 0

        # --- Exportación directa ---
        if args.export and args.input:
            ok = app.export_video(args.input, args.export)
            print(f"[XARION] Exportación: {'OK' if ok else 'FALLÓ'}")
            return 0 if ok else 1

        # --- Grabar si se pidió ---
        if args.record:
            app.start_recording(args.record)

        # --- Acciones ---
        if args.gesture:
            try:
                app.set_gesture(GestureType(args.gesture))
            except ValueError:
                print(f"[XARION] Gesto inválido: {args.gesture}")

        if args.text:
            app.speak(args.text, voice=args.voice)

        # --- Demo ---
        if args.demo or not (args.text or args.record):
            _run_demo(app, duration=args.duration or 12.0)

        # --- Bucle principal ---
        if args.duration > 0:
            app.run_forever()
        elif args.text or args.gesture or args.demo:
            # Pequeña ventana para procesar el bucle
            app.start()
            start = time.time()
            timeout = args.duration if args.duration > 0 else 15.0
            while time.time() - start < timeout:
                time.sleep(0.1)
            app.stop()
        else:
            app.run_forever()

    finally:
        # --- Cerrar grabación si está activa ---
        if app.recorder.is_recording():
            app.stop_recording()

        # --- Parada limpia ---
        app.stop()
        print("[XARION] Cerrado correctamente")

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(main())