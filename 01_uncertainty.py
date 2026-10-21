# ============================
# DIRECTORIES (defaults; can also be given as arguments 3 and 4)
idir = 'data'   # Input folder (one subfolder per season: data/<tri>/)
odir = 'out'    # Output folder
# ============================

import pandas as pd
import xarray as xr
from glob import glob as gb
import os
import re
import sys
import warnings
warnings.filterwarnings("ignore")

############################
# READ COMMAND LINE ARGUMENTS
# --force: run the calculation even if the output files already exist
force = '--force' in sys.argv
args = [a for a in sys.argv[1:] if a != '--force']
var = args[0]       # Variable: 'pr' (precipitation) or 'tas' (temperature)
tri = args[1]  # Season: 'djf', 'mam', 'jja' or 'son'
if len(args) > 2: idir = args[2]  # Input folder (optional)
if len(args) > 3: odir = args[3]  # Output folder (optional)

# SEASON TO FILE PREFIX
# 'djf' (December-January-February) -> 'm1'
# 'mam' (March-April-May) -> 'm4'
# 'jja' (June-July-August) -> 'm7'
# 'son' (September-October-November) -> 'm10'
if tri == 'djf': per = 'm1'
elif tri == 'mam': per = 'm4'
elif tri == 'jja': per = 'm7'
elif tri == 'son': per = 'm10'
print(var, per)
print("Input folder:  %s" % os.path.abspath(os.path.join(idir, tri)))
print("Output folder: %s" % os.path.abspath(odir))

# FUNCTIONS #########################

def polinom(d, var):
    """
    Fit a degree 4 polynomial to the time series and return:
    - delta: anomaly from the 1981-2010 reference period
    - residuo: percent difference between the data and the polynomial
    """
    # Polynomial coefficients (degree 4)
    coef = d.polyfit(dim='time', deg=4, full=True)
    # Fitted polynomial series
    s_poli = xr.polyval(coord=d.time, coeffs=coef['%s_polyfit_coefficients' % var])
    # Residual = e(t): percent difference between data and polynomial
    residuo0 = ((d[var] / s_poli) * 100) - 100
    # Mean of the reference period (1981-2010)
    prom_PR = s_poli.sel(time=slice('1981', '2010')).mean(dim='time')
    # Delta: anomaly from the reference period
    if 't' in var:
        # Temperature: absolute difference (degrees)
        delta0 = s_poli - ((s_poli / s_poli) * prom_PR)
    else:
        # Precipitation: percent difference
        delta0 = ((s_poli / prom_PR) * 100) - 100
    return delta0, residuo0

# CHECK EXISTING OUTPUT FILES #########################
# If the 4 output files already exist, skip the calculation (unless --force)
os.makedirs(odir, exist_ok=True)

archivos_salida = [
    os.path.join(odir, 'toe_%s_%s.nc' % (var, per)),
    os.path.join(odir, 'Tmu_%s_%s.nc' % (var, per)),
    os.path.join(odir, 'Tsu_%s_%s.nc' % (var, per)),
    os.path.join(odir, 'Tvi_%s_%s.nc' % (var, per))
]

todos_existentes = all(os.path.exists(f) for f in archivos_salida)

if todos_existentes and not force:
    print("=" * 50)
    print("WARNING: Output files already exist.")
    for f in archivos_salida:
        print("  -> %s" % f)
    print("Skipping calculation. Delete these files or use --force to run it again.")
    print("=" * 50)
    sys.exit(0)

############################
# PART 1: READ DATA AND FIT POLYNOMIAL
# Read the NetCDF files for each SSP scenario found in the input folder
# Get delta and residual for each model, then group by scenario

# Find scenarios from the file names (..._ssp126.nc -> '126')
all_files = gb(os.path.join(idir, tri, '%s_%s_*_ssp*.nc' % (per, var)))
matches = [re.search(r'_ssp(\d+)\.nc$', f) for f in all_files]
scenarios = sorted({m.group(1) for m in matches if m})
print("Scenarios found: %s" % ', '.join('SSP' + e for e in scenarios))

# Scenario uncertainty is the variance between scenarios: we need at least 2
if len(scenarios) < 2:
    print("ERROR: Need at least 2 scenarios in %s, found %d."
          % (os.path.join(idir, tri), len(scenarios)))
    sys.exit(1)

