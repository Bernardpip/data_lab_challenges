"""Point d'entrée UNIQUE des vues : chargement, nettoyage, cache.

    loader (brut) → clean → data (@st.cache_data)
                              ↓
          analytics · recettes · profils · perimetre
                              ↓
                        views → charts

Une vue n'appelle jamais le loader ni le nettoyage directement. Sans cette
règle, Streamlit rejouant tout le script à chaque clic, chaque interaction
relirait les fichiers.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from utils.loader import charger_tout


@st.cache_data(show_spinner=False)
def bruts():
    """Fichiers tels que lus, sans nettoyage.

    Nécessaires aux profils par fichier : la volumétrie et les anomalies
    doivent être décrites AVANT traitement, sinon on présente comme propre un
    jeu qui ne l'était pas.
    """

    return charger_tout()


@st.cache_data(show_spinner=False)
def datasets():
    """Jeux nettoyés, prêts à l'analyse."""

    raw = charger_tout()

    return {
        # "eaux": nettoyer_eaux(raw["eaux"]),
    }


def apply_filters(cadre, selection):
    """Applique la barre de filtres unique de la vue.

    `selection` vient de `socle.ui.filters` : {colonne: valeur}, où la valeur
    est une LISTE de modalités (appartenance) ou un COUPLE (intervalle). Une
    valeur vide ou None ne filtre rien — « rien de coché » veut dire « tout »,
    convention tenue dans toute l'application.

    L'intervalle n'est appliqué que s'il a été resserré (le socle renvoie None
    à pleine amplitude) : sinon, les lignes dont la valeur est absente
    seraient écartées dès l'ouverture, amputant la base sans que personne
    n'ait rien demandé.
    """

    sortie = cadre

    for colonne, valeur in selection.items():
        if not valeur:
            continue

        if isinstance(valeur, tuple):
            debut, fin = valeur
            sortie = sortie[sortie[colonne].between(debut, fin)]
        else:
            sortie = sortie[sortie[colonne].isin(valeur)]

    return sortie
