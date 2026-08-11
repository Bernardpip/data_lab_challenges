"""Risque d'inondation — les 388 cantons du référentiel ISRI-TG.

Aucun texte visible ici : tout vient de `i18n/locales/risque.json`.

C'est la seule section du tableau de bord qui couvre le pays ENTIER. Toutes
les autres travaillent sur des parcs partiels, et le disent.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui, charts
from socle.charts import maps
from socle.design.tokens import RISQUE_OFFICIEL, RISQUE_CONTOUR
from socle.i18n.traduction import t

from utils.data import datasets, apply_filters
from utils import analytics, barres


def _selection():
    """La barre territoriale, partagée avec le reste de l'application."""

    cantons = datasets()["cantons"]

    return apply_filters(cantons, barres.territoriale(cantons, avec_commune=True))


def render_carto():
    tr, tc = t("risque"), t("commun")
    filtre = _selection()

    if filtre.empty:
        st.info(tc("aucun_resultat"))
        return

    ui.stat_tiles([
        {"value": ui.fr_number(len(filtre)), "label": tr("tuile_cantons"),
         "delta": tr("tuile_cantons_detail",
                     {"regions": int(filtre["region"].nunique())}),
         "good": None, "icon": "map-pin"},
        {"value": ui.fr_number(filtre["risque_pts"].median(), 1), "unit": " pts",
         "label": tr("tuile_median"), "delta": tr("tuile_median_detail"),
         "good": None, "icon": "bar-chart-3"},
        {"value": ui.fr_number(filtre["risque_pts"].max(), 1), "unit": " pts",
         "label": tr("tuile_max"),
         "delta": str(filtre.loc[filtre["risque_pts"].idxmax(), "canton"]),
         "good": False, "icon": "flag"},
        {"value": ui.compact(float(filtre["population"].sum())),
         "label": tr("tuile_population"), "delta": tr("tuile_population_detail"),
         "good": None, "icon": "trending-up"},
    ])

    with ui.card(tr("carte_titre"), tr("carte_sous_titre"), "map-pin"):
        # Rampe du PRODUCTEUR, relevée au pixel sur la carte officielle : le
        # lecteur qui connaît le PDF doit reconnaître la même carte.
        bornes, methode = maps.choroplethe(
            filtre, valeur="risque_pts", cle="carte_fri",
            champs=["canton", "prefecture", "region", "risque_pts", "population"],
            libelles=[tr("col_canton"), tr("col_prefecture"), tr("col_region"),
                      tr("col_risque"), tr("col_population")],
            height=980, rampe=RISQUE_OFFICIEL, couleur_contour=RISQUE_CONTOUR,
        )

        if bornes:
            repartition = analytics.repartition_par_classe(
                filtre, bornes, [tr(f"classe_{i}") for i in range(1, len(bornes))])

            maps.legende_paliers(
                bornes, rampe=RISQUE_OFFICIEL, libelle=tr("legende_titre"),
                unite=" pts", decimales=1,
                effectifs=repartition["cantons"].tolist(),
            )
            ui.note(tr("note_classes", {
                "nombre": len(bornes) - 1,
                "bas": ui.fr_number(bornes[0], 1),
                "haut": ui.fr_number(bornes[-1], 1),
                "coupure": ui.fr_number(bornes[-2], 1),
            }))

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with ui.card(tr("carte_top_titre"), tr("carte_top_sous_titre"), "flag"):
            top = analytics.cantons_plus_exposes(filtre, 15)
            charts.sucette_h(top, "canton", "risque_pts", unit=" pts", decimals=1)
            ui.note(tr("note_top", {
                "premier": str(top.iloc[0]["canton"]),
                "risque": ui.fr_number(top.iloc[0]["risque_pts"], 1),
                "rapport": ui.fr_number(
                    top.iloc[0]["risque_pts"] / filtre["risque_pts"].median(), 1),
            }))
            charts.table_twin(top.rename(columns={
                "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
                "region": tr("col_region"), "risque_pts": tr("col_risque"),
                "population": tr("col_population")}))

    with droite:
        with ui.card(tr("carte_regions_titre"), tr("carte_regions_sous_titre"),
                     "bar-chart-3"):
            regions = analytics.risque_par_region(filtre)
            charts.bar_h(regions, "region", "risque_median", unit=" pts")
            ui.note(tr("note_regions", {
                "tete": str(regions.iloc[0]["region"]),
                "median": ui.fr_number(regions.iloc[0]["risque_median"], 1),
                "queue": str(regions.iloc[-1]["region"]),
                "median_queue": ui.fr_number(regions.iloc[-1]["risque_median"], 1),
            }))
            charts.table_twin(regions.rename(columns={
                "region": tr("col_region"), "cantons": tr("col_cantons"),
                "risque_median": tr("col_risque_median"),
                "risque_max": tr("col_risque_max"),
                "population": tr("col_population")}))


