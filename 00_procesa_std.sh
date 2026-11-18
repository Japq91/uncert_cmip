#!/bin/bash

# =============================================================================
# Script: 00_procesa_std.sh
# Runs the full TOE analysis with the OLD method (before October 2026):
#   - internal variability (VI) as standard deviation  (--vi=std)
#   - temperature residual in percent                    (--resid=pct)
# Precipitation (pr) always uses the percent residual, so for pr this is the
# same as: bash 00_procesa.sh pr,<season> --vi=std
# Kept to reproduce and compare old results. The recommended flow is 00_procesa.sh.
# Results and figures end in _std_pct (temperature) or _std (pr), so they do not
# overwrite the results of 00_procesa.sh.
# Activate the virtual environment first: source .venv/bin/activate
# =============================================================================

usage() {
    echo "Usage: bash $0 <variable>,<season> [input_dir,output_dir] [--force]"
    echo "  variable     pr | tas | tasmax | tasmin"
    echo "  season       djf | mam | jja | son | ann (annual)"
    echo "  input_dir    folder with <season>/ subfolders   (optional, default: data)"
    echo "  output_dir   folder for the .nc results          (optional, default: out)"
    echo "  --force      recalculate even if the .nc results already exist"
    echo "Method (fixed): VI as standard deviation, temperature residual in percent."
    echo "Example: bash $0 tas,jja"
    echo "Example: bash $0 tasmax,djf data,out --force"
}

# The method is fixed in this script: do not accept --vi or --resid
for a in "$@"; do
    case "$a" in
        -h|--help) usage; exit 0 ;;
        --vi=*|--resid=*)
            echo "ERROR: '$a' is not allowed here: this script always uses --vi=std --resid=pct."
            echo "For other methods use 00_procesa.sh."
            exit 1 ;;
    esac
done

echo "Old method: VI as standard deviation, temperature residual in percent"
exec bash 00_procesa.sh "$@" --vi=std --resid=pct
