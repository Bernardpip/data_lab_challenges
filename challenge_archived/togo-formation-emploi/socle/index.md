# socle/ — la part qui ne connaît aucun corpus

Paquet importable, installé par `pip install -e ../monorepo_folder`. Extrait du
pilote *Adéquation formation-emploi au Togo*, il en garde les décisions
durement acquises — et rien de son sujet.

| Dossier | Ce qu'il porte | Lignes |
|---|---|---|
| [design/](design/index.md) | tokens, 862 l. de CSS, icônes lucide | 1 328 |
| [charts/](charts/index.md) | les 9 formes autorisées + 2 formes de carte | 713 |
| [ui/](ui/index.md) | cartes, tuiles, notes, barres de filtres | 440 |
| [shell/](shell/index.md) | route, sidebar, top bar, onglets, footer | 570 |
| [i18n/](i18n/index.md) | moteur de traduction + les textes du socle | 300 |
| [stats/](stats/index.md) | ols, élasticité, corrélation, concentration | 224 |
| [rapport/](rapport/index.md) | charte PPTX, objet `Langue`, montage bilingue | 280 |
| `audit.py` | prouver une absence au lieu de l'affirmer | 155 |

`audit.py` est seul à la racine parce qu'il ne dépend d'aucun des sept autres :
il travaille sur des DataFrames bruts, sans Streamlit ni Plotly.

## Ce qu'on n'y met jamais

Un chargement de données, une agrégation métier, une navigation, un texte
visible. Ces quatre choses se re-décident à chaque défi ; les loger ici
lierait le socle à un corpus et le rendrait inutilisable pour le suivant.

`outils/verifier_socle.py` refuse un module nommé `loader`, `clean`,
`analytics`, `recettes`, `profils` ou `perimetre`, ainsi que tout `.csv`,
`.geojson`, `.gpkg` ou `.xlsx` déposé ici.

## Trois interdits, coûteux à retrouver

- **aucun hex dans le corps du CSS** — les couleurs descendent de
  `design/tokens.py` en variables `--kg-*` ;
- **aucun texte visible dans le code** — tout passe par les tables JSON, et
  aucun chiffre n'est figé dans une phrase (il ne suivrait pas les filtres) ;
- **la forme d'un graphe découle de son job** — une couleur par barre sur des
  catégories nominales ré-encode la longueur ; deux axes Y se remplacent par
  `line_indexed` en base 100.

Le détail des signatures et le contrat i18n : [../docs/api-socle.md](../docs/api-socle.md).
