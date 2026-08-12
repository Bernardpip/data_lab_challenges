"""Croisements — ce que la jointure au canton autorise, et rien de plus.

Aucun texte visible ici : tout vient de `i18n/locales/croisements.json`.

Chaque carte affiche le nombre d'observations de sa recette et son seuil de
solidité. Une recette sous le seuil n'est pas tracée : on dit qu'elle l'est,
plutôt que de dessiner une tendance sur trop peu de points.
"""

# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui, charts
from socle.design.tokens import STATUS, INK
from socle.i18n.traduction import t

from utils import econometrie
from utils.data import datasets, apply_filters
from utils import barres, recettes


def _cadres():
    data = datasets()
    cantons = data["cantons"]
    selection = barres.territoriale(cantons)

    return data, apply_filters(cantons, selection)


def render_ouvrages_risque():
    tr, tc = t("croisements"), t("commun")
    data, cantons = _cadres()

    if cantons.empty:
        st.info(tc("aucun_resultat"))
        return

    recette = recettes.croisement_ouvrages_risque(cantons, data["tde"], data["coso"])

    if recette is None:
        ui.note(tr("note_sous_seuil", {"seuil": recettes.SEUIL_CANTONS}))
        return

    table = recette["table"]

    ui.stat_tiles([
        {"value": ui.fr_number(recette["observations"]),
         "label": tr("tuile_cantons"),
         "delta": tr("tuile_cantons_detail", {"seuil": recette["seuil"]}),
         "good": None, "icon": "search"},
        {"value": ui.fr_number(recette["ouvrages"]), "label": tr("tuile_ouvrages"),
         "delta": tr("tuile_ouvrages_detail"), "good": None, "icon": "building-2"},
        {"value": ui.fr_number(int(len(cantons) - recette["observations"])),
         "label": tr("tuile_sans"),
         "delta": tr("tuile_sans_detail", {
             "part": ui.fr_number(
                 100 * (len(cantons) - recette["observations"]) / len(cantons), 0)}),
         "good": False, "icon": "flag"},
    ])

    with ui.card(tr("carte_recette_titre"), tr("carte_recette_sous_titre"), "search"):
        ui.note(tr("note_ingredients", {
            "ingredients": " · ".join(recette["ingredients"]),
            "cle": recette["cle"],
            "observations": ui.fr_number(recette["observations"]),
            "seuil": recette["seuil"],
        }))

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with ui.card(tr("carte_nuage_titre"), tr("carte_nuage_sous_titre"), "search"):
            if len(table) < 3:
                ui.note(tc("pas_assez_de_points"))
            else:
                charts.scatter_fit(
                    table["risque_pts"], table["ouvrages"], labels=table["canton"],
                    x_titre=tr("axe_risque"), y_titre=tr("axe_ouvrages"),
                )
                ui.note(tr("note_nuage", {"n": ui.fr_number(len(table))}))

    with droite:
        with ui.card(tr("carte_top_titre"), tr("carte_top_sous_titre"), "flag"):
            top = table.head(15)
            charts.sucette_h(top, "canton", "risque_pts", unit=" pts", decimals=1)
            ui.note(tr("note_top", {
                "canton": str(top.iloc[0]["canton"]),
                "risque": ui.fr_number(top.iloc[0]["risque_pts"], 1),
                "ouvrages": ui.fr_number(int(top.iloc[0]["ouvrages"])),
            }))

    charts.table_twin(table.rename(columns={
        "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
        "region": tr("col_region"), "risque_pts": tr("col_risque"),
        "population": tr("col_population"), "ouvrages": tr("col_ouvrages"),
        "parcs": tr("col_parcs")}))


