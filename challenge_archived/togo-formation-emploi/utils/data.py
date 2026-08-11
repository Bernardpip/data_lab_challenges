"""Accès aux données : chargement, nettoyage, cache — un seul point d'entrée
pour toutes les vues.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from utils.loader import load_all_data
from utils.clean import (
    clean_formations, clean_superieur, clean_indicateur, clean_budget,
    clean_indicateurs_sup,
)


@st.cache_data(show_spinner=False)
def bruts():
    """Fichiers tels que lus, sans nettoyage.

    Nécessaires aux profils par fichier : la volumétrie et les anomalies
    doivent être décrites AVANT traitement, sinon on présente comme propre un
    jeu qui ne l'était pas.
    """

    return load_all_data()


@st.cache_data(show_spinner=False)
def datasets():
    """Jeux de données nettoyés, prêts à l'analyse."""

    raw = load_all_data()

    return {
        "formations": clean_formations(raw["formations"]),
        # Dictionnaire des champs — non nettoyé (c'est de la métadonnée),
        # exposé pour l'inventaire des sources en annexe.
        "formations_detail": raw["formations_detail"],
        "superieur": clean_superieur(raw["etablissements"]),
        "chomage": clean_indicateur(raw["chomage"]),
        "depenses": clean_indicateur(raw["depenses"]),
        "inscriptions": clean_indicateur(raw["inscriptions"]),
        "budget": clean_budget(raw["budget"]),
        "indicateurs_sup": clean_indicateurs_sup(raw["indicateurs_sup"]),
    }


def apply_filters(formations, selection):
    """Applique la barre de filtres unique (une seule pour toute la section :
    jamais de filtre par graphe).

    Deux natures de filtre coexistent :
      · les listes de modalités (région, filière…) → appartenance ;
      · l'année de création → intervalle, passé sous la forme d'un couple.

    L'année n'est PAS renseignée pour tous les établissements. L'intervalle
    n'est donc appliqué que s'il a été resserré : à pleine amplitude, les
    établissements sans année sont conservés, sinon l'ouverture du tableau de
    bord amputerait d'emblée la base sans que personne n'ait rien demandé.
    """

    out = formations

    for column, valeur in selection.items():
        if not valeur:
            continue

        if isinstance(valeur, tuple):
            debut, fin = valeur
            annees = out[column]
            out = out[annees.between(debut, fin)]
        else:
            out = out[out[column].isin(valeur)]

    return out
