```markdown
# XARION 1.0

<p align="center">
  <img src="AVATAR XARION MEJORADO.png" alt="Avatar XARION 1.0" width="600"/>
</p>

<p align="center">
  <b>Avatar animado con voz, movimiento y gestos, construido desde cero en Python.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-brightgreen" alt="Version"/>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python"/>
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="License"/>
  <img src="https://img.shields.io/badge/status-active-success" alt="Status"/>
</p>

---

## Descripcion

XARION 1.0 es un proyecto modular de avatar animado que combina:

- Renderizado de un avatar (robot con ojos luminosos, antena y logo X)
- Sintesis de voz (TTS) multi-motor
- Analisis de audio en tiempo real (RMS, pitch, beats, fonemas)
- Movimiento natural de cabeza, cuerpo, ojos y boca
- Gestos programados (neutral, pregunta, habla)
- Grabacion y exportacion de video en multiples formatos

El objetivo del proyecto es crear un avatar expresivo y modular que pueda hablar, moverse y reaccionar a la voz, sin depender de IA conversacional en su primera version.

La filosofia es construir primero una base solida que hable y se mueva naturalmente. Despues, todo lo demas.

---

## Objetivo de XARION 1.0

```text
                 XARION 1.0
                      |
          +-----------+-----------+
          |                       |
        AVATAR                   TTS
          |                       |
          |                  Voz generada
          |                       |
          +-----------+-----------+
                      |
              AUDIO ANALYZER
                      |
              MOTION ENGINE
                      |
          +-----------+-----------+
          |           |           |
        OJOS        BOCA       CUERPO
          |           |           |
          +-----------+-----------+
                      |
              VIDEO FINAL
