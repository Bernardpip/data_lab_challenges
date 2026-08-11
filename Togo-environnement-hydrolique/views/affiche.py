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
    """Barre territoriale de l'affiche, et son effet sur les trois jeux.

    Le filtre se PEINT à gauche mais s'applique aux deux colonnes : une région
    choisie qui ne redessinerait pas les cartes ferait mentir la page.

    Les deux parcs ne sont restreints que si une modalité est réellement
    cochée. À pleine amplitude, les joindre au référentiel écarterait les
    ouvrages dont le canton n'y est pas rattaché — 27 microprojets COSO — et
    le total afficherait 191 au lieu de 218 sans que personne n'ait rien
    demandé. Un filtre au repos ne doit rien retirer.
    """

    selection = barres.zone_territoriale(data["cantons"])
    cantons = apply_filters(data["cantons"], selection)

    if not any(selection.values()):
        return {**data, "cantons": cantons}

    cles = set(cantons["cle_canton"])

    return {
        **data,
        "cantons": cantons,
        "tde": data["tde"][data["tde"]["cle_canton"].isin(cles)],
        "coso": data["coso"][data["coso"]["cle_canton"].isin(cles)],
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
        ("angle", tr("onglet_angle_mort")),
    ], cle="cartes_affiche", libelle=tr("onglets_cartes"), fond="#FFFFFF")

    if retenu == "risque":
        _carte_risque(tr, data, hauteur_carte)
    elif retenu == "parcs":
        _carte_parcs(tr, data, faits, corpus, hauteur_carte)
    else:
        _carte_angle_mort(tr, data, hauteur_carte)


def render():
    tr = t("affiche")
    trs = t("synthese")
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

    def gauche(vue):
        if vue != "diagnostic":
            _zone(tr("zone_gauche"), tr(f"vue_{vue}"), 760)
            return

        data = _filtrer(brut)
        faits = analytics.synthese(data["cantons"], data["tde"], data["coso"],
                                   data["ventes"])
        # Les faits sont RECALCULÉS sur le périmètre retenu : les servir tels
        # que le corpus entier les donne ferait dire « 330 cantons sans
        # ouvrage » à une page qui n'en montre plus que douze.
        etat["data"], etat["faits"] = data, faits

        _gauche_diagnostic(trs, data, faits, corpus)

    def droite(vue):
        if vue != "diagnostic":
            # La zone entière : la colonne droite démarre au ras du bord haut
            # et ne défile pas, donc son contenu la remplit ou laisse un vide.
            _zone(tr("zone_droite"), tr(f"carte_{vue}"), int(zone))
            return

        _droite_diagnostic(trs, etat["data"], etat["faits"], corpus,
                           hauteur_carte)

    # Le sous-titre est CALCULÉ : il suivra les données, comme tout le reste.
    render_affiche(
        titre=tr("titre"),
        sous_titre=tr("sous_titre", {
            "cantons": corpus["cantons"],
            "ouvrages": corpus["tde_total"] + corpus["coso_total"],
        }),
        sur_titre=tr("sur_titre"),
        vues=[{"key": cle, "label": tr(f"vue_{cle}")} for cle in VUES],
        rendu_gauche=gauche,
        rendu_droite=droite,
        echelle=ECHELLE,
        pied_gauche=tr("pied_source"),
        pied_droit=tr("pied_auteur"),

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
