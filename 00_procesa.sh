#!/bin/bash

# =============================================================================
# Script: 00_procesa.sh
# Runs the full TOE analysis:
#   1. 01_uncertainty.py  -> uncertainties and TOE
#   2. 02_grafica.py     -> maps and plots
# Activate the virtual environment first: source .venv/bin/activate
# =============================================================================

# --- Check arguments ---
if [ $# -ne 2 ]; then
    echo "Usage: $0 <variable> <season>"
    echo "Example: $0 tas jja"
    echo "Example: $0 pr djf"
    exit 1
fi

VAR="$1" # "pr" or "tas"
TRI="$2" # "djf" or "jja"

# --- Check that the scripts exist ---
for script in 01_uncertainty.py 02_grafica.py; do
    if [ ! -f "$script" ]; then
        echo "ERROR: '$script' not found"
        exit 1
    fi
done

# --- Run the pipeline ---
echo "Variable: $VAR | Season: $TRI"
echo "----------------------------------------"

echo "[1/2] Running 01_uncertainty.py..."
python 01_uncertainty.py "$VAR" "$TRI"
if [ $? -ne 0 ]; then
    echo "ERROR in 01_uncertainty.py"
    exit 1
fi

echo "[2/2] Running 02_grafica.py..."
python 02_grafica.py "$VAR" "$TRI"
if [ $? -ne 0 ]; then
    echo "ERROR in 02_grafica.py"
    exit 1
fi

echo "----------------------------------------"
echo "Pipeline finished: $VAR $TRI"