```

Sin IA conversacional. Sin web todavia. Primero el avatar debe hablar y moverse de forma natural.

---

## Caracteristicas

### Avatar
- Renderizado por capas (PNG, Live2D, VRM, GLB, FBX, custom JSON)
- Ojos con direccion de mirada, dilatacion y brillo reactivo
- Parpadeo automatico con curvas suaves y dobles parpadeos
- Boca con sistema completo de visemas (A, E, I, O, U, M, F, S, L, R, TH)
- Coarticulacion entre visemas vecinos
- Cabeza con 8 modos (idle, talking, listening, thinking, nodding, shaking, looking, surprised)
- Cuerpo con 9 modos y respiracion, balanceo, rebote y micro-movimientos
- Antena con pulso luminoso reactivo

### Audio
- TTS multi-motor: Edge TTS, pyttsx3, Piper, Coqui, ElevenLabs, custom
- Analizador de audio: RMS, dB, pitch (autocorrelacion), centroide espectral, ZCR
- Bandas de energia: low / mid / high
- Deteccion de beats con umbral dinamico y BPM estimado
- Estimacion de fonemas para sincronizacion labial
- Volumen con fade, mute, limitador y normalizacion
- Ritmo con prediccion del siguiente beat y downbeats
- Sincronizacion audio-avatar con 5 modos y compensacion de latencia

### Movimiento
- Motion Engine con 7 modos (idle, voice, rhythm, gesture, combined, precise, disabled)
- Suavizado avanzado: lerp, ease_in/out, exponential, spring, critical_damp
- Movimiento en reposo con 6 variantes (calm, curious, sleepy, energetic, focused, breathing)
- Movimiento reactivo a voz con 5 modos (subtle, natural, expressive, dramatic, minimal)
- Ataque/liberacion adaptativo para respuesta natural

### Gestos
- Neutral con 6 variantes (base, attentive, relaxed, friendly, professional, contemplative)
- Pregunta con 6 variantes (neutral, curious, surprised, confused, intrigued, skeptical)
- Habla con 6 variantes (normal, enthusiastic, calm, excited, serious, friendly)
- Nodding ocasional, salida automatica por silencio y callbacks

### Interfaz
- Controles con 15 acciones (play, pause, stop, speak, record, export, mute, etc.)
- Settings con 6 perfiles (default, performance, quality, low_end, streaming, debug)
- Vista previa con 6 modos y 8 overlays informativos
- Autoguardado y persistencia en JSON

### Salida
- Grabador con backends OpenCV, imageio o RAW
- Exportador con 5 formatos (mp4, webm, mkv, mov, gif) y 5 calidades
- Extraccion de audio y generacion de miniaturas
- Metadatos y faststart

---

## Arquitectura

```text
XARION-1.0/
|
+-- app/
|   +-- core/
|   |   +-- config.py
|   |   +-- state.py
|   |   +-- engine.py
|   |
|   +-- avatar/
|   |   +-- loader.py
|   |   +-- renderer.py
|   |   +-- eyes.py
|   |   +-- blink.py
|   |   +-- mouth.py
|   |   +-- head_motion.py
|   |   +-- body_motion.py
|   |
|   +-- audio/
|   |   +-- tts.py
|   |   +-- audio_analyzer.py
|   |   +-- volume.py
|   |   +-- rhythm.py
|   |   +-- synchronization.py
|   |
|   +-- motion/
|   |   +-- motion_engine.py
|   |   +-- smoothing.py
|   |   +-- idle_motion.py
|   |   +-- voice_motion.py
|   |
|   +-- gestures/
|   |   +-- neutral.py
|   |   +-- question.py
|   |   +-- talking.py
|   |
|   +-- interface/
|   |   +-- controls.py
|   |   +-- settings.py
|   |   +-- preview.py
|   |
|   +-- output/
|       +-- recorder.py
|       +-- video_export.py
|
+-- assets/
|   +-- avatar/
|   +-- voices/
|   +-- animations/
|   +-- sounds/
|
+-- tests/
+-- docs/
+-- config/
+-- scripts/
|
+-- main.py
+-- requirements.txt
+-- README.md
```

---

## Instalacion

### Requisitos previos

- Python 3.10 o superior
- pip actualizado
- Opcional: ffmpeg instalado en el sistema (para exportacion de video)

### Instalacion minima funcional

```bash
pip install numpy Pillow edge-tts opencv-python
```

### Instalacion recomendada

```bash
pip install numpy Pillow edge-tts opencv-python librosa soundfile
```

### Instalacion completa

```bash
pip install -r requirements.txt
```

### Clonar y ejecutar

```bash
git clone https://github.com/Erhik-jhan/XARION1.0.git
cd XARION-1.0
python main.py
```

---

## Uso

### Ejecucion por defecto

```bash
python main.py
```

### Demo autoejecutable

```bash
python main.py --demo
```

### Sintetizar y animar texto

```bash
python main.py --text "Hola, soy XARION 1.0"
```

### Con gesto especifico

```bash
python main.py --text "Que necesitas?" --gesture question
```

### Grabar a video

```bash
python main.py --record output.mp4 --text "Hola, mundo"
```

### Exportar video existente

```bash
python main.py --input raw.mp4 --export final.webm
```

### Ver estado del sistema

```bash
python main.py --status
```

### Duracion limitada

```bash
python main.py --demo --duration 15
```

---

## Como funciona

### Pipeline completo

```text
1. main.py inicializa todos los modulos
              |
2. XarionEngine empieza el bucle principal a FPS fijo
              |
3. Cada frame:
   a. Analiza el audio actual (si esta reproduciendose)
   b. Actualiza los controllers del avatar (ojos, boca, cabeza, cuerpo)
   c. El MotionEngine combina senales (idle + voz + ritmo + gesto)
   d. El SynchronizationController alinea audio y movimiento
   e. El gesto activo modula la pose final
   f. El Renderer dibuja el frame
   g. El Recorder captura el frame (si esta grabando)
              |
