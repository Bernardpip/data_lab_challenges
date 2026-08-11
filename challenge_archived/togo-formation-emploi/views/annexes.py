"""Annexes — sources, méthodologie, conditions d'affichage et crédits.

Tout ce qui permet de refaire, vérifier ou contester les analyses : d'où vient
chaque chiffre, ce qui a été nettoyé, et ce que les données ne permettent pas
de dire.

Les structures ci-dessous ne portent plus que ce qui n'est PAS du texte : la
clé du jeu chargé, l'URL, et les identifiants de traduction. Les libellés
vivent dans `i18n/locales/annexes.json`.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle.ui import filters
from socle.ui import card, note
from utils.data import datasets
from socle.i18n.traduction import t


# L'énoncé du concours. Cité comme les sources de données le sont : par son
# adresse, pour qu'un lecteur puisse confronter le tableau de bord à ce qui
# était demandé plutôt qu'à ce qu'on en rapporte ici.
CHALLENGE_URL = "https://datalab.gouv.tg/data-challenges/defis/education-defi-2"


# Les 9 ressources ouvertes mobilisées — une entrée par FICHIER réellement
# téléchargé, y compris les deux ressources annexes du jeu DEFT-TG (liste par
# statut et dictionnaire des champs) souvent oubliées des inventaires.
# La neuvième (DICES-TG) a été ajoutée après les huit autres : c'est la seule
# qui porte les indicateurs de l'objectif n°2 du cahier des charges.
SOURCES = [
    {
        "cle": "formations",
        "i18n": "src_formations",
        "producteur": "producteur_ministere",
        "origine": "origine_ministere",
        "url": "https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-etablissements-de-formations-techniques-au-togo/#/resources/41c1f1bf-f034-4bb3-88ea-663d80cb47b6",
    },
    {
        "cle": None,
        "i18n": "src_controle",
        "producteur": "producteur_ministere",
        "origine": "origine_ministere",
        "url": "https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-etablissements-de-formations-techniques-au-togo/#/resources/dacd0d8f-42db-44b1-aa4d-b16f50da7839",
    },
    {
        "cle": "formations_detail",
        "i18n": "src_dictionnaire",
        "producteur": "producteur_ministere",
        "origine": "origine_ministere",
        "url": "https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-etablissements-de-formations-techniques-au-togo/#/resources",
    },
    {
        "cle": "superieur",
        "i18n": "src_superieur",
        "producteur": "producteur_portail",
        "origine": "origine_portail",
        "url": "https://opendata.gouv.tg/fr/datasets/donnee-ouverte-sur-la-repartition-des-etablissements-denseignement-superieur-ayant-fonctionne-par-type-statut-et-localisation-geographique-au-togo/",
    },
    {
        "cle": "budget",
        "i18n": "src_budget",
        "producteur": "producteur_portail",
        "origine": "origine_portail",
        "url": "https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-le-budget-de-lenseignement-superieur-et-budget-national-votes-et-executes-au-togo/",
    },
    {
        "cle": "depenses",
        "i18n": "src_depenses",
        "producteur": "producteur_bm",
        "origine": "origine_bm",
        "url": "https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-depenses-publiques-par-etudiant-dans-lenseignement-superieur-au-togo/",
    },
    {
        "cle": "inscriptions",
        "i18n": "src_inscriptions",
        "producteur": "producteur_bm",
        "origine": "origine_bm",
        "url": "https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-inscriptions-scolaires-enseignement-superieur-brut-au-togo/",
    },
    {
        "cle": "indicateurs_sup",
        "i18n": "src_indicateurs",
        "producteur": "producteur_portail",
        "origine": "origine_portail",
        "url": "https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-les-indicateurs-cles-de-lenseignement-superieur-au-togo/20250108-152242/observationdata-fspjmfg.csv",
    },
    {
        "cle": "chomage",
        "i18n": "src_chomage",
        "producteur": "producteur_bm_oit",
        "origine": "origine_bm",
        "url": "https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-le-chomage-des-diplomes-de-lenseignement-superieur-au-togo-de-la-population-active-totale-diplomee-de-lenseignement-superieur/",
    },
]


# Le nettoyage, décrit ligne à ligne. Sous forme de données plutôt que de
# tableau figé : c'est ce qui permet de le filtrer par fichier, et d'éviter
# qu'il diverge du code de `utils/clean.py` sans qu'on s'en aperçoive.
# `champ` reste littéral quand c'est un nom de colonne du fichier source — un
# identifiant technique ne se traduit pas ; `champ_i18n` sert quand c'est une
# description.
NETTOYAGE = [
    {"fichier": "fichier_technique", "champ": "`activite_statut`",
     "i18n": "net_statut"},
    {"fichier": "fichier_technique", "champ": "`etablissement_categorie`",
     "i18n": "net_categorie"},
    {"fichier": "fichier_technique", "champ": "`Nsp`, `N/a`, `Neant`",
     "i18n": "net_sentinelles"},
    {"fichier": "fichier_technique", "champ": "`etab_creation_date`",
     "i18n": "net_date"},
    {"fichier": "fichier_technique", "champ": "`terrain`, `toilette_type`",
     "i18n": "net_terrain"},
    {"fichier": "fichier_technique", "champ": "`geometry`",
     "i18n": "net_geometry"},
    {"fichier": "fichier_superieur", "champ_i18n": "net_agregats_champ",
     "i18n": "net_agregats"},
    {"fichier": "fichier_budget", "champ": "`Unit`", "i18n": "net_unit"},
    {"fichier": "fichier_indicateurs", "champ": "`Unit`", "i18n": "net_unit_sup"},
    {"fichier": "fichier_indicateurs", "champ_i18n": "net_feminisation_champ",
     "i18n": "net_feminisation"},
    {"fichier": "fichier_series", "champ_i18n": "net_vides_champ",
     "i18n": "net_vides"},
]


def _origine(source):
    """Qui produit réellement la donnée, derrière le portail qui la publie.

    Trois séries transitent par opendata.gouv.tg mais sont produites par la
    Banque mondiale : la distinction compte, car elle explique leur format
    (une mesure par an, des années entières vides) et leurs lacunes.
    """

    return t("annexes")(source["origine"])


def render_sources():
    tr, tf, tc = t("annexes"), t("filtres"), t("commun")
    data = datasets()

    origines = sorted({_origine(s) for s in SOURCES})
    etats = [tr("etat_chargee"), tr("etat_controle")]

    selection = filters.choix([
        {"libelle": tf("producteur"), "cle": "filtre_source_origine",
         "placeholder": tc("tous"), "options": origines,
         "aide": tr("aide_producteur")},
        {"libelle": tf("usage"), "cle": "filtre_source_etat",
         "placeholder": tc("tous"), "options": etats},
    ])

    def passe(source):
        etat = tr("etat_chargee") if source["cle"] else tr("etat_controle")
        return (filters.retenu(selection["filtre_source_origine"], _origine(source))
                and filters.retenu(selection["filtre_source_etat"], etat))

    retenues = [s for s in SOURCES if passe(s)]

    if not retenues:
        st.info(tr("info_aucune_ressource"))
        return

    sous_titre = (
        tr("carte_sources_sous_titre") if len(retenues) == len(SOURCES)
        else tr("carte_sources_sous_titre_filtre",
                {"retenues": len(retenues), "total": len(SOURCES)})
    )

    with card(tr("carte_sources_titre"), sous_titre, "table-2"):
        for source in retenues:
            jeu = data.get(source["cle"]) if source["cle"] else None
            volume = (
                tr("volume", {"lignes": jeu.shape[0], "colonnes": jeu.shape[1]})
                if jeu is not None else tr("volume_non_chargee")
            )

            st.markdown(
                '<div style="padding:12px 0;border-bottom:1px solid var(--kg-color-border-light);">'
                f'<div style="font-size:var(--kg-fs-lg);font-weight:600;">'
                f'{tr(source["i18n"] + "_titre")}</div>'
                '<div style="color:var(--kg-color-text-muted);font-size:var(--kg-fs-xs);'
                f'margin-top:2px;">{tr(source["producteur"])} · {volume}</div>'
                '<div style="color:var(--kg-color-text-secondary);margin-top:6px;">'
                f'<b>{tr("libelle_contenu")}</b> {tr(source["i18n"] + "_contenu")}</div>'
                '<div style="color:var(--kg-color-text-secondary);margin-top:2px;">'
                f'<b>{tr("libelle_usage")}</b> {tr(source["i18n"] + "_usage")}</div>'
                f'<div style="margin-top:6px;"><a href="{source["url"]}" target="_blank" '
                'style="color:var(--kg-color-link);font-size:var(--kg-fs-xs);'
                'word-break:break-all;">'
                f'{source["url"]}</a></div>'
                "</div>",
                unsafe_allow_html=True
            )

        note(tr("note_sources"))


def render_methodologie():
    tr, tf, tc = t("annexes"), t("filtres"), t("commun")

    fichiers = sorted({tr(l["fichier"]) for l in NETTOYAGE})

    selection = filters.choix([
        {"libelle": tf("fichier"), "cle": "filtre_nettoyage_fichier",
         "placeholder": tc("tous"), "options": fichiers,
         "aide": tr("aide_fichier_nettoyage")},
    ])["filtre_nettoyage_fichier"]

    retenues = [l for l in NETTOYAGE
                if filters.retenu(selection, tr(l["fichier"]))]

    sous_titre = (
        tr("carte_nettoyage_sous_titre") if len(retenues) == len(NETTOYAGE)
        else tr("carte_nettoyage_sous_titre_filtre",
                {"retenues": len(retenues), "total": len(NETTOYAGE)})
    )

    with card(tr("carte_nettoyage_titre"), sous_titre, "search"):
        lignes = "\n".join(
            "| {fichier} | {champ} | {probleme} | {traitement} |".format(
                fichier=tr(l["fichier"]),
                champ=l.get("champ") or tr(l["champ_i18n"]),
                probleme=tr(l["i18n"] + "_probleme"),
                traitement=tr(l["i18n"] + "_traitement"),
            )
            for l in retenues
        )

        st.markdown(tr("entete_nettoyage") + "\n" + lignes)

        if any(l["fichier"] == "fichier_superieur" for l in retenues):
            note(tr("note_superieur_contradiction"))

    with card(tr("carte_limites_titre"), tr("carte_limites_sous_titre"), "flag"):
        st.markdown(tr("limites_corps"))
        note(tr("note_limites"))


def render_affichage():
    tr, tc = t("annexes"), t("commun")

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with card(tr("carte_affichage_titre"), tr("carte_affichage_sous_titre"),
                  "settings"):
            st.markdown(tr("affichage_tableau"))
            note(tr("note_affichage"))

    with droite:
        with card(tr("carte_credits_titre"), tr("carte_credits_sous_titre"),
                  "lightbulb"):
            # Une ligne par mention, libellé en gris et valeur en gras : la
            # même grammaire que les tuiles d'indicateur du tableau de bord.
            # La ligne « Challenge » porte en plus le lien vers l'énoncé —
            # c'est la seule mention qui renvoie à un document opposable.
            defi = (
                f'<a href="{CHALLENGE_URL}" target="_blank" '
                'rel="noopener noreferrer" style="color:var(--kg-color-link);">'
                f'{tr("credit_challenge_valeur")}</a>'
            )

            mentions = [
                (tr("credit_realise_par"), "Kokou PIPI"),
                (tr("credit_entreprise"), "Freelance"),
                (tr("credit_pour"), tc("laboratoire")),
                (tr("credit_secteur"), tr("credit_secteur_valeur")),
                (tr("credit_thematique"), tr("credit_thematique_valeur")),
                (tr("credit_challenge"), defi),
                (tr("credit_periode"), tr("credit_periode_valeur")),
                (tr("credit_produit"), tc("marque")),
            ]

            lignes = "".join(
                '<div style="display:flex;gap:10px;align-items:baseline;">'
                f'<span style="flex:0 0 108px;color:var(--kg-color-text-muted);">'
                f'{libelle}</span><b>{valeur}</b></div>'
                for libelle, valeur in mentions
            )

            st.markdown(f'<div style="line-height:1.9;">{lignes}</div>',
                        unsafe_allow_html=True)

            # Devise de l'auteur, non attribuée : elle clôt le bloc d'identité,
            # au-dessus de la note de provenance qui traite d'autre chose.
            # Volontairement discrète — italique, gris de retrait, sans
            # guillemets typographiques ajoutés par le code : la ponctuation
            # appartient au texte traduit, qui ne suit pas les mêmes règles
            # d'une langue à l'autre.
            st.markdown(
                '<div style="margin:14px 0 12px;padding-top:12px;'
                'border-top:1px solid var(--kg-color-border-light);'
                'color:var(--kg-color-text-muted);font-style:italic;'
                'font-size:var(--kg-fs-xs);">'
                f'{tr("credit_devise")}</div>',
                unsafe_allow_html=True
            )

            note(tr("note_donnees_credits"))

        with card(tr("carte_pile_titre"), tr("carte_pile_sous_titre"), "table-2"):
            st.markdown(tr("pile_corps"))
