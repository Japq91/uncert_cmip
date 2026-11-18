# uncert_cmip

Descomposición de la incertidumbre en las proyecciones climáticas CMIP6 y cálculo del
**Time of Emergence (TOE)** para precipitación (`pr`) y temperatura media, máxima y mínima
(`tas`, `tasmax`, `tasmin`) sobre Sudamérica,
con énfasis en Perú.

La incertidumbre total de la proyección se separa en tres fuentes:

| Fuente | Abreviatura | Cómo se estima |
|---|---|---|
| Escenarios | SU | Varianza entre los promedios multimodelo de cada SSP |
| Modelos | MU | Promedio de la varianza entre modelos dentro de cada SSP |
| Variabilidad interna | VI | Dispersión del residuo respecto a un polinomio de grado 4, en ventanas móviles de 30 años |

Las anomalías se calculan respecto al periodo de referencia **1981–2010** (configurable en `01_uncertainty.py`).

## Estructura

```
.
├── setup_env.sh        # Crea el entorno virtual e instala los paquetes
├── setup_env1.sh       # Igual, para servidores con sistema antiguo (ver Instalación)
├── 00_procesa.sh       # Ejecuta el flujo completo (01 + 02 + 03)
├── 00_procesa_std.sh   # Mismo flujo con el método antiguo (VI como std, residuo en %)
├── 01_uncertainty.py   # Calcula SU, MU, VI y TOE  -> out/
├── 02_grafica.py       # Genera mapas y gráficos     -> figures/
├── 03_series_modelos.py # Series de tiempo de cada modelo -> figures/
├── Clase.ipynb         # Versión paso a paso del análisis (notebook)
├── uncert_2026.ppt     # Presentación
├── data/
│   ├── djf/            # Archivos m1_<var>_<modelo>_<ssp>.nc  (diciembre-enero-febrero)
│   └── jja/            # Archivos m7_<var>_<modelo>_<ssp>.nc  (junio-julio-agosto)
└── shape/              # Shapefiles de Perú y Sudamérica
```

**Modelos:** ACCESS-CM2, AWI-CM-1-1-MR, FGOALS-f3-L, GFDL-ESM4, IPSL-CM6A-LR, KACE-1-0-G, MRI-ESM2-0  
**Escenarios:** SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5

Los modelos y escenarios se detectan automáticamente a partir de los nombres de archivo en
`data/<trimestre>/` (formato `<per>_<var>_<modelo>_ssp<XXX>.nc`). Para agregar o quitar uno,
basta con agregar o borrar sus archivos. Se necesitan al menos 2 escenarios y 2 modelos por escenario.

### Trimestres y anual

Cada archivo tiene **un valor por año**, que resume un trimestre o el año completo. Cada periodo
tiene su subcarpeta en `data/` y su prefijo en los nombres de archivo:

| Opción | Periodo | Carpeta | Prefijo |
|---|---|---|---|
| `djf` | diciembre-enero-febrero | `data/djf/` | `m1_` |
| `mam` | marzo-abril-mayo | `data/mam/` | `m4_` |
| `jja` | junio-julio-agosto | `data/jja/` | `m7_` |
| `son` | septiembre-octubre-noviembre | `data/son/` | `m10_` |
| `ann` | año completo | `data/ann/` | `ann_` |

El valor de cada año no significa lo mismo para las dos variables:

- **Precipitación (`pr`):** es el **acumulado** del periodo, es decir, la lluvia total del
  trimestre o del año.
- **Temperatura (`tas`, `tasmax`, `tasmin`):** es el **promedio** del periodo, es decir, la
  temperatura media, máxima o mínima promedio del trimestre o del año.

