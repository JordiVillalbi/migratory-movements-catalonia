
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path

# --------------------------------------------------
# 1. CARREGAR DADES DE MIGRACIONS
# --------------------------------------------------

df = pd.read_csv(
    "data/raw/migration/migracions_totes_comarques.csv"
)

# Netejar noms de columnes
df.columns = df.columns.str.strip()

# Preparar codi de comarca per fer el join
df["Codi"] = df["Codi"].astype(str).str.zfill(2)

# Variable que volem representar
variable = "Saldo migratori total"

df[variable] = pd.to_numeric(
    df[variable], errors="coerce"
)

# --------------------------------------------------
# 2. DESCARREGAR LÍMITS GEOGRÀFICS
# --------------------------------------------------

url = (
    "https://services.arcgis.com/fwF8e4aLR6TRWtqM/"
    "arcgis/rest/services/comarques_catalunya_etiquetes/"
    "FeatureServer/0/query?"
    "where=1%3D1&outFields=CODICOMAR,NOMCOMAR"
    "&returnGeometry=true&outSR=4326&f=geojson"
)

gdf = gpd.read_file(url)

print("Columnes del mapa:", gdf.columns.tolist())
print("Nombre de geometries:", len(gdf))

# --------------------------------------------------
# 3. UNIR MAPA I DADES
# --------------------------------------------------

gdf["CODICOMAR"] = (
    gdf["CODICOMAR"].astype(str).str.zfill(2)
)

gdf = gdf.merge(
    df[["Codi", "Nom", variable]],
    left_on="CODICOMAR",
    right_on="Codi",
    how="left"
)

# Comprovar si totes les comarques tenen dades
print("\nComarques sense dades:")
print(gdf[gdf[variable].isna()][["CODICOMAR", "NOMCOMAR"]])

# Projectar a coordenades UTM
gdf = gdf.to_crs(epsg=25831)

# --------------------------------------------------
# 4. REPRESENTAR EL MAPA
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(11, 10))

# Escala de colors centrada en zero
vmax = gdf[variable].abs().max()

norm = TwoSlopeNorm(
    vmin=-vmax,
    vcenter=0,
    vmax=vmax
)

gdf.plot(
    column=variable,
    cmap="RdYlGn",
    norm=norm,
    linewidth=0.6,
    edgecolor="white",
    legend=True,
    legend_kwds={
        "label": "Saldo migratori (persones)",
        "shrink": 0.65
    },
    missing_kwds={
        "color": "lightgrey",
        "label": "Sense dades"
    },
    ax=ax
)

# Títol
ax.set_title(
    "Saldo migratori total per comarca",
    fontsize=17,
    fontweight="bold",
    pad=20
)

ax.set_axis_off()

plt.tight_layout()

# Guardar gràfic
Path("figures").mkdir(exist_ok=True)

plt.savefig(
    "figures/mapa_saldo_migratori.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
