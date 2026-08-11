# socle/charts/ — la forme découle du job

```python
from socle import charts
from socle.charts import maps

charts.bar_h(cadre, "region", "effectif")
charts.table_twin(cadre)          # obligatoire, sous chaque graphe
```

| Fichier | Contenu |
|---|---|
| `figures.py` | les 9 formes autorisées (Plotly) |
| `maps.py` | 2 formes de carte (Folium) |

## Choisir sa forme

| Job | Forme | Couleur |
|---|---|---|
| Magnitude, catégories nominales | `bar_h` | **une seule** teinte |
| Magnitude, catégories ordonnées | `column_series` | une seule teinte |
| Magnitude sur grille | `heatmap` | rampe séquentielle + valeurs écrites |
| Part-à-tout | `bar_stacked_h` | slots catégoriels, 2px de surface entre segments |
| Évolution | `line_series` | 1 slot par entité (`slot=` figé si un filtre peut en retirer) |
| Deux échelles différentes | `line_indexed` (base 100) | **jamais deux axes Y** |
| Polarité | `diverging_bar` | 2 pôles + gris neutre au milieu |
| Relation | `scatter_fit` | 1 teinte, droite sur la **plage observée** seulement |
| Identité située | `maps.points` | 1 teinte |
| Magnitude située | `maps.disques` | 1 teinte, aire ∝ valeur |

Un chiffre seul n'est **pas** un graphe : `ui.stat_tiles` ou `ui.hero`.

## `table_twin()` est obligatoire

Aucune valeur ne doit être accessible par la seule couleur. Le jumeau tableau
sert autant le lecteur daltonien que celui qui veut le chiffre exact — et il
coûte une ligne.

## Deux pièges retrouvés à la main

**Le rayon d'un disque suit la racine carrée de la valeur**, jamais la valeur.
L'œil lit l'aire : un rayon linéaire gonfle le premier point au carré de son
avance et écrase tous les autres.

**`slot=` se fige sur une série qu'un filtre peut retirer.** Sans cela,
masquer la première repeint toutes les suivantes, et la couleur suit le rang
au lieu de l'entité.
