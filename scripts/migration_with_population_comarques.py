import re
import time
import unicodedata
from pathlib import Path

import pandas as pd
import requests

MIG = "https://www.idescat.cat/pub/?id=mm&n=5489&geo=com%3A{c}&f=ssv"
POB = "https://www.idescat.cat/indicadors/?id=aec&n=15224&f=ssv&t={a}00"
ANY_MIN, ANY_MAX = 2002, 2022       # el saldo extern només existeix des del 2002
SORTIDA = Path("data/raw/migration/saldo_extern_comarques.csv")


def num(x):
    """'47.138' / '4288 (b)' -> número ; '..' -> NaN"""
    x = re.sub(r"\(.*?\)", "", str(x)).replace(".", "").replace(" ", "")
    return pd.to_numeric(x.strip('"'), errors="coerce")


def norm(s):
    s = unicodedata.normalize("NFKC", str(s)).replace("’", "'")
    return s.strip().lower()


def get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8"
    time.sleep(0.5)
    return r.text.splitlines()


# 1) Saldo migratori EXTERN (10a fila de dades), tots els anys
rows = []
nom_comarca = {}                                 # codi -> nom, el treu de la descàrrega
for n in range(1, 43):                           # sense el Lluçanès (43)
    c = f"{n:02d}"
    linies = get(MIG.format(c=c))
    nom_comarca[c] = linies[1].strip().strip('"')    # 2a línia = nom de la comarca
    h = next(i for i, l in enumerate(linies) if re.match(r";(19|20)\d{2}", l))
    anys = [a.strip('" ') for a in linies[h].split(";")[1:]]
    dades = [l.split(";") for l in linies[h + 1:]
             if any(x.strip() for x in l.split(";")[1:])]
    extern = dades[9][-len(anys):]               # 10a fila = Migracions externes, saldo
    rows += [(c, int(a), num(v)) for a, v in zip(anys, extern) if a.isdigit()]
    print(c, nom_comarca[c])

df = pd.DataFrame(rows, columns=["Codi", "Any", "Saldo_ext"])
df = df[df["Any"].between(ANY_MIN, ANY_MAX)].dropna(subset=["Saldo_ext"])

# 2) Població a 1 de gener (fins ANY_MAX + 1)
nom2codi = {norm(n): c for c, n in nom_comarca.items()}

rows = []
for a in range(ANY_MIN, ANY_MAX + 2):
    for l in get(POB.format(a=a)):
        c = l.split(";")
        if len(c) > 1 and norm(c[0]) in nom2codi:
            rows.append((nom2codi[norm(c[0])], a, num(c[1])))
    print(a, "OK")

pob = pd.DataFrame(rows, columns=["Codi", "Any", "Pob"]).set_index(["Codi", "Any"])["Pob"]

# 3) Població mitjana = mitjana de l'1 de gener de l'any i del següent
#    (si només n'hi ha una, com al Moianès 2015, fa servir aquella)
p0 = pob.reindex(pd.MultiIndex.from_frame(df[["Codi", "Any"]])).values
p1 = pob.reindex(pd.MultiIndex.from_arrays([df["Codi"], df["Any"] + 1])).values
df["Poblacio"] = pd.DataFrame({"a": p0, "b": p1}).mean(axis=1).values
df["saldo_ext_per_mil"] = df["Saldo_ext"] / df["Poblacio"] * 1000
df["Nom"] = df["Codi"].map(nom_comarca)
df = df[["Codi", "Nom", "Any", "Saldo_ext", "Poblacio", "saldo_ext_per_mil"]]
df = df.sort_values(["Any", "Codi"]).reset_index(drop=True)

SORTIDA.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(SORTIDA, index=False, encoding="utf-8-sig")

print(df.shape, "| files sense població:", df["Poblacio"].isna().sum())
print(df.groupby("Any")["Codi"].nunique().to_string())