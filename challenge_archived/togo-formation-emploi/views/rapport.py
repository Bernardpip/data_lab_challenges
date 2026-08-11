"""Rapport — la lecture continue des analyses, en trois temps.

Le tableau de bord répond à des questions ponctuelles ; le rapport tient le
raisonnement d'un bout à l'autre : ce qu'on cherchait, ce que les données
disent, ce qu'il faut en faire. Chaque chiffre cité est calculé en direct
depuis les jeux nettoyés — aucun n'est figé dans le texte.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle.ui import card, note, stat_tiles, fr_number, pill, repere_externe
from utils.data import datasets, bruts
from utils import analytics, contexte, perimetre
from socle.i18n.traduction import t


# Verdict d'un indicateur → (genre de pastille, clé de libellé). La couleur ne
# porte jamais seule le sens : elle est toujours doublée du libellé, traduit.
_VERDICTS = {
    perimetre.HONORE: ("good", "verdict_honore"),
    perimetre.PARTIEL: ("warning", "verdict_partiel"),
    perimetre.IMPOSSIBLE: ("critical", "verdict_impossible"),
}


def _chiffres():
    """Tous les repères du rapport, calculés une fois."""

    data = datasets()
    formations = data["formations"]

    faits = analytics.concentration(formations)
    sup = analytics.superieur_synthese(data["superieur"])
    budget = analytics.execution_budgetaire(data["budget"])
    compare = analytics.execution_comparee(data["budget"])
    infra = analytics.infrastructures(formations)
    reseau = analytics.maillage(formations)
    decennies = analytics.creation_par_decennie(formations)
    series = analytics.ciseaux(data["inscriptions"], data["depenses"], base=1998)

    inscriptions = data["inscriptions"]
    depenses = data["depenses"]
    chomage = data["chomage"]

    return {
        "formations": formations,
        "faits": faits,
        "sup": sup,
        "budget": budget,
        "compare": compare,
        "infra": infra,
        "reseau": reseau,
        "decennies": decennies,
        "acces_indice": series[0]["y"][-1] if series else None,
        "depense_indice": series[1]["y"][-1] if len(series) > 1 else None,
        "inscription_debut": inscriptions.iloc[0],
        "inscription_fin": inscriptions.iloc[-1],
        "depense_debut": depenses.iloc[0],
        "depense_fin": depenses.iloc[-1],
        "chomage_fin": chomage.iloc[-1],
        "chomage_pic": chomage.loc[chomage["valeur"].idxmax()],
    }


# ─── Introduction ───────────────────────────────────────────────────────────

def render_intro():
    tr = t("rapport")
    c = _chiffres()

    stat_tiles([
        {"label": tr("tuile_jeux"), "value": "9", "icon": "table-2",
         "delta": tr("tuile_jeux_detail"), "good": True},
        {"label": tr("tuile_etablissements"),
         "value": fr_number(c["faits"]["total"]), "icon": "building-2",
         "delta": tr("tuile_etablissements_detail",
                     {"localites": c["reseau"]["localites"]}), "good": True},
        {"label": tr("tuile_periode"), "value": "1971", "unit": "→ 2025",
         "icon": "trending-up", "delta": tr("tuile_periode_detail")},
        {"label": tr("tuile_granularite"),
         "value": fr_number(c["reseau"]["cantons"]),
         "unit": tr("tuile_granularite_unite"),
         "icon": "map-pin", "delta": tr("tuile_granularite_detail")},
    ])

    with card(tr("carte_intro_titre"), tr("carte_intro_sous_titre"), "flag"):
        st.markdown(tr("intro_question"))
        st.markdown(tr("intro_materiau"))
        note(tr("note_nettoyage"))

    with card(tr("carte_demarche_titre"), tr("carte_demarche_sous_titre"),
              "search"):
        st.markdown(tr("demarche_principes"))

    _render_perimetre()


def _render_perimetre():
    """1.4 — l'audit indicateur par indicateur du cahier des charges.

    Placé dans l'introduction, et non relégué en annexe : un lecteur doit
    savoir ce que le travail peut établir AVANT de lire les constats, pas après.
    """

    tr = t("rapport")
    inventaire = perimetre.audit(bruts())
    compte, ecart = inventaire["compte"], inventaire["ecart"]

    with card(
        tr("carte_perimetre_titre"),
        tr("carte_perimetre_sous_titre", {"total": inventaire["total"]}),
        "search",
    ):
        stat_tiles([
            {"label": tr("tuile_honores"),
             "value": str(compte[perimetre.HONORE]),
             "unit": f'/ {inventaire["total"]}', "icon": "bar-chart-3",
             "delta": tr("tuile_honores_detail"), "good": True},
            {"label": tr("tuile_partiels"),
             "value": str(compte[perimetre.PARTIEL]),
             "unit": f'/ {inventaire["total"]}', "icon": "flag",
             "delta": tr("tuile_partiels_detail")},
            {"label": tr("tuile_impossibles"),
             "value": str(compte[perimetre.IMPOSSIBLE]),
             "unit": f'/ {inventaire["total"]}', "icon": "search",
             "delta": tr("tuile_impossibles_detail"), "good": False},
        ])

        lignes = []
        objectif_courant = None

        for entree in inventaire["lignes"]:
            if entree["objectif"] != objectif_courant:
                objectif_courant = entree["objectif"]
                lignes.append(
                    '<div style="margin:14px 0 4px;font-weight:600;'
                    'color:var(--kg-color-text);">'
                    f'{objectif_courant}</div>'
                )

            genre, cle_libelle = _VERDICTS[entree["verdict"]]

            lignes.append(
                '<div style="display:flex;gap:12px;align-items:baseline;'
                'padding:7px 0 7px 14px;'
                'border-bottom:1px solid var(--kg-color-border-light);">'
                f'<span style="flex:0 0 96px;">{pill(genre, tr(cle_libelle))}</span>'
                '<div style="flex:1;">'
                f'<div>{entree["indicateur"]}</div>'
                '<div style="color:var(--kg-color-text-secondary);'
                'font-size:var(--kg-fs-xs);margin-top:2px;">'
                f'{entree["motif"]}</div>'
                '<div style="color:var(--kg-color-text-muted);'
                'font-size:var(--kg-fs-xs);margin-top:2px;">'
                f'{tr("libelle_source", {"source": entree["source"]})}</div>'
                "</div></div>"
            )

        st.markdown("".join(lignes), unsafe_allow_html=True)

    with card(tr("carte_causes_titre"), tr("carte_causes_sous_titre"), "flag"):
        st.markdown(tr("causes_corps", {
            "publies": ecart["publies"],
            "decrits": ecart["decrits"],
            "communs": ecart["communs"],
            "part": fr_number(ecart["part_publiee"], 1),
            "absents": ecart["absents"],
            "champs_eleves": "`, `".join(ecart["familles"]["Effectifs d'élèves"]),
            "nb_enseignants": len(ecart["familles"]["Personnel enseignant"]),
            "nb_sexe": len(ecart["familles"]["Ventilation par sexe"]),
        }))

        note(tr("note_consequence", {"absents": ecart["absents"]}))
        note(tr("note_verification"))


# ─── Développement ──────────────────────────────────────────────────────────

def render_developpement():
    tr = t("rapport")
    c = _chiffres()
    faits, sup, infra = c["faits"], c["sup"], c["infra"]

    with card(tr("carte_dev_titre"), tr("carte_dev_sous_titre"), "bar-chart-3"):
        st.markdown(tr("dev_constat_1", {
            "region_tete": faits["region_tete"],
            "part_tete": fr_number(faits["part_region_tete"], 1),
            "part_deux": fr_number(faits["part_deux_prefectures"], 1),
            "region_queue": faits["region_queue"],
            "etab_queue": faits["etab_region_queue"],
            "part_lome": fr_number(sup["part_lome"], 0),
            "part_prive": fr_number(sup["part_prive"], 0),
        }))

        st.markdown(tr("dev_constat_2", {
            "acces": fr_number(c["acces_indice"] / 100, 1),
            "perte": fr_number(100 - c["depense_indice"], 0),
            "depense_debut": fr_number(c["depense_debut"]["valeur"], 0),
            "depense_fin": fr_number(c["depense_fin"]["valeur"], 0),
        }))

        st.markdown(tr("dev_constat_3", {
            "moyenne_es": fr_number(c["compare"]["taux_es"].mean(), 1),
            "moyenne_nat": fr_number(c["compare"]["taux_national"].mean(), 1),
            "taux_2018": fr_number(c["budget"].iloc[-1]["taux"], 1),
            "part_prive": fr_number(sup["part_prive"], 0),
        }))

        st.markdown(tr("dev_constat_4", {
            "part_sport": fr_number(infra["part_sport"], 0),
            "part_wc": fr_number(infra["part_wc"], 0),
            "part_inconnu": fr_number(infra["part_sanitaire_inconnu"], 0),
            "part_foncier": fr_number(infra["part_prive"], 0),
        }))

    with card(tr("carte_chomage_titre"), tr("carte_chomage_sous_titre"), "flag"):
        st.markdown(tr("chomage_corps", {
            "taux": fr_number(c["chomage_fin"]["valeur"], 1),
            "annee": int(c["chomage_fin"]["annee"]),
            "pic": fr_number(c["chomage_pic"]["valeur"], 1),
            "annee_pic": int(c["chomage_pic"]["annee"]),
        }))

        for cle in ("jeunes_sans_emploi", "sous_emploi", "informel"):
            repere_externe(contexte.repere(cle))


# ─── Conclusion ─────────────────────────────────────────────────────────────

def render_conclusion():
    tr = t("rapport")
    c = _chiffres()
    faits, sup = c["faits"], c["sup"]

    with card(tr("carte_conclusion_titre"), tr("carte_conclusion_sous_titre"),
              "lightbulb"):
        st.markdown(tr("conclusion_reponse", {
            "part_tete": fr_number(faits["part_region_tete"], 0),
            "part_lome": fr_number(sup["part_lome"], 0),
            "part_prive": fr_number(sup["part_prive"], 0),
        }))

        inventaire = perimetre.audit(bruts())
        ecart = inventaire["ecart"]

        st.markdown(tr("conclusion_limites", {
            "total": inventaire["total"],
            "honores": inventaire["compte"][perimetre.HONORE],
            "partiels": inventaire["compte"][perimetre.PARTIEL],
            "impossibles": inventaire["compte"][perimetre.IMPOSSIBLE],
            "decrits": ecart["decrits"],
            "publies": ecart["publies"],
            "absents": ecart["absents"],
        }))

        note(tr("note_decision", {"absents": ecart["absents"]}))

    with card(tr("carte_suites_titre"), tr("carte_suites_sous_titre"), "flag"):
        st.markdown(tr("suites_corps"))
