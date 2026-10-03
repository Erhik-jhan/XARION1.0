#!/usr/bin/env bash

# =========================================================
# XARION 1.0 - Script de build y empaquetado
# =========================================================
# Uso:
#   ./scripts/build.sh                -> build estandar
#   ./scripts/build.sh --clean        -> limpiar antes
#   ./scripts/build.sh --wheel        -> generar wheel
#   ./scripts/build.sh --sdist        -> generar sdist
#   ./scripts/build.sh --all          -> wheel + sdist
#   ./scripts/build.sh --docker       -> build docker (opcional)
# =========================================================

set -e

# ---------------------------------------------------------
# Rutas
# ---------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/build"
EGG_INFO_DIR="$PROJECT_ROOT/XARION_1_0.egg-info"

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
CLEAN=false
BUILD_WHEEL=false
BUILD_SDIST=false
BUILD_DOCKER=false

for arg in "$@"; do
    case $arg in
        --clean)  CLEAN=true ;;
        --wheel)  BUILD_WHEEL=true ;;
        --sdist)  BUILD_SDIST=true ;;
        --all)    BUILD_WHEEL=true; BUILD_SDIST=true ;;
        --docker) BUILD_DOCKER=true ;;
        -h|--help)
            echo "Uso: $0 [--clean] [--wheel] [--sdist] [--all] [--docker]"
            exit 0
            ;;
        *)
            log_warn "Argumento desconocido: $arg"
            ;;
    esac
done

# Default: si no se especifica nada, build estandar
if [ "$BUILD_WHEEL" = false ] && [ "$BUILD_SDIST" = false ] && [ "$BUILD_DOCKER" = false ]; then
    BUILD_WHEEL=true
fi

# ---------------------------------------------------------
# Comprobar python
# ---------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    log_error "python3 no encontrado."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
log_info "Python detectado: $PY_VERSION"

# ---------------------------------------------------------
# Limpiar
# ---------------------------------------------------------
if [ "$CLEAN" = true ]; then
    log_step "Limpiando artefactos anteriores"
    rm -rf "$DIST_DIR" "$BUILD_DIR" "$EGG_INFO_DIR"
    find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyo" -delete 2>/dev/null || true
    log_info "Limpieza completada"
fi

# ---------------------------------------------------------
# Instalar herramientas de build
# ---------------------------------------------------------
log_step "Verificando herramientas de build"
python3 -m pip install --upgrade pip setuptools wheel >/dev/null
if [ "$BUILD_WHEEL" = true ] || [ "$BUILD_SDIST" = true ]; then
    python3 -m pip install --upgrade build twine >/dev/null
fi

# ---------------------------------------------------------
# Verificar pyproject.toml o setup.py
# ---------------------------------------------------------
if [ ! -f "pyproject.toml" ] && [ ! -f "setup.py" ]; then
    log_warn "No existe pyproject.toml ni setup.py"
    log_warn "Se generara un pyproject.toml minimo para el build"

    cat > pyproject.toml <<'EOF'
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "xarion"
version = "1.0.0"
description = "XARION 1.0 - Avatar animado con voz, movimiento y gestos"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [{ name = "XARION" }]
keywords = ["avatar", "tts", "animation", "motion", "python"]

dependencies = [
    "numpy>=1.24.0",
    "Pillow>=10.0.0",
]

[project.optional-dependencies]
audio = ["edge-tts", "pyttsx3", "librosa", "soundfile"]
video = ["opencv-python", "imageio", "imageio-ffmpeg"]
full  = ["edge-tts", "pyttsx3", "librosa", "soundfile", "opencv-python", "imageio", "imageio-ffmpeg"]

[project.scripts]
xarion = "main:main"

[tool.setuptools]
packages = ["app", "app.core", "app.avatar", "app.audio", "app.motion", "app.gestures", "app.interface", "app.output"]
py-modules = ["main"]
EOF

    log_info "pyproject.toml generado"
fi

# ---------------------------------------------------------
# Build wheel
# ---------------------------------------------------------
if [ "$BUILD_WHEEL" = true ]; then
    log_step "Construyendo wheel"
    python3 -m build --wheel
    log_info "Wheel generado en dist/"
fi

# ---------------------------------------------------------
# Build sdist
# ---------------------------------------------------------
if [ "$BUILD_SDIST" = true ]; then
    log_step "Construyendo sdist"
    python3 -m build --sdist
    log_info "sdist generado en dist/"
fi

# ---------------------------------------------------------
# Build docker (opcional)
# ---------------------------------------------------------
if [ "$BUILD_DOCKER" = true ]; then
    if ! command -v docker >/dev/null 2>&1; then
        log_error "docker no encontrado"
        exit 1
    fi

    log_step "Generando Dockerfile"
    cat > Dockerfile <<'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt || true

COPY . .

CMD ["python3", "main.py", "--demo"]
EOF

    log_step "Construyendo imagen docker"
    docker build -t xarion:1.0.0 .
    log_info "Imagen docker construida: xarion:1.0.0"
fi

# ---------------------------------------------------------
# Verificar resultado
# ---------------------------------------------------------
if [ -d "$DIST_DIR" ]; then
    log_step "Artefactos generados"
    ls -lh "$DIST_DIR" || true
fi

log_info "Build completado correctamente."