# socle/stats/ — économétrie

```python
from socle.stats import econometrie as eco

modele = eco.ols(x, y)          # n, pente, p, r2, ic95…
eco.elasticite(inscriptions, depenses)
eco.rupture_de_tendance(serie, annee_rupture=2000)
eco.concentration(effectifs)    # indice de concentration
```

| Fonction | Ce qu'elle établit |
|---|---|
| `ols` | régression linéaire, avec tous ses diagnostics |
| `tendance_temporelle` | pente annuelle d'une série |
| `elasticite` | variation relative d'une grandeur par rapport à une autre |
| `correlation` | coefficient et significativité |
| `rupture_de_tendance` | avant/après une année charnière |
| `concentration` | à quel point une distribution est concentrée |
| `execution_vs_montant` | taux d'exécution rapporté au montant voté |

## La règle qui justifie ce module

**`ols()` renvoie toujours son effectif, sa p-value, son R² et son intervalle
de confiance à 95 %.** Un modèle non significatif s'affiche comme tel.

Le retirer de la page donnerait au reste une solidité qu'il n'a pas : le
lecteur ne verrait que les relations qui « marchent » et croirait à une
démonstration là où il n'y a qu'une sélection. Un résultat qui ne conclut pas
est un résultat.

Corollaire côté vue : sous trois points, aucune tendance n'est tracée — une
droite entre deux mesures n'établit rien. `ui.filters.periode` signale en
rouge, série par série, quand le filtre descend sous ce seuil.
