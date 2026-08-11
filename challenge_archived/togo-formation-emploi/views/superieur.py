"""Enseignement supérieur — dynamique d'accès, indicateurs clés et réseau.

Aucun texte visible n'est écrit ici : tout vient de
`i18n/locales/superieur.json` via `t("superieur")`.
"""

# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import streamlit as st

from socle import charts
from socle.ui import filters
from utils import barres
from socle.charts import maps
from socle.ui import card, stat_tiles, note, fr_number
from utils.data import datasets
from utils import analytics, recettes
from socle.i18n.traduction import t


def render_indicateurs():
    tr = t("superieur")
    data = datasets()

    # Deux séries lacunaires et d'amplitudes différentes (1971-2020 contre
    # 1998-2017) : le curseur porte sur leur union, le décompte à droite dit
    # ce qui reste réellement de chacune.
    debut, fin = barres.periode(
        {tr("serie_acces"): data["inscriptions"],
         tr("serie_depense"): data["depenses"]},
        cle="filtre_periode_superieur",
    )

    inscriptions = filters.entre(data["inscriptions"], debut, fin)
    depenses = filters.entre(data["depenses"], debut, fin)

    if inscriptions.empty or depenses.empty:
        st.info(tr("info_deux_series_vides"))
        return

    premiere, derniere = inscriptions.iloc[0], inscriptions.iloc[-1]
    dep_premiere, dep_derniere = depenses.iloc[0], depenses.iloc[-1]

    stat_tiles([
        {"label": tr("tuile_taux", {"annee": int(derniere["annee"])}),
         "value": fr_number(derniere["valeur"], 1), "unit": "%",
         "icon": "graduation-cap",
         "delta": tr("tuile_taux_detail", {
             "valeur": fr_number(premiere["valeur"], 1),
             "annee": int(premiere["annee"])}),
         "good": True},
        {"label": tr("tuile_progression"),
         "value": f'×{fr_number(derniere["valeur"] / premiere["valeur"], 0)}',
         "icon": "trending-up",
         "delta": f'{int(premiere["annee"])} → {int(derniere["annee"])}',
         "good": True},
        {"label": tr("tuile_depense", {"annee": int(dep_derniere["annee"])}),
         "value": fr_number(dep_derniere["valeur"], 0),
         "unit": tr("unite_pib_hab"), "icon": "wallet",
         "delta": tr("tuile_depense_detail", {
             "part": fr_number((1 - dep_derniere["valeur"] / dep_premiere["valeur"]) * 100, 0),
             "annee": int(dep_premiere["annee"])}),
         "good": False},
        {"label": tr("tuile_annees_documentees"),
         "value": fr_number(len(inscriptions)), "icon": "table-2",
         "delta": tr("tuile_annees_documentees_detail",
                     {"debut": debut, "fin": fin})},
    ])

    with card(tr("carte_dynamique_titre"),
              tr("carte_dynamique_sous_titre", {"debut": int(premiere["annee"]),
                                                "fin": int(derniere["annee"])}),
              "trending-up"):
        charts.line_series(
            [{"name": tr("legende_taux"),
              "x": inscriptions["annee"].tolist(),
              "y": inscriptions["valeur"].tolist()}],
            unit="%", height=300,
        )
        note(tr("note_dynamique", {
            "debut_valeur": fr_number(premiere["valeur"], 1),
            "debut_annee": int(premiere["annee"]),
            "fin_valeur": fr_number(derniere["valeur"], 1),
            "fin_annee": int(derniere["annee"]),
            "facteur": fr_number(derniere["valeur"] / premiere["valeur"], 1),
        }))
        charts.table_twin(
            inscriptions.rename(columns={
                "annee": tr("colonne_annee"),
                "valeur": tr("colonne_taux_brut"),
            })
        )

    with card(tr("carte_depense_titre"),
              tr("carte_depense_sous_titre",
                 {"debut": int(dep_premiere["annee"]),
                  "fin": int(dep_derniere["annee"])}),
              "wallet"):
        charts.line_series(
            [{"name": tr("legende_depense"),
              "x": depenses["annee"].tolist(),
              "y": depenses["valeur"].tolist()}],
            unit="%", height=260,
        )
        note(tr("note_depense", {
            "debut_valeur": fr_number(dep_premiere["valeur"], 0),
            "debut_annee": int(dep_premiere["annee"]),
            "fin_valeur": fr_number(dep_derniere["valeur"], 0),
            "fin_annee": int(dep_derniere["annee"]),
        }))
        charts.table_twin(
            depenses.rename(columns={
                "annee": tr("colonne_annee"),
                "valeur": tr("colonne_depense_pib"),
            })
        )


