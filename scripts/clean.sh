#!/usr/bin/env bash

# =========================================================
# XARION 1.0 - Script de limpieza
# =========================================================
# Uso:
#   ./scripts/clean.sh              -> limpieza estandar
#   ./scripts/clean.sh --all        -> limpieza profunda
#   ./scripts/clean.sh --cache      -> solo cache de Python
#   ./scripts/clean.sh --build      -> solo artefactos de build
#   ./scripts/clean.sh --output     -> solo salidas generadas
#   ./scripts/clean.sh --voices     -> solo voces TTS
#   ./scripts/clean.sh --logs       -> solo logs
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
CLEAN_ALL=false
CLEAN_CACHE=false
CLEAN_BUILD=false
CLEAN_OUTPUT=false
CLEAN_VOICES=false
CLEAN_LOGS=false

for arg in "$@"; do
    case $arg in
        --all)    CLEAN_ALL=true ;;
        --cache)  CLEAN_CACHE=true ;;
        --build)  CLEAN_BUILD=true ;;
        --output) CLEAN_OUTPUT=true ;;
        --voices) CLEAN_VOICES=true ;;
        --logs)   CLEAN_LOGS=true ;;
        -h|--help)
            echo "Uso: $0 [--all] [--cache] [--build] [--output] [--voices] [--logs]"
            exit 0
            ;;
        *)
            log_warn "Argumento desconocido: $arg"
            ;;
    esac
done

# Si no se especifica nada, limpieza estandar (cache + build)
if [ "$CLEAN_ALL" = false ] && \
   [ "$CLEAN_CACHE" = false ] && \
   [ "$CLEAN_BUILD" = false ] && \
   [ "$CLEAN_OUTPUT" = false ] && \
   [ "$CLEAN_VOICES" = false ] && \
   [ "$CLEAN_LOGS" = false ]; then
    CLEAN_CACHE=true
    CLEAN_BUILD=true
fi

if [ "$CLEAN_ALL" = true ]; then
    CLEAN_CACHE=true
    CLEAN_BUILD=true
    CLEAN_OUTPUT=true
    CLEAN_VOICES=true
    CLEAN_LOGS=true
fi

log_info "Iniciando limpieza..."
log_info "Directorio raiz: $PROJECT_ROOT"

# ---------------------------------------------------------
# Cache de Python
# ---------------------------------------------------------
if [ "$CLEAN_CACHE" = true ]; then
    log_step "Limpiando cache de Python"

    find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyo" -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyd" -delete 2>/dev/null || true

    rm -rf "$PROJECT_ROOT/.pytest_cache" 2>/dev/null || true
    rm -rf "$PROJECT_ROOT/.mypy_cache" 2>/dev/null || true
    rm -rf "$PROJECT_ROOT/.ruff_cache" 2>/dev/null || true
    rm -rf "$PROJECT_ROOT/.tox" 2>/dev/null || true

    log_info "Cache de Python limpiada"
fi

# ---------------------------------------------------------
# Artefactos de build
# ---------------------------------------------------------
if [ "$CLEAN_BUILD" = true ]; then
    log_step "Limpiando artefactos de build"

    rm -rf "$PROJECT_ROOT/dist" 2>/dev/null || true
    rm -rf "$PROJECT_ROOT/build" 2>/dev/null || true
    rm -rf "$PROJECT_ROOT"/*.egg-info 2>/dev/null || true
    rm -rf "$PROJECT_ROOT"/*.egg 2>/dev/null || true
    rm -rf "$PROJECT_ROOT"/*.whl 2>/dev/null || true

    log_info "Artefactos de build limpiados"
fi

# ---------------------------------------------------------
# Salidas generadas
# ---------------------------------------------------------
if [ "$CLEAN_OUTPUT" = true ]; then
    log_step "Limpiando salidas de video"

    if [ -d "$PROJECT_ROOT/output" ]; then
        find "$PROJECT_ROOT/output" -type f \( -name "*.mp4" -o -name "*.webm" -o -name "*.mkv" -o -name "*.mov" -o -name "*.gif" -o -name "*.raw" \) -delete 2>/dev/null || true
        log_info "Salidas de video limpiadas"
    else
        log_warn "Carpeta output no encontrada"
    fi
fi

# ---------------------------------------------------------
# Voces TTS generadas
# ---------------------------------------------------------
if [ "$CLEAN_VOICES" = true ]; then
    log_step "Limpiando voces TTS generadas"

    if [ -d "$PROJECT_ROOT/assets/voices" ]; then
        find "$PROJECT_ROOT/assets/voices" -type f \( -name "tts_*.wav" -o -name "tts_*.mp3" \) -delete 2>/dev/null || true
        log_info "Voces TTS limpiadas"
    else
        log_warn "Carpeta assets/voices no encontrada"
    fi
fi

# ---------------------------------------------------------
# Logs
# ---------------------------------------------------------
if [ "$CLEAN_LOGS" = true ]; then
    log_step "Limpiando logs"

    find "$PROJECT_ROOT" -type f -name "*.log" -delete 2>/dev/null || true
    rm -rf "$PROJECT_ROOT/logs" 2>/dev/null || true

    log_info "Logs limpiados"
fi

# ---------------------------------------------------------
# Estado final
# ---------------------------------------------------------
log_info "Limpieza completada correctamente."

# Espacio liberado estimado (informativo)
if command -v du >/dev/null 2>&1; then
    SIZE=$(du -sh "$PROJECT_ROOT" 2>/dev/null | cut -f1)
    log_info "Tamano actual del proyecto: $SIZE"
fi