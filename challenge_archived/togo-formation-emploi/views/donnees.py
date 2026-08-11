"""Données — lecture fichier par fichier, puis croisements entre fichiers.

Deux angles complémentaires que l'organisation thématique du tableau de bord
ne donne pas :
  · ce que vaut chaque jeu pris isolément (couverture, trous, pièges) ;
  · ce que seuls plusieurs jeux réunis permettent d'établir.

Aucun texte visible n'est écrit ici : tout vient de `i18n/locales/donnees.json`
via `t("donnees")`.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import charts
from socle.ui import filters
from utils import barres
from socle.ui import card, note, stat_tiles, fr_number
from socle.design.tokens import STATUS
from utils.data import datasets, bruts
from utils import profils, recettes
from socle.i18n.traduction import t


# ─── Analyse individuelle ───────────────────────────────────────────────────

def render_fichiers():
    tr, tf, tc = t("donnees"), t("filtres"), t("commun")

    data = datasets()
    brut = bruts()

    fiches = profils.tous_les_profils(data, brut)
    natures = sorted({f["nature"] for f in fiches})

    # Le filtre porte sur le niveau géographique et sur la présence d'un
    # relevé de complétude ; il restreint la liste déroulante qui le suit.
    # Trois contrôles, une unité de grille chacun.
    colonnes = st.columns([2, 2, 2, 6], gap="small")
    gauche, milieu, droite = colonnes[0], colonnes[1], colonnes[2]

    with gauche:
        nature_retenue = st.multiselect(
            tf("niveau"), natures, placeholder=tc("tous"),
            key="filtre_fichier_nature", help=tr("aide_niveau"),
        )

    with milieu:
        qualite = st.multiselect(
            tf("completude"),
            [tr("completude_disponible"), tr("completude_sans_objet")],
            placeholder=tc("tous"), key="filtre_fichier_qualite",
            help=tr("aide_completude"),
        )

    def passe(fiche):
        etat = (tr("completude_disponible") if fiche["completude"] is not None
                else tr("completude_sans_objet"))
        return (filters.retenu(nature_retenue, fiche["nature"])
                and filters.retenu(qualite, etat))

    retenues = [f for f in fiches if passe(f)]

    stat_tiles([
        {"label": tr("tuile_fichiers"), "value": str(len(retenues)),
         "icon": "table-2",
         "delta": tr("tuile_fichiers_detail", {"total": len(fiches)}),
         "good": True},
        {"label": tr("tuile_lignes"),
         "value": fr_number(sum(f["lignes"] for f in retenues)),
         "icon": "bar-chart-3", "delta": tr("tuile_lignes_detail")},
        {"label": tr("tuile_infranationales"),
         "value": str(sum(1 for f in retenues
                          if f["nature_cle"] == profils.NATURE_INFRANATIONALE)),
         "icon": "map-pin",
         "delta": tr("tuile_infranationales_detail"), "good": False},
        {"label": tr("tuile_annees"), "value": "1922", "unit": "→ 2025",
         "icon": "trending-up", "delta": tr("tuile_annees_detail")},
    ])

    if not retenues:
        st.info(tr("info_aucun_fichier"))
        return

    with droite:
        # La clé dépend de la liste retenue : sans cela, un index mémorisé
        # pourrait pointer hors de la liste après resserrement du filtre.
        choix = st.selectbox(
            tf("fichier"),
            options=list(range(len(retenues))),
            format_func=lambda i: f'{retenues[i]["titre"]}  ·  {retenues[i]["code"]}',
            key="profil_fichier_" + "-".join(f["code"] for f in retenues),
        )

    fiche = retenues[choix]

    with card(fiche["titre"], fiche["code"], "table-2"):
        st.markdown(
            "| | |\n|---|---|\n"
            f'| **{tr("fiche_volumetrie")}** | '
            f'{tr("fiche_volumetrie_valeur", {"lignes": fr_number(fiche["lignes"]), "colonnes": fiche["colonnes"]})} |\n'
            f'| **{tr("fiche_granularite")}** | {fiche["granularite"]} |\n'
            f'| **{tr("fiche_niveau")}** | {fiche["nature"]} |\n'
            f'| **{tr("fiche_periode")}** | {fiche["periode"]} |\n'
            f'| **{tr("fiche_cle")}** | {fiche["cle"]} |'
        )

        for titre, detail in fiche["constats"]:
            st.markdown(
                '<div style="padding:9px 0;border-bottom:1px solid '
                'var(--kg-color-border-light);">'
                f'<div style="font-weight:600;">{titre}</div>'
                '<div style="color:var(--kg-color-text-secondary);margin-top:2px;">'
                f'{detail}</div></div>',
                unsafe_allow_html=True
            )

    if fiche["completude"] is not None and not fiche["completude"].empty:
        with card(tr("carte_completude_titre"),
                  tr("carte_completude_sous_titre"), "search"):
            comp = fiche["completude"]
            charts.bar_h(
                comp.assign(taux=comp["taux"].round(1)),
                "champ", "taux", unit="%",
            )
            note(tr("note_completude", {
                "faibles": len(comp[comp["taux"] < 90]),
                "total": len(comp),
                "champ": comp.iloc[0]["champ"],
                "taux": fr_number(comp.iloc[0]["taux"], 0),
            }))
            charts.table_twin(
                comp.round(1).rename(columns={
                    "champ": tr("colonne_champ"),
                    "renseignes": tr("colonne_renseignes"),
                    "taux": tr("colonne_taux"),
                })
            )


# ─── Croisements ────────────────────────────────────────────────────────────

# Seuil de solidité, recette par recette. Il n'est pas uniforme : dix années
# communes pour une série temporelle, cinq régions pour le croisement
# géographique — un même nombre ne vaut pas la même chose selon l'unité.
_SEUILS = {
    "acces_et_moyens": 10,
    "budget_par_acces": 8,
    "coherence_financement": 8,
    "reseaux_par_region": 5,
    "acces_et_insertion": 10,
    "acces_et_effectifs": 5,
}


def _entete_recette(nom, recette):
    """Bandeau d'identité d'une recette : ingrédients, clé, solidité."""

    tr = t("donnees")

    seuil = _SEUILS[nom]
    obs = recette["observations"]
    solide = obs >= seuil

    couleur = STATUS["good"] if solide else STATUS["warning"]
    verdict = (tr("verdict_solide") if solide
               else tr("verdict_fragile", {"obs": obs}))

    ingredients = "  +  ".join(recette["ingredients"])

    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;gap:16px;align-items:center;'
        'padding:9px 12px;background:var(--kg-color-surface-secondary);'
        'border-radius:6px;font-size:var(--kg-fs-xs);margin-bottom:8px;">'
        f'<span style="display:inline-flex;align-items:center;gap:6px;font-weight:600;">'
        f'<span style="width:8px;height:8px;border-radius:9999px;'
        f'background:{couleur};"></span>{verdict}</span>'
        f'<span><b>{tr("entete_ingredients")}</b> {ingredients}</span>'
        f'<span><b>{tr("entete_cle")}</b> {recette["cle"]}</span>'
        f'<span><b>{tr("entete_observations")}</b> {obs}</span>'
        "</div>",
        unsafe_allow_html=True
    )


def render_croisements():
    tr, tc = t("donnees"), t("commun")

    data = datasets()
    inv = recettes.inventaire(data)

    r1, r2 = inv["acces_et_moyens"], inv["budget_par_acces"]
    r3, r4, r5 = (inv["coherence_financement"], inv["reseaux_par_region"],
                  inv["acces_et_insertion"])
    r6 = inv["acces_et_effectifs"]

    # Les deux filtres portent sur ce qui distingue vraiment les recettes :
    # ce qu'elles valent, et de quels fichiers elles dépendent.
    tous_ingredients = sorted({
        ingredient for recette in inv.values() if recette
        for ingredient in recette["ingredients"]
    })
    selection = filters.choix([
        {"libelle": t("filtres")("solidite"), "cle": "filtre_recette_solidite",
         "placeholder": tc("toutes"),
         "options": [tr("verdict_solide"), tr("etat_fragile")],
         "aide": tr("aide_solidite")},
        {"libelle": t("filtres")("ingredient"),
         "cle": "filtre_recette_ingredient",
         "placeholder": tc("tous"), "options": tous_ingredients},
    ])

    def visible(nom):
        recette = inv[nom]

        if not recette:
            return False

        etat = (tr("verdict_solide")
                if recette["observations"] >= _SEUILS[nom]
                else tr("etat_fragile"))

        return (
            filters.retenu(selection["filtre_recette_solidite"], etat)
            and (not selection["filtre_recette_ingredient"]
                 or any(i in selection["filtre_recette_ingredient"]
                        for i in recette["ingredients"]))
        )

    affichees = [nom for nom in inv if visible(nom)]

    stat_tiles([
        {"label": tr("tuile_croisements"), "value": str(len(affichees)),
         "icon": "search",
         "delta": tr("tuile_croisements_detail", {"total": len(inv)})},
        {"label": tr("tuile_plus_solide"), "value": f'{r1["observations"]}',
         "unit": tr("unite_annees"), "icon": "trending-up",
         "delta": tr("tuile_plus_solide_detail",
                     {"debut": r1["periode"][0], "fin": r1["periode"][1]}),
         "good": True},
        {"label": tr("tuile_geographique"), "value": "1", "icon": "map-pin",
         "delta": tr("tuile_geographique_detail")},
        {"label": tr("tuile_plus_attendu"), "value": f'{r5["observations"]}',
         "unit": tr("unite_annees"), "icon": "flag",
         "delta": tr("tuile_plus_attendu_detail"), "good": False},
    ])

    if not affichees:
        st.info(tr("info_aucun_croisement"))
        return

    # ── Recette 1 ────────────────────────────────────────────────────────────
    if visible("acces_et_moyens"):
        with card(tr("r1_titre"), tr("r1_sous_titre"), "trending-up"):
            _entete_recette("acces_et_moyens", r1)
            charts.line_indexed(
                [
                    {"name": tr("r1_serie_acces"),
                     "x": r1["table"]["annee"].tolist(),
                     "y": r1["table"]["acces_indice"].round(1).tolist()},
                    {"name": tr("r1_serie_depense"),
                     "x": r1["table"]["annee"].tolist(),
                     "y": r1["table"]["depense_indice"].round(1).tolist()},
                ],
                base_year=r1["periode"][0],
            )
            note(tr("r1_note", {
                "ecart": fr_number(r1["ecart_final"], 0),
                "annee": r1["periode"][1],
            }))
            charts.table_twin(
                r1["table"].round(1).rename(columns={
                    "annee": tr("colonne_annee"),
                    "acces": tr("colonne_acces"),
                    "depense": tr("colonne_depense_pib"),
                    "acces_indice": tr("colonne_acces_indice"),
                    "depense_indice": tr("colonne_depense_indice"),
                    "ecart": tr("colonne_ecart"),
                })
            )

    # ── Recette 2 ────────────────────────────────────────────────────────────
    if visible("budget_par_acces"):
        with card(tr("r2_titre"), tr("r2_sous_titre"), "wallet"):
            _entete_recette("budget_par_acces", r2)
            charts.line_series(
                [{"name": tr("r2_serie"),
                  "x": r2["table"]["annee"].tolist(),
                  "y": r2["table"]["budget_par_point"].round(0).tolist()}],
                unit="M FCFA",
                height=260,
            )
            note(tr("r2_note", {
                "debut": r2["periode"][0], "fin": r2["periode"][1],
                "budget": fr_number(r2["evolution_budget"], 0),
                "acces": fr_number(r2["evolution_acces"], 0),
                "ratio": fr_number(r2["evolution_ratio"], 0),
            }))
            charts.table_twin(
                r2["table"].round(1).rename(columns={
                    "annee": tr("colonne_annee"),
                    "es_vote": tr("colonne_budget_vote"),
                    "es_execute": tr("colonne_execute"),
                    "taux_acces": tr("colonne_taux_acces"),
                    "budget_par_point": tr("colonne_budget_par_point"),
                })
            )

    # ── Recette 3 ────────────────────────────────────────────────────────────
    if visible("coherence_financement"):
        with card(tr("r3_titre"), tr("r3_sous_titre"), "search"):
            _entete_recette("coherence_financement", r3)
            charts.line_indexed(
                [
                    {"name": tr("r3_serie_budget"),
                     "x": r3["table"]["annee"].tolist(),
                     "y": r3["table"]["budget_indice"].round(1).tolist()},
                    {"name": tr("r3_serie_depense"),
                     "x": r3["table"]["annee"].tolist(),
                     "y": r3["table"]["depense_indice"].round(1).tolist()},
                ],
                base_year=r3["periode"][0],
            )
            note(tr("r3_note", {
                "budget": fr_number(r3["budget_evolution"], 0),
                "depense": fr_number(abs(r3["depense_evolution"]), 0),
            }))
            charts.table_twin(
                r3["table"].round(1).rename(columns={
                    "annee": tr("colonne_annee"),
                    "es_vote": tr("colonne_budget_vote"),
                    "depense_pib": tr("colonne_depense_pib"),
                })
            )

    # ── Recette 4 ────────────────────────────────────────────────────────────
    if visible("reseaux_par_region"):
        with card(tr("r4_titre"), tr("r4_sous_titre"), "map-pin"):
            _entete_recette("reseaux_par_region", r4)

            table = r4["table"]
            charts.bar_stacked_h(
                table.rename(columns={
                    "technique": tr("r4_serie_technique"),
                    "superieur": tr("r4_serie_superieur"),
                }),
                "region", [tr("r4_serie_technique"), tr("r4_serie_superieur")],
            )
            plateaux = table[table.region == "Plateaux"]
            note(tr("r4_note", {
                "part_tech": fr_number(table.iloc[0]["part_technique"], 0),
                "part_sup": fr_number(table.iloc[0]["part_superieur"], 0),
                "plateaux_tech": fr_number(plateaux["part_technique"].iloc[0], 0),
                "plateaux_sup": fr_number(plateaux["part_superieur"].iloc[0], 0),
            }))
            note(tr("r4_reserve", {"millesimes": r4["millesimes"]}))
            charts.table_twin(
                table.round(1).rename(columns={
                    "region": tr("colonne_region"),
                    "technique": tr("colonne_technique"),
                    "superieur": tr("colonne_superieur"),
                    "total": tr("colonne_total"),
                    "part_technique": tr("colonne_part_technique"),
                    "part_superieur": tr("colonne_part_superieur"),
                    "ecart_points": tr("colonne_ecart_points"),
                })
            )

    # ── Recette 5 ────────────────────────────────────────────────────────────
    if visible("acces_et_insertion"):
        with card(tr("r5_titre"), tr("r5_sous_titre"), "flag"):
            _entete_recette("acces_et_insertion", r5)
            charts.scatter_fit(
                r5["table"]["acces"], r5["table"]["chomage"],
                labels=r5["table"]["annee"].astype(int),
                x_titre=tr("r5_axe_x"), y_titre=tr("r5_axe_y"),
                height=280,
            )
            note(tr("r5_note", {
                "obs": r5["observations"],
                "debut": r5["periode"][0], "fin": r5["periode"][1],
            }))
            charts.table_twin(
                r5["table"].round(2).rename(columns={
                    "annee": tr("colonne_annee"),
                    "acces": tr("colonne_acces"),
                    "chomage": tr("colonne_chomage"),
                })
            )

    # ── Recette 6 ────────────────────────────────────────────────────────────
    if visible("acces_et_effectifs") and r6:
        with card(tr("r6_titre"), tr("r6_sous_titre"), "graduation-cap"):
            _entete_recette("acces_et_effectifs", r6)
            charts.line_indexed(
                [
                    {"name": tr("r6_serie_taux"),
                     "x": r6["table"]["annee"].tolist(),
                     "y": r6["table"]["taux_indice"].round(1).tolist()},
                    {"name": tr("r6_serie_effectifs"),
                     "x": r6["table"]["annee"].tolist(),
                     "y": r6["table"]["effectifs_indice"].round(1).tolist()},
                ],
                base_year=r6["periode"][0],
            )
            note(tr("r6_note_1"))
            note(tr("r6_note_2", {
                "debut": r6["periode"][0], "fin": r6["periode"][1],
                "taux": fr_number(r6["var_taux"], 1),
                "effectifs": fr_number(r6["var_effectifs"], 1),
                "ecart": fr_number(r6["ecart_points"], 1),
            }))
            charts.table_twin(
                r6["table"].round(1).rename(columns={
                    "annee": tr("colonne_annee"),
                    "taux": tr("colonne_taux_brut"),
                    "effectifs": tr("colonne_effectifs"),
                    "taux_indice": tr("colonne_taux_indice"),
                    "effectifs_indice": tr("colonne_effectifs_indice"),
                })
            )
