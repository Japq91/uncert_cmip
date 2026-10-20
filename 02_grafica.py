# ============================
# DIRECTORIES (change here if needed)
idir = 'out'    # Input folder (.nc files made by 01_uncertainty.py)
odir = 'figures'    # Output folder (.png figures)
# ============================

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import geopandas as gpd
import sys
import os

############################
# VARIABLE AND SEASON
var = sys.argv[1]       # Variable: 'pr' (precipitation) or 'tas' (temperature)
tri = sys.argv[2]  # Season: 'djf' or 'jja'

# SEASON TO FILE PREFIX
# 'djf' (December-January-February) -> 'm1'
# 'jja' (June-July-August) -> 'm7'
if tri == 'djf': per = 'm1'
elif tri == 'jja': per = 'm7'
print(var, per)

os.makedirs(odir, exist_ok=True)

# CHECK INPUT FILES #########################
# Make sure the input files exist before going on
archivos_entrada = [
    os.path.join(idir, 'toe_%s_%s.nc' % (var, per)),
    os.path.join(idir, 'Tmu_%s_%s.nc' % (var, per)),
    os.path.join(idir, 'Tsu_%s_%s.nc' % (var, per)),
    os.path.join(idir, 'Tvi_%s_%s.nc' % (var, per))
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
ofile = os.path.join(idir, 'toe_%s_%s.nc' % (var, per))
TOE = xr.open_dataset(ofile)['__xarray_dataarray_variable__']

# PART 1: BUILD TOE YEAR GRID #########################
# t_TOE holds, for each grid point, the year when TOE
# passes the threshold

t_TOE = TOE * np.nan  # Start with NaN
tpr = 2020

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

# --- High threshold map (TOE_2: +2 for tas, +1 for pr) ---
fig, ax = plt.subplots(figsize=(10, 8))
TOE_2.plot(ax=ax, levels=np.arange(2020, 2104, 4), cmap='turbo')
ax.set_xlim(-83, -67)   #
ax.set_ylim(-19, 0.5)     #
# --- SHAPEFILES ---
shp_peru.plot(ax=ax, fc='none', edgecolor='black', linewidth=0.8)
shp_suda.plot(ax=ax, fc='white', edgecolor='gray', linewidth=0.3)
# --- LABELS ---
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')
ax.set_title('Time of Emergence - Umbral alto (%s, %s)' % (var.upper(), tri.upper()))
plt.tight_layout()
plt.savefig(os.path.join(odir, 'TOE_%s_%s_umbral_alto.png' % (var, tri)), dpi=100, bbox_inches='tight')
plt.close()

# --- Low threshold map (TOE_1: +1 for tas, -1 for pr) ---
fig, ax = plt.subplots(figsize=(10, 8))
TOE_1.plot(ax=ax, levels=np.arange(2020, 2104, 4), cmap='turbo')
ax.set_xlim(-83, -67)   # Longitude
ax.set_ylim(-19, 0.5)     # Latitude
# --- SHAPEFILES ---
shp_peru.plot(ax=ax, fc='none', edgecolor='black', linewidth=0.8)
shp_suda.plot(ax=ax, fc='white', edgecolor='gray', linewidth=0.3)
# --- LABELS ---
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')
ax.set_title('Time of Emergence - Umbral bajo (%s, %s)' % (var.upper(), tri.upper()))
plt.tight_layout()
plt.savefig(os.path.join(odir, 'TOE_%s_%s_umbral_bajo.png' % (var, tri)), dpi=100, bbox_inches='tight')
plt.close()

# PART 4: UNCERTAINTY SPLIT FOR PERU #########################
# Percent of each uncertainty source
# in the Peru region (lat: -17 to -12, lon: -75 to -70)

varn = '__xarray_dataarray_variable__'

mu_perc = xr.open_dataset(os.path.join(idir, 'Tmu_%s_%s.nc' % (var, per)))[varn]\
    .sel(lat=slice(-17, -12), lon=slice(-75, -70))\
    .mean(dim=['lon', 'lat'])

su_perc = xr.open_dataset(os.path.join(idir, 'Tsu_%s_%s.nc' % (var, per)))[varn]\
    .sel(lat=slice(-17, -12), lon=slice(-75, -70))\
    .mean(dim=['lon', 'lat'])

vi_perc = xr.open_dataset(os.path.join(idir, 'Tvi_%s_%s.nc' % (var, per)))[varn]\
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

ax.stackplot(range(2020, 2101), pmu, psu, pvi, labels=label, colors=color_m)
ax.set_title(tri.upper(), fontsize=12)
ax.set_ylabel('Porcentaje de incertidumbre (%)')
ax.legend(loc='upper left', fontsize=11)
ax.margins(0, 0)
ax.set_xlim(2020, 2100)
ax.set_ylim(0, 100)

plt.savefig(os.path.join(odir, 'Fraccion_incertidumbre_peru_%s_%s_interpol.png' % (var, tri)),
            dpi=100, bbox_inches='tight')
plt.close()