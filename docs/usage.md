```bash
cat > docs/usage.md << 'XARION_EOF'
# Guia de uso de XARION 1.0

Guia completa para usar XARION desde la linea de comandos y
desde el codigo Python.

## Inicio rapido

```bash
python main.py --demo
```

Ejecuta una demo autoejecutable de 12 segundos que hace hablar
al avatar con varios gestos.

## Uso desde linea de comandos

### Ejecucion por defecto

```bash
python main.py
```

Arranca el motor en modo interactivo hasta recibir Ctrl+C.

### Demo autoejecutable

```bash
python main.py --demo
```

### Sintetizar texto

```bash
python main.py --text "Hola, soy XARION"
```

Genera voz y activa el gesto de habla.

### Con voz especifica

```bash
python main.py --text "Hola" --voice es-ES-ElviraNeural
```

### Con gesto especifico

```bash
python main.py --text "Que necesitas?" --gesture question
```

Gestos disponibles: `neutral`, `question`, `talking`.

### Grabar a video

```bash
python main.py --record output.mp4 --text "Hola, mundo"
```

### Grabar sin texto

```bash
python main.py --record output.mp4 --demo
```

### Exportar video existente

```bash
python main.py --input raw.mp4 --export final.webm
```

### Duracion limitada

```bash
python main.py --demo --duration 15
```

### Combinaciones

```bash
python main.py --text "Analizando datos" --gesture talking --record analisis.mp4 --duration 30
```

### Ver estado

```bash
python main.py --status
```

Devuelve un JSON con el estado completo del sistema.

### Usar configuracion externa

```bash
python main.py --settings /ruta/a/settings.json
```

## Flags disponibles

| Flag          | Descripcion                                |
|---------------|--------------------------------------------|
| `--text`      | Texto a sintetizar y animar                |
| `--voice`     | Voz TTS a usar                             |
| `--gesture`   | Gesto a activar (neutral, question, talking) |
| `--record`    | Archivo de salida para grabar              |
| `--export`    | Exportar video existente                   |
| `--input`     | Video de entrada para exportar             |
| `--demo`      | Ejecutar demo autoejecutable               |
| `--settings`  | Ruta a archivo de configuracion            |
| `--duration`  | Duracion maxima en segundos                |
| `--status`    | Mostrar estado y salir                     |

## Uso desde Python

### Inicializacion basica

```python
from main import XarionApplication
from app.core.config import Config

app = XarionApplication(Config())
app.initialize()
```

### Hablar

```python
app.speak("Hola, soy XARION 1.0")
```

### Preguntar

```python
app.ask("Que necesitas?")
```

### Cambiar gesto

```python
from app.core.state import GestureType
app.set_gesture(GestureType.QUESTION)
```

### Grabar

```python
app.start_recording("output.mp4")
app.speak("Esto se esta grabando")
import time
time.sleep(5)
app.stop_recording()
```

### Exportar

```python
app.export_video("output.mp4", "final.webm")
```

### Ejecutar bucle principal

```python
app.run_forever()
```

### Estado del sistema

```python
import json
print(json.dumps(app.status(), indent=2, default=str))
```

## Uso con controladores individuales

### Solo TTS

```python
from app.audio.tts import TTSController
from app.core.config import Config

tts = TTSController(Config())
tts.initialize()
result = tts.synthesize("Hola mundo", voice="es-ES-AlvaroNeural")
print(result["path"], result["duration"])
```

### Solo analisis de audio

```python
from app.audio.audio_analyzer import AudioAnalyzer
from app.core.config import Config

analyzer = AudioAnalyzer(Config())
analyzer.initialize()
analyzer.load("audio.wav")
features = analyzer.analyze()
print(features.rms, features.pitch)
```

### Solo movimiento

```python
from app.motion.motion_engine import MotionEngine, MotionMode
from app.core.config import Config
from app.core.state import State

engine = MotionEngine(Config())
engine.initialize()
engine.set_mode(MotionMode.VOICE)
state = State()
engine.update(0.016, state)
print(engine.get_signals())
```

### Solo gestos

```python
from app.gestures.question import QuestionGesture
from app.core.config import Config
from app.core.state import State

gesture = QuestionGesture(Config())
gesture.initialize()
gesture.activate(hold_duration=2.0)
state = State()
for _ in range(60):
    gesture.update(0.016, state)
print(gesture.get_phase())
```

## Configuracion

### Editar settings.json

Los ajustes se guardan en `config/settings.json`. Ejemplo:

```json
{
  "render": {
    "fps": 30,
    "width": 1280,
    "height": 720
  },
  "audio": {
    "tts_engine": "edge",
    "tts_voice": "es-ES-AlvaroNeural"
  }
}
```

### Cambiar ajustes desde Python

```python
from app.interface.settings import SettingsController
from app.core.config import Config

