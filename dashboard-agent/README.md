# Dashboard Agent

Agent IA qui transforme un fichier de données (CSV, Excel, JSON, Parquet) en dashboard HTML :
il **choisit les KPI** pertinents pour le métier et **le bon visuel pour chaque question**,
puis génère une page autonome (mode clair/sombre, responsive, vue tableau pour chaque graphique).

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

python -m dashboard_agent mes_ventes.xlsx --objectif "suivi mensuel pour la direction commerciale"
# -> mes_ventes.dashboard.html  +  mes_ventes.dashboard.spec.json
```

## Comment ça marche

```
fichier ──► loader (types, dates, nombres « 1 234,56 ») ──► profil des colonnes
                                                              │
                         ┌────────────────────────────────────┘
                         ▼
                 Claude (agent, outils)
                 ├─ get_column_details   explorer une colonne
                 ├─ test_aggregation     vérifier un KPI sur les vraies données
                 └─ submit_dashboard     soumettre la spec (validée, sinon erreurs renvoyées)
                         │
                         ▼
            spec JSON (KPI + visuels, aucun chiffre) ──► engine (pandas) ──► render (HTML + Chart.js)
```

Principe clé : **l'IA décide, le code calcule.** Le modèle ne voit qu'un profil des données
(types, statistiques, valeurs fréquentes, 5 lignes d'exemple) et produit une *spécification* ;
tous les chiffres affichés sont recalculés par pandas. Un chiffre halluciné ne peut donc pas
se retrouver dans un KPI.

### Ce que l'agent sait faire
- Identifier le domaine, le grain d'une ligne, les mesures, dimensions et l'axe temporel.
- Construire de vrais KPI : ratios d'agrégats (taux de marge = Σ marge / Σ CA, panier moyen =
  Σ CA / nb distinct de commandes), comptage d'entités en `count_distinct`, moyennes pour ce qui
  n'est pas additif, sens « plus haut = mieux » ou non (coûts, délais).
- Évolution vs période précédente + sparkline ; **la période en cours (mois incomplet) est
  exclue** pour ne pas afficher une fausse chute.
- Choisir le visuel selon la question : courbe (temps), barres triées (classement),
  barres empilées (composition), donut (≤ 5 parts seulement), histogramme (distribution),
  nuage de points (relation), heatmap (croisement), tableau (détail). Les catégories au-delà
  du top N sont regroupées dans « Autres ».
- Se corriger : si la spec référence une colonne absente ou une agrégation incohérente
  (somme d'un texte, ligne sans axe temporel…), l'erreur lui est renvoyée et il resoumet.

Les règles métier et de dataviz sont dans [`dashboard_agent/prompts.py`](dashboard_agent/prompts.py) :
c'est le fichier à adapter pour votre contexte (vocabulaire, KPI maison, charte).

## Options

| Option | Rôle |
|---|---|
| `--objectif "..."` | Question métier / public visé : c'est ce qui oriente le plus le choix des KPI |
| `--sheet NOM` | Feuille Excel à lire |
| `--spec fichier.spec.json` | Re-générer le HTML depuis une spec (par ex. retouchée à la main) **sans appel à l'IA** |
| `--profile` | Afficher seulement le profil des colonnes détecté |
| `--model` | Modèle Claude (défaut `claude-opus-5-5`) |
| `--effort` | `low` … `max` (défaut `high`) : profondeur d'analyse vs coût |

La spec JSON est sauvegardée à chaque exécution : vous pouvez modifier un titre, retirer un
graphique ou changer un type de visuel, puis relancer avec `--spec`.

## Exemple fourni

```bash
python examples/generate_sample.py                     # régénère examples/ventes.csv
python -m dashboard_agent examples/ventes.csv \
       --spec examples/ventes.spec.json -o demo.html    # rendu sans clé API
```

## Utilisation en Python

```python
from dashboard_agent.agent import DashboardAgent
from dashboard_agent.engine import compute_dashboard
from dashboard_agent.loader import load_table
from dashboard_agent.render import write_html

df = load_table("rh_effectifs.xlsx")
result = DashboardAgent(on_event=print).run(df, "rh_effectifs.xlsx", objective="pilotage RH trimestriel")
write_html(compute_dashboard(df, result.spec), "rh.html")
```

## Tests

```bash
python -m pytest -q   # hors-ligne : parsing, calculs, validation, boucle agent avec un faux client
```

## Notes techniques
- API Claude via le SDK officiel `anthropic`, réponses en streaming, réflexion adaptative,
  mise en cache du prompt. Le paramètre `fallbacks: "default"` (bêta) relance automatiquement
  sur un autre modèle si un filtre de sécurité refuse une requête à tort.
- Le HTML charge Chart.js 4.4.1 depuis cdnjs ; il faut donc une connexion internet pour
  afficher les graphiques (KPI et tableaux s'affichent sans).
- Palette catégorielle validée pour le daltonisme, mode sombre dédié, formats de nombres et de
  dates localisés (`locale`, `currency` dans la spec).
