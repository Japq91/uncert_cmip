#!/bin/bash

# =============================================================================
# Script: setup_env.sh
# Creates a virtual environment with uv and installs the packages.
# Usage: bash setup_env.sh [venv_folder] [python_version]
# Example: bash setup_env.sh .venv 3.11
# =============================================================================

# --- Settings (change if needed) ---
VENV_DIR="${1:-.venv}"
PY_VERSION="${2:-3.11}"

PACKAGES=(
    "numpy"
    "pandas<3"      # The code uses '12M' and '1Y' frequencies, removed in pandas 3
    "xarray"
    "netCDF4"       # Needed for open_dataset / to_netcdf
    "scipy"
    "matplotlib"
    "geopandas"     # Reads shapefiles
)

# --- Check that uv is installed ---
if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: 'uv' is not installed."
    echo "Install it with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# --- Create the virtual environment ---
if [ -d "$VENV_DIR" ]; then
    echo "WARNING: '$VENV_DIR' already exists. Using it (delete it to start over)."
else
    echo "Creating virtual environment in '$VENV_DIR' (Python $PY_VERSION)..."
    uv venv "$VENV_DIR" --python "$PY_VERSION"
    if [ $? -ne 0 ]; then
        echo "ERROR creating the virtual environment"
        exit 1
    fi
fi

# --- Install packages ---
echo "Installing packages..."
uv pip install --python "$VENV_DIR/bin/python" "${PACKAGES[@]}"
if [ $? -ne 0 ]; then
    echo "ERROR installing packages"
    exit 1
fi

echo "----------------------------------------"
echo "Environment ready. To activate it:"
echo "  source $VENV_DIR/bin/activate"
echo "Then run, for example:"
echo "  bash 00_procesa.sh tas jja"