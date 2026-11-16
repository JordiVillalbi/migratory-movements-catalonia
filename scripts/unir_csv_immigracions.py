
"""Uneix els CSV anuals d'Idescat (emigracions i immigracions externes) en taules LLARGUES.

Per cada conjunt (emigracions_externes, immigracions_externes):
  Llegeix:  <arrel_projecte>/data/raw/migration/<conjunt>/*.csv
  Escriu:   <arrel_projecte>/data/processed/<conjunt>.csv
L'arrel del projecte és la carpeta pare de 'scripts', així funciona des de qualsevol directori.
"""
import csv, re, sys, glob, os
from collections import defaultdict
from pathlib import Path

ARREL = Path(__file__).resolve().parent.parent
RAW = ARREL / 'data' / 'raw' / 'migration'
PROCESSED = ARREL / 'data' / 'processed'
# conjunt -> nom de la columna de la 1a dimensió (on va / d'on ve)
CONJUNTS = {'emigracions_externes': 'destinacio', 'immigracions_externes': 'procedencia'}

def llegeix(path):
    txt = open(path, encoding='utf-8-sig').read()
    delim = ';' if txt.count(';') > txt.count(',') else ','
    return list(csv.reader(txt.splitlines(), delimiter=delim))

def num(x):
    x = x.strip()
    if x in ('', '-', '..'):
        return None
    if x.count(',') == 1 and x.count('.'):   # format 1.234,5
        x = x.replace('.', '').replace(',', '.')
    return float(x)

def processa(path):
    rows = llegeix(path)
    m = re.search(r'(19|20)\d{2}', ' '.join(' '.join(r) for r in rows[:3])) or re.search(r'(19|20)\d{2}', os.path.basename(path))
    any_ = int(m.group(0))
    h = next(i for i, r in enumerate(rows) if any('Homes' in c for c in r))
    cap = rows[h]
    out = []
    for r in rows[h+1:]:
        if not r or not r[0].strip():
            continue
        dest = r[0].strip()
        if dest.lower() == 'total':          # els totals es poden recalcular
            continue
        for j in range(1, len(cap)):
            nac, _, sexe = cap[j].partition('. ')
            if nac.strip() == 'Total' or sexe.strip() == 'Total' or not sexe:
                continue                      # evita doble comptatge
            out.append((any_, dest, nac.strip(), sexe.strip(), num(r[j])))
    return any_, out

def uneix(conjunt, nom_col):
    entrada, sortida = RAW / conjunt, PROCESSED / f'{conjunt}.csv'
    fitxers = sorted(glob.glob(str(entrada / '*.csv')))
    if not fitxers:
        print(f'[{conjunt}] cap CSV a {entrada}, s\'omet')
        return
    tot, cats = [], defaultdict(set)
    for f in fitxers:
        a, o = processa(f)
        tot += o
        for x in o: cats[a].add(x[1])
    tot.sort()
    sortida.parent.mkdir(parents=True, exist_ok=True)
    with open(sortida, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['any', nom_col, 'nacionalitat', 'sexe', 'valor']); w.writerows(tot)
    base = cats[min(cats)]
    for a in sorted(cats):
        if cats[a] != base:
            print(f'[{conjunt}] ⚠ {a}: categories diferents  +{sorted(cats[a]-base)}  -{sorted(base-cats[a])}')
    print(f'[{conjunt}] {len(fitxers)} fitxers, {len(tot)} files -> {sortida}')

if __name__ == '__main__':
    for conjunt, nom_col in CONJUNTS.items():
        uneix(conjunt, nom_col)