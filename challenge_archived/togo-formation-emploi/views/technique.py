"""Formations techniques — cartographie et structure de l'offre.

La barre de filtres est UNIQUE et placée au-dessus de tout ce qu'elle cadre :
tous les graphes de la section se redessinent sur la même sélection (jamais de
filtre logé dans une carte de graphe).

Aucun texte visible n'est écrit ici : tout vient de
`i18n/locales/technique.json` via `t("technique")`.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import charts
from socle.ui import filters
from utils import barres
from socle.charts import maps
from socle.ui import card, stat_tiles, note, fr_number
from utils.data import datasets, apply_filters
from utils import analytics
from socle.i18n.traduction import t


def _selection():
    data = datasets()
    formations = data["formations"]
    selection = barres.territoriale(formations)

    return formations, apply_filters(formations, selection)


def _chart_filieres(filtre, height=None):
    tr = t("technique")

    filieres = (
        filtre.groupby("categorie").size()
        .reset_index(name="etablissements")
    )
    charts.bar_h(filieres, "categorie", "etablissements", height=height)
    note(tr("note_filieres"))
    charts.table_twin(
        filieres.rename(columns={
            "categorie": tr("colonne_filiere"),
            "etablissements": tr("colonne_etablissements"),
        })
    )


def _chart_statuts(filtre, height=None):
    tr = t("technique")

    statuts = (
        filtre.groupby("statut").size()
        .reset_index(name="etablissements")
    )
    charts.bar_h(statuts, "statut", "etablissements", height=height)
    note(tr("note_statuts"))
    charts.table_twin(
        statuts.rename(columns={
            "statut": tr("colonne_statut"),
            "etablissements": tr("colonne_etablissements"),
        })
    )


def _chart_prefectures(filtre, top=8):
    tr = t("technique")

    prefectures = analytics.par_prefecture(filtre, top=top)
    charts.bar_h(prefectures, "prefecture", "etablissements")

    # Le constat compare la tête du classement au reste du PAYS, pas au reste
    # du graphe : découper à 8 ou à 12 ne doit pas changer le fait énoncé.
    tete = prefectures.head(2)
    total_tete = int(tete["etablissements"].sum())

    note(tr("note_prefectures", {
        "tete": tr("et").join(tete["prefecture"]),
        "total_tete": total_tete,
        "reste": len(filtre) - total_tete,
        "autres": filtre["prefecture"].nunique() - len(tete),
    }))
    charts.table_twin(
        prefectures.rename(columns={
            "prefecture": tr("colonne_prefecture"),
            "region": tr("colonne_region"),
            "etablissements": tr("colonne_etablissements"),
        })
    )


def render_carto():
    tr, tc = t("technique"), t("commun")
    formations = datasets()["formations"]

    # La barre est PLEINE LARGEUR, au-dessus des deux colonnes : elle cadre
    # aussi bien les graphes de gauche que la carte de droite, et une barre
    # doit se tenir au-dessus de tout ce qu'elle gouverne. Logée dans la
    # colonne de gauche, elle donnait en plus à ses cinq filtres deux tiers de
    # la place disponible, où ils ne tenaient plus sur une seule ligne.
    selection = barres.territoriale(formations)
    filtre = apply_filters(formations, selection)

    # 2/3 KPI + graphes · 1/3 carte. La colonne étroite convient bien mieux au
    # Togo (pays très étiré nord-sud) qu'une carte pleine largeur, qui devait
    # dézoomer pour caser l'extension nord-sud et révélait toute l'Afrique de
    # l'Ouest.
    gauche, droite = st.columns([2, 1], gap="small")

    with gauche:
        geolocalises = filtre.dropna(subset=["lat", "lon"])

        stat_tiles([
            {"label": tr("tuile_selectionnes"), "value": fr_number(len(filtre)),
             "icon": "building-2",
             "delta": tr("tuile_selectionnes_detail",
                         {"total": fr_number(len(formations))}),
             "good": True},
            {"label": tr("tuile_geolocalises"), "value": fr_number(len(geolocalises)),
             "icon": "map-pin",
             "delta": tr("tuile_geolocalises_detail", {
                 "part": fr_number(len(geolocalises) / max(len(filtre), 1) * 100, 0)}),
             "good": True},
            {"label": tr("tuile_prefectures"),
             "value": fr_number(filtre["prefecture"].nunique()),
             "icon": "flag",
             "delta": tr("tuile_prefectures_detail",
                         {"total": formations["prefecture"].nunique()}),
             "good": True},
            {"label": tr("tuile_filieres"),
             "value": fr_number(filtre["categorie"].nunique()),
             "icon": "bar-chart-3",
             "delta": tr("tuile_filieres_detail",
                         {"total": formations["categorie"].nunique()}),
             "good": True},
        ])

        if filtre.empty:
            st.info(tc("aucun_etablissement"))
        else:
            filieres_col, statut_col = st.columns(2, gap="small")

            with filieres_col:
                with card(tr("carte_filieres_titre"),
                          tr("carte_filieres_sous_titre"), "bar-chart-3"):
                    _chart_filieres(filtre, height=250)

            with statut_col:
                with card(tr("carte_bati_titre"), tr("carte_bati_sous_titre"),
                          "building-2"):
                    _chart_statuts(filtre, height=250)

            with card(tr("carte_prefectures_titre"),
                      tr("carte_prefectures_sous_titre"), "map-pin"):
                _chart_prefectures(filtre)

    with droite:
        with card(tr("carte_implantation_titre"),
                  tr("carte_implantation_sous_titre"), "map-pin"):
            # Hauteur calée sur celle de la colonne de gauche (tuiles + deux
            # graphes courts + « Préfectures »), pour éviter le vide sous la
            # carte sans étirer le cadre au-delà de la carte elle-même.
            #
            # L'infobulle est fournie par la vue : le socle ignore quelles
            # colonnes ce fichier porte, et c'est ce qui lui permet de servir
            # la carte des villes du supérieur avec le même code.
            maps.points(
                filtre, cle="carte_formations", height=980,
                message_vide=tc("aucun_etablissement_geolocalise"),
                infobulle=lambda row: (
                    f'<b>{row["etab_nom"]}</b><br>'
                    f'{row["prefecture"]} · {row["region"]}<br>'
                    f'<span style="color:#475569;">{row["categorie"]}</span>'
                ),
            )


def render_dynamique():
    tr, tc = t("technique"), t("commun")
    _, filtre = _selection()

    if filtre.empty:
        st.info(tc("aucun_etablissement"))
        return

    decennies = analytics.creation_par_decennie(filtre)
    datees = filtre["annee_creation"].dropna()

    if decennies.empty:
        st.info(tr("info_aucune_annee"))
        return

    pic = decennies.loc[decennies["creations"].idxmax()]
    recentes = int(datees[datees >= 2010].count())

    stat_tiles([
        {"label": tr("tuile_dates"), "value": fr_number(len(datees)),
         "icon": "table-2",
         "delta": tr("tuile_dates_detail", {
             "total": fr_number(len(filtre)),
             "part": fr_number(len(datees) / max(len(filtre), 1) * 100, 0)}),
         "good": True},
        {"label": tr("tuile_recents"), "value": fr_number(recentes),
         "icon": "trending-up",
         "delta": tr("tuile_recents_detail", {
             "part": fr_number(recentes / max(len(datees), 1) * 100, 0)}),
         "good": True},
        {"label": tr("tuile_decennie"), "value": f'{int(pic["decennie"])}s',
         "icon": "bar-chart-3",
         "delta": tr("tuile_decennie_detail",
                     {"creations": int(pic["creations"])}),
         "good": True},
        {"label": tr("tuile_ancien"),
         "value": fr_number(int(datees.min())) if len(datees) else "—",
         "icon": "flag", "delta": tr("tuile_ancien_detail")},
    ])

    with card(tr("carte_rythme_titre"), tr("carte_rythme_sous_titre"),
              "trending-up"):
        charts.column_series(
            decennies["libelle"].tolist(),
            decennies["creations"].tolist(),
            unit=tr("unite_creations"),
            height=280,
            highlight=f'{int(pic["decennie"])}s',
            note_last=tr("annotation_decennie_incomplete"),
        )
        note(tr("note_rythme", {"creations": int(pic["creations"])}))
        charts.table_twin(
            decennies[["libelle", "creations", "cumul"]].rename(columns={
                "libelle": tr("colonne_decennie"),
                "creations": tr("colonne_creations"),
                "cumul": tr("colonne_cumul"),
            })
        )

    with card(tr("carte_ou_quand_titre"), tr("carte_ou_quand_sous_titre"),
              "map-pin"):
        grille = analytics.creation_par_region_decennie(filtre)

        if grille.empty:
            st.info(tr("info_pas_assez_datees"))
        else:
            charts.heatmap(grille)
            note(tr("note_ou_quand"))
            charts.table_twin(grille.reset_index())


def render_equipements():
    tr, tc = t("technique"), t("commun")
    _, filtre = _selection()

    if filtre.empty:
        st.info(tc("aucun_etablissement"))
        return

    infra = analytics.infrastructures(filtre)
    reseau = analytics.maillage(filtre)
    ouverture = analytics.amplitude_ouverture(filtre)

    stat_tiles([
        {"label": tr("tuile_sport"), "value": fr_number(infra["part_sport"], 0),
         "unit": "%", "icon": "flag",
         "delta": tr("tuile_sport_detail",
                     {"nombre": fr_number(infra["sans_sport"])}),
         "good": False},
        {"label": tr("tuile_wc"), "value": fr_number(infra["part_wc"], 0),
         "unit": "%", "icon": "building-2",
         "delta": tr("tuile_wc_detail", {
             "part": fr_number(infra["part_sanitaire_inconnu"], 0)}),
         "good": False},
        {"label": tr("tuile_foncier"), "value": fr_number(infra["part_prive"], 0),
         "unit": "%", "icon": "map-pin",
         "delta": tr("tuile_foncier_detail"), "good": False},
        {"label": tr("tuile_localites"), "value": fr_number(reseau["localites"]),
         "icon": "table-2",
         "delta": tr("tuile_localites_detail", {
             "cantons": reseau["cantons"], "communes": reseau["communes"]}),
         "good": True},
    ])

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with card(tr("carte_sanitaire_titre"), tr("carte_sanitaire_sous_titre"),
                  "building-2"):
            charts.bar_h(infra["sanitaire"], "sanitaire", "etablissements")
            note(tr("note_sanitaire", {
                "part": fr_number(infra["part_sanitaire_inconnu"], 0)}))
            charts.table_twin(
                infra["sanitaire"].rename(columns={
                    "sanitaire": tr("colonne_equipement"),
                    "etablissements": tr("colonne_etablissements"),
                })
            )

    with droite:
        with card(tr("carte_foncier_titre"), tr("carte_foncier_sous_titre"),
                  "map-pin"):
            charts.bar_h(infra["foncier"], "foncier_famille", "etablissements")
            note(tr("note_foncier"))
            charts.table_twin(
                infra["foncier"].rename(columns={
                    "foncier_famille": tr("colonne_foncier"),
                    "etablissements": tr("colonne_etablissements"),
                })
            )

    if ouverture:
        with card(tr("carte_ouverture_titre"), tr("carte_ouverture_sous_titre"),
                  "settings"):
            charts.column_series(
                ouverture["distribution"]["libelle"].tolist(),
                ouverture["distribution"]["etablissements"].tolist(),
                unit=tr("unite_etablissements"),
                height=240,
            )
            note(tr("note_ouverture", {
                "part": fr_number(ouverture["part_5_jours"], 0),
                "au_dela": ouverture["au_dela_de_5"],
            }))
            charts.table_twin(
                ouverture["distribution"][["libelle", "etablissements"]].rename(
                    columns={
                        "libelle": tr("colonne_ouverture"),
                        "etablissements": tr("colonne_etablissements"),
                    })
            )


def render_etablissements():
    tr = t("technique")
    _, filtre = _selection()

    with card(tr("carte_liste_titre"),
              tr("carte_liste_sous_titre", {"nombre": fr_number(len(filtre))}),
              "table-2"):
        colonnes = [
            "etab_nom", "region", "prefecture", "commune_nom_bdd",
            "categorie", "statut", "annee_creation", "sport",
        ]

        st.dataframe(
            filtre[colonnes].rename(columns={
                "etab_nom": tr("colonne_etablissement"),
                "region": tr("colonne_region"),
                "prefecture": tr("colonne_prefecture"),
                "commune_nom_bdd": tr("colonne_commune"),
                "categorie": tr("colonne_filiere"),
                "statut": tr("colonne_statut"),
                "annee_creation": tr("colonne_creation"),
                "sport": tr("colonne_sport"),
            }),
            use_container_width=True,
            hide_index=True,
            height=460,
        )