def render_reseau():
    tr, tf, tc = t("superieur"), t("filtres"), t("commun")

    data = datasets()
    complet = data["superieur"]

    # Le fichier n'a que trois dimensions — ville, type, statut : la barre les
    # reprend toutes les trois. Une sélection vide vaut « tout ».
    selection = filters.choix([
        {"libelle": tf("ville"), "cle": "filtre_sup_ville",
         "placeholder": tc("toutes"),
         "options": sorted(complet["ville"].unique().tolist())},
        {"libelle": tf("type"), "cle": "filtre_sup_type",
         "placeholder": tc("tous"),
         "options": sorted(complet["type"].unique().tolist())},
        {"libelle": tf("statut"), "cle": "filtre_sup_statut",
         "placeholder": tc("tous"),
         "options": sorted(complet["statut"].unique().tolist())},
    ])

    superieur = complet
    for colonne, cle in (("ville", "filtre_sup_ville"),
                         ("type", "filtre_sup_type"),
                         ("statut", "filtre_sup_statut")):
        if selection[cle]:
            superieur = superieur[superieur[colonne].isin(selection[cle])]

    synthese = analytics.superieur_synthese(superieur)
    villes = analytics.superieur_par_ville(superieur)

    if synthese["total"] == 0:
        st.info(tc("aucun_etablissement"))
        return

    # 2/3 indicateurs + graphes · 1/3 carte — même partage que la cartographie
    # des formations techniques. La colonne étroite convient au Togo, pays très
    # étiré nord-sud : en pleine largeur, la carte devrait dézoomer pour caser
    # l'extension nord-sud et révélerait toute l'Afrique de l'Ouest.
    gauche, droite = st.columns([2, 1], gap="small")

    with droite:
        with card(tr("carte_implantation_titre"),
                  tr("carte_implantation_sous_titre"), "map-pin"):
            situees, sans_position = recettes.villes_situees(
                superieur, data["formations"])
            # Même hauteur que la carte des formations techniques : les deux
            # cartes montrent le même pays, elles doivent se lire à la même
            # échelle d'une page à l'autre.
            #
            # L'aire du disque porte le nombre d'établissements — le socle en
            # tire le rayon par racine carrée. « établissement », « public » et
            # « privé » étaient écrits en dur dans l'ancien composant : ils
            # restaient français dans la version anglaise.
            def _infobulle_ville(row):
                total = int(row["total"])
                cle = ("carte_infobulle_un" if total == 1
                       else "carte_infobulle_plusieurs")

                return (
                    f'<b>{row["ville"]}</b> · {row["region"]}<br>'
                    f'{tr(cle, {"total": total})}<br>'
                    '<span style="color:#475569;">'
                    + tr("carte_infobulle_statuts", {
                        "publics": int(row["Public"]),
                        "prives": int(row["Privé"]),
                    })
                    + "</span>"
                )

            maps.disques(
                situees, valeur="total", cle="carte_superieur",
                etiquette="ville", infobulle=_infobulle_ville, height=980,
                message_vide=tc("aucune_ville_avec_etablissement"),
            )

            note(tr("note_carte_derivee"))

            if sans_position:
                note(tr("note_villes_sans_position",
                        {"villes": ", ".join(sans_position)}))

    with gauche:
        complet_total = analytics.superieur_synthese(complet)["total"]

        stat_tiles([
            {"label": tr("tuile_etablissements", {"annee": synthese["annee"]}),
             "value": fr_number(synthese["total"]), "icon": "building-2",
             "delta": tr("tuile_etablissements_detail",
                         {"villes": synthese["villes"]})},
            {"label": tr("tuile_prive"),
             "value": fr_number(synthese["part_prive"], 0), "unit": "%",
             "icon": "flag",
             "delta": tr("tuile_prive_detail",
                         {"publics": int(villes["Public"].sum())}),
             "good": False},
            {"label": tr("tuile_lome"),
             "value": fr_number(synthese["part_lome"], 0), "unit": "%",
             "icon": "map-pin",
             "delta": tr("tuile_lome_detail" if synthese["total"] == complet_total
                         else "tuile_lome_detail_filtre"),
             "good": False},
        ])

        with card(tr("carte_reseau_titre"), tr("carte_reseau_sous_titre"),
                  "building-2"):
            charts.bar_stacked_h(villes, "ville", ["Public", "Privé"])

            hors_lome = villes[villes["ville"].str.lower() != "lomé"]
            autres = len(hors_lome)
            suite = tr("reseau_une_autre_ville" if autres == 1
                       else "reseau_autres_villes", {
                "autres": autres,
                "reste": int(hors_lome["total"].sum()),
                "publics": int(hors_lome["Public"].sum()),
            })

            # Le constat « privé » n'a de sens que si le filtre laisse les deux
            # statuts en présence : filtré sur le public, « privé (0 %) » serait
            # un artefact du filtre, pas un fait sur le réseau.
            note(tr("note_reseau_filtre" if selection["filtre_sup_statut"]
                    else "note_reseau", {
                "prive": fr_number(synthese["part_prive"], 0),
                "lome": fr_number(synthese["part_lome"], 0),
                "suite": suite,
            }))
            charts.table_twin(
                villes.rename(columns={
                    "ville": tr("colonne_ville"),
                    "Public": tr("statut_public"),
                    "Privé": tr("statut_prive"),
                    "total": tr("colonne_total"),
                })
            )

        with card(tr("carte_types_titre"), tr("carte_types_sous_titre"),
                  "graduation-cap"):
            par_type = (
                superieur.pivot_table(
                    index="type", columns="statut", values="valeur", aggfunc="sum"
                )
                .fillna(0)
                .reset_index()
            )

            # Un filtre sur le statut fait disparaître une colonne du pivot : la
            # série empilée la réclame quand même, à zéro.
            for colonne in ("Public", "Privé"):
                if colonne not in par_type.columns:
                    par_type[colonne] = 0

            charts.bar_stacked_h(par_type, "type", ["Public", "Privé"])

            note(tr("note_types", {
                "universites": int(
                    superieur[superieur["type"] == "Université"]["valeur"].sum()),
                "total": synthese["total"],
            }))
            charts.table_twin(par_type)


