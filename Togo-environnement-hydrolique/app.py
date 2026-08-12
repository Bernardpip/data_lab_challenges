"""Tableau de bord — Accès à l'eau potable au Togo.

Point d'entrée : configure la page, déclare où vivent les traductions, puis
monte l'AFFICHE — seul gabarit de ce défi — qui résout la route depuis la
configuration de son menu et sert le composant de la vue active.

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

from nav_config import NAV_SECTIONS                 # noqa: E402
# Les vues ne sont plus importées ici : la configuration du menu, dans
# `views/affiche.py`, les référence une par une et les relie à leurs données.


# L'AFFICHE est le seul gabarit de ce défi. La console — sidebar, barre
# d'onglets, une colonne — a servi à construire les vingt-trois vues, puis
# l'affiche les a toutes reprises : mêmes fonctions, appelées dans deux
# colonnes au lieu d'une. Les garder toutes deux, c'était offrir deux chemins
# vers le même écran, et prendre le risque qu'une correction faite d'un côté
# manque de l'autre.
#
# Les ADRESSES de la console restent valides. Elles ont circulé — dans des
# liens, des captures, un rapport — et une adresse publiée ne se casse pas :
# elle se redirige. `?s=parc&t=tde` devient `?sec=parc&v=tde`, et le contenu
# est le même.
# Deux onglets ont changé de nom en rejoignant l'affiche : leur identifiant y
# entrait en collision avec celui d'une vue de la synthèse.
_ONGLETS_RENOMMES = {"priorites": "priorites_reco"}


def _rediriger_ancienne_route():
    """Traduit une adresse de console en adresse d'affiche, puis recharge."""

    params = st.query_params
    section, onglet = params.get("s"), params.get("t")

    if not section or section == "affiche" or section not in {
        s["key"] for s in NAV_SECTIONS
    }:
        return False

    garde = {cle: params[cle] for cle in ("lang", "h") if cle in params}
    params.clear()
    params.update({**garde, "s": "affiche", "sec": section})

    if onglet:
        params["v"] = _ONGLETS_RENOMMES.get(onglet, onglet)

    st.rerun()

    return True


if not _rediriger_ancienne_route():
    from views import affiche

    affiche.render()
