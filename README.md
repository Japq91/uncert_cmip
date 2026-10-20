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
`netCDF4`, `scipy`, `matplotlib` y `geopandas`.

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
bash 00_procesa.sh <variable> <trimestre>
```

| Argumento | Valores |
|---|---|
| `variable` | `pr` (precipitación) o `tas` (temperatura) |
| `trimestre` | `djf` (dic-ene-feb) o `jja` (jun-jul-ago) |

Ejemplos:

```bash
bash 00_procesa.sh tas jja
bash 00_procesa.sh pr djf
```

Para procesar las cuatro combinaciones:

```bash
for v in pr tas; do for t in djf jja; do bash 00_procesa.sh $v $t; done; done
```

Si los archivos de `out/` ya existen, `01_uncertainty.py` omite el cálculo y pasa directo a las gráficas.
Para recalcular, borra los archivos correspondientes en `out/`.

## Resultados

**`out/`** (NetCDF):

- `toe_<var>_<per>.nc` — Time of Emergence
- `Tmu_<var>_<per>.nc` — fracción de incertidumbre por modelos
- `Tsu_<var>_<per>.nc` — fracción de incertidumbre por escenarios
- `Tvi_<var>_<per>.nc` — fracción de incertidumbre por variabilidad interna

**`figures/`** (PNG):

- `TOE_<var>_<tri>_umbral_alto.png` y `TOE_<var>_<tri>_umbral_bajo.png` — mapas del TOE
- `Fraccion_incertidumbre_peru_<var>_<tri>_interpol.png` — fracción de cada fuente de
  incertidumbre (2020–2100) promediada en el sur de Perú (17°S–12°S, 75°W–70°W)

Las carpetas de entrada y salida se pueden cambiar en las variables `idir` y `odir` al
inicio de cada script `.py`.
