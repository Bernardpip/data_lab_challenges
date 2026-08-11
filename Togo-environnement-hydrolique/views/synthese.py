"""Vue d'ensemble — ce que le corpus établit, et ce qu'il refuse d'établir.

Aucun texte visible n'est écrit ici : tout vient de `i18n/locales/synthese.json`.

Ces deux onglets n'ont PAS de barre de filtres, et c'est délibéré : ils
décrivent le corpus entier. Un filtre y donnerait l'impression qu'on peut
restreindre un diagnostic qui vaut, précisément, pour tout le pays.
"""

# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui, charts
from socle.charts import maps
from socle.design.tokens import RISQUE_OFFICIEL, RISQUE_CONTOUR, SERIES
from socle.i18n.traduction import t

from utils.data import datasets
from utils import analytics, perimetre, contexte

# Les verdicts de l'audit, traduits en pastilles du socle.
PASTILLE = {"honore": "good", "partiel": "warning", "impossible": "critical"}


def render_diagnostic():
    tr = t("synthese")
    data = datasets()
    faits = analytics.synthese(data["cantons"], data["tde"], data["coso"],
                               data["ventes"])

    ui.stat_tiles([
        {"value": ui.fr_number(faits["cantons"]), "label": tr("tuile_cantons"),
         "delta": tr("tuile_cantons_detail", {"regions": faits["regions"]}),
         "good": None, "icon": "map-pin"},
        {"value": ui.compact(faits["population"]), "label": tr("tuile_population"),
         "delta": tr("tuile_population_detail"), "good": None, "icon": "trending-up"},
        {"value": ui.fr_number(faits["risque_median"], 1), "unit": " pts",
         "label": tr("tuile_risque"),
         "delta": tr("tuile_risque_detail", {
             "canton": faits["canton_le_plus_expose"],
             "max": ui.fr_number(faits["risque_max"], 1)}),
         "good": None, "icon": "flag"},
        {"value": ui.fr_number(faits["cantons_sans_ouvrage"]),
         "label": tr("tuile_sans_ouvrage"),
         "delta": tr("tuile_sans_ouvrage_detail",
                     {"part": ui.fr_number(faits["part_sans_ouvrage"], 0)}),
         "good": False, "icon": "search"},
        {"value": "7 / 33", "label": tr("tuile_publies"),
         "delta": tr("tuile_publies_detail"), "good": False, "icon": "table-2"},
    ])

    # La carte à DROITE, dans une colonne étroite et haute — le gabarit du
    # pilote (?s=technique&t=carto). Le Togo s'étire sur 5,15° de latitude
    # pour 1,9° de longitude : dans un cadre de ~560 × 980 px, c'est la
    # hauteur qui fixe le zoom, et le pays ENTIER entre avec ses marges. En
    # pleine largeur, les mêmes 980 px n'achetaient que des marges vides.
    gauche, droite = st.columns([62, 38], gap="small")

    with gauche:
        # Trois cartes rondes : elles disent d'un regard ce qu'aucun tableau
        # ne dit — que les deux inventaires ne couvrent pas le même pays.
        with ui.card(tr("carte_couverture_titre"),
                     tr("carte_couverture_sous_titre"), "map-pin"):
            maps.cartes_miniatures(data["cantons"], [
                {"libelle": tr("mini_cantons"),
                 "compte": ui.fr_number(faits["cantons"]),
                 "detail": tr("mini_cantons_detail"), "teinte": SERIES[0]},
                {"libelle": tr("mini_tde"),
                 "compte": ui.fr_number(faits["tde_total"]),
                 "detail": tr("mini_tde_detail"), "teinte": SERIES[1],
                 "points": data["tde"]},
                {"libelle": tr("mini_coso"),
                 "compte": ui.fr_number(faits["coso_total"]),
                 "detail": tr("mini_coso_detail",
                              {"situes": faits["coso_situes"]}),
                 "teinte": SERIES[2],
                 "points": data["coso"][data["coso"]["situe"]]},
            ])
            ui.note(tr("note_couverture", {
                "part_maritime": ui.fr_number(faits["tde_part_maritime"], 0),
                "sans": ui.fr_number(faits["cantons_sans_ouvrage"]),
            }))

        with ui.card(tr("carte_parcs_titre"), tr("carte_parcs_sous_titre"),
                     "building-2"):
            fusion = (
                analytics.tde_par_region(data["tde"])
                .rename(columns={"ouvrages": "TdE"})
                .merge(
                    analytics.coso_par_region(data["coso"])
                    .rename(columns={"ouvrages": "COSO"}),
                    on="region", how="outer")
                .fillna(0)
            )

            charts.bar_stacked_h(fusion, "region", ["TdE", "COSO"],
                                 unit=tr("unite_ouvrages"))
            ui.note(tr("note_parcs", {
                "tde": ui.fr_number(faits["tde_total"]),
                "part_maritime": ui.fr_number(faits["tde_part_maritime"], 0),
                "coso": ui.fr_number(faits["coso_total"]),
            }))
            charts.table_twin(fusion.rename(columns={"region": tr("col_region")}))

        with ui.card(tr("carte_publication_titre"),
                     tr("carte_publication_sous_titre"), "table-2"):
            ecart = perimetre.ecart_publication()
            cadre = pd.DataFrame([
                {"etat": tr("champs_publies"), "champs": int(ecart["communs"])},
                {"etat": tr("champs_absents"), "champs": int(ecart["absents"])},
            ])

            charts.bar_h(cadre, "etat", "champs", unit=tr("unite_champs"),
                         highlight=tr("champs_absents"))
            ui.note(tr("note_publication", {
                "decrits": ecart["decrits"], "publies": ecart["communs"],
                "part": ui.fr_number(ecart["part_publiee"], 0),
            }))
            charts.table_twin(cadre.rename(columns={
                "etat": tr("col_etat"), "champs": tr("col_champs")}))

    with droite:
        with ui.card(tr("carte_risque_titre"), tr("carte_risque_sous_titre"),
                     "map-pin"):
            bornes, _ = maps.choroplethe(
                data["cantons"], valeur="risque_pts", cle="carte_diagnostic",
                champs=["canton", "prefecture", "risque_pts", "population"],
                libelles=[tr("col_canton"), tr("col_prefecture"),
                          tr("col_risque"), tr("col_population")],
                height=980, rampe=RISQUE_OFFICIEL,
                couleur_contour=RISQUE_CONTOUR,
            )

            if bornes:
                repartition = analytics.repartition_par_classe(
                    data["cantons"], bornes,
                    [tr(f"classe_{i}") for i in range(1, len(bornes))],
                )
                maps.legende_paliers(
                    bornes, rampe=RISQUE_OFFICIEL, libelle=tr("legende_titre"),
                    unite=" pts", decimales=1,
                    effectifs=repartition["cantons"].tolist(),
                )
                ui.note(tr("note_risque", {
                    "seuil": ui.fr_number(bornes[-2], 1),
                    "cantons": ui.fr_number(int(repartition["cantons"].iloc[-1])),
                    "population": ui.compact(
                        float(repartition["population"].iloc[-1])),
                }))
                charts.table_twin(repartition.rename(columns={
                    "classe": tr("col_classe"), "cantons": tr("col_cantons"),
                    "population": tr("col_population")}))

    ui.section_header(tr("contexte_titre"), tr("contexte_sous_titre"), "flag")

    for repere in contexte.reperes()[:3]:
        ui.repere_externe({
            "valeur": repere["valeur"],
            "libelle": tr(f"repere_{repere['cle']}"),
            "detail": tr(f"repere_{repere['cle']}_detail",
                         {"annee": repere["annee"]}),
            "source": repere["source"],
            "url": repere["url"],
        })


