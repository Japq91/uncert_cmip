#!/bin/bash

# =============================================================================
# Script: 00_procesa.sh
# Runs the full TOE analysis:
#   1. 01_uncertainty.py  -> uncertainties and TOE
#   2. 02_grafica.py     -> maps and plots
# Activate the virtual environment first: source .venv/bin/activate
# =============================================================================

usage() {
    echo "Usage: bash $0 <variables> <seasons> [input_dir] [output_dir] [figures_dir] [--force]"
    echo "  variables    pr | tas            (comma list allowed: pr,tas)"
    echo "  seasons      djf | mam | jja | son  (comma list allowed: djf,jja)"
    echo "  input_dir    folder with <season>/ subfolders   (default: data)"
    echo "  output_dir   folder for the .nc results          (default: out)"
    echo "  figures_dir  folder for the .png figures         (default: figures)"
    echo "  --force      recalculate even if the .nc results already exist"
    echo "Example: bash $0 tas jja"
    echo "Example: bash $0 pr,tas djf,jja"
    echo "Example: bash $0 pr djf data out figures --force"
}

# --- Read --force (it can go anywhere) ---
FORCE=""
ARGS=()
for a in "$@"; do
    if [ "$a" = "--force" ]; then
        FORCE="--force"
    elif [[ "$a" == -* ]]; then
        echo "ERROR: Unknown option '$a'."
        usage
        exit 1
    else
        ARGS+=("$a")
    fi
done

# --- Check arguments ---
if [ ${#ARGS[@]} -lt 2 ] || [ ${#ARGS[@]} -gt 5 ]; then
    echo "ERROR: Expected 2 to 5 arguments (plus optional --force), got ${#ARGS[@]}."
    usage
    exit 1
fi

IFS=',' read -ra VARS <<< "${ARGS[0]}"  # Variables: "pr", "tas"
IFS=',' read -ra TRIS <<< "${ARGS[1]}"  # Seasons: "djf", "mam", "jja", "son"
IDIR="${ARGS[2]:-data}"     # Input folder
ODIR="${ARGS[3]:-out}"      # Output folder (.nc)
FDIR="${ARGS[4]:-figures}"  # Figures folder (.png)

if [ ${#VARS[@]} -eq 0 ] || [ ${#TRIS[@]} -eq 0 ]; then
    echo "ERROR: Variable and season can not be empty."
    usage
    exit 1
fi

# Season to file prefix
season_prefix() {
    case "$1" in
        djf) echo "m1" ;;
        mam) echo "m4" ;;
        jja) echo "m7" ;;
        son) echo "m10" ;;
    esac
}

for VAR in "${VARS[@]}"; do
    case "$VAR" in
        pr|tas) ;;
        *) echo "ERROR: Variable '$VAR' is not valid. Use 'pr' or 'tas'."; usage; exit 1 ;;
    esac
done

for TRI in "${TRIS[@]}"; do
    if [ -z "$(season_prefix "$TRI")" ]; then
        echo "ERROR: Season '$TRI' is not valid. Use 'djf', 'mam', 'jja' or 'son'."
        usage
        exit 1
    fi
done

# --- Check input folder (all combinations, before running anything) ---
if [ ! -d "$IDIR" ]; then
    echo "ERROR: Input folder '$IDIR' does not exist."
    exit 1
fi
for TRI in "${TRIS[@]}"; do
    if [ ! -d "$IDIR/$TRI" ]; then
        echo "ERROR: Folder '$IDIR/$TRI' does not exist."
        echo "Subfolders found in '$IDIR':"
        SUBS=$(ls -d "$IDIR"/*/ 2>/dev/null)
        if [ -n "$SUBS" ]; then echo "$SUBS" | sed 's/^/  /'; else echo "  (none)"; fi
        exit 1
    fi
    PER=$(season_prefix "$TRI")
    for VAR in "${VARS[@]}"; do
        NFILES=$(ls "$IDIR/$TRI"/${PER}_${VAR}_*_ssp*.nc 2>/dev/null | wc -l)
        if [ "$NFILES" -eq 0 ]; then
            echo "ERROR: No files like '${PER}_${VAR}_<model>_ssp<XXX>.nc' in '$IDIR/$TRI'."
            exit 1
        fi
    done
done

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

# --- Run the pipeline for each variable and season ---
for VAR in "${VARS[@]}"; do
    for TRI in "${TRIS[@]}"; do
        echo "========================================"
        echo "Variable: $VAR | Season: $TRI${FORCE:+ | --force}"
        echo "Input: $IDIR/$TRI | Output: $ODIR | Figures: $FDIR"
        echo "----------------------------------------"

        echo "[1/2] Running 01_uncertainty.py..."
        python 01_uncertainty.py "$VAR" "$TRI" "$IDIR" "$ODIR" $FORCE
        if [ $? -ne 0 ]; then
            echo "ERROR in 01_uncertainty.py ($VAR $TRI)"
            exit 1
        fi

        echo "[2/2] Running 02_grafica.py..."
        python 02_grafica.py "$VAR" "$TRI" "$ODIR" "$FDIR"
        if [ $? -ne 0 ]; then
            echo "ERROR in 02_grafica.py ($VAR $TRI)"
            exit 1
        fi
    done
done

echo "========================================"
echo "Pipeline finished: ${VARS[*]} x ${TRIS[*]}"
