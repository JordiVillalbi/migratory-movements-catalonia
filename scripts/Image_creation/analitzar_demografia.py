from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. RUTES RELATIVES (Apunta automàticament a 'Projecte_Big_ Data/' des de 'scripts/')
ROOT_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT_DIR / "data" / "raw" / "demografia"
PROCESSED_DIR = ROOT_DIR / "data" / "processed" / "demografia"
FIGURES_DIR = ROOT_DIR / "results" / "figures"/ "piramides"

# Crea les carpetes de sortida automàticament si algun company encara no les té
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# 2. CÀRREGA I NETEJA DE DADES
df_mig = pd.read_csv(RAW_DIR / "migracions_idescat_tots_els_anys.csv", sep=";")
df_pob = pd.read_csv(RAW_DIR / "poblacio_idescat_agrupada.csv", sep=";")

df_mig["Grup_edat"] = df_mig["Grup_edat"].str.strip()
df_pob["Grup_edat"] = df_pob["Grup_edat"].str.strip()

# Netegem punts dels milers i anotacions de l'Idescat com (b) o (p)
for df_temp in [df_mig, df_pob]:
    cols_num = [c for c in df_temp.columns if c not in ["Any", "Grup_edat"]]
    for col in cols_num:
        df_temp[col] = (
            df_temp[col]
            .astype(str)
            .str.replace(r"\(.*?\)", "", regex=True)
            .str.replace(".", "", regex=False)
            .str.strip()
            .astype(int)
        )

# 3. CREUAMENT I CÀLCUL D'INDICADORS
df = pd.merge(df_mig, df_pob, on=["Any", "Grup_edat"], how="inner")

for sexe in ["homes", "dones", "total"]:
    df[f"Taxa_neta_{sexe}_‰"] = (df[f"Saldo_migratori_{sexe}"] / df[f"Poblacio_{sexe}"] * 1000).round(2)
    df[f"Index_eficacia_{sexe}"] = (
        df[f"Saldo_migratori_{sexe}"] / (df[f"Immigracions_{sexe}"] + df[f"Emigracions_{sexe}"])
    ).round(3)

df["Ratio_masc_poblacio"] = (df["Poblacio_homes"] / df["Poblacio_dones"] * 100).round(2)
df["Ratio_masc_saldo"] = (df["Saldo_migratori_homes"] / df["Saldo_migratori_dones"] * 100).round(2)

# Excloem la fila 'Total' per calcular el pes percentual de cada grup d'edat
df_sense_total = df[df["Grup_edat"] != "Total"].copy()
totals_anuals = df_sense_total.groupby("Any")[["Poblacio_total", "Saldo_migratori_total"]].transform("sum")

df_sense_total["Pes_poblacio_%"] = (df_sense_total["Poblacio_total"] / totals_anuals["Poblacio_total"] * 100).round(2)
df_sense_total["Pes_saldo_mig_%"] = (df_sense_total["Saldo_migratori_total"] / totals_anuals["Saldo_migratori_total"] * 100).round(2)
df_sense_total["Diferencia_estructura_pp"] = (df_sense_total["Pes_saldo_mig_%"] - df_sense_total["Pes_poblacio_%"]).round(2)

# Guardem el CSV processat
ruta_processed = PROCESSED_DIR / "estudi_impacte_migracions.csv"
df_sense_total.to_csv(ruta_processed, index=False, sep=";", encoding="utf-8-sig")
print(f"✅ Dataset analític guardat a: {ruta_processed}")

# 4. GENERACIÓ DE LES PIRÀMIDES DE POBLACIÓ VS. SALDO MIGRATORI
ordre_grups = [
    "De 0 a 14 anys",
    "De 15 a 29 anys",
    "De 30 a 34 anys",
    "De 35 a 44 anys",
    "De 45 a 59 anys",
    "De 60 anys i més"
]

for any_sel in sorted(df_sense_total["Any"].unique()):
    df_any = df_sense_total[df_sense_total["Any"] == any_sel].copy()
    df_any["Grup_edat"] = pd.Categorical(df_any["Grup_edat"], categories=ordre_grups, ordered=True)
    df_any = df_any.sort_values("Grup_edat")

    tot_pob = df_any["Poblacio_total"].sum()
    tot_saldo = df_any["Saldo_migratori_total"].sum()

    pct_pob_h = -(df_any["Poblacio_homes"] / tot_pob) * 100
    pct_pob_d = (df_any["Poblacio_dones"] / tot_pob) * 100
    pct_sal_h = -(df_any["Saldo_migratori_homes"] / tot_saldo) * 100
    pct_sal_d = (df_any["Saldo_migratori_dones"] / tot_saldo) * 100

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    y = np.arange(len(ordre_grups))

    ax.barh(y, pct_pob_h, height=0.75, color="#B0C4DE", alpha=0.75, label="Població Resident (Homes)")
    ax.barh(y, pct_pob_d, height=0.75, color="#F4C2C2", alpha=0.75, label="Població Resident (Dones)")
    ax.barh(y, pct_sal_h, height=0.38, color="#1F4E79", label="Saldo Migratori Net (Homes)")
    ax.barh(y, pct_sal_d, height=0.38, color="#C0392B", label="Saldo Migratori Net (Dones)")

    ax.set_yticks(y)
    ax.set_yticklabels(ordre_grups, fontsize=10, fontweight="bold")
    ax.axvline(0, color="black", linewidth=0.9)

    xticks = np.arange(-30, 35, 5)
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{abs(x)}%" for x in xticks])
    ax.set_xlim(-32, 32)

    ax.set_xlabel("% respecte al total de cada grup (Població vs. Saldo Migratori)")
    ax.set_title(f"Impacte de les Migracions en l'Estructura Demogràfica ({any_sel})", fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    ax.legend(loc="lower right", fontsize=9)

    plt.tight_layout()
    ruta_img = FIGURES_DIR / f"piramide_migracions_{any_sel}.png"
    plt.savefig(ruta_img)
    plt.close()
    print(f"✅ Piràmide guardada a: {ruta_img}")