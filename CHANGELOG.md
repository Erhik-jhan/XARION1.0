cat > CHANGELOG.md << 'XARION_EOF'
# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato esta basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/)
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Planeado
- Integracion real con Live2D y VRM
- Ventana nativa con PyQt6 / PySide6
- Streaming en tiempo real
- Sistema de plugins
- IA conversacional (LLM)
- Reconocimiento de voz (STT)

## [1.0.0] - 2026-10-02

### Anadido

#### Core
- `Config` con rutas, parametros de render, audio, motion y grabacion
- `State` con sub-estados especializados (avatar, audio, motion, gestos, grabacion)
- `XarionEngine` como motor central del pipeline
- Sistema de eventos y callbacks entre modulos
- Registro dinamico de submodulos
- Bucle principal con control de FPS

#### Avatar
- `AvatarLoader` con soporte para VRM, GLB, GLTF, FBX, Live2D, PNG por capas y JSON custom
- Deteccion automatica de formato
- Extraccion de metadatos (texturas, motions, expressions, capas)
- `AvatarRenderer` con render por capas y transformaciones por componente
- `EyesController` con mirada, apertura, dilatacion, glow, saccades y seguimiento
- `BlinkController` con parpadeo automatico, dobles y curva suave
- `MouthController` con 13 visemas, coarticulacion, perfiles y reaccion a audio
- `HeadMotionController` con 8 modos (idle, talking, listening, thinking, nodding, shaking, looking, surprised)
- `BodyMotionController` con 9 modos (idle, talking, listening, thinking, emphasis, excited, tired, surprised, recording)

#### Audio
- `TTSController` multi-motor: Edge, pyttsx3, Piper, Coqui, ElevenLabs y custom
- Cache de sintesis y estadisticas
- `AudioAnalyzer` con RMS, dB, pitch (autocorrelacion), centroide espectral, ZCR
- Deteccion de bandas de energia (low, mid, high)
- Deteccion de beats con umbral dinamico y BPM estimado
- Estimacion heuristica de fonemas
- `VolumeController` con fade, mute, limitador suave y normalizacion
- `RhythmController` con historial de beats, prediccion y downbeats
- `SynchronizationController` con 5 modos y compensacion de latencia

#### Motion
- `MotionEngine` con 7 modos y combinacion ponderada de senales
- `SmoothingController` con 7 tipos (lerp, ease_in/out, exponential, spring, critical_damp)
- `IdleMotionController` con 6 variantes de reposo
- `VoiceMotionController` con 5 modos de reaccion a voz y suavizado adaptativo

#### Gestos
- `NeutralGesture` con 6 variantes de pose base
- `QuestionGesture` con 6 variantes y ciclo enter/hold/exit
- `TalkingGesture` con 6 variantes, nodding ocasional y salida por silencio

#### Interfaz
- `ControlsController` con 15 acciones de control y registro de callbacks
- `SettingsController` con 6 perfiles y persistencia JSON
- `PreviewController` con 6 modos de vista y 8 overlays informativos

#### Output
- `Recorder` con backends OpenCV, imageio, FFMPEG y RAW
- `VideoExporter` con 5 formatos, 5 calidades, extraccion de audio y miniaturas

#### CLI
- `main.py` con flags: `--text`, `--voice`, `--gesture`, `--record`, `--export`, `--input`, `--demo`, `--settings`, `--duration`, `--status`
- Modo demo autoejecutable
- Cierre limpio mediante senales SIGINT y SIGTERM

#### Proyecto
- `requirements.txt` con dependencias separadas por categoria
- `pyproject.toml` con metadata, extras y configuracion de herramientas
- `.gitignore` completo
- `.env.example` con todas las variables de entorno
- Scripts: `run.sh`, `setup.sh`, `build.sh`, `clean.sh`
- Suite de tests: core, avatar, audio, motion, gestures, interface, output

### Notas
- Primera version estable de XARION
- Arquitectura modular preparada para crecer
- Backends opcionales con fallback automatico si no estan instalados

[Unreleased]: https://github.com/tu-usuario/xarion-1.0/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/tu-usuario/xarion-1.0/releases/tag/v1.0.0
XARION_EOF
echo "[OK] CHANGELOG.md"