"""Pression démographique et consommation — deux mailles incomparables.

Aucun texte visible ici : tout vient de `i18n/locales/demographie.json`.

La population par canton (2022) et le recensement (2010) ne se recouvrent pas.
Les ventes d'eau, elles, n'ont aucune maille territoriale. Chaque onglet dit
lequel des deux il manipule, et aucun ne les mélange.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui, charts
from socle.charts import maps
from socle.i18n.traduction import t

from utils.data import datasets, apply_filters
from utils import analytics, barres, recettes


def render_pression(avec_carte=True):
    """`avec_carte=False` laisse la carte à l'appelant.

    L'affiche la pose dans sa colonne droite ; la console garde le rendu
    complet. Ici la carte n'est pas dans une colonne : la rendre optionnelle
    suffit, rien d'autre ne se réorganise.
    """

    tr, tc = t("demographie"), t("commun")
    data = datasets()
    cantons = data["cantons"]
    filtre = apply_filters(cantons, barres.territoriale(cantons))

    if filtre.empty:
        st.info(tc("aucun_resultat"))
        return

    rgph = data["population"]
    total_2010 = float(rgph.loc[rgph["libelle"] == "TOGO", "habitants"].sum())
    total_cantons = float(cantons["population"].sum())

    ui.stat_tiles([
        {"value": ui.compact(float(filtre["population"].sum())),
         "label": tr("tuile_population"),
         "delta": tr("tuile_population_detail",
                     {"cantons": ui.fr_number(len(filtre))}),
         "good": None, "icon": "trending-up"},
        {"value": ui.compact(total_2010), "label": tr("tuile_rgph"),
         "delta": tr("tuile_rgph_detail"), "good": None, "icon": "table-2"},
        {"value": ui.fr_number(
            100 * (total_cantons - total_2010) / total_2010, 0), "unit": " %",
         "label": tr("tuile_ecart"), "delta": tr("tuile_ecart_detail"),
         "good": False, "icon": "flag"},
    ])

    if avec_carte:
      with ui.card(tr("carte_population_titre"), tr("carte_population_sous_titre"),
                   "map-pin"):
          maps.choroplethe(
              filtre, valeur="population", cle="carte_population",
              champs=["canton", "prefecture", "population", "risque_pts"],
              libelles=[tr("col_canton"), tr("col_prefecture"),
                        tr("col_population"), tr("col_risque")],
              height=560,
          )
          ui.note(tr("note_population", {
              "premier": str(filtre.loc[filtre["population"].idxmax(), "canton"]),
              "habitants": ui.compact(float(filtre["population"].max())),
          }))

    recette = recettes.croisement_equipement_population(
        filtre, data["tde"], data["coso"])

    if recette is None:
        ui.note(tr("note_densite_insuffisante"))
        return

    # Deux classements reliés : la forme dit QUI change de place entre
    # population et équipement, ce que deux graphes côte à côte ne disent pas.

    with ui.card(tr("carte_pentes_titre"), tr("carte_pentes_sous_titre"), "search"):
        complet = recette["table"]
        rang_pop = complet["population"].rank(ascending=False, method="first")
        rang_eq = complet["ouvrages_10k"].rank(ascending=False, method="first")
        decrocheurs = int(((rang_eq - rang_pop) >= 5).sum())

        charts.pentes_appariees(
            complet, "canton", "population", "ouvrages_10k",
            titre_gauche=tr("pentes_gauche"), titre_droite=tr("pentes_droite"),
            unit_droite=tr("unite_pour_10k"), max_rows=14, decimals=1,
        )
        ui.note(tr("note_pentes", {
            "croisement": ui.fr_number(decrocheurs),
            "observations": ui.fr_number(recette["observations"]),
        }))

    with ui.card(tr("carte_densite_titre"), tr("carte_densite_sous_titre"),
                 "bar-chart-3"):
        table = recette["table"].head(20)
        charts.sucette_h(table, "canton", "ouvrages_10k",
                         unit=tr("unite_pour_10k"), decimals=2)
        ui.note(tr("note_densite", {
            "observations": ui.fr_number(recette["observations"]),
            "seuil": recette["seuil"],
            "faible": str(table.iloc[0]["canton"]),
            "valeur": ui.fr_number(table.iloc[0]["ouvrages_10k"], 2),
        }))
        charts.table_twin(recette["table"].rename(columns={
            "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
            "region": tr("col_region"), "population": tr("col_population"),
            "ouvrages": tr("col_ouvrages"), "ouvrages_10k": tr("col_pour_10k"),
            "risque_pts": tr("col_risque")}))


def render_ventes():
    tr, tc = t("demographie"), t("commun")
    ventes = datasets()["ventes"]

    if ventes.empty:
        st.info(tc("aucune_mesure"))
        return

    debut, fin = barres.periode(
        {tr("serie_ventes"): ventes}, cle="filtre_periode_ventes",
        aide=tr("aide_periode"),
    )
    cadre = ventes[ventes["annee"].between(debut, fin)]

    if cadre.empty:
        st.info(tc("aucune_mesure"))
        return

    par_annee = analytics.ventes_par_annee(cadre)

    ui.stat_tiles([
        {"value": ui.compact(float(cadre["volume_m3"].sum())), "unit": " m³",
         "label": tr("tuile_volume"),
         "delta": tr("tuile_volume_detail", {"debut": debut, "fin": fin}),
         "good": None, "icon": "trending-up"},
        {"value": ui.fr_number(int(cadre["categorie"].nunique())),
         "label": tr("tuile_categories"), "delta": tr("tuile_categories_detail"),
         "good": None, "icon": "table-2"},
        {"value": ui.fr_number(int(par_annee["categories"].iloc[-1])),
         "label": tr("tuile_derniere"),
         "delta": tr("tuile_derniere_detail",
                     {"annee": int(par_annee["annee"].iloc[-1])}),
         "good": None, "icon": "flag"},
    ])

    with ui.card(tr("carte_series_titre"), tr("carte_series_sous_titre"),
                 "trending-up"):
        series = analytics.ventes_series(cadre)

        if not series:
            st.info(tc("aucune_mesure"))
        else:
            charts.line_series(series, x_title=tr("axe_annee"), unit=" m³",
                               height=320)
            ui.note(tr("note_series", {
                "premier": series[0]["name"],
                "volume": ui.compact(float(sum(series[0]["y"]))),
                "categories": len(series),
            }))
            charts.table_twin(cadre.rename(columns={
                "categorie": tr("col_categorie"), "annee": tr("col_annee"),
                "volume_m3": tr("col_volume")})[
                    [tr("col_categorie"), tr("col_annee"), tr("col_volume")]])

    with ui.card(tr("carte_derniere_titre"), tr("carte_derniere_sous_titre"),
                 "bar-chart-3"):
        derniere = analytics.ventes_derniere_annee(cadre)
        charts.bar_h(derniere, "categorie", "volume_m3", unit=" m³")
        ui.note(tr("note_national"))
        charts.table_twin(derniere.rename(columns={
            "categorie": tr("col_categorie"), "volume_m3": tr("col_volume")}))


def carte_population_seule(hauteur=None):
    """La population par canton, pour la colonne droite de l'affiche."""

    tr = t("demographie")
    cantons = datasets()["cantons"]

    for colonne, cle in (("region", "filtre_region"),
                         ("prefecture", "filtre_prefecture")):
        retenues = st.session_state.get(cle) or []

        if retenues:
            cantons = cantons[cantons[colonne].isin(retenues)]

    def dessin(h):
        maps.choroplethe(
            cantons, valeur="population", cle="carte_population_droite",
            champs=["canton", "prefecture", "population", "risque_pts"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_population"), tr("col_risque")],
            height=h,
        )

    maps.carte(tr("carte_population_titre"), cle="population_droite",
               dessin=dessin, sous_titre=tr("carte_population_sous_titre"),
               **({"hauteur": hauteur} if hauteur else {}))
