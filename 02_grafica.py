import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import geopandas as gpd
import sys
import os

############################
# CONFIGURACION DE VARIABLES Y PERIODO
var = sys.argv[1]       # Variable: 'pr' (precipitacion) o 'tas' (temperatura)
tri = sys.argv[2]  #  Trimestre : 'jja'

# MAPEO DE PERIODOS
# 'def' (default/estandar) se mapea a periodo 'm1'
# 'jja' (junio-julio-agosto) se mapea a periodo 'm7'
if tri == 'def': per = 'm1'
elif tri == 'jja': per = 'm7'
print(var, per)

# VERIFICACION DE ARCHIVOS DE ENTRADA #########################
# Verifica que los archivos de entrada existan antes de continuar
archivos_entrada = [
    'out/toe_%s_%s.nc' % (var, per),
    'out/Tmu_%s_%s.nc' % (var, per),
    'out/Tsu_%s_%s.nc' % (var, per),
    'out/Tvi_%s_%s.nc' % (var, per)
]

for archivo in archivos_entrada:
    if not os.path.exists(archivo):
        print("ERROR: No se encontro el archivo de entrada:")
        print("  -> %s" % archivo)
        print("Ejecute primero el script de calculo de incertidumbre.")
        sys.exit(1)

# CARGA DE SHAPEFILES (limites geograficos) #########################
# Carga los shapefiles de Peru y Sudamerica para los mapas
shp_peru = gpd.read_file('shape/peru.shp')
shp_suda = gpd.read_file('shape/suda.shp')
#
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['DejaVu Serif'],
    'font.size': 12,
})
# CARGA DE DATOS TOE #########################
ofile = 'out/toe_%s_%s.nc' % (var, per)
TOE = xr.open_dataset(ofile)['__xarray_dataarray_variable__']

# PARTE 1: CONSTRUCCION DE MATRIZ TEMPORAL DE TOE #########################
# Crea una matriz t_TOE donde cada celda contiene el año en que TOE
# supera el umbral correspondiente para cada punto de grilla

t_TOE = TOE * np.nan  # Inicializa con NaN
tpr = 2020

for tpru in range(len(TOE.time)):
    t_TOE = t_TOE.where(~((TOE < tpr) & (TOE['time.year'] == tpr)), tpr)
    tpr = tpr + 1

# PARTE 2: APLICACION DE UMBRALES POR VARIABLE #########################
# Para precipitacion (pr): umbral negativo (-1) y positivo (+1)
# Para temperatura (tas): umbral +1 y +2 (grados de anomalia)

if var == 'pr':
    # --- UMBRALES PARA PRECIPITACION ---
    for umbr in [-1, 1]:
        TOE_umbr = TOE[0] * 0  # Inicializa en cero
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
    # --- UMBRALES PARA TEMPERATURA ---
    for umbr in [1, 2]:
        TOE_umbr = TOE[0] * 0  # Inicializa en cero
        for t in range(len(TOE.time)):
            TOE_umbr = TOE_umbr.where(
                ~((TOE[t] > umbr) & (TOE_umbr <= 0)), t_TOE[t]
            )
            if umbr == 1:
                TOE_u1_tas = TOE_umbr  # Umbral +1°C
            else:
                TOE_u2_tas = TOE_umbr  # Umbral +2°C
    TOE_1 = TOE_u1_tas.where(~(TOE_u1_tas == 0), np.nan)
    TOE_2 = TOE_u2_tas.where(~(TOE_u2_tas == 0), np.nan)

# PARTE 3: MAPAS DE TOE #########################

# --- Mapa umbral alto (TOE_2: +2°C para tas, +1 para pr) ---
fig, ax = plt.subplots(figsize=(10, 8))
TOE_2.plot(ax=ax, levels=np.arange(2020, 2104, 4), cmap='turbo')
ax.set_xlim(-83, -67)   #
ax.set_ylim(-19, 0.5)     #
# --- SHAPEFILES ---
shp_peru.plot(ax=ax, fc='none', edgecolor='black', linewidth=0.8)
shp_suda.plot(ax=ax, fc='white', edgecolor='gray', linewidth=0.3)
# --- ETIQUETAS ---
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')
ax.set_title('Time of Emergence - Umbral alto (%s, %s)' % (var.upper(), tri.upper()))
plt.tight_layout()
plt.savefig('out/TOE_%s_%s_umbral_alto.png' % (var, tri), dpi=100, bbox_inches='tight')
plt.show()

# --- Mapa umbral bajo (TOE_1: +1°C para tas, -1 para pr) ---
fig, ax = plt.subplots(figsize=(10, 8))
TOE_1.plot(ax=ax, levels=np.arange(2020, 2104, 4), cmap='turbo')
ax.set_xlim(-83, -67)   # Longitud
ax.set_ylim(-19, 0.5)     # Latitud
# --- SHAPEFILES ---
shp_peru.plot(ax=ax, fc='none', edgecolor='black', linewidth=0.8)
shp_suda.plot(ax=ax, fc='white', edgecolor='gray', linewidth=0.3)
# --- ETIQUETAS ---
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')
ax.set_title('Time of Emergence - Umbral bajo (%s, %s)' % (var.upper(), tri.upper()))
plt.tight_layout()
plt.savefig('out/TOE_%s_%s_umbral_bajo.png' % (var, tri), dpi=100, bbox_inches='tight')
plt.show()

# PARTE 4: DECOMPOSICION DE INCERTIDUMBRE PARA PERU #########################
# Calcula la fraccion porcentual de cada componente de incertidumbre
# en la region de Peru (lat: -17 a -12, lon: -75 a -70)

varn = '__xarray_dataarray_variable__'

mu_perc = xr.open_dataset('out/Tmu_%s_%s.nc' % (var, per))[varn]\
    .sel(lat=slice(-17, -12), lon=slice(-75, -70))\
    .mean(dim=['lon', 'lat'])

su_perc = xr.open_dataset('out/Tsu_%s_%s.nc' % (var, per))[varn]\
    .sel(lat=slice(-17, -12), lon=slice(-75, -70))\
    .mean(dim=['lon', 'lat'])

vi_perc = xr.open_dataset('out/Tvi_%s_%s.nc' % (var, per))[varn]\
    .sel(lat=slice(-17, -12), lon=slice(-75, -70))\
    .mean(dim=['lon', 'lat'])

# Incertidumbre total y fraccion porcentual de cada componente
total = vi_perc + su_perc + mu_perc
pvi = vi_perc * 100 / total   # Variabilidad Interna (%)
psu = su_perc * 100 / total   # Incertidumbre de Escenario (%)
pmu = mu_perc * 100 / total   # Incertidumbre de Modelo (%)

# PARTE 5: GRAFICO DE FRACCION DE INCERTIDUMBRE #########################

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

plt.savefig('out/Fraccion_incertidumbre_peru_%s_%s_interpol.png' % (var, tri),
            dpi=100, bbox_inches='tight')
plt.show()