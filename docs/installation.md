```bash
cat > docs/installation.md << 'XARION_EOF'
# Instalacion de XARION 1.0

Guia completa de instalacion paso a paso.

## Requisitos del sistema

### Minimos

- Python 3.10 o superior
- pip actualizado
- 500 MB de espacio libre
- Sistema operativo: Linux, macOS o Windows

### Recomendados

- Python 3.11 o 3.12
- 2 GB de RAM
- ffmpeg instalado
- GPU con soporte OpenGL (opcional)

## Instalacion rapida

```bash
git clone https://github.com/Erhik-jhan/XARION1.0.git
cd XARION1.0
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install numpy Pillow edge-tts opencv-python
python main.py --demo
```

## Instalacion detallada

### 1. Verificar Python

```bash
python3 --version
```

Debe mostrar 3.10 o superior. Si no, instala una version reciente.

En Arch Linux:

```bash
sudo pacman -S python python-pip
```

En Ubuntu/Debian:

```bash
sudo apt install python3 python3-pip python3-venv
```

En macOS:

```bash
brew install python@3.12
```

### 2. Clonar el repositorio

```bash
git clone https://github.com/Erhik-jhan/XARION1.0.git
cd XARION1.0
```

### 3. Crear entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Windows:

```bash
.venv\Scripts\activate
```

### 4. Actualizar pip

```bash
pip install --upgrade pip setuptools wheel
```

### 5. Instalar dependencias

#### Opcion A: instalacion minima

```bash
pip install numpy Pillow edge-tts opencv-python
```

Suficiente para: TTS basico, analisis basico, grabacion.

#### Opcion B: instalacion recomendada

```bash
pip install numpy Pillow edge-tts opencv-python librosa soundfile
```

Anade: analisis espectral avanzado, lectura de audio mejorada.

#### Opcion C: instalacion completa

```bash
pip install -r requirements.txt
```

#### Opcion D: instalacion como paquete editable

```bash
pip install -e .
```

#### Opcion E: con extras por categoria

```bash
pip install -e ".[audio]"
pip install -e ".[video]"
pip install -e ".[full]"
pip install -e ".[dev]"
```

### 6. Instalar ffmpeg (opcional pero recomendado)

Necesario para exportacion avanzada de video.

En Arch Linux:

```bash
sudo pacman -S ffmpeg
```

En Ubuntu/Debian:

```bash
sudo apt install ffmpeg
```

En macOS:

```bash
brew install ffmpeg
```

Verificar:

```bash
ffmpeg -version
```

### 7. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y ajusta lo que necesites. Como minimo:

```text
XARION_TTS_ENGINE=edge
XARION_TTS_VOICE=es-ES-AlvaroNeural
```

Si vas a usar ElevenLabs:

```text
ELEVENLABS_API_KEY=tu_api_key_aqui
```

### 8. Verificar instalacion

```bash
python main.py --status
```

Debe mostrar el estado del sistema sin errores.

### 9. Ejecutar demo

```bash
python main.py --demo
```

## Instalacion por motor TTS

### Edge TTS (recomendado)

```bash
pip install edge-tts
```

Sin API key. Requiere conexion a internet.

### pyttsx3 (offline, sistema)

```bash
pip install pyttsx3
```

En Linux requiere espeak:

```bash
sudo pacman -S espeak-ng
```

### Piper (offline, rapido)

```bash
pip install piper-tts
```

Descarga un modelo de voz:

```bash
# Ejemplo para espanol
mkdir -p assets/voices/piper
cd assets/voices/piper
# Descarga desde https://huggingface.co/rhasspy/piper-voices
```

Configura en `.env`:

```text
PIPER_BIN=piper
PIPER_MODEL=/ruta/al/modelo.onnx
```

### Coqui TTS (offline, neural)

```bash
pip install TTS
```

Puede tardar bastante en instalar. Requiere PyTorch.

### ElevenLabs (online, alta calidad)

```bash
pip install elevenlabs
```

Configura en `.env`:

```text
ELEVENLABS_API_KEY=tu_api_key
```

## Instalacion por backend de video

### OpenCV (recomendado)

```bash
pip install opencv-python
```

### imageio

```bash
pip install imageio imageio-ffmpeg
```

### Solo ffmpeg (pipe)

Asegurate de tener ffmpeg instalado. El Recorder lo usara como fallback.

## Instalacion en sistemas especificos

### Arch Linux

```bash
sudo pacman -S python python-pip python-virtualenv ffmpeg espeak-ng
git clone https://github.com/Erhik-jhan/XARION1.0.git
cd XARION1.0
python -m venv .venv
source .venv/bin/activate
pip install -e ".[full]"
```

### Ubuntu 22.04+

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip ffmpeg espeak-ng
git clone https://github.com/Erhik-jhan/XARION1.0.git
cd XARION1.0
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[full]"
```

### macOS

```bash
brew install python@3.12 ffmpeg
git clone https://github.com/Erhik-jhan/XARION1.0.git
cd XARION1.0
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[full]"
```

### Windows

Descarga Python desde python.org.

```powershell
git clone https://github.com/Erhik-jhan/XARION1.0.git
cd XARION1.0
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[full]"
```

Para ffmpeg en Windows, descarga desde ffmpeg.org y anade al PATH.

## Verificacion

### Comprobar Python

```bash
python --version
```

### Comprobar dependencias

```bash
python -c "import numpy; print('numpy', numpy.__version__)"
python -c "import PIL; print('Pillow', PIL.__version__)"
python -c "import edge_tts; print('edge-tts OK')"
python -c "import cv2; print('opencv', cv2.__version__)"
```

### Comprobar ffmpeg

```bash
ffmpeg -version | head -n 1
```

### Comprobar XARION

```bash
python main.py --status
```

## Problemas comunes

### ModuleNotFoundError

Falta una dependencia. Instalala:

```bash
pip install nombre_del_modulo
```

### Python version too old

Instala Python 3.10 o superior.

### Permission denied al crear venv

Usa `python3 -m venv .venv` sin sudo. Nunca uses sudo con pip.

### edge-tts no responde

Verifica conexion a internet. Es un servicio online.

### ffmpeg not found

Instala ffmpeg o configura la ruta en `.env`:

```text
FFMPEG_BIN=/usr/bin/ffmpeg
```

### Error al exportar video

Verifica que tienes `opencv-python` o `imageio-ffmpeg` instalado.

### Error con PyAudio / sounddevice

Instala los headers de audio:

En Arch:

```bash
sudo pacman -S portaudio
```

En Ubuntu:

```bash
sudo apt install portaudio19-dev
```

## Desinstalacion

```bash
deactivate
cd ..
rm -rf XARION1.0
```

Si instalaste como paquete:

```bash
pip uninstall xarion
```

## Siguientes pasos

- Leer `usage.md` para aprender a usar XARION.
- Leer `architecture.md` para entender el diseno interno.
- Leer `api.md` para la referencia de clases.
XARION_EOF
echo "[OK] docs/installation.md"
```