def render_limites():
    tr = t("synthese")
    data = datasets()
    resultats = perimetre.audit()
    compte = perimetre.compte()

    ui.stat_tiles([
        {"value": ui.fr_number(compte["honore"]), "label": tr("tuile_honores"),
         "delta": tr("tuile_honores_detail"), "good": True, "icon": "flag"},
        {"value": ui.fr_number(compte["partiel"]), "label": tr("tuile_partiels"),
         "delta": tr("tuile_partiels_detail"), "good": None, "icon": "search"},
        {"value": ui.fr_number(compte["impossible"]),
         "label": tr("tuile_impossibles"),
         "delta": tr("tuile_impossibles_detail"), "good": False, "icon": "table-2"},
    ])

    gauche, droite = st.columns([62, 38], gap="small")

    with gauche:
        with ui.card(tr("carte_limites_titre"), tr("carte_limites_sous_titre"),
                     "flag"):
            for resultat in resultats:
                cle = resultat["cle"]

                st.markdown(f"**{tr(f'{cle}_titre')}**")
                st.markdown(ui.pill(PASTILLE[resultat["verdict"]],
                                    tr(f"verdict_{resultat['verdict']}")),
                            unsafe_allow_html=True)
                # Les mesures sont déjà comptées par `perimetre.audit` ; la
                # vue ne fait que les mettre en forme pour l'interpolation.
                st.markdown(tr(f"{cle}_detail", {
                    str(cle_mesure): (
                        ui.fr_number(valeur, 0) if isinstance(valeur, float)
                        else ui.fr_number(valeur) if isinstance(valeur, int)
                        else str(valeur)
                    )
                    for cle_mesure, valeur in resultat["mesures"].items()
                }))

                if resultat["cause"]:
                    ui.note(tr(f"cause_{resultat['cause']}"))

        with ui.card(tr("carte_refus_titre"), tr("carte_refus_sous_titre"),
                     "search"):
            for index in range(1, 5):
                ui.note(tr(f"refus_{index}"))

    with droite:
        # PAS la carte du risque : l'onglet parle de ce que le corpus ne dit
        # pas, et sa carte est celle de l'angle mort — foncé là où au moins
        # un ouvrage est recensé, clair partout ailleurs. Le grand vide clair
        # au centre du pays EST le constat.
        with ui.card(tr("limites_carte_titre"), tr("limites_carte_sous_titre"),
                     "map-pin"):
            couverture = analytics.couverture(data["cantons"], data["tde"],
                                              data["coso"])

            # Classes LINÉAIRES à deux paliers, jamais des quantiles : sur un
            # indicateur 0/1 dont 85 % des valeurs sont nulles, toutes les
            # bornes de quantiles jusqu'au 80e centile valent 0 — la carte
            # dégénérerait en une classe unique, uniformément claire.
            maps.choroplethe(
                couverture, valeur="couvert", cle="carte_angle_mort",
                champs=["canton", "prefecture", "region", "ouvrages"],
                libelles=[tr("col_canton"), tr("col_prefecture"),
                          tr("col_region"), tr("col_ouvrages")],
                height=980, nombre=2, methode="lineaire",
            )

            # Pas de legende_paliers : des bornes « 0 / 0,5 / 1 » ne disent
            # rien sur un indicateur binaire. La note porte les effectifs.
            ui.note(tr("note_angle_mort", {
                "couverts": ui.fr_number(int(couverture["couvert"].sum())),
                "sans": ui.fr_number(int((couverture["couvert"] == 0).sum())),
                "part": ui.fr_number(
                    100 * (couverture["couvert"] == 0).sum() / len(couverture), 0),
            }))

            equipes = (
                couverture[couverture["ouvrages"] > 0]
                .drop(columns="geometry")
                [["canton", "prefecture", "region", "ouvrages"]]
                .sort_values("ouvrages", ascending=False)
                .reset_index(drop=True)
            )
            charts.table_twin(equipes.rename(columns={
                "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
                "region": tr("col_region"), "ouvrages": tr("col_ouvrages")}))
