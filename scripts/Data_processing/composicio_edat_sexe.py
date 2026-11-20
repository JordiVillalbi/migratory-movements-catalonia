import os
import pandas as pd

# 1. Ruta exacta del teu projecte on es guardarà el fitxer
carpeta_desti = r"data/raw/demografia"

# Ens assegurem que la carpeta existeixi (si no existeix, la crea automàticament)
os.makedirs(carpeta_desti, exist_ok=True)

# Ruta completa incloent el nom del fitxer CSV
ruta_fitxer = os.path.join(carpeta_desti, "migracions_idescat_tots_els_anys.csv")

# 2. Llista d'anys a comprovar
anys = range(2005, 2027)
taules = []

# Noms nets per a les 10 columnes de la taula
columnes = [
    "Grup_edat",
    "Immigracions_homes", "Immigracions_dones", "Immigracions_total",
    "Emigracions_homes", "Emigracions_dones", "Emigracions_total",
    "Saldo_migratori_homes", "Saldo_migratori_dones", "Saldo_migratori_total"
]

print("Descarregant dades de l'Idescat...")

for any_actual in anys:
    url = f"https://www.idescat.cat/pub/?id=mm&n=6382&t={any_actual}00&f=ssv"
    
    try:
        df = pd.read_csv(url, sep=";", skiprows=6, header=None)
        df = df.iloc[:, :10]
        df.columns = columnes
        
        df = df.dropna(subset=["Grup_edat"])
        df = df[~df["Grup_edat"].astype(str).str.startswith("Font:")]
        
        if not df.empty:
            df.insert(0, "Any", any_actual)
            taules.append(df)
            print(f"Any {any_actual} descarregat.")
            
    except Exception:
        pass

# 3. Guardem el CSV a la carpeta del teu projecte
if taules:
    df_final = pd.concat(taules, ignore_index=True)
    df_final.to_csv(ruta_fitxer, index=False, sep=";", encoding="utf-8-sig")
    print(f"\n Fet! Fitxer guardat correctament a:\n{ruta_fitxer}")
else:
    print("\n No s'han pogut descarregar dades.")