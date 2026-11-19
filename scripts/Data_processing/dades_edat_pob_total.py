import os
import pandas as pd

# 1. Ruta exacta del teu projecte
carpeta_desti = r"data/raw/demografia"
os.makedirs(carpeta_desti, exist_ok=True)
ruta_fitxer = os.path.join(carpeta_desti, "poblacio_idescat_agrupada.csv")

# 2. Diccionari d'equivalències (Franges de 5 anys -> Franges de Migracions)
mapa_edats = {
    "De 0 a 4 anys": "De 0 a 14 anys",
    "De 5 a 9 anys": "De 0 a 14 anys",
    "De 10 a 14 anys": "De 0 a 14 anys",
    "De 15 a 19 anys": "De 15 a 29 anys",
    "De 20 a 24 anys": "De 15 a 29 anys",
    "De 25 a 29 anys": "De 15 a 29 anys",
    "De 30 a 34 anys": "De 30 a 34 anys",
    "De 35 a 39 anys": "De 35 a 44 anys",
    "De 40 a 44 anys": "De 35 a 44 anys",
    "De 45 a 49 anys": "De 45 a 59 anys",
    "De 50 a 54 anys": "De 45 a 59 anys",
    "De 55 a 59 anys": "De 45 a 59 anys",
    "De 60 a 64 anys": "De 60 anys i més",
    "De 65 a 69 anys": "De 60 anys i més",
    "De 70 a 74 anys": "De 60 anys i més",
    "De 75 a 79 anys": "De 60 anys i més",
    "De 80 a 84 anys": "De 60 anys i més",
    "De 85 a 89 anys": "De 60 anys i més",
    "De 90 a 94 anys": "De 60 anys i més",
    "De 95 a 99 anys": "De 60 anys i més",
    "100 anys o més": "De 60 anys i més",
    "Total": "Total"
}

# Ordre lògic perquè la taula final no s'ordeni alfabèticament
ordre_grups = [
    "De 0 a 14 anys",
    "De 15 a 29 anys",
    "De 30 a 34 anys",
    "De 35 a 44 anys",
    "De 45 a 59 anys",
    "De 60 anys i més",
    "Total"
]

# 3. Anys disponibles a l'indicador (2012 a 2026)
anys = range(2012, 2027)
taules = []

print("Descarregant i agrupant dades de població de l'Idescat...")

for any_actual in anys:
    url = f"https://www.idescat.cat/indicadors/?id=aec&n=15231&t={any_actual}&f=ssv"
    
    try:
        # Llegim totes les files per filtrar només les que coincideixen amb el nostre mapa d'edats
        df = pd.read_csv(url, sep=";", header=None, names=["Grup_edat_5", "Poblacio_homes", "Poblacio_dones", "Poblacio_total"])
        
        # Netegem espais en blanc
        df["Grup_edat_5"] = df["Grup_edat_5"].astype(str).str.strip()
        
        # Ens quedem estrictament amb les files d'edat vàlides (ignorem títols i notes al peu)
        df = df[df["Grup_edat_5"].isin(mapa_edats.keys())].copy()
        
        if not df.empty:
            # Netegem els punts dels milers i passem a número enter (int)
            for col in ["Poblacio_homes", "Poblacio_dones", "Poblacio_total"]:
                df[col] = df[col].astype(str).str.replace(".", "", regex=False).str.strip().astype(int)
            
            # Mapegem a les noves categories
            df["Grup_edat"] = df["Grup_edat_5"].map(mapa_edats)
            
            # Agrupem i sumem per les noves categories
            df_agrupat = df.groupby("Grup_edat", as_index=False)[["Poblacio_homes", "Poblacio_dones", "Poblacio_total"]].sum()
            
            # Mantenim l'ordre cronològic de les edats
            df_agrupat["Grup_edat"] = pd.Categorical(df_agrupat["Grup_edat"], categories=ordre_grups, ordered=True)
            df_agrupat = df_agrupat.sort_values("Grup_edat")
            
            # Afegim la columna de l'any
            df_agrupat.insert(0, "Any", any_actual)
            taules.append(df_agrupat)
            print(f" Any {any_actual} processat correctament.")
            
    except Exception as e:
        print(f" No s'ha pogut processar l'any {any_actual}: {e}")

# 4. Guardem el CSV final unificat
if taules:
    df_final = pd.concat(taules, ignore_index=True)
    df_final.to_csv(ruta_fitxer, index=False, sep=";", encoding="utf-8-sig")
    print(f"\n Fet! Fitxer de població agrupada guardat a:\n{ruta_fitxer}")
else:
    print("\n No s'han pogut descarregar dades.")