El cálculo es el mismo en todos los casos. Para `pr` la señal (delta) y el residuo respecto al
polinomio se expresan en **porcentaje**; para `tas`, `tasmax` y `tasmin`, como **diferencia
absoluta** (°C). Así la señal y la variabilidad interna quedan en las mismas unidades y el TOE no
depende del valor absoluto de la temperatura. Un residuo en porcentaje no sirve para temperatura:
`tasmin` puede estar cerca o por debajo de 0 °C (Andes en invierno) y la división se dispara.

> **Nota:** hasta noviembre de 2026 el residuo de `tas` se calculaba en porcentaje. Los resultados
> de `tas` calculados antes de ese cambio no son comparables con los nuevos; recalcúlalos con
> `--force`.

### Periodo de los datos

Los años se leen de los archivos; no es necesario que lleguen a 2100. Al empezar,
`01_uncertainty.py` muestra el periodo común a todos los archivos y el periodo de los resultados:

```
Common period of all files: 1981-2064 (84 years)
Analysis period (results): 2020-2064 (45 years)
```

- **Periodo común:** va del año inicial más tardío al año final más temprano de todos los archivos.
  Todos los archivos se recortan a ese periodo antes del cálculo.
- **Modelos con otros años:** si algún archivo no tiene los mismos años que la mayoría, el script
  avisa cuáles son y los recorta al periodo común:
  ```
  WARNING: Most files have 1981-2067 (87 years), but these do not:
    -> m1_pr_GFDL-ESM4_ssp126.nc: 1981-2060 (80 years)
  All files will be cut to the common period 1981-2060.
  ```
- **Años faltantes:** si a un archivo le falta un año en medio de la serie, el script se detiene.
- **Periodo de referencia:** debe estar dentro del periodo común; si no, el script se detiene. Se
  cambia en `ref_ini, ref_end` al inicio de `01_uncertainty.py`.
- **Inicio de los resultados:** es 2020 (`fut_ini`) o, si los datos empiezan más tarde, el año
  inicial + 39. La variabilidad interna usa ventanas de 30 años y luego una media móvil de 10
  años, así que su primer valor aparece 39 años después del inicio. Los datos deben llegar al
  menos hasta ese año.

### Variabilidad interna: desviación estándar o varianza

La opción `--vi` de `00_procesa.sh` define cómo se mide la variabilidad interna (VI):

- `--vi=var` (por defecto): varianza de los residuos.
- `--vi=std`: desviación estándar de los residuos. Es el método anterior; se mantiene solo para
  comparar resultados.

Se recomienda `var` porque deja las unidades correctas en los dos usos de la VI:

| | `--vi=var` | `--vi=std` |
|---|---|---|
| Fracción de incertidumbre | VI, MU y SU son varianzas | Suma una desviación estándar con dos varianzas |
| TOE = señal / √VI | señal / desviación estándar | señal / √(desviación estándar), sin sentido físico |

Esto afecta la incertidumbre total, el TOE y el gráfico de fracciones. Los resultados y las figuras
llevan `_std` o `_var` al final del nombre, así que los dos cálculos pueden convivir en la misma
carpeta sin pisarse, y los títulos de las figuras indican cuál se usó (`VI: std` o `VI: var`).

Las figuras usan el periodo de los resultados en el título, en la barra de colores de los mapas y
en el eje horizontal del gráfico de fracciones.

### Método antiguo: `00_procesa_std.sh`

`00_procesa_std.sh` corre el mismo flujo con el método usado antes de octubre de 2026, para
reproducir y comparar resultados anteriores:

- variabilidad interna como **desviación estándar** (`--vi=std`);
- residuo de temperatura (`tas`, `tasmax`, `tasmin`) en **porcentaje** respecto al polinomio
  (`--resid=pct`). `pr` usa siempre el residuo en porcentaje.

```bash
bash 00_procesa_std.sh <variable>,<trimestre> [carpeta_entrada,carpeta_salida] [--force]
bash 00_procesa_std.sh tas,jja
```