# ─── Indicateurs clés (DICES-TG) ─────────────────────────────────────────────

def render_cles():
    """Objectif n°2 du cahier des charges : effectifs, féminisation, filières
    scientifiques et ratio étudiant/enseignant.

    Ces quatre indicateurs n'existaient dans aucune des huit premières
    ressources. Ils viennent d'un neuvième jeu (DICES-TG), qui porte en outre
    la dépense par étudiant en FRANCS — de quoi trancher enfin une ambiguïté
    que le reste du tableau de bord ne pouvait que signaler.
    """

    tr = t("superieur")

    data = datasets()
    indicateurs = data["indicateurs_sup"]

    debut, fin = barres.periode(
        {tr("serie_dices"): indicateurs},
        cle="filtre_periode_cles",
        aide=tr("aide_periode_cles"),
    )

    cadre = filters.entre(indicateurs, debut, fin)

    effectifs = analytics.evolution_sup(cadre, "effectifs")
    feminite = analytics.evolution_sup(cadre, "feminite")
    scientifiques = analytics.evolution_sup(cadre, "scientifiques")
    ratio = analytics.evolution_sup(cadre, "ratio_encadrement")

    if not effectifs:
        st.info(tr("info_effectifs_insuffisants"))
        return

    def tuile(evolution, cle_label, icone, decimales=0, bon=True):
        """Tuile d'un indicateur, ou tuile « indisponible » si la série manque."""

        if not evolution:
            return {"label": tr(cle_label), "value": "—", "icon": icone,
                    "delta": tr("tuile_indisponible")}

        unite = tr(evolution["unite_cle"]) if evolution["unite_cle"] else ""

        return {
            "label": f'{tr(cle_label)} ({evolution["annee_fin"]})',
            "value": fr_number(evolution["valeur_fin"], decimales),
            # L'unité « étudiants » ferait doublon avec le libellé de la tuile.
            "unit": "" if unite == tr("unite_etudiants") else unite,
            "icon": icone,
            "delta": tr("tuile_variation", {
                "variation": fr_number(evolution["variation_pct"], 1),
                "annee": evolution["annee_debut"]}),
            "good": bon,
        }

    stat_tiles([
        tuile(effectifs, "tuile_effectifs", "graduation-cap"),
        tuile(feminite, "tuile_feminite", "flag", 1),
        tuile(scientifiques, "tuile_scientifiques", "bar-chart-3", 1),
        # Un ratio d'encadrement qui BAISSE est une amélioration : moins
        # d'étudiants par enseignant. Le sens de la couleur est donc inversé.
        tuile(ratio, "tuile_ratio", "trending-up", 0, bon=True),
    ])

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with card(tr("carte_effectifs_titre"), tr("carte_effectifs_sous_titre"),
                  "graduation-cap"):
            serie = effectifs["serie"]
            charts.column_series(
                [str(int(a)) for a in serie["annee"]],
                serie["valeur"].round(0).tolist(),
                unit=tr("unite_etudiants"), height=260,
            )
            note(tr("note_effectifs", {
                "debut_valeur": fr_number(effectifs["valeur_debut"]),
                "debut_annee": effectifs["annee_debut"],
                "fin_valeur": fr_number(effectifs["valeur_fin"]),
                "fin_annee": effectifs["annee_fin"],
                "variation": fr_number(effectifs["variation_pct"], 1),
                "manquante": effectifs["annee_fin"] - 1,
            }))
            charts.table_twin(
                serie[["annee", "valeur"]].rename(columns={
                    "annee": tr("colonne_annee"),
                    "valeur": tr("colonne_etudiants_inscrits"),
                })
            )

    with droite:
        with card(tr("carte_ratio_titre"), tr("carte_ratio_sous_titre"),
                  "trending-up"):
            if not ratio:
                st.info(tr("info_ratio_insuffisant"))
            else:
                serie = ratio["serie"]
                charts.line_series(
                    [{"name": tr("legende_ratio"),
                      "x": serie["annee"].astype(int).tolist(),
                      "y": serie["valeur"].tolist()}],
                    unit="", height=260,
                )
                note(tr("note_ratio", {
                    "debut_valeur": fr_number(ratio["valeur_debut"], 0),
                    "debut_annee": ratio["annee_debut"],
                    "fin_valeur": fr_number(ratio["valeur_fin"], 0),
                    "fin_annee": ratio["annee_fin"],
                    "variation": fr_number(abs(ratio["variation_pct"]), 0),
                    "n": ratio["n"],
                }))
                charts.table_twin(
                    serie[["annee", "valeur"]].rename(columns={
                        "annee": tr("colonne_annee"),
                        "valeur": tr("colonne_ratio"),
                    })
                )

    # ─── Enseignants reconstitués ────────────────────────────────────────────
    enseignants = analytics.enseignants_implicites(cadre)

    if enseignants is not None and len(enseignants) >= 2:
        with card(tr("carte_enseignants_titre"),
                  tr("carte_enseignants_sous_titre"), "search"):
            charts.column_series(
                [str(a) for a in enseignants["annee"]],
                enseignants["enseignants"].round(0).tolist(),
                unit=tr("unite_enseignants"), height=250,
            )

            premier, dernier = enseignants.iloc[0], enseignants.iloc[-1]

            note(tr("note_enseignants_methode", {
                "part": fr_number(dernier["part_publique"], 1),
                "annee": int(dernier["annee"]),
            }))
            note(tr("note_enseignants_resultat", {
                "debut": fr_number(premier["enseignants"], 0),
                "annee_debut": int(premier["annee"]),
                "fin": fr_number(dernier["enseignants"], 0),
                "annee_fin": int(dernier["annee"]),
                "croissance": fr_number(
                    (dernier["enseignants"] / premier["enseignants"] - 1) * 100, 0),
                "croissance_etudiants": fr_number(
                    (dernier["effectifs_publics"] / premier["effectifs_publics"] - 1) * 100, 0),
            }))
            charts.table_twin(
                enseignants.round(1).rename(columns={
                    "annee": tr("colonne_annee"),
                    "effectifs": tr("colonne_etudiants_total"),
                    "part_publique": tr("colonne_part_publique"),
                    "effectifs_publics": tr("colonne_etudiants_publics"),
                    "ratio_encadrement": tr("colonne_ratio_court"),
                    "enseignants": tr("colonne_enseignants_calcule"),
                })
            )

    # ─── Féminisation ────────────────────────────────────────────────────────
    with card(tr("carte_feminisation_titre"),
              tr("carte_feminisation_sous_titre"), "flag"):
        if not feminite:
            st.info(tr("info_feminisation_insuffisante"))
        else:
            filles_sc = analytics.evolution_sup(cadre, "filles_scientifiques")

            series = [{
                "name": tr("legende_feminite"),
                "x": feminite["serie"]["annee"].astype(int).tolist(),
                "y": feminite["serie"]["valeur"].tolist(),
                "slot": 0,
            }]

            if filles_sc:
                series.append({
                    "name": tr("legende_filles_sciences"),
                    "x": filles_sc["serie"]["annee"].astype(int).tolist(),
                    "y": filles_sc["serie"]["valeur"].tolist(),
                    "slot": 1,
                })

            charts.line_series(series, unit="%", height=280, end_labels=False)

            franchit = feminite["serie"][feminite["serie"]["valeur"] >= 50]
            bascule = (
                tr("feminisation_bascule",
                   {"annee": int(franchit.iloc[0]["annee"])})
                if not franchit.empty else ""
            )

            note(tr("note_feminisation", {
                "debut_valeur": fr_number(feminite["valeur_debut"], 1),
                "debut_annee": feminite["annee_debut"],
                "fin_valeur": fr_number(feminite["valeur_fin"], 1),
                "fin_annee": feminite["annee_fin"],
                "bascule": bascule,
            }))

            ecart = analytics.ecart_feminisation(cadre)

            if ecart is not None and not ecart.empty:
                dernier = ecart.iloc[-1]
                note(tr("note_ecart_feminisation", {
                    "annee": int(dernier["annee"]),
                    "feminite": fr_number(dernier["feminite"], 1),
                    "scientifiques": fr_number(dernier["filles_scientifiques"], 1),
                    "ecart": fr_number(dernier["ecart_points"], 1),
                    "annees": len(ecart),
                }))

            note(tr("note_doublon_feminisation"))
            charts.table_twin(
                feminite["serie"][["annee", "valeur"]].rename(columns={
                    "annee": tr("colonne_annee"),
                    "valeur": tr("colonne_part_femmes"),
                })
            )

    # ─── Filières scientifiques ──────────────────────────────────────────────
    bas_gauche, bas_droite = st.columns(2, gap="small")

    with bas_gauche:
        with card(tr("carte_scientifiques_titre"),
                  tr("carte_scientifiques_sous_titre"), "bar-chart-3"):
            if not scientifiques:
                st.info(tr("info_scientifiques_insuffisant"))
            else:
                serie = scientifiques["serie"]
                charts.line_series(
                    [{"name": tr("legende_scientifiques"),
                      "x": serie["annee"].astype(int).tolist(),
                      "y": serie["valeur"].tolist()}],
                    unit="%", height=250,
                )
                note(tr("note_scientifiques", {
                    "debut": fr_number(scientifiques["valeur_debut"], 1),
                    "fin": fr_number(scientifiques["valeur_fin"], 1),
                    "annee_debut": scientifiques["annee_debut"],
                    "annee_fin": scientifiques["annee_fin"],
                    "points": fr_number(scientifiques["variation_points"], 1),
                }))
                charts.table_twin(
                    serie[["annee", "valeur"]].rename(columns={
                        "annee": tr("colonne_annee"),
                        "valeur": tr("colonne_part_scientifique"),
                    })
                )

    with bas_droite:
        with card(tr("carte_francs_titre"), tr("carte_francs_sous_titre"),
                  "wallet"):
            totale = analytics.depense_totale(cadre)

            if totale is None:
                st.info(tr("info_francs_insuffisant"))
            else:
                table = totale["table"]
                charts.column_series(
                    [str(a) for a in table["annee"]],
                    table["depense_fcfa"].round(0).tolist(),
                    unit=tr("unite_fcfa"), height=250,
                )
                note(tr("note_francs", {
                    "debut": fr_number(table.iloc[0]["depense_fcfa"], 0),
                    "annee_debut": int(table.iloc[0]["annee"]),
                    "fin": fr_number(table.iloc[-1]["depense_fcfa"], 0),
                    "annee_fin": int(table.iloc[-1]["annee"]),
                    "variation": fr_number(totale["var_unitaire"], 1),
                }))
                note(tr("note_francs_masse", {
                    "effectifs": fr_number(totale["var_effectifs"], 0),
                    "debut": fr_number(table.iloc[0]["total_millions"] / 1000, 1),
                    "fin": fr_number(table.iloc[-1]["total_millions"] / 1000, 1),
                    "variation": fr_number(totale["var_totale"], 0),
                }))
                charts.table_twin(
                    table.round(0).rename(columns={
                        "annee": tr("colonne_annee"),
                        "depense_fcfa": tr("colonne_depense_fcfa"),
                        "effectifs": tr("colonne_etudiants"),
                        "total_millions": tr("colonne_depense_totale"),
                    })
                )

    # ─── Les autres séries du fichier ────────────────────────────────────────
    with card(tr("carte_autres_titre"), tr("carte_autres_sous_titre"), "table-2"):
        autres = ["part_education", "part_superieur_pib", "densite_etudiants",
                  "densite_publique", "inscription_bacheliers"]
        lignes = []

        for cle in autres:
            evolution = analytics.evolution_sup(cadre, cle)

            if not evolution:
                continue

            lignes.append({
                tr("colonne_indicateur"): tr("ind_" + cle),
                tr("colonne_unite"): tr(evolution["unite_cle"]),
                tr("colonne_debut"): f'{evolution["annee_debut"]} : '
                                     f'{fr_number(evolution["valeur_debut"], 2)}',
                tr("colonne_fin"): f'{evolution["annee_fin"]} : '
                                   f'{fr_number(evolution["valeur_fin"], 2)}',
                tr("colonne_variation"): f'{fr_number(evolution["variation_pct"], 1)} %',
                tr("colonne_mesures"): evolution["n"],
            })

        if lignes:
            st.dataframe(pd.DataFrame(lignes), use_container_width=True,
                         hide_index=True)

        bacheliers = analytics.evolution_sup(cadre, "inscription_bacheliers")

        if bacheliers:
            note(tr("note_bacheliers", {
                "debut": fr_number(bacheliers["valeur_debut"], 0),
                "annee_debut": bacheliers["annee_debut"],
                "fin": fr_number(bacheliers["valeur_fin"], 1),
                "annee_fin": bacheliers["annee_fin"],
            }))