s = SettingsController(Config())
s.load()
s.set("render.fps", 60)
s.set("audio.tts_voice", "es-ES-ElviraNeural")
s.save()
```

### Aplicar un perfil

```python
from app.interface.settings import SettingsProfile
s.apply_profile(SettingsProfile.PERFORMANCE)
s.save()
```

Perfiles: `default`, `performance`, `quality`, `low_end`, `streaming`, `debug`.

## Cambiar de motor TTS

### En runtime

```python
app.tts.set_engine("piper")
app.tts.set_language("es")
```

### En settings.json

```json
{
  "audio": {
    "tts_engine": "piper",
    "tts_voice": "es_ES-mls_10246-low"
  }
}
```

## Cambiar modo de movimiento

```python
from app.motion.motion_engine import MotionMode
app.motion_engine.set_mode(MotionMode.EXPRESSIVE)
```

Modos: `disabled`, `idle`, `voice`, `rhythm`, `gesture`, `combined`, `precise`.

## Cambiar gestos

### Variantes de neutral

```python
from app.gestures.neutral import NeutralVariant
app.gesture_neutral.set_variant(NeutralVariant.FRIENDLY)
```

### Variantes de pregunta

```python
from app.gestures.question import QuestionVariant
app.gesture_question.set_variant(QuestionVariant.SURPRISED)
```

### Variantes de habla

```python
from app.gestures.talking import TalkingVariant
app.gesture_talking.set_variant(TalkingVariant.ENTHUSIASTIC)
```

## Grabacion

### Iniciar grabacion

```python
app.start_recording("output.mp4")
```

### Detener

```python
path = app.stop_recording()
print(path)
```

### Con audio

```python
app.recorder.attach_audio("audio.wav")
app.start_recording("output.mp4")
```

### Limites

```python
app.recorder.set_limits(max_frames=900, max_duration=30.0)
```

## Exportacion

### Convertir formato

```python
from app.output.video_export import ExportFormat, ExportQuality
app.exporter.set_format(ExportFormat.WEBM)
app.exporter.set_quality(ExportQuality.ULTRA)
app.exporter.export("input.mp4", "output.webm")
```

### Cambiar resolucion

```python
app.exporter.set_resolution(1920, 1080)
```

### Anadir metadatos

```python
app.exporter.set_metadata("title", "Demo XARION")
app.exporter.set_metadata("author", "Erhik-jhan")
```

## Uso en scripts

### Script de automatizacion

```python
#!/usr/bin/env python3
from main import XarionApplication
from app.core.config import Config

app = XarionApplication(Config())
app.initialize()

textos = [
    "Bienvenido a XARION",
    "Este es un ejemplo",
    "Hasta luego",
]

app.start_recording("demo.mp4")
for t in textos:
    app.speak(t)
    app.run_for(3.0)
app.stop_recording()
app.export_video("demo.mp4", "demo.webm")
```

### Con manejo de errores

```python
try:
    app = XarionApplication(Config())
    app.initialize()
    app.speak("Hola")
    app.run_forever()
except KeyboardInterrupt:
    print("Interrumpido por el usuario")
finally:
    app.stop()
```

## Ejemplos completos

### Ejemplo 1: hablar y grabar

```python
from main import XarionApplication
from app.core.config import Config
import time

app = XarionApplication(Config())
app.initialize()

app.start_recording("output.mp4")
app.speak("Hola, soy XARION 1.0")
time.sleep(3)
app.speak("Estoy listo para ayudarte")
time.sleep(3)
app.stop_recording()
```

### Ejemplo 2: cambiar gestos dinamicamente

```python
from app.core.state import GestureType

app.speak("Hola")
time.sleep(2)
app.set_gesture(GestureType.QUESTION)
app.ask("Que necesitas?")
time.sleep(3)
app.set_gesture(GestureType.NEUTRAL)
```

### Ejemplo 3: exportar a multiples formatos

```python
from app.output.video_export import ExportFormat

app.export_video("raw.mp4", "final.mp4")
app.exporter.set_format(ExportFormat.WEBM)
app.export_video("raw.mp4", "final.webm")
app.exporter.set_format(ExportFormat.GIF)
app.export_video("raw.mp4", "final.gif")
```

## Consejos

- Usa `--status` para diagnosticar problemas.
- Usa `--demo` para verificar que todo funciona.
- Usa perfiles de settings para cambiar rapido entre configuraciones.
- Usa `edge-tts` como motor por defecto: es ligero y sin API key.
- Activa `librosa` si haces mucho analisis de audio.
- Instala `ffmpeg` si vas a exportar video con frecuencia.

## Solucion de problemas

### No se escucha nada

- Verifica el volumen del sistema.
- Comprueba `tts.get_info()["engine_ready"]`.
- Prueba con otro motor TTS.

### El video sale vacio

- Verifica que el renderer este inicializado.
- Comprueba que el avatar este cargado.
- Revisa que el backend de video este disponible.

### El avatar no se mueve

- Verifica `state.motion.state`.
- Comprueba que el MotionEngine este activo.
- Revisa los pesos de distribucion.

### El gesto no cambia

- Verifica `state.gesture.current`.
- Comprueba que el gesto este activado.
- Revisa la duracion de transicion.

## Siguientes pasos

- Leer `api.md` para referencia completa de clases.
- Leer `architecture.md` para entender el diseno.
- Leer `faq.md` para dudas comunes.
XARION_EOF
echo "[OK] docs/usage.md"
```