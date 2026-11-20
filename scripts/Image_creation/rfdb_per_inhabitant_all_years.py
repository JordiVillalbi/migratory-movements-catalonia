from pathlib import Path as FilePath

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import ticker
from matplotlib.markers import MarkerStyle
from matplotlib.path import Path

ROOT_DIR = FilePath(__file__).resolve().parents[2]

# 1. Custom vector person-silhouette marker
def create_person_marker():
    theta = np.linspace(0, 2 * np.pi, 17)
    head_x = 0.22 * np.cos(theta)
    head_y = 0.62 + 0.22 * np.sin(theta)
    body_x = np.array([-0.42, -0.42, -0.28, 0.28, 0.42, 0.42, -0.42])
    body_y = np.array([-0.65,  0.10,  0.30, 0.30, 0.10, -0.65, -0.65])
    verts = np.vstack([
        np.column_stack([head_x, head_y]),
        np.column_stack([body_x, body_y])
    ])
    codes = (
        [Path.MOVETO] + [Path.LINETO] * (len(head_x) - 1) +
        [Path.MOVETO] + [Path.LINETO] * (len(body_x) - 2) + [Path.CLOSEPOLY]
    )
    return MarkerStyle(Path(verts, codes))

person_marker = create_person_marker()

# 2. Load files where data is stored
df_saldo = pd.read_csv(ROOT_DIR / 'data' / 'raw' / 'migration' / 'saldo_extern_comarques.csv')
df_rfdb = pd.read_csv(ROOT_DIR / 'data' / 'raw' / 'economics' / 'rfdb_per_habitant_comarques_2005_2023.csv')

merged = pd.merge(
    df_rfdb,
    df_saldo,
    left_on=['any', 'comarca'],
    right_on=['Any', 'Nom'],
    how='inner'
)

# 3. Group comarcas per year into the 4 population brackets
bins = [0, 5000, 30000, 100000, np.inf]
group_labels = [
    '< 5,000',
    '5,000 – 30,000',
    '30,000 – 100,000',
    '> 100,000'
]
merged['pop_group'] = pd.cut(
    merged['Poblacio'],
    bins=bins,
    labels=group_labels,
    right=False
)

# 4. Aggregate per year and population group (population-weighted averages)
def aggregate_group(g):
    total_pop = g['Poblacio'].sum()
    return pd.Series({
        'rfdb_per_habitant_euros': (g['rfdb_per_habitant_euros'] * g['Poblacio']).sum() / total_pop,
        'saldo_ext_per_mil': (g['Saldo_ext'].sum() / total_pop) * 1000,
        'total_pop': total_pop
    })

df_grouped = (
    merged.groupby(['any', 'pop_group'], observed=True)
    .apply(aggregate_group, include_groups=False)
    .reset_index()
    .sort_values(['pop_group', 'any'])
)

universal_colors = {
    '< 5,000':          '#7F7F7F',
    '5,000 – 30,000':   '#E69F00',
    '30,000 – 100,000': '#009E73',
    '> 100,000':        '#0072B2'
}

# --- ISOTYPE STEP CONFIGURATION ---
# 10.0 -> 10‰ = 1 person, 20‰ = 2 people, 30‰ = 3 people (change to 5.0 if rates are smaller)
STEP = 10.0

fig, ax = plt.subplots(figsize=(15, 8.8))

min_year, max_year = int(df_grouped['any'].min()), int(df_grouped['any'].max())
y_min, y_max = df_grouped['rfdb_per_habitant_euros'].min(), df_grouped['rfdb_per_habitant_euros'].max()
y_pad = (y_max - y_min) * 0.14
ax.set_xlim(min_year - 0.7, max_year + 0.7)
ax.set_ylim(y_min - y_pad, y_max + y_pad)

# Horizontal & vertical spacing for multi-person clusters so they never overlap neighboring years
icon_dx = 0.14
icon_dy = (y_max - y_min) * 0.018

