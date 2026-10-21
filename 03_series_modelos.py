# ============================
# DIRECTORIES (defaults; can also be given as arguments 3 and 4)
idir = 'data'       # Input folder (one subfolder per season: data/<tri>/)
odir = 'figures'    # Output folder (.png figures)
# ============================
# Time series of each model (mean over the whole lat-lon box)
# One figure per scenario. All figures share the same y-axis and the same
# color for each model, so they can be compared.
# Usage: python 03_series_modelos.py <variable> <season> [input_dir] [output_dir]
# Example: python 03_series_modelos.py pr djf data figures
# ============================

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from glob import glob as gb
import os
import re
import sys

############################
# READ COMMAND LINE ARGUMENTS
args = [a for a in sys.argv[1:] if not a.startswith('--')]
if len(args) < 2:
    print("Usage: python %s <variable> <season> [input_dir] [output_dir]" % sys.argv[0])
    sys.exit(1)
var = args[0]       # Variable: 'pr' (precipitation) or 'tas' (temperature)
tri = args[1]       # Season: 'djf', 'mam', 'jja', 'son', or 'ann' (annual)
if len(args) > 2: idir = args[2]  # Input folder (optional)
if len(args) > 3: odir = args[3]  # Output folder (optional)

# SEASON TO FILE PREFIX
pers = {'djf': 'm1', 'mam': 'm4', 'jja': 'm7', 'son': 'm10', 'ann': 'ann'}
if var not in ('pr', 'tas') or tri not in pers:
    print("ERROR: variable must be pr|tas and season djf|mam|jja|son|ann, got '%s %s'." % (var, tri))
    sys.exit(1)
per = pers[tri]

# Name of the data folder, used in the figure names (data/ -> 'data')
carpeta = os.path.basename(os.path.normpath(idir))
print(var, per)
print("Input folder:  %s" % os.path.abspath(os.path.join(idir, tri)))
print("Output folder: %s" % os.path.abspath(odir))
os.makedirs(odir, exist_ok=True)

# FIND MODELS AND SCENARIOS #########################
# File names: <per>_<var>_<model>_ssp<XXX>.nc -> model and scenario
patron = re.compile(r'^%s_%s_(.+)_ssp(\d+)\.nc$' % (per, var))
files = {}  # files[scenario][model] = path
for f in sorted(gb(os.path.join(idir, tri, '%s_%s_*_ssp*.nc' % (per, var)))):
    m = patron.match(os.path.basename(f))
    if m:
        files.setdefault(m.group(2), {})[m.group(1)] = f
if not files:
    print("ERROR: No files like '%s_%s_<model>_ssp<XXX>.nc' in %s" % (per, var, os.path.join(idir, tri)))
    sys.exit(1)
scenarios = sorted(files)
models = sorted({mdl for s in files.values() for mdl in s})
print("Scenarios found: %s" % ', '.join('SSP' + e for e in scenarios))
print("Models found (%d): %s" % (len(models), ', '.join(models)))

# SPATIAL MEAN #########################
# Mean over lat and lon, weighted by cos(lat) (grid cells are smaller near the poles)
def media_espacial(file):
    da = xr.open_dataset(file)[var]
    w = np.cos(np.deg2rad(da['lat']))
    return da.weighted(w).mean(dim=['lat', 'lon'])

series = {e: {mdl: media_espacial(f) for mdl, f in files[e].items()} for e in scenarios}

# FIGURE STYLE #########################
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['DejaVu Serif'],
    'font.size': 10,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.linewidth': 0.8,
    'legend.frameon': False,
})
# Same color for each model in all figures
cmap = plt.get_cmap('tab10' if len(models) <= 10 else 'tab20')
colores = {mdl: cmap(i) for i, mdl in enumerate(models)}

# Same y-axis for all scenarios
vals = np.concatenate([s.values for e in scenarios for s in series[e].values()])
y_min, y_max = np.nanmin(vals), np.nanmax(vals)
pad = 0.05 * (y_max - y_min)
ylim = (y_min - pad, y_max + pad)

if var == 'pr':
    ylabel = 'Precipitación %s (mm)' % ('acumulada anual' if tri == 'ann' else 'acumulada')
else:
    ylabel = 'Temperatura media (°C)'

# ONE FIGURE PER SCENARIO #########################
for e in scenarios:
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    for mdl in models:
        if mdl not in series[e]:
            continue
        s = series[e][mdl]
        ax.plot(s['time.year'], s, color=colores[mdl], lw=1.1, label=mdl)
    years = np.concatenate([s['time.year'].values for s in series[e].values()])
    ax.set_xlim(years.min(), years.max())
    # Year labels: first year, then every 20 years (not too close to the first one)
    ticks = [y for y in range(int(years.min()) // 20 * 20 + 20, int(years.max()) + 1, 20)
             if y - years.min() >= 10]
    ax.set_xticks([int(years.min())] + ticks)
    ax.set_ylim(ylim)
    ax.set_xlabel('Año')
    ax.set_ylabel(ylabel)
    ax.set_title('SSP%s - %s (%d modelos)' % (e, tri.upper(), len(series[e])), fontsize=10)
    ax.grid(axis='y', lw=0.4, alpha=0.4)
    # Legend outside, to the right, so it does not cover the lines
    ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8, handlelength=1.5)
    fig.tight_layout()
    ofile = os.path.join(odir, 'Series_%s_%s_%s_ssp%s.png' % (carpeta, var, tri, e))
    fig.savefig(ofile, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Saved: %s" % ofile)
