import os
import pandas as pd

# 1. Rutes del teu projecte
carpeta_desti = r"data/raw/demografia"
ruta_entrada = os.path.join(carpeta_desti, "poblacio_raw_idescat.csv")
ruta_sortida = os.path.join(carpeta_desti, "poblacio_idescat_agrupada.csv")

# 2. Diccionari d'equivalències (en minúscules per coincidir amb el CSV raw)
mapa_edats = {
    "de 0 a 4 anys": "De 0 a 14 anys",
    "de 5 a 9 anys": "De 0 a 14 anys",
    "de 10 a 14 anys": "De 0 a 14 anys",
    "de 15 a 19 anys": "De 15 a 29 anys",
    "de 20 a 24 anys": "De 15 a 29 anys",
    "de 25 a 29 anys": "De 15 a 29 anys",
    "de 30 a 34 anys": "De 30 a 34 anys",
    "de 35 a 39 anys": "De 35 a 44 anys",
    "de 40 a 44 anys": "De 35 a 44 anys",
    "de 45 a 49 anys": "De 45 a 59 anys",
    "de 50 a 54 anys": "De 45 a 59 anys",
    "de 55 a 59 anys": "De 45 a 59 anys",
    "de 60 a 64 anys": "De 60 anys i més",
    "de 65 a 69 anys": "De 60 anys i més",
    "de 70 a 74 anys": "De 60 anys i més",
    "de 75 a 79 anys": "De 60 anys i més",
    "de 80 a 84 anys": "De 60 anys i més",
    "de 85 a 89 anys": "De 60 anys i més",
    "de 90 a 94 anys": "De 60 anys i més",
    "de 95 a 99 anys": "De 60 anys i més",
    "100 anys o més": "De 60 anys i més",
    "de 85 anys i més": "De 60 anys i més",
    "85 anys i més": "De 60 anys i més",
    "total": "Total"
}

ordre_grups = [
    "De 0 a 14 anys",
    "De 15 a 29 anys",
    "De 30 a 34 anys",
    "De 35 a 44 anys",
    "De 45 a 59 anys",
    "De 60 anys i més",
    "Total"
]

# 3. Llegim el CSV raw descarregat (7 columnes separades per ';')
df = pd.read_csv(
    ruta_entrada,
    sep=";",
    header=None,
    names=["Periode", "Territori", "Edat_raw", "Sexe", "Concepte", "Estat", "Valor"]
)

# Ens quedem amb Catalunya i amb S1/ (població a 1 de gener de cada any; si hi ha S2/ l'ignorem perquè no dupliqui)
df["Periode"] = df["Periode"].astype(str).str.strip()
df = df[df["Periode"].str.startswith("S1/")].copy()
df["Any"] = df["Periode"].str.replace("S1/", "", regex=False).astype(int)

# Normalitzem text i números
df["Edat_raw"] = df["Edat_raw"].astype(str).str.strip().str.lower()
df["Sexe"] = df["Sexe"].astype(str).str.strip().str.lower()
df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
df = df.dropna(subset=["Valor"])
df["Valor"] = df["Valor"].astype(int)

# Mapegem als 6 grups d'edat + Total
df["Grup_edat"] = df["Edat_raw"].map(mapa_edats)
df = df.dropna(subset=["Grup_edat"])

# Agrupem per Any, Grup_edat i Sexe, i passem Sexe a columnes (homes, dones, total)
df_pivot = (
    df.groupby(["Any", "Grup_edat", "Sexe"], as_index=False)["Valor"]
    .sum()
    .pivot(index=["Any", "Grup_edat"], columns="Sexe", values="Valor")
    .reset_index()
)

# Reanomenem les columnes al format exacte que espera analitzar_demografia.py
df_pivot = df_pivot.rename(columns={
    "homes": "Poblacio_homes",
    "dones": "Poblacio_dones",
    "total": "Poblacio_total"
})[["Any", "Grup_edat", "Poblacio_homes", "Poblacio_dones", "Poblacio_total"]]

# Ordenem cronològicament per Any i Grup_edat
df_pivot["Grup_edat"] = pd.Categorical(df_pivot["Grup_edat"], categories=ordre_grups, ordered=True)
df_pivot = df_pivot.sort_values(["Any", "Grup_edat"]).reset_index(drop=True)

# Guardem el resultat
df_pivot.to_csv(ruta_sortida, index=False, sep=";", encoding="utf-8-sig")
print(f"✅ Fitxer generat correctament a: {ruta_sortida}")
print(f"Anys processats: {sorted(df_pivot['Any'].unique())}")