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
Para usar los trimestres `mam` o `son`, crea `data/mam/` (archivos `m4_...`) o `data/son/`
(archivos `m10_...`) con el mismo formato.

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
bash 00_procesa.sh <variable>,<trimestre> [carpeta_entrada,carpeta_salida] [--force]
```

| Argumento | Valores | Por defecto |
|---|---|---|
| `variable` | `pr` (precipitación) o `tas` (temperatura) | obligatorio |
| `trimestre` | `djf` (dic-ene-feb), `mam` (mar-abr-may), `jja` (jun-jul-ago) o `son` (sep-oct-nov) | obligatorio |
| `carpeta_entrada` | carpeta con una subcarpeta por trimestre (`djf/`, `jja/`, ...) | `data` |
| `carpeta_salida` | carpeta para los `.nc` de resultados | `out` |
| `--force` | recalcula aunque los `.nc` de resultados ya existan (puede ir en cualquier posición) | desactivado |

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

# Recalcular aunque ya existan resultados
bash 00_procesa.sh tas,jja data,out --force
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
python 01_uncertainty.py <variable> <trimestre> [carpeta_entrada] [carpeta_salida] [--force]
python 02_grafica.py     <variable> <trimestre> [carpeta_resultados] [carpeta_figuras]
```

Por ejemplo:

```bash
python 01_uncertainty.py pr djf datos resultados
python 02_grafica.py pr djf resultados figures
```

Si `01_uncertainty.py` guardó en otra carpeta que `out/`, hay que indicársela a `02_grafica.py`;
si no, la buscará en `out/` y avisará que no encuentra los archivos. Al correrlos por separado no
se hacen las validaciones de `00_procesa.sh`.

### Archivos ya calculados

Si los 4 `.nc` de una combinación ya existen en la carpeta de salida, `01_uncertainty.py` omite el
cálculo y pasa directo a las gráficas. Para recalcular, usa `--force` o borra esos archivos. Las
figuras se vuelven a generar siempre (tardan pocos segundos).

## Resultados

**`out/`** (NetCDF):

- `toe_<var>_<per>.nc` — Time of Emergence
- `Tmu_<var>_<per>.nc` — incertidumbre por modelos (MU)
- `Tsu_<var>_<per>.nc` — incertidumbre por escenarios (SU)
- `Tvi_<var>_<per>.nc` — variabilidad interna (VI)

`<per>` es el prefijo del trimestre: `m1` (djf), `m4` (mam), `m7` (jja) o `m10` (son).

**`figures/`** (PNG):

- `TOE_<var>_<tri>_umbral_alto.png` y `TOE_<var>_<tri>_umbral_bajo.png` — mapas del TOE
- `Fraccion_incertidumbre_peru_<var>_<tri>_interpol.png` — fracción de cada fuente de
  incertidumbre en el periodo de los resultados, promediada en el sur de Perú
  (17°S–12°S, 75°W–70°W)

Si pasas otra carpeta de salida como argumento, los `.nc` se guardan ahí en vez de `out/`; las
figuras van siempre a `figures/`. Los valores por defecto están en las variables `idir` y `odir`
al inicio de cada script `.py`.
