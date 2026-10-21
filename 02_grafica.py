# ============================
# DIRECTORIES (defaults; can also be given as arguments 3 and 4)
idir = 'out'    # Input folder (.nc files made by 01_uncertainty.py)
odir = 'figures'    # Output folder (.png figures)
vi_stat = 'var'     # Which results to plot: 'var' or 'std' (can also be given as --vi=std or --vi=var)
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
args = [a for a in sys.argv[1:] if not a.startswith('--')]
var = args[0]       # Variable: 'pr' (precipitation) or 'tas' (temperature)
tri = args[1]  # Season: 'djf', 'mam', 'jja', 'son', or 'ann' (annual)
if len(args) > 2: idir = args[2]  # Input folder (optional)
if len(args) > 3: odir = args[3]  # Output folder (optional)
if vi_stat not in ('std', 'var'):
    print("ERROR: --vi must be 'std' or 'var', got '%s'." % vi_stat)
    sys.exit(1)

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
print("Internal variability (VI) as: %s" % vi_stat)

os.makedirs(odir, exist_ok=True)

# CHECK INPUT FILES #########################
# Make sure the input files exist before going on
archivos_entrada = [
    os.path.join(idir, 'toe_%s_%s_%s.nc' % (var, per, vi_stat)),
    os.path.join(idir, 'Tmu_%s_%s_%s.nc' % (var, per, vi_stat)),
    os.path.join(idir, 'Tsu_%s_%s_%s.nc' % (var, per, vi_stat)),
    os.path.join(idir, 'Tvi_%s_%s_%s.nc' % (var, per, vi_stat))
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
ofile = os.path.join(idir, 'toe_%s_%s_%s.nc' % (var, per, vi_stat))
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
# Precipitation (pr): negative (-1) and positive (+1) threshold
# Temperature (tas): +1 and +2 threshold

if var == 'pr':
    # --- PRECIPITATION THRESHOLDS ---
    for umbr in [-1, 1]:
        TOE_umbr = TOE[0] * 0  # Start with zero
        for t in range(len(TOE.time)):
            if umbr == -1:
                TOE_umbr = TOE_umbr.where(
                    ~((TOE[t] < umbr) & (TOE_umbr <= 0)), t_TOE[t]
                )
                TOE_umbralnegativo_pr = TOE_umbr
            else:
                TOE_umbr = TOE_umbr.where(
                    ~((TOE[t] > umbr) & (TOE_umbr <= 0)), t_TOE[t]
                )
                TOE_umbralpositivo_pr = TOE_umbr
    TOE_1 = TOE_umbralnegativo_pr.where(~(TOE_umbralnegativo_pr == 0), np.nan)
    TOE_2 = TOE_umbralpositivo_pr.where(~(TOE_umbralpositivo_pr == 0), np.nan)

else:
    # --- TEMPERATURE THRESHOLDS ---
    for umbr in [1, 2]:
        TOE_umbr = TOE[0] * 0  # Start with zero
        for t in range(len(TOE.time)):
            TOE_umbr = TOE_umbr.where(
                ~((TOE[t] > umbr) & (TOE_umbr <= 0)), t_TOE[t]
            )
            if umbr == 1:
                TOE_u1_tas = TOE_umbr  # +1 threshold
            else:
                TOE_u2_tas = TOE_umbr  # +2 threshold
    TOE_1 = TOE_u1_tas.where(~(TOE_u1_tas == 0), np.nan)
    TOE_2 = TOE_u2_tas.where(~(TOE_u2_tas == 0), np.nan)

# PART 3: TOE MAPS #########################
# Thresholds are signal-to-noise values (signal / std of internal variability)
# pr:  TOE_2 = +1 (increase),  TOE_1 = -1 (decrease)
# tas: TOE_2 = +2 (high),      TOE_1 = +1 (low)
if var == 'pr':
    name_2, title_2 = 'umbral_positivo', 'Aumento (+1)'
    name_1, title_1 = 'umbral_negativo', 'Disminución (-1)'
else:
    name_2, title_2 = 'umbral_alto', 'Umbral alto (+2)'
    name_1, title_1 = 'umbral_bajo', 'Umbral bajo (+1)'

# --- TOE_2 map ---
fig, ax = plt.subplots(figsize=(10, 8))
TOE_2.plot(ax=ax, levels=levels, cmap='turbo', cbar_kwargs=cbar_kw)
ax.set_xlim(-83, -67)   #
ax.set_ylim(-19, 0.5)     #
# --- SHAPEFILES ---
shp_peru.plot(ax=ax, fc='none', edgecolor='black', linewidth=0.8)
shp_suda.plot(ax=ax, fc='white', edgecolor='gray', linewidth=0.3)
# --- LABELS ---
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')
ax.set_title('Time of Emergence - %s (%s, %s, %d-%d, VI: %s)' % (title_2, var.upper(), tri.upper(), y_ini, y_end, vi_stat))
plt.tight_layout()
plt.savefig(os.path.join(odir, 'TOE_%s_%s_%s_%s.png' % (var, tri, name_2, vi_stat)), dpi=100, bbox_inches='tight')
plt.close()

# --- TOE_1 map ---
fig, ax = plt.subplots(figsize=(10, 8))
TOE_1.plot(ax=ax, levels=levels, cmap='turbo', cbar_kwargs=cbar_kw)
ax.set_xlim(-83, -67)   # Longitude
ax.set_ylim(-19, 0.5)     # Latitude
# --- SHAPEFILES ---
shp_peru.plot(ax=ax, fc='none', edgecolor='black', linewidth=0.8)
shp_suda.plot(ax=ax, fc='white', edgecolor='gray', linewidth=0.3)
# --- LABELS ---
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')
ax.set_title('Time of Emergence - %s (%s, %s, %d-%d, VI: %s)' % (title_1, var.upper(), tri.upper(), y_ini, y_end, vi_stat))
plt.tight_layout()
plt.savefig(os.path.join(odir, 'TOE_%s_%s_%s_%s.png' % (var, tri, name_1, vi_stat)), dpi=100, bbox_inches='tight')
plt.close()

# PART 4: UNCERTAINTY SPLIT FOR PERU #########################
# Percent of each uncertainty source
# in the Peru region (lat: -17 to -12, lon: -75 to -70)

varn = '__xarray_dataarray_variable__'

mu_perc = xr.open_dataset(os.path.join(idir, 'Tmu_%s_%s_%s.nc' % (var, per, vi_stat)))[varn]\
    .sel(lat=slice(-17, -12), lon=slice(-75, -70))\
    .mean(dim=['lon', 'lat'])

su_perc = xr.open_dataset(os.path.join(idir, 'Tsu_%s_%s_%s.nc' % (var, per, vi_stat)))[varn]\
    .sel(lat=slice(-17, -12), lon=slice(-75, -70))\
    .mean(dim=['lon', 'lat'])

vi_perc = xr.open_dataset(os.path.join(idir, 'Tvi_%s_%s_%s.nc' % (var, per, vi_stat)))[varn]\
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
ax.set_title('%s (%d-%d) - VI: %s' % (tri.upper(), y_ini, y_end, vi_stat), fontsize=12)
ax.set_ylabel('Porcentaje de incertidumbre (%)')
ax.legend(loc='upper left', fontsize=11)
ax.margins(0, 0)
ax.set_xlim(y_ini, y_end)
ax.set_xticks(year_ticks)
ax.set_ylim(0, 100)

plt.savefig(os.path.join(odir, 'Fraccion_incertidumbre_peru_%s_%s_interpol_%s.png' % (var, tri, vi_stat)),
            dpi=100, bbox_inches='tight')
plt.close()