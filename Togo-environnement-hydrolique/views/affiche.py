"""Affiche — la page qui affirme, sans sidebar.

Aucun texte visible ici : tout vient de `i18n/locales/affiche.json`.

**Le contenu des deux colonnes n'est pas encore écrit.** Ce module ne monte
pour l'instant que le GABARIT : le menu haut, les quatre vues, et deux zones
marquées. Il sert à valider la structure avant d'y verser quoi que ce soit.
"""

# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui, charts
from socle.charts import maps
from socle.charts.maps import silhouette_svg
from socle.design.tokens import RISQUE_OFFICIEL, RISQUE_CONTOUR, SERIES
from socle.shell import render_affiche
from socle.shell.affiche import hauteur_colonne_droite
from socle.i18n.traduction import t

from views import annexes as annexes_vue
from views import croisements as croisements_vue
from views import demographie as demographie_vue
from views import donnees as donnees_vue
from views import parc as parc_vue
from views import recommandations as recommandations_vue
from views import risque as risque_vue
from views import recit
from socle.design.marque import datalab_marque

from utils import liens
from utils.data import datasets, apply_filters
from utils import analytics, perimetre, barres

# Les quatre vues du menu haut. « Données » et « Annexes » en sont écartées :
# elles servent à vérifier, pas à convaincre, et restent accessibles depuis le
# tableau de bord complet.
VUES = ["diagnostic", "risque", "parc", "priorites"]

# Vert du drapeau togolais — couleur de MARQUE, jamais de série.
VERT_TOGO = "#006A4E"

# Les deux teintes de surface de la page, déclarées UNE fois. Le menu et les
# deux colonnes partagent le même fond et le même trait : trois valeurs
# proches mais distinctes se voient — l'œil lit un défaut d'alignement là où
# il n'y a qu'une inattention.
FOND = "#FFFFFF"                      # le menu seul
TEINTE_COLONNES = "#F0F0F0"           # fond ET bordure de la colonne gauche

# La colonne droite est une AUTRE moitié, pas la suite de la première : elle
# porte donc sa propre teinte, d'un cran plus sombre, et un filet la sépare.
# À fond identique et sans trait, les deux colonnes coulaient l'une dans
# l'autre et la page se lisait comme un seul bloc — l'écran n'était partagé
# que dans le code.
TEINTE_DROITE = "#E6E9EC"
FILET = "#D3D8DE"

# Échelle de la page. Déclarée ici plutôt qu'au seul appel de `render_affiche`
# parce que la hauteur de la colonne droite s'en déduit : sous `zoom`, un
# pixel de mise en page ne vaut plus un pixel d'écran.
# 0,85 : réglé à l'écran sur un portable de 1 440 × 820, où la page à
# l'échelle 1 débordait avant même la première carte.
ECHELLE = 0.85

# Ce que le rail d'onglets prend dans la colonne droite, au-dessus du panneau
# de carte : sa propre hauteur et l'écart qui le sépare du panneau. Mesuré à
# l'écran. Le reste du poste — titre, rembourrages, bandeau de légende — est
# connu de `maps.hauteur_dans`, qui est seul à savoir de quoi une carte est
# faite.
RAIL_ONGLETS = 43


def _zone(libelle, detail, hauteur):
    """Zone de contenu — provisoire, le temps de valider le gabarit.

    Bâtie sur `ui.panneau` plutôt qu'en HTML maison : c'est la brique que le
    vrai contenu occupera, et la tester dès maintenant évite de découvrir ses
    marges au moment de la remplir.
    """

    with ui.panneau(hauteur=hauteur, couleur=TEINTE_COLONNES):
        st.markdown(
            f'<div style="text-align:center;padding:24px 0;">'
            f'<div style="font-size:12px;letter-spacing:.1em;'
            f'text-transform:uppercase;color:var(--kg-color-text-muted);">'
            f'{libelle}</div>'
            f'<div style="font-size:13px;color:var(--kg-color-text-secondary);'
            f'margin-top:6px;">{detail}</div></div>',
            unsafe_allow_html=True,
        )


def _filtrer(data):
    """Barre de l'affiche, et son effet sur les trois jeux.

    Le filtre se PEINT à gauche mais s'applique aux deux colonnes : une région
    choisie qui ne redessinerait pas les cartes ferait mentir la page.

    Deux portées, et elles ne se confondent pas :

    · le TERRITOIRE — région, préfecture, canton — cadre le référentiel, et
      les deux parcs suivent par leur rattachement de canton ;
    · l'ANNÉE d'achèvement n'existe qu'au COSO, et ne restreint que lui. Le
      référentiel des cantons ne porte aucune date, le parc TdE non plus :
      leur appliquer l'intervalle les viderait entièrement.

    Les deux parcs ne sont restreints par le territoire que si une modalité
    est réellement cochée. À pleine amplitude, les joindre au référentiel
    écarterait les ouvrages dont le canton n'y est pas rattaché — 27
    microprojets COSO — et le total afficherait 191 au lieu de 218 sans que
    personne n'ait rien demandé. Un filtre au repos ne doit rien retirer.
    """

    selection = barres.zone_territoriale(data["cantons"], coso=data["coso"])

    territoire = {colonne: valeur for colonne, valeur in selection.items()
                  if colonne != "annee_achevement"}

    cantons = apply_filters(data["cantons"], territoire)
    # `apply_filters` ignore une colonne absente du cadre : la même sélection
    # peut donc être servie aux trois jeux, chacun ne retenant que ce qui le
    # concerne. L'année ne mord que sur le COSO, seul à la porter.
    coso = apply_filters(data["coso"], selection)

    if not any(territoire.values()):
        return {**data, "cantons": cantons, "coso": coso}

    cles = set(cantons["cle_canton"])

    return {
        **data,
        "cantons": cantons,
        "tde": data["tde"][data["tde"]["cle_canton"].isin(cles)],
        "coso": coso[coso["cle_canton"].isin(cles)],
    }


