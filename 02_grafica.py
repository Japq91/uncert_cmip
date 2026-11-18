# ============================
# DIRECTORIES (defaults; can also be given as arguments 3 and 4)
idir = 'out'    # Input folder (.nc files made by 01_uncertainty.py)
odir = 'figures'    # Output folder (.png figures)
vi_stat = 'var'     # Which results to plot: 'var' or 'std' (can also be given as --vi=std or --vi=var)
resid = 'abs'       # Temperature residual of the results: 'abs' or 'pct' (can also be given as --resid=abs or --resid=pct)
# ============================

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import geopandas as gpd
import sys
import os

############################
# VARIABLE AND SEASON
# --vi=std or --vi=var: which results to plot
for a in sys.argv[1:]:
    if a.startswith('--vi='): vi_stat = a.split('=', 1)[1]
    if a.startswith('--resid='): resid = a.split('=', 1)[1]
args = [a for a in sys.argv[1:] if not a.startswith('--')]
var = args[0]       # Variable: 'pr' (precipitation), 'tas', 'tasmax' or 'tasmin' (temperature)
tri = args[1]  # Season: 'djf', 'mam', 'jja', 'son', or 'ann' (annual)
if len(args) > 2: idir = args[2]  # Input folder (optional)
if len(args) > 3: odir = args[3]  # Output folder (optional)
if var not in ('pr', 'tas', 'tasmax', 'tasmin'):
    print("ERROR: variable must be pr, tas, tasmax or tasmin, got '%s'." % var)
    sys.exit(1)
if vi_stat not in ('std', 'var'):
    print("ERROR: --vi must be 'std' or 'var', got '%s'." % vi_stat)
    sys.exit(1)
if resid not in ('abs', 'pct'):
    print("ERROR: --resid must be 'abs' or 'pct', got '%s'." % resid)
    sys.exit(1)
# Tag of the files (same as 01_uncertainty.py): _var, _std, or _var_pct / _std_pct
# (_pct only for temperature with --resid=pct; precipitation always uses the percent residual)
pct = var != 'pr' and resid == 'pct'
tag = vi_stat + ('_pct' if pct else '')
# Method shown in the titles
metodo = 'VI: %s%s' % (vi_stat, ', residuo %' if pct else '')

# SEASON TO FILE PREFIX
# 'djf' (December-January-February) -> 'm1'
# 'mam' (March-April-May) -> 'm4'
# 'jja' (June-July-August) -> 'm7'
# 'son' (September-October-November) -> 'm10'
# 'ann' (annual) -> 'ann'
if tri == 'djf': per = 'm1'
elif tri == 'mam': per = 'm4'
elif tri == 'jja': per = 'm7'
elif tri == 'son': per = 'm10'
elif tri == 'ann': per = 'ann'
print(var, per)
print("Input folder:  %s" % os.path.abspath(idir))
print("Output folder: %s" % os.path.abspath(odir))
print("Method: %s" % metodo)

os.makedirs(odir, exist_ok=True)

# CHECK INPUT FILES #########################
# Make sure the input files exist before going on
archivos_entrada = [
    os.path.join(idir, 'toe_%s_%s_%s.nc' % (var, per, tag)),
    os.path.join(idir, 'Tmu_%s_%s_%s.nc' % (var, per, tag)),
    os.path.join(idir, 'Tsu_%s_%s_%s.nc' % (var, per, tag)),
    os.path.join(idir, 'Tvi_%s_%s_%s.nc' % (var, per, tag))
]

for archivo in archivos_entrada:
    if not os.path.exists(archivo):
        print("ERROR: Input file not found:")
        print("  -> %s" % archivo)
        print("Run 01_uncertainty.py first.")
        sys.exit(1)

# LOAD SHAPEFILES (borders) #########################
# Peru and South America shapefiles for the maps
shp_peru = gpd.read_file('shape/peru.shp')
shp_suda = gpd.read_file('shape/suda.shp')
#
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['DejaVu Serif'],
    'font.size': 12,
})
# LOAD TOE DATA #########################
ofile = os.path.join(idir, 'toe_%s_%s_%s.nc' % (var, per, tag))
TOE = xr.open_dataset(ofile)['__xarray_dataarray_variable__']

# PART 1: BUILD TOE YEAR GRID #########################
# t_TOE holds, for each grid point, the year when TOE
# passes the threshold

# First and last year of the results (taken from the data, e.g. 2020-2100 or 2020-2067)
y_ini = int(TOE['time.year'][0])
y_end = int(TOE['time.year'][-1])
print("Results period: %d-%d" % (y_ini, y_end))

# One color per year: each year goes from y to y+1
levels = list(range(y_ini, y_end + 2))
# Year labels every 10 years, always showing y_ini and y_end
year_ticks = list(range(y_ini, y_end - 4, 10)) + [y_end]
# Colorbar: 75% of the panel height, labels in the middle of each year color
cbar_kw = {'label': 'Year', 'shrink': 0.75,
           'ticks': [t + 0.5 for t in year_ticks], 'format': lambda x, pos: '%d' % x}

t_TOE = TOE * np.nan  # Start with NaN
tpr = y_ini

