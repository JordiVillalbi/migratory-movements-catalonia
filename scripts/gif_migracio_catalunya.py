import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Patch
from pathlib import Path
from matplotlib.animation import FuncAnimation, PillowWriter

CSV = "data/raw/migration/saldo_extern_comarques.csv"

df = pd.read_csv(CSV)
df["Codi"] = df["Codi"].astype(str).str.zfill(2)


def taxa_anual(any):
    """Taxa anual de saldo migratori per 1.000 habitants."""
    s = df[df["Any"] == any].groupby("Codi")[
        ["Saldo_ext", "Poblacio"]
    ].sum()

    return s["Saldo_ext"] / s["Poblacio"] * 1000


url = (
    "https://services.arcgis.com/fwF8e4aLR6TRWtqM/"
    "arcgis/rest/services/comarques_catalunya_etiquetes/"
    "FeatureServer/0/query?"
    "where=1%3D1&outFields=CODICOMAR,NOMCOMAR"
    "&returnGeometry=true&outSR=4326&f=geojson"
)

gdf = gpd.read_file(url)
gdf["Codi"] = gdf["CODICOMAR"].astype(str).str.zfill(2)

ANYS = list(range(2002, 2023))

for any in ANYS:
    gdf[str(any)] = gdf["Codi"].map(taxa_anual(any))

gdf = gdf.to_crs(epsg=25831)

# Escala comuna
cols = [str(any) for any in ANYS]

lim = np.nanpercentile(
    np.abs(gdf[cols].to_numpy(float)), 95
)

norm = Normalize(vmin=-lim, vmax=lim)
cmap = "RdBu"

print(gdf[["NOMCOMAR"] + cols].head())
print("Límit de l'escala:", lim)


# Figura i eixos
fig, ax = plt.subplots(figsize=(8, 9), layout="constrained")

# Barra de colors fixa
sm = ScalarMappable(norm=norm, cmap=cmap)

fig.colorbar(
    sm,
    ax=ax,
    shrink=0.65,
    extend="both",
    label="Net external migration per 1,000 inhabitants"
)

# Funció que actualitza el mapa
def actualitzar(i):
    ax.clear()

    any_actual = ANYS[i]

    gdf.plot(
        column=str(any_actual),
        cmap=cmap,
        norm=norm,
        linewidth=0.4,
        edgecolor="0.35",
        missing_kwds={
            "color": "lightgrey",
            "edgecolor": "0.5",
            "hatch": "///"
        },
        ax=ax
    )

    ax.set_title(
        str(any_actual),
        fontsize=24,
        fontweight="bold",
        pad=12
    )

    ax.set_axis_off()

    return ax,

# Crear animació
ani = FuncAnimation(
    fig,
    actualitzar,
    frames=len(ANYS),
    interval=1000,
    repeat=True
)

# Guardar GIF
ani.save(
    "results/figures/mapa_saldo_extern_anual.gif",
    writer=PillowWriter(fps=1),
    dpi=150
)

plt.show()
