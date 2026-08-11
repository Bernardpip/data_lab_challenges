"""Les neuf formes autorisées, plus les cartes.

Le module se consomme comme dans le pilote :

    from socle import charts
    charts.bar_h(df, "region", "effectif")

La forme découle du JOB, jamais de l'envie :

    magnitude, catégories nominales   → bar_h              une seule teinte
    magnitude, catégories ordonnées   → column_series      une seule teinte
    magnitude sur grille              → heatmap            rampe 1 teinte
    part-à-tout                       → bar_stacked_h      slots catégoriels
    évolution                         → line_series        1 slot par entité
    deux échelles différentes         → line_indexed       jamais 2 axes Y
    polarité                          → diverging_bar      2 pôles + gris
    relation                          → scatter_fit        plage observée
    identité située                   → maps.points
    magnitude située                  → maps.disques

`table_twin()` accompagne OBLIGATOIREMENT tout graphe : aucune valeur ne doit
être accessible par la seule couleur.
"""

from socle.charts.figures import (
    anneau,
    demi_anneau,
    petits_multiples,
    pentes_appariees,
    sucette_h,
    table_twin,
    bar_h,
    column_series,
    heatmap,
    bar_stacked_h,
    line_series,
    line_indexed,
    diverging_bar,
    scatter_fit,
)

__all__ = [
    "anneau",
    "demi_anneau",
    "petits_multiples",
    "pentes_appariees",
    "sucette_h",
    "table_twin",
    "bar_h",
    "column_series",
    "heatmap",
    "bar_stacked_h",
    "line_series",
    "line_indexed",
    "diverging_bar",
    "scatter_fit",
]
