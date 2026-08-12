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

# L'affiche a ensuite été réordonnée en RÉCIT : ses sections ne sont plus des
# thèmes — risque, parc, démographie — mais des actes, et les thèmes s'y sont
# redistribués. Une adresse de console désigne donc un acte, et parfois un
# onglet qui a changé de section en même temps que de voisins.
#
# Ces deux tables sont la mémoire de ce déplacement. Elles ne coûtent que
# quelques lignes, et sans elles chaque lien publié pendant six mois tomberait
# sur la page d'accueil sans un mot d'explication.
_SECTIONS_RECIT = {
    "synthese": "constat",
    "parc": "ou",
    "demographie": "habitants",
    "croisements": "inondation",
    "recommandations": "agir",
    "donnees": "preuves",
    "annexes": "preuves",
    "inondation": "inondation",
}

# Onglets dont la section d'accueil a changé avec le récit : l'identifiant
# suffit à les retrouver, mais pas à savoir où ils vivent désormais.
_ONGLETS_DEPLACES = {
    "diagnostic": ("constat", "home"),
    "risque": ("inondation", "alea"),
    "priorites": ("agir", "priorites_reco"),
    "fri_carto": ("inondation", "alea"),
    "fri_facteurs": ("inondation", "facteurs"),
    "tde": ("ou", "repartition"),
    "coso": ("ou", "repartition"),
    "technique": ("etat", "fragilite"),
    "maintenance": ("etat", "entretien"),
    "allocation": ("habitants", "allocation"),
    "pression": ("habitants", "pression"),
    "ventes": ("habitants", "ventes"),
    "ouvrages_risque": ("inondation", "ouvrages_risque"),
}


def _rediriger_ancienne_route():
    """Traduit une adresse de console en adresse d'affiche, puis recharge."""

    params = st.query_params
    section, onglet = params.get("s"), params.get("t")

    if not section or section == "affiche" or section not in {
        s["key"] for s in NAV_SECTIONS
    }:
        return False

    garde = {cle: params[cle] for cle in ("lang", "h") if cle in params}

    # L'ONGLET commande quand il est connu : il désigne un contenu précis,
    # là où la section ne désigne qu'un voisinage. Une vue déplacée d'une
    # section à l'autre serait sinon servie dans son ancien acte, où elle
    # n'existe plus.
    acte, vue = _ONGLETS_DEPLACES.get(
        onglet, (_SECTIONS_RECIT.get(section, "constat"),
                 _ONGLETS_RENOMMES.get(onglet, onglet)))

    params.clear()
    params.update({**garde, "s": "affiche", "sec": acte})

    if vue:
        params["v"] = vue

    st.rerun()

    return True


if not _rediriger_ancienne_route():
    from views import affiche

    affiche.render()