for grp_name, color in universal_colors.items():
    sub = df_grouped[df_grouped['pop_group'] == grp_name].sort_values('any')
    if sub.empty:
        continue

    ax.plot(
        sub['any'],
        sub['rfdb_per_habitant_euros'],
        color=color,
        linewidth=1.6,
        alpha=0.45,
        zorder=2
    )

    for _, row in sub.iterrows():
        yr = row['any']
        rfdb = row['rfdb_per_habitant_euros']
        rate = row['saldo_ext_per_mil']
        is_neg = rate < 0

        # Round to nearest STEP (e.g., 10‰ -> 1 icon, 20‰ -> 2 icons)
        n_icons = int(round(abs(rate) / STEP))

        if n_icons == 0:
            # Near-zero rate (< half a STEP): subtle dot on the trendline
            ax.scatter([yr], [rfdb], s=28, color=color, alpha=0.75, zorder=3)
        else:
            # Arrange icons in neat rows of up to 3 people side-by-side
            for idx in range(n_icons):
                r_idx = idx // 3
                c_idx = idx % 3
                row_count = min(3, n_icons - r_idx * 3)
                x_off = (c_idx - (row_count - 1) / 2.0) * icon_dx
                y_off = r_idx * icon_dy

                ax.scatter(
                    [yr + x_off],
                    [rfdb + y_off],
                    s=155,
                    marker=person_marker,
                    facecolor='white' if is_neg else color,
                    edgecolor=color if is_neg else 'white',
                    linewidth=1.5 if is_neg else 0.7,
                    alpha=0.95,
                    zorder=4
                )

ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
ax.tick_params(axis='x', rotation=45)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,} €'))

# Bottom-right isotype legend
legend_handles = [
    plt.Line2D([0], [0], marker='o', linestyle='None', markerfacecolor='#666666', markeredgecolor='none',
               markersize=5, label=f'< {STEP/2:.0f} ‰ (Near zero)'),
    plt.Line2D([0], [0], marker=person_marker, linestyle='None', markerfacecolor='#555555', markeredgecolor='white',
               markersize=12, label=f'1 Person = +{STEP:.0f} ‰ (Inflow)'),
    plt.Line2D([0], [0], marker=person_marker, linestyle='None', markerfacecolor='white', markeredgecolor='#333333',
               markeredgewidth=1.4, markersize=12, label=f'1 Hollow Person = -{STEP:.0f} ‰ (Outflow)')
]
iso_legend = ax.legend(
    handles=legend_handles,
    title=f'Isotype Scale (1 Icon = {STEP:.0f} ‰)',
    loc='lower right',
    frameon=True,
    facecolor='white',
    edgecolor='#CCCCCC',
    labelspacing=1.15,
    borderpad=0.9,
    fontsize=9.5,
    title_fontsize=9.5
)
ax.add_artist(iso_legend)

# Top centered legend for the 4 population groups
color_handles = [
    plt.Line2D([0], [0], marker=person_marker, color=color, label=f'Pop. {grp_name}',
               markerfacecolor=color, markeredgecolor='white', markersize=12, linewidth=2)
    for grp_name, color in universal_colors.items()
]
ax.legend(
    handles=color_handles,
    title='Comarca Population Bracket',
    title_fontsize=10,
    loc='upper center',
    bbox_to_anchor=(0.5, 1.11),
    ncol=4,
    frameon=True,
    facecolor='white',
    edgecolor='#CCCCCC',
    fontsize=10
)

ax.set_title(
    f'Evolution of Disposable Income (RFDB) & Net External Migration Isotypes ({min_year}–{max_year})',
    fontsize=14.5,
    fontweight='bold',
    pad=52
)
ax.set_xlabel('Year', fontsize=11)
ax.set_ylabel('Gross Disposable Household Income — RFDB (€ per inhabitant)', fontsize=11)
ax.grid(True, linestyle=':', alpha=0.6)
ax.spines[['top', 'right']].set_visible(False)

plt.tight_layout()
ruta_figura = ROOT_DIR / 'results' / 'figures' / f'rfdb_evolution_isotypes_{min_year}_{max_year}.png'
ruta_figura.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(ruta_figura, dpi=300, bbox_inches='tight')
plt.show()