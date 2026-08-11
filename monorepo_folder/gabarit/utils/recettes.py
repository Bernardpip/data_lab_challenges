"""Croisements multi-fichiers — chacun déclare ses ingrédients et sa solidité.

Une « recette » est un croisement que les données AUTORISENT. Deux règles la
gouvernent, et elles sont la moitié de la note d'analyse :

  · **aucun croisement que les données n'autorisent pas.** Un indicateur
    national n'entre jamais dans un score régional : le résultat aurait l'air
    d'une donnée alors qu'il serait une invention ;

  · **chaque recette déclare ses ingrédients, sa clé de jointure et son nombre
    d'observations**, avec un seuil de solidité qui lui est PROPRE. Dix années
    ne valent pas cinq régions : un seuil unique pour tout le tableau de bord
    validerait des croisements creux et en rejetterait de bons.

La jointure est INTERNE et le résultat n'est jamais complété : une année
absente d'un des deux jeux disparaît du croisement, elle ne s'invente pas.
"""

# pyrefly: ignore [missing-import]
import pandas as pd    # noqa: F401

from socle.i18n.traduction import t    # noqa: F401


# def croisement_xxx(gauche, droite, seuil=3):
#     """<Ce que SEUL ce croisement permet d'établir>.
#
#     Jointure INTERNE sur l'année — aucune année manquante n'est remplie.
#     """
#
#     tr = t("recettes")
#     fusion = pd.merge(gauche, droite, on="annee", how="inner").dropna()
#
#     if len(fusion) < seuil:
#         # Une tendance sur deux points n'existe pas : mieux vaut ne rien
#         # afficher que d'afficher une droite qui n'a pas de sens.
#         return None
#
#     return {
#         "ingredients": [tr("ing_gauche"), tr("ing_droite")],
#         "cle": tr("cle_annee"),
#         "observations": len(fusion),
#         "seuil": seuil,
#         "periode": (int(fusion["annee"].min()), int(fusion["annee"].max())),
#         "table": fusion,
#         # + les variations déjà calculées, pour que la vue n'ait rien à faire
#     }
