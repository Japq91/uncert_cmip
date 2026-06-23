import pandas as pd
import xarray as xr
from glob import glob as gb
import os
import sys
import warnings
warnings.filterwarnings("ignore")

############################
# LECTURA DE ARGUMENTOS DE LINEA DE COMANDOS
var = sys.argv[1]       # Variable: 'pr' (precipitacion) o 'tas' (temperatura)
tri = sys.argv[2]  #  Trimestre : 'jja'

# MAPEO DE PERIODOS
# 'def' (default/estandar) se mapea a periodo 'm1'
# 'jja' (junio-julio-agosto) se mapea a periodo 'm7'
if tri == 'def': per = 'm1'
elif tri == 'jja': per = 'm7'
print(var, per)

# FUNCIONES #########################

def polinom(d, var):
    """
    Ajusta un polinomio de grado 4 a la serie temporal y calcula:
    - delta: anomalia respecto al periodo de referencia 1981-2010
    - residuo: desviacion porcentual del dato respecto al polinomio
    """
    # Genera los coeficientes del polinomio de grado 4
    coef = d.polyfit(dim='time', deg=4, full=True)
    # Serie polinomica ajustada
    s_poli = xr.polyval(coord=d.time, coeffs=coef['%s_polyfit_coefficients' % var])
    # Residuo = ε(t): desviacion porcentual del dato respecto al polinomio
    residuo0 = ((d[var] / s_poli) * 100) - 100
    # Promedio del Periodo de Referencia (1981-2010)
    prom_PR = s_poli.sel(time=slice('1981', '2010')).mean(dim='time')
    # Delta: anomalia respecto al periodo de referencia
    if 't' in var:
        # Para temperatura: diferencia absoluta ΔT
        delta0 = s_poli - ((s_poli / s_poli) * prom_PR)
    else:
        # Para precipitacion: diferencia porcentual ΔP
        delta0 = ((s_poli / prom_PR) * 100) - 100
    return delta0, residuo0

# VERIFICACION DE ARCHIVOS EXISTENTES #########################
# Si los 4 archivos de salida ya existen, se omite el calculo
out_dir = 'out'
os.makedirs(out_dir, exist_ok=True)

archivos_salida = [
    'out/toe_%s_%s.nc' % (var, per),
    'out/Tmu_%s_%s.nc' % (var, per),
    'out/Tsu_%s_%s.nc' % (var, per),
    'out/Tvi_%s_%s.nc' % (var, per)
]

todos_existentes = all(os.path.exists(f) for f in archivos_salida)

if todos_existentes:
    print("=" * 50)
    print("AVISO: Los archivos de salida ya existen.")
    for f in archivos_salida:
        print("  -> %s" % f)
    print("Omitiendo calculo. Para recalcular, elimine los archivos.")
    print("=" * 50)
    sys.exit(0)

############################
# PARTE 1: LECTURA DE DATOS Y AJUSTE POLINOMIAL
# Procesa los archivos NetCDF de cada escenario SSP (126, 245, 370, 585)
# Calcula delta y residuo para cada modelo, luego agrupa por escenario
j=0; k=0
for exp in ['126', '245', '370', '585'][:]:
    files = gb('data/%s/%s_%s*%s*.nc' % (tri, per, var, exp))
    i = 0
    print("Procesando escenario SSP%s..." % exp)
    for file in files[:]:
        ds = xr.open_dataset(file)
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

    # Ordena cronologicamente y calcula estadisticas por escenario
    delta21 = delta2.sortby('time', ascending=True)
    # Varianza entre modelos de un escenario
    var_delta21 = delta21.groupby('time.year').var()
    # Promedio entre modelos de un escenario
    prom_delta21 = delta21.groupby('time.year').mean()

    if '126' in exp:
        lst_var_mdl = var_delta21
        lst_prom_mdl = prom_delta21
    else:
        lst_var_mdl = xr.concat([lst_var_mdl, var_delta21], dim='year')
        lst_prom_mdl = xr.concat([lst_prom_mdl, prom_delta21], dim='year')

