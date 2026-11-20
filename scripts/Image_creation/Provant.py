from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

# ==============================================================================
# 1. RUTES RELATIVES (des de Projecte_Big_Data/scripts/Image_creation/)
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "demografia" / "estudi_impacte_migracions.csv"
FIGURES_DIR = BASE_DIR / "results" / "figures"
PIRAMIDES_DIR = FIGURES_DIR / "piramides"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
PIRAMIDES_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 2. ESTÈTICA SOBRIA I NETA
# ==============================================================================
plt.rcParams.update({
    "font.sans-serif": "DejaVu Sans",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "grid.color": "#E5E5E5",
    "grid.linestyle": "-",
    "grid.linewidth": 0.6,
    "figure.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.2
})

BLAU = "#2B5C8F"
VERMELL = "#C0392B"
GRIS = "#8C969E"

ORDRE_EDATS = [
    "De 0 a 14 anys",
    "De 15 a 29 anys",
    "De 30 a 34 anys",
    "De 35 a 44 anys",
    "De 45 a 59 anys",
    "De 60 anys i més"
]

AMPLADA_INTERVAL = {
    "De 0 a 14 anys": 15,
    "De 15 a 29 anys": 15,
    "De 30 a 34 anys": 5,
    "De 35 a 44 anys": 10,
    "De 45 a 59 anys": 15,
    "De 60 anys i més": 25
}

# ==============================================================================
# 3. CÀRREGA DE DADES
# ==============================================================================
def carregar_dades(ruta: Path) -> pd.DataFrame:
    df = pd.read_csv(ruta, sep=";")
    df = df[df["Any"].isin([2022, 2023, 2024])].copy()
    df = df[df["Grup_edat"].isin(ORDRE_EDATS)].copy()
    
    df["Grup_edat"] = pd.Categorical(df["Grup_edat"], categories=ORDRE_EDATS, ordered=True)
    df = df.sort_values(["Any", "Grup_edat"]).reset_index(drop=True)
    
    df["Anys_interval"] = df["Grup_edat"].map(AMPLADA_INTERVAL).astype(int)
    df["Taxa_migratoria_%"] = (df["Saldo_migratori_total"] / df["Poblacio_total"]) * 100
    
    return df

# ==============================================================================
# GRÀFIC 1: FLUXOS MIGRATORIS ACUMULATS PER EDAT (2022-2024)
# ==============================================================================
def plot_fluxos_edat(df: pd.DataFrame, output_path: Path):
    df_agg = df.groupby("Grup_edat", observed=False).agg({
        "Immigracions_total": "sum",
        "Emigracions_total": "sum"
    }).reset_index()

    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(df_agg))

    ax.barh(y, -df_agg["Emigracions_total"], color=VERMELL, height=0.55, label="Emigracions")
    ax.barh(y, df_agg["Immigracions_total"], color=BLAU, height=0.55, label="Immigracions")

    ax.axvline(0, color="#333333", linewidth=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(df_agg["Grup_edat"], fontsize=10)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, pos: f"{abs(int(x))/1000:.0f}k"))
    ax.set_xlim(-320000, 620000)
    ax.grid(axis="x")
    ax.set_axisbelow(True)

    ax.set_title("Fluxos migratoris acumulats per edat (2022–2024)", fontsize=12, fontweight="bold", loc="left", pad=12)
    ax.set_xlabel("Persones (milers)", fontsize=10)
    ax.legend(frameon=False, loc="lower right", fontsize=9.5)

    plt.savefig(output_path)
    plt.close()

# ==============================================================================
# GRÀFIC 2: PIRÀMIDE REAL VS. SENSE MIGRACIÓ (2024)
# ==============================================================================
def plot_piramide(df: pd.DataFrame, output_path: Path):
    pob_2024 = df[df["Any"] == 2024][["Grup_edat", "Poblacio_homes", "Poblacio_dones"]].copy()
    saldo_acum = df.groupby("Grup_edat", observed=False).agg({
        "Saldo_migratori_homes": "sum",
        "Saldo_migratori_dones": "sum",
        "Anys_interval": "first"
    }).reset_index()

    dades = pd.merge(pob_2024, saldo_acum, on="Grup_edat")

    # Normalitzem per any d'edat per corregir que els trams tinguin diferents amplades
    h_real = (dades["Poblacio_homes"] / dades["Anys_interval"])
    d_real = (dades["Poblacio_dones"] / dades["Anys_interval"])
    h_sense = ((dades["Poblacio_homes"] - dades["Saldo_migratori_homes"]) / dades["Anys_interval"])
    d_sense = ((dades["Poblacio_dones"] - dades["Saldo_migratori_dones"]) / dades["Anys_interval"])

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    y = np.arange(len(dades))

    ax.barh(y, -h_real, color=BLAU, height=0.6, label="Homes (2024)")
    ax.barh(y, d_real, color=VERMELL, height=0.6, label="Dones (2024)")

    ax.barh(y, -h_sense, facecolor="none", edgecolor="#111111", linestyle="--", linewidth=1.2, height=0.6, label="Sense migració 2022–24")
    ax.barh(y, d_sense, facecolor="none", edgecolor="#111111", linestyle="--", linewidth=1.2, height=0.6)

    ax.axvline(0, color="#333333", linewidth=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(dades["Grup_edat"], fontsize=10)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, pos: f"{abs(int(x))/1000:.0f}k"))
    ax.set_xlim(-80000, 80000)
    ax.grid(axis="x")
    ax.set_axisbelow(True)

    ax.set_title("Piràmide de població: real vs. escenari sense migració (2024)", fontsize=12, fontweight="bold", loc="left", pad=12)
    ax.set_xlabel("Residents per any d'edat (milers)", fontsize=10)
    ax.legend(frameon=False, loc="lower right", fontsize=9)

    plt.savefig(output_path)
    plt.close()

