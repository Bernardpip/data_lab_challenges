"""Fiche par fichier — décrite AVANT nettoyage.

Ce que chaque fiche relève, et qui vient de la lecture RÉELLE du fichier
(phase 2), jamais d'une supposition :

    code          sigle stable, utilisé partout ensuite
    volumétrie    lignes × colonnes BRUTES
    granularité   la plus fine : national / région / préfecture / canton / GPS
    période       millésimes réels, trous compris
    format        large / long (colonne « indicateur ») / géo
    pièges        sentinelles, doublons de casse, totaux embarqués
    permet        et surtout ce qu'il ne permet PAS

Le dernier champ est le plus utile du tableau de bord : c'est lui qui empêche
un lecteur d'attendre du corpus ce qu'il ne contient pas.
"""

from socle.audit import profil_fichier

from utils.data import bruts


# Ce qui ne se calcule pas : granularité, période, format, pièges. Relevé à la
# main lors de la lecture des fichiers, une entrée par ressource.
FICHES = {
    # "eaux": {
    #     "code": "DVECA-TG",
    #     "granularite": "point GPS",
    #     "periode": "2019-2024, 2021 absente",
    #     "format": "large",
    #     "pieges": "sentinelle « Nsp » ; Lomé écrit en trois graphies",
    #     "permet": "densité d'équipement par canton",
    #     "ne_permet_pas": "aucune mesure de débit — le champ existe, il est vide",
    #     "source": "https://opendata.gouv.tg/...",
    # },
}


def profils():
    """Les fiches, complétées par la volumétrie mesurée sur le fichier brut."""

    corpus = bruts()

    return [
        {**fiche, "cle": cle, **profil_fichier(corpus[cle])}
        for cle, fiche in FICHES.items()
        if cle in corpus
    ]
