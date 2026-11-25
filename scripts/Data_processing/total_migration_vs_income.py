"""
Migracions externes (saldo migratori exterior) + sou mitjà aproximat (rendiments del
treball / base imposable IRPF per declarant) per comarca de Catalunya (2005 - 2024).

Sortida única:
  - data/processed/economics/migracio_externa_salaris_comarques.csv
  Columnes: comarca, any, saldo_migratori_exterior, sou_mitja_eur
"""

import os
import re
import time
import unicodedata
from io import StringIO

import pandas as pd
import requests


# =====================================================
# CONFIGURACIÓ
# =====================================================

ANYS = list(range(2005, 2025))  # Del 2005 al 2024 inclòs

OUTPUT_DIR = "data/processed/economics"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "migracio_externa_salaris_comarques.csv")

# Idescat: Moviments migratoris externs per comarques
URL_MIGRACIONS_COM = "https://www.idescat.cat/pub/?geo=com&id=mm&n=5489&t={any}00"

# Idescat: IRPF oficial per comarques (rendiments del treball / base imposable)
URLS_IRPF_COM = [
    "https://www.idescat.cat/pub/?id=irpf&n=16160&geo=com&t={any}00",
    "https://www.idescat.cat/pub/?id=irpf&n=4070&geo=com&t={any}00",
    "https://www.idescat.cat/indicadors/?id=aec&n=15905&t={any}00",
]


# =====================================================
# FUNCIONS AUXILIARS
# =====================================================

def normalitza(text):
    text = unicodedata.normalize("NFKD", str(text).lower().strip())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text)


def clau_comarca(text):
    """Unifica els noms de les comarques per creuar les taules sense pèrdues."""
    n = normalitza(text)
    n = re.sub(r"\(.*?\)", "", n).strip()
    n = re.sub(r"^val d'", "", n)
    n = re.sub(r"^(el |la |les |els |l')", "", n)
    equivalencies = {
        "aran": "aran",
        "val d'aran": "aran",
        "llucanes": "llucanes",
    }
    return equivalencies.get(n.strip(), n.strip())


def numero_idescat(valor):
    """Converteix números en format català/europeu (punt = milers, coma = decimals)."""
    if isinstance(valor, (int, float)):
        return float(valor)
    if valor is None or pd.isna(valor):
        return float("nan")
    s = str(valor).strip().replace("\xa0", "").replace(" ", "")
    if s in ["", "-", ":", "..", "nan", "None"]:
        return float("nan")
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def descarrega(url):
    """Descarrega una URL directament en memòria."""
    time.sleep(0.3)
    try:
        r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        return r.content if r.status_code == 200 else None
    except requests.RequestException:
        return None


# =====================================================
# 1. SALDO MIGRATORI EXTERIOR PER COMARCA
# =====================================================

def obtenir_migracions_com(any_):
    contingut = descarrega(URL_MIGRACIONS_COM.format(any=any_))
    if not contingut:
        return pd.DataFrame()
    try:
        taules = pd.read_html(StringIO(contingut.decode("utf-8", errors="replace")))
    except Exception:
        return pd.DataFrame()
    if not taules:
        return pd.DataFrame()

    df = max(taules, key=len).copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(map(str, c)) for c in df.columns]
    df.columns = [normalitza(c) for c in df.columns]

    col_nom = next((c for c in df.columns if "nom" in c or "comarca" in c), None)
    col_imm = next((c for c in df.columns if "externes immigracions" in c), None)
    col_emi = next((c for c in df.columns if "externes emigracions" in c), None)

    if not col_nom or not col_imm or not col_emi:
        return pd.DataFrame()

    imm = df[col_imm].apply(numero_idescat)
    emi = df[col_emi].apply(numero_idescat)

    out = pd.DataFrame({
        "comarca": df[col_nom].astype(str).str.strip(),
        "any": any_,
        "saldo_migratori_exterior": imm - emi,
    })
    out = out.dropna(subset=["saldo_migratori_exterior"])
    out = out[out["comarca"].map(clau_comarca) != "catalunya"]
    return out


# =====================================================
# 2. SOU MITJÀ (RENDIMENTS TREBALL / IRPF) PER COMARCA
# =====================================================

def obtenir_sou_com(any_):
    for plantilla in URLS_IRPF_COM:
        contingut = descarrega(plantilla.format(any=any_))
        if not contingut:
            continue
        try:
            taules = pd.read_html(StringIO(contingut.decode("utf-8", errors="replace")))
        except Exception:
            continue
        if not taules:
            continue

        df = max(taules, key=len).copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [" ".join(map(str, c)) for c in df.columns]
        df.columns = [normalitza(c) for c in df.columns]

        if len(df) < 35:
            continue

        col_nom = next(
            (c for c in df.columns if any(k in c for k in ["nom", "comarca", "territori"])),
            df.columns[0],
        )
        # Prioritza rendiments del treball i, si no hi és, base imposable per declarant
        col_sou = next((c for c in df.columns if "treball" in c), None)
        if col_sou is None:
            col_sou = next((c for c in df.columns if "base imposable" in c), None)

        if col_sou:
            valors = df[col_sou].apply(numero_idescat)
            # Si l'import ve en milers d'euros per declarant (ex: 24,5), passem a euros
            if valors.median() < 200:
                valors = valors * 1000.0

            out = pd.DataFrame({
                "comarca": df[col_nom].astype(str).str.strip(),
                "any": any_,
                "sou_mitja_eur": valors,
            })
            out = out.dropna(subset=["sou_mitja_eur"])
            out = out[~out["comarca"].map(clau_comarca).isin(["catalunya", "total", "font:", ""])]
            if len(out) >= 35:
                return out

    return pd.DataFrame()


# =====================================================
# 3. CONSOLIDACIÓ I GUARDAT
# =====================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    llista_mig, llista_sou = [], []

    for any_ in ANYS:
        print(f"Processant any {any_}...")
        m = obtenir_migracions_com(any_)
        if not m.empty:
            llista_mig.append(m)

        s = obtenir_sou_com(any_)
        if not s.empty:
            llista_sou.append(s)

    if not llista_mig:
        raise ValueError("No s'han pogut descarregar les dades de migració.")

    df_mig = pd.concat(llista_mig, ignore_index=True)
    df_mig["clau"] = df_mig["comarca"].map(clau_comarca)

    if llista_sou:
        df_sou = pd.concat(llista_sou, ignore_index=True)
        df_sou["clau"] = df_sou["comarca"].map(clau_comarca)
        df_final = df_mig.merge(
            df_sou[["clau", "any", "sou_mitja_eur"]],
            on=["clau", "any"],
            how="left",
        )
    else:
        df_final = df_mig.copy()
        df_final["sou_mitja_eur"] = float("nan")

    # Ens quedem estrictament amb les columnes demanades
    df_final = (
        df_final[["comarca", "any", "saldo_migratori_exterior", "sou_mitja_eur"]]
        .sort_values(["comarca", "any"])
        .reset_index(drop=True)
    )

    df_final.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\n[OK] Fitxer guardat a: {OUTPUT_FILE} ({len(df_final)} files)")
    print(df_final.head(15).to_string(index=False))


if __name__ == "__main__":
    main()