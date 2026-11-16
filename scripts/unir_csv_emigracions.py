
"""Uneix els CSV anuals d'Idescat (Emigracions externes) en una sola taula LLARGA.

Llegeix:  <arrel_projecte>/data/raw/migration/emigracions_externes/*.csv
Escriu:   <arrel_projecte>/data/processed/emigracions_externes.csv
L'arrel del projecte és la carpeta pare de 'scripts', així funciona des de qualsevol directori.
"""
import csv, re, sys, glob, os
from collections import defaultdict
from pathlib import Path

ARREL = Path(__file__).resolve().parent.parent
ENTRADA = ARREL / 'data' / 'raw' / 'migration' / 'emigracions_externes'
SORTIDA = ARREL / 'data' / 'processed' / 'emigracions_externes.csv'

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

if __name__ == '__main__':
    fitxers = sorted(glob.glob(str(ENTRADA / '*.csv')))
    if not fitxers:
        sys.exit(f'No s\'han trobat CSV a {ENTRADA}')
    tot, destins = [], defaultdict(set)
    for f in fitxers:
        a, o = processa(f)
        tot += o
        for x in o: destins[a].add(x[1])
    tot.sort()
    SORTIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SORTIDA, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['any', 'destinacio', 'nacionalitat', 'sexe', 'valor']); w.writerows(tot)
    base = destins[min(destins)]
    for a in sorted(destins):
        if destins[a] != base:
            print(f'⚠ {a}: categories diferents  +{sorted(destins[a]-base)}  -{sorted(base-destins[a])}')
    print(f'{len(fitxers)} fitxers, {len(tot)} files -> {SORTIDA}')