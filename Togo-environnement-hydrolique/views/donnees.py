"""Données — les fichiers avant traitement, les recettes, le périmètre.

Aucun texte visible ici : tout vient de `i18n/locales/donnees.json`.

Les profils décrivent les jeux BRUTS, jamais nettoyés : un fichier présenté
après nettoyage paraîtrait plus propre qu'il n'est, et effacerait le travail
qu'il a fallu lui appliquer.
"""

# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui, charts
from socle.ui import filters
from socle.i18n.traduction import t

from utils.data import datasets
from utils import profils, recettes, perimetre

PASTILLE = {"honore": "good", "partiel": "warning", "impossible": "critical"}


def _mega(octets):
    return octets / 1024 / 1024


def render_fichiers():
    tr, tc = t("donnees"), t("commun")
    fiches = profils.profils()
    citees = profils.citees()
    doublon = profils.doublon_raster()

    granularites = sorted({f["granularite"] for f in fiches})
    selection = filters.choix([{
        "cle": "filtre_granularite", "libelle": tr("filtre_granularite"),
        "options": [tr(f"gran_{g}") for g in granularites],
        "placeholder": tc("toutes"),
    }])
    retenues = selection["filtre_granularite"]

    ui.stat_tiles([
        {"value": ui.fr_number(len(fiches)), "label": tr("tuile_charges"),
         "delta": tr("tuile_charges_detail"), "good": None, "icon": "table-2"},
        {"value": ui.fr_number(len(citees)), "label": tr("tuile_citees"),
         "delta": tr("tuile_citees_detail", {
             "mo": ui.fr_number(sum(_mega(c["octets"]) for c in citees), 0)}),
         "good": None, "icon": "search"},
        {"value": ui.fr_number(sum(f["lignes"] for f in fiches)),
         "label": tr("tuile_lignes"), "delta": tr("tuile_lignes_detail"),
         "good": None, "icon": "bar-chart-3"},
    ])

    for fiche in fiches:
        libelle_gran = tr(f"gran_{fiche['granularite']}")

        if retenues and libelle_gran not in retenues:
            continue

        with ui.card(tr(f"fiche_{fiche['cle']}_titre"),
                     tr(f"fiche_{fiche['cle']}_sous_titre"), "table-2"):
            st.markdown(ui.pill("neutral", fiche["code"]), unsafe_allow_html=True)
            st.markdown(tr("fiche_volumetrie", {
                "lignes": ui.fr_number(fiche["lignes"]),
                "colonnes": ui.fr_number(fiche["colonnes"]),
                "granularite": libelle_gran,
                "periode": tr(f"periode_{fiche['periode']}"),
                "format": tr(f"format_{fiche['format']}"),
                "completude": ui.fr_number(fiche["completude"], 0),
                "mo": ui.fr_number(_mega(fiche["octets"]), 1),
            }))
            ui.note(tr(f"fiche_{fiche['cle']}_permet"))
            ui.note(tr(f"fiche_{fiche['cle']}_ne_permet_pas"))

            if fiche["colonnes_vides"]:
                ui.note(tr("fiche_colonnes_vides", {
                    "nombre": len(fiche["colonnes_vides"]),
                    "liste": ", ".join(fiche["colonnes_vides"][:6]),
                }))

    with ui.card(tr("carte_citees_titre"), tr("carte_citees_sous_titre"), "search"):
        cadre = pd.DataFrame([
            {"ressource": tr(f"citee_{c['cle']}"),
             "mo": round(_mega(c["octets"]), 1),
             "entites": c["entites"] or 0}
            for c in citees
        ])
        charts.bar_h(cadre, "ressource", "mo", unit=" Mo")
        ui.note(tr("note_citees", {
            "mo": ui.fr_number(cadre["mo"].sum(), 0),
            "mailles": ui.fr_number(int(cadre["entites"].max())),
        }))

        if doublon["identique"]:
            ui.note(tr("note_doublon", {
                "mo": ui.fr_number(_mega(doublon["octets_tif"]), 0)}))

        charts.table_twin(cadre.rename(columns={
            "ressource": tr("col_ressource"), "mo": tr("col_poids"),
            "entites": tr("col_entites")}))


