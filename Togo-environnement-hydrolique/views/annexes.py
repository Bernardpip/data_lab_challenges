"""Annexes — sources, méthodologie, conditions d'affichage.

Aucun texte visible ici : tout vient de `i18n/locales/annexes.json`.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui
from socle.ui import filters
from socle.i18n.traduction import t

from utils import contexte

# Les cinq ressources de l'énoncé, avec leur sigle et leur producteur.
SOURCES = [
    {"cle": "DCEF", "code": "DCEF-TG", "producteur": "TdE",
     "url": "https://opendata.gouv.tg/fr/datasets/"
            "donnees-ouvertes-sur-les-chateaux-deau-forages-tde/"},
    {"cle": "PCIAEPH", "code": "PCIAEPH-TG", "producteur": "Projet COSO",
     "url": "https://opendata.gouv.tg/fr/datasets/"
            "projet-coso-infrastructures-dalimentation-en-eau-potable-"
            "et-hydraulique-au-togo/"},
    {"cle": "ISRI", "code": "ISRI-TG", "producteur": "Data AI Lab",
     "url": "https://opendata.gouv.tg/fr/datasets/"
            "indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/"},
    {"cle": "DVECA", "code": "DVECA-TG", "producteur": "TdE",
     "url": "https://opendata.gouv.tg/s/resources/"
            "donnees-ouvertes-sur-les-ventes-deau-par-categorie-dabonnes-"
            "en-m3-au-togo/"},
    {"cle": "DPSSA", "code": "DPSSA-TG", "producteur": "INSEED",
     "url": "https://opendata.gouv.tg/s/resources/"
            "donnees-ouvertes-sur-la-population-par-subdivision-administrative-"
            "du-togo/"},
]


def render_sources():
    tr, tc = t("annexes"), t("commun")

    producteurs = sorted({s["producteur"] for s in SOURCES})
    selection = filters.choix([{
        "cle": "filtre_producteur", "libelle": tr("filtre_producteur"),
        "options": producteurs, "placeholder": tc("tous"),
    }])
    retenus = selection["filtre_producteur"]

    for source in SOURCES:
        if retenus and source["producteur"] not in retenus:
            continue

        with ui.card(tr(f"source_{source['cle']}_titre"),
                     tr(f"source_{source['cle']}_sous_titre"), "table-2"):
            st.markdown(ui.pill("neutral", source["code"]), unsafe_allow_html=True)
            st.markdown(tr(f"source_{source['cle']}_corps",
                           {"producteur": source["producteur"]}))
            st.markdown(f"[{tr('voir_sur_portail')}]({source['url']})")

    ui.section_header(tr("contexte_titre"), tr("contexte_sous_titre"), "flag")

    for repere in contexte.reperes():
        ui.repere_externe({
            "valeur": repere["valeur"],
            "libelle": tr(f"repere_{repere['cle']}"),
            "detail": tr(f"repere_{repere['cle']}_detail",
                         {"annee": repere["annee"]}),
            "source": repere["source"],
            "url": repere["url"],
        })


def render_methodologie():
    tr = t("annexes")

    with ui.card(tr("methode_chaine_titre"), tr("methode_chaine_sous_titre"),
                 "search"):
        st.markdown(tr("methode_chaine_corps"))

    with ui.card(tr("methode_regles_titre"), tr("methode_regles_sous_titre"),
                 "flag"):
        for index in range(1, 6):
            st.markdown(f"**{tr(f'regle_{index}_titre')}**")
            st.markdown(tr(f"regle_{index}_corps"))

    with ui.card(tr("methode_jointure_titre"), tr("methode_jointure_sous_titre"),
                 "table-2"):
        st.markdown(tr("methode_jointure_corps"))
        ui.note(tr("methode_jointure_note"))

    with ui.card(tr("methode_classes_titre"), tr("methode_classes_sous_titre"),
                 "bar-chart-3"):
        st.markdown(tr("methode_classes_corps"))
        ui.note(tr("methode_classes_note"))


def render_affichage():
    tr = t("annexes")

    with ui.card(tr("affichage_titre"), tr("affichage_sous_titre"), "settings"):
        st.markdown(tr("affichage_corps"))

    with ui.card(tr("affichage_couleur_titre"),
                 tr("affichage_couleur_sous_titre"), "bar-chart-3"):
        st.markdown(tr("affichage_couleur_corps"))
        ui.note(tr("affichage_couleur_note"))
