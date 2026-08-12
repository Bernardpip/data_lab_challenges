"""Tableau de bord — Accès à l'eau potable au Togo.

Point d'entrée : configure la page, déclare où vivent les traductions, puis
monte la coquille du socle, qui résout la route et sert le composant de
l'onglet actif.

Ce fichier ne contient QUE du câblage : aucune donnée, aucun calcul, aucun
texte visible.
"""

from pathlib import Path

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import i18n

st.set_page_config(
    page_title="TOGO · Eau & Assainissement",
    page_icon="🇹🇬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# AVANT tout import de vue : le socle ignore où sont les textes de ce défi
# tant qu'on ne le lui a pas dit, et une vue qui traduirait avant cet appel
# afficherait ses clés brutes.
i18n.configurer(Path(__file__).parent / "i18n" / "locales")

from socle.shell import render_shell                # noqa: E402

from nav_config import NAV_SECTIONS                 # noqa: E402
from views import (                                 # noqa: E402
    synthese, risque, parc, demographie, croisements,
    recommandations, donnees, annexes,
)


BRAND = {
    "name": "Eau & Assainissement",
    "wordmark": "Eau & Assainissement",
    "studio": "ANALYTICS CONSOLE",
    "signature": "TOGO par ANALYTICS",
    "footer_mark": "TOGO",
    "icon": "map-pin",
    "org": "République togolaise",
    "flag": "🇹🇬",
    "lab": "Data AI Lab",
    "lab_wordmark": "Togo<br>AI Lab",
    "lab_url": "https://datalab.gouv.tg/",
    "author": "Kokou PIPI",
}


# Registre : clé d'onglet (cf. nav_config) → fonction qui rend la vue.
CONTENT_REGISTRY = {
    "diagnostic": synthese.render_diagnostic,
    "limites": synthese.render_limites,

    "fri_carto": risque.render_carto,
    "fri_facteurs": risque.render_facteurs,

    "tde": parc.render_tde,
    "coso": parc.render_coso,
    "technique": parc.render_technique,

    "pression": demographie.render_pression,
    "ventes": demographie.render_ventes,

    "ouvrages_risque": croisements.render_ouvrages_risque,
    "maintenance": croisements.render_maintenance,

    "priorites": recommandations.render_priorites,
    "leviers": recommandations.render_leviers,

    "fichiers": donnees.render_fichiers,
    "recettes": donnees.render_recettes,
    "perimetre": donnees.render_perimetre,

    "preuves": annexes.render_preuves,
    "sources": annexes.render_sources,
    "methodologie": annexes.render_methodologie,
    "affichage": annexes.render_affichage,
}


# L'affiche est une COQUILLE différente, pas un onglet de plus : elle n'a ni
# sidebar, ni barre d'onglets, ni filtres. Le branchement se fait donc ici, sur
# la section demandée, avant que la coquille ordinaire ne se monte — les deux
# injectent la même feuille de style et ne peuvent pas coexister dans un run.
if st.query_params.get("s") == "affiche":
    from views import affiche

    affiche.render()
else:
    render_shell(
        brand=BRAND,
        content_registry=CONTENT_REGISTRY,
        sections=NAV_SECTIONS,
        footer_context="opendata.gouv.tg",
        footer_context_url="https://opendata.gouv.tg/",
    )
