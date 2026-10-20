#!/bin/bash

# =============================================================================
# Script: 00_procesa.sh
# Runs the full TOE analysis:
#   1. 01_uncertainty.py  -> uncertainties and TOE
#   2. 02_grafica.py     -> maps and plots
# Activate the virtual environment first: source .venv/bin/activate
# =============================================================================

usage() {
    echo "Usage: bash $0 <variable> <season> [input_dir] [output_dir] [figures_dir]"
    echo "  variable     pr | tas"
    echo "  season       djf | jja"
    echo "  input_dir    folder with <season>/ subfolders   (default: data)"
    echo "  output_dir   folder for the .nc results          (default: out)"
    echo "  figures_dir  folder for the .png figures         (default: figures)"
    echo "Example: bash $0 tas jja"
    echo "Example: bash $0 pr djf data out figures"
}

# --- Check arguments ---
if [ $# -lt 2 ] || [ $# -gt 5 ]; then
    echo "ERROR: Expected 2 to 5 arguments, got $#."
    usage
    exit 1
fi

VAR="$1"              # "pr" or "tas"
TRI="$2"              # "djf" or "jja"
IDIR="${3:-data}"     # Input folder
ODIR="${4:-out}"      # Output folder (.nc)
FDIR="${5:-figures}"  # Figures folder (.png)

case "$VAR" in
    pr|tas) ;;
    *) echo "ERROR: Variable '$VAR' is not valid. Use 'pr' or 'tas'."; usage; exit 1 ;;
esac

case "$TRI" in
    djf) PER="m1" ;;
    jja) PER="m7" ;;
    *) echo "ERROR: Season '$TRI' is not valid. Use 'djf' or 'jja'."; usage; exit 1 ;;
esac

# --- Check input folder ---
if [ ! -d "$IDIR" ]; then
    echo "ERROR: Input folder '$IDIR' does not exist."
    exit 1
fi
if [ ! -d "$IDIR/$TRI" ]; then
    echo "ERROR: Folder '$IDIR/$TRI' does not exist."
    echo "Subfolders found in '$IDIR':"
    SUBS=$(ls -d "$IDIR"/*/ 2>/dev/null)
    if [ -n "$SUBS" ]; then echo "$SUBS" | sed 's/^/  /'; else echo "  (none)"; fi
    exit 1
fi
NFILES=$(ls "$IDIR/$TRI"/${PER}_${VAR}_*_ssp*.nc 2>/dev/null | wc -l)
if [ "$NFILES" -eq 0 ]; then
    echo "ERROR: No files like '${PER}_${VAR}_<model>_ssp<XXX>.nc' in '$IDIR/$TRI'."
    exit 1
fi

# --- Check output folders (create them if needed) ---
for d in "$ODIR" "$FDIR"; do
    if [ -e "$d" ] && [ ! -d "$d" ]; then
        echo "ERROR: '$d' exists but is a file, not a folder."
        exit 1
    fi
    if [ ! -d "$d" ]; then
        echo "Creating folder '$d'"
        mkdir -p "$d" || { echo "ERROR: Could not create '$d'."; exit 1; }
    fi
    if [ ! -w "$d" ]; then
        echo "ERROR: No write permission in '$d'."
        exit 1
    fi
done

# --- Check that the scripts exist ---
for script in 01_uncertainty.py 02_grafica.py; do
    if [ ! -f "$script" ]; then
        echo "ERROR: '$script' not found"
        exit 1
    fi
done

# --- Run the pipeline ---
echo "Variable: $VAR | Season: $TRI"
echo "Input: $IDIR/$TRI ($NFILES files) | Output: $ODIR | Figures: $FDIR"
echo "----------------------------------------"

echo "[1/2] Running 01_uncertainty.py..."
python 01_uncertainty.py "$VAR" "$TRI" "$IDIR" "$ODIR"
if [ $? -ne 0 ]; then
    echo "ERROR in 01_uncertainty.py"
    exit 1
fi

echo "[2/2] Running 02_grafica.py..."
python 02_grafica.py "$VAR" "$TRI" "$ODIR" "$FDIR"
if [ $? -ne 0 ]; then
    echo "ERROR in 02_grafica.py"
    exit 1
fi

echo "----------------------------------------"
echo "Pipeline finished: $VAR $TRI"