def _gauche_diagnostic(tr, data, faits, corpus):
    """Colonne 62 % de la vue Diagnostic — les chiffres et les graphes.

    Reprend les blocs de `?s=synthese&t=diagnostic`, textes compris : le
    domaine i18n `synthese` sert les deux pages, et un chiffre corrigé là-bas
    se corrige ici sans qu'on y pense.
    """

    ui.stat_tiles([
        {"value": ui.fr_number(faits["cantons"]), "label": tr("tuile_cantons"),
         "delta": tr("tuile_cantons_detail", {"regions": faits["regions"]}),
         "good": None, "icon": "map-pin"},
        {"value": ui.compact(faits["population"]),
         "label": tr("tuile_population"),
         "delta": tr("tuile_population_detail"), "good": None,
         "icon": "trending-up"},
        {"value": ui.fr_number(faits["cantons_sans_ouvrage"]),
         "label": tr("tuile_sans_ouvrage"),
         "delta": tr("tuile_sans_ouvrage_detail",
                     {"part": ui.fr_number(faits["part_sans_ouvrage"], 0)}),
         "good": False, "icon": "search"},
        {"value": "7 / 33", "label": tr("tuile_publies"),
         "delta": tr("tuile_publies_detail"), "good": False, "icon": "table-2"},
    ])

    with ui.card(tr("carte_parcs_titre"), tr("carte_parcs_sous_titre"),
                 "building-2"):
        fusion = (
            analytics.tde_par_region(data["tde"])
            .rename(columns={"ouvrages": "TdE"})
            .merge(
                analytics.coso_par_region(data["coso"])
                .rename(columns={"ouvrages": "COSO"}),
                on="region", how="outer")
            .fillna(0)
        )

        charts.bar_stacked_h(fusion, "region", ["TdE", "COSO"],
                             unit=tr("unite_ouvrages"))
        # Le CORPUS, pas la sélection : cette note énonce un constat sur les
        # deux inventaires — ils ne se recouvrent pas —, elle ne décrit pas ce
        # que le graphe montre. Nourrie du filtre, elle produisait sous
        # « Savanes » un « 0 % des 0 ouvrages TdE sont en Maritime » qui n'est
        # ni faux ni utile, seulement absurde.
        ui.note(tr("note_parcs", {
            "tde": ui.fr_number(corpus["tde_total"]),
            "part_maritime": ui.fr_number(corpus["tde_part_maritime"], 0),
            "coso": ui.fr_number(corpus["coso_total"]),
        }))
        charts.table_twin(fusion.rename(columns={"region": tr("col_region")}))

    with ui.card(tr("carte_publication_titre"),
                 tr("carte_publication_sous_titre"), "table-2"):
        ecart = perimetre.ecart_publication()
        cadre = pd.DataFrame([
            {"etat": tr("champs_publies"), "champs": int(ecart["communs"])},
            {"etat": tr("champs_absents"), "champs": int(ecart["absents"])},
        ])

        # Anneau : « 7 champs décrits sur 33 » est une part d'un tout, et deux
        # barres laissaient le lecteur faire la division lui-même.
        #
        # Les deux parts sont `absents` et `communs`, JAMAIS `publies` : ce
        # dernier compte les colonnes du fichier diffusé — huit, dont `FID` et
        # `geometry`, qui ne figurent dans aucun dictionnaire. Les additionner
        # aux 26 champs manquants donnait 34 pour un référentiel de 33, en
        # mélangeant deux populations. C'est l'anneau qui l'a révélé : une part
        # d'un tout ne pardonne pas ce que deux barres laissaient passer.
        charts.anneau(
            [tr("champs_absents"), tr("champs_publies")],
            [int(ecart["absents"]), int(ecart["communs"])],
            centre=f'{int(ecart["communs"])} / {int(ecart["decrits"])}',
            sous_centre=tr("champs_publies"), height=260,
        )
        ui.note(tr("note_publication", {
            "decrits": ecart["decrits"], "publies": ecart["communs"],
            "part": ui.fr_number(ecart["part_publiee"], 0),
        }))
        charts.table_twin(cadre.rename(columns={
            "etat": tr("col_etat"), "champs": tr("col_champs")}))


