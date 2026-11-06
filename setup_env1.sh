#!/bin/bash

# =============================================================================
# Script: setup_env.sh
# Creates a virtual environment with uv and installs the packages.
# Usage: bash setup_env.sh [venv_folder] [python_version]
# Example: bash setup_env.sh .venv 3.11
#
# Only precompiled wheels are installed (--only-binary :all:), so nothing is
# compiled from source. On servers with an old glibc/system libraries
# (e.g. CentOS 7), uv automatically picks the newest versions that ship wheels
# for that system, instead of failing while building pyproj, netCDF4, etc.
# =============================================================================

# --- Settings (change if needed) ---
VENV_DIR="${1:-.venv}"
PY_VERSION="${2:-3.11}"

PACKAGES=(
    "numpy"
    "pandas<3"      # The code uses '12M' and '1Y' frequencies, removed in pandas 3
    "xarray"
    "netCDF4"       # Needed for open_dataset / to_netcdf
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

# --- Show system info (useful for debugging) ---
GLIBC=$(ldd --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+$')
echo "System: $(uname -sm), glibc ${GLIBC:-unknown}"

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

# --- Install packages (wheels only, never build from source) ---
echo "Installing packages (precompiled wheels only)..."
uv pip install --python "$VENV_DIR/bin/python" --only-binary :all: "${PACKAGES[@]}"
if [ $? -ne 0 ]; then
    echo "----------------------------------------"
    echo "ERROR installing packages."
    echo "No compatible precompiled versions were found for this system."
    echo "Options:"
    echo "  1) Try another Python version:  rm -rf $VENV_DIR && bash setup_env.sh $VENV_DIR 3.10"
    echo "  2) Use conda-forge instead (brings its own PROJ/GDAL/HDF5):"
    echo "     conda create -n uncert_cmip -c conda-forge python=3.11 numpy 'pandas<3' xarray netcdf4 matplotlib geopandas"
    exit 1
fi

# --- Quick check that everything imports ---
echo "Checking imports..."
"$VENV_DIR/bin/python" -c "import numpy, pandas, xarray, netCDF4, matplotlib, geopandas, pyproj; \
print('numpy', numpy.__version__, '| pandas', pandas.__version__, '| xarray', xarray.__version__, \
'| geopandas', geopandas.__version__, '| pyproj', pyproj.__version__, '| PROJ', pyproj.proj_version_str)"
if [ $? -ne 0 ]; then
    echo "ERROR: packages installed but some import failed (see message above)"
    exit 1
fi

echo "----------------------------------------"
echo "Environment ready. To activate it:"
echo "  source $VENV_DIR/bin/activate"
echo "Then run, for example:"
echo "  bash 00_procesa.sh tas,jja"
