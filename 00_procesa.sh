#!/bin/bash

# =============================================================================
# Script: 00_procesa.sh
# Ejecuta el flujo completo de analisis TOE:
#   1. 01_uncertainty.py  -> Calcula incertidumbres y TOE
#   2. 02_grafica.py     -> Genera mapas y graficos
# =============================================================================

# --- Validacion de argumentos ---
if [ $# -ne 2 ]; then
    echo "Uso: $0 <variable> <trimestre>"
    echo "Ejemplo: $0 tas jja"
    echo "Ejemplo: $0 pr def"
    exit 1
fi

VAR="$1" #"tas" #"pr" "tas"
TRI="$2" #"def" #"jja" "def"

# --- Verifica que los scripts existan ---
for script in 01_uncertainty.py 02_grafica.py; do
    if [ ! -f "$script" ]; then
        echo "ERROR: No se encontro '$script'"
        exit 1
    fi
done

# --- Ejecuta el pipeline ---
echo "Variable: $VAR | Trimestre: $TRI"
echo "----------------------------------------"

echo "[1/2] Ejecutando 01_uncertainty.py..."
python 01_uncertainty.py "$VAR" "$TRI"
if [ $? -ne 0 ]; then
    echo "ERROR en 01_uncertainty.py"
    exit 1
fi

echo "[2/2] Ejecutando 02_grafica.py..."
python 02_grafica.py "$VAR" "$TRI"
if [ $? -ne 0 ]; then
    echo "ERROR en 02_grafica.py"
    exit 1
fi

echo "----------------------------------------"
echo "Pipeline completado: $VAR $TRI"