########## PARTE 2: AGREGACION DE ESCENARIOS Y CALCULO DE INCERTIDUMBRES #########

# Ordena las incertidumbres acumuladas por escenario
var_mdl_2 = lst_var_mdl.sortby('year', ascending=True)
prom_mdl_2 = lst_prom_mdl.sortby('year', ascending=True)

# Ordena los deltas y residuos de todos los modelos/escenarios
delta31 = delta3.sortby('time', ascending=True)
residuo41 = residuo4.sortby('time', ascending=True)

# G0: Promedio de todos los modelos en todos los escenarios (senal climatico)
G0 = delta31.groupby('time.year').mean()
G0['year'] = pd.date_range('1981', freq='12M', periods=len(G0.year))
G0 = G0.rename({'year': 'time'})

# SU: Incertidumbre de Escenarios (Scenario Uncertainty)
# Calculada como la varianza entre el promedio de modelos de cada escenario
SU0 = prom_mdl_2.groupby('year').var()
SU0['year'] = pd.date_range('1981', freq='12M', periods=len(SU0.year))
SU0 = SU0.rename({'year': 'time'})

# MU: Incertidumbre de Modelos (Model Uncertainty)
# Calculada como el promedio de la varianza entre modelos de cada escenario
MU0 = var_mdl_2.groupby('year').mean()
MU0['year'] = pd.date_range('1981', freq='12M', periods=len(MU0.year))
MU0 = MU0.rename({'year': 'time'})

########## PARTE 3: CALCULO DE VARIANZA INTERNA (VI) CON VENTANAS MOVILES #########

# Calcula la desviacion estandar del residuo en ventanas de 30 anos
# La ventana se desplaza ano a ano, generando una serie temporal de VI
year_c = 2010
l = 0
for ktime in range(len(ds['time']) - 30):
    y_i = residuo41['time.year'][ktime * k].values
    yi = str(y_i.tolist())
    y_f = (residuo41['time.year'][ktime * k].values) + 29
    yf = str(y_f.tolist())
    # Selecciona ventana de 30 anos
    residuo42 = residuo41.sel(time=slice(yi, yf))
    # Desviacion estandar y varianza intra-ventana
    residuo43_std = residuo42.std(dim='time')
    residuo43_var = residuo42.var(dim='time')
    year_c = year_c + 1
    # Expande dimension temporal para concatenar
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

########## PARTE 4: SUAVIZADO Y SELECCION DE PERIODO #########

# Ordena y asigna fechas a la Varianza Interna
VI0 = residuo_45_std.sortby('time', ascending=True)
VI0['time'] = pd.date_range('2011', freq='12M', periods=len(VI0.time))
# Suavizado con media movil de 10 anos
VI1 = VI0.rolling(time=10, center=False).mean()

# Selecciona el periodo comun de analisis: 2020-2100
VI = VI1.sel(time=slice('2020', '2100'))
G = G0.sel(time=slice('2020', '2100'))
SU = SU0.sel(time=slice('2020', '2100'))
MU = MU0.sel(time=slice('2020', '2100'))

########## PARTE 5: CALCULO DE STN Y TOE, Y EXPORTACION #########

# TU: Incertidumbre Total = Varianza Interna + Incertidumbre de Modelos + Incertidumbre de Escenarios
TU = VI + MU + SU

# STN: Signal-to-Noise Ratio (relacion senal/ruido)
STN = G / (TU) ** 0.5

# TOE: Time of Emergence (tiempo de emergencia del cambio climatico)
TOE = G / (VI) ** 0.5

# Exporta los resultados a archivos NetCDF
print("Guardando archivos de salida...")
TOE.to_netcdf('out/toe_%s_%s.nc' % (var, per))
MU.to_netcdf('out/Tmu_%s_%s.nc' % (var, per))
SU.to_netcdf('out/Tsu_%s_%s.nc' % (var, per))
VI.to_netcdf('out/Tvi_%s_%s.nc' % (var, per))
print("Calculo completado exitosamente.")