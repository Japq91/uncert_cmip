#!/bin/bash

# =============================================================================
# Script: 00_procesa.sh
# Runs the full TOE analysis:
#   1. 01_uncertainty.py  -> uncertainties and TOE
#   2. 02_grafica.py     -> maps and plots
# Activate the virtual environment first: source .venv/bin/activate
# =============================================================================

FDIR="figures"  # Figures folder (.png)

usage() {
    echo "Usage: bash $0 <variable>,<season> [input_dir,output_dir] [--vi=std|var] [--force]"
    echo "  variable     pr | tas"
    echo "  season       djf | mam | jja | son | ann (annual)"
    echo "  input_dir    folder with <season>/ subfolders   (optional, default: data)"
    echo "  output_dir   folder for the .nc results          (optional, default: out)"
    echo "  --vi=std     internal variability as standard deviation (default)"
    echo "  --vi=var     internal variability as variance"
    echo "  --force      recalculate even if the .nc results already exist"
    echo "Example: bash $0 tas,jja"
    echo "Example: bash $0 pr,djf data,out"
    echo "Example: bash $0 pr,djf datos            (only input_dir)"
    echo "Example: bash $0 pr,djf ,resultados      (only output_dir)"
    echo "Example: bash $0 pr,djf data,out --force"
    echo "Example: bash $0 pr,djf --vi=var"
}

# --- Read options --force and --vi (they can go anywhere) ---
FORCE=""
VI="std"
ARGS=()
for a in "$@"; do
    if [ "$a" = "--force" ]; then
        FORCE="--force"
    elif [[ "$a" == --vi=* ]]; then
        VI="${a#--vi=}"
    elif [[ "$a" == -* ]]; then
        echo "ERROR: Unknown option '$a'."
        usage
        exit 1
    else
        ARGS+=("$a")
    fi
done

# --- Check arguments ---
if [ ${#ARGS[@]} -lt 1 ] || [ ${#ARGS[@]} -gt 2 ]; then
    echo "ERROR: Expected 1 or 2 arguments (plus options), got ${#ARGS[@]}."
    usage
    exit 1
fi

# First argument: variable,season
IFS=',' read -r VAR TRI EXTRA <<< "${ARGS[0]}"
if [ -z "$VAR" ] || [ -z "$TRI" ] || [ -n "$EXTRA" ]; then
    echo "ERROR: First argument must be <variable>,<season> (for example pr,djf), got '${ARGS[0]}'."
    usage
    exit 1
fi

# Second argument (optional): input_dir,output_dir
IFS=',' read -r IDIR ODIR EXTRA <<< "${ARGS[1]}"
if [ -n "$EXTRA" ]; then
    echo "ERROR: Second argument must be <input_dir>,<output_dir>, got '${ARGS[1]}'."
    usage
    exit 1
fi
IDIR="${IDIR:-data}"  # Input folder
ODIR="${ODIR:-out}"   # Output folder (.nc)

case "$VI" in
    std|var) ;;
    *) echo "ERROR: --vi must be 'std' or 'var', got '$VI'."; usage; exit 1 ;;
esac

case "$VAR" in
    pr|tas) ;;
    *) echo "ERROR: Variable '$VAR' is not valid. Use 'pr' or 'tas'."; usage; exit 1 ;;
esac

case "$TRI" in
    djf) PER="m1" ;;
    mam) PER="m4" ;;
    jja) PER="m7" ;;
    son) PER="m10" ;;
    ann) PER="ann" ;;
    *) echo "ERROR: Season '$TRI' is not valid. Use 'djf', 'mam', 'jja', 'son' or 'ann'."; usage; exit 1 ;;
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
echo "Variable: $VAR | Season: $TRI | VI: $VI${FORCE:+ | --force}"
echo "Input: $IDIR/$TRI ($NFILES files) | Output: $ODIR | Figures: $FDIR"
echo "----------------------------------------"

echo "[1/2] Running 01_uncertainty.py..."
python 01_uncertainty.py "$VAR" "$TRI" "$IDIR" "$ODIR" --vi="$VI" $FORCE
if [ $? -ne 0 ]; then
    echo "ERROR in 01_uncertainty.py"
    exit 1
fi

echo "[2/2] Running 02_grafica.py..."
python 02_grafica.py "$VAR" "$TRI" "$ODIR" "$FDIR" --vi="$VI"
if [ $? -ne 0 ]; then
    echo "ERROR in 02_grafica.py"
    exit 1
fi

echo "----------------------------------------"
echo "Pipeline finished: $VAR $TRI"
