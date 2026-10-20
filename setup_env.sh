#!/bin/bash

# =============================================================================
# Script: setup_env.sh
# Crea un entorno virtual con uv e instala los paquetes del analisis TOE.
# Uso: ./setup_env.sh [directorio_venv] [version_python]
# Ejemplo: ./setup_env.sh .venv 3.11
# =============================================================================

# --- Configuracion (modificar si es necesario) ---
VENV_DIR="${1:-.venv}"
PY_VERSION="${2:-3.11}"

PACKAGES=(
    "numpy"
    "pandas<3"      # El script usa alias de frecuencia '12M' y '1Y', removidos en pandas 3
    "xarray"
    "netCDF4"       # Necesario para open_dataset / to_netcdf
    "scipy"
    "matplotlib"
    "geopandas"     # Incluye dependencias para leer shapefiles
)

# --- Verifica que uv este instalado ---
if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: 'uv' no esta instalado."
    echo "Instalelo con:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# --- Crea el entorno virtual ---
if [ -d "$VENV_DIR" ]; then
    echo "AVISO: '$VENV_DIR' ya existe. Se reutiliza (para recrearlo, eliminelo)."
else
    echo "Creando entorno virtual en '$VENV_DIR' (Python $PY_VERSION)..."
    uv venv "$VENV_DIR" --python "$PY_VERSION"
    if [ $? -ne 0 ]; then
        echo "ERROR al crear el entorno virtual"
        exit 1
    fi
fi

# --- Instala los paquetes ---
echo "Instalando paquetes..."
uv pip install --python "$VENV_DIR/bin/python" "${PACKAGES[@]}"
if [ $? -ne 0 ]; then
    echo "ERROR al instalar los paquetes"
    exit 1
fi

echo "----------------------------------------"
echo "Entorno listo. Para activarlo:"
echo "  source $VENV_DIR/bin/activate"
echo "Luego ejecute, por ejemplo:"
echo "  bash 00_procesa.sh tas jja"