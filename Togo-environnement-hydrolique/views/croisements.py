"""Croisements — ce que la jointure au canton autorise, et rien de plus.

Aucun texte visible ici : tout vient de `i18n/locales/croisements.json`.

Chaque carte affiche le nombre d'observations de sa recette et son seuil de
solidité. Une recette sous le seuil n'est pas tracée : on dit qu'elle l'est,
plutôt que de dessiner une tendance sur trop peu de points.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui, charts
from socle.i18n.traduction import t

from utils.data import datasets, apply_filters
from utils import barres, recettes


def _cadres():
    data = datasets()
    cantons = data["cantons"]
    selection = barres.territoriale(cantons)

    return data, apply_filters(cantons, selection)


def render_ouvrages_risque():
    tr, tc = t("croisements"), t("commun")
    data, cantons = _cadres()

    if cantons.empty:
        st.info(tc("aucun_resultat"))
        return

    recette = recettes.croisement_ouvrages_risque(cantons, data["tde"], data["coso"])

    if recette is None:
        ui.note(tr("note_sous_seuil", {"seuil": recettes.SEUIL_CANTONS}))
        return

    table = recette["table"]

    ui.stat_tiles([
        {"value": ui.fr_number(recette["observations"]),
         "label": tr("tuile_cantons"),
         "delta": tr("tuile_cantons_detail", {"seuil": recette["seuil"]}),
         "good": None, "icon": "search"},
        {"value": ui.fr_number(recette["ouvrages"]), "label": tr("tuile_ouvrages"),
         "delta": tr("tuile_ouvrages_detail"), "good": None, "icon": "building-2"},
        {"value": ui.fr_number(int(len(cantons) - recette["observations"])),
         "label": tr("tuile_sans"),
         "delta": tr("tuile_sans_detail", {
             "part": ui.fr_number(
                 100 * (len(cantons) - recette["observations"]) / len(cantons), 0)}),
         "good": False, "icon": "flag"},
    ])

    with ui.card(tr("carte_recette_titre"), tr("carte_recette_sous_titre"), "search"):
        ui.note(tr("note_ingredients", {
            "ingredients": " · ".join(recette["ingredients"]),
            "cle": recette["cle"],
            "observations": ui.fr_number(recette["observations"]),
            "seuil": recette["seuil"],
        }))

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with ui.card(tr("carte_nuage_titre"), tr("carte_nuage_sous_titre"), "search"):
            if len(table) < 3:
                ui.note(tc("pas_assez_de_points"))
            else:
                charts.scatter_fit(
                    table["risque_pts"], table["ouvrages"], labels=table["canton"],
                    x_titre=tr("axe_risque"), y_titre=tr("axe_ouvrages"),
                )
                ui.note(tr("note_nuage", {"n": ui.fr_number(len(table))}))

    with droite:
        with ui.card(tr("carte_top_titre"), tr("carte_top_sous_titre"), "flag"):
            top = table.head(15)
            charts.sucette_h(top, "canton", "risque_pts", unit=" pts", decimals=1)
            ui.note(tr("note_top", {
                "canton": str(top.iloc[0]["canton"]),
                "risque": ui.fr_number(top.iloc[0]["risque_pts"], 1),
                "ouvrages": ui.fr_number(int(top.iloc[0]["ouvrages"])),
            }))

    charts.table_twin(table.rename(columns={
        "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
        "region": tr("col_region"), "risque_pts": tr("col_risque"),
        "population": tr("col_population"), "ouvrages": tr("col_ouvrages"),
        "parcs": tr("col_parcs")}))


def render_maintenance():
    tr, tc = t("croisements"), t("commun")
    data, cantons = _cadres()

    if cantons.empty:
        st.info(tc("aucun_resultat"))
        return

    coso = data["coso"]

    from utils import analytics

    plans = analytics.maintenance(coso)
    sans = int((~coso["plan_maintenance"]).sum())

    ui.stat_tiles([
        {"value": ui.fr_number(sans), "label": tr("tuile_sans_plan"),
         "delta": tr("tuile_sans_plan_detail",
                     {"part": ui.fr_number(100 * sans / len(coso), 0)}),
         "good": False, "icon": "settings"},
        {"value": ui.fr_number(int(coso["plan_maintenance"].sum())),
         "label": tr("tuile_avec_plan"), "delta": tr("tuile_avec_plan_detail"),
         "good": True, "icon": "flag"},
        {"value": ui.fr_number(int(coso["fonds_entretien"].notna().sum())),
         "label": tr("tuile_fonds"),
         "delta": tr("tuile_fonds_detail",
                     {"total": ui.fr_number(len(coso))}),
         "good": None, "icon": "table-2"},
    ])

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with ui.card(tr("carte_plan_titre"), tr("carte_plan_sous_titre"),
                     "settings"):
            lisible = plans.assign(plan=plans["plan"].map(
                lambda p: tr(f"plan_{p}")))
            charts.bar_h(lisible, "plan", "ouvrages", unit=tr("unite_ouvrages"),
                         highlight=tr("plan_sans"))
            ui.note(tr("note_plan", {
                "sans": ui.fr_number(sans),
                "total": ui.fr_number(len(coso)),
                "part": ui.fr_number(100 * sans / len(coso), 0),
            }))
            charts.table_twin(lisible.rename(columns={
                "plan": tr("col_plan"), "ouvrages": tr("col_ouvrages")}))

    with droite:
        with ui.card(tr("carte_fonds_titre"), tr("carte_fonds_sous_titre"),
                     "search"):
            nuage = coso[["localite", "cout_estime", "fonds_entretien"]].dropna()

            if len(nuage) < 3:
                ui.note(tc("pas_assez_de_points"))
            else:
                charts.scatter_fit(
                    nuage["cout_estime"], nuage["fonds_entretien"],
                    labels=nuage["localite"],
                    x_titre=tr("axe_cout"), y_titre=tr("axe_fonds"),
                )
                ui.note(tr("note_fonds", {
                    "n": ui.fr_number(len(nuage)),
                    "part": ui.fr_number(100 * len(nuage) / len(coso), 0),
                }))
                charts.table_twin(nuage.rename(columns={
                    "localite": tr("col_localite"), "cout_estime": tr("col_cout"),
                    "fonds_entretien": tr("col_fonds")}))

    recette = recettes.croisement_maintenance_risque(cantons, coso)

    with ui.card(tr("carte_risque_titre"), tr("carte_risque_sous_titre"), "flag"):
        if recette is None:
            ui.note(tr("note_sous_seuil", {"seuil": recettes.SEUIL_CANTONS}))
            return

        table = recette["table"].head(15)
        charts.sucette_h(table, "canton", "sans_plan", unit=tr("unite_ouvrages"))
        ui.note(tr("note_risque", {
            "observations": ui.fr_number(recette["observations"]),
            "seuil": recette["seuil"],
            "ouvrages": ui.fr_number(recette["ouvrages"]),
            "canton": str(table.iloc[0]["canton"]),
            "risque": ui.fr_number(table.iloc[0]["risque_pts"], 1),
        }))
        charts.table_twin(recette["table"].rename(columns={
            "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
            "region": tr("col_region"), "risque_pts": tr("col_risque"),
            "population": tr("col_population"), "sans_plan": tr("col_sans_plan")}))
