"""Point d'entrée UNIQUE des vues : chargement, nettoyage, cache.

    loader (brut) → clean → data (@st.cache_data)
                              ↓
          analytics · recettes · profils · perimetre · contexte
                              ↓
                        views → charts

Une vue n'appelle jamais le loader ni le nettoyage directement. Streamlit
rejouant tout le script à chaque clic, chaque interaction relirait les
388 polygones de cantons et les 218 microprojets.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from utils.loader import charger_tout, poids_des_fichiers
from utils.clean import (
    nettoyer_cantons, nettoyer_tde, nettoyer_dictionnaire_tde,
    nettoyer_coso, nettoyer_ventes, nettoyer_population,
)


@st.cache_data(show_spinner=False)
def bruts():
    """Fichiers tels que lus, sans nettoyage.

    Nécessaires aux profils et à l'audit de périmètre : la volumétrie et les
    absences doivent être décrites AVANT traitement. Un audit qui balaierait
    les jeux nettoyés ne trouverait pas les colonnes que le nettoyage a
    renommées — et conclurait à tort qu'elles n'existent pas.
    """

    return charger_tout()


@st.cache_data(show_spinner=False)
def datasets():
    """Jeux nettoyés, prêts à l'analyse."""

    raw = charger_tout()

    return {
        "cantons": nettoyer_cantons(raw["cantons"]),
        "tde": nettoyer_tde(raw["tde"]),
        "tde_dictionnaire": nettoyer_dictionnaire_tde(raw["tde_dictionnaire"]),
        "coso": nettoyer_coso(raw["coso"], geo=raw["coso_geo"]),
        "ventes": nettoyer_ventes(raw["ventes"]),
        "population": nettoyer_population(raw["population"]),
    }


@st.cache_data(show_spinner=False)
def poids():
    """Poids sur disque de chaque ressource, citée comprise."""

    return poids_des_fichiers()


def apply_filters(cadre, selection):
    """Applique la barre de filtres unique de la vue.

    `selection` vient de `socle.ui.filters` : {colonne: valeur}, où la valeur
    est une LISTE de modalités (appartenance) ou un COUPLE (intervalle). Une
    valeur vide ou None ne filtre rien — « rien de coché » veut dire « tout »,
    convention tenue dans toute l'application.

    Une colonne absente du cadre est ignorée plutôt que de lever : les vues
    partagent leurs clés de session, si bien qu'une région choisie sur la
    carte des cantons suit l'utilisateur jusqu'au parc COSO, qui ne porte pas
    forcément les mêmes colonnes.
    """

    sortie = cadre

    for colonne, valeur in selection.items():
        if not valeur or colonne not in sortie.columns:
            continue

        if isinstance(valeur, tuple):
            debut, fin = valeur
            sortie = sortie[sortie[colonne].between(debut, fin)]
        else:
            sortie = sortie[sortie[colonne].isin(valeur)]

    return sortie
