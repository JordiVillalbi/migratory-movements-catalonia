
import pandas as pd
import requests
from io import StringIO
from pathlib import Path

# URL de descàrrega de totes les comarques
url = "https://www.idescat.cat/pub/?f=ssv&geo=com&id=mm&n=5489"

# Descarregar les dades
response = requests.get(url)
response.raise_for_status()

# Llegir el CSV
# Les primeres 6 línies són informació introductòria
df = pd.read_csv(
    StringIO(response.text),
    sep=";",
    skiprows=6,
    encoding="utf-8"
)

# Crear carpeta de destinació si no existeix
Path("data").mkdir(exist_ok=True)

# Exportar
df.to_csv(
    "data/raw/migration/migracions_totes_comarques.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Descàrrega completada!")
print("Dimensions:", df.shape)
print(df.head())
print("Columnes:", df.columns.tolist())
