# Uneix els CSV anuals d'Idescat en un sol CSV per conjunt (emigracions / immigracions)
import csv
import re
from pathlib import Path

arrel = Path(__file__).resolve().parent.parent
conjunts = {"emigracions_externes": "destinacio", "immigracions_externes": "procedencia"}

for nom, col in conjunts.items():
    carpeta = arrel / "data" / "raw" / "migration" / nom
    files = []

    for fitxer in sorted(carpeta.glob("*.csv")):
        text = fitxer.read_text(encoding="utf-8-sig")
        sep = ";" if text.count(";") > text.count(",") else ","
        taula = list(csv.reader(text.splitlines(), delimiter=sep))

        any_ = int(re.search(r"(19|20)\d{2}", " ".join(taula[1])).group(0))  # "Catalunya. 2005"
        cap = next(i for i, f in enumerate(taula) if "Espanyola. Homes" in f)

        for fila in taula[cap + 1:]:
            if not fila or fila[0] == "Total":
                continue
            for j in range(1, len(fila)):
                nacionalitat, _, sexe = taula[cap][j].partition(". ")
                if sexe in ("", "Total"):
                    continue
                files.append([any_, fila[0], nacionalitat, sexe, float(fila[j])])

    files.sort()
    sortida = arrel / "data" / "processed" / f"{nom}.csv"
    sortida.parent.mkdir(parents=True, exist_ok=True)
    with open(sortida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["any", col, "nacionalitat", "sexe", "valor"])
        w.writerows(files)
    print(nom, len(files), "files")