j=0; k=0
for n, exp in enumerate(scenarios):
    files = gb(os.path.join(idir, tri, '%s_%s_*_ssp%s.nc' % (per, var, exp)))
    print("Processing scenario SSP%s (%d models)..." % (exp, len(files)))
    # Model uncertainty is the variance between models: we need at least 2
    if len(files) < 2:
        print("ERROR: Need at least 2 models for SSP%s, found %d." % (exp, len(files)))
        sys.exit(1)
    i = 0
    for file in files[:]:
        ds0 = xr.open_dataset(file)
        ds = ds0[[var]].sortby('lat', ascending=True)  # Make sure latitude goes from south to north
        delta, residuo = polinom(ds, var)
        if i == 0:
            delta2 = delta
        else:
            delta2 = xr.concat([delta, delta2], dim='time')
        if j == 0:
            delta3 = delta
            residuo4 = residuo
        else:
            delta3 = xr.concat([delta, delta3], dim='time')
            residuo4 = xr.concat([residuo, residuo4], dim='time')
        j = j + 1
        k = k + 1
        i = i + 1

    # Sort by time and get statistics for this scenario
    delta21 = delta2.sortby('time', ascending=True)
    # Variance between models (one scenario)
    var_delta21 = delta21.groupby('time.year').var()
    # Mean of all models (one scenario)
    prom_delta21 = delta21.groupby('time.year').mean()

    if n == 0:
        lst_var_mdl = var_delta21
        lst_prom_mdl = prom_delta21
    else:
        lst_var_mdl = xr.concat([lst_var_mdl, var_delta21], dim='year')
        lst_prom_mdl = xr.concat([lst_prom_mdl, prom_delta21], dim='year')

########## PART 2: COMBINE SCENARIOS AND COMPUTE UNCERTAINTIES #########

# Sort the values collected for each scenario
var_mdl_2 = lst_var_mdl.sortby('year', ascending=True)
prom_mdl_2 = lst_prom_mdl.sortby('year', ascending=True)

# Sort deltas and residuals of all models and scenarios
delta31 = delta3.sortby('time', ascending=True)
residuo41 = residuo4.sortby('time', ascending=True)

# G0: mean of all models and all scenarios (climate signal)
G0 = delta31.groupby('time.year').mean()
G0['year'] = pd.date_range('1981', freq='12M', periods=len(G0.year))
G0 = G0.rename({'year': 'time'})

# SU: Scenario Uncertainty
# Variance between the model means of each scenario
SU0 = prom_mdl_2.groupby('year').var()
SU0['year'] = pd.date_range('1981', freq='12M', periods=len(SU0.year))
SU0 = SU0.rename({'year': 'time'})

# MU: Model Uncertainty
# Mean of the variance between models in each scenario
MU0 = var_mdl_2.groupby('year').mean()
MU0['year'] = pd.date_range('1981', freq='12M', periods=len(MU0.year))
MU0 = MU0.rename({'year': 'time'})

########## PART 3: INTERNAL VARIABILITY (VI) WITH MOVING WINDOWS #########

# Standard deviation of the residual in 30-year windows
# The window moves one year at a time, giving a VI time series
year_c = 2010
l = 0
for ktime in range(len(ds['time']) - 30):
    y_i = residuo41['time.year'][ktime * k].values
    yi = str(y_i.tolist())
    y_f = (residuo41['time.year'][ktime * k].values) + 29
    yf = str(y_f.tolist())
    # Select a 30-year window
    residuo42 = residuo41.sel(time=slice(yi, yf))
    # Standard deviation and variance inside the window
    residuo43_std = residuo42.std(dim='time')
    residuo43_var = residuo42.var(dim='time')
    year_c = year_c + 1
    # Add a time dimension so we can concatenate
    time_d = pd.date_range('%d' % year_c, freq='1Y', periods=1)
    time_ds = xr.DataArray(time_d, [('time', time_d)])
    residuo44_std = residuo43_std.expand_dims(time=time_ds)
    residuo44_var = residuo43_var.expand_dims(time=time_ds)
    if l == 0:
        residuo_45_std = residuo44_std
        residuo_45_var = residuo44_var
    else:
        residuo_45_std = xr.concat([residuo44_std, residuo_45_std], dim='time')
        residuo_45_var = xr.concat([residuo44_var, residuo_45_var], dim='time')
    l = l + 1

########## PART 4: SMOOTHING AND PERIOD SELECTION #########

# Sort Internal Variability and set its dates
VI0 = residuo_45_std.sortby('time', ascending=True)
VI0['time'] = pd.date_range('2011', freq='12M', periods=len(VI0.time))
# 10-year moving average
VI1 = VI0.rolling(time=10, center=False).mean()

# Keep the common analysis period: 2020-2100
VI = VI1.sel(time=slice('2020', '2100'))
G = G0.sel(time=slice('2020', '2100'))
SU = SU0.sel(time=slice('2020', '2100'))
MU = MU0.sel(time=slice('2020', '2100'))

########## PART 5: STN AND TOE, AND SAVE RESULTS #########

# TU: Total Uncertainty = Internal Variability + Model Uncertainty + Scenario Uncertainty
TU = VI + MU + SU

# STN: Signal-to-Noise Ratio
STN = G / (TU) ** 0.5

# TOE: Time of Emergence (when the climate change signal emerges)
TOE = G / (VI) ** 0.5

# Save results as NetCDF files
print("Saving output files...")
TOE.to_netcdf(os.path.join(odir, 'toe_%s_%s.nc' % (var, per)))
MU.to_netcdf(os.path.join(odir, 'Tmu_%s_%s.nc' % (var, per)))
SU.to_netcdf(os.path.join(odir, 'Tsu_%s_%s.nc' % (var, per)))
VI.to_netcdf(os.path.join(odir, 'Tvi_%s_%s.nc' % (var, per)))
print("Calculation finished.")