4. Al detener: el VideoExporter genera el archivo final
```

### Sistema de senales

Cada fuente de movimiento produce una senal normalizada (0.0 a 1.0):

| Fuente  | Base de calculo                           |
|---------|-------------------------------------------|
| idle    | Respiracion + balanceo + micro-movimiento |
| voice   | RMS + pitch + energia                     |
| rhythm  | Beats + BPM + punch                       |
| gesture | Pose especifica del gesto activo          |

El MotionEngine combina estas senales con pesos por modo y las distribuye a cabeza, cuerpo y boca.

---

## Ejemplos

### Hablar con animacion

```python
from main import XarionApplication
from app.core.config import Config

app = XarionApplication(Config())
app.initialize()
app.speak("Hola, soy XARION 1.0. Estoy listo para ayudarte.")
app.run_forever()
```

### Grabacion y exportacion

```python
app.start_recording("raw.mp4")
app.speak("Esto se va a grabar en video.")
time.sleep(5)
app.stop_recording()
app.export_video("raw.mp4", "final.webm")
```

### Cambiar gesto manualmente

```python
from app.core.state import GestureType
app.set_gesture(GestureType.QUESTION)
```

---

## Configuracion

Los ajustes se guardan en config/settings.json y se pueden editar desde el SettingsController.

### Secciones

- general: idioma, tema, autoguardado
- render: fps, resolucion, calidad
- avatar: ruta por defecto, escala, auto-blink
- audio: motor TTS, voz, sample rate
- motion: modo, intensidad, suavizado
- gestures: variantes por defecto
- recording: codec, fps, resolucion
- performance: CPU, memoria, multithreading
- debug: log level, overlays

### Perfiles disponibles

- default: valores estandar
- performance: maxima fluidez
- quality: maxima calidad visual
- low_end: equipos modestos
- streaming: para grabacion en vivo
- debug: modo desarrollo

---

## Pruebas

```bash
pytest tests/
```

Ejemplo de test:

```python
def test_engine_initializes():
    from app.core.engine import XarionEngine
    from app.core.config import Config
    engine = XarionEngine(Config())
    engine.initialize()
    assert engine.state.engine_state.value in ("ready", "loading")
```

---

## Roadmap

### Version 1.0 (actual)
- Estructura modular completa
- Motor central y pipeline
- Avatar por capas
- TTS multi-motor
- Analizador de audio
- Sistema de visemas
- Motion engine con modos
- Suavizado avanzado
- Gestos neutral, pregunta y habla
- Grabacion y exportacion

### Version 1.1 (proxima)
- Integracion real con Live2D o VRM
- Renderizado en ventana nativa (PyQt/PySide)
- Mas variantes de gestos
- Streaming en tiempo real

### Version 2.0 (futuro)
- IA conversacional (LLM)
- Reconocimiento de voz (STT)
- Integracion web (WebSocket)
- Plugin system

---

## Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Haz un fork del proyecto
2. Crea una rama (git checkout -b feature/nueva-funcionalidad)
3. Commit con mensajes claros (git commit -m "Anade X")
4. Push a tu rama (git push origin feature/nueva-funcionalidad)
5. Abre un Pull Request

Sigue el estilo del codigo existente y documenta los cambios importantes.

---

## Licencia

Este proyecto esta bajo la licencia MIT. Consulta el archivo LICENSE para mas informacion.

---

## Agradecimientos

- Inspirado en avatares animados modernos y sistemas de Live2D y VRM
- Construido con Python, numpy, Pillow y edge-tts
- Diseno de avatar original: AVATAR XARION MEJORADO

---

## Contacto

- Proyecto: XARION 1.0
- Version: 1.0.0
- Estado: Activo en desarrollo

---

<p align="center">
  <b>XARION 1.0</b> — Hecho con dedicacion, modularidad y codigo limpio.
</p>

<p align="center">
  <img src="AVATAR XARION MEJORADO.png" alt="Avatar XARION 1.0" width="300"/>
</p>
```