def render_maintenance():
    tr, tc = t("croisements"), t("commun")
    data, cantons = _cadres()

    if cantons.empty:
        st.info(tc("aucun_resultat"))
        return

    coso = data["coso"]

    from utils import analytics

    plans = analytics.maintenance(coso)
    sans = int((~coso["plan_maintenance"]).sum())

    ui.stat_tiles([
        {"value": ui.fr_number(sans), "label": tr("tuile_sans_plan"),
         "delta": tr("tuile_sans_plan_detail",
                     {"part": ui.fr_number(100 * sans / len(coso), 0)}),
         "good": False, "icon": "settings"},
        {"value": ui.fr_number(int(coso["plan_maintenance"].sum())),
         "label": tr("tuile_avec_plan"), "delta": tr("tuile_avec_plan_detail"),
         "good": True, "icon": "flag"},
        {"value": ui.fr_number(int(coso["fonds_entretien"].notna().sum())),
         "label": tr("tuile_fonds"),
         "delta": tr("tuile_fonds_detail",
                     {"total": ui.fr_number(len(coso))}),
         "good": None, "icon": "table-2"},
    ])

    gauche, droite = st.columns(2, gap="small")

    with gauche:
        with ui.card(tr("carte_plan_titre"), tr("carte_plan_sous_titre"),
                     "settings"):
            lisible = plans.assign(plan=plans["plan"].map(
                lambda p: tr(f"plan_{p}")))

            # Demi-anneau plutôt que deux barres : la question posée ici est
            # une PART D'UN TOUT — quelle fraction du parc est sans plan —, et
            # deux barres obligent à faire la somme de tête pour y répondre.
            # Le demi-cercle laisse en outre son centre au chiffre qui compte.
            ordre = [tr("plan_sans"), tr("plan_avec")]
            valeurs = [int(lisible.loc[lisible["plan"] == nom, "ouvrages"].sum())
                       for nom in ordre]

            # « Sans plan » est un CONSTAT défavorable : il porte la teinte
            # d'alerte de la charte, l'autre part restant en gris de retrait.
            # La couleur devient ainsi un verdict, pas un code d'identité que
            # la légende suffirait à donner.
            charts.demi_anneau(
                ordre, valeurs,
                couleurs=[STATUS["critical"], INK["deemphasis"]],
                centre=f'{ui.fr_number(100 * sans / len(coso), 0)} %',
                sous_centre=tr("plan_sans"),
            )
            ui.note(tr("note_plan", {
                "sans": ui.fr_number(sans),
                "total": ui.fr_number(len(coso)),
                "part": ui.fr_number(100 * sans / len(coso), 0),
            }))
            charts.table_twin(lisible.rename(columns={
                "plan": tr("col_plan"), "ouvrages": tr("col_ouvrages")}))

    with droite:
        with ui.card(tr("carte_fonds_titre"), tr("carte_fonds_sous_titre"),
                     "search"):
            nuage = coso[["localite", "cout_estime", "fonds_entretien"]].dropna()

            if len(nuage) < 3:
                ui.note(tc("pas_assez_de_points"))
            else:
                charts.scatter_fit(
                    nuage["cout_estime"], nuage["fonds_entretien"],
                    labels=nuage["localite"],
                    x_titre=tr("axe_cout"), y_titre=tr("axe_fonds"),
                )
                ui.note(tr("note_fonds", {
                    "n": ui.fr_number(len(nuage)),
                    "part": ui.fr_number(100 * len(nuage) / len(coso), 0),
                }))
                charts.table_twin(nuage.rename(columns={
                    "localite": tr("col_localite"), "cout_estime": tr("col_cout"),
                    "fonds_entretien": tr("col_fonds")}))

    recette = recettes.croisement_maintenance_risque(cantons, coso)

    with ui.card(tr("carte_risque_titre"), tr("carte_risque_sous_titre"), "flag"):
        if recette is None:
            ui.note(tr("note_sous_seuil", {"seuil": recettes.SEUIL_CANTONS}))
            return

        table = recette["table"].head(15)
        charts.sucette_h(table, "canton", "sans_plan", unit=tr("unite_ouvrages"))
        ui.note(tr("note_risque", {
            "observations": ui.fr_number(recette["observations"]),
            "seuil": recette["seuil"],
            "ouvrages": ui.fr_number(recette["ouvrages"]),
            "canton": str(table.iloc[0]["canton"]),
            "risque": ui.fr_number(table.iloc[0]["risque_pts"], 1),
        }))
        charts.table_twin(recette["table"].rename(columns={
            "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
            "region": tr("col_region"), "risque_pts": tr("col_risque"),
            "population": tr("col_population"), "sans_plan": tr("col_sans_plan")}))


