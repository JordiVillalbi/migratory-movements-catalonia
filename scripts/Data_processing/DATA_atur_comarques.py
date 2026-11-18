import csv
import re
import time

import requests
from bs4 import BeautifulSoup

URL = "https://www.idescat.cat/indicadors/"
PARAMS = {"id": "aec", "n": "15303"}  # fil=<número> es va afegint per comarca
OUTPUT = "data/processed/social/atur_comarques.csv"

# Ordre del desplegable de l'Idescat: fil=1 és Alt Camp ... fil=43 és Vallès Oriental
COMARQUES = [
    "Alt Camp", "Alt Empordà", "Alt Penedès", "Alt Urgell", "Alta Ribagorça",
    "Anoia", "Aran", "Bages", "Baix Camp", "Baix Ebre", "Baix Empordà",
    "Baix Llobregat", "Baix Penedès", "Barcelonès", "Berguedà", "Cerdanya",
    "Conca de Barberà", "Garraf", "Garrigues", "Garrotxa", "Gironès",
    "Lluçanès", "Maresme", "Moianès", "Montsià", "Noguera", "Osona",
    "Pallars Jussà", "Pallars Sobirà", "Pla d'Urgell", "Pla de l'Estany",
    "Priorat", "Ribera d'Ebre", "Ripollès", "Segarra", "Segrià", "Selva",
    "Solsonès", "Tarragonès", "Terra Alta", "Urgell", "Vallès Occidental",
    "Vallès Oriental",
]


def parse_num(text):
    """'1.228,1' -> 1228.1 ; '..' o buit -> None"""
    text = text.strip()
    if not text or text.startswith(".."):
        return None
    return float(text.replace(".", "").replace(",", "."))


def fmt(x):
    return "" if x is None else x


def scrape_comarca(session, fil):
    r = session.get(URL, params={**PARAMS, "fil": fil}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Comprovació: el títol de la taula ha d'acabar amb el nom de la comarca esperada
    nom = COMARQUES[fil - 1]
    caption = soup.find("caption")
    if caption and not caption.get_text(" ", strip=True).endswith(nom):
        print(f"  AVÍS: fil={fil} esperava '{nom}' però la taula diu "
              f"'{caption.get_text(' ', strip=True)[-30:]}'")

    # Agafem la taula que té les columnes Homes / Dones / Total
    taula = None
    for t in soup.find_all("table"):
        capcalera = t.get_text(" ", strip=True)
        if "Homes" in capcalera and "Dones" in capcalera:
            taula = t
            break
    if taula is None:
        raise RuntimeError(f"No he trobat la taula per fil={fil} ({nom})")

    files = []
    for tr in taula.find_all("tr"):
        cel = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
        # Només les files de dades: la primera cel·la és un any (4 dígits)
        if len(cel) >= 4 and re.fullmatch(r"\d{4}", cel[0]):
            any_ = int(cel[0])
            homes, dones, total = (parse_num(c) for c in cel[1:4])
            files.append((nom, any_, dones, homes, total))
    return files


def main():
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (script atur comarques)"

    total_files = 0
    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["comarca", "any", "dones", "homes", "total"])
        for fil in range(1, len(COMARQUES) + 1):
            print(f"[{fil}/{len(COMARQUES)}] {COMARQUES[fil - 1]}")
            for nom, any_, dones, homes, total in scrape_comarca(session, fil):
                w.writerow([nom, any_, fmt(dones), fmt(homes), fmt(total)])
                total_files += 1
            time.sleep(0.5)  # no saturem el servidor

    print(f"\nFet: {total_files} files desades a {OUTPUT}")


if __name__ == "__main__":
    main()