# ==============================================================================
# GRÀFIC 3: TAXA MIGRATÒRIA NETA ANUAL (%)
# ==============================================================================
def plot_heatmap_taxa(df: pd.DataFrame, output_path: Path):
    pivot = df.pivot(index="Grup_edat", columns="Any", values="Taxa_migratoria_%").iloc[::-1]

    fig, ax = plt.subplots(figsize=(7.5, 5))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        cmap="Blues",
        cbar_kws={"label": "Taxa migratòria neta (%)"},
        linewidths=1,
        linecolor="white",
        annot_kws={"size": 10},
        ax=ax
    )

    ax.set_title("Taxa de creixement migratori anual per edat (%)", fontsize=12, fontweight="bold", loc="left", pad=12)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="y", rotation=0, labelsize=10)
    ax.tick_params(axis="x", labelsize=10)

    plt.savefig(output_path)
    plt.close()

# ==============================================================================
# GRÀFIC 4: ESTRUCTURA PER EDAT (% POBLACIÓ VS. % SALDO MIGRATORI)
# ==============================================================================
def plot_estructura_comparada(df: pd.DataFrame, output_path: Path):
    pob_2024 = df[df["Any"] == 2024].groupby("Grup_edat", observed=False)["Poblacio_total"].sum()
    saldo_acum = df.groupby("Grup_edat", observed=False)["Saldo_migratori_total"].sum()

    pct_pob = (pob_2024 / pob_2024.sum()) * 100
    pct_mig = (saldo_acum / saldo_acum.sum()) * 100

    fig, ax = plt.subplots(figsize=(9.5, 5))
    x = np.arange(len(ORDRE_EDATS))
    width = 0.35

    ax.bar(x - width/2, pct_pob, width, color=GRIS, label="Població resident (2024)")
    ax.bar(x + width/2, pct_mig, width, color=BLAU, label="Saldo migratori net (2022–2024)")

    for i in range(len(ORDRE_EDATS)):
        ax.text(x[i] - width/2, pct_pob.iloc[i] + 0.5, f"{pct_pob.iloc[i]:.1f}%", ha="center", va="bottom", fontsize=8.5, color="#444444")
        ax.text(x[i] + width/2, pct_mig.iloc[i] + 0.5, f"{pct_mig.iloc[i]:.1f}%", ha="center", va="bottom", fontsize=8.5, color=BLAU, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(ORDRE_EDATS, fontsize=9.5)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, max(pct_mig.max(), pct_pob.max()) + 6)
    ax.grid(axis="y")
    ax.set_axisbelow(True)

    ax.set_title("Distribució per edat: població resident vs. saldo migratori (%)", fontsize=12, fontweight="bold", loc="left", pad=12)
    ax.set_ylabel("Pes sobre el total del grup (%)", fontsize=10)
    ax.legend(frameon=False, loc="upper right", fontsize=9.5)

    plt.savefig(output_path)
    plt.close()

# ==============================================================================
# EXECUCIÓ
# ==============================================================================
if __name__ == "__main__":
    df_cat = carregar_dades(DATA_PATH)

    plot_fluxos_edat(df_cat, FIGURES_DIR / "01_fluxos_migratoris_edat.png")
    plot_piramide(df_cat, PIRAMIDES_DIR / "02_piramide_real_vs_sense_migracio.png")
    plot_heatmap_taxa(df_cat, FIGURES_DIR / "03_heatmap_taxa_migratoria.png")
    plot_estructura_comparada(df_cat, FIGURES_DIR / "04_estructura_poblacio_vs_migracio.png")
    
    print("Gràfics generats correctament.")