def render_allocation():
    """Ce que les corrélations autorisent à dire de la répartition.

    Le reste du tableau de bord décrit ; cet onglet estime. Il ne demande pas
    combien d'ouvrages existent, mais ce qui explique qu'un canton en reçoive
    un — et il répond par des coefficients, des erreurs-types et des effectifs.
    """

    tr, tc = t("croisements"), t("commun")
    data = datasets()
    cantons, tde, coso = data["cantons"], data["tde"], data["coso"]

    cout = econometrie.fonction_de_cout(coso)
    elast = econometrie.elasticite_investissement(cantons, coso)
    equipe = econometrie.qui_est_equipe(cantons, tde, coso)
    couverture = econometrie.couverture_par_region(cantons, tde, coso)

    pente_pop = elast["simple"]["termes"].iloc[1]
    pente_cout = cout["estimation"]["termes"].iloc[1]
    plateaux = couverture["regions"].iloc[-1]

    ui.stat_tiles([
        {"value": ui.fr_number(pente_pop["coefficient"], 2),
         "label": tr("alloc_tuile_elasticite"),
         "delta": tr("alloc_tuile_elasticite_detail",
                     {"n": elast["cantons"]}), "good": False, "icon": "trending-up"},
        {"value": ui.fr_number(cout["estimation"]["r2"], 3),
         "label": tr("alloc_tuile_cout"),
         "delta": tr("alloc_tuile_cout_detail",
                     {"cout": ui.compact(cout["cout_median"])}),
         "good": None, "icon": "table-2"},
        {"value": ui.compact(float(plateaux["habitants_par_ouvrage"])),
         "label": tr("alloc_tuile_plateaux"),
         "delta": tr("alloc_tuile_plateaux_detail"), "good": False,
         "icon": "map-pin"},
    ])

    # ── 1. Le résultat qui commande les autres ──────────────────────────────
    with ui.card(tr("alloc_cout_titre"), tr("alloc_cout_sous_titre"), "table-2"):
        profil = cout["profil"].assign(
            quintile=cout["profil"]["quintile"].map(
                lambda q: tr(f"quintile_{q}")))

        charts.bar_h(profil, "quintile", "cout_par_beneficiaire",
                     unit=tr("unite_fcfa"), trier=False)
        ui.note(tr("alloc_cout_note", {
            "coef": ui.fr_number(pente_cout["coefficient"], 3),
            "t": ui.fr_number(pente_cout["t"], 2),
            "cout": ui.compact(cout["cout_median"]),
            "rapport": ui.fr_number(
                profil["cout_par_beneficiaire"].iloc[0]
                / profil["cout_par_beneficiaire"].iloc[-1], 0),
        }))
        charts.table_twin(profil[["quintile", "ouvrages",
                                  "beneficiaires_median", "cout_median",
                                  "cout_par_beneficiaire"]].rename(columns={
            "quintile": tr("col_quintile"), "ouvrages": tr("col_ouvrages"),
            "beneficiaires_median": tr("col_beneficiaires"),
            "cout_median": tr("col_cout"),
            "cout_par_beneficiaire": tr("col_cout_par_benef")}))

    # ── 2. La règle de répartition ──────────────────────────────────────────
    with ui.card(tr("alloc_elasticite_titre"), tr("alloc_elasticite_sous_titre"),
                 "trending-up"):
        contre = econometrie.contrefactuel_demographique(cantons, coso)

        charts.sucette_h(
            contre["cadre"].head(8).assign(
                deficit=-contre["cadre"].head(8)["ecart"] / 1e6),
            "canton", "deficit", unit=tr("unite_millions"))
        ui.note(tr("alloc_elasticite_note", {
            "coef": ui.fr_number(pente_pop["coefficient"], 2),
            "gain": ui.fr_number(
                100 * (2 ** pente_pop["coefficient"] - 1), 0),
            "gini": ui.fr_number(contre["gini"], 2),
            "interdecile": ui.fr_number(contre["rapport_interdecile"], 1),
        }))
        charts.table_twin(contre["cadre"].rename(columns={
            "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
            "population": tr("col_population"), "investi": tr("col_investi"),
            "equitable": tr("col_equitable"), "ecart": tr("col_ecart"),
            "par_habitant": tr("col_par_habitant")}))

    # ── 3. Le besoin explique-t-il la dotation ? ────────────────────────────
    with ui.card(tr("alloc_modele_titre"), tr("alloc_modele_sous_titre"),
                 "search"):
        comparaison = pd.DataFrame([
            {"modele": tr("modele_sans_region"),
             "variance": 100 * equipe["sans_region"]["r2"]},
            {"modele": tr("modele_avec_region"),
             "variance": 100 * equipe["avec_region"]["r2"]},
        ])

        charts.bar_h(comparaison, "modele", "variance", unit="%", trier=False)

        risque = equipe["avec_region"]["termes"]
        ligne = risque[risque["terme"] == "risque"].iloc[0]
        ui.note(tr("alloc_modele_note", {
            "sans": ui.fr_number(100 * equipe["sans_region"]["r2"], 0),
            "avec": ui.fr_number(100 * equipe["avec_region"]["r2"], 0),
            "t": ui.fr_number(abs(ligne["t"]), 2),
        }))
        charts.table_twin(equipe["avec_region"]["termes"].round(4).rename(
            columns={"terme": tr("col_terme"),
                     "coefficient": tr("col_coefficient"),
                     "erreur_type": tr("col_erreur_type")}))

    # ── 4. Ce que l'indice classe réellement ────────────────────────────────
    with ui.card(tr("alloc_fri_titre"), tr("alloc_fri_sous_titre"), "flag"):
        ordre = econometrie.ce_que_le_fri_ordonne(cantons)
        lisible = ordre["correlations"].assign(
            dimension=ordre["correlations"]["dimension"].map(
                lambda d: tr(f"dimension_{d}")),
            correlation=ordre["correlations"]["rho"].abs())

        charts.bar_h(lisible, "dimension", "correlation", unit="ρ")
        ui.note(tr("alloc_fri_note", {
            "exposition": ui.fr_number(
                float(ordre["correlations"].loc[
                    ordre["correlations"]["dimension"] == "exposition",
                    "rho"].iloc[0]), 2),
            "alea": ui.fr_number(
                float(ordre["correlations"].loc[
                    ordre["correlations"]["dimension"] == "alea",
                    "rho"].iloc[0]), 2),
        }))
        charts.table_twin(ordre["sommet"].rename(columns={
            "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
            "risque_pts": tr("col_risque"),
            "susceptibilite": tr("col_alea"),
            "population": tr("col_population"),
            "rang_alea": tr("col_rang_alea")}))
