import os
import re
import urllib.request

import pandas as pd

# 1. Ruta exacta del teu projecte on es guardarà el fitxer
carpeta_desti = r"data/raw/economics"
os.makedirs(carpeta_desti, exist_ok=True)
ruta_fitxer = os.path.join(carpeta_desti, "rfdb_per_inhabitant_2005_2009.csv")


def trobar_codis_taula_rfdb():
  """Llegeix l'índex HTML de l'Idescat per trobar els codis 'n=' reals de RFDB per comarques."""
  codis = []
  urls_index = [
      "https://www.idescat.cat/pub/?id=rfdbc",
      "https://www.idescat.cat/pub/?id=aec&t=201100",
      "https://www.idescat.cat/pub/?id=aec&t=200900",
  ]
  for u in urls_index:
    try:
      req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
      html = urllib.request.urlopen(req, timeout=15).read().decode(
          "utf-8", errors="ignore"
      )
      # Busquem tots els enllaços tipus ?id=rfdbc&n=XXXX o ?id=aec&n=XXXX
      matches = re.findall(
          r'href="[^"]*\?id=(rfdbc|aec)[^"]*n=(\d+)[^"]*"[^>]*>(.*?)</a>',
          html,
          re.IGNORECASE | re.DOTALL,
      )
      for pub_id, n_code, text in matches:
        text_net = re.sub(r"<[^>]+>", "", text).lower()
        if ("renda" in text_net or "rfdb" in text_net) and (
            "comarques" in text_net or "comarca" in text_net
        ):
          codis.append((pub_id, n_code, text_net.strip()))
    except Exception:
      continue
  # Eliminem duplicats mantenint l'ordre
  vistos = set()
  unics = []
  for item in codis:
    if (item[0], item[1]) not in vistos:
      vistos.add((item[0], item[1]))
      unics.append(item)
  return unics


print("Cercant els codis reals de taula (n=) a l'Idescat...")
codis_trobats = trobar_codis_taula_rfdb()
for pub_id, n_code, desc in codis_trobats:
  print(f"  -> Trobat: id={pub_id} | n={n_code} ({desc[:60]}...)")

anys = range(2005, 2010)
taules = []
columnes = [
    "Comarca",
    "RFDB_milers_euros",
    "RFDB_per_habitant_euros",
    "Index_Catalunya_100",
]

print("\nDescarregant dades de RFDB per comarca...")

for any_actual in anys:
  descarregat = False

  for pub_id, n_code, _ in codis_trobats:
    # A l'Anuari (aec), l'edició sol ser 2 anys posterior a la dada
    t_anys = (
        [f"{any_actual}00"]
        if pub_id == "rfdbc"
        else [f"{any_actual+2}00", f"{any_actual+1}00"]
    )

    for t_val in t_anys:
      url = f"https://www.idescat.cat/pub/?id={pub_id}&n={n_code}&t={t_val}&f=ssv"
      try:
        # Llegim sense saltar files inicialment per detectar on comencen les comarques
        df_raw = pd.read_csv(url, sep=";", header=None, on_bad_lines="skip")

        # Busquem la fila on apareix "Alt Camp" (primera comarca alfabètica) per tallar la capçalera exacta
        idx_inici = df_raw[
            df_raw[0].astype(str).str.contains("Alt Camp", na=False)
        ].index
        if len(idx_inici) == 0:
          continue

        df = df_raw.iloc[idx_inici[0] :].copy()

        if df.shape[1] >= 4:
          df = df.iloc[:, :4]
          df.columns = columnes

          df = df.dropna(subset=["Comarca"])
          df = df[
              ~df["Comarca"]
              .astype(str)
              .str.contains("Font:|Nota:|Catalunya|Total", na=False)
          ]

          # Verifiquem que tinguem les ~41 comarques
          if len(df) >= 35:
            df.insert(0, "Any", any_actual)
            taules.append(df)
            print(
                f"✅ Any {any_actual} descarregat (id={pub_id}, n={n_code} -"
                f" {len(df)} comarques)."
            )
            descarregat = True
            break
      except Exception:
        continue
    if descarregat:
      break

# Guardem el CSV a la carpeta del teu projecte
if taules:
  df_final = pd.concat(taules, ignore_index=True)
  df_final = df_final[["Any", "Comarca", "RFDB_per_habitant_euros"]]
  df_final.to_csv(ruta_fitxer, index=False, sep=";", encoding="utf-8-sig")
  print(f"\n🎉 Fet! Fitxer guardat correctament a:\n{ruta_fitxer}")
else:
  print("\n❌ No s'han trobat dades del 2005–2009 amb aquests codis.")