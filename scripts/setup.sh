#!/usr/bin/env bash

# =========================================================
# XARION 1.0 - Script de instalacion
# =========================================================
# Uso:
#   ./scripts/setup.sh              -> instalacion minima
#   ./scripts/setup.sh --recommended
#   ./scripts/setup.sh --full
#   ./scripts/setup.sh --venv
# =========================================================

set -e

# ---------------------------------------------------------
# Rutas
# ---------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------
# Colores
# ---------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# ---------------------------------------------------------
# Funciones
# ---------------------------------------------------------
log_info() {
    echo -e "${GREEN}[XARION]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[XARION]${NC} $1"
}

log_error() {
    echo -e "${RED}[XARION]${NC} $1"
}

log_step() {
    echo -e "${CYAN}==>${NC} $1"
}

# ---------------------------------------------------------
# Argumentos
# ---------------------------------------------------------
MODE="minimal"
USE_VENV=false

for arg in "$@"; do
    case $arg in
        --recommended) MODE="recommended" ;;
        --full)        MODE="full" ;;
        --venv)        USE_VENV=true ;;
        --minimal)     MODE="minimal" ;;
        -h|--help)
            echo "Uso: $0 [--minimal|--recommended|--full] [--venv]"
            exit 0
            ;;
        *)
            log_warn "Argumento desconocido: $arg"
            ;;
    esac
done

log_info "Modo de instalacion: $MODE"
log_info "Entorno virtual: $USE_VENV"

# ---------------------------------------------------------
# Comprobar python
# ---------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    log_error "python3 no encontrado. Instala Python 3.10 o superior."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
log_info "Python detectado: $PY_VERSION"

# ---------------------------------------------------------
# Crear entorno virtual (opcional)
# ---------------------------------------------------------
if [ "$USE_VENV" = true ]; then
    log_step "Creando entorno virtual .venv"
    python3 -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    log_info "Entorno virtual activado"
fi

# ---------------------------------------------------------
# Actualizar pip
# ---------------------------------------------------------
log_step "Actualizando pip"
python3 -m pip install --upgrade pip setuptools wheel

# ---------------------------------------------------------
# Instalar dependencias segun modo
# ---------------------------------------------------------
case $MODE in
    minimal)
        log_step "Instalando dependencias minimas"
        python3 -m pip install \
            numpy \
            Pillow \
            edge-tts \
            opencv-python
        ;;
    recommended)
        log_step "Instalando dependencias recomendadas"
        python3 -m pip install \
            numpy \
            Pillow \
            edge-tts \
            opencv-python \
            librosa \
            soundfile
        ;;
    full)
        log_step "Instalando dependencias completas"
        if [ -f "requirements.txt" ]; then
            python3 -m pip install -r requirements.txt
        else
            python3 -m pip install \
                numpy \
                Pillow \
                edge-tts \
                pyttsx3 \
                opencv-python \
                imageio \
                imageio-ffmpeg \
                librosa \
                soundfile \
                sounddevice \
                pydub
        fi
        ;;
    *)
        log_error "Modo invalido: $MODE"
        exit 1
        ;;
esac

# ---------------------------------------------------------
# Verificar instalacion
# ---------------------------------------------------------
log_step "Verificando instalacion"
python3 - <<'PY'
import importlib, sys

required = ["numpy", "PIL"]
optional = ["cv2", "edge_tts", "librosa", "soundfile", "imageio"]

missing_required = []
for mod in required:
    try:
        importlib.import_module(mod)
    except Exception:
        missing_required.append(mod)

if missing_required:
    print("[XARION] ERROR: faltan dependencias requeridas:", ", ".join(missing_required))
    sys.exit(1)

print("[XARION] Dependencias requeridas: OK")

available = []
for mod in optional:
    try:
        importlib.import_module(mod)
        available.append(mod)
    except Exception:
        pass

if available:
    print("[XARION] Opcionales disponibles:", ", ".join(available))
else:
    print("[XARION] Sin opcionales detectadas")
PY

# ---------------------------------------------------------
# Comprobar ffmpeg
# ---------------------------------------------------------
if command -v ffmpeg >/dev/null 2>&1; then
    log_info "ffmpeg detectado"
else
    log_warn "ffmpeg no encontrado. La exportacion avanzada de video puede fallar."
fi

# ---------------------------------------------------------
# Crear carpetas del proyecto si no existen
# ---------------------------------------------------------
log_step "Verificando estructura de carpetas"
mkdir -p assets/avatar assets/voices assets/animations assets/sounds
mkdir -p config tests docs scripts output
log_info "Estructura de carpetas verificada"

# ---------------------------------------------------------
# Listo
# ---------------------------------------------------------
log_info "Instalacion completada correctamente."
log_info "Ejecuta:  python3 main.py --demo"