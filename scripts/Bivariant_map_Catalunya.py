import io
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from PIL import Image

# ==================================================
# CONFIGURACIÓ
# ==================================================

CSV_MIGRACIO = "data/raw/migration/saldo_extern_comarques.csv"
CSV_ATUR = "data/processed/social/atur_comarques.csv"

OUTPUT_GIF = "results/figures/mapa_bivariant_migracio_atur.gif"

# True  -> els talls dels tercils es calculen amb TOTS els anys junts, de manera que
#          els colors són comparables entre fotogrames (recomanat per a un GIF).
# False -> els tercils es recalculen cada any (només mostra la posició relativa de l'any).
TERCILS_GLOBALS = True

MS_PER_FRAME = 1200       # durada de cada any en mil·lisegons
MS_ULTIM_FRAME = 3000     # pausa més llarga a l'últim any
DPI = 100

# ==================================================
# FUNCIONS AUXILIARS
# ==================================================


def normalitza_nom(nom):
    """Normalitza noms de comarca per poder-los creuar (accents, majúscules, apòstrofs)."""
    nom = unicodedata.normalize("NFKD", str(nom))
    nom = "".join(c for c in nom if not unicodedata.combining(c))
    nom = nom.lower().strip().replace("'", "").replace("’", "")
    if nom in ("val daran", "vall daran"):
        nom = "aran"
    return nom


def classificar(s, talls):
    """0 = Baix, 1 = Mitjà, 2 = Alt, segons els talls (q1, q2). NaN es manté NaN."""
    q1, q2 = talls
    res = pd.Series(np.nan, index=s.index)
    valid = s.notna()
    res.loc[valid] = np.select([s[valid] <= q1, s[valid] <= q2], [0, 1], default=2)
    return res


# ==================================================
# 1. LLEGIR DADES
# ==================================================

df_mig = pd.read_csv(CSV_MIGRACIO)
df_atur = pd.read_csv(CSV_ATUR, encoding="utf-8-sig")

df_mig.columns = df_mig.columns.str.strip()
df_atur.columns = df_atur.columns.str.strip()

