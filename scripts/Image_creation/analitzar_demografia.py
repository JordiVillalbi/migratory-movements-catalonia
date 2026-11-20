from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw" / "demografia"
PROC_DIR = ROOT_DIR / "data" / "processed" / "demografia"
PROC_DIR.mkdir(parents=True, exist_ok=True)

df_mig = pd.read_csv(RAW_DIR / "migracions_idescat_tots_els_anys.csv", sep=";")
df_pob = pd.read_csv(RAW_DIR / "poblacio_idescat_agrupada.csv", sep=";")

# Netegem punts de milers, espais i notes al peu (com la 'b' de '15229 b')
cols_mig = [
    "Immigracions_homes", "Immigracions_dones", "Immigracions_total",
    "Emigracions_homes", "Emigracions_dones", "Emigracions_total",
    "Saldo_migratori_homes", "Saldo_migratori_dones", "Saldo_migratori_total"
]
for col in cols_mig:
    df_mig[col] = (
        df_mig[col].astype(str)
        .str.replace(r"[^0-9\-]", "", regex=True)
        .astype(int)
    )

for df in (df_mig, df_pob):
    df["Any"] = df["Any"].astype(int)
    df["Grup_edat"] = df["Grup_edat"].astype(str).str.strip()

df_final = pd.merge(df_mig, df_pob, on=["Any", "Grup_edat"], how="inner")
df_final["Taxa_neta_1000"] = ((df_final["Saldo_migratori_total"] / df_final["Poblacio_total"]) * 1000).round(2)

ruta_sortida = PROC_DIR / "estudi_impacte_migracions.csv"
df_final.to_csv(ruta_sortida, index=False, sep=";", encoding="utf-8-sig")
print(f"Fitxer creuat actualitzat correctament: {ruta_sortida}")
