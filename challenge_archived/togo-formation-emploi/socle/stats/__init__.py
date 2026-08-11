"""Économétrie — et l'obligation de publier ce qui ne conclut pas.

    from socle.stats import econometrie as eco
    modele = eco.ols(x, y)     # -> n, pente, p, r2, ic95…

`ols()` renvoie TOUJOURS son effectif, sa p-value, son R² et son intervalle de
confiance. Un modèle non significatif s'affiche comme tel : le retirer de la
page donnerait au reste une solidité qu'il n'a pas.
"""

from socle.stats import econometrie

__all__ = ["econometrie"]
