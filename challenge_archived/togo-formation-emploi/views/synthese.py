"""Vue d'ensemble — la lecture nationale : où est l'offre, et l'accès a-t-il
progressé au même rythme que les moyens ?

Aucun texte visible n'est écrit ici : tout vient de `i18n/locales/synthese.json`
via `t("synthese")`. Les valeurs calculées sont passées en paramètres — un
commentaire d'analyse cite ses chiffres, il ne peut donc pas être une chaîne
figée.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import charts
from socle.ui import filters
from utils import barres
from socle.ui import card, stat_tiles, note, fr_number, repere_externe
from utils.data import datasets, apply_filters
from utils import analytics, contexte
from socle.i18n.traduction import t


def _pluriel(nombre):
    """Marque du pluriel, injectée comme paramètre.

    Le français et l'anglais accordent tous deux au-delà de un : une seule
    clé suffit. Une langue à règles différentes demanderait deux entrées
    distinctes plutôt qu'un paramètre.
    """

    return "s" if nombre > 1 else ""


def render_synthese():
    tr = t("synthese")
    tc = t("commun")

    data = datasets()
    formations = data["formations"]

    # La barre cadre la lecture territoriale. Les indicateurs nationaux
    # (accès, chômage, réseau du supérieur) n'existent qu'au niveau national :
    # ils ne bougent pas, et une note le dit sous les tuiles.
    selection = barres.territoriale(formations)
    filtre = apply_filters(formations, selection)

    if filtre.empty:
        st.info(tc("aucun_etablissement"))
        return

    faits = analytics.concentration(filtre)
    sup = analytics.superieur_synthese(data["superieur"])
    chomage = data["chomage"]
    inscriptions = data["inscriptions"]

    dernier_chomage = chomage.iloc[-1]
    pic_chomage = chomage.loc[chomage["valeur"].idxmax()]
    derniere_inscription = inscriptions.iloc[-1]
    premiere_inscription = inscriptions.iloc[0]

    complet = len(filtre) == len(formations)
    detail = {
        "total": fr_number(len(formations)),
        "regions": faits["regions"],
        "prefectures": faits["prefectures"],
        "s_region": _pluriel(faits["regions"]),
        "s_prefecture": _pluriel(faits["prefectures"]),
    }

    stat_tiles([
        {
            "label": tr("tuile_etablissements"),
            "value": fr_number(faits["total"]),
            "icon": "building-2",
            "delta": tr("tuile_etablissements_detail" if complet
                        else "tuile_etablissements_detail_filtre", detail),
            "good": True,
        },
        {
            "label": tr("tuile_concentration", {"region": faits["region_tete"]}),
            "value": fr_number(faits["part_region_tete"], 0),
            "unit": "%",
            "icon": "map-pin",
            "delta": tr("tuile_concentration_detail",
                        {"part": fr_number(faits["part_deux_prefectures"], 0)}),
            "good": False,
        },
        {
            "label": tr("tuile_superieur", {"annee": sup["annee"]}),
            "value": fr_number(sup["total"]),
            "icon": "graduation-cap",
            "delta": tr("tuile_superieur_detail",
                        {"part": fr_number(sup["part_lome"], 0)}),
            "good": False,
        },
        {
            "label": tr("tuile_inscription",
                        {"annee": int(derniere_inscription["annee"])}),
            "value": fr_number(derniere_inscription["valeur"], 1),
            "unit": "%",
            "icon": "trending-up",
            "delta": tr("tuile_inscription_detail", {
                "facteur": fr_number(
                    derniere_inscription["valeur"] / premiere_inscription["valeur"], 0),
                "annee": int(premiere_inscription["annee"]),
            }),
            "good": True,
        },
        {
            "label": tr("tuile_chomage", {"annee": int(dernier_chomage["annee"])}),
            "value": fr_number(dernier_chomage["valeur"], 1),
            "unit": "%",
            "icon": "flag",
            "delta": tr("tuile_chomage_detail", {
                "ecart": fr_number(pic_chomage["valeur"] - dernier_chomage["valeur"], 1),
                "annee": int(pic_chomage["annee"]),
            }),
            "good": True,
        },
    ])

    if not complet:
        note(tr("note_indicateurs_nationaux"))

    gauche, droite = st.columns([1, 1], gap="small")

    with gauche:
        with card(tr("carte_couverture_titre"),
                  tr("carte_couverture_sous_titre"), "map-pin"):
            regions = analytics.par_region(filtre)

            # Forme « emphase » : l'histoire est UNE région, pas cinq séries.
            charts.bar_h(regions, "region", "etablissements",
                         highlight=faits["region_tete"])

            if faits["regions"] > 1:
                # Comparaison tête / queue — elle n'a de sens qu'à plusieurs
                # régions, sinon la même région serait ses deux extrémités.
                note(tr("note_couverture", {
                    "region_tete": faits["region_tete"],
                    "part": fr_number(faits["part_region_tete"], 0),
                    "perimetre": tr("perimetre_pays" if complet
                                    else "perimetre_selection"),
                    "region_queue": faits["region_queue"],
                    "nombre": faits["etab_region_queue"],
                }))
            else:
                note(tr("note_couverture_une_region", {
                    "region": faits["region_tete"],
                    "total": faits["total"],
                    "prefectures": faits["prefectures"],
                }))

            charts.table_twin(
                regions.assign(part=regions["part"].round(1))
                       .rename(columns={
                           "region": tr("colonne_region"),
                           "etablissements": tr("colonne_etablissements"),
                           "part": tr("colonne_part"),
                       })
            )

    with droite:
        with card(tr("carte_grille_titre"), tr("carte_grille_sous_titre"),
                  "bar-chart-3"):
            grille = analytics.grille_region_categorie(filtre)
            charts.heatmap(grille)

            par_filiere = filtre.groupby("categorie").size().sort_values(ascending=False)

            note(tr("note_grille", {
                "part": fr_number(par_filiere.iloc[0] / len(filtre) * 100, 0),
                "modalite": par_filiere.index[0],
            }))
            charts.table_twin(grille.reset_index())

    _carte_rapport(tr)


@st.cache_data(show_spinner=False)
def _rapport_pptx(langue):
    """Le PowerPoint sérialisé, dans la langue demandée.

    Construit en mémoire et jamais écrit sur disque : le conteneur de
    production a un système de fichiers éphémère, et un fichier archivé
    divergerait des données à la première mise à jour des jeux.

    L'import est local à la fonction : `scripts/` n'est pas un module de
    l'application, et le charger au démarrage ferait payer python-pptx à
    toutes les vues alors qu'une seule s'en sert.
    """

    from scripts.generer_presentation import octets

    return octets(langue)


def _carte_rapport(tr):
    """Téléchargement du livrable, dans l'une ou l'autre langue.

    Les deux langues sont offertes SÉPARÉMENT du sélecteur de la barre
    latérale, et non calées dessus : un lecteur consulte volontiers le
    tableau de bord dans sa langue tout en devant transmettre le rapport
    dans l'autre. Les libellés des boutons sont donc des endonymes —
    « Français » reste « Français » en anglais, comme la bascule FR / EN.
    """

    with card(tr("carte_rapport_titre"), tr("carte_rapport_sous_titre"),
              "flag"):
        colonnes = st.columns([2, 2, 8], gap="small")

        for colonne, code in zip(colonnes, ("fr", "en")):
            contenu, nom = _rapport_pptx(code)

            with colonne:
                st.download_button(
                    tr(f"rapport_bouton_{code}"),
                    data=contenu,
                    file_name=nom,
                    mime=("application/vnd.openxmlformats-officedocument"
                          ".presentationml.presentation"),
                    key=f"rapport_pptx_{code}",
                    use_container_width=True,
                )

        note(tr("note_rapport"))


def render_adequation():
    tr = t("synthese")

    data = datasets()

    # Quatre séries d'amplitudes très différentes (accès depuis 1971, budget
    # depuis 2013 seulement) : le décompte affiché à droite du curseur évite
    # de resserrer sans voir qu'on vide une série au passage.
    debut, fin = barres.periode(
        {
            tr("serie_acces"): data["inscriptions"],
            tr("serie_depense"): data["depenses"],
            tr("serie_chomage"): data["chomage"],
            tr("serie_budget"): data["budget"],
        },
        cle="filtre_periode_adequation",
        aide=tr("aide_periode"),
    )

    inscriptions = filters.entre(data["inscriptions"], debut, fin)
    depenses = filters.entre(data["depenses"], debut, fin)
    chomage = filters.entre(data["chomage"], debut, fin)
    budget_source = filters.entre(data["budget"], debut, fin)

    with card(tr("carte_ciseaux_titre"), tr("carte_ciseaux_sous_titre"),
              "trending-up"):
        base = analytics.annee_de_base(inscriptions, depenses, base=debut)
        series = analytics.ciseaux(inscriptions, depenses, base=debut)

        if len(series) < 2 or len(series[0]["x"]) < 2:
            st.info(tr("info_pas_assez_annees_communes"))
        else:
            charts.line_indexed(series, base_year=base)

            note(tr("note_ciseaux", {
                "base": base,
                "acces": fr_number(series[0]["y"][-1] / 100, 1),
                "perte": fr_number(100 - series[1]["y"][-1], 0),
            }))

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with card(tr("carte_chomage_titre"), tr("carte_chomage_sous_titre"),
                  "flag"):
            if chomage.empty:
                st.info(tr("info_chomage_vide"))
            else:
                charts.line_series(
                    [{
                        "name": tr("legende_chomage"),
                        "x": chomage["annee"].tolist(),
                        "y": chomage["valeur"].tolist(),
                    }],
                    unit="%",
                )

                pic = chomage.loc[chomage["valeur"].idxmax()]

                note(tr("note_chomage", {
                    "mesures": len(chomage),
                    "etendue": int(chomage["annee"].max() - chomage["annee"].min()) + 1,
                    "pic": fr_number(pic["valeur"], 1),
                    "annee_pic": int(pic["annee"]),
                }))
                charts.table_twin(
                    chomage.rename(columns={
                        "annee": tr("colonne_annee"),
                        "valeur": tr("colonne_chomage"),
                    })
                )

            repere_externe(contexte.repere("jeunes_sans_emploi"))

    with droite:
        with card(tr("carte_budget_titre"), tr("carte_budget_sous_titre"),
                  "wallet"):
            budget = analytics.execution_budgetaire(budget_source)

            if budget.empty:
                st.info(tr("info_budget_vide"))
            else:
                charts.diverging_bar(
                    budget["annee"].tolist(),
                    budget["ecart"].round(1).tolist(),
                )

                pire = budget.loc[budget["ecart"].idxmin()]

                note(tr("note_budget", {
                    "annee": int(pire["annee"]),
                    "ecart": fr_number(pire["ecart"], 1),
                }))
                charts.table_twin(
                    budget[["annee", "es_vote", "es_execute", "taux"]]
                    .round(1)
                    .rename(columns={
                        "annee": tr("colonne_annee"),
                        "es_vote": tr("colonne_vote"),
                        "es_execute": tr("colonne_execute"),
                        "taux": tr("colonne_execution"),
                    })
                )
