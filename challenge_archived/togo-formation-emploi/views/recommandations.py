"""Recommandations — ce que les analyses impliquent, territoire par territoire
puis levier par levier.

Aucun texte visible n'est écrit ici : tout vient de
`i18n/locales/recommandations.json` via `t("recommandations")`.

`_LEVIERS` ne porte plus que l'ossature : le préfixe de clé i18n (`l1` →
`l1_titre`, `l1_constat`, `l1_action`) et la vue qui établit le constat. Le
champ `preuve` sert aussi de source au filtre par domaine, d'où sa forme
« Section › Vue » et ses deux clés — l'une pour la section (traduite via
`nav_sections`), l'autre pour l'onglet (via `nav_items`).
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import charts
from socle.ui import filters
from utils import barres
from socle.ui import card, note, pill, fr_number
from utils.data import datasets, apply_filters
from utils import analytics
from socle.i18n.traduction import t


_NIVEAUX = {
    "critical": "niveau_critical",
    "warning": "niveau_warning",
    "good": "niveau_good",
}


# Vingt-six leviers. Chaque entrée dit d'où vient son texte (`i18n`) et quelle
# vue établit son constat (`section` / `item`, clés de nav_config).
_LEVIERS = [
    {"i18n": "l1", "section": "synthese", "item": "synthese"},
    {"i18n": "l2", "section": "financement", "item": "execution"},
    {"i18n": "l3", "section": "superieur", "item": "sup_cles"},
    {"i18n": "l4", "section": "technique", "item": "carto"},
    {"i18n": "l5", "section": "financement", "item": "chomage"},
    {"i18n": "l6", "section": "rapport", "item": "eco_limites"},
    {"i18n": "l7", "section": "rapport", "item": "rapport_intro"},
    {"i18n": "l8", "section": "financement", "item": "execution"},
    {"i18n": "l9", "section": "technique", "item": "dynamique"},
    {"i18n": "l10", "section": "technique", "item": "dynamique"},
    {"i18n": "l11", "section": "technique", "item": "equipements"},
    {"i18n": "l12", "section": "technique", "item": "equipements"},
    {"i18n": "l13", "section": "technique", "item": "equipements"},
    {"i18n": "l14", "section": "technique", "item": "carto"},
    {"i18n": "l15", "section": "annexes", "item": "methodologie"},
    {"i18n": "l16", "section": "technique", "item": "carto"},
    {"i18n": "l17", "section": "technique", "item": "carto"},
    {"i18n": "l18", "section": "financement", "item": "chomage"},
    {"i18n": "l19", "section": "financement", "item": "chomage"},
    {"i18n": "l20", "section": "annexes", "item": "methodologie"},
    {"i18n": "l21", "section": "annexes", "item": "sources"},
    {"i18n": "l22", "section": "superieur", "item": "sup_reseau"},
    {"i18n": "l23", "section": "superieur", "item": "sup_reseau"},
    {"i18n": "l24", "section": "superieur", "item": "sup_reseau"},
    {"i18n": "l25", "section": "superieur", "item": "sup_cles"},
    {"i18n": "l26", "section": "financement", "item": "execution"},
]


def render_priorites():
    tr, tc = t("recommandations"), t("commun")

    data = datasets()
    formations = data["formations"]

    # Même barre que la Vue d'ensemble et les Formations techniques : le score
    # se recalcule sur le périmètre retenu, ce qui permet de le lire filière
    # par filière — une région bien dotée globalement peut n'avoir aucune
    # offre diplômante.
    selection = barres.territoriale(formations)
    filtre = apply_filters(formations, selection)

    if filtre.empty:
        st.info(tc("aucun_etablissement"))
        return

    score = analytics.score_territorial(filtre)
    faits = analytics.concentration(filtre)

    with card(tr("carte_score_titre"), tr("carte_score_sous_titre"), "flag"):
        charts.bar_h(
            score.assign(score=score["score"].round(0)),
            "region", "score",
            highlight=score.iloc[0]["region"],
        )

        lignes = []

        for _, row in score.iterrows():
            lignes.append(
                '<div style="display:flex;align-items:center;gap:10px;'
                'padding:7px 0;border-bottom:1px solid var(--kg-color-border-light);">'
                f'<span style="width:110px;font-weight:600;">{row["region"]}</span>'
                f'{pill(row["niveau"], tr(_NIVEAUX[row["niveau"]]))}'
                '<span style="color:var(--kg-color-text-muted);margin-left:auto;">'
                + tr("ligne_score", {
                    "etablissements": int(row["etablissements"]),
                    "prefectures": int(row["prefectures"]),
                    "score": fr_number(row["score"], 0),
                })
                + "</span></div>"
            )

        st.markdown("".join(lignes), unsafe_allow_html=True)

        if len(score) > 1:
            # La région en tête du classement est celle du score le plus BAS —
            # `score_territorial` trie en ordre croissant. Ce n'est pas
            # forcément celle qui compte le moins d'établissements : le score
            # pondère aussi l'étendue préfectorale couverte.
            derniere = score.iloc[0]
            moins_dotee = faits["region_queue"]

            nuance = (
                "" if derniere["region"] == moins_dotee
                else tr("note_score_nuance", {
                    "region": moins_dotee,
                    "etablissements": faits["etab_region_queue"],
                })
            )

            note(tr("note_score", {
                "region": derniere["region"],
                "score": fr_number(derniere["score"], 0),
                "etablissements": int(derniere["etablissements"]),
                "prefectures": int(derniere["prefectures"]),
                "nuance": nuance,
            }))
        else:
            # Le score est un classement RELATIF : à une seule région, il vaut
            # mécaniquement 100 et ne veut plus rien dire.
            note(tr("note_score_une_region"))

        charts.table_twin(
            score.assign(score=score["score"].round(1))
            .rename(columns={
                "region": tr("colonne_region"),
                "etablissements": tr("colonne_etablissements"),
                "prefectures": tr("colonne_prefectures"),
                "score": tr("colonne_score"),
                "niveau": tr("colonne_niveau"),
            })
        )


def _domaine(levier):
    """Section du tableau de bord qui établit le constat du levier.

    Traduite : le filtre affiche des libellés, il doit suivre la langue.
    """

    return t("nav_sections")(levier["section"])


def _preuve(levier):
    """« Section › Vue », dans la langue active."""

    return (f'{t("nav_sections")(levier["section"])} › '
            f'{t("nav_items")(levier["item"])}')


def render_leviers():
    tr, tf, tc = t("recommandations"), t("filtres"), t("commun")

    domaines = sorted({_domaine(levier) for levier in _LEVIERS})

    selection = filters.choix([
        {"libelle": tf("domaine"), "cle": "filtre_levier_domaine",
         "placeholder": tc("tous"), "options": domaines,
         "aide": tr("aide_domaine")},
    ])["filtre_levier_domaine"]

    # La numérotation reste celle de la liste complète : le levier n°14 doit
    # rester le n°14 quel que soit le filtre, sinon aucune référence ne tient.
    retenus = [
        (index, levier) for index, levier in enumerate(_LEVIERS, start=1)
        if filters.retenu(selection, _domaine(levier))
    ]

    sous_titre = (
        tr("carte_leviers_sous_titre") if len(retenus) == len(_LEVIERS)
        else tr("carte_leviers_sous_titre_filtre",
                {"retenus": len(retenus), "total": len(_LEVIERS)})
    )

    with card(tr("carte_leviers_titre", {"nombre": len(retenus)}), sous_titre,
              "lightbulb"):
        for index, levier in retenus:
            cle = levier["i18n"]

            st.markdown(
                '<div style="padding:12px 0;border-bottom:1px solid var(--kg-color-border-light);">'
                '<div style="display:flex;gap:10px;align-items:baseline;">'
                '<span style="color:var(--kg-color-primary);font-weight:700;'
                f'font-size:var(--kg-fs-lg);">{index}</span>'
                '<div style="flex:1;">'
                f'<div style="font-size:var(--kg-fs-lg);font-weight:600;">'
                f'{tr(cle + "_titre")}</div>'
                '<div style="color:var(--kg-color-text-secondary);margin-top:5px;">'
                f'<b>{tr("libelle_constat")}</b> {tr(cle + "_constat")}</div>'
                '<div style="color:var(--kg-color-text-secondary);margin-top:3px;">'
                f'<b>{tr("libelle_action")}</b> {tr(cle + "_action")}</div>'
                '<div style="color:var(--kg-color-text-muted);margin-top:5px;'
                'font-size:var(--kg-fs-xs);">'
                + tr("libelle_source", {"preuve": _preuve(levier)})
                + "</div></div></div></div>",
                unsafe_allow_html=True
            )
