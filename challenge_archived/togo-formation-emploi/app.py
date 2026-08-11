"""Tableau de bord — Adéquation formation-emploi au Togo.

Point d'entrée : configure la page, déclare où vivent les traductions, puis
monte la coquille du socle (`render_shell`), qui résout la route et sert le
composant de l'onglet actif.
"""

from pathlib import Path

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import i18n

st.set_page_config(
    page_title="TOGO · Formation & Emploi",
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
    synthese, technique, superieur, financement, recommandations,
    rapport, econometrie, donnees, annexes,
)


BRAND = {
    "name": "Formation & Emploi",
    "wordmark": "Formation & Emploi",
    "studio": "ANALYTICS CONSOLE",
    "signature": "TOGO par ANALYTICS",
    "footer_mark": "TOGO",
    "icon": "graduation-cap",
    "org": "République togolaise",
    "flag": "🇹🇬",
    "lab": "Data AI Lab",
    # Deux lignes courtes tiennent mieux dans la hauteur de la top bar qu'une
    # longue. Ce libellé était écrit en dur dans la coquille avant l'extraction
    # du socle, ce qui obligeait à l'éditer pour changer de commanditaire.
    "lab_wordmark": "Togo<br>AI Lab",
    "lab_url": "https://datalab.gouv.tg/",
    "author": "Kokou PIPI",
}


# Registre : clé d'onglet (cf. nav_config) → composant qui rend la vue.
# Une clé absente rend `ComingSoonPage`, comme dans AppGenericComponent.
CONTENT_REGISTRY = {
    "synthese": synthese.render_synthese,
    "adequation": synthese.render_adequation,

    "carto": technique.render_carto,
    "dynamique": technique.render_dynamique,
    "equipements": technique.render_equipements,
    "etablissements": technique.render_etablissements,

    "sup_indicateurs": superieur.render_indicateurs,
    "sup_cles": superieur.render_cles,
    "sup_reseau": superieur.render_reseau,

    "budget": financement.render_budget,
    "execution": financement.render_execution,
    "depense": financement.render_depense,
    "chomage": financement.render_chomage,

    "priorites": recommandations.render_priorites,
    "leviers": recommandations.render_leviers,

    "rapport_intro": rapport.render_intro,
    "rapport_dev": rapport.render_developpement,
    "eco_modeles": econometrie.render_modeles,
    "eco_limites": econometrie.render_limites,
    "rapport_conclusion": rapport.render_conclusion,

    "fichiers": donnees.render_fichiers,
    "croisements": donnees.render_croisements,

    "sources": annexes.render_sources,
    "methodologie": annexes.render_methodologie,
    "affichage": annexes.render_affichage,
}


render_shell(
    brand=BRAND,
    content_registry=CONTENT_REGISTRY,
    sections=NAV_SECTIONS,
    footer_context="opendata.gouv.tg",
    footer_context_url="https://opendata.gouv.tg/",
)
