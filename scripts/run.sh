#!/usr/bin/env bash

# =========================================================
# XARION 1.0 - Script de ejecucion
# =========================================================
# Uso:
#   ./scripts/run.sh                 -> ejecucion por defecto
#   ./scripts/run.sh --demo          -> demo autoejecutable
#   ./scripts/run.sh --text "Hola"   -> sintetizar texto
#   ./scripts/run.sh --record out.mp4
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

# ---------------------------------------------------------
# Comprobaciones previas
# ---------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    log_error "python3 no encontrado. Instala Python 3.10 o superior."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
log_info "Python detectado: $PY_VERSION"

if [ ! -f "main.py" ]; then
    log_error "main.py no encontrado. Ejecuta desde la raiz del proyecto."
    exit 1
fi

# ---------------------------------------------------------
# Entorno virtual (opcional)
# ---------------------------------------------------------
if [ -d "venv" ]; then
    log_info "Activando entorno virtual venv..."
    # shellcheck disable=SC1091
    source venv/bin/activate
elif [ -d ".venv" ]; then
    log_info "Activando entorno virtual .venv..."
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

# ---------------------------------------------------------
# Comprobar dependencias minimas
# ---------------------------------------------------------
python3 - <<'PY'
import importlib, sys
missing = []
for mod in ("numpy", "PIL"):
    try:
        importlib.import_module(mod)
    except Exception:
        missing.append(mod)
if missing:
    print("[XARION] Dependencias faltantes:", ", ".join(missing))
    sys.exit(1)
PY

if [ $? -ne 0 ]; then
    log_warn "Instalando dependencias minimas..."
    python3 -m pip install --upgrade pip
    python3 -m pip install numpy Pillow edge-tts opencv-python
fi

# ---------------------------------------------------------
# Ejecucion
# ---------------------------------------------------------
log_info "Iniciando XARION 1.0..."
python3 main.py "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log_info "Ejecucion finalizada correctamente."
else
    log_error "XARION termino con codigo $EXIT_CODE"
fi

exit $EXIT_CODE