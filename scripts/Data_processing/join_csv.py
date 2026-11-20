#!/usr/bin/env python3
"""Uneix els CSV anuals d'Idescat (Emigracions externes) en una sola taula LLARGA.
Ús:  python3 unir_csv.py carpeta_amb_csv sortida.csv
Accepta fitxers .csv amb coma o punt i coma. L'any s'extreu de la línia
'Catalunya. AAAA' (o, si falla, del nom del fitxer)."""
import csv
import glob
import os
import re
import sys
from collections import defaultdict


def llegeix(path):
    txt = open(path, encoding='utf-8-sig').read()
    delim = ';' if txt.count(';') > txt.count(',') else ','
    return list(csv.reader(txt.splitlines(), delimiter=delim))

def num(x):
    x = x.strip().replace('.', '').replace(',', '.') if x.count(',') == 1 and x.count('.') else x.strip()
    return float(x) if x not in ('', '-', '..') else None

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
    carpeta, sortida = sys.argv[1], sys.argv[2]
    fitxers = sorted(glob.glob(os.path.join(carpeta, '*.csv')))
    tot, destins = [], defaultdict(set)
    for f in fitxers:
        a, o = processa(f)
        tot += o
        for x in o: destins[a].add(x[1])
    tot.sort()
    with open(sortida, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['any', 'destinacio', 'nacionalitat', 'sexe', 'valor']); w.writerows(tot)
    # Control de coherència: categories de destinació per any
    base = destins[min(destins)]
    for a in sorted(destins):
        if destins[a] != base:
            print(f'⚠ {a}: categories diferents  +{sorted(destins[a]-base)}  -{sorted(base-destins[a])}')
    print(f'{len(fitxers)} fitxers, {len(tot)} files -> {sortida}')