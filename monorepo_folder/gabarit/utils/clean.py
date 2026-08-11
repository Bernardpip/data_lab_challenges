"""Nettoyage — une fonction par jeu, un commentaire par anomalie traitée.

Le commentaire n'est pas de la politesse : il est la seule trace de ce qui a
été décidé sur les données. « Sans ça, les deux graphies de Lomé comptent
comme deux villes » se relit ; un `.str.title()` nu, non.

Deux règles qui priment sur la propreté apparente :

  · **aucune donnée fabriquée** — pas d'interpolation, pas de moyenne glissée
    dans un trou de série ;
  · **les non-réponses restent visibles** sous `NON_RENSEIGNE` plutôt que
    supprimées. Les supprimer embellit toutes les répartitions et fait
    disparaître le seul constat qui appelait une action.
"""

# pyrefly: ignore [missing-import]
import pandas as pd

# Modalité affichée pour une valeur absente. Une seule constante, pour que la
# même chaîne serve au nettoyage, aux agrégations et aux libellés d'axes.
NON_RENSEIGNE = "Non renseigné"

# Sentinelles rencontrées sur les portails opendata : elles signifient
# « absent », pas « zéro ».
SENTINELLES = ("", "Nsp", "N/a", "NA", "n/a", "-", "--", "ND", "nd")


def normaliser_texte(serie):
    """Espaces superflus retirés, casse uniformisée, sentinelles → absent.

    La casse d'abord : « LOME », « Lomé » et « lome » sont trois graphies
    d'une même ville, et un `groupby` les compterait comme trois modalités.
    """

    nettoyee = serie.astype("string").str.strip()
    nettoyee = nettoyee.replace(list(SENTINELLES), pd.NA)

    return nettoyee


def combler_libelles(cadre, colonnes):
    """Remplace les valeurs absentes par `NON_RENSEIGNE` sur les colonnes
    NOMINALES seulement.

    Jamais sur une colonne numérique : une non-réponse n'est pas un zéro, et
    la transformer en texte ferait basculer toute la colonne en `object`.
    """

    for colonne in colonnes:
        cadre[colonne] = cadre[colonne].fillna(NON_RENSEIGNE)

    return cadre


# def nettoyer_xxx(brut):
#     """<Ce que ce jeu devient, et ce qu'on a dû trancher pour l'obtenir>."""
#
#     cadre = brut.copy()
#     cadre.columns = [c.strip().lower() for c in cadre.columns]
#
#     for colonne in ("region", "prefecture"):
#         cadre[colonne] = normaliser_texte(cadre[colonne])
#
#     # Le fichier embarque ses propres totaux (« Ensemble », « Total ») : les
#     # garder doublerait chaque somme.
#     cadre = cadre[~cadre["region"].isin(["Ensemble", "Total"])]
#
#     return combler_libelles(cadre, ["region", "prefecture"])
