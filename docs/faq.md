```bash
cat > docs/faq.md << 'XARION_EOF'
# Preguntas frecuentes (FAQ)

Respuestas a las dudas mas comunes sobre XARION 1.0.

## General

### Que es XARION?

XARION 1.0 es un sistema modular de avatar animado construido
desde cero en Python. Combina sintesis de voz, analisis de audio
en tiempo real, movimiento natural y gestos programados.

### XARION usa inteligencia artificial?

No en su version 1.0. El sistema usa algoritmos deterministicos
de analisis de audio y movimiento. La IA conversacional esta
planeada para la version 2.0.

### XARION es gratuito?

Si. El proyecto esta bajo licencia MIT y es completamente libre.

### En que lenguajes esta escrito?

Python 3.10 o superior, exclusivamente.

### Que formatos de avatar soporta?

- VRM
- GLB / GLTF
- FBX
- Live2D (model3.json)
- PNG por capas
- JSON personalizado

## Instalacion

### Que version de Python necesito?

Python 3.10 o superior. Se recomienda 3.11 o 3.12.

### Por que no funciona en Python 3.9?

Porque usamos caracteristicas modernas como `dataclasses`,
`match` en algunos lugares y type hints actualizados.

### Necesito ffmpeg?

Solo si vas a exportar video avanzado o extraer audio. Para
grabacion basica con OpenCV no es necesario.

### Por que pide edge-tts si tengo otras opciones?

Edge TTS es el motor por defecto porque:
- No requiere API key
- Funciona en cualquier sistema
- Genera voz de alta calidad
- Es ligero

Puedes cambiarlo por pyttsx3 (offline), Piper, Coqui o ElevenLabs.

### Que es un entorno virtual y por que usarlo?

Un entorno virtual aísla las dependencias del proyecto de las del
sistema. Es una buena practica usar `python -m venv .venv`.

### Puedo instalarlo sin entorno virtual?

Si, pero no es recomendado. Puede causar conflictos de versiones
con otras librerias del sistema.

### Como verifico que todo funciona?

```bash
python main.py --status
```

Si devuelve un JSON sin errores, todo esta correcto.

### Como desinstalo XARION?

```bash
deactivate
cd ..
rm -rf XARION1.0
```

Si lo instalaste como paquete:

```bash
pip uninstall xarion
```

## Uso

### Como hago hablar al avatar?

```bash
python main.py --text "Hola, soy XARION"
```

O desde Python:

```python
app.speak("Hola, soy XARION")
```

### Como cambio la voz?

```bash
python main.py --text "Hola" --voice es-ES-ElviraNeural
```

O:

```python
app.tts.set_voice("es-ES-ElviraNeural")
```

### Que voces estan disponibles?

Depende del motor:

- **Edge TTS**: consulta https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/voices/list?trustedclienttoken=6A5AA1D4EAFF4E9FB37E23D68491D6F4
- **ElevenLabs**: voces de tu cuenta
- **Piper**: modelos descargados localmente
- **Coqui**: modelos disponibles en su repositorio

### Como grabo un video?

```bash
python main.py --record output.mp4 --text "Hola"
```

### Como exporto a otro formato?

```bash
python main.py --input raw.mp4 --export final.webm
```

### Como cambio el gesto?

```bash
python main.py --gesture question --text "Que necesitas?"
```

Gestos: `neutral`, `question`, `talking`.

### Como ejecuto la demo?

```bash
python main.py --demo
```

### Como veo el estado del sistema?

```bash
python main.py --status
```

### Como configuro la duracion?

```bash
python main.py --demo --duration 15
```

## Errores y problemas

### ModuleNotFoundError: No module named 'X'

Falta una dependencia. Instalala:

```bash
pip install X
```

Si es una dependencia opcional, el sistema seguira funcionando
con un fallback.

### Pylance dice "Import could not be resolved"

Es una advertencia, no un error. El sistema usa importlib y
degradacion automatica, por lo que funcionara igual.

Si quieres eliminar la advertencia, instala la dependencia.

### edge-tts no responde

Verifica tu conexion a internet. Es un servicio online.

Si persiste:

```bash
pip install --upgrade edge-tts
```

### ffmpeg not found

Instala ffmpeg:

```bash
sudo pacman -S ffmpeg       # Arch
sudo apt install ffmpeg     # Ubuntu
brew install ffmpeg         # macOS
```

O configura la ruta en `.env`:

```text
FFMPEG_BIN=/usr/bin/ffmpeg
```

### Error al exportar video

Verifica que tienes instalado:

```bash
pip install opencv-python
# o
pip install imageio imageio-ffmpeg
```

### Error con PyAudio / sounddevice

Falta portaudio:

```bash
sudo pacman -S portaudio       # Arch
sudo apt install portaudio19-dev  # Ubuntu
brew install portaudio         # macOS
```

### Permission denied al crear venv

No uses sudo. Crea el venv como usuario normal:

```bash
python3 -m venv .venv
```

### Python version too old

Instala Python 3.10 o superior.

### El avatar no se ve

Verifica:
- Que la imagen este en la ruta configurada
- Que el formato sea compatible
- Que `avatar_loaded` sea `True`

```python
print(app.state.avatar_loaded)
```

### El avatar no se mueve

Verifica:
- `state.motion.state` no sea `DISABLED`
- `motion_engine` este registrado
- Los pesos no esten todos en cero

### No se escucha nada

Verifica:
- Volumen del sistema
- `tts.get_info()["engine_ready"]` sea `True`
- Probar con otro motor TTS

### El video sale vacio

Verifica:
- Renderer inicializado
- Avatar cargado
- Backend de video disponible

### El gesto no cambia

Verifica:
- `state.gesture.current`
- El gesto este activado
- Duracion de transicion no sea muy larga

## Configuracion

### Donde estan los ajustes?

En `config/settings.json`.

### Como cambio el FPS?

```python
s.set("render.fps", 60)
s.save()
```

O en `settings.json`:

```json
{"render": {"fps": 60}}
```

### Como cambio la resolucion?

```json
{"render": {"width": 1920, "height": 1080}}
```

### Que son los perfiles?

Configuraciones predefinidas para distintos escenarios:

- `default`: valores estandar
- `performance`: maxima fluidez
- `quality`: maxima calidad visual
- `low_end`: equipos modestos
- `streaming`: para grabacion en vivo
- `debug`: modo desarrollo

### Como aplico un perfil?

```python
from app.interface.settings import SettingsProfile
s.apply_profile(SettingsProfile.PERFORMANCE)
s.save()
```

### Donde se guardan los videos generados?

En `output/` por defecto. Configurable en `settings.json`.

## Avatar

### Que formatos de imagen acepta?

PNG por capas. Cada capa debe llamarse:

- `body.png`
- `eyes.png`
- `mouth.png`
- `head.png`
- `antenna.png`

### Como creo un avatar por capas?

1. Crea cada capa como PNG transparente.
2. Colocalas en `assets/avatar/`.
3. Configura `default_path` en `settings.json`.
4. Ejecuta con `--text` para probar.

### Como uso un modelo VRM?

1. Coloca el archivo `.vrm` en `assets/avatar/`.
2. Configura `default_format: "vrm"` en `settings.json`.
3. Ejecuta XARION.

Nota: el renderizado 3D real requiere integracion externa
(planeada para v1.1).

### Puedo usar varios avatares?

En v1.0 solo se carga uno a la vez. Multiples avatares estan
planeados para futuras versiones.

## Audio

### Que motor TTS me recomiendas?

Para empezar: **Edge TTS**. Es ligero, sin API key y de alta
calidad.

Para offline: **Piper** o **pyttsx3**.

Para maxima calidad: **ElevenLabs** (requiere API key y tiene costo).

### Como funciona el analisis de audio?

El `AudioAnalyzer` extrae features en tiempo real:

- RMS (volumen)
- dB
- Pitch (autocorrelacion)
- Centroide espectral
- ZCR (zero crossing rate)
- Bandas de energia (low, mid, high)
- Beats
- BPM estimado
- Fonema heuristico

Estas features alimentan al movimiento y la sincronizacion.

### Que es un visema?

Un visema es la representacion visual de un fonema. XARION usa
13 visemas: `SILENCE`, `A`, `E`, `I`, `O`, `U`, `M`, `F`, `S`,
`L`, `R`, `TH`, `NEUTRAL`.

### Como se sincroniza la boca con la voz?

El `SynchronizationController` alinea el audio con el renderizado
usando un buffer de features y compensacion de latencia.

## Motion

### Que modos de movimiento hay?

- `disabled`: sin movimiento
- `idle`: solo reposo
- `voice`: reactivo a voz
- `rhythm`: reactivo a beats
- `gesture`: solo gestos
- `combined`: todos los anteriores
- `precise`: alta fidelidad, baja latencia

### Que es el suavizado?

Tecnicas para evitar saltos bruscos en el movimiento:
lerp, exponential, spring, ease_in/out, critical_damp.

### Por que el movimiento se ve robotico?

Ajusta el `smoothing` a un valor mas alto (0.20 a 0.30) o usa
el tipo `spring`.

### Como aumento la intensidad del movimiento?

```python
app.motion_engine.set_intensity(1.5)
```

## Gestos

### Cuantos gestos hay?

Tres gestos base:

- `neutral`: pose en reposo
- `question`: pregunta o curiosidad
- `talking`: habla

Cada uno con 6 variantes.

### Como creo un nuevo gesto?

1. Crea un archivo en `app/gestures/`.
2. Define las variantes como Enum.
3. Define los perfiles como dict.
4. Implementa `activate`, `deactivate`, `update`.
5. Registra en `main.py`.

## Contribucion

### Como contribuyo al proyecto?

Lee `CONTRIBUTING.md` en la raiz.

### Donde reporto bugs?

En GitHub Issues:
https://github.com/Erhik-jhan/XARION1.0/issues

### Aceptan pull requests?

Si, son bienvenidos.

## Rendimiento

### Cuantos FPS se recomiendan?

- 24-30 fps: suficiente para la mayoria de casos
- 60 fps: para animaciones muy fluidas
- Menos de 24: puede verse entrecortado

### Consume muchos recursos?

Depende de:
- FPS configurado
- Motor TTS
- Backend de video

Puedes bajar FPS y usar un backend ligero si es necesario.

### Puedo usar GPU?

No en v1.0. La aceleracion GPU esta planeada para el futuro.

## Desarrollo

### Como anado un modulo nuevo?

1. Crea el archivo en `app/<modulo>/`.
2. Implementa `initialize()` y `update()` si aplica.
3. Registra en `main.py` via `engine.register()`.
4. Anade su estado a `State` si es necesario.
5. Anade tests en `tests/`.

### Como ejecuto los tests?

```bash
pytest tests/
```

O por archivo:

```bash
pytest tests/test_core.py -v
```

### Como formateo el codigo?

```bash
black app tests main.py
ruff check app tests main.py
```

### Como verifico tipos?

```bash
mypy app
```

## Roadmap

### Que viene en la v1.1?

- Integracion real con Live2D y VRM
- Ventana nativa (PyQt6)
- Mas variantes de gestos
- Streaming en tiempo real

### Que viene en la v2.0?

- IA conversacional (LLM)
- Reconocimiento de voz (STT)
- Integracion web (WebSocket)
- Sistema de plugins

### Cuando saldra la v2.0?

No hay fecha definida. Depende del ritmo de desarrollo.

## Otros

### XARION reemplaza a Live2D?

No. XARION es un sistema completo que puede integrar Live2D
como backend de renderizado.

### Puedo usar XARION comercialmente?

Si. La licencia MIT lo permite.

### Puedo vender mi avatar hecho con XARION?

Si, siempre que cumplas con la licencia MIT. Los assets que
tu crees son tuyos.

### Como contacto al autor?

- Repositorio: https://github.com/Erhik-jhan/XARION1.0
- Issues: https://github.com/Erhik-jhan/XARION1.0/issues

### Donde reporto un error en esta documentacion?

En GitHub Issues con la etiqueta `documentation`.
XARION_EOF
echo "[OK] docs/faq.md"
```