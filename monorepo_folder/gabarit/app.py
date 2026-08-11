"""Tableau de bord — {{TITRE}}.

Point d'entrée : configure la page, déclare où vivent les traductions, puis
monte la coquille du socle, qui résout la route et sert le composant de
l'onglet actif.

Ce fichier ne contient QUE du câblage : aucune donnée, aucun calcul, aucun
texte visible. Les trois choses qu'il déclare — la marque, l'emplacement des
locales, le registre de contenu — sont les seules qu'un défi doive décider
avant d'écrire sa première vue.
"""

from pathlib import Path

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import i18n

st.set_page_config(
    page_title="{{TITRE_ONGLET}}",
    page_icon="🇹🇬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# AVANT tout import de vue : le socle ignore où sont les textes du défi tant
# qu'on ne le lui a pas dit, et une vue qui traduirait avant cet appel
# afficherait ses clés brutes.
i18n.configurer(Path(__file__).parent / "i18n" / "locales")

from socle.shell import render_shell           # noqa: E402

from nav_config import NAV_SECTIONS            # noqa: E402
from views import apercu                       # noqa: E402


BRAND = {
    "name": "{{NOM_COURT}}",
    "wordmark": "{{NOM_COURT}}",
    "studio": "ANALYTICS CONSOLE",
    "signature": "TOGO par ANALYTICS",
    "footer_mark": "TOGO",
    "icon": "layout-dashboard",       # cf. socle/design/icons.py
    "org": "République togolaise",
    "flag": "🇹🇬",
    "lab": "Data AI Lab",
    "lab_wordmark": "Togo<br>AI Lab",  # deux lignes courtes dans la top bar
    "lab_url": "https://datalab.gouv.tg/",
    "author": "{{AUTEUR}}",
}


# Registre : clé d'onglet (cf. nav_config) → fonction qui rend la vue.
# Une clé absente rend « bientôt disponible » au lieu de planter, ce qui
# permet de déclarer la navigation validée en phase 3 AVANT d'écrire les vues.
CONTENT_REGISTRY = {
    "apercu": apercu.render_apercu,
}


render_shell(
    brand=BRAND,
    content_registry=CONTENT_REGISTRY,
    sections=NAV_SECTIONS,
    footer_context="opendata.gouv.tg",
    footer_context_url="https://opendata.gouv.tg/",
)
