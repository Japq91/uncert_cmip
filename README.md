# uncert_cmip

Descomposición de la incertidumbre en las proyecciones climáticas CMIP6 y cálculo del
**Time of Emergence (TOE)** para precipitación (`pr`) y temperatura (`tas`) sobre Sudamérica,
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
├── 00_procesa.sh       # Ejecuta el flujo completo (01 + 02)
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
- **Temperatura (`tas`):** es el **promedio** del periodo, es decir, la temperatura media del
  trimestre o del año.

El cálculo es el mismo en todos los casos. Para `pr` los cambios se expresan en **porcentaje**
respecto al periodo de referencia, y para `tas` como **diferencia absoluta** (°C).

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

```bash
bash setup_env.sh
```

Esto crea la carpeta `.venv/` con Python 3.11 e instala `numpy`, `pandas<3`, `xarray`,
`netCDF4`, `matplotlib` y `geopandas`.

Opcionalmente puedes indicar otra carpeta y otra versión de Python:

```bash
bash setup_env.sh mi_entorno 3.12
```

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
bash 00_procesa.sh <variable>,<trimestre> [carpeta_entrada,carpeta_salida] [--vi=std|var] [--force]
```

| Argumento | Valores | Por defecto |
|---|---|---|
| `variable` | `pr` (precipitación) o `tas` (temperatura) | obligatorio |
| `trimestre` | `djf`, `mam`, `jja`, `son` o `ann` (anual); ver [Trimestres y anual](#trimestres-y-anual) | obligatorio |
| `carpeta_entrada` | carpeta con una subcarpeta por trimestre (`djf/`, `jja/`, `ann/`, ...) | `data` |
| `carpeta_salida` | carpeta para los `.nc` de resultados | `out` |
| `--vi` | variabilidad interna como varianza (`var`) o desviación estándar (`std`); ver [más abajo](#variabilidad-interna-desviación-estándar-o-varianza) | `var` |
| `--force` | recalcula aunque los `.nc` de resultados ya existan | desactivado |

Las opciones `--vi` y `--force` pueden ir en cualquier posición.

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

Para procesar las cuatro combinaciones:

```bash
for v in pr tas; do for t in djf jja; do bash 00_procesa.sh $v,$t; done; done
```

Antes de correr, el script revisa los argumentos y se detiene con un mensaje si la variable o el
trimestre no son válidos, si el formato no es el esperado (por ejemplo `pr djf` en vez de `pr,djf`),
si la carpeta de entrada (o su subcarpeta del trimestre) no existe o no tiene archivos, si alguna
carpeta de salida es en realidad un archivo, o si se escribe mal una opción (por ejemplo `--forse`).
Las carpetas de salida se crean si no existen.

### Cómo se conectan las carpetas

`00_procesa.sh` pasa la misma carpeta de salida a los dos scripts: `01_uncertainty.py` guarda ahí
los `.nc` y `02_grafica.py` los lee desde ahí. Por ejemplo, con
`bash 00_procesa.sh pr,djf datos,resultados`:

| Script | Lee de | Guarda en |
|---|---|---|
| `01_uncertainty.py` | `datos/djf/` | `resultados/` |
| `02_grafica.py` | `resultados/` | `figures/` |

### Correr los scripts por separado

También se pueden correr sin `00_procesa.sh`. En ese caso las carpetas se pasan como argumentos 3
y 4; si no se pasan, se usan los valores de `idir` y `odir` al inicio de cada script:

```bash
python 01_uncertainty.py <variable> <trimestre> [carpeta_entrada] [carpeta_salida] [--vi=std|var] [--force]
python 02_grafica.py     <variable> <trimestre> [carpeta_resultados] [carpeta_figuras] [--vi=std|var]
```

Por ejemplo:

```bash
python 01_uncertainty.py pr djf datos resultados
python 02_grafica.py pr djf resultados figures
```

Si `01_uncertainty.py` guardó en otra carpeta que `out/`, hay que indicársela a `02_grafica.py`;
si no, la buscará en `out/` y avisará que no encuentra los archivos. Al correrlos por separado no
se hacen las validaciones de `00_procesa.sh`.

### Series de tiempo de los modelos

`03_series_modelos.py` grafica los datos de entrada (no los resultados): la serie de tiempo de
cada modelo, promediada en toda la región (lat y lon, ponderado por cos(lat)). Hace una figura
por escenario; todas usan el mismo eje Y y el mismo color para cada modelo, para poder
compararlas. No depende de `01_uncertainty.py` y no se corre desde `00_procesa.sh`.

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

`<vi>` es `std` o `var` según la opción `--vi`. `<per>` es el prefijo del trimestre: `m1` (djf), `m4` (mam), `m7` (jja), `m10` (son) o `ann` (anual).

**`figures/`** (PNG):

- Mapas del TOE (año en que la señal emerge), dos por variable:

  | Variable | Archivo | Umbral | Significado |
  |---|---|---|---|
  | `pr` | `TOE_pr_<tri>_umbral_positivo_<vi>.png` | +1 | La precipitación **aumenta** por encima del ruido |
  | `pr` | `TOE_pr_<tri>_umbral_negativo_<vi>.png` | −1 | La precipitación **disminuye** por debajo del ruido |
  | `tas` | `TOE_tas_<tri>_umbral_alto_<vi>.png` | +2 | Calentamiento de 2 veces el ruido |
  | `tas` | `TOE_tas_<tri>_umbral_bajo_<vi>.png` | +1 | Calentamiento de 1 vez el ruido |

  Los umbrales son una relación señal/ruido (`TOE = señal / √VI`), no grados ni porcentajes:
  +2 para `tas` significa dos desviaciones estándar de la variabilidad interna, no +2 °C.
- `Fraccion_incertidumbre_peru_<var>_<tri>_interpol_<vi>.png` — fracción de cada fuente de
  incertidumbre en el periodo de los resultados, promediada en el sur de Perú
  (17°S–12°S, 75°W–70°W)

Si pasas otra carpeta de salida como argumento, los `.nc` se guardan ahí en vez de `out/`; las
figuras van siempre a `figures/`. Los valores por defecto están en las variables `idir` y `odir`
al inicio de cada script `.py`.
