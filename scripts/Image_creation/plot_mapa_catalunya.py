import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Patch
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CSV = ROOT_DIR / "data" / "raw" / "migration" / "saldo_extern_comarques.csv"

# Períodes sense solapament; el 2021 és una ruptura de font de l'INE
PERIODES = [
    ("2002–2008", 2002, 2008),
    ("2009–2014", 2009, 2014),
    ("2015–2020", 2015, 2020),
    ("2021–2022", 2021, 2022),
]

df = pd.read_csv(CSV)
df["Codi"] = df["Codi"].astype(str).str.zfill(2)


def taxa(ini, fi):
    """Taxa del període = suma de saldos / suma de població-any, per 1.000."""
    s = df[df["Any"].between(ini, fi)].groupby("Codi")[["Saldo_ext", "Poblacio"]].sum()
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

for titol, ini, fi in PERIODES:
    gdf[titol] = gdf["Codi"].map(taxa(ini, fi))

gdf = gdf.to_crs(epsg=25831)

# Escala única, simètrica al voltant de 0 i retallada al percentil 95
cols = [p[0] for p in PERIODES]
lim = np.nanpercentile(np.abs(gdf[cols].to_numpy(float)), 95)
norm = Normalize(vmin=-lim, vmax=lim)
cmap = "RdBu"

# Figura
fig, axes = plt.subplots(2, 2, figsize=(11, 10.5), layout="constrained")
fig.get_layout_engine().set(wspace=0.01, hspace=0.04)

for ax, (titol, ini, fi) in zip(axes.flat, PERIODES):
    gdf.plot(
        column=titol, cmap=cmap, norm=norm,
        linewidth=0.4, edgecolor="0.35",
        missing_kwds={"color": "lightgrey", "edgecolor": "0.5", "hatch": "///"},
        ax=ax,
    )
    ax.set_title(titol, fontsize=14, fontweight="bold")
    ax.set_axis_off()

axes[1, 1].legend(
    handles=[Patch(facecolor="lightgrey", edgecolor="0.5", hatch="///",
                   label="No data")],
    loc="lower right", frameon=False, fontsize=9,
)

sm = ScalarMappable(norm=norm, cmap=cmap)
fig.colorbar(sm, ax=axes, shrink=0.6, extend="both",
             label="People per 1.000 inhabitants per year")

fig.suptitle("Net external migration by comarca (annual average)",
             fontsize=17, fontweight="bold")

ruta_figura = ROOT_DIR / "results" / "figures" / "mapa_saldo_extern_4periodes.png"
ruta_figura.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(ruta_figura, dpi=300, bbox_inches="tight")
plt.show()