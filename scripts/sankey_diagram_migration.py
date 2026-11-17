import pandas as pd
import plotly.graph_objects as go

df_emigracions = pd.read_csv(r"data/processed/emigracions_externes.csv")
df_immigracions = pd.read_csv(r"data/processed/immigracions_externes.csv")

imm_grup = df_immigracions.groupby("procedencia")["valor"].sum()
em_grup = df_emigracions.groupby("destinacio")["valor"].sum()

em_grup = em_grup.drop("Baixes per caducitat", errors="ignore")
imm_grup = imm_grup[imm_grup > 0].dropna()
em_grup = em_grup[em_grup > 0].dropna()

origens = list(imm_grup.index)
destinacions = list(em_grup.index)

nodes = origens + ["Catalunya"] + destinacions

idx_origen = {o: i for i, o in enumerate(origens)}
idx_catalunya = len(origens)
idx_desti = {d: len(origens) + 1 + i for i, d in enumerate(destinacions)}

x = [0.001] * len(origens) + [0.5] + [0.999] * len(destinacions)
y = (
    [(i + 0.5) / len(origens) for i in range(len(origens))]
    + [0.5]
    + [(i + 0.5) / len(destinacions) for i in range(len(destinacions))]
)

sources, targets, values = [], [], []

for proc, valor in imm_grup.items():
    sources.append(idx_origen[proc])
    targets.append(idx_catalunya)
    values.append(valor)

for dest, valor in em_grup.items():
    sources.append(idx_catalunya)
    targets.append(idx_desti[dest])
    values.append(valor)


fig = go.Figure(data=[go.Sankey(
    node=dict(
        label=nodes,
        x=x,
        y=y,
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
    ),
)])

fig.show()