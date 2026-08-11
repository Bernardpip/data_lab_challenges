"""Agrégations métier — une fonction par question du défi.

C'est ici que se joue la note d'analyse (C2), et nulle part ailleurs : **les
vues ne calculent rien, les graphes ne calculent rien**. Une vue qui ferait un
`groupby` rendrait son chiffre invérifiable et non réutilisable par le rapport
PowerPoint — qui doit produire exactement les mêmes valeurs que l'écran.

Chaque fonction reçoit un cadre DÉJÀ filtré et renvoie soit un DataFrame prêt
à tracer, soit un dictionnaire de faits que la vue se contente d'afficher.
"""

# pyrefly: ignore [missing-import]
import pandas as pd    # noqa: F401  (utilisé dès la première agrégation)

from utils.clean import NON_RENSEIGNE    # noqa: F401


# def par_region(cadre):
#     """Effectifs par région, du plus grand au plus petit.
#
#     `NON_RENSEIGNE` est CONSERVÉ dans le décompte et trié comme les autres :
#     l'écarter ferait passer une lacune de collecte pour une absence de fait.
#     """
#
#     compte = (
#         cadre.groupby("region", dropna=False)
#         .size().reset_index(name="effectif")
#         .sort_values("effectif", ascending=False)
#     )
#
#     return compte
#
#
# def concentration(cadre):
#     """Les faits que la vue d'ensemble affiche, calculés une seule fois."""
#
#     compte = par_region(cadre)
#     total = int(compte["effectif"].sum())
#
#     return {
#         "total": total,
#         "tete": compte.iloc[0]["region"],
#         "part_tete": 100 * compte.iloc[0]["effectif"] / total if total else 0,
#     }
