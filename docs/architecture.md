```bash
cat > docs/architecture.md << 'XARION_EOF'
# Arquitectura de XARION 1.0

Documento tecnico que describe el diseno interno del sistema, los
modulos que lo componen y como se comunican entre si.

## Vision general

XARION 1.0 es una aplicacion modular con un motor central que
orquesta todo el pipeline. Cada subsistema es independiente y
se conecta al motor a traves de un registro dinamico.

## Principios de diseno

- Modularidad: cada modulo tiene una responsabilidad unica.
- Bajo acoplamiento: los modulos se comunican via interfaces claras.
- Backends opcionales: las dependencias pesadas son opcionales.
- Fallback automatico: si un backend no esta, se usa otro.
- Estado centralizado: todo se comparte a traves de State.
- Auto-registro: los controllers se registran en el motor.

## Capas del sistema

```text
+-----------------------------------------------------+
|                   main.py (CLI)                     |
+-----------------------------------------------------+
|              XarionApplication                      |
+-----------------------------------------------------+
|              XarionEngine (core)                    |
+-----------------------------------------------------+
|  Avatar  |  Audio  |  Motion  |  Gestures  | Output |
+-----------------------------------------------------+
|              State (compartido)                     |
+-----------------------------------------------------+
|              Config (compartido)                    |
+-----------------------------------------------------+
```

## Modulos

### core

Nucleo del sistema. Contiene la configuracion, el estado global y
el motor principal.

- config.py: constantes, rutas y parametros globales.
- state.py: dataclasses con todo el estado (avatar, audio, motion,
  gestos, grabacion) y enums asociados.
- engine.py: XarionEngine, el orquestador del pipeline.

### avatar

Representa visualmente al personaje.

- loader.py: carga modelos en multiples formatos.
- renderer.py: dibuja el avatar aplicando transformaciones.
- eyes.py: control de ojos (mirada, brillo, saccades).
- blink.py: parpadeo automatico con curvas suaves.
- mouth.py: visemas, coarticulacion y sincronizacion labial.
- head_motion.py: movimiento de cabeza (pitch, yaw, roll).
- body_motion.py: movimiento corporal (posicion, rotacion, escala).

### audio

Voz y analisis.

- tts.py: sintesis multi-motor con cache.
- audio_analyzer.py: features de audio en tiempo real.
- volume.py: volumen, mute, fade y limitador.
- rhythm.py: deteccion de beats, BPM y prediccion.
- synchronization.py: alineacion entre audio y avatar.

### motion

Generacion de movimiento natural.

- motion_engine.py: combina senales y las distribuye.
- smoothing.py: suavizado con multiples algoritmos.
- idle_motion.py: movimiento en reposo.
- voice_motion.py: movimiento reactivo a la voz.

### gestures

Gestos programados.

- neutral.py: pose base con variantes.
- question.py: gesto de pregunta con ciclo enter/hold/exit.
- talking.py: gesto de habla reactivo a audio.

### interface

Control, configuracion y previsualizacion.

- controls.py: acciones de control y callbacks.
- settings.py: configuracion persistente y perfiles.
- preview.py: vista previa con modos y overlays.

### output

Produccion de video.

- recorder.py: captura de frames con multiples backends.
- video_export.py: exportacion a multiples formatos.

## Flujo de datos

```text
TEXTO
  |
  v
TTSController --> audio.wav
  |
  v
AudioAnalyzer --> AudioFeatures
  |
  +--> RhythmController
  +--> SynchronizationController
  |
  v
MotionEngine --> senales por componente
  |
  +--> HeadMotionController
  +--> BodyMotionController
  +--> MouthController
  +--> EyesController
  +--> BlinkController
  |
  v
Gesto activo modula la pose
  |
  v
AvatarRenderer --> frame
  |
  v
Recorder --> video.mp4
  |
  v
