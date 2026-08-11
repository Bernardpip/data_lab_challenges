"""Financement & insertion — moyens publics engagés, et ce qu'ils produisent.

Aucun texte visible n'est écrit ici : tout vient de
`i18n/locales/financement.json` via `t("financement")`.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import charts
from socle.ui import filters
from utils import barres
from socle.ui import card, stat_tiles, note, fr_number, repere_externe
from utils.data import datasets
from utils import analytics, contexte
from socle.i18n.traduction import t


def _exercices(data, cle, extras=None):
    """Barre de période commune aux vues budgétaires.

    Le budget n'est documenté que sur six exercices : le curseur y sert moins à
    explorer qu'à isoler une sous-période, typiquement pour vérifier si un
    constat tient sans l'exercice 2018, très atypique.
    """

    tr = t("financement")

    resultat = barres.periode(
        {tr("serie_exercices"): data["budget"]}, cle=cle,
        aide=tr("aide_exercices"), extras=extras,
    )

    if extras:
        debut, fin, selections = resultat
        return filters.entre(data["budget"], debut, fin), debut, fin, selections

    debut, fin = resultat
    return filters.entre(data["budget"], debut, fin), debut, fin


def render_budget():
    tr = t("financement")

    data = datasets()
    source, debut, fin = _exercices(data, "filtre_periode_budget")
    budget = analytics.execution_budgetaire(source)

    if len(budget) < 2:
        st.info(tr("info_deux_exercices"))
        return

    dernier = budget.iloc[-1]

    stat_tiles([
        {"label": tr("tuile_vote", {"annee": int(dernier["annee"])}),
         "value": fr_number(dernier["es_vote"] / 1000, 1),
         "unit": tr("unite_md_fcfa"), "icon": "wallet",
         "delta": tr("tuile_vote_detail", {"variation": fr_number(
             (dernier["es_vote"] / budget.iloc[-2]["es_vote"] - 1) * 100, 0)}),
         "good": True},
        {"label": tr("tuile_execution"),
         "value": fr_number(dernier["taux"], 1), "unit": "%",
         "icon": "trending-up",
         "delta": tr("tuile_execution_detail",
                     {"ecart": fr_number(dernier["ecart"], 1)}),
         "good": False},
        {"label": tr("tuile_part_national"),
         "value": fr_number(dernier["part_national"], 1), "unit": "%",
         "icon": "flag", "delta": tr("tuile_part_national_detail")},
        {"label": tr("tuile_part_education"),
         "value": fr_number(dernier["part_education"], 1), "unit": "%",
         "icon": "graduation-cap", "delta": tr("tuile_part_education_detail")},
    ])

    with card(tr("carte_budget_titre"),
              tr("carte_budget_sous_titre", {"debut": int(budget.iloc[0]["annee"]),
                                             "fin": int(dernier["annee"])}),
              "wallet"):
        charts.line_series(
            [
                {"name": tr("legende_vote"), "x": budget["annee"].tolist(),
                 "y": budget["es_vote"].tolist()},
                {"name": tr("legende_execute"), "x": budget["annee"].tolist(),
                 "y": budget["es_execute"].tolist()},
            ],
            unit="M FCFA", height=280, end_labels=False,
        )
        # L'exercice le plus mal exécuté de la période retenue — sur la série
        # complète c'est 2018, mais le constat doit se recalculer si l'on
        # retire cet exercice.
        pire = budget.loc[budget["ecart"].idxmin()]
        autres = budget[budget["annee"] != pire["annee"]]

        note(tr("note_budget", {
            "annee": int(pire["annee"]),
            "ecart": fr_number(abs(pire["ecart"]), 1),
            "manquant": fr_number((pire["es_vote"] - pire["es_execute"]) / 1000, 1),
            "min": fr_number(abs(autres["ecart"]).min(), 1),
            "max": fr_number(abs(autres["ecart"]).max(), 1),
        }))
        charts.table_twin(
            budget[["annee", "es_vote", "es_execute", "taux", "part_national"]]
            .round(1)
            .rename(columns={
                "annee": tr("colonne_annee"),
                "es_vote": tr("colonne_vote"),
                "es_execute": tr("colonne_execute"),
                "taux": tr("colonne_execution"),
                "part_national": tr("colonne_part_national"),
            })
        )

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with card(tr("carte_ecart_titre"), tr("carte_ecart_sous_titre"),
                  "bar-chart-3"):
            charts.diverging_bar(budget["annee"].tolist(),
                                 budget["ecart"].round(1).tolist())
            meilleur = budget.loc[budget["ecart"].idxmax()]

            note(tr("note_ecart", {
                "min": fr_number(abs(meilleur["ecart"]), 1),
                "annee_min": int(meilleur["annee"]),
                "max": fr_number(abs(pire["ecart"]), 1),
                "annee_max": int(pire["annee"]),
            }))

    with droite:
        with card(tr("carte_priorite_titre"), tr("carte_priorite_sous_titre"),
                  "trending-up"):
            charts.line_series(
                [{"name": tr("legende_part_national"),
                  "x": budget["annee"].tolist(),
                  "y": budget["part_national"].round(2).tolist()}],
                unit="%", height=240,
            )
            note(tr("note_priorite", {
                "min": fr_number(budget["part_national"].min(), 1),
                "max": fr_number(budget["part_national"].max(), 1),
            }))


def render_execution():
    tr = t("financement")
    data = datasets()

    niveaux_libelles = [tr("niveau_superieur"), tr("niveau_education"),
                        tr("niveau_national")]

    # Second filtre, dans la MÊME rangée : quels niveaux comparer. C'est le
    # cœur de la vue — retirer le budget national fait disparaître le point de
    # comparaison qui corrige la lecture du taux d'exécution du supérieur.
    budget, debut, fin, selections = _exercices(
        data, "filtre_periode_execution",
        extras=[{
            "libelle": t("filtres")("niveaux"), "cle": "filtre_niveaux_budget",
            "placeholder": t("commun")("tous"), "options": niveaux_libelles,
            "aide": tr("aide_niveaux"),
        }],
    )
    niveaux = selections["filtre_niveaux_budget"]

    if len(budget) < 2:
        st.info(tr("info_deux_exercices_comparaison"))
        return

    compare = analytics.execution_comparee(budget)
    poids = analytics.poids_education(budget)
    subvention = analytics.subvention_prive(budget)

    moyenne_es = compare["taux_es"].mean()
    moyenne_nat = compare["taux_national"].mean()
    dernier_poids = poids.iloc[-1]

    stat_tiles([
        {"label": tr("tuile_exec_superieur"),
         "value": fr_number(moyenne_es, 1), "unit": "%", "icon": "trending-up",
         "delta": tr("tuile_exec_superieur_detail",
                     {"ecart": fr_number(moyenne_es - moyenne_nat, 1)}),
         "good": True},
        {"label": tr("tuile_exec_etat"),
         "value": fr_number(moyenne_nat, 1), "unit": "%", "icon": "wallet",
         "delta": tr("tuile_exec_etat_detail"), "good": False},
        {"label": tr("tuile_part_educ"),
         "value": fr_number(dernier_poids["part_educ_national"], 1), "unit": "%",
         "icon": "graduation-cap",
         "delta": tr("tuile_part_educ_detail",
                     {"annee": int(dernier_poids["annee"])})},
        {"label": tr("tuile_subvention"), "value": "0", "unit": "FCFA",
         "icon": "flag",
         "delta": tr("tuile_subvention_detail", {"annees": subvention["annees"]}),
         "good": False},
    ])

    with card(tr("carte_compare_titre"),
              tr("carte_compare_sous_titre",
                 {"debut": int(compare["annee"].min()),
                  "fin": int(compare["annee"].max())}),
              "bar-chart-3"):
        toutes = [
            {"name": niveaux_libelles[0], "x": compare["annee"].tolist(),
             "y": compare["taux_es"].round(1).tolist()},
            {"name": niveaux_libelles[1], "x": compare["annee"].tolist(),
             "y": compare["taux_educ"].round(1).tolist()},
            {"name": niveaux_libelles[2], "x": compare["annee"].tolist(),
             "y": compare["taux_national"].round(1).tolist()},
        ]
        # La couleur suit l'entité, jamais son rang : filtrer les niveaux ne
        # doit pas repeindre ceux qui restent.
        series = [
            dict(serie, slot=index)
            for index, serie in enumerate(toutes)
            if filters.retenu(niveaux, serie["name"])
        ]

        charts.line_series(series, unit="%", height=300, end_labels=False)

        pire_es = compare.loc[compare["taux_es"].idxmin()]
        hausse = budget.set_index("annee")["es_vote"].pct_change().get(pire_es["annee"])
        contexte_hausse = (
            tr("contexte_hausse", {"hausse": fr_number(hausse * 100, 0)})
            if hausse is not None and hausse == hausse and hausse > 0.2 else ""
        )

        note(tr("note_compare", {
            "moyenne_es": fr_number(moyenne_es, 1),
            "moyenne_nat": fr_number(moyenne_nat, 1),
            "annee": int(pire_es["annee"]),
            "taux": fr_number(pire_es["taux_es"], 1),
            "contexte": contexte_hausse,
        }))

        if niveaux and niveaux_libelles[2] not in niveaux:
            note(tr("note_national_masque"))

        charts.table_twin(
            compare.round(1).rename(columns={
                "annee": tr("colonne_annee"),
                "taux_es": tr("colonne_superieur"),
                "taux_educ": tr("colonne_education"),
                "taux_national": tr("colonne_national"),
            })
        )

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with card(tr("carte_poids_titre"), tr("carte_poids_sous_titre"),
                  "graduation-cap"):
            charts.line_series(
                [{"name": tr("legende_poids"), "x": poids["annee"].tolist(),
                  "y": poids["part_educ_national"].round(1).tolist()}],
                unit="%", height=240,
            )
            note(tr("note_poids", {
                "min": fr_number(poids["part_educ_national"].min(), 1),
                "max": fr_number(poids["part_educ_national"].max(), 1),
                "part": fr_number(poids["part_es_educ"].mean(), 0),
            }))
            charts.table_twin(
                poids.round(1).rename(columns={
                    "annee": tr("colonne_annee"),
                    "part_educ_national": tr("colonne_educ_national"),
                    "part_es_educ": tr("colonne_sup_educ"),
                    "part_es_national": tr("colonne_sup_national"),
                })
            )

    with droite:
        with card(tr("carte_subvention_titre"), tr("carte_subvention_sous_titre"),
                  "flag"):
            st.markdown(
                '<div style="display:flex;flex-direction:column;justify-content:center;'
                'align-items:center;height:240px;text-align:center;">'
                '<div style="font-size:56px;font-weight:600;line-height:1;'
                'color:var(--kg-color-text);">0</div>'
                '<div style="color:var(--kg-color-text-muted);margin-top:8px;">'
                + tr("subvention_legende", {"annees": subvention["annees"],
                                            "debut": debut, "fin": fin})
                + "</div></div>",
                unsafe_allow_html=True
            )
            note(tr("note_subvention"))
            charts.table_twin(
                subvention["serie"].rename(columns={
                    "annee": tr("colonne_annee"),
                    "subvention_prive": tr("colonne_subvention"),
                })
            )

    # ─── Ce que les taux masquent : les montants ────────────────────────────
    non_consomme = analytics.credits_non_consommes(budget)
    croissance = analytics.croissance_budgetaire(budget)
    pib = analytics.poids_dans_le_pib(budget)

    with card(tr("carte_montants_titre"), tr("carte_montants_sous_titre"),
              "wallet"):
        serie = non_consomme["serie"]
        montants = [
            {"name": niveaux_libelles[2], "x": serie["annee"].tolist(),
             "y": (serie["non_consomme_national"] / 1000).round(1).tolist()},
            {"name": niveaux_libelles[1], "x": serie["annee"].tolist(),
             "y": (serie["non_consomme_educ"] / 1000).round(1).tolist()},
            {"name": niveaux_libelles[0], "x": serie["annee"].tolist(),
             "y": (serie["non_consomme_es"] / 1000).round(1).tolist()},
        ]

        charts.line_series(
            [dict(s, slot=i) for i, s in enumerate(montants)
             if filters.retenu(niveaux, s["name"])],
            unit="Md FCFA", height=290, end_labels=False,
        )

        surexecution = non_consomme["surexecution_educ"]
        phrase = (
            tr("surexecution_educ",
               {"annees": " et ".join(str(a) for a in surexecution)})
            if surexecution else tr("surexecution_aucune")
        )

        note(tr("note_montants", {
            "debut": debut, "fin": fin,
            "national": fr_number(non_consomme["cumul_national"] / 1000, 0),
            "superieur": fr_number(non_consomme["cumul_es"] / 1000, 1),
            "part": fr_number(
                non_consomme["cumul_es"] / non_consomme["cumul_national"] * 100, 0),
            "surexecution": phrase,
        }))
        charts.table_twin(
            serie.round(0).rename(columns={
                "annee": tr("colonne_annee"),
                "non_consomme_es": tr("colonne_non_consomme_sup"),
                "non_consomme_educ": tr("colonne_non_consomme_educ"),
                "non_consomme_national": tr("colonne_non_consomme_nat"),
            })
        )

    bas_gauche, bas_droite = st.columns(2, gap="small")

    with bas_gauche:
        with card(tr("carte_priorise_titre"),
                  tr("carte_priorise_sous_titre",
                     {"debut": croissance["periode"][0],
                      "fin": croissance["periode"][1]}),
                  "trending-up"):
            charts.column_series(
                [tr("colonne_graphe_superieur"), tr("colonne_graphe_education"),
                 tr("colonne_graphe_national")],
                [round(croissance["es"], 1), round(croissance["educ"], 1),
                 round(croissance["national"], 1)],
                unit="%", height=250,
                highlight=tr("colonne_graphe_superieur"),
            )
            note(tr("note_priorise", {
                "es": fr_number(croissance["es"], 0),
                "educ": fr_number(croissance["educ"], 0),
                "national": fr_number(croissance["national"], 0),
            }))

    with bas_droite:
        with card(tr("carte_pib_titre"), tr("carte_pib_sous_titre"), "flag"):
            if pib is None or pib.empty:
                st.info(tr("info_pib_absent"))
            else:
                # Deux points de mesure seulement : une courbe suggérerait une
                # tendance qui n'est pas établie, et les trois niveaux ont des
                # ordres de grandeur trop éloignés (34 % contre 1 %) pour tenir
                # sur un même axe. Le contrat « stat tile » est la forme juste
                # pour une poignée de chiffres avec une variation.
                pib_debut, pib_fin = pib.iloc[0], pib.iloc[-1]

                def ecart_pib(colonne, decimales):
                    # Un seul exercice renseigné : il n'y a pas d'écart à
                    # afficher, seulement un point de mesure isolé.
                    if len(pib) < 2:
                        return tr("pib_seul_exercice")

                    return tr("pib_ecart", {
                        "ecart": fr_number(pib_fin[colonne] - pib_debut[colonne],
                                           decimales),
                        "annee": int(pib_debut["annee"]),
                    })

                stat_tiles([
                    {"label": tr("tuile_pib_national",
                                 {"annee": int(pib_fin["annee"])}),
                     "value": fr_number(pib_fin["part_national"], 1),
                     "unit": tr("unite_pib"), "icon": "wallet",
                     "delta": ecart_pib("part_national", 1), "good": False},
                    {"label": tr("tuile_pib_educ",
                                 {"annee": int(pib_fin["annee"])}),
                     "value": fr_number(pib_fin["part_educ"], 1),
                     "unit": tr("unite_pib"), "icon": "graduation-cap",
                     "delta": ecart_pib("part_educ", 1), "good": False},
                    {"label": tr("tuile_pib_sup",
                                 {"annee": int(pib_fin["annee"])}),
                     "value": fr_number(pib_fin["part_es"], 2),
                     "unit": tr("unite_pib"), "icon": "trending-up",
                     "delta": ecart_pib("part_es", 2), "good": False},
                ])

                charts.table_twin(
                    pib.round(2).rename(columns={
                        "annee": tr("colonne_annee"),
                        "part_national": tr("colonne_pib_national"),
                        "part_educ": tr("colonne_pib_educ"),
                        "part_es": tr("colonne_pib_sup"),
                    })
                )
                note(tr("note_pib", {
                    "pib": len(pib), "total": len(budget),
                    "moyenne": fr_number(pib["part_educ"].mean(), 1),
                }))


def render_depense():
    tr = t("financement")
    data = datasets()

    debut, fin = barres.periode(
        {tr("serie_depense"): data["depenses"],
         tr("serie_acces"): data["inscriptions"],
         tr("serie_budget"): data["budget"]},
        cle="filtre_periode_depense",
    )

    depenses = filters.entre(data["depenses"], debut, fin)
    inscriptions = filters.entre(data["inscriptions"], debut, fin)
    budget = filters.entre(data["budget"], debut, fin)

    if len(depenses) < 2:
        st.info(tr("info_depense_insuffisante"))
        return

    premiere, derniere = depenses.iloc[0], depenses.iloc[-1]

    with card(tr("carte_depense_titre"), tr("carte_depense_sous_titre"),
              "wallet"):
        charts.line_series(
            [{"name": tr("legende_depense"), "x": depenses["annee"].tolist(),
              "y": depenses["valeur"].tolist()}],
            unit="%", height=300,
        )
        note(tr("note_depense", {
            "variation": fr_number((derniere["valeur"] / premiere["valeur"] - 1) * 100, 0),
            "debut": int(premiere["annee"]), "fin": int(derniere["annee"]),
            "mesures": len(depenses),
            "etendue": int(derniere["annee"] - premiere["annee"]) + 1,
        }))

        # La comparaison en francs n'est possible que si le budget et l'accès
        # ont eux aussi des points dans l'intervalle : sans cela, la précision
        # de lecture ne peut pas être chiffrée, seulement énoncée.
        chiffrage = ""

        if len(budget) >= 2 and len(inscriptions) >= 2:
            budget_valide = budget.dropna(subset=["es_vote"])

            if len(budget_valide) >= 2:
                chiffrage = tr("chiffrage_budget", {
                    "debut": int(budget_valide.iloc[0]["annee"]),
                    "fin": int(budget_valide.iloc[-1]["annee"]),
                    "budget": fr_number(
                        (budget_valide.iloc[-1]["es_vote"]
                         / budget_valide.iloc[0]["es_vote"] - 1) * 100, 1),
                    "acces": fr_number(
                        (inscriptions.iloc[-1]["valeur"]
                         / inscriptions.iloc[0]["valeur"] - 1) * 100, 1),
                })

        note(tr("note_precision_lecture", {"chiffrage": chiffrage}))
        note(tr("note_francs_disponibles"))
        charts.table_twin(
            depenses.rename(columns={
                "annee": tr("colonne_annee"),
                "valeur": tr("colonne_depense_pib"),
            })
        )

    base = analytics.annee_de_base(inscriptions, depenses, base=debut)

    with card(tr("carte_effort_titre"),
              tr("carte_effort_sous_titre", {"base": base}) if base
              else tr("carte_effort_sous_titre_sans_base"),
              "trending-up"):
        series = analytics.ciseaux(inscriptions, depenses, base=debut)

        if len(series) < 2 or len(series[0]["x"]) < 2:
            st.info(tr("info_pas_assez_annees_communes"))
        else:
            charts.line_indexed(series, base_year=base)
            note(tr("note_effort"))


def render_chomage():
    tr = t("financement")
    data = datasets()

    debut, fin = barres.periode(
        {tr("serie_chomage"): data["chomage"]},
        cle="filtre_periode_chomage",
        aide=tr("aide_periode_chomage"),
    )

    chomage = filters.entre(data["chomage"], debut, fin)

    if len(chomage) < 2:
        st.info(tr("info_chomage_insuffisant"))
        return

    pic = chomage.loc[chomage["valeur"].idxmax()]
    dernier = chomage.iloc[-1]
    premier = chomage.iloc[0]

    stat_tiles([
        {"label": tr("tuile_chomage", {"annee": int(dernier["annee"])}),
         "value": fr_number(dernier["valeur"], 1), "unit": "%", "icon": "flag",
         "delta": tr("tuile_chomage_detail", {
             "pic": fr_number(pic["valeur"], 1), "annee": int(pic["annee"])}),
         "good": True},
        {"label": tr("tuile_amplitude"),
         "value": fr_number(pic["valeur"] - chomage["valeur"].min(), 1),
         "unit": tr("unite_pts"), "icon": "trending-up",
         "delta": tr("tuile_amplitude_detail")},
        {"label": tr("tuile_mesures"), "value": fr_number(len(chomage)),
         "icon": "table-2",
         "delta": f'{int(chomage["annee"].min())} → {int(chomage["annee"].max())}'},
    ])

    with card(tr("carte_chomage_titre"), tr("carte_chomage_sous_titre"), "flag"):
        charts.line_series(
            [{"name": tr("serie_chomage"), "x": chomage["annee"].tolist(),
              "y": chomage["valeur"].tolist()}],
            unit="%", height=300,
        )
        note(tr("note_chomage", {
            "mesures": len(chomage),
            "etendue": int(dernier["annee"] - premier["annee"]) + 1,
            "annee_pic": int(pic["annee"]),
            "annee_fin": int(dernier["annee"]),
            "annee_debut": int(premier["annee"]),
            "sens": tr("sens_superieur" if dernier["valeur"] > premier["valeur"]
                       else "sens_inferieur"),
        }))
        charts.table_twin(
            chomage.rename(columns={
                "annee": tr("colonne_annee"),
                "valeur": tr("colonne_chomage"),
            })
        )

    with card(tr("carte_trompeur_titre"),
              tr("carte_trompeur_sous_titre",
                 {"taux": fr_number(dernier["valeur"], 1)}),
              "search"):
        note(tr("note_trompeur"))

        for cle in ("jeunes_sans_emploi", "sous_emploi", "informel", "jeunesse"):
            repere_externe(contexte.repere(cle))

    with card(tr("carte_limite_titre"), tr("carte_limite_sous_titre"), "flag"):
        st.markdown(tr("limite_corps"))