def _carte_risque(tr, data, hauteur_carte):
    def dessin(hauteur):
        return maps.choroplethe(
            data["cantons"], valeur="risque_pts", cle="carte_aff_risque",
            champs=["canton", "prefecture", "risque_pts", "population"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_risque"), tr("col_population")],
            height=hauteur, rampe=RISQUE_OFFICIEL,
            couleur_contour=RISQUE_CONTOUR,
        )

    def pied(resultat):
        bornes, _ = resultat

        if not bornes:
            return

        repartition = analytics.repartition_par_classe(
            data["cantons"], bornes,
            [tr(f"classe_{i}") for i in range(1, len(bornes))],
        )
        maps.legende_paliers(
            bornes, rampe=RISQUE_OFFICIEL, libelle=tr("legende_titre"),
            unite=" pts", decimales=1,
            effectifs=repartition["cantons"].tolist(),
        )
        ui.note(tr("note_risque", {
            "seuil": ui.fr_number(bornes[-2], 1),
            "cantons": ui.fr_number(int(repartition["cantons"].iloc[-1])),
            "population": ui.compact(float(repartition["population"].iloc[-1])),
        }))

    maps.carte(tr("carte_risque_titre"), cle="aff_risque", dessin=dessin,
               legende=pied, sous_titre=tr("carte_risque_sous_titre"),
               hauteur=hauteur_carte)


def _carte_parcs(tr, data, faits, corpus, hauteur_carte):
    # Les DEUX inventaires sur une seule carte. En deux cartes, l'œil devait
    # faire l'aller-retour ; superposés sur le même fond, le fait central se
    # lit d'un coup : les points bleus tiennent dans le sud, les orange dans
    # le nord, et le centre du pays reste vide.
    coso_situes = data["coso"][data["coso"]["situe"]]

    def dessin(hauteur):
        maps.points_multi(
            [
                # Le COSO d'abord, le TdE ensuite : 218 points contre 67, et
                # les 67 se peignent au-dessus pour rester visibles.
                {"df": coso_situes, "libelle": tr("mini_coso"),
                 "couleur": SERIES[1], "rayon": 4,
                 "infobulle": lambda ligne: (
                     f'<b>{ligne["localite"]}</b><br>{ligne["type_ouvrage"]}'
                     f'<br>{ligne["canton"]} · {ligne["region"]}')},
                {"df": data["tde"], "libelle": tr("mini_tde"),
                 "couleur": SERIES[0], "rayon": 5,
                 "infobulle": lambda ligne: (
                     f'<b>{ligne["ouvrage"]}</b><br>{ligne["nature"]}'
                     f'<br>{ligne["canton"]} · {ligne["region"]}')},
            ],
            cle="carte_aff_parcs",
            # Le fond commande le cadrage : sans lui la carte s'ajusterait aux
            # ouvrages et montrerait leur enveloppe, jamais le pays — or c'est
            # le vide entre les deux amas qui porte le constat.
            fond=data["cantons"],
            height=hauteur,
        )

    def pied(_):
        maps.legende_series([
            {"libelle": tr("mini_tde"), "couleur": SERIES[0],
             "detail": ui.fr_number(faits["tde_total"])},
            {"libelle": tr("mini_coso"), "couleur": SERIES[1],
             "detail": tr("legende_coso_situes",
                          {"situes": faits["coso_situes"],
                           "total": faits["coso_total"]})},
        ])
        # Le constat porte sur le corpus, la légende ci-dessus porte déjà sur
        # ce qui est dessiné.
        ui.note(tr("note_couverture", {
            "part_maritime": ui.fr_number(corpus["tde_part_maritime"], 0),
            "sans": ui.fr_number(corpus["cantons_sans_ouvrage"]),
        }))

    maps.carte(tr("parcs_carte_titre"), cle="aff_parcs", dessin=dessin,
               legende=pied, sous_titre=tr("parcs_carte_sous_titre"),
               hauteur=hauteur_carte)


def _carte_angle_mort(tr, data, hauteur_carte):
    couverture = analytics.couverture(data["cantons"], data["tde"],
                                      data["coso"])

    def dessin(hauteur):
        # Classes linéaires à deux paliers — des quantiles sur un indicateur
        # 0/1 à 85 % de zéros dégénéreraient en une classe unique.
        maps.choroplethe(
            couverture, valeur="couvert", cle="carte_aff_angle",
            champs=["canton", "prefecture", "region", "ouvrages"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_region"), tr("col_ouvrages")],
            height=hauteur, nombre=2, methode="lineaire",
        )

    def pied(_):
        # Pas de legende_paliers : des bornes « 0 / 0,5 / 1 » ne disent rien
        # sur un indicateur binaire. La note porte les effectifs.
        ui.note(tr("note_angle_mort", {
            "couverts": ui.fr_number(int(couverture["couvert"].sum())),
            "sans": ui.fr_number(int((couverture["couvert"] == 0).sum())),
            "part": ui.fr_number(
                100 * (couverture["couvert"] == 0).sum() / len(couverture), 0),
        }))

    maps.carte(tr("limites_carte_titre"), cle="aff_angle", dessin=dessin,
               legende=pied, sous_titre=tr("limites_carte_sous_titre"),
               hauteur=hauteur_carte)


def _droite_diagnostic(tr, data, faits, corpus, hauteur_carte):
    """Colonne 38 % — les trois cartes, une par onglet.

    Empilées, elles imposaient un défilement de trois hauteurs de carte et
    invitaient à les comparer côte à côte alors qu'elles ne répondent pas à la
    même question. En onglets, on en regarde une à la fois.

    Colonne étroite et cartes hautes : le Togo s'étire sur 5,15° de latitude
    pour 1,9° de longitude, c'est la HAUTEUR qui fixe le zoom et le pays
    ENTIER entre.
    """

    retenu = ui.onglets([
        ("risque", tr("onglet_risque")),
        ("parcs", tr("onglet_parcs")),
    ], cle="cartes_affiche", libelle=tr("onglets_cartes"), fond="#FFFFFF")

    # La couverture du corpus a quitté ce rang : elle est le sujet ENTIER de
    # l'onglet « Les limites », et la garder ici en aurait fait la troisième
    # carte d'une vue qui parle d'autre chose.
    if retenu == "parcs":
        _carte_parcs(tr, data, faits, corpus, hauteur_carte)
    else:
        _carte_risque(tr, data, hauteur_carte)



# ─── Vue « risque » ──────────────────────────────────────────────────────────

def _gauche_risque(tr, data, faits, corpus):
    """Le fait central du défi : où le risque se concentre, et sur qui."""

    classes = analytics.population_par_classe(data["cantons"])
    hautes = classes[classes["classe_officielle"].isin(analytics.CLASSES_HAUTES)]

    ui.stat_tiles([
        {"value": ui.fr_number(int(hautes["cantons"].sum())),
         "label": tr("risque_tuile_cantons"),
         "delta": tr("risque_tuile_cantons_detail", {
             "part": ui.fr_number(100 * hautes["cantons"].sum()
                                  / len(data["cantons"]), 0)}),
         "good": False, "icon": "flag"},
        {"value": ui.compact(float(hautes["population"].sum())),
         "label": tr("risque_tuile_population"),
         "delta": tr("risque_tuile_population_detail", {
             "part": ui.fr_number(hautes["part_population"].sum(), 0)}),
         "good": False, "icon": "trending-up"},
        {"value": ui.fr_number(faits["risque_median"], 1), "unit": " pts",
         "label": tr("risque_tuile_median"),
         "delta": tr("risque_tuile_median_detail", {
             "canton": faits["canton_le_plus_expose"],
             "max": ui.fr_number(faits["risque_max"], 1)}),
         "good": None, "icon": "map-pin"},
    ])

    with ui.card(tr("risque_carte_classes_titre"),
                 tr("risque_carte_classes_sous_titre"), "flag"):
        lisible = classes.assign(
            classe=classes["classe_officielle"].map(
                lambda c: tr(f"classe_off_{c}")))

        # Barres de POPULATION, non de cantons : compter les cantons donnerait
        # « 17 sur 388 » et ferait passer le sujet pour marginal, quand ces
        # 17 cantons abritent un tiers du pays.
        # `trier=False` : l'échelle de risque a un ordre propre, et le
        # classement par effectif la mélangeait.
        charts.bar_h(lisible, "classe", "population",
                     unit=tr("unite_habitants"),
                     highlight=tr("classe_off_tres_eleve"), trier=False)
        ui.note(tr("risque_note_classes", {
            "cantons": ui.fr_number(int(hautes["cantons"].sum())),
            "part_cantons": ui.fr_number(100 * hautes["cantons"].sum()
                                         / len(data["cantons"]), 0),
            "part_pop": ui.fr_number(hautes["part_population"].sum(), 0),
        }))
        charts.table_twin(lisible[["classe", "cantons", "population"]].rename(
            columns={"classe": tr("col_classe"), "cantons": tr("col_cantons"),
                     "population": tr("col_population")}))

    with ui.card(tr("risque_carte_matrice_titre"),
                 tr("risque_carte_matrice_sous_titre"), "search"):
        matrice = analytics.matrice_risque_equipement(
            data["cantons"], data["tde"], data["coso"])
        lisible = matrice.assign(
            classe=matrice["classe_officielle"].map(
                lambda c: tr(f"classe_off_{c}")))

        charts.bar_stacked_h(
            lisible.rename(columns={"equipes": tr("col_equipes"),
                                    "sans_ouvrage": tr("col_sans_ouvrage")}),
            "classe", [tr("col_equipes"), tr("col_sans_ouvrage")],
            unit=tr("unite_cantons"))
        ui.note(tr("risque_note_matrice", {
            "part": ui.fr_number(
                matrice.loc[matrice["classe_officielle"].isin(
                    analytics.CLASSES_HAUTES), "part_equipee"].mean(), 0),
        }))
        charts.table_twin(lisible[["classe", "cantons", "equipes",
                                   "sans_ouvrage"]].rename(columns={
            "classe": tr("col_classe"), "cantons": tr("col_cantons"),
            "equipes": tr("col_equipes"),
            "sans_ouvrage": tr("col_sans_ouvrage")}))


def _droite_risque(tr, data, faits, corpus, hauteur_carte):
    """Une seule carte : le risque, dans les CLASSES du producteur."""

    def dessin(hauteur):
        return maps.choroplethe(
            data["cantons"], valeur="risque_pts", cle="carte_aff_risque_off",
            champs=["canton", "prefecture", "risque_pts", "population"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_risque"), tr("col_population")],
            height=hauteur, rampe=RISQUE_OFFICIEL,
            couleur_contour=RISQUE_CONTOUR,
            # Les BORNES DU PRODUCTEUR, pas des quantiles : c'est la carte
            # officielle que cette vue rejoue, et un lecteur qui la compare à
            # la planche du ministère doit y retrouver les mêmes teintes.
            bornes=[b * 100 for b in analytics.SEUILS_OFFICIELS],
        )

    def pied(resultat):
        bornes, _ = resultat

        if not bornes:
            return

        classes = analytics.population_par_classe(data["cantons"])
        maps.legende_paliers(
            bornes, rampe=RISQUE_OFFICIEL, libelle=tr("legende_officielle"),
            unite=" pts", decimales=0,
            effectifs=classes["cantons"].tolist(),
        )
        ui.note(tr("risque_note_carte"))

    maps.carte(tr("risque_carte_titre"), cle="aff_risque_off", dessin=dessin,
               legende=pied, sous_titre=tr("risque_carte_sous_titre"),
               hauteur=hauteur_carte)




# ─── Vue « parc » ────────────────────────────────────────────────────────────

def _gauche_parc(tr, data, faits, corpus):
    """Ce que le COSO documente de sa propre exécution — délais et argent."""

    coso = data["coso"]
    budget = analytics.chaine_budgetaire(coso)
    benef = analytics.beneficiaires(coso)
    retards = analytics.delais(coso)["retard_jours"].dropna()

    ui.stat_tiles([
        {"value": ui.fr_number(int((retards > 0).sum())),
         "label": tr("parc_tuile_retard"),
         "delta": tr("parc_tuile_retard_detail", {
             "total": ui.fr_number(int(len(retards))),
             "median": ui.fr_number(retards.median(), 0)}),
         "good": False, "icon": "settings"},
        {"value": ui.compact(benef["total"]),
         "label": tr("parc_tuile_beneficiaires"),
         "delta": tr("parc_tuile_beneficiaires_detail", {
             "part": ui.fr_number(benef["part_femmes"], 0)}),
         "good": None, "icon": "trending-up"},
        {"value": ui.compact(float(budget.loc[budget["etape"] == "paye",
                                              "montant"].iloc[0])),
         "label": tr("parc_tuile_paye"),
         "delta": tr("parc_tuile_paye_detail"), "good": None, "icon": "table-2"},
    ])

    with ui.card(tr("parc_carte_delais_titre"),
                 tr("parc_carte_delais_sous_titre"), "settings"):
        par_type = analytics.delais_par_type(coso)
        court = par_type.assign(
            type_court=par_type["cle_type"].map(lambda c: tr(f"type_{c}")))

        charts.bar_h(court, "type_court", "retard_median",
                     unit=tr("unite_jours"))
        ui.note(tr("parc_note_delais", {
            "en_retard": ui.fr_number(int((retards > 0).sum())),
            "total": ui.fr_number(int(len(retards))),
            "median": ui.fr_number(retards.median(), 0),
        }))
        charts.table_twin(par_type.rename(columns={
            "type_ouvrage": tr("col_type"), "ouvrages": tr("col_ouvrages"),
            "retard_median": tr("col_retard"),
            "en_retard": tr("col_en_retard")}))

    with ui.card(tr("parc_carte_budget_titre"),
                 tr("parc_carte_budget_sous_titre"), "table-2"):
        lisible = budget.assign(
            etape=budget["etape"].map(lambda e: tr(f"etape_{e}")))
        charts.bar_h(lisible, "etape", "montant", unit=tr("unite_fcfa"),
                     highlight=tr("etape_estime"))

        estime = float(budget.loc[budget["etape"] == "estime", "montant"].iloc[0])
        contracte = float(budget.loc[budget["etape"] == "contracte",
                                     "montant"].iloc[0])
        ui.note(tr("parc_note_budget", {
            "estime": ui.compact(estime), "contracte": ui.compact(contracte),
            "ecart": ui.fr_number(100 * (1 - contracte / estime), 0),
        }))
        charts.table_twin(lisible.rename(columns={
            "etape": tr("col_etape"), "montant": tr("col_montant"),
            "ouvrages": tr("col_ouvrages")}))


def _droite_parc(tr, data, faits, corpus, hauteur_carte):
    """Les deux inventaires sur un seul fond — l'emprise réelle du parc."""

    _carte_parcs(tr, data, faits, corpus, hauteur_carte)


# ─── Vue « priorités » ───────────────────────────────────────────────────────

def _gauche_priorites(tr, data, faits, corpus):
    """La recommandation n'est pas une phrase : c'est cette liste."""

    prioritaires = analytics.cantons_prioritaires(
        data["cantons"], data["tde"], data["coso"])
    cpb = analytics.cout_par_beneficiaire(data["coso"])
    mediane_cout = float(cpb["cout_beneficiaire"].median()) if len(cpb) else 0.0

    ui.stat_tiles([
        {"value": ui.fr_number(len(prioritaires)),
         "label": tr("prio_tuile_cantons"),
         "delta": tr("prio_tuile_cantons_detail"), "good": False,
         "icon": "flag"},
        {"value": ui.compact(float(prioritaires["population"].sum())),
         "label": tr("prio_tuile_population"),
         "delta": tr("prio_tuile_population_detail"), "good": False,
         "icon": "trending-up"},
        {"value": ui.fr_number(mediane_cout, 0), "unit": " F",
         "label": tr("prio_tuile_cout"),
         "delta": tr("prio_tuile_cout_detail", {
             "n": ui.fr_number(len(cpb))}), "good": None, "icon": "table-2"},
    ])

    with ui.card(tr("prio_carte_liste_titre"), tr("prio_carte_liste_sous_titre"),
                 "flag"):
        # Sucettes et non barres : la population s'étale de 6 000 à 294 000
        # habitants, et douze barres pleines à cette dynamique noircissent la
        # carte sans rien ajouter à la comparaison.
        charts.sucette_h(prioritaires, "canton", "population",
                         unit=tr("unite_habitants"))
        ui.note(tr("prio_note_liste", {
            "n": ui.fr_number(len(prioritaires)),
            "population": ui.compact(float(prioritaires["population"].sum())),
        }))
        charts.table_twin(prioritaires.rename(columns={
            "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
            "region": tr("col_region"), "risque_pts": tr("col_risque"),
            "population": tr("col_population")}))

    with ui.card(tr("prio_carte_leviers_titre"),
                 tr("prio_carte_leviers_sous_titre"), "search"):
        for index in range(1, 4):
            ui.note(tr(f"prio_levier_{index}", {
                "cantons": ui.fr_number(len(prioritaires)),
                "cout": ui.fr_number(mediane_cout, 0),
            }))


def _droite_priorites(tr, data, faits, corpus, hauteur_carte):
    """Les cantons à couvrir, sur la carte du risque officiel."""

    prioritaires = analytics.cantons_prioritaires(
        data["cantons"], data["tde"], data["coso"])
    noms = set(prioritaires["canton"])

    def dessin(hauteur):
        # Une choroplèthe BINAIRE : prioritaire ou non. Reprendre la teinte du
        # risque ferait relire la même carte que l'onglet précédent, alors que
        # la question a changé — non plus « où est le risque » mais « où faut-il
        # aller ».
        cadre = data["cantons"].assign(
            prioritaire=data["cantons"]["canton"].isin(noms).astype(int))

        return maps.choroplethe(
            cadre, valeur="prioritaire", cle="carte_aff_prio",
            champs=["canton", "prefecture", "region", "population"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_region"), tr("col_population")],
            height=hauteur, nombre=2, methode="lineaire",
        )

    def pied(_):
        ui.note(tr("prio_note_carte", {"n": ui.fr_number(len(prioritaires))}))

    maps.carte(tr("prio_carte_titre"), cle="aff_prio", dessin=dessin,
               legende=pied, sous_titre=tr("prio_carte_sous_titre"),
               hauteur=hauteur_carte)



# ─── Portage de la console ───────────────────────────────────────────────────
#
# Les sections de la console deviennent le premier rang du menu, ses onglets le
# second. Le contenu, lui, se répartit selon une règle unique :
#
#   · une vue qui portait une CARTE la voit passer à droite, ses graphes
#     restant à gauche ;
#   · une vue de graphes purs — dix-sept des vingt et une — garde tout à
#     gauche, et reçoit à droite la carte de RÉFÉRENCE de sa section.
#
# La seconde moitié de la règle n'est pas un remplissage. Une colonne droite
# vide sur dix-sept vues sur vingt et une aurait fait de l'affiche une page à
# une colonne avec une bande blanche ; et une carte de référence stable donne
# au lecteur un repère qui ne bouge pas quand il change d'onglet.


def _perimetre_partage(brut):
    """Le périmètre retenu par la barre de filtres de la vue portée.

    La colonne gauche se peint AVANT la droite : quand elle a fini, les clés
    de session `filtre_region` et `filtre_prefecture` portent déjà la
    sélection. La carte de droite les relit plutôt que d'afficher le pays
    entier — sinon elle contredirait, sans le dire, la colonne d'à côté.

    Ce sont les MÊMES clés que la console : elles sont partagées entre toutes
    les vues qui portent la même matière, et c'est ce partage qui rend la
    lecture possible ici sans rien passer d'une colonne à l'autre.
    """

    cantons = brut["cantons"]
    restreint = False

    for colonne, cle in (("region", "filtre_region"),
                         ("prefecture", "filtre_prefecture")):
        retenues = st.session_state.get(cle) or []

        if retenues:
            cantons = cantons[cantons[colonne].isin(retenues)]
            restreint = True

    if not restreint:
        return {**brut, "cantons": cantons}

    # Les deux parcs suivent le référentiel, et seulement quand une modalité
    # est cochée : à pleine amplitude, les joindre écarterait les ouvrages dont
    # le canton n'est pas rattaché. C'est la règle de `_filtrer`, et les cartes
    # du récit — entretien, débit, remise — la demandent : elles peignent des
    # OUVRAGES, non des cantons, et resteraient nationales sous un filtre
    # régional.
    cles = set(cantons["cle_canton"])

    return {
        **brut,
        "cantons": cantons,
        "tde": brut["tde"][brut["tde"]["cle_canton"].isin(cles)],
        "coso": brut["coso"][brut["coso"]["cle_canton"].isin(cles)],
    }


def _carte_reference_risque(tr, data, faits, corpus, hauteur_carte):
    """La carte de référence des sections qui n'en portent pas : le risque."""

    _carte_risque(tr, data, hauteur_carte)


def _console(rendu):
    """Adapte une vue de console en peintre de colonne gauche.

    La fonction de la console est appelée TELLE QUELLE : elle porte déjà ses
    tuiles, sa barre de filtres, ses cartes de contenu et ses tableaux
    jumeaux, le tout traduit et éprouvé. La réécrire pour la loger dans une
    colonne de 62 % dupliquerait des centaines de lignes pour un résultat
    identique — et deux copies d'un même calcul finissent toujours par
    diverger.
    """

    def peindre(tr, data, faits, corpus):
        rendu()

    return peindre


def _etroit(rendu):
    """Peint `rendu` dans le contexte de colonne étroite."""

    with barres.colonne_etroite():
        rendu()


def _cartes(options, cle, tr):
    """Colonne droite à PLUSIEURS cartes — une par onglet.

    Empilées, deux cartes imposent un défilement de deux hauteurs et invitent à
    les comparer côte à côte alors qu'elles ne répondent pas à la même
    question. En onglets, on en regarde une à la fois.

    `options` : liste de `(clé, libellé, peintre)`. Le rang n'est posé que s'il
    y a plus d'une carte : un onglet unique est un bouton qui ne fait rien.
    """

    if len(options) == 1:
        options[0][2]()
        return

    retenu = ui.onglets([(c, libelle) for c, libelle, _ in options],
                        cle=cle, libelle=tr("onglets_cartes"), fond=FOND)

    for c, _, peintre in options:
        if c == retenu:
            peintre()
            return

    options[0][2]()


def configuration(tr, trs, trr, brut, corpus, hauteur_carte):
    """La configuration déclarative du menu — un seul objet, tout le chemin.

    Les composants sont liés ICI à leurs données : chaque entrée reçoit des
    fonctions sans argument, prêtes à peindre. Le socle n'a donc rien à savoir
    du corpus, et la configuration n'a rien à savoir du rendu.

    Une entrée porte en outre sa carte de RÉFÉRENCE : elle vaut pour tous ses
    onglets, et la déclarer une fois évite qu'un onglet ajouté plus tard
    l'oublie et laisse la colonne droite vide.

    Les libellés sont passés DÉJÀ TRADUITS plutôt qu'en dictionnaires
    {fr, en} : la configuration se reconstruit à chaque rendu, donc dans la
    langue active, et le socle accepte les deux formes. Les textes restent
    ainsi dans les fichiers i18n du défi, où le contrôle de complétude les
    trouve — un dictionnaire écrit ici y échapperait.
    """

    etat = {}

    def propre(gauche, droite=None, traducteur=None):
        """Un onglet PROPRE à l'affiche — filtres de l'affiche, deux colonnes.

        `traducteur` désigne le domaine i18n du peintre : `synthese` pour les
        vues d'origine, `recit` pour les actes. Il est passé plutôt que deviné,
        parce qu'un peintre ne doit pas avoir à savoir dans quel domaine vivent
        ses textes — c'est la configuration qui les relie.
        """

        parle = traducteur or trs

        def peindre_gauche():
            data = _filtrer(brut)
            faits = analytics.synthese(data["cantons"], data["tde"],
                                       data["coso"], data["ventes"])
            # Les faits sont RECALCULÉS sur le périmètre retenu : les servir
            # tels que le corpus entier les donne ferait dire « 330 cantons
            # sans ouvrage » à une page qui n'en montre plus que douze.
            etat["data"], etat["faits"] = data, faits
            gauche(parle, data, faits, corpus)

        if droite is None:
            return peindre_gauche

        def peindre_droite():
            droite(parle, etat["data"], etat["faits"], corpus, hauteur_carte)

        return {"gauche": peindre_gauche, "droite": peindre_droite}

    def recit_(gauche, *cartes):
        """Un onglet du RÉCIT — peintre de gauche, et ses cartes de droite.

        Les peintres de carte de `recit` prennent `(tr, data, hauteur)`, sans
        les faits : une carte ne commente pas la synthèse, elle montre un
        territoire. La signature plus courte évite de traîner deux arguments
        que ces fonctions n'utiliseraient jamais.

        `cartes` : suite de `(clé, libellé, peintre)`. Aucune carte donnée, et
        la colonne droite retombe sur la carte de référence de la section.
        """

        def peindre_gauche():
            data = _filtrer(brut)
            faits = analytics.synthese(data["cantons"], data["tde"],
                                       data["coso"], data["ventes"])
            etat["data"], etat["faits"] = data, faits

            # L'accroche de l'acte se DÉCLARE en tête du peintre, où ses
            # chiffres sont calculés, et se peint ICI, après les tuiles et les
            # graphes : la colonne ouvre sur les faits et se referme sur le
            # propos. On vide la file avant, jamais après — une vue qui
            # échouerait en cours de route laisserait sinon son accroche à la
            # suivante.
            recit.oublier_accroches()
            gauche(trr, data, faits, corpus)
            recit.poser_accroches()

        if not cartes:
            return peindre_gauche

        def peindre_droite():
            _cartes(
                [(c, libelle,
                  (lambda p=peintre: p(trr, etat["data"], hauteur_carte)))
                 for c, libelle, peintre in cartes],
                cle="cartes_" + cartes[0][0], tr=tr,
            )

        return {"gauche": peindre_gauche, "droite": peindre_droite}

    def portee(rendu):
        """Un onglet PORTÉ de la console — il apporte ses propres filtres.

        Le rendu est enveloppé dans le contexte de COLONNE ÉTROITE : les
        barres de filtres y renoncent à leur colonne d'appui, qui laissait un
        tiers de la zone vide dans une colonne de 62 % — vérifié à l'écran sur
        la vue des forages. La console, elle, garde sa grille à douze unités.
        """

        def peindre():
            with barres.colonne_etroite():
                rendu()

        return peindre

    def carte_de_section():
        """Le repli de colonne droite : le risque, dans le périmètre partagé."""

        _carte_risque(trs, _perimetre_partage(brut), hauteur_carte)

    def carte_du_corpus():
        """Le repli de l'acte des preuves : ce que le corpus couvre."""

        _carte_angle_mort(trs, _perimetre_partage(brut), hauteur_carte)

    def avec(traducteur, peintre, *extras):
        """Fige le domaine i18n — et les arguments — d'un peintre de carte.

        Les cartes de `recit` prennent `(tr, data, hauteur)` ; celles écrites
        pour les vues d'origine en prennent cinq et lisent leurs textes dans un
        autre domaine. Plutôt que d'aligner vingt signatures, on adapte ici :
        la configuration est le seul endroit qui connaisse les deux mondes.
        """

        return lambda _tr, data, hauteur: peintre(traducteur, data, *extras,
                                                  hauteur)

    def cartes_de(cle, *cartes):
        """Colonne droite d'un onglet PORTÉ, qui n'a pas passé par `propre`.

        Le périmètre vient des clés de session posées par la barre de filtres
        de la colonne gauche — la même mécanique que `carte_de_section`, et
        pour la même raison : la carte doit montrer ce que les graphes d'à côté
        montrent, sans que rien ne transite d'une colonne à l'autre.
        """

        def peindre():
            data = _perimetre_partage(brut)

            _cartes(
                [(c, libelle, (lambda p=peintre: p(trr, data, hauteur_carte)))
                 for c, libelle, peintre in cartes],
                cle="cartes_" + cle, tr=tr,
            )

        return peindre

    return {
        "menu_active_color": VERT_TOGO,
        "menu_inactive_color": "transparent",
        "tab_active_color": FOND,
        "tab_inactive_color": "transparent",
        "menu_items": [
            # ── Acte 0 · Le constat ──────────────────────────────────────
            {"id": "constat", "name": tr("section_constat"),
             "is_default": True, "reference": None, "tab_items": [
                {"id": "home", "name": tr("vue_home"), "is_default": True,
                 "component": propre(_gauche_diagnostic, _droite_diagnostic)},
                {"id": "paradoxe", "name": tr("vue_paradoxe"),
                 "component": recit_(recit.paradoxe, (
                     "bivariee", tr("onglet_bivariee"), recit.carte_bivariee))},
                {"id": "limites", "name": tr("vue_limites"),
                 "component": recit_(recit.limites, (
                     "couverture", tr("onglet_couverture"),
                     avec(trs, _carte_angle_mort)))},
            ]},

            # ── Acte 1 · Où est l'eau ? ──────────────────────────────────
            {"id": "ou", "name": tr("section_ou"),
             "reference": carte_de_section, "tab_items": [
                {"id": "repartition", "name": tr("vue_repartition"),
                 "is_default": True,
                 "component": recit_(
                     recit.repartition,
                     ("parcs", tr("onglet_les_deux"),
                      lambda _tr, data, h: _carte_parcs(
                          trs, data, etat["faits"], corpus, h)),
                     ("tde", tr("onglet_tde"),
                      lambda _tr, data, h: parc_vue.carte_tde_seule(h)),
                     ("coso", tr("onglet_coso"),
                      lambda _tr, data, h: parc_vue.carte_coso_seule(h)))},
                {"id": "densite", "name": tr("vue_densite"),
                 "component": recit_(
                     recit.densite,
                     ("densite", tr("onglet_densite"), recit.carte_densite),
                     ("population", tr("onglet_population"),
                      lambda _tr, data, h:
                          demographie_vue.carte_population_seule(h)))},
                {"id": "deserts", "name": tr("vue_deserts"),
                 "component": recit_(
                     recit.deserts,
                     ("deserts", tr("onglet_deserts"), recit.carte_deserts),
                     ("rayons", tr("onglet_rayons"), recit.carte_rayons))},
            ]},

            # ── Acte 2 · Dans quel état ? ────────────────────────────────
            {"id": "etat", "name": tr("section_etat"),
             "reference": carte_de_section, "tab_items": [
                {"id": "angle_mort", "name": tr("vue_angle_mort"),
                 "is_default": True,
                 "component": recit_(recit.angle_mort, (
                     "couverture", tr("onglet_couverture"),
                     avec(trs, _carte_angle_mort)))},
                {"id": "entretien", "name": tr("vue_entretien"),
                 "component": recit_(recit.entretien, (
                     "entretien", tr("onglet_entretien"),
                     recit.carte_entretien))},
                {"id": "fragilite", "name": tr("vue_fragilite"),
                 "component": recit_(recit.fragilite, (
                     "debit", tr("onglet_debit"), recit.carte_debit))},
                {"id": "service", "name": tr("vue_service"),
                 "component": recit_(recit.service, (
                     "service", tr("onglet_service"), recit.carte_service))},
            ]},

            # ── Acte 3 · Pour combien d'habitants ? ──────────────────────
            {"id": "habitants", "name": tr("section_habitants"),
             "reference": carte_de_section, "tab_items": [
                {"id": "pression", "name": tr("vue_pression"),
                 "is_default": True, "component": {
                     "gauche": lambda: _etroit(
                         lambda: demographie_vue.render_pression(
                             avec_carte=False)),
                     "droite": cartes_de(
                         "pression",
                         ("population", tr("onglet_population"),
                          lambda _tr, data, h:
                              demographie_vue.carte_population_seule(h)),
                         ("densite", tr("onglet_densite"),
                          recit.carte_densite)),
                 }},
                {"id": "ventes", "name": tr("vue_ventes"),
                 "component": portee(demographie_vue.render_ventes)},
                {"id": "allocation", "name": tr("vue_allocation"),
                 "component": {
                     "gauche": portee(croisements_vue.render_allocation),
                     "droite": cartes_de(
                         "allocation",
                         ("investissement", tr("onglet_investissement"),
                          recit.carte_investissement)),
                 }},
                {"id": "rattrapage", "name": tr("vue_rattrapage"),
                 "component": recit_(recit.rattrapage, (
                     "deficit", tr("onglet_deficit"), recit.carte_deficit))},
            ]},

            # ── Acte 4 · Et quand l'eau monte ? ──────────────────────────
            {"id": "inondation", "name": tr("section_inondation"),
             "reference": carte_de_section, "tab_items": [
                {"id": "alea", "name": tr("vue_alea"), "is_default": True,
                 "component": {
                     "gauche": lambda: _etroit(
                         lambda: risque_vue.render_carto(avec_carte=False)),
                     "droite": cartes_de(
                         "alea",
                         ("officiel", tr("onglet_fri_officiel"),
                          avec(trs, _droite_risque, None, corpus)),
                         ("quantiles", tr("onglet_fri_quantiles"),
                          avec(trs, _carte_risque))),
                 }},
                {"id": "facteurs", "name": tr("vue_fri_facteurs"),
                 "component": portee(risque_vue.render_facteurs)},
                {"id": "ouvrages_risque", "name": tr("vue_ouvrages_risque"),
                 "component": {
                     "gauche": portee(croisements_vue.render_ouvrages_risque),
                     "droite": cartes_de(
                         "ouvrages",
                         ("bivariee", tr("onglet_bivariee"),
                          recit.carte_bivariee)),
                 }},
                {"id": "fri", "name": tr("vue_fri"),
                 "component": recit_(
                     recit.que_classe_le_fri,
                     ("officiel", tr("onglet_fri_officiel"),
                      avec(trs, _droite_risque, None, corpus)),
                     ("ampute", tr("onglet_fri_sans_pop"),
                      recit.carte_fri_ampute))},
            ]},

            # ── Acte 5 · Que faire ? ─────────────────────────────────────
            {"id": "agir", "name": tr("section_agir"),
             "reference": carte_de_section, "tab_items": [
                {"id": "priorites_reco", "name": tr("vue_priorites_reco"),
                 "is_default": True, "component": {
                     "gauche": portee(recommandations_vue.render_priorites),
                     "droite": cartes_de(
                         "priorites",
                         ("prioritaires", tr("onglet_prioritaires"),
                          avec(trs, _droite_priorites, None, corpus))),
                 }},
                {"id": "facture", "name": tr("vue_facture"),
                 "component": recit_(recit.facture, (
                     "facture", tr("onglet_facture"), recit.carte_facture))},
                {"id": "leviers", "name": tr("vue_leviers"),
                 "component": portee(recommandations_vue.render_leviers)},
            ]},

            # ── Acte 6 · Proposition ─────────────────────────────────────
            #
            # Le seul acte qui PROPOSE. Il vient après « Que faire » — les
            # leviers d'abord, leur chiffrage ensuite — et avant les preuves,
            # qui ferment le dossier : une proposition se lit pendant qu'on a
            # encore les constats en tête, pas après l'appareil critique.
            {"id": "proposition", "name": tr("section_proposition"),
             "reference": carte_de_section, "tab_items": [
                {"id": "ouvrages", "name": tr("vue_proposition_ouvrages"),
                 "is_default": True,
                 "component": recit_(
                     recit.proposition_ouvrages,
                     # Le PROGRAMME d'abord : c'est la proposition. La carte du
                     # besoin reste derrière, comme sa justification.
                     ("programme", tr("onglet_programme"),
                      recit.carte_programme_ouvrages),
                     ("besoin", tr("onglet_besoin"),
                      recit.carte_deficit_canton))},
                {"id": "inondations",
                 "name": tr("vue_proposition_inondations"),
                 "component": recit_(
                     recit.proposition_inondations,
                     ("programme", tr("onglet_programme"),
                      recit.carte_programme_inondations),
                     ("exposes", tr("onglet_exposes"), recit.carte_exposes))},
            ]},

            # ── Acte 7 · Ce qu'on sait, ce qu'on ignore ──────────────────
            {"id": "preuves", "name": tr("section_preuves"),
             "reference": carte_du_corpus, "tab_items": [
                {"id": "fichiers", "name": tr("vue_fichiers"),
                 "is_default": True,
                 "component": portee(donnees_vue.render_fichiers)},
                {"id": "recettes", "name": tr("vue_recettes"),
                 "component": portee(donnees_vue.render_recettes)},
                {"id": "perimetre", "name": tr("vue_perimetre"),
                 "component": portee(donnees_vue.render_perimetre)},
                {"id": "preuves", "name": tr("vue_preuves"),
                 "component": portee(annexes_vue.render_preuves)},
                {"id": "sources", "name": tr("vue_sources"),
                 "component": portee(annexes_vue.render_sources)},
                {"id": "methodologie", "name": tr("vue_methodologie"),
                 "component": portee(annexes_vue.render_methodologie)},
                {"id": "affichage", "name": tr("vue_affichage"),
                 "component": portee(annexes_vue.render_affichage)},
            ]},
        ],
    }



def render():
    tr = t("affiche")
    trs = t("synthese")
    # Le récit a son propre domaine i18n : ses textes sont éditoriaux — des
    # phrases, pas des étiquettes — et les mêler aux libellés du tableau de
    # bord aurait rendu illisible le fichier des deux.
    trr = t("recit")
    brut = datasets()

    # Le menu se peint AVANT les colonnes : son sous-titre ne peut pas suivre
    # un filtre qui n'a pas encore été lu. Il annonce donc le CORPUS, ce qui
    # est aussi ce qu'on attend d'un titre d'affiche — il nomme le sujet, il
    # ne commente pas la sélection en cours.
    corpus = analytics.synthese(brut["cantons"], brut["tde"], brut["coso"],
                                brut["ventes"])

    # La colonne gauche porte la barre de filtres, et elle se peint AVANT la
    # droite : le périmètre qu'elle retient est donc connu quand les cartes se
    # dessinent. Ce dictionnaire est le seul lien entre les deux — le socle
    # appelle les deux rendus sans rien se passer.
    etat = {}

    # La colonne droite ne défile pas : ce qu'on y pose doit tenir dans la
    # fenêtre, à la hauteur près. La zone est donc MESURÉE — le socle demande
    # sa hauteur au navigateur — et la carte s'y règle. Une hauteur en dur
    # remplissait un écran et un seul : celui sur lequel elle avait été
    # choisie.
    zone = hauteur_colonne_droite(ECHELLE)
    hauteur_carte = maps.hauteur_dans(zone, reserve=RAIL_ONGLETS)

    config = configuration(tr, trs, trr, brut, corpus, hauteur_carte)

    render_affiche(
        titre=tr("titre"),
        sous_titre=tr("sous_titre", {
            "cantons": corpus["cantons"],
            "ouvrages": corpus["tde_total"] + corpus["coso_total"],
        }),
        sur_titre=tr("sur_titre"),
        # Tout le chemin — entrées, onglets, composants, couleurs — tient dans
        # cet objet. Le socle n'en connaît ni les données ni les vues.
        config=config,
        echelle=ECHELLE,
        # Le pied porte la signature à GAUCHE et la provenance à DROITE :
        # « @Kokou PIPI | LinkedIn · Portfolio » d'un côté, le laboratoire et
        # le défi de l'autre. Les adresses viennent toutes de `utils.liens` —
        # aucune n'est écrite ici, sinon l'en-tête et le pied en tiendraient
        # deux copies qui divergeraient au premier changement de domaine.
        pied_gauche=(
            f'<span class="kg-foot-auteur">{tr("realise_par")}'
            f' {tr("auteur")}</span>'
            '<span class="kg-foot-sep">|</span>'
            + liens.lien("LinkedIn_url")
            + '<span class="kg-foot-point">·</span>'
            + liens.lien("Portfolio_url")
        ),
        pied_droit=(
            liens.lien("data_lab_url")
            + '<span class="kg-foot-sep">/</span>'
            + liens.lien("data_lab_challenge_url")
        ),
        # Les neuf réglages d'apparence. Le vert est celui du drapeau
        # togolais ; il désigne le commanditaire, jamais une donnée — aucune
        # série du tableau de bord ne l'emploie.
        couleur_sur_titre=VERT_TOGO,
        couleur_titre="#0F172A",
        couleur_sous_titre="#475569",
        couleur_vue_active=VERT_TOGO,
        couleur_vue_inactive="#FFFFFF",
        couleur_langue_active="#FFFFFF",
        couleur_langue_inactive="#F1F5F9",
        couleur_fond_menu=FOND,
        couleur_bordure_menu="#E2E8F0",
        marge_menu=True,
        # 0 aucune · 1 discrète · 2 la charte · 3 marquée.
        ombre_menu=3,
        # Deux rangées : l'identité et la langue, puis le rail des quatre
        # vues. Mesuré à l'écran — 14 de rembourrage haut, 62 de bloc de
        # titres, 12 d'écart, 36 de boutons, 20 de rembourrage bas.
        hauteur_menu=144,
        # La silhouette vient de la MÊME couche que les cartes de la page :
        # un logo dessiné à part pourrait montrer des frontières que les
        # données ne connaissent pas.
        # La silhouette mène au site de l'institution ; la marque, à celui du
        # laboratoire. Les deux ouvrent dans un onglet neuf : quitter l'affiche
        # pour un site externe ferait perdre le périmètre en cours.
        logo_url="https://www.republiquetogolaise.tg/",
        marque=datalab_marque(taille=30,
                              adresse=liens.adresse("data_lab_url")),
        logo=silhouette_svg(brut["cantons"], hauteur=68,
                            couleur=VERT_TOGO, libelle=tr("logo_alt")),
        # ── Les deux colonnes ────────────────────────────────────────────
        # L'écran est PARTAGÉ, et il doit se voir. Le filet court sur toute la
        # hauteur, du bord haut au pied, et la droite porte sa propre teinte :
        # à fond identique et sans trait, les deux moitiés coulaient l'une
        # dans l'autre et rien ne disait où finissait le propos, où commençait
        # la carte.
        separation_colonnes=True,
        couleur_separation=FILET,

        colonne_gauche_poids=62,
        colonne_gauche_fond=TEINTE_COLONNES,
        colonne_gauche_bordure=TEINTE_COLONNES,

        colonne_droite_poids=38,
        colonne_droite_fond=TEINTE_DROITE,
        colonne_droite_bordure=FILET,
    )
