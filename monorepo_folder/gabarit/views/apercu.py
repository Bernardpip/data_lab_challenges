"""Aperçu — la vue témoin du gabarit, à remplacer par la première vraie vue.

Elle montre la forme qu'une vue doit avoir, et rien d'autre :

    1. les traducteurs en tête, un par domaine ;
    2. les données par le point d'entrée UNIQUE (`datasets`) ;
    3. UNE barre de filtres, tout en haut, ou aucune ;
    4. les faits calculés par `analytics` — la vue ne calcule rien ;
    5. les chiffres seuls en tuiles, les graphes dans des cartes ;
    6. une `note()` qui porte la CONCLUSION, avec ses chiffres en paramètres ;
    7. `table_twin()` sous chaque graphe.

Aucun texte visible n'est écrit ici : tout vient de `i18n/locales/apercu.json`.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui
from socle.i18n.traduction import t

from utils.data import datasets


def render_apercu():
    tr, tc = t("apercu"), t("commun")
    data = datasets()

    if not data:
        # Le gabarit démarre AVANT que le corpus ne soit déclaré : cet état
        # doit s'afficher proprement, sinon la première exécution d'un
        # nouveau défi accueille son auteur par une trace d'exception.
        ui.hero("0", tr("aucun_jeu"), tr("aucun_jeu_detail"))
        return

    ui.stat_tiles([
        {"value": ui.fr_number(len(data)), "label": tr("jeux_charges"),
         "icon": "table-2"},
    ])

    with ui.card(tr("carte_titre"), tr("carte_sous_titre"), "layout-dashboard"):
        st.info(tc("aucun_resultat"))
        ui.note(tr("note_amorce", {"jeux": len(data)}))
