# Migratory Movements in Catalonia

Exploratory analysis and visualization of **external migration in Catalonia** and how it relates to
demography, income, unemployment and education. The project cross-references open data from
[Idescat](https://www.idescat.cat) (the Statistical Institute of Catalonia) and the Catalan education
data to produce static figures, maps and animated GIFs.

Repository originally named `Projecte_Big_Data` · Authors: [Jordi Villalbi](https://github.com/JordiVillalbi)
, [Maria Salceda](https://github.com/mariasalceda), [Carles López-Arenas](https://github.com/carleslopez-11), [Joan Lampurlanés](https://github.com/joan-24)
## Questions explored

- Where do people who move to (and out of) Catalonia come from, and how has the **net flow** by world region evolved since 2005?
- Which **comarques** (counties) gain or lose population through external migration, and how does that change over time?
- Is net migration related to **income** (household disposable income per inhabitant, personal income tax base) and to **unemployment**?
- What is the **age and sex profile** of migrants compared with the resident population?
- How has the number of **foreign students** in compulsory secondary education (ESO) evolved, and how do 4th-year ESO results in Catalan and mathematics differ by gender?

## Start here

1. Set up the environment: [Environment setup](#environment-setup).
2. Browse the results in [`results/figures/`](results/figures/).
3. Re-run the pipeline following [Reproducing the analysis](#reproducing-the-analysis).

## Repository

| Folder / file | Contents |
|---|---|
| `data/raw/` | Datasets as downloaded from the sources (some via scraping scripts) |
| `data/processed/` | Cleaned and merged tables produced by the scripts |
| `notebooks` | Notebooks for image creation and data processing |
| `scripts/Data_processing/` | Downloading, scraping, cleaning and merging |
| `scripts/Image_creation/` | Static figures (Matplotlib, Plotly) |
| `scripts/Gif_creation/` | Animated maps and charts |
| `scripts/analitzar_demografia.py` | Age/sex analysis of migration and population pyramids |
| `results/figures/` | Generated PNG and GIF files |
| `environment.yml` | Conda environment (`migration-catalonia`) |
| `LICENSE` | GPL-3.0 |

Data folders are organised by theme: `migration`, `demografia`, `economics`, `education`, `social`
(`healthcare` is reserved but empty).

## Data

All sources are Catalan/Spanish official statistics. Every file keeps the source note in its header where Idescat provides one.

| Theme | Files (in `data/raw/` unless noted) | Coverage | Source |
|---|---|---|---|
| External immigration and emigration | `migration/immigracions_externes/`, `migration/emigracions_externes/` (one CSV per year); long-format versions in `data/processed/migration/` | 2005–2024, by region of origin/destination, nationality and sex | Idescat, from the INE residential variation / migration statistics |
| Net external migration by comarca | `migration/saldo_extern_comarques.csv` | 2002–2022, 42 comarques, with population and rate per 1,000 inhabitants | Idescat (migration and population indicators) |
| All migration types by comarca | `migration/migracions_totes_comarques.csv` | Internal, Spanish and external flows | Idescat |
| Migration and population by age | `demografia/migracions_idescat_tots_els_anys.csv`, `demografia/poblacio_idescat_agrupada.csv`; result in `data/processed/demografia/estudi_impacte_migracions.csv` | Migration 2005 onwards, population 2012 onwards, grouped by age band and sex | Idescat |
| Natural growth and foreign population | `demografia/creixement_nat_pob.csv`, `demografia/estructura_edat.csv` | Catalonia / Spain; foreign population 2015–2025 | Idescat (Padró continu, Census) |
| Household income per inhabitant (RFDB) | `economics/rfdb_per_habitant_comarques_2005_2023.csv` | 2005–2023, by comarca | Idescat |
| Personal income tax (IRPF) | `economics/irpf_2000_2024.csv` | 2000–2024, Catalonia | Idescat |
| Employment rate | `economics/taxa_ocupacio.csv` | Catalonia, Spain, EU | Idescat (EPA) and Eurostat |
| Unemployment by comarca | `data/processed/social/atur_comarques.csv` | 2015–2025, 43 comarques, by sex | Idescat |
| Foreign students per classroom raw data | `education/alumnes_estrangers_per_aula/` (one file per school year) | 2015/16–2024/25 | Catalan education department enrolment files |
| Foreign students per classroom processed data | `data/processed/education/dades_netes_estrangers_eso.csv` | 2012/13–2024/25; single-file data | Catalan education department enrolment files |
| Early school leaving | `education/abandonament_prematur.csv` | Catalonia / Spain / EU | Idescat, Eurostat |
| 4th-year ESO raw results  | `resultats_academics_quart_eso_raw.zip` | Catalonia / Spain / EU | Idescat, Eurostat |
| 4th-year ESO processed results v1 | `data/processed/education/resultats_academics__quart_eso_processat.csv` | 2012–2025; Catalan, reading, writing and maths scores by gender | Catalan education department |
| 4th-year ESO processed results v2 | `data/processed/education/resultats_academics_quart_eso_processat_nou.csv` | 2012–2025; Catalan, reading, writing and maths scores by nature (public or private school) and number of inhabitants | Catalan education department |


> Check the terms of use of each original source before reusing the data.

## Scripts

Scripts are grouped by stage; run the data processing stage first.

### 1. Data processing (`scripts/Data_processing/`)

| Script | What it does |
|---|---|
| `join_csv.py` | Merges the yearly Idescat immigration/emigration CSVs into one long table |
| `migration_with_population_comarques.py` | Downloads net external migration and population by comarca and writes `saldo_extern_comarques.csv` |
| `DATA_atur_comarques.py` | Scrapes Idescat to build `atur_comarques.csv` |
| `composicio_edat_sexe.py` | Downloads household income (RFDB) per comarca from Idescat |
| `dades_edat_pob_total.py` | Downloads population by age and regroups it into the age bands used for migration |
| `../analitzar_demografia.py` | Merges migration and population by age, computes net rates and an efficiency index, and draws yearly migration pyramids |

### 2. Static figures (`scripts/Image_creation/`)

| Script | Output |
|---|---|
| `time_series_net_flux.py`, `time_series_net_flux_2.0.py` | Net migration flow by region of origin/destination (`flux_migratori_net_regions`, `net_flux_stacked_regions`) |
| `irpf_vs_net_flux.py` | Net flow against income-tax base per taxpayer (`net_flux_and_base_imposable`) |
| `plot_mapa_catalunya.py` | Choropleth of net external migration rate for four periods (`mapa_saldo_extern_4periodes`) |
| `rfdb_per_inhabitant_comarca_any.py` | Income vs migration quadrant chart for a chosen year (`rfdb_vs_migration_2022`) |
| `rfdb_per_inhabitant_all_years.py` | Income vs migration evolution charts, including person-icon markers (`rfdb_evolution_*`, `migration_evolution_*`) |
| `sankey_diagram_migration.py` | Interactive Plotly Sankey: origins → Catalonia → destinations |


### 3. Animations (`scripts/Gif_creation/`)

| Script | Output |
|---|---|
| `gif_migracio_catalunya.py` | Annual choropleth of net external migration by comarca, 2002–2022 |
| `Bivariant_map_Catalunya.py` | Bivariate map of migration × unemployment (terciles) |
| `rfdb_migration_comarques_GIF.py` | Income vs migration scatter animated by year |

## Notebooks

| Script | Output |
|---|---|
| `alumnes_aula_tendencia.ipynb` | Evolution of the number of foreign students in Catalan classes (`foreign_students_evolution`) |
| `alumnes_municipis_menors.ipynb` | 4th-year ESO results averaged across public Catalan schools in villages with 100000 inhabitants or less (`evolucio_4t_eso`) |
| `alumnes_per_aula.ipynb` | Counts foreign pupils in compulsory secondary education per school year |
| `analisi_4t_eso.ipynb` | 4th-year ESO results by gender and averaged, across all Catalan schools (`evolucio_4t_eso`) |
| `comparativa_4t_eso.ipynb` | Puts together the averaged results for all Catalan schools and public schools in villages with 100000 inhabitants or less. Also, plots net migratory flux in Catalonia and compares it with the evolution of the number of foreign students in Catalan classes, and with the rate in which this evolution happens.  |

## Results

Generated files live in [`results/figures/`](results/figures/):

- Net migration maps by comarca (4-period panel and annual GIF) and a bivariate migration–unemployment map
- Net migration flow by region of origin/destination (time series and stacked)
- Income (RFDB, IRPF) against migration, static and animated
- Migration pyramids by age and sex, 2012–2026
- Foreign students in ESO and its comparison with migratory flux, and 4th-year ESO results by gender and gender-free

## Environment setup

Python 3.12 with conda ([`environment.yml`](environment.yml)):

```console
git clone https://github.com/JordiVillalbi/migratory-movements-catalonia.git
cd migratory-movements-catalonia
conda env create -f environment.yml
conda activate migration-catalonia
python -m ipykernel install --user --name migration-catalonia
jupyter lab
```

Main packages: `pandas`, `numpy`, `geopandas`, `shapely`, `pyproj`, `fiona`, `matplotlib`, `seaborn`,
`plotly`, `pillow`, `requests`, `beautifulsoup4`, `jupyterlab`.

## Reproducing the analysis

1. Create the environment (above). An internet connection is needed: several scripts download data from Idescat, and the map scripts fetch comarca boundaries from an online ArcGIS service.
2. Run the scripts in `scripts/Data_processing/`, then `scripts/analitzar_demografia.py`.
3. Run the scripts in `scripts/Image_creation/` and `scripts/Gif_creation/`.

Most scripts locate the project root from their own path, but the three scripts in `Gif_creation/`
read paths relative to the working directory, so run them **from the repository root**
(`python scripts/Gif_creation/Bivariant_map_Catalunya.py`). The notebooks expect to be opened from
their own folder.

## Notes and limitations

- 4th-year ESO results are provided only as a processed file (the raw files are not in the repository).
- The 2021 data point has a source change at the INE, so figures treat 2021–2022 as a separate period.
- Net migration by comarca excludes the Lluçanès (created in 2023), while unemployment includes it.
- Annotation marks from Idescat (e.g. provisional values) are stripped during cleaning.

## AI disclaimer

Parts of the code, comments and documentation (including this README) were written or revised with the help of AI tools, namely, Claude Sonnet 5.5, Gemini Hydrogen and ChatGPT-6. All content has been reviewed by the authors.

## License

Code released under the [GNU General Public License v3.0](LICENSE). Datasets keep their own licences.