df_mig["Codi"] = (
    df_mig["Codi"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
)

# ==================================================
# 2. GEOMETRIES DE LES COMARQUES (es descarreguen un sol cop)
# ==================================================

url = (
    "https://services.arcgis.com/fwF8e4aLR6TRWtqM/"
    "arcgis/rest/services/comarques_catalunya_etiquetes/"
    "FeatureServer/0/query?"
    "where=1%3D1&outFields=CODICOMAR,NOMCOMAR"
    "&returnGeometry=true&outSR=4326&f=geojson"
)

gdf = gpd.read_file(url)
gdf["Codi"] = gdf["CODICOMAR"].astype(str).str.zfill(2)
gdf["clau"] = gdf["NOMCOMAR"].map(normalitza_nom)
gdf = gdf.to_crs(epsg=25831)

# ==================================================
# 3. PANEL COMARCA x ANY AMB LES DUES VARIABLES
# ==================================================

# Migració externa per 1.000 habitants
mig_all = (
    df_mig.groupby(["Any", "Codi"])[["Saldo_ext", "Poblacio"]].sum().reset_index()
)
mig_all = mig_all.rename(columns={"Any": "any"})
mig_all["any"] = mig_all["any"].astype(int)
mig_all["migracio"] = mig_all["Saldo_ext"] / mig_all["Poblacio"] * 1000

# Atur: el CSV només porta el nom de la comarca, el creuem amb el codi via el mapa
clau_a_codi = gdf.set_index("clau")["Codi"]
atur_df = df_atur.copy()
atur_df["clau"] = atur_df["comarca"].map(normalitza_nom)
atur_df["Codi"] = atur_df["clau"].map(clau_a_codi)

sense_parella = atur_df.loc[atur_df["Codi"].isna(), "comarca"].unique()
if len(sense_parella):
    print("AVÍS: comarques de l'atur que no coincideixen amb el mapa:", list(sense_parella))

atur_df = atur_df.dropna(subset=["Codi"])
atur_df["any"] = atur_df["any"].astype(int)

# Només els anys i comarques on hi ha dades de les dues fonts
panel = mig_all.merge(atur_df[["Codi", "any", "total"]], on=["Codi", "any"], how="inner")
panel["atur_1000"] = panel["total"] / panel["Poblacio"] * 1000

anys = sorted(panel["any"].unique())
print(f"Anys amb dades de les dues fonts: {anys[0]}–{anys[-1]} ({len(anys)} anys)")
print("Anys de migració:", sorted(mig_all["any"].unique()))
print("Anys d'atur:", sorted(atur_df["any"].unique()))

# ==================================================
# 4. TALLS DELS TERCILS
# ==================================================

if TERCILS_GLOBALS:
    TALLS_MIG = tuple(panel["migracio"].quantile([1 / 3, 2 / 3]).values)
    TALLS_ATU = tuple(panel["atur_1000"].quantile([1 / 3, 2 / 3]).values)

# ==================================================
# 5. PALETA BIVARIANT
# ==================================================

# Files: atur (baix -> alt) ; Columnes: migració (baix -> alt)
colors = [
    ["#e8e8e8", "#ace4e4", "#5ac8c8"],
    ["#e4acac", "#a5add3", "#5698b9"],
    ["#c85a5a", "#b66a9c", "#3b4994"],
]

cmap_bivariant = ListedColormap([
    colors[2][0], colors[2][1], colors[2][2],
    colors[1][0], colors[1][1], colors[1][2],
    colors[0][0], colors[0][1], colors[0][2],
])

# ==================================================
# 6. DIBUIXAR UN FOTOGRAMA
# ==================================================


def dibuixa_any(any_):
    d = panel[panel["any"] == any_].set_index("Codi")

    g = gdf.copy()
    g["migracio"] = g["Codi"].map(d["migracio"])
    g["atur_1000"] = g["Codi"].map(d["atur_1000"])

    if TERCILS_GLOBALS:
        c_mig, c_atu = TALLS_MIG, TALLS_ATU
    else:
        c_mig = tuple(g["migracio"].quantile([1 / 3, 2 / 3]).values)
        c_atu = tuple(g["atur_1000"].quantile([1 / 3, 2 / 3]).values)

    g["mig_cat"] = classificar(g["migracio"], c_mig)
    g["atur_cat"] = classificar(g["atur_1000"], c_atu)

    g["color"] = [
        colors[int(y)][int(x)] if pd.notna(x) and pd.notna(y) else "#d3d3d3"
        for x, y in zip(g["mig_cat"], g["atur_cat"])
    ]

    fig, (ax, lax) = plt.subplots(
        1, 2, figsize=(12, 9), gridspec_kw={"width_ratios": [4, 1.3]}
    )

    g.plot(color=g["color"], edgecolor="white", linewidth=0.6, ax=ax)

    ax.set_title(
        f"External migration and registered unemployment\nby comarca, Catalonia ({any_})",
        fontsize=16,
        fontweight="bold",
        pad=15,
    )
    ax.set_axis_off()
    ax.legend(
        handles=[Patch(facecolor="#d3d3d3", edgecolor="white", label="No data")],
        loc="lower right",
        frameon=False,
        fontsize=10,
    )

    # Llegenda 3x3
    lax.imshow(
        np.arange(9).reshape(3, 3),
        cmap=cmap_bivariant,
        interpolation="nearest",
        vmin=0,
        vmax=8,
    )
    lax.set_xticks([0, 1, 2])
    lax.set_yticks([0, 1, 2])
    lax.set_xticklabels([
        f"Low\n(< {c_mig[0]:.1f})",
        f"Medium\n({c_mig[0]:.1f}–{c_mig[1]:.1f})",
        f"High\n(> {c_mig[1]:.1f})",
    ], fontsize=9)
    lax.set_yticklabels([
        f"High\n(> {c_atu[1]:.0f})",
        f"Medium\n({c_atu[0]:.0f}–{c_atu[1]:.0f})",
        f"Low\n(< {c_atu[0]:.0f})",
    ], fontsize=9)
    lax.set_xlabel("Net external migration\n(per 1,000 inhabitants)", fontsize=10, labelpad=10)
    lax.set_ylabel("Registered unemployed\n(per 1,000 inhabitants)", fontsize=10, labelpad=10)
    lax.set_title("Bivariate legend", fontsize=12, fontweight="bold", pad=12)
    lax.tick_params(length=0)
    for spine in lax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()

    # Sense bbox_inches="tight" perquè tots els fotogrames tinguin la mateixa mida
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


# ==================================================
# 7. GENERAR EL GIF
# ==================================================

frames = []
for a in anys:
    print(f"Dibuixant {a}...")
    frames.append(dibuixa_any(a))

# Paleta adaptativa per evitar tramat als colors plans del mapa
frames_p = [f.convert("P", palette=Image.ADAPTIVE, colors=256) for f in frames]

durades = [MS_PER_FRAME] * len(frames_p)
durades[-1] = MS_ULTIM_FRAME

Path(OUTPUT_GIF).parent.mkdir(parents=True, exist_ok=True)

frames_p[0].save(
    OUTPUT_GIF,
    save_all=True,
    append_images=frames_p[1:],
    duration=durades,
    loop=0,
    optimize=False,
) 

print(f"GIF desat a {OUTPUT_GIF}")