Es lo mismo que `bash 00_procesa.sh <variable>,<trimestre> --vi=std --resid=pct`; el método queda
fijo y no acepta `--vi` ni `--resid`. Los resultados y figuras de temperatura terminan en
`_std_pct` y los de `pr` en `_std`, así que no pisan los de `00_procesa.sh`. Los títulos indican
`VI: std, residuo %`.

Este método da años de emergencia más tardíos para la temperatura (por ejemplo `tas` JJA, mediana
del dominio: +1 en 2048 y +2 en 2077, frente a 2020 y 2032 con el método actual), pero mezcla
unidades: la señal está en °C y el ruido en % de la temperatura, así que el TOE depende de cuán
cálido es el lugar. Donde la temperatura está cerca de 0 °C (Andes, sobre todo con `tasmin`) el
ruido se infla y la señal no emerge nunca. Se recomienda `00_procesa.sh`.

## Instalación

### 1. Instalar `uv` (solo una vez)

El entorno se crea con [uv](https://docs.astral.sh/uv/). Si no lo tienes:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Cierra y vuelve a abrir la terminal para que `uv` quede disponible.

### 2. Clonar el repositorio

```bash
git clone https://github.com/Japq91/uncert_cmip.git
cd uncert_cmip
```

### 3. Crear el entorno virtual

Hay dos scripts. Crean el mismo entorno (`.venv/` con Python 3.11 y los paquetes `numpy`,
`pandas<3`, `xarray`, `netCDF4`, `matplotlib` y `geopandas`); cambia solo cómo instalan los
paquetes:

| Script | Cuándo usarlo |
|---|---|
| `setup_env.sh` | **Por defecto.** Computadora o servidor con un sistema operativo actual. |
| `setup_env1.sh` | Solo si `setup_env.sh` falla en un servidor con un sistema operativo antiguo (por ejemplo CentOS 7). |

#### Opción normal: `setup_env.sh`

```bash
bash setup_env.sh
```

Opcionalmente puedes indicar otra carpeta y otra versión de Python:

```bash
bash setup_env.sh mi_entorno 3.12
```

#### Servidores con sistema antiguo: `setup_env1.sh`

**El problema:** cuando `uv` no encuentra un paquete precompilado compatible con el sistema,
intenta compilarlo desde el código fuente. En un servidor antiguo (glibc vieja) eso suele fallar
con `pyproj` (lo usa `geopandas`) o con `netCDF4`, porque necesitan librerías del sistema (PROJ,
HDF5) más nuevas que las instaladas. El error aparece mientras se instalan los paquetes y menciona
la compilación (*building*, *build failed*) de alguno de ellos.

**Qué hace distinto `setup_env1.sh`:**

1. Instala **solo paquetes precompilados** (`--only-binary :all:`) y nunca compila. `uv` elige
   las versiones más nuevas que tengan paquetes para ese sistema, aunque sean algo más antiguas.
2. Muestra el sistema y la **versión de glibc** al empezar, para diagnosticar problemas.
3. Al terminar, **comprueba que todos los paquetes se puedan importar** y muestra sus versiones.
4. Si no encuentra paquetes compatibles, se detiene y sugiere qué hacer (ver abajo).

Acepta los mismos argumentos que `setup_env.sh`. Si `setup_env.sh` ya creó un `.venv/` a medias,
bórralo antes:

```bash
rm -rf .venv
bash setup_env1.sh
bash setup_env1.sh mi_entorno 3.10   # otra carpeta y otra versión de Python
```

**Si `setup_env1.sh` también falla**, tienes dos alternativas:

- Probar con otra versión de Python: `rm -rf .venv && bash setup_env1.sh .venv 3.10`
- Crear el entorno con conda-forge, que trae sus propias librerías PROJ, GDAL y HDF5 y no depende
  de las del sistema:

  ```bash
  conda create -n uncert_cmip -c conda-forge python=3.11 numpy 'pandas<3' xarray netcdf4 matplotlib geopandas
  conda activate uncert_cmip
  ```

  En ese caso, en el paso 4 activa el entorno con `conda activate uncert_cmip` en vez de
  `source .venv/bin/activate`.

### 4. Activar el entorno

**Este paso es obligatorio antes de correr `00_procesa.sh`.** Hay que repetirlo cada vez que
abras una terminal nueva:

```bash
source .venv/bin/activate
```

Sabrás que está activo porque el prompt mostrará `(.venv)` al inicio. Para salir del entorno: `deactivate`.

## Uso

Con el entorno activado:

```bash
bash 00_procesa.sh <variable>,<trimestre> [carpeta_entrada,carpeta_salida] [--vi=std|var] [--resid=abs|pct] [--force]
```

| Argumento | Valores | Por defecto |
|---|---|---|
| `variable` | `pr` (precipitación), `tas` (temperatura media), `tasmax` (máxima) o `tasmin` (mínima) | obligatorio |
| `trimestre` | `djf`, `mam`, `jja`, `son` o `ann` (anual); ver [Trimestres y anual](#trimestres-y-anual) | obligatorio |
| `carpeta_entrada` | carpeta con una subcarpeta por trimestre (`djf/`, `jja/`, `ann/`, ...) | `data` |
| `carpeta_salida` | carpeta para los `.nc` de resultados | `out` |
| `--vi` | variabilidad interna como varianza (`var`) o desviación estándar (`std`); ver [más abajo](#variabilidad-interna-desviación-estándar-o-varianza) | `var` |
| `--resid` | residuo de temperatura en grados (`abs`) o en porcentaje (`pct`, método antiguo; ver [`00_procesa_std.sh`](#método-antiguo-00_procesa_stdsh)). No afecta a `pr` | `abs` |
| `--force` | recalcula aunque los `.nc` de resultados ya existan | desactivado |

Las opciones `--vi`, `--resid` y `--force` pueden ir en cualquier posición.

Las figuras se guardan siempre en `figures/`. Los valores van separados por comas y **sin espacios**
(`pr,djf`, no `pr, djf`).

Ejemplos:

```bash
# Carpetas por defecto (data y out)
bash 00_procesa.sh pr,djf

# Con carpetas propias
bash 00_procesa.sh pr,djf data,resultados

# Solo cambiar la carpeta de entrada, o solo la de salida
bash 00_procesa.sh pr,djf datos
bash 00_procesa.sh pr,djf ,resultados

# Datos anuales (data/ann/)
bash 00_procesa.sh pr,ann

# Recalcular aunque ya existan resultados
bash 00_procesa.sh tas,jja data,out --force

# Variabilidad interna con el método anterior (desviación estándar), para comparar
bash 00_procesa.sh pr,djf --vi=std
```

Para procesar todas las combinaciones de variable y trimestre:

```bash
for v in pr tas tasmax tasmin; do for t in djf jja; do bash 00_procesa.sh $v,$t; done; done
```

Antes de correr, el script revisa los argumentos y se detiene con un mensaje si la variable o el
trimestre no son válidos, si el formato no es el esperado (por ejemplo `pr djf` en vez de `pr,djf`),
si la carpeta de entrada (o su subcarpeta del trimestre) no existe o no tiene archivos, si alguna
carpeta de salida es en realidad un archivo, o si se escribe mal una opción (por ejemplo `--forse`).
Las carpetas de salida se crean si no existen.

### Cómo se conectan las carpetas

`00_procesa.sh` pasa la misma carpeta de salida a `01_uncertainty.py` y `02_grafica.py`:
`01_uncertainty.py` guarda ahí los `.nc` y `02_grafica.py` los lee desde ahí.
`03_series_modelos.py` usa la misma carpeta de entrada que `01_uncertainty.py`. Por ejemplo, con
`bash 00_procesa.sh pr,djf datos,resultados`:

| Script | Lee de | Guarda en |
|---|---|---|
| `01_uncertainty.py` | `datos/djf/` | `resultados/` |
| `02_grafica.py` | `resultados/` | `figures/` |
| `03_series_modelos.py` | `datos/djf/` | `figures/` |

### Correr los scripts por separado

También se pueden correr sin `00_procesa.sh`. En ese caso las carpetas se pasan como argumentos 3
y 4; si no se pasan, se usan los valores de `idir` y `odir` al inicio de cada script:

```bash
python 01_uncertainty.py <variable> <trimestre> [carpeta_entrada] [carpeta_salida] [--vi=std|var] [--resid=abs|pct] [--force]
python 02_grafica.py     <variable> <trimestre> [carpeta_resultados] [carpeta_figuras] [--vi=std|var] [--resid=abs|pct]
```

Por ejemplo:

```bash
python 01_uncertainty.py pr djf datos resultados
python 02_grafica.py pr djf resultados figures
```

Si `01_uncertainty.py` guardó en otra carpeta que `out/`, hay que indicársela a `02_grafica.py`;
si no, la buscará en `out/` y avisará que no encuentra los archivos. Lo mismo con `--vi` y
`--resid`: `02_grafica.py` debe recibir los mismos valores que `01_uncertainty.py` para encontrar
los archivos. Al correrlos por separado no se hacen las validaciones de `00_procesa.sh`.

### Notebook `Clase.ipynb`

Hace el mismo cálculo que `01_uncertainty.py` y `02_grafica.py`, paso a paso, para la clase. Las
opciones van en la primera celda de código:

| Variable | Valores | Equivale a |
|---|---|---|
| `var`, `tri` | igual que en los scripts | `<variable>,<trimestre>` |
| `idir`, `odir`, `fdir` | carpetas de datos, resultados y figuras | `carpeta_entrada,carpeta_salida` y `figures/` |
| `vi_stat` | `'var'` (recomendado) o `'std'` | `--vi` |
| `resid` | `'abs'` (recomendado) o `'pct'` | `--resid` |

Con `vi_stat = 'std'` y `resid = 'pct'` reproduce `00_procesa_std.sh`. Los resultados, las figuras
y sus nombres son los mismos que los de los scripts, así que el notebook puede leer o pisar
archivos hechos por ellos.

### Series de tiempo de los modelos

`03_series_modelos.py` grafica los datos de entrada (no los resultados): la serie de tiempo de
cada modelo, promediada en toda la región (lat y lon, ponderado por cos(lat)). Hace una figura
por escenario; todas usan el mismo eje Y y el mismo color para cada modelo, para poder
compararlas. `00_procesa.sh` lo corre como tercer paso, con la misma carpeta de entrada; no
depende de los resultados de `01_uncertainty.py`, así que también se puede correr solo:

```bash
python 03_series_modelos.py <variable> <trimestre> [carpeta_entrada] [carpeta_figuras]
python 03_series_modelos.py pr djf                # data/djf -> figures/
python 03_series_modelos.py tas jja datos figures # datos/jja -> figures/
```

Las figuras se llaman `Series_<carpeta>_<var>_<tri>_ssp<XXX>.png`, donde `<carpeta>` es el nombre
de la carpeta de entrada (`data`, `datos`, ...), para distinguir figuras de datos distintos. La
leyenda usa el nombre del modelo que está entre `_` en el nombre del archivo
(`m1_pr_ACCESS-CM2_ssp126.nc` -> `ACCESS-CM2`).

### Archivos ya calculados

Si los 4 `.nc` de una combinación ya existen en la carpeta de salida, `01_uncertainty.py` omite el
cálculo y pasa directo a las gráficas. Para recalcular, usa `--force` o borra esos archivos. Las
figuras se vuelven a generar siempre (tardan pocos segundos).

## Resultados

**`out/`** (NetCDF):

- `toe_<var>_<per>_<vi>.nc` — Time of Emergence
- `Tmu_<var>_<per>_<vi>.nc` — incertidumbre por modelos (MU)
- `Tsu_<var>_<per>_<vi>.nc` — incertidumbre por escenarios (SU)
- `Tvi_<var>_<per>_<vi>.nc` — variabilidad interna (VI)

`<vi>` es `std` o `var` según la opción `--vi`; para temperatura con `--resid=pct` (o
`00_procesa_std.sh`) se agrega `_pct` (`std_pct`, `var_pct`). `<per>` es el prefijo del trimestre: `m1` (djf), `m4` (mam), `m7` (jja), `m10` (son) o `ann` (anual).

**`figures/`** (PNG):

- Mapas del TOE (año en que la señal emerge), dos para `pr` y tres para temperatura:

  | Variable | Archivo | Umbral | Significado |
  |---|---|---|---|
  | `pr` | `TOE_pr_<tri>_umbral_positivo_<vi>.png` | +1 | La precipitación **aumenta** por encima del ruido |
  | `pr` | `TOE_pr_<tri>_umbral_negativo_<vi>.png` | −1 | La precipitación **disminuye** por debajo del ruido |
  | `tas`, `tasmax`, `tasmin` | `TOE_<var>_<tri>_umbral_bajo_<vi>.png` | +1 | Calentamiento de 1 vez el ruido |
  | `tas`, `tasmax`, `tasmin` | `TOE_<var>_<tri>_umbral_alto_<vi>.png` | +2 | Calentamiento de 2 veces el ruido |
  | `tas`, `tasmax`, `tasmin` | `TOE_<var>_<tri>_umbral_muy_alto_<vi>.png` | +3 | Calentamiento de 3 veces el ruido |

  Los umbrales son una relación señal/ruido (`TOE = señal / √VI`), no grados ni porcentajes:
  +2 para `tas` (o `tasmax`, `tasmin`) significa dos desviaciones estándar de la variabilidad interna, no +2 °C.
  En los trópicos la temperatura emerge pronto (la variabilidad interanual es pequeña), así que el
  umbral +1 suele marcar el primer año de los resultados en casi todo el mapa; el +3 da más
  contraste entre regiones. Un píxel con el primer año (por ejemplo 2020) significa "ese año o
  antes": la señal ya emergió al inicio del periodo de resultados.

  **Escala de colores:** discreta, de 21 colores, abierta en las dos puntas (triángulos en la barra).
  Cada color agrupa varios años: con resultados 2020-2100 son 4 años por color, con bordes en
  2024, 2028, ..., 2100. El periodo se reparte igual si es más corto (por ejemplo 2020-2064 da 2
  años por color).

  | Parte de la barra | Significado (resultados 2020-2100) |
  |---|---|
  | Triángulo inferior | Emerge antes de 2024, incluido "ya emergió en 2020 o antes" |
  | Colores intermedios (19) | Emerge en ese bloque de 4 años, por ejemplo 2024-2027 |
  | Triángulo superior | Emerge en 2100 |
  | Blanco | No emerge dentro del periodo de resultados |

  El número de colores se cambia en `n_colores` en `02_grafica.py` (y en el notebook).
- `Fraccion_incertidumbre_peru_<var>_<tri>_interpol_<vi>.png` — fracción de cada fuente de
  incertidumbre en el periodo de los resultados, promediada en el sur de Perú
  (17°S–12°S, 75°W–70°W)
- `Series_<carpeta>_<var>_<tri>_ssp<XXX>.png` — serie de tiempo de cada modelo, una figura por
  escenario (ver [Series de tiempo de los modelos](#series-de-tiempo-de-los-modelos))

Si pasas otra carpeta de salida como argumento, los `.nc` se guardan ahí en vez de `out/`; las
figuras van siempre a `figures/`. Los valores por defecto están en las variables `idir` y `odir`
al inicio de cada script `.py`.
