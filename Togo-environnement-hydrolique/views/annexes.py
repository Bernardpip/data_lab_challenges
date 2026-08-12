"""Annexes — sources, méthodologie, conditions d'affichage.

Aucun texte visible ici : tout vient de `i18n/locales/annexes.json`.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui, charts
from socle.ui import filters
from socle.i18n.traduction import t

import pandas as pd

from utils import contexte, analytics, perimetre
from utils.data import datasets

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


def render_preuves():
    """Ce que la façade affirme, vérifié pièce par pièce.

    L'affiche pose trois constats en une page ; ici chacun est ramené à son
    fichier et à son décompte. C'est la seule vue du tableau de bord dont le
    lecteur attendu n'est pas le décideur mais le contradicteur.
    """

    tr, tc = t("annexes"), t("commun")
    data = datasets()
    ecart = perimetre.ecart_publication()

    ui.stat_tiles([
        {"value": f'{ecart["communs"]} / {ecart["decrits"]}',
         "label": tr("preuve_tuile_champs"),
         "delta": tr("preuve_tuile_champs_detail",
                     {"absents": ecart["absents"]}),
         "good": False, "icon": "table-2"},
        {"value": "42 / 388", "label": tr("preuve_tuile_fri"),
         "delta": tr("preuve_tuile_fri_detail"), "good": None, "icon": "search"},
        {"value": ui.fr_number(len(analytics.cantons_prioritaires(
            data["cantons"], data["tde"], data["coso"]))),
         "label": tr("preuve_tuile_prio"),
         "delta": tr("preuve_tuile_prio_detail"), "good": False, "icon": "flag"},
    ])

    # ── Preuve 1 : les champs décrits et non diffusés ───────────────────────
    with ui.card(tr("preuve_champs_titre"), tr("preuve_champs_sous_titre"),
                 "table-2"):
        familles = pd.DataFrame([
            {"famille": tr(f"famille_{cle}"), "champs": len(noms),
             "detail": " · ".join(noms)}
            for cle, noms in ecart["familles"].items() if noms
        ])

        if not familles.empty:
            charts.bar_h(familles, "famille", "champs",
                         unit=tr("unite_champs"))

        ui.note(tr("preuve_champs_note", {
            "decrits": ecart["decrits"], "publies": ecart["communs"],
            "absents": ecart["absents"],
        }))

        # Les NOMS, pas un décompte : « 26 champs manquent » se conteste,
        # « `fonctionnalite`, `debit`, `maintenance_societe` manquent » se
        # vérifie en ouvrant le dictionnaire du producteur.
        for cle, noms in ecart["familles"].items():
            if noms:
                st.markdown(f"**{tr(f'famille_{cle}')}** — `" +
                            "`, `".join(noms) + "`")

    # ── Preuve 2 : les seuils officiels contre les quantiles ────────────────
    with ui.card(tr("preuve_seuils_titre"), tr("preuve_seuils_sous_titre"),
                 "flag"):
        officiel = analytics.population_par_classe(data["cantons"])
        lisible = officiel.assign(
            classe=officiel["classe_officielle"].map(
                lambda c: t("synthese")(f"classe_off_{c}")))

        charts.bar_h(lisible, "classe", "cantons",
                     unit=tr("unite_cantons"), trier=False)
        ui.note(tr("preuve_seuils_note"))
        charts.table_twin(lisible[["classe", "cantons", "population"]].rename(
            columns={"classe": tr("col_classe"), "cantons": tr("col_cantons"),
                     "population": tr("col_population")}))

    # ── Preuve 3 : l'indice publié est-il reproductible ? ───────────────────
    with ui.card(tr("preuve_fri_titre"), tr("preuve_fri_sous_titre"), "search"):
        formes = analytics.reconstitution_fri(data["cantons"])
        detail, avec_zero, total = analytics.zeros_composantes(data["cantons"])

        lisible = formes.assign(
            forme=formes["forme"].map(lambda f: tr(f"forme_{f}")),
            variance=(100 * formes["r2"]).round(1))

        charts.bar_h(lisible, "forme", "variance", unit="%", trier=False)
        ui.note(tr("preuve_fri_note", {
            "sans_zero": int(total - avec_zero), "total": total,
            "avec_zero": avec_zero,
        }))
        charts.table_twin(lisible[["forme", "variance", "cantons"]].rename(
            columns={"forme": tr("col_forme"), "variance": tr("col_variance"),
                     "cantons": tr("col_cantons")}))

        ui.note(tr("preuve_fri_zeros", {
            "urban": int(detail.loc[detail["composante"] == "norm_urban",
                                    "cantons_a_zero"].iloc[0]),
            "build": int(detail.loc[detail["composante"] == "norm_build",
                                    "cantons_a_zero"].iloc[0]),
        }))
