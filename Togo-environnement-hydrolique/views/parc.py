"""Parc d'ouvrages — deux inventaires partiels, tenus séparés.

Aucun texte visible ici : tout vient de `i18n/locales/parc.json`.

Les deux parcs ne sont JAMAIS additionnés dans un total présenté comme
national : 65 des 67 ouvrages TdE sont en Maritime, les 218 microprojets COSO
sont au Nord. Le corpus ne contient pas d'inventaire national des points
d'eau, et le tableau de bord ne doit pas laisser croire le contraire.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui, charts
from socle.charts import maps
from socle.i18n.traduction import t

from utils.data import datasets, apply_filters
from utils import analytics, barres


def render_tde():
    tr, tc = t("parc"), t("commun")
    data = datasets()
    filtre = apply_filters(data["tde"], barres.parc_tde(data["tde"]))

    if filtre.empty:
        st.info(tc("aucun_resultat"))
        return

    ui.stat_tiles([
        {"value": ui.fr_number(len(filtre)), "label": tr("tde_tuile_total"),
         "delta": tr("tde_tuile_total_detail",
                     {"cantons": int(filtre["canton"].nunique())}),
         "good": None, "icon": "building-2"},
        {"value": ui.fr_number(int(filtre["lat"].notna().sum())),
         "label": tr("tde_tuile_situes"),
         "delta": tr("tde_tuile_situes_detail"), "good": True, "icon": "map-pin"},
        {"value": ui.fr_number(
            100 * (filtre["region"] == "Maritime").sum() / len(filtre), 0),
         "unit": " %", "label": tr("tde_tuile_maritime"),
         "delta": tr("tde_tuile_maritime_detail"), "good": False, "icon": "flag"},
        {"value": "8 / 33", "label": tr("tde_tuile_champs"),
         "delta": tr("tde_tuile_champs_detail"), "good": False, "icon": "table-2"},
    ])

    gauche, droite = st.columns([2, 1], gap="small")

    with gauche:
        with ui.card(tr("tde_carte_titre"), tr("tde_carte_sous_titre"), "map-pin"):
            maps.points(
                filtre, cle="carte_tde", height=560,
                message_vide=tc("aucun_point_localise"),
                infobulle=lambda row: (
                    f'<b>{row["ouvrage"]}</b><br>'
                    f'{row["canton"]} · {row["prefecture"]}<br>'
                    f'<span style="color:#475569;">{row["region"]}</span>'
                ),
            )
            ui.note(tr("tde_note_carte", {
                "total": ui.fr_number(len(filtre)),
                "cantons": ui.fr_number(int(filtre["canton"].nunique())),
            }))

    with droite:
        with ui.card(tr("tde_carte_nature_titre"),
                     tr("tde_carte_nature_sous_titre"), "building-2"):
            nature = analytics.tde_par_nature(filtre)
            charts.bar_h(nature, "nature", "ouvrages", unit=tr("unite_ouvrages"))
            ui.note(tr("tde_note_nature", {
                "nsp": ui.fr_number(int(
                    nature.loc[nature["nature"] == tc("non_renseigne"), "ouvrages"].sum()
                )),
                "total": ui.fr_number(len(filtre)),
            }))
            charts.table_twin(nature.rename(columns={
                "nature": tr("col_nature"), "ouvrages": tr("col_ouvrages")}))

        with ui.card(tr("tde_carte_regions_titre"),
                     tr("tde_carte_regions_sous_titre"), "bar-chart-3"):
            regions = analytics.tde_par_region(filtre)
            charts.bar_h(regions, "region", "ouvrages", unit=tr("unite_ouvrages"))
            charts.table_twin(regions.rename(columns={
                "region": tr("col_region"), "ouvrages": tr("col_ouvrages")}))


def render_coso():
    tr, tc = t("parc"), t("commun")
    data = datasets()
    filtre = apply_filters(data["coso"], barres.parc_coso(data["coso"]))

    if filtre.empty:
        st.info(tc("aucun_resultat"))
        return

    situes = int(filtre["situe"].sum())

    ui.stat_tiles([
        {"value": ui.fr_number(len(filtre)), "label": tr("coso_tuile_total"),
         "delta": tr("coso_tuile_total_detail",
                     {"cantons": int(filtre["canton"].nunique())}),
         "good": None, "icon": "building-2"},
        {"value": ui.fr_number(situes), "label": tr("coso_tuile_situes"),
         "delta": tr("coso_tuile_situes_detail", {
             "part": ui.fr_number(100 * situes / len(filtre), 0)}),
         "good": False, "icon": "map-pin"},
        {"value": ui.fr_number(int((~filtre["plan_maintenance"]).sum())),
         "label": tr("coso_tuile_sans_plan"),
         "delta": tr("coso_tuile_sans_plan_detail", {
             "part": ui.fr_number(
                 100 * (~filtre["plan_maintenance"]).sum() / len(filtre), 0)}),
         "good": False, "icon": "settings"},
        {"value": ui.compact(float(filtre["population_desservie"].sum())),
         "label": tr("coso_tuile_beneficiaires"),
         "delta": tr("coso_tuile_beneficiaires_detail", {
             "renseignes": ui.fr_number(
                 int(filtre["population_desservie"].notna().sum()))}),
         "good": None, "icon": "trending-up"},
    ])

    gauche, droite = st.columns([2, 1], gap="small")

    with gauche:
        with ui.card(tr("coso_carte_titre"), tr("coso_carte_sous_titre"), "map-pin"):
            maps.points(
                filtre[filtre["situe"]], cle="carte_coso", height=560,
                message_vide=tc("aucun_point_localise"),
                infobulle=lambda row: (
                    f'<b>{row["localite"]}</b><br>'
                    f'{row["canton"]} · {row["prefecture"]}<br>'
                    f'<span style="color:#475569;">{row["type_ouvrage"]}</span>'
                ),
            )
            # Le chiffre des non-situés est LA limite de cette carte : sans
            # lui, un lecteur croirait voir tout le parc.
            ui.note(tr("coso_note_carte", {
                "situes": ui.fr_number(situes),
                "total": ui.fr_number(len(filtre)),
                "absents": ui.fr_number(len(filtre) - situes),
            }))

    with droite:
        with ui.card(tr("coso_carte_type_titre"), tr("coso_carte_type_sous_titre"),
                     "building-2"):
            types = analytics.coso_par_type(filtre)
            charts.sucette_h(types, "type_ouvrage", "ouvrages",
                             unit=tr("unite_ouvrages"), max_rows=8)
            ui.note(tr("coso_note_type", {
                "premier": str(types.iloc[0]["type_ouvrage"]),
                "part": ui.fr_number(
                    100 * types.iloc[0]["ouvrages"] / len(filtre), 0),
            }))
            charts.table_twin(types.rename(columns={
                "type_ouvrage": tr("col_type"), "ouvrages": tr("col_ouvrages")}))

        with ui.card(tr("coso_carte_avancement_titre"),
                     tr("coso_carte_avancement_sous_titre"), "bar-chart-3"):
            avancement = analytics.coso_par_avancement(filtre)
            charts.bar_h(avancement, "avancement", "ouvrages",
                         unit=tr("unite_ouvrages"))
            charts.table_twin(avancement.rename(columns={
                "avancement": tr("col_avancement"), "ouvrages": tr("col_ouvrages")}))


def render_technique():
    tr, tc = t("parc"), t("commun")
    data = datasets()
    filtre = apply_filters(data["coso"], barres.parc_coso(data["coso"],
                                                          avec_annee=False))

    if filtre.empty:
        st.info(tc("aucun_resultat"))
        return

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with ui.card(tr("tech_carte_nuage_titre"), tr("tech_carte_nuage_sous_titre"),
                     "search"):
            nuage = analytics.coso_technique(filtre)

            if len(nuage) < 3:
                ui.note(tc("pas_assez_de_points"))
            else:
                charts.scatter_fit(
                    nuage["profondeur"], nuage["debit"], labels=nuage["localite"],
                    x_titre=tr("axe_profondeur"), y_titre=tr("axe_debit"),
                )
                ui.note(tr("tech_note_nuage", {
                    "n": ui.fr_number(len(nuage)),
                    "total": ui.fr_number(len(filtre)),
                }))
                charts.table_twin(nuage.rename(columns={
                    "localite": tr("col_localite"), "canton": tr("col_canton"),
                    "region": tr("col_region"), "type_ouvrage": tr("col_type"),
                    "profondeur": tr("col_profondeur"), "debit": tr("col_debit")}))

    with droite:
        with ui.card(tr("tech_carte_completude_titre"),
                     tr("tech_carte_completude_sous_titre"), "table-2"):
            completude = analytics.completude_coso(filtre)
            lisible = completude.assign(
                champ=completude["champ"].map(lambda c: tr(f"champ_{c}"))
            )
            charts.sucette_h(lisible, "champ", "part", unit=" %")
            ui.note(tr("tech_note_completude", {
                "moins": str(lisible.iloc[0]["champ"]),
                "part": ui.fr_number(lisible.iloc[0]["part"], 0),
            }))
            charts.table_twin(lisible.rename(columns={
                "champ": tr("col_champ"), "renseignes": tr("col_renseignes"),
                "total": tr("col_total"), "part": tr("col_part")}))
