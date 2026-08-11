"""Recommandations — un ordre de priorité, déclaré comme tel.

Aucun texte visible ici : tout vient de `i18n/locales/recommandations.json`.

Le score de priorisation est une somme de RANGS, pondérée à parts égales. Ce
n'est pas un modèle, et la vue le dit avant d'afficher le classement : lui
prêter une autorité qu'il n'a pas serait la faute la plus coûteuse de ce
tableau de bord, puisque c'est de lui que découleraient des investissements.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui, charts
from socle.i18n.traduction import t

from utils.data import datasets, apply_filters
from utils import barres, recettes, perimetre

# Chaque levier renvoie à la CAUSE du manque qu'il traite. Les causes ne
# s'adressent pas de la même façon : republier ne coûte pas ce que coûte
# enquêter.
LEVIERS = ["republier", "inventorier", "entretenir", "prioriser", "geolocaliser"]


def render_priorites():
    tr, tc = t("recommandations"), t("commun")
    data = datasets()
    cantons = data["cantons"]
    filtre = apply_filters(cantons, barres.territoriale(cantons))

    if filtre.empty:
        st.info(tc("aucun_resultat"))
        return

    recette = recettes.score_de_priorisation(filtre, data["tde"], data["coso"])
    table = recette["table"]

    ui.stat_tiles([
        {"value": ui.fr_number(recette["observations"]),
         "label": tr("tuile_cantons"), "delta": tr("tuile_cantons_detail"),
         "good": None, "icon": "map-pin"},
        {"value": ui.fr_number(recette["equipes"]), "label": tr("tuile_equipes"),
         "delta": tr("tuile_equipes_detail", {
             "part": ui.fr_number(
                 100 * recette["equipes"] / recette["observations"], 0)}),
         "good": False, "icon": "building-2"},
        {"value": str(table.iloc[0]["canton"]), "label": tr("tuile_premier"),
         "delta": tr("tuile_premier_detail",
                     {"score": ui.fr_number(table.iloc[0]["score"], 2)}),
         "good": None, "icon": "flag"},
    ])

    with ui.card(tr("carte_methode_titre"), tr("carte_methode_sous_titre"),
                 "search"):
        ui.note(tr("note_methode"))
        ui.note(tr("note_methode_limite"))

    with ui.card(tr("carte_score_titre"), tr("carte_score_sous_titre"), "flag"):
        top = table.head(20)
        charts.sucette_h(top, "canton", "score", unit="", decimals=3)
        ui.note(tr("note_score", {
            "premier": str(top.iloc[0]["canton"]),
            "region": str(top.iloc[0]["region"]),
            "risque": ui.fr_number(top.iloc[0]["risque_pts"], 1),
            "population": ui.compact(float(top.iloc[0]["population"])),
            "ouvrages": ui.fr_number(int(top.iloc[0]["ouvrages"])),
        }))
        charts.table_twin(table.rename(columns={
            "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
            "region": tr("col_region"), "risque_pts": tr("col_risque"),
            "population": tr("col_population"), "ouvrages": tr("col_ouvrages"),
            "ouvrages_10k": tr("col_pour_10k"), "score": tr("col_score"),
            "rang_risque": tr("col_rang_risque"),
            "rang_population": tr("col_rang_population"),
            "rang_deficit": tr("col_rang_deficit")}))

    with ui.card(tr("carte_composantes_titre"),
                 tr("carte_composantes_sous_titre"), "bar-chart-3"):
        top = table.head(12)
        charts.bar_stacked_h(
            top, "canton",
            ["rang_risque", "rang_population", "rang_deficit"],
            unit="",
        )
        ui.note(tr("note_composantes"))


def render_leviers():
    tr, tc = t("recommandations"), t("commun")
    resultats = perimetre.audit()
    ecart = perimetre.ecart_publication()
    data = datasets()

    ui.stat_tiles([
        {"value": ui.fr_number(ecart["absents"]), "label": tr("tuile_absents"),
         "delta": tr("tuile_absents_detail", {"decrits": ecart["decrits"]}),
         "good": False, "icon": "table-2"},
        {"value": ui.fr_number(int((~data["coso"]["plan_maintenance"]).sum())),
         "label": tr("tuile_sans_plan"), "delta": tr("tuile_sans_plan_detail"),
         "good": False, "icon": "settings"},
        {"value": ui.fr_number(
            int(len(data["coso"]) - data["coso"]["situe"].sum())),
         "label": tr("tuile_sans_position"),
         "delta": tr("tuile_sans_position_detail"), "good": False,
         "icon": "map-pin"},
    ])

    with ui.card(tr("carte_leviers_titre"), tr("carte_leviers_sous_titre"),
                 "lightbulb"):
        for levier in LEVIERS:
            st.markdown(f"**{tr(f'levier_{levier}_titre')}**")
            st.markdown(ui.pill(tr(f"levier_{levier}_pastille_kind"),
                                tr(f"levier_{levier}_pastille")),
                        unsafe_allow_html=True)
            st.markdown(tr(f"levier_{levier}_corps", {
                "absents": ui.fr_number(ecart["absents"]),
                "decrits": ui.fr_number(ecart["decrits"]),
                "sans_plan": ui.fr_number(
                    int((~data["coso"]["plan_maintenance"]).sum())),
                "sans_position": ui.fr_number(
                    int(len(data["coso"]) - data["coso"]["situe"].sum())),
                "cantons": ui.fr_number(len(data["cantons"])),
            }))
            ui.note(tr(f"levier_{levier}_note"))

    with ui.card(tr("carte_verdicts_titre"), tr("carte_verdicts_sous_titre"),
                 "flag"):
        for resultat in resultats:
            if resultat["verdict"] == "honore":
                continue

            st.markdown(f"**{tr(resultat['cle'] + '_rappel')}**")
            ui.note(tr(f"cause_{resultat['cause']}"))