def render_recettes():
    tr, tc = t("donnees"), t("commun")
    data = datasets()
    toutes = recettes.toutes(data["cantons"], data["tde"], data["coso"])

    solides = sum(1 for r in toutes if r["recette"] is not None)

    ui.stat_tiles([
        {"value": ui.fr_number(len(toutes)), "label": tr("tuile_recettes"),
         "delta": tr("tuile_recettes_detail"), "good": None, "icon": "search"},
        {"value": ui.fr_number(solides), "label": tr("tuile_solides"),
         "delta": tr("tuile_solides_detail",
                     {"seuil": recettes.SEUIL_CANTONS}),
         "good": True, "icon": "flag"},
        {"value": ui.fr_number(len(toutes) - solides),
         "label": tr("tuile_ecartees"), "delta": tr("tuile_ecartees_detail"),
         "good": None if solides == len(toutes) else False, "icon": "table-2"},
    ])

    for entree in toutes:
        cle, recette = entree["cle"], entree["recette"]

        with ui.card(tr(f"recette_{cle}_titre"), tr(f"recette_{cle}_sous_titre"),
                     "search"):
            if recette is None:
                st.markdown(ui.pill("critical", tr("recette_sous_seuil")), unsafe_allow_html=True)
                ui.note(tr("recette_sous_seuil_detail",
                           {"seuil": recettes.SEUIL_CANTONS}))
                continue

            assez = recette["observations"] >= recette["seuil"]
            st.markdown(
                ui.pill("good" if assez else "warning",
                        tr("recette_solide") if assez else tr("recette_fragile")),
                unsafe_allow_html=True,
            )

            st.markdown(tr("recette_declaration", {
                "ingredients": " · ".join(recette["ingredients"]),
                "cle": recette["cle"],
                "observations": ui.fr_number(recette["observations"]),
                "seuil": recette["seuil"],
            }))
            ui.note(tr(f"recette_{cle}_note"))
            charts.table_twin(recette["table"].head(50))


def render_perimetre():
    tr, tc = t("donnees"), t("commun")
    resultats = perimetre.audit()
    compte = perimetre.compte()
    ecart = perimetre.ecart_publication()

    ui.stat_tiles([
        {"value": ui.fr_number(compte["honore"]), "label": tr("tuile_honores"),
         "delta": tr("tuile_honores_detail"), "good": True, "icon": "flag"},
        {"value": ui.fr_number(compte["partiel"]), "label": tr("tuile_partiels"),
         "delta": tr("tuile_partiels_detail"), "good": None, "icon": "search"},
        {"value": ui.fr_number(compte["impossible"]),
         "label": tr("tuile_impossibles"),
         "delta": tr("tuile_impossibles_detail"), "good": False,
         "icon": "table-2"},
    ])

    with ui.card(tr("carte_audit_titre"), tr("carte_audit_sous_titre"), "flag"):
        ui.note(tr("note_audit_methode"))

        for resultat in resultats:
            st.markdown(f"**{tr(resultat['cle'] + '_titre')}**")
            st.markdown(ui.pill(PASTILLE[resultat["verdict"]],
                                tr(f"verdict_{resultat['verdict']}")),
                        unsafe_allow_html=True)

            preuve = resultat["preuve"]
            ui.note(tr("preuve_trouvee", {
                "fichiers": ", ".join(sorted({p["fichier"] for p in preuve})),
                "nombre": len(preuve),
            }) if preuve else tr("preuve_introuvable"))

    with ui.card(tr("carte_dictionnaire_titre"),
                 tr("carte_dictionnaire_sous_titre"), "table-2"):
        cadre = pd.DataFrame([
            {"famille": tr(f"famille_{nom}"), "champs": len(champs)}
            for nom, champs in ecart["familles"].items()
        ])
        charts.bar_h(cadre, "famille", "champs", unit=tr("unite_champs"))
        ui.note(tr("note_dictionnaire", {
            "decrits": ecart["decrits"], "publies": ecart["communs"],
            "absents": ecart["absents"],
            "part": ui.fr_number(ecart["part_publiee"], 0),
        }))
        charts.table_twin(cadre.rename(columns={
            "famille": tr("col_famille"), "champs": tr("col_champs")}))