for tpru in range(len(TOE.time)):
    t_TOE = t_TOE.where(~((TOE < tpr) & (TOE['time.year'] == tpr)), tpr)
    tpr = tpr + 1

# PART 2: THRESHOLDS FOR EACH VARIABLE #########################
# Thresholds are signal-to-noise values (TOE = signal / sqrt(VI)), not degrees or percent
# Precipitation (pr): -1 (decrease) and +1 (increase)
# Temperature (tas, tasmax, tasmin): +1, +2 and +3
# (threshold, file name, title)
if var == 'pr':
    umbrales = [(1, 'umbral_positivo', 'Aumento (+1)'),
                (-1, 'umbral_negativo', 'Disminución (-1)')]
else:
    umbrales = [(1, 'umbral_bajo', 'Umbral bajo (+1)'),
                (2, 'umbral_alto', 'Umbral alto (+2)'),
                (3, 'umbral_muy_alto', 'Umbral muy alto (+3)')]

def anio_umbral(umbr):
    """Year when TOE first passes the threshold (above if umbr > 0, below if umbr < 0).
    NaN where it never passes it in the results period."""
    TOE_umbr = TOE[0] * 0  # Start with zero
    for t in range(len(TOE.time)):
        cruza = (TOE[t] < umbr) if umbr < 0 else (TOE[t] > umbr)
        TOE_umbr = TOE_umbr.where(~(cruza & (TOE_umbr <= 0)), t_TOE[t])
    return TOE_umbr.where(~(TOE_umbr == 0), np.nan)

# PART 3: TOE MAPS (one per threshold) #########################
for umbr, name, title in umbrales:
    TOE_u = anio_umbral(umbr)
    fig, ax = plt.subplots(figsize=(6, 8))
    TOE_u.plot(ax=ax, levels=levels, cmap='turbo', cbar_kwargs=cbar_kw)
    ax.set_xlim(-83, -67)     # Longitude
    ax.set_ylim(-19, 0.5)     # Latitude
    # --- SHAPEFILES ---
    shp_peru.plot(ax=ax, fc='none', edgecolor='black', linewidth=0.8)
    shp_suda.plot(ax=ax, fc='white', edgecolor='gray', linewidth=0.3)
    # --- LABELS ---
    ax.set_xlabel('Longitud')
    ax.set_ylabel('Latitud')
    ax.set_title('Time of Emergence - %s\n%s, %s, %d-%d, %s' % (title, var.upper(), tri.upper(), y_ini, y_end, metodo), fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(odir, 'TOE_%s_%s_%s_%s.png' % (var, tri, name, tag)), dpi=100, bbox_inches='tight')
    plt.close()

# PART 4: UNCERTAINTY SPLIT FOR PERU #########################
# Percent of each uncertainty source
# in the Peru region (lat: -17 to -12, lon: -75 to -70)

varn = '__xarray_dataarray_variable__'

mu_perc = xr.open_dataset(os.path.join(idir, 'Tmu_%s_%s_%s.nc' % (var, per, tag)))[varn]\
    .sel(lat=slice(-17, -12), lon=slice(-75, -70))\
    .mean(dim=['lon', 'lat'])

su_perc = xr.open_dataset(os.path.join(idir, 'Tsu_%s_%s_%s.nc' % (var, per, tag)))[varn]\
    .sel(lat=slice(-17, -12), lon=slice(-75, -70))\
    .mean(dim=['lon', 'lat'])

vi_perc = xr.open_dataset(os.path.join(idir, 'Tvi_%s_%s_%s.nc' % (var, per, tag)))[varn]\
    .sel(lat=slice(-17, -12), lon=slice(-75, -70))\
    .mean(dim=['lon', 'lat'])

# Total uncertainty and percent of each source
total = vi_perc + su_perc + mu_perc
pvi = vi_perc * 100 / total   # Internal Variability (%)
psu = su_perc * 100 / total   # Scenario Uncertainty (%)
pmu = mu_perc * 100 / total   # Model Uncertainty (%)

# PART 5: UNCERTAINTY FRACTION PLOT #########################

color_m = ['#1a4a8c', '#fb0b26', '#fbd326']
label = ['Incertidumbre Modelo', 'Incertidumbre Escenario', 'Variabilidad Interna']

fig, ax = plt.subplots(1, 1, figsize=(9, 6), sharey=True, sharex=True)
fig.subplots_adjust(hspace=0.17, wspace=0.05)
fig.suptitle('PERU', y=0.99, fontsize=18)

ax.stackplot(pmu['time.year'], pmu, psu, pvi, labels=label, colors=color_m)
ax.set_title('%s (%d-%d) - %s' % (tri.upper(), y_ini, y_end, metodo), fontsize=12)
ax.set_ylabel('Porcentaje de incertidumbre (%)')
ax.legend(loc='upper left', fontsize=11)
ax.margins(0, 0)
ax.set_xlim(y_ini, y_end)
ax.set_xticks(year_ticks)
ax.set_ylim(0, 100)

plt.savefig(os.path.join(odir, 'Fraccion_incertidumbre_peru_%s_%s_interpol_%s.png' % (var, tri, tag)),
            dpi=100, bbox_inches='tight')
plt.close()