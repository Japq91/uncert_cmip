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

Las anomalías se calculan respecto al periodo de referencia **1981–2010**.

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
  incertidumbre (2020–2100) promediada en el sur de Perú (17°S–12°S, 75°W–70°W)

Si pasas otra carpeta de salida como argumento, los `.nc` se guardan ahí en vez de `out/`; las
figuras van siempre a `figures/`. Los valores por defecto están en las variables `idir` y `odir`
al inicio de cada script `.py`.