VideoExporter --> formato final
```

## Ciclo de vida del motor

1. main.py instancia XarionApplication.
2. XarionApplication construye todos los modulos.
3. Los modulos se conectan entre si via register().
4. initialize() carga configuracion y prepara cada modulo.
5. start() arranca el bucle principal a FPS fijo.
6. Cada tick ejecuta el pipeline completo.
7. stop() detiene el bucle y cierra recursos.

## Sistema de senales

Cada fuente de movimiento emite una senal normalizada (0.0 a 1.0):

| Fuente   | Calculo base                                  |
|----------|-----------------------------------------------|
| idle     | Respiracion + balanceo + micro-movimiento     |
| voice    | RMS + pitch + energia                         |
| rhythm   | Beats + BPM + punch                           |
| gesture  | Pose del gesto activo                         |

El MotionEngine combina estas senales con pesos por modo y las
distribuye a cabeza, cuerpo y boca.

## Sistema de suavizado

Se aplican varias tecnicas segun la necesidad:

- lerp: interpolacion lineal basica.
- exponential: suavizado exponencial (por defecto).
- ease_in / ease_out / ease_in_out: curvas de aceleracion.
- spring: muelle fisico con rigidez y amortiguacion.
- critical_damp: amortiguado critico sin overshoot.

Cada componente (posicion, rotacion, escala, ojos, boca) tiene su
propio factor de suavizado.

## Gestion de estado

Todo el estado se concentra en la clase State:

- engine_state: estado general.
- avatar_components: sub-estados del avatar.
- audio: estado del audio y features.
- motion: estado del movimiento.
- gesture: gesto activo y transicion.
- recording: estado de grabacion.

Los controllers leen y escriben directamente sobre State.

## Sistema de callbacks

El motor implementa un patron observador simple:

```python
engine.on("tick", callback)
engine.emit("tick", delta)
```

Esto permite que modulos externos se enganchen al pipeline sin
modificar el motor.

## Backends opcionales

El sistema usa importlib para cargar dependencias pesadas:

```python
try:
    import cv2
except ImportError:
    cv2 = None
```

Si una dependencia no esta disponible, el modulo degrada a un
fallback funcional. Esto permite que XARION arranque incluso con
instalaciones minimas.

## Extension de XARION

Para anadir un nuevo modulo:

1. Crear el archivo en el directorio correspondiente.
2. Implementar initialize() y update() si aplica.
3. Registrar el modulo en main.py via engine.register().
4. Anadir su estado a State si es necesario.
5. Anadir tests en tests/.

Para anadir un nuevo gesto:

1. Crear el archivo en app/gestures/.
2. Definir las variantes como Enum.
3. Definir los perfiles como dict.
4. Implementar activate/deactivate/update.
5. Registrar en main.py y anadir a GestureType.

Para anadir un nuevo motor TTS:

1. Crear el inicializador en TTSController.
2. Anadir la entrada en DEFAULT_VOICES.
3. Anadir la rama en _dispatch_synthesis.
4. Implementar el metodo _synthesize_<motor>.

## Convenciones de codigo

- Nombres de clase: PascalCase.
- Nombres de funcion/metodo: snake_case.
- Nombres de constante: UPPER_SNAKE_CASE.
- Archivos: lowercase con guion bajo.
- Docstrings en cada clase y funcion publica.
- Type hints en parametros y retornos.

## Rendimiento

- El bucle principal usa control de FPS con time.sleep.
- El analizador procesa chunks de tamano configurable.
- El suavizado usa interpolacion exponencial para evitar calculos pesados.
- El renderer aplica transformaciones sin recompilar capas.
- El grabador respeta FPS y descarta frames si se atrasa.

## Limitaciones conocidas

- El render nativo en ventana requiere integracion externa (PyQt, pygame).
- El analisis de fonemas es heuristico, no un reconocedor real.
- La exportacion con ffmpeg depende de tener ffmpeg instalado.
- No hay soporte para multiples avatares simultaneos en la v1.0.

## Roadmap arquitectonico

- v1.1: integracion con Live2D y VRM reales.
- v1.1: ventana nativa con PyQt6.
- v1.2: streaming en tiempo real.
- v2.0: sistema de plugins y arquitectura de eventos avanzada.
XARION_EOF
echo "[OK] docs/architecture.md"
```