def render_facteurs():
    tr, tc = t("risque"), t("commun")
    filtre = _selection()

    if filtre.empty:
        st.info(tc("aucun_resultat"))
        return

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with ui.card(tr("carte_composantes_titre"),
                     tr("carte_composantes_sous_titre"), "bar-chart-3"):
            composantes = analytics.composantes_du_risque(filtre)

            if composantes.empty:
                st.info(tc("aucune_mesure"))
            else:
                lisible = composantes.assign(
                    composante=composantes["composante"].map(
                        lambda c: tr(f"composante_{c}"))
                )
                charts.bar_h(lisible, "composante", "valeur", unit="")
                ui.note(tr("note_composantes", {
                    "forte": str(lisible.iloc[-1]["composante"]),
                    "valeur": ui.fr_number(lisible.iloc[-1]["valeur"], 2),
                }))
                charts.table_twin(lisible.rename(columns={
                    "composante": tr("col_composante"),
                    "valeur": tr("col_valeur_normalisee")}))

    with droite:
        with ui.card(tr("carte_nuage_titre"), tr("carte_nuage_sous_titre"),
                     "search"):
            nuage = analytics.susceptibilite_vs_risque(filtre)

            if len(nuage) < 3:
                ui.note(tc("pas_assez_de_points"))
            else:
                charts.scatter_fit(
                    nuage["susceptibilite"], nuage["risque_pts"],
                    labels=nuage["canton"],
                    x_titre=tr("axe_susceptibilite"), y_titre=tr("axe_risque"),
                )
                ui.note(tr("note_nuage", {"n": ui.fr_number(len(nuage))}))
                charts.table_twin(nuage.rename(columns={
                    "canton": tr("col_canton"), "region": tr("col_region"),
                    "susceptibilite": tr("col_susceptibilite"),
                    "risque_pts": tr("col_risque"),
                    "population": tr("col_population")}))

    with ui.card(tr("carte_population_titre"), tr("carte_population_sous_titre"),
                 "trending-up"):
        bornes, _ = maps.paliers(filtre["risque_pts"], 5)

        if len(bornes) < 2:
            st.info(tc("aucune_mesure"))
            return

        etiquettes = [tr(f"classe_{i}") for i in range(1, len(bornes))]
        repartition = analytics.repartition_par_classe(filtre, bornes, etiquettes)

        charts.column_series(
            repartition["classe"].astype(str).tolist(),
            repartition["population"].tolist(),
            unit=tr("unite_habitants"), height=280,
        )
        ui.note(tr("note_population", {
            "haute": ui.compact(float(repartition["population"].iloc[-1])),
            "part": ui.fr_number(
                100 * repartition["population"].iloc[-1]
                / max(repartition["population"].sum(), 1), 0),
        }))
        charts.table_twin(repartition.rename(columns={
            "classe": tr("col_classe"), "cantons": tr("col_cantons"),
            "population": tr("col_population")}))
