"""Le récit — sept actes, et ce que l'inventaire ne racontait pas.

Le tableau de bord répondait par thème : le risque ici, le parc là, les
croisements dans un troisième tiroir. Un lecteur qui arrivait par le milieu
trouvait des chiffres justes sans jamais rencontrer la question à laquelle ils
répondent.

Ce module porte les vues qui manquaient à la narration, dans l'ordre où elles
se lisent :

    0  Le constat            ce que le corpus donne, et le paradoxe qu'il pose
    1  Où est l'eau          la répartition, la densité, et les déserts
    2  Dans quel état        l'objectif que les données ne permettent PAS
    3  Pour combien d'hab.   la pression, l'argent, le rattrapage
    4  Quand l'eau monte     l'aléa, les ouvrages exposés, ce que le FRI classe
    5  Que faire             les priorités, la facture, les leviers
    6  Ce qu'on sait         les preuves, les recettes, le périmètre

**Aucun calcul ici.** Les chiffres viennent de `analytics`, `econometrie` et
`accessibilite` ; ce module compose. La règle vaut pour tout le défi et se
paye ici : le rapport PowerPoint appelle les mêmes fonctions et sort les mêmes
nombres, sans qu'aucune vue n'ait à être relue.

Les peintres de COLONNE GAUCHE prennent `(tr, data, faits, corpus)`, ceux de
COLONNE DROITE `(tr, data, hauteur)`. La signature est la même que celle des
vues d'origine : la configuration du menu les mélange librement.
"""

# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import streamlit as st

from socle import ui, charts
from socle.charts import maps
from socle.design.tokens import (RISQUE_OFFICIEL, RISQUE_CONTOUR, SERIES,
                                 STATUS, ORDINAL)

from utils import analytics, accessibilite, econometrie

# Les quatre cases de la lecture croisée risque × équipement, dans l'ordre de
# la gravité. Deux axes ne se lisent pas sur une seule teinte : la première
# version en donnait quatre nuances de vert, et les 318 cantons de la deuxième
# case noyaient les 12 de la quatrième — vérifié à l'écran, le pays entier
# paraissait uniforme.
#
# Les teintes disent donc chacune un état plutôt qu'un rang : le GRIS pour
# l'ordinaire — risque modéré, pas d'ouvrage, le cas de 82 % du pays —, le BLEU
# pour ce qui est desservi, l'AMBRE pour un risque élevé mais couvert, le ROUGE
# pour la seule case qui appelle une décision.
BIVARIEE = ["#7fb3e0", "#e4e6e8", "#f0b357", "#c0392b"]

# Teintes des deux états d'un ouvrage, partout où la carte oppose un fait à son
# absence — plan de maintenance, remise à la communauté. Elles ne viennent pas
# de la palette de séries : ce sont des STATUTS, et deux statuts qui se
# ressembleraient se liraient comme deux catégories équivalentes.
FAIT = STATUS["good"]
MANQUE = STATUS["critical"]


# L'accroche en attente de rendu. Un seul élément à la fois — une vue n'a
# qu'un propos — mais une liste plutôt qu'un scalaire pour que deux appels
# accidentels se voient tous les deux au lieu de s'écraser en silence.
_ACCROCHES = []


def accroche(paragraphes, titre=None, sur_titre=None):
    """Le bloc éditorial de l'acte — DIFFÉRÉ jusqu'au pied de la colonne.

    Il se déclare en tête du peintre, là où ses chiffres viennent d'être
    calculés, et se peint en BAS de la colonne : la page ouvre sur les tuiles
    et les graphes, et la phrase qui les conclut se lit après eux, à sa place
    de conclusion.

    Pourquoi différer plutôt que déplacer l'appel en fin de fonction : deux
    vues sortent par un `return` anticipé quand leur mesure est vide, et
    l'accroche placée après ce retour n'aurait jamais été peinte — le seul cas
    où le lecteur en aurait le plus besoin. Ici, elle est mise de côté dès
    qu'elle est déclarée, et `poser_accroches()` la sort quoi qu'il arrive.
    """

    _ACCROCHES.append((paragraphes, titre, sur_titre))


def oublier_accroches():
    """Vide la file — à appeler AVANT de peindre une colonne.

    Le module survit d'un rendu à l'autre : une vue qui lèverait une exception
    entre la déclaration et le rendu laisserait sinon son accroche traîner, et
    la vue suivante afficherait le propos de la précédente.
    """

    _ACCROCHES.clear()


def poser_accroches():
    """Peint ce qui a été mis de côté — le dernier geste de la colonne."""

    while _ACCROCHES:
        paragraphes, titre, sur_titre = _ACCROCHES.pop(0)
        ui.accroche_editoriale(paragraphes, titre=titre, sur_titre=sur_titre)


def onglets_cartes(options, cle, libelle):
    """Le rang d'onglets de la colonne droite, quand une vue porte plusieurs cartes.

    `st.tabs` est inutilisable ici : ses panneaux inactifs sont en
    `display:none`, une carte Leaflet qui y monte reçoit une largeur nulle et
    reste blanche jusqu'au prochain rechargement. `ui.onglets` ne rend QUE le
    contenu actif — la carte se monte donc toujours dans un conteneur visible.
    """

    return ui.onglets(options, cle=cle, libelle=libelle, fond="#FFFFFF")


# ═══ Acte 0 · Le constat ═════════════════════════════════════════════════════

def paradoxe(tr, data, faits, corpus):
    """Le fait qui tient tout le dossier : le risque et l'équipement s'ignorent."""

    matrice = analytics.matrice_risque_equipement(
        data["cantons"], data["tde"], data["coso"])
    hautes = matrice[matrice["classe_officielle"].isin(analytics.CLASSES_HAUTES)]
    prioritaires = analytics.cantons_prioritaires(
        data["cantons"], data["tde"], data["coso"])

    exposes = int(hautes["cantons"].sum())
    equipes = int(hautes["equipes"].sum())

    accroche(
        [tr("paradoxe_texte_1", {
            "exposes": ui.fr_number(exposes),
            "population": ui.compact(float(hautes["population"].sum())),
            "equipes": ui.fr_number(equipes),
        }),
         tr("paradoxe_texte_2", {
             "sans": ui.fr_number(len(prioritaires)),
             "pop": ui.compact(float(prioritaires["population"].sum())),
         })],
        titre=tr("paradoxe_titre"), sur_titre=tr("acte_0"),
    )

    ui.stat_tiles([
        {"value": ui.fr_number(exposes), "label": tr("paradoxe_tuile_exposes"),
         "delta": tr("paradoxe_tuile_exposes_detail", {
             "part": ui.fr_number(100 * exposes / len(data["cantons"]), 0)
             if len(data["cantons"]) else "0"}),
         "good": False, "icon": "flag"},
        {"value": ui.fr_number(equipes), "label": tr("paradoxe_tuile_equipes"),
         "delta": tr("paradoxe_tuile_equipes_detail", {
             "part": ui.fr_number(100 * equipes / exposes, 0) if exposes else "0"}),
         "good": False, "icon": "map-pin"},
        {"value": ui.fr_number(len(prioritaires)),
         "label": tr("paradoxe_tuile_prioritaires"),
         "delta": tr("paradoxe_tuile_prioritaires_detail"), "good": False,
         "icon": "search"},
    ])

    with ui.card(tr("paradoxe_carte_titre"), tr("paradoxe_carte_sous_titre"),
                 "search"):
        lisible = matrice.assign(
            classe=matrice["classe_officielle"].map(
                lambda c: tr(f"classe_off_{c}")))

        charts.bar_stacked_h(
            lisible.rename(columns={"equipes": tr("col_equipes"),
                                    "sans_ouvrage": tr("col_sans_ouvrage")}),
            "classe", [tr("col_equipes"), tr("col_sans_ouvrage")],
            unit=tr("unite_cantons"))
        ui.note(tr("paradoxe_note", {
            "part_haute": ui.fr_number(
                100 * equipes / exposes, 0) if exposes else "0",
            "part_basse": ui.fr_number(
                matrice.loc[~matrice["classe_officielle"].isin(
                    analytics.CLASSES_HAUTES), "part_equipee"].mean(), 0),
        }))
        charts.table_twin(lisible[["classe", "cantons", "equipes",
                                   "sans_ouvrage"]].rename(columns={
            "classe": tr("col_classe"), "cantons": tr("col_cantons"),
            "equipes": tr("col_equipes"),
            "sans_ouvrage": tr("col_sans_ouvrage")}))


def carte_bivariee(tr, data, hauteur):
    """Les quatre cases du croisement, sur le territoire.

    Deux cartes côte à côte — le risque, puis l'équipement — laissaient au
    lecteur le soin de superposer mentalement 388 polygones. La lecture croisée
    est le SUJET : elle doit être dessinée, pas déduite.
    """

    equipes = set(data["tde"]["cle_canton"]) | set(data["coso"]["cle_canton"])
    cadre = analytics.classer_officiel(data["cantons"])
    haut = cadre["classe_officielle"].isin(analytics.CLASSES_HAUTES)
    equipe = cadre["cle_canton"].isin(equipes)

    cadre = cadre.assign(
        croisement=(haut.astype(int) * 2 + (~equipe).astype(int)),
        lecture=[tr(f"bivariee_{h}{e}") for h, e in
                 zip(haut.astype(int), (~equipe).astype(int))],
    )

    def dessin(h):
        return maps.choroplethe(
            cadre, valeur="croisement", cle="carte_recit_bivariee",
            champs=["canton", "prefecture", "lecture", "population"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_lecture"), tr("col_population")],
            height=h, rampe=BIVARIEE, couleur_contour=RISQUE_CONTOUR,
            # Quatre cases, quatre teintes : des bornes à mi-chemin des codes
            # entiers garantissent qu'aucune valeur ne tombe sur une coupure.
            bornes=[-0.5, 0.5, 1.5, 2.5, 3.5],
        )

    def pied(_):
        effectifs = cadre["croisement"].value_counts().reindex(
            range(4), fill_value=0)

        maps.legende_series([
            {"libelle": tr(f"bivariee_{code // 2}{code % 2}"),
             "couleur": BIVARIEE[code],
             "detail": ui.fr_number(int(effectifs[code]))}
            for code in range(4)
        ])
        ui.note(tr("bivariee_note", {
            "critiques": ui.fr_number(int(effectifs[3])),
            "population": ui.compact(float(
                cadre.loc[cadre["croisement"] == 3, "population"].sum())),
        }))

    maps.carte(tr("bivariee_carte_titre"), cle="recit_bivariee", dessin=dessin,
               legende=pied, sous_titre=tr("bivariee_carte_sous_titre"),
               hauteur=hauteur)


def limites(tr, data, faits, corpus):
    """Ce que le corpus ne dit pas — annoncé avant qu'on ait à le découvrir."""

    from utils import perimetre

    ecart = perimetre.ecart_publication()

    accroche(
        [tr("limites_texte_1", {"decrits": ecart["decrits"],
                                "publies": ecart["communs"]}),
         tr("limites_texte_2")],
        titre=tr("limites_titre"), sur_titre=tr("acte_0"),
    )

    ui.stat_tiles([
        {"value": f'{int(ecart["communs"])} / {int(ecart["decrits"])}',
         "label": tr("limites_tuile_champs"),
         "delta": tr("limites_tuile_champs_detail", {
             "part": ui.fr_number(ecart["part_publiee"], 0)}),
         "good": "attention", "icon": "table-2"},
        {"value": "0", "label": tr("limites_tuile_etat"),
         "delta": tr("limites_tuile_etat_detail"), "good": False,
         "icon": "search"},
        {"value": ui.fr_number(corpus["cantons_sans_ouvrage"]),
         "label": tr("limites_tuile_sans"),
         "delta": tr("limites_tuile_sans_detail"), "good": False,
         "icon": "map-pin"},
    ])

    with ui.card(tr("limites_carte_champs_titre"),
                 tr("limites_carte_champs_sous_titre"), "table-2"):
        charts.anneau(
            [tr("champs_absents"), tr("champs_publies")],
            [int(ecart["absents"]), int(ecart["communs"])],
            centre=f'{int(ecart["communs"])} / {int(ecart["decrits"])}',
            sous_centre=tr("champs_publies"), height=260,
        )
        ui.note(tr("limites_note_champs", {
            "absents": int(ecart["absents"]),
        }))

    with ui.card(tr("limites_carte_impossibles_titre"),
                 tr("limites_carte_impossibles_sous_titre"), "search"):
        for index in range(1, 4):
            ui.note(tr(f"limites_impossible_{index}"))


# ═══ Acte 1 · Où est l'eau ? ═════════════════════════════════════════════════

def repartition(tr, data, faits, corpus):
    """Deux inventaires, deux moitiés de pays, et rien au milieu."""

    tde, coso = data["tde"], data["coso"]

    accroche(
        [tr("ou_texte_1", {"tde": ui.fr_number(corpus["tde_total"]),
                           "coso": ui.fr_number(corpus["coso_total"]),
                           "part": ui.fr_number(corpus["tde_part_maritime"], 0)}),
         tr("ou_texte_2")],
        titre=tr("ou_titre"), sur_titre=tr("acte_1"),
    )

    ui.stat_tiles([
        {"value": ui.fr_number(len(tde)), "label": tr("ou_tuile_tde"),
         "delta": tr("ou_tuile_tde_detail",
                     {"regions": int(tde["region"].nunique())}),
         "good": None, "icon": "map-pin"},
        {"value": ui.fr_number(len(coso)), "label": tr("ou_tuile_coso"),
         "delta": tr("ou_tuile_coso_detail",
                     {"situes": int(coso["situe"].sum())}),
         "good": None, "icon": "building-2"},
        {"value": ui.fr_number(faits["cantons_sans_ouvrage"]),
         "label": tr("ou_tuile_sans"),
         "delta": tr("ou_tuile_sans_detail", {
             "part": ui.fr_number(faits["part_sans_ouvrage"], 0)}),
         "good": False, "icon": "search"},
    ])

    with ui.card(tr("ou_carte_regions_titre"), tr("ou_carte_regions_sous_titre"),
                 "building-2"):
        fusion = (
            analytics.tde_par_region(tde).rename(columns={"ouvrages": "TdE"})
            .merge(analytics.coso_par_region(coso)
                   .rename(columns={"ouvrages": "COSO"}),
                   on="region", how="outer")
            .fillna(0)
        )

        charts.bar_stacked_h(fusion, "region", ["TdE", "COSO"],
                             unit=tr("unite_ouvrages"))
        ui.note(tr("ou_note_regions", {
            "tde": ui.fr_number(corpus["tde_total"]),
            "part_maritime": ui.fr_number(corpus["tde_part_maritime"], 0),
            "coso": ui.fr_number(corpus["coso_total"]),
        }))
        charts.table_twin(fusion.rename(columns={"region": tr("col_region")}))

    with ui.card(tr("ou_carte_types_titre"), tr("ou_carte_types_sous_titre"),
                 "settings"):
        types = analytics.coso_par_type(coso)
        court = types.assign(
            type_court=types["type_ouvrage"].map(
                lambda libelle: tr(f"type_{analytics.cle_type_ouvrage(libelle)}")))

        charts.bar_h(court, "type_court", "ouvrages", unit=tr("unite_ouvrages"))
        ui.note(tr("ou_note_types", {"n": int(len(types))}))
        charts.table_twin(types.rename(columns={
            "type_ouvrage": tr("col_type"), "ouvrages": tr("col_ouvrages")}))

    with ui.card(tr("ou_carte_etat_titre"), tr("ou_carte_etat_sous_titre"),
                 "table-2"):
        # Deux décomptes dans une même carte : ils répondent à la même question
        # — « que sont ces ouvrages » — posée à chacun des deux inventaires.
        # Les séparer en deux cartes aurait suggéré deux sujets.
        nature = analytics.tde_par_nature(tde)
        avancement = analytics.coso_par_avancement(coso)

        charts.bar_h(nature, "nature", "ouvrages", unit=tr("unite_ouvrages"))
        ui.note(tr("ou_note_nature", {
            "nsp": ui.fr_number(int(
                nature.loc[nature["nature"].astype(str).str.contains(
                    "renseign", case=False, na=False), "ouvrages"].sum())),
            "total": ui.fr_number(len(tde)),
        }))
        charts.table_twin(nature.rename(columns={
            "nature": tr("col_nature"), "ouvrages": tr("col_ouvrages")}))

        charts.bar_h(avancement, "avancement", "ouvrages",
                     unit=tr("unite_ouvrages"))
        ui.note(tr("ou_note_avancement", {"n": int(len(avancement))}))
        charts.table_twin(avancement.rename(columns={
            "avancement": tr("col_avancement"), "ouvrages": tr("col_ouvrages")}))


def densite(tr, data, faits, corpus):
    """Un ouvrage pour combien d'habitants — et l'écart entre les régions."""

    couverture = econometrie.couverture_par_region(
        data["cantons"], data["tde"], data["coso"])
    regions = couverture["regions"]

    accroche(
        [tr("densite_texte_1", {
            "national": ui.fr_number(couverture["national"], 0),
            "pire": str(regions["region"].iloc[-1]),
            "pire_valeur": ui.compact(float(
                regions["habitants_par_ouvrage"].iloc[-1])),
            "mieux": str(regions["region"].iloc[0]),
            "mieux_valeur": ui.fr_number(
                float(regions["habitants_par_ouvrage"].iloc[0]), 0),
        }),
         tr("densite_texte_2", {
             "gini": ui.fr_number(couverture["gini_couverture"], 2)})],
        titre=tr("densite_titre"), sur_titre=tr("acte_1"),
    )

    with ui.card(tr("densite_carte_titre"), tr("densite_carte_sous_titre"),
                 "trending-up"):
        # Sucettes : le rapport va de 6 800 à 1 669 612 habitants par ouvrage,
        # et cinq barres pleines à cette dynamique ne laissent voir qu'une
        # seule marque.
        charts.sucette_h(regions.sort_values("habitants_par_ouvrage",
                                             ascending=False),
                         "region", "habitants_par_ouvrage",
                         unit=tr("unite_habitants"))
        ui.note(tr("densite_note", {
            "rapport": ui.fr_number(
                float(regions["habitants_par_ouvrage"].max()
                      / regions["habitants_par_ouvrage"].min()), 0),
        }))
        charts.table_twin(regions[[
            "region", "cantons", "population", "ouvrages",
            "habitants_par_ouvrage", "part_couverte"]].rename(columns={
                "region": tr("col_region"), "cantons": tr("col_cantons"),
                "population": tr("col_population"),
                "ouvrages": tr("col_ouvrages"),
                "habitants_par_ouvrage": tr("col_habitants_ouvrage"),
                "part_couverte": tr("col_part_couverte")}))

    with ui.card(tr("concentration_carte_titre"),
                 tr("concentration_carte_sous_titre"), "search"):
        serree = accessibilite.concentration(
            data["cantons"], data["tde"], data["coso"])

        if serree.empty:
            ui.note(tr("concentration_vide"))
            return

        lisible = serree.assign(
            inventaire=serree["inventaire"].map(
                lambda cle: tr(f"inventaire_{cle}")))

        charts.bar_h(lisible, "inventaire", "R", unit="", decimals=2)
        ensemble = serree[serree["inventaire"] == "ensemble"]
        ui.note(tr("concentration_note", {
            "r": ui.fr_number(float(ensemble["R"].iloc[0]), 2)
            if len(ensemble) else "—",
            "observe": ui.fr_number(float(ensemble["voisin_observe_km"].iloc[0]), 1)
            if len(ensemble) else "—",
            "attendu": ui.fr_number(float(ensemble["voisin_attendu_km"].iloc[0]), 1)
            if len(ensemble) else "—",
        }))
        charts.table_twin(lisible.rename(columns={
            "inventaire": tr("col_inventaire"), "ouvrages": tr("col_ouvrages"),
            "voisin_observe_km": tr("col_voisin_observe"),
            "voisin_attendu_km": tr("col_voisin_attendu")}))


def carte_densite(tr, data, hauteur):
    """Ouvrages pour 10 000 habitants, canton par canton."""

    couverture = analytics.couverture(data["cantons"], data["tde"], data["coso"])
    cadre = couverture.assign(
        pour_10000=10000 * couverture["ouvrages"]
        / couverture["population"].replace(0, np.nan)
    ).fillna({"pour_10000": 0})

    def dessin(h):
        return maps.choroplethe(
            cadre, valeur="pour_10000", cle="carte_recit_densite",
            champs=["canton", "prefecture", "ouvrages", "population"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_ouvrages"), tr("col_population")],
            height=h, nombre=5, methode="quantiles",
        )

    def pied(resultat):
        bornes, _ = resultat

        if bornes:
            maps.legende_paliers(bornes, libelle=tr("densite_legende"),
                                 decimales=2)

        ui.note(tr("densite_note_carte", {
            "sans": ui.fr_number(int((cadre["ouvrages"] == 0).sum())),
            "total": ui.fr_number(len(cadre)),
        }))

    maps.carte(tr("densite_carte_map_titre"), cle="recit_densite", dessin=dessin,
               legende=pied, sous_titre=tr("densite_carte_map_sous_titre"),
               hauteur=hauteur)


def deserts(tr, data, faits, corpus):
    """La distance au point d'eau — la mesure qui manquait au décompte."""

    mesure = accessibilite.deserts(data["cantons"], data["tde"], data["coso"])
    rayons = accessibilite.rayons_de_marche(
        data["cantons"], data["tde"], data["coso"])
    cadre = mesure["cadre"]

    accroche(
        [tr("deserts_texte_1", {
            "mediane": ui.fr_number(mesure["mediane_km"], 0),
            "max": ui.fr_number(float(cadre["distance_km"].max()), 0)
            if len(cadre) else "—",
            "loin": ui.fr_number(len(mesure["cantons"])),
            "seuil": ui.fr_number(mesure["seuil_km"], 0),
        }),
         tr("deserts_texte_2", {
             "part": ui.fr_number(
                 float(rayons.loc[rayons["rayon_km"] == 1, "part"].iloc[0]), 1)
             if len(rayons) else "—",
             "population": ui.compact(float(mesure["population"])),
         })],
        titre=tr("deserts_titre"), sur_titre=tr("acte_1"),
    )

    ui.stat_tiles([
        {"value": ui.fr_number(mesure["mediane_km"], 0), "unit": " km",
         "label": tr("deserts_tuile_mediane"),
         "delta": tr("deserts_tuile_mediane_detail"), "good": False,
         "icon": "map-pin"},
        {"value": ui.fr_number(mesure["part_population"], 0), "unit": " %",
         "label": tr("deserts_tuile_part"),
         "delta": tr("deserts_tuile_part_detail", {
             "seuil": ui.fr_number(mesure["seuil_km"], 0)}),
         "good": False, "icon": "trending-up"},
        {"value": ui.fr_number(
            float(rayons.loc[rayons["rayon_km"] == 1, "part"].iloc[0]), 1)
            if len(rayons) else "—", "unit": " %",
         "label": tr("deserts_tuile_rayon"),
         # Le chiffre est juste, l'hypothèse de densité uniforme ne l'est pas :
         # c'est une réserve de lecture, pas un échec.
         "delta": tr("deserts_tuile_rayon_detail"), "good": "attention",
         "icon": "search"},
    ])

    with ui.card(tr("deserts_carte_rayons_titre"),
                 tr("deserts_carte_rayons_sous_titre"), "trending-up"):
        lisible = rayons.assign(
            rayon=rayons["rayon_km"].map(
                lambda km: tr("deserts_rayon_libelle",
                              {"km": ui.fr_number(km, 1)})))

        charts.bar_h(lisible, "rayon", "part", unit=" %", trier=False)
        ui.note(tr("deserts_note_rayons"))
        charts.table_twin(rayons.rename(columns={
            "rayon_km": tr("col_rayon"), "population": tr("col_population"),
            "part": tr("col_part")}))

    with ui.card(tr("deserts_carte_liste_titre"),
                 tr("deserts_carte_liste_sous_titre"), "flag"):
        pires = mesure["cantons"].head(12)

        charts.sucette_h(pires, "canton", "distance_km", unit=" km")
        ui.note(tr("deserts_note_liste", {
            "n": ui.fr_number(len(mesure["cantons"])),
            "part": ui.fr_number(mesure["part_cantons"], 0),
        }))
        charts.table_twin(pires[["canton", "prefecture", "region",
                                 "distance_km", "population"]].rename(columns={
            "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
            "region": tr("col_region"), "distance_km": tr("col_distance"),
            "population": tr("col_population")}))


def carte_deserts(tr, data, hauteur):
    """La distance au point d'eau le plus proche, en kilomètres."""

    cadre = accessibilite.distance_au_point_deau(
        data["cantons"], data["tde"], data["coso"])
    # La géométrie ne voyage pas avec le résultat du calcul : on la rattache
    # par la CLÉ de canton, jamais par le nom — deux préfectures peuvent porter
    # un canton du même nom, et la jointure dupliquerait leurs polygones.
    situe = data["cantons"].merge(
        cadre[["cle_canton", "distance_km"]], on="cle_canton", how="inner")

    def dessin(h):
        return maps.choroplethe(
            situe, valeur="distance_km", cle="carte_recit_deserts",
            champs=["canton", "prefecture", "distance_km", "population"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_distance"), tr("col_population")],
            height=h, nombre=5, methode="quantiles",
        )

    def pied(resultat):
        bornes, _ = resultat

        if bornes:
            maps.legende_paliers(bornes, libelle=tr("deserts_legende"),
                                 unite=" km", decimales=0)

        ui.note(tr("deserts_note_carte", {
            "mediane": ui.fr_number(float(situe["distance_km"].median()), 0),
        }))

    maps.carte(tr("deserts_carte_map_titre"), cle="recit_deserts", dessin=dessin,
               legende=pied, sous_titre=tr("deserts_carte_map_sous_titre"),
               hauteur=hauteur)


def carte_rayons(tr, data, hauteur):
    """Les ouvrages et leur rayon de marche, sur le pays entier.

    Les disques ne sont pas décoratifs : leur AIRE est celle du rayon de 5 km,
    à l'échelle de la carte. Ce que le lecteur voit est donc littéralement la
    surface desservie — et le blanc qui reste, littéralement, ce qui ne l'est
    pas.
    """

    coso_situes = data["coso"][data["coso"]["situe"]]

    def dessin(h):
        maps.points_multi(
            [
                {"df": coso_situes, "libelle": tr("mini_coso"),
                 "couleur": SERIES[1], "rayon": 9,
                 "infobulle": lambda ligne: (
                     f'<b>{ligne["localite"]}</b><br>{ligne["canton"]}')},
                {"df": data["tde"], "libelle": tr("mini_tde"),
                 "couleur": SERIES[0], "rayon": 9,
                 "infobulle": lambda ligne: (
                     f'<b>{ligne["ouvrage"]}</b><br>{ligne["canton"]}')},
            ],
            cle="carte_recit_rayons", fond=data["cantons"], height=h,
        )

    def pied(_):
        rayons = accessibilite.rayons_de_marche(
            data["cantons"], data["tde"], data["coso"])

        maps.legende_series([
            {"libelle": tr("mini_tde"), "couleur": SERIES[0],
             "detail": ui.fr_number(len(data["tde"]))},
            {"libelle": tr("mini_coso"), "couleur": SERIES[1],
             "detail": ui.fr_number(len(coso_situes))},
        ])
        ui.note(tr("rayons_note_carte", {
            "un": ui.fr_number(
                float(rayons.loc[rayons["rayon_km"] == 1, "part"].iloc[0]), 1)
            if len(rayons) else "—",
            "cinq": ui.fr_number(
                float(rayons.loc[rayons["rayon_km"] == 5, "part"].iloc[0]), 0)
            if len(rayons) else "—",
        }))

    maps.carte(tr("rayons_carte_titre"), cle="recit_rayons", dessin=dessin,
               legende=pied, sous_titre=tr("rayons_carte_sous_titre"),
               hauteur=hauteur)


# ═══ Acte 2 · Dans quel état ? ═══════════════════════════════════════════════

def _avertissement(tr, cle_texte):
    """Le bandeau qui ouvre chaque vue de l'acte 2.

    Il est répété sur les quatre onglets, à dessein : un lecteur qui arrive par
    un lien direct sur « Fragilité » doit savoir, avant de lire un seul
    chiffre, que rien ici ne mesure une panne.
    """

    st.markdown(
        f'<div class="kg-card" style="padding:14px 18px;'
        f'border-left:3px solid {STATUS["warning"]};margin-bottom:12px;">'
        f'{ui.pill("warning", tr("etat_avertissement_titre"))}'
        f'<div style="font-size:14px;line-height:1.6;margin-top:8px;'
        f'color:var(--kg-color-text-secondary);">{tr(cle_texte)}</div></div>',
        unsafe_allow_html=True,
    )


def angle_mort(tr, data, faits, corpus):
    """L'objectif que le corpus ne permet pas de tenir, et pourquoi."""

    _avertissement(tr, "etat_avertissement_texte")

    tde = data["tde"]
    coso = data["coso"]

    accroche(
        [tr("angle_texte_1", {"colonnes": len(tde.columns)}),
         tr("angle_texte_2")],
        titre=tr("angle_titre"), sur_titre=tr("acte_2"),
    )

    ui.stat_tiles([
        {"value": "0", "label": tr("angle_tuile_etat"),
         "delta": tr("angle_tuile_etat_detail"), "good": False, "icon": "search"},
        {"value": ui.fr_number(int(coso["plan_maintenance"].sum())),
         "label": tr("angle_tuile_plan"),
         "delta": tr("angle_tuile_plan_detail", {"total": len(coso)}),
         "good": False, "icon": "settings"},
        {"value": ui.fr_number(int(coso["debit"].notna().sum())),
         "label": tr("angle_tuile_debit"),
         "delta": tr("angle_tuile_debit_detail", {"total": len(coso)}),
         "good": "attention", "icon": "table-2"},
    ])

    with ui.card(tr("angle_carte_titre"), tr("angle_carte_sous_titre"),
                 "table-2"):
        completude = analytics.completude_coso(coso)
        lisible = completude.assign(
            champ=completude["champ"].map(lambda c: tr(f"champ_{c}")))

        charts.bar_h(lisible, "champ", "part", unit=" %", decimals=0)
        ui.note(tr("angle_note", {
            "debit": ui.fr_number(
                float(completude.loc[completude["champ"] == "debit",
                                     "part"].iloc[0]), 0),
        }))
        charts.table_twin(lisible.rename(columns={
            "champ": tr("col_champ"), "renseignes": tr("col_renseignes"),
            "part": tr("col_part")}))

    with ui.card(tr("angle_carte_substituts_titre"),
                 tr("angle_carte_substituts_sous_titre"), "search"):
        for index in range(1, 4):
            ui.note(tr(f"angle_substitut_{index}"))


def entretien(tr, data, faits, corpus):
    """Le plan de maintenance — le seul entretien mesurable du corpus."""

    _avertissement(tr, "etat_avertissement_entretien")

    plans = analytics.plan_de_maintenance(data["coso"])

    if plans.empty:
        ui.note(tr("entretien_vide"))
        return

    total = int(plans["ouvrages"].sum())
    avec = int(plans["avec_plan"].sum())

    accroche(
        [tr("entretien_texte_1", {
            "avec": ui.fr_number(avec), "total": ui.fr_number(total),
            "part": ui.fr_number(100 * avec / total, 0) if total else "0"}),
         tr("entretien_texte_2", {
             "haut": str(plans["region"].iloc[0]),
             "haut_part": ui.fr_number(float(plans["part"].iloc[0]), 0),
             "bas": str(plans["region"].iloc[-1]),
             "bas_part": ui.fr_number(float(plans["part"].iloc[-1]), 0),
         })],
        titre=tr("entretien_titre"), sur_titre=tr("acte_2"),
    )

    # Le fonds d'entretien est la SECONDE trace d'intention du corpus, et la
    # plus concrète : un plan sans argent n'engage personne. Les deux tiennent
    # dans la même vue parce qu'ils répondent à la même question.
    fonds = int(data["coso"]["fonds_entretien"].notna().sum())

    ui.stat_tiles([
        {"value": ui.fr_number(avec), "label": tr("entretien_tuile_avec"),
         "delta": tr("entretien_tuile_avec_detail", {
             "part": ui.fr_number(100 * avec / total, 0) if total else "0"}),
         "good": True, "icon": "flag"},
        {"value": ui.fr_number(total - avec), "label": tr("entretien_tuile_sans"),
         "delta": tr("entretien_tuile_sans_detail"), "good": False,
         "icon": "settings"},
        {"value": ui.fr_number(fonds), "label": tr("entretien_tuile_fonds"),
         "delta": tr("entretien_tuile_fonds_detail", {
             "total": ui.fr_number(total)}),
         "good": False, "icon": "table-2"},
    ])

    with ui.card(tr("entretien_carte_titre"), tr("entretien_carte_sous_titre"),
                 "settings"):
        charts.bar_stacked_h(
            plans.rename(columns={"avec_plan": tr("col_avec_plan"),
                                  "sans_plan": tr("col_sans_plan")}),
            "region", [tr("col_avec_plan"), tr("col_sans_plan")],
            unit=tr("unite_ouvrages"))
        ui.note(tr("entretien_note", {
            "sans": ui.fr_number(total - avec),
            "part": ui.fr_number(100 * (total - avec) / total, 0) if total else "0",
        }))
        charts.table_twin(plans.rename(columns={
            "region": tr("col_region"), "ouvrages": tr("col_ouvrages"),
            "avec_plan": tr("col_avec_plan"), "sans_plan": tr("col_sans_plan"),
            "part": tr("col_part")}))


def _carte_binaire(tr, cadre, colonne, cle, titre, sous_titre, hauteur,
                   libelle_vrai, libelle_faux, note, fond):
    """Deux couches de points opposant un fait à son absence.

    Un seul peintre pour « avec / sans plan de maintenance » et « remis / en
    attente » : les deux cartes posent la même question — où est ce qui manque
    — et deux implémentations auraient fini par diverger sur un rayon ou une
    teinte.

    `note` est une FONCTION `(manquants_situés, manquants_au_total) -> texte` :
    seule cette fonction connaît les deux décomptes, et l'appelant ne peut donc
    pas écrire une note qui contredise la légende.
    """

    situes = cadre[cadre["situe"]]
    vrais = situes[situes[colonne].astype(bool)]
    faux = situes[~situes[colonne].astype(bool)]

    # La note compte ce que la carte MONTRE — les ouvrages situés — et non le
    # parc entier. Vérifié à l'écran : une note annonçant 108 ouvrages sous une
    # légende qui en dénombrait 37 laissait le lecteur chercher son erreur.
    note = note(len(faux), int((~cadre[colonne].astype(bool)).sum()))

    def infobulle(ligne):
        return f'<b>{ligne["localite"]}</b><br>{ligne["canton"]} · {ligne["region"]}'

    def dessin(h):
        maps.points_multi(
            [
                {"df": faux, "libelle": libelle_faux, "couleur": MANQUE,
                 "rayon": 5, "infobulle": infobulle},
                {"df": vrais, "libelle": libelle_vrai, "couleur": FAIT,
                 "rayon": 5, "infobulle": infobulle},
            ],
            cle=f"carte_{cle}", fond=fond, height=h,
        )

    def pied(_):
        maps.legende_series([
            {"libelle": libelle_vrai, "couleur": FAIT,
             "detail": ui.fr_number(len(vrais))},
            {"libelle": libelle_faux, "couleur": MANQUE,
             "detail": ui.fr_number(len(faux))},
        ])
        ui.note(note)

    maps.carte(titre, cle=cle, dessin=dessin, legende=pied,
               sous_titre=sous_titre, hauteur=hauteur)


def carte_entretien(tr, data, hauteur):
    """Où sont les ouvrages dont personne n'a prévu l'entretien."""

    _carte_binaire(
        tr, data["coso"], "plan_maintenance", "recit_entretien",
        tr("entretien_carte_map_titre"), tr("entretien_carte_map_sous_titre"),
        hauteur, tr("legende_avec_plan"), tr("legende_sans_plan"),
        lambda situes, total: tr("entretien_note_carte", {
            "sans": ui.fr_number(situes), "total": ui.fr_number(total)}),
        data["cantons"],
    )


def fragilite(tr, data, faits, corpus):
    """Le débit — qui tombera en panne, faute de savoir qui l'est."""

    _avertissement(tr, "etat_avertissement_fragilite")

    mesure = analytics.fragilite_debit(data["coso"])

    if not mesure["renseignes"]:
        ui.note(tr("fragilite_vide"))
        return

    accroche(
        [tr("fragilite_texte_1", {
            "renseignes": ui.fr_number(mesure["renseignes"]),
            "total": ui.fr_number(mesure["total"]),
            "median": ui.fr_number(mesure["median"], 1),
            "fragiles": ui.fr_number(mesure["fragiles"]),
            "seuil": ui.fr_number(mesure["seuil"], 0),
        }),
         tr("fragilite_texte_2", {
             "aberrants": ui.fr_number(
                 mesure["aberrants"] + mesure["profondeurs_aberrantes"]),
         })],
        titre=tr("fragilite_titre"), sur_titre=tr("acte_2"),
    )

    ui.stat_tiles([
        {"value": ui.fr_number(mesure["median"], 1), "unit": " m³/h",
         "label": tr("fragilite_tuile_median"),
         "delta": tr("fragilite_tuile_median_detail", {
             "n": ui.fr_number(mesure["renseignes"])}),
         "good": None, "icon": "trending-up"},
        {"value": ui.fr_number(mesure["fragiles"]),
         "label": tr("fragilite_tuile_fragiles"),
         "delta": tr("fragilite_tuile_fragiles_detail", {
             "seuil": ui.fr_number(mesure["seuil"], 0)}),
         "good": False, "icon": "flag"},
        {"value": ui.fr_number(
            100 * mesure["renseignes"] / mesure["total"], 0)
            if mesure["total"] else "0", "unit": " %",
         "label": tr("fragilite_tuile_couverture"),
         "delta": tr("fragilite_tuile_couverture_detail"), "good": "attention",
         "icon": "table-2"},
    ])

    with ui.card(tr("fragilite_carte_regions_titre"),
                 tr("fragilite_carte_regions_sous_titre"), "settings"):
        charts.bar_h(mesure["regions"], "region", "part_fragiles", unit=" %")
        ui.note(tr("fragilite_note_regions", {
            "region": str(mesure["regions"]["region"].iloc[0]),
            "part": ui.fr_number(
                float(mesure["regions"]["part_fragiles"].iloc[0]), 0),
            "n": int(mesure["regions"]["forages"].iloc[0]),
        }))
        charts.table_twin(mesure["regions"].rename(columns={
            "region": tr("col_region"), "forages": tr("col_forages"),
            "debit_median": tr("col_debit_median"),
            "fragiles": tr("col_fragiles"),
            "part_fragiles": tr("col_part_fragiles")}))

    with ui.card(tr("fragilite_carte_nuage_titre"),
                 tr("fragilite_carte_nuage_sous_titre"), "search"):
        relation = analytics.relation_profondeur_debit(data["coso"])
        technique = relation["cadre"]

        if relation["modele"] is None:
            ui.note(tr("fragilite_nuage_vide"))
            return

        charts.scatter_fit(
            technique["profondeur"], technique["debit"],
            labels=technique["localite"], modele=relation["modele"],
            x_titre=tr("axe_profondeur"), y_titre=tr("axe_debit"),
        )
        ui.note(tr("fragilite_note_nuage", {
            "n": relation["n"],
            "pente": ui.fr_number(relation["modele"]["pente"], 3),
            "r2": ui.fr_number(relation["r2"], 3),
        }))


def carte_debit(tr, data, hauteur):
    """Le débit des forages, en disques proportionnels."""

    mesure = analytics.fragilite_debit(data["coso"])
    cadre = data["coso"][data["coso"]["situe"]].dropna(subset=["debit"])
    cadre = cadre[cadre["debit"] <= analytics.DEBIT_MAXIMAL]

    def dessin(h):
        maps.disques(
            cadre, valeur="debit", cle="carte_recit_debit",
            # Pas d'ÉTIQUETTE : les forages mesurés sont groupés dans le nord,
            # et trente-huit labels s'y empilaient jusqu'à devenir un pâté.
            # L'identité passe par l'infobulle, la magnitude par l'aire.
            fond=data["cantons"],
            infobulle=lambda ligne: (
                f'<b>{ligne["localite"]}</b><br>'
                f'{ui.fr_number(ligne["debit"], 1)} m³/h<br>'
                f'{ligne["canton"]} · {ligne["region"]}'),
            height=h,
        )

    def pied(_):
        ui.note(tr("debit_note_carte", {
            "n": ui.fr_number(len(cadre)),
            "fragiles": ui.fr_number(mesure["fragiles"]),
            "seuil": ui.fr_number(mesure["seuil"], 0),
        }))

    maps.carte(tr("debit_carte_titre"), cle="recit_debit", dessin=dessin,
               legende=pied, sous_titre=tr("debit_carte_sous_titre"),
               hauteur=hauteur)


def service(tr, data, faits, corpus):
    """Entre la réception et la remise : le temps où l'ouvrage n'existe pour personne."""

    _avertissement(tr, "etat_avertissement_service")

    mesure = analytics.mise_en_service(data["coso"])

    accroche(
        [tr("service_texte_1", {
            "receptionnes": ui.fr_number(mesure["receptionnes"]),
            "remis": ui.fr_number(mesure["remis"]),
            "attente": ui.fr_number(mesure["en_attente"]),
        }),
         tr("service_texte_2", {
             "delai": ui.fr_number(mesure["delai_median"], 0),
             "mesures": ui.fr_number(mesure["mesures"]),
             "sans": ui.fr_number(mesure["sans_reception"]),
         })],
        titre=tr("service_titre"), sur_titre=tr("acte_2"),
    )

    ui.stat_tiles([
        {"value": ui.fr_number(mesure["en_attente"]),
         "label": tr("service_tuile_attente"),
         "delta": tr("service_tuile_attente_detail", {
             "receptionnes": ui.fr_number(mesure["receptionnes"])}),
         "good": False, "icon": "settings"},
        {"value": ui.fr_number(mesure["delai_median"], 0), "unit": " j",
         "label": tr("service_tuile_delai"),
         "delta": tr("service_tuile_delai_detail", {
             "mois": ui.fr_number(mesure["delai_median"] / 30.4, 0)}),
         "good": False, "icon": "trending-up"},
        {"value": ui.fr_number(mesure["sans_reception"]),
         "label": tr("service_tuile_sans"),
         "delta": tr("service_tuile_sans_detail"), "good": "attention",
         "icon": "table-2"},
    ])

    with ui.card(tr("service_carte_titre"), tr("service_carte_sous_titre"),
                 "settings"):
        charts.bar_stacked_h(
            mesure["regions"].rename(columns={
                "remis": tr("col_remis"), "en_attente": tr("col_en_attente")}),
            "region", [tr("col_remis"), tr("col_en_attente")],
            unit=tr("unite_ouvrages"))
        ui.note(tr("service_note", {
            "attente": ui.fr_number(mesure["en_attente"]),
            "delai": ui.fr_number(mesure["delai_median"], 0),
        }))
        charts.table_twin(mesure["regions"].rename(columns={
            "region": tr("col_region"), "ouvrages": tr("col_ouvrages"),
            "receptionnes": tr("col_receptionnes"), "remis": tr("col_remis"),
            "en_attente": tr("col_en_attente")}))


def carte_service(tr, data, hauteur):
    """Où attendent les ouvrages reçus mais jamais remis."""

    coso = data["coso"]
    remis = pd.to_datetime(coso["official_handover_date_to_community"],
                           errors="coerce").notna()
    cadre = coso.assign(remis=remis)

    _carte_binaire(
        tr, cadre, "remis", "recit_service",
        tr("service_carte_map_titre"), tr("service_carte_map_sous_titre"),
        hauteur, tr("legende_remis"), tr("legende_en_attente"),
        lambda situes, total: tr("service_note_carte", {
            "attente": ui.fr_number(situes), "total": ui.fr_number(total)}),
        data["cantons"],
    )


# ═══ Acte 3 · Pour combien d'habitants ? ═════════════════════════════════════

def rattrapage(tr, data, faits, corpus):
    """L'inégalité de dotation, convertie en ouvrages manquants."""

    deficit = analytics.deficit_ouvrages(
        data["cantons"], data["tde"], data["coso"])
    regions = deficit["regions"]

    accroche(
        [tr("rattrapage_texte_1", {
            "etalon": ui.fr_number(deficit["etalon"], 0),
            "manquants": ui.fr_number(deficit["manquants"]),
        }),
         tr("rattrapage_texte_2", {
             "region": str(regions["region"].iloc[0]),
             "n": ui.fr_number(int(regions["manquants"].iloc[0])),
         })],
        titre=tr("rattrapage_titre"), sur_titre=tr("acte_3"),
    )

    ui.stat_tiles([
        {"value": ui.fr_number(deficit["manquants"]),
         "label": tr("rattrapage_tuile_manquants"),
         "delta": tr("rattrapage_tuile_manquants_detail", {
             "etalon": ui.fr_number(deficit["etalon"], 0)}),
         "good": False, "icon": "flag"},
        {"value": ui.compact(deficit["etalon"]),
         "label": tr("rattrapage_tuile_etalon"),
         "delta": tr("rattrapage_tuile_etalon_detail"), "good": None,
         "icon": "trending-up"},
        {"value": ui.fr_number(int((regions["manquants"] > 0).sum())),
         "label": tr("rattrapage_tuile_regions"),
         "delta": tr("rattrapage_tuile_regions_detail",
                     {"total": len(regions)}),
         "good": False, "icon": "map-pin"},
    ])

    with ui.card(tr("rattrapage_carte_titre"), tr("rattrapage_carte_sous_titre"),
                 "building-2"):
        charts.bar_h(regions, "region", "manquants", unit=tr("unite_ouvrages"))
        ui.note(tr("rattrapage_note", {
            "manquants": ui.fr_number(deficit["manquants"]),
            "etalon": ui.fr_number(deficit["etalon"], 0),
        }))
        charts.table_twin(regions[[
            "region", "population", "ouvrages", "habitants_par_ouvrage",
            "ouvrages_requis", "manquants"]].rename(columns={
                "region": tr("col_region"), "population": tr("col_population"),
                "ouvrages": tr("col_ouvrages"),
                "habitants_par_ouvrage": tr("col_habitants_ouvrage"),
                "ouvrages_requis": tr("col_requis"),
                "manquants": tr("col_manquants")}))


def _carte_par_region(tr, data, colonne, cle, titre, sous_titre, hauteur,
                      valeurs, libelle_legende, note, decimales=0):
    """Une choroplèthe dont la valeur est portée par la RÉGION, non le canton.

    Le déficit et la facture se calculent par région : les peindre au canton
    ferait croire à une mesure locale, et les peindre sur une seule couleur par
    région dit exactement ce que le chiffre vaut — un agrégat.
    """

    cadre = data["cantons"].merge(valeurs[["region", colonne]], on="region",
                                  how="left")
    cadre[colonne] = cadre[colonne].fillna(0)

    def dessin(h):
        return maps.choroplethe(
            cadre, valeur=colonne, cle=f"carte_{cle}",
            champs=["region", "canton", colonne],
            libelles=[tr("col_region"), tr("col_canton"), libelle_legende],
            height=h, nombre=min(5, max(int(valeurs[colonne].nunique()), 1)),
            methode="lineaire",
        )

    def pied(resultat):
        bornes, _ = resultat

        if bornes:
            maps.legende_paliers(bornes, libelle=libelle_legende,
                                 decimales=decimales)

        ui.note(note)

    maps.carte(titre, cle=cle, dessin=dessin, legende=pied,
               sous_titre=sous_titre, hauteur=hauteur)


def carte_deficit(tr, data, hauteur):
    """Les ouvrages manquants, région par région."""

    deficit = analytics.deficit_ouvrages(
        data["cantons"], data["tde"], data["coso"])

    _carte_par_region(
        tr, data, "manquants", "recit_deficit",
        tr("rattrapage_carte_map_titre"), tr("rattrapage_carte_map_sous_titre"),
        hauteur, deficit["regions"], tr("col_manquants"),
        tr("rattrapage_note_carte", {
            "manquants": ui.fr_number(deficit["manquants"]),
            "etalon": ui.fr_number(deficit["etalon"], 0)}),
    )


def carte_investissement(tr, data, hauteur):
    """L'investissement COSO par habitant, canton par canton.

    Par HABITANT et non en montant : un canton deux fois plus peuplé qui reçoit
    deux fois plus n'a rien reçu de particulier, et une carte des montants
    bruts n'aurait dessiné que la démographie.
    """

    ecart = econometrie.contrefactuel_demographique(data["cantons"],
                                                    data["coso"])
    cadre = ecart["cadre"]

    if cadre.empty:
        maps.carte(tr("investissement_carte_titre"), cle="recit_investissement",
                   dessin=lambda h: ([], "vide"),
                   legende=lambda _: ui.note(tr("investissement_vide")),
                   sous_titre=tr("investissement_carte_sous_titre"),
                   hauteur=hauteur)
        return

    situe = data["cantons"].merge(
        cadre[["canton", "par_habitant", "investi", "ecart"]],
        on="canton", how="inner")

    def dessin(h):
        return maps.choroplethe(
            situe, valeur="par_habitant", cle="carte_recit_investissement",
            champs=["canton", "prefecture", "par_habitant", "population"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_par_habitant"), tr("col_population")],
            height=h, nombre=5, methode="quantiles",
        )

    def pied(resultat):
        bornes, _ = resultat

        if bornes:
            maps.legende_paliers(bornes, libelle=tr("investissement_legende"),
                                 decimales=0)

        ui.note(tr("investissement_note_carte", {
            "n": ui.fr_number(len(situe)),
            "gini": ui.fr_number(ecart["gini"], 2),
            "rapport": ui.fr_number(ecart["rapport_interdecile"], 1),
        }))

    maps.carte(tr("investissement_carte_titre"), cle="recit_investissement",
               dessin=dessin, legende=pied,
               sous_titre=tr("investissement_carte_sous_titre"),
               hauteur=hauteur)


# ═══ Acte 6 · Proposition ════════════════════════════════════════════════════
#
# Les cinq actes précédents décrivent. Celui-ci PROPOSE, et c'est un régime
# différent : il faut poser un objectif de service que les données ne portent
# pas. La règle tenue partout ici — l'hypothèse est écrite en clair, chiffrée à
# l'écran, et le lecteur voit la facture bouger avec elle. Un seul chiffre
# aurait fait passer un choix politique pour un résultat de calcul.


def _scenarios_lisibles(tr, scenarios):
    """Les seuils de desserte, en libellés — « 1 ouvrage / 1 000 habitants »."""

    return scenarios.assign(
        seuil=scenarios["norme"].map(
            lambda n: tr("proposition_norme", {"n": ui.fr_number(n)})))


# Le PROGRAMME que l'affiche propose, et ses trois paramètres. Ils sont ici,
# en clair, parce qu'ils sont contestables : un lecteur qui juge le seuil trop
# modeste ou l'horizon trop long doit voir où le changer.
#
# 1 ouvrage pour 5 000 habitants : le plus bas des quatre seuils du tableau, et
# le seul dont la facture — 27,6 Md sur cinq ans, soit 5,5 Md par an — reste du
# même ordre que ce qu'un programme sectoriel engage réellement. Viser le seuil
# villageois donnerait 450 Md, c'est-à-dire un document que personne n'ouvre.
NORME_PROGRAMME = 5000
HORIZON_OUVRAGES = 5
HORIZON_INONDATIONS = 3
PREMIERE_ANNEE = 2027


def annees_du_programme():
    """Toutes les années que les deux programmes peuvent porter.

    Sert à ÉTENDRE l'amplitude du curseur d'années de la barre de filtres : il
    est bâti sur les achèvements du COSO, qui s'arrêtent en 2026, et ne pouvait
    donc désigner aucune des années que la proposition affiche.
    """

    fin = PREMIERE_ANNEE + max(HORIZON_OUVRAGES, HORIZON_INONDATIONS) - 1

    return tuple(range(PREMIERE_ANNEE, fin + 1))


def _annees_retenues():
    """L'intervalle du curseur d'années, lu dans la session.

    Même mécanique que le périmètre territorial : la barre de filtres se peint
    en tête de colonne, ses clés sont donc déjà posées quand les blocs qui
    suivent les lisent. Rien ne transite d'un composant à l'autre.
    """

    retenu = st.session_state.get("filtre_annee")

    if not retenu:
        return None

    return int(retenu[0]), int(retenu[-1])


def _restreindre(programme):
    """Ne garde du programme que les chantiers des années retenues.

    Le calendrier, la carte et la liste se recalculent alors sur la même
    tranche : un utilisateur qui ne veut voir que 2027 doit obtenir un
    programme de 2027, pas la totalité avec une année surlignée.

    Les TOTAUX suivent la restriction. C'est délibéré : le montant affiché doit
    être celui des chantiers montrés, sinon la page annonce une facture qui ne
    correspond à rien de visible.
    """

    annees = _annees_retenues()
    cadre = programme.get("cadre")

    if annees is None or cadre is None or cadre.empty:
        return programme

    debut, fin = annees
    retenu = cadre[cadre["annee"].between(debut, fin)]

    if len(retenu) == len(cadre):
        return programme

    colonne = "manquants" if "manquants" in retenu.columns else "montant"

    return {
        **programme,
        "cadre": retenu,
        "annees": analytics._par_annee(retenu, colonne) if len(retenu)
        else retenu.head(0),
        "total": float(retenu["montant"].sum()),
        "ouvrages": int(retenu.get("manquants", pd.Series(dtype=int)).sum()),
        "cantons": int(len(retenu)),
    }


def _entretien(tr, programme, coso, cle_note):
    """La prévision d'ENTRETIEN du parc que le programme livre.

    Elle manquait, et son absence répétait exactement ce que l'acte 2 reproche
    au corpus : 173 microprojets sur 218 n'ont aucun plan de maintenance
    déclaré. Une proposition qui budgète la construction sans l'entretien
    construit des ouvrages qui tomberont.
    """

    observe = analytics.taux_entretien_observe(coso)
    courbe = analytics.entretien_previsionnel(programme, observe["part_mediane"])
    scenarios = analytics.entretien_scenarios(programme,
                                              observe=observe["part_mediane"])

    if courbe.empty:
        return

    with ui.card(tr("entretien_previsionnel_titre"),
                 tr("entretien_previsionnel_sous_titre"), "settings"):
        charts.column_series(
            courbe["annee"].astype(int).tolist(),
            (courbe["entretien"] / 1e6).tolist(),
            unit=tr("unite_millions"), height=240, decimals=0,
        )
        ui.note(tr(cle_note, {
            "provision": ui.compact(observe["provision_mediane"]),
            "part": ui.fr_number(100 * observe["part_mediane"], 2),
            "n": ui.fr_number(observe["ouvrages"]),
            "total": ui.fr_number(observe["total"]),
            "plateau": ui.compact(float(courbe["entretien"].max())),
        }))

        lisible = scenarios.assign(
            libelle=scenarios["taux"].map(
                lambda taux: tr("entretien_taux",
                                {"taux": ui.fr_number(100 * taux, 2)})))

        charts.bar_h(lisible.assign(milliards=lisible["cumul"] / 1e9),
                     "libelle", "milliards", unit=tr("unite_milliards"),
                     trier=False, decimals=2)
        ui.note(tr("entretien_previsionnel_note_scenarios", {
            "bas": ui.fr_number(float(scenarios["part_investissement"].min()), 0),
            "haut": ui.fr_number(float(scenarios["part_investissement"].max()), 0),
        }))
        charts.table_twin(lisible[["libelle", "annuel_plateau", "cumul",
                                   "part_investissement"]].rename(columns={
            "libelle": tr("col_taux"),
            "annuel_plateau": tr("col_entretien_annuel"),
            "cumul": tr("col_entretien_cumul"),
            "part_investissement": tr("col_part_investissement")}))


def _calendrier(tr, programme, cle_note, parametres=None):
    """Le calendrier du programme — dépense par année, et cumul.

    Colonnes verticales et non barres horizontales : l'axe est le TEMPS, il a
    un sens de lecture, et le coucher obligerait à le relire de bas en haut.
    """

    annees = programme["annees"]

    if annees.empty:
        return

    with ui.card(tr("programme_calendrier_titre"),
                 tr("programme_calendrier_sous_titre", {
                     "debut": programme["debut"],
                     "fin": programme["debut"] + programme["horizon"] - 1}),
                 "trending-up"):
        charts.column_series(
            annees["annee"].astype(int).tolist(),
            (annees["montant"] / 1e9).tolist(),
            unit=tr("unite_milliards"), height=240, decimals=1,
        )
        ui.note(tr(cle_note, {**(parametres or {}),
                              "annuel": ui.compact(
                                  float(annees["montant"].mean())),
                              "total": ui.compact(programme["total"]),
                              "debut": programme["debut"],
                              "fin": programme["debut"]
                              + programme["horizon"] - 1}))
        charts.table_twin(annees[["annee", "cantons", "ouvrages",
                                  "montant", "cumul"]].rename(columns={
            "annee": tr("col_annee"), "cantons": tr("col_cantons"),
            "ouvrages": tr("col_ouvrages"), "montant": tr("col_montant"),
            "cumul": tr("col_cumul")}))


def _chantiers(tr, programme, colonnes=None):
    """La liste des chantiers — canton, ouvrages, montant, année."""

    cadre = programme["cadre"]

    if cadre.empty:
        return

    with ui.card(tr("programme_chantiers_titre"),
                 tr("programme_chantiers_sous_titre"), "flag"):
        lisible = cadre.assign(
            urgence=cadre["urgence"].map(lambda cle: tr(f"urgence_{cle}")))

        charts.table_twin(
            lisible[colonnes or ["canton", "prefecture", "region", "urgence",
                                 "manquants", "montant", "annee"]].rename(
                columns={
                    "canton": tr("col_canton"),
                    "prefecture": tr("col_prefecture"),
                    "region": tr("col_region"), "urgence": tr("col_urgence"),
                    "manquants": tr("col_ouvrages"),
                    "montant": tr("col_montant"), "annee": tr("col_annee")}),
            label=tr("programme_chantiers_table"))
        ui.note(tr("programme_chantiers_note", {
            "chantiers": ui.fr_number(len(cadre)),
            "premiere": ui.fr_number(int(
                (cadre["annee"] == cadre["annee"].min()).sum())),
            "debut": programme["debut"],
        }))


def _carte_programme(tr, programme, cle, titre, sous_titre, hauteur, fond,
                     note, detail):
    """Les chantiers du programme, situés et datés.

    Une couche par ANNÉE, du plus foncé au plus clair : la couleur porte le
    calendrier, ce qu'aucune choroplèthe de besoin ne pouvait dire. Le montant
    et le nombre d'ouvrages vivent dans l'infobulle — les écrire sur la carte
    aurait donné trois cents étiquettes empilées.

    Le point est le point REPRÉSENTATIF du canton, jamais un site réel : le
    corpus ne porte ni habitat, ni nappe, ni foncier. Il dit DANS QUEL CANTON
    construire, et la vue le dit aussi, en toutes lettres.
    """

    cadre = programme["cadre"]

    if cadre.empty:
        return

    annees = sorted(cadre["annee"].unique())

    # Les teintes sont ÉTALÉES sur toute la rampe plutôt que prises dans
    # l'ordre : à trois années, les trois premières teintes de l'ordinal se
    # ressemblaient trop pour qu'on distingue 2027 de 2028 sur la carte.
    # Rampe inversée — la plus foncée à la première année : l'urgence se lit
    # dans l'intensité, et c'est elle qu'on veut voir en premier.
    rampe = list(reversed(ORDINAL))
    pas = (len(rampe) - 1) / max(len(annees) - 1, 1)
    teintes = [rampe[min(int(round(index * pas)), len(rampe) - 1)]
               for index in range(len(annees))]

    def dessin(h):
        maps.points_multi(
            [
                {"df": cadre[cadre["annee"] == annee],
                 "libelle": str(int(annee)),
                 # Les couches sont peintes dans l'ordre reçu : les dernières
                 # années d'abord, pour que les premières — les urgentes —
                 # restent au-dessus là où deux chantiers se recouvrent.
                 "couleur": teintes[index],
                 "rayon": 6,
                 "infobulle": (lambda ligne: detail(ligne))}
                for index, annee in reversed(list(enumerate(annees)))
            ],
            cle=f"carte_{cle}", fond=fond, height=h,
        )

    def pied(_):
        maps.legende_series([
            {"libelle": str(int(annee)),
             "couleur": teintes[index],
             "detail": ui.fr_number(int((cadre["annee"] == annee).sum()))}
            for index, annee in enumerate(annees)
        ], libelle=tr("programme_legende"))
        ui.note(note)

    maps.carte(titre, cle=cle, dessin=dessin, legende=pied,
               sous_titre=sous_titre, hauteur=hauteur)


def proposition_ouvrages(tr, data, faits, corpus):
    """Ce qu'il manque en forages et en châteaux, et ce que ça coûte."""

    etalon = analytics.deficit_ouvrages(
        data["cantons"], data["tde"], data["coso"])["etalon"]
    normes = (*analytics.NORMES_DESSERTE, int(round(etalon)))

    besoin = analytics.besoin_par_norme(
        data["cantons"], data["tde"], data["coso"], normes=normes)
    nature = analytics.parc_par_nature(data["tde"])
    scenarios = besoin["scenarios"]

    # Le scénario du bourg — un forage photovoltaïque pour mille habitants —
    # sert de référence dans le texte : c'est l'objet que le COSO construit
    # réellement, au prix qu'il a réellement payé.
    reference = scenarios[scenarios["norme"] == 1000]

    accroche(
        [tr("proposition_ouvrages_texte_1", {
            "existants": ui.fr_number(besoin["existants"]),
            "population": ui.compact(besoin["population"]),
            "chateaux": ui.fr_number(nature["chateaux"]),
        }),
         tr("proposition_ouvrages_texte_2", {
             "manquants": ui.fr_number(int(reference["manquants"].iloc[0]))
             if len(reference) else "—",
             "cout": ui.compact(float(reference["cout"].iloc[0]))
             if len(reference) else "—",
             "unitaire": ui.compact(besoin["unitaire"]),
         }),
         tr("proposition_ouvrages_texte_3")],
        titre=tr("proposition_ouvrages_titre"), sur_titre=tr("acte_6"),
    )

    ui.stat_tiles([
        {"value": ui.fr_number(int(reference["manquants"].iloc[0]))
            if len(reference) else "—",
         "label": tr("proposition_tuile_manquants"),
         "delta": tr("proposition_tuile_manquants_detail"), "good": False,
         "icon": "building-2"},
        {"value": ui.compact(float(reference["cout"].iloc[0]))
            if len(reference) else "—", "unit": " F",
         "label": tr("proposition_tuile_cout"),
         "delta": tr("proposition_tuile_cout_detail", {
             "unitaire": ui.compact(besoin["unitaire"])}),
         # Le prix unitaire est constaté, le SEUIL de service est posé : la
         # facture dépend d'une hypothèse, et la tuile doit le dire.
         "good": "attention", "icon": "table-2"},
        {"value": ui.fr_number(nature["chateaux"]),
         "label": tr("proposition_tuile_chateaux"),
         "delta": tr("proposition_tuile_chateaux_detail", {
             "forages": ui.fr_number(nature["forages"])}),
         "good": False, "icon": "flag"},
    ])

    with ui.card(tr("proposition_carte_scenarios_titre"),
                 tr("proposition_carte_scenarios_sous_titre"), "table-2"):
        lisible = _scenarios_lisibles(tr, scenarios)

        # Le graphe porte les MILLIARDS, non les francs : à 450 090 690 777,
        # l'étiquette débordait de la barre et se faisait rogner. La table
        # jumelle garde le franc près, pour qui veut vérifier.
        # `trier=False` : les seuils ont un ORDRE propre — du plus ambitieux au
        # plus modeste — et les ranger par facture le mélangerait.
        charts.bar_h(lisible.assign(milliards=lisible["cout"] / 1e9),
                     "seuil", "milliards", unit=tr("unite_milliards"),
                     trier=False, decimals=1)
        ui.note(tr("proposition_note_scenarios", {
            "haut": ui.compact(float(scenarios["cout"].max())),
            "bas": ui.compact(float(scenarios["cout"].min())),
            "etalon": ui.fr_number(int(scenarios["norme"].max())),
        }))
        charts.table_twin(lisible[["seuil", "requis", "existants",
                                   "manquants", "cout"]].rename(columns={
            "seuil": tr("col_seuil"), "requis": tr("col_requis"),
            "existants": tr("col_existants"),
            "manquants": tr("col_manquants"), "cout": tr("col_cout")}))

    programme = _restreindre(analytics.programme_ouvrages(
        data["cantons"], data["tde"], data["coso"],
        norme=NORME_PROGRAMME, horizon=HORIZON_OUVRAGES,
        debut=PREMIERE_ANNEE))

    _calendrier(tr, programme, "programme_ouvrages_note", {
        "ouvrages": ui.fr_number(programme["ouvrages"]),
        "cantons": ui.fr_number(len(programme["cadre"])),
        "norme": ui.fr_number(programme["norme"]),
    })
    _entretien(tr, programme, data["coso"], "entretien_ouvrages_note")
    _chantiers(tr, programme)

    with ui.card(tr("proposition_carte_nature_titre"),
                 tr("proposition_carte_nature_sous_titre"), "building-2"):
        charts.bar_h(nature["detail"], "nature", "ouvrages",
                     unit=tr("unite_ouvrages"))
        ui.note(tr("proposition_note_nature", {
            "chateaux": ui.fr_number(nature["chateaux"]),
            "total": ui.fr_number(nature["total"]),
        }))
        charts.table_twin(nature["detail"].rename(columns={
            "nature": tr("col_nature"), "ouvrages": tr("col_ouvrages")}))


def carte_programme_ouvrages(tr, data, hauteur):
    """Les chantiers d'ouvrages, situés dans leur canton et datés."""

    programme = _restreindre(analytics.programme_ouvrages(
        data["cantons"], data["tde"], data["coso"],
        norme=NORME_PROGRAMME, horizon=HORIZON_OUVRAGES,
        debut=PREMIERE_ANNEE))

    _carte_programme(
        tr, programme, "recit_prog_ouvrages",
        tr("programme_ouvrages_map_titre", {
            "debut": programme["debut"],
            "fin": programme["debut"] + programme["horizon"] - 1}),
        tr("programme_ouvrages_map_sous_titre", {
            "debut": programme["debut"],
            "fin": programme["debut"] + programme["horizon"] - 1}),
        hauteur, data["cantons"],
        tr("programme_ouvrages_note_carte", {
            "chantiers": ui.fr_number(len(programme["cadre"])),
            "ouvrages": ui.fr_number(programme["ouvrages"]),
            "total": ui.compact(programme["total"]),
        }),
        lambda ligne: (
            f'<b>{ligne["canton"]}</b> · {ligne["prefecture"]}<br>'
            f'{ui.fr_number(int(ligne["manquants"]))} '
            f'{tr("unite_ouvrages")}<br>'
            f'{ui.compact(float(ligne["montant"]))} F CFA<br>'
            f'{tr("programme_infobulle_annee")} <b>{int(ligne["annee"])}</b>'),
    )


def carte_programme_inondations(tr, data, hauteur):
    """Les aménagements de gestion des eaux, situés et datés."""

    programme = _restreindre(analytics.programme_inondations(
        data["cantons"], data["tde"], data["coso"],
        cout_unitaire=COUT_RETENU, horizon=HORIZON_INONDATIONS,
        debut=PREMIERE_ANNEE))

    _carte_programme(
        tr, programme, "recit_prog_inondations",
        tr("programme_inondations_map_titre", {
            "debut": programme["debut"],
            "fin": programme["debut"] + programme["horizon"] - 1}),
        tr("programme_inondations_map_sous_titre", {
            "debut": programme["debut"],
            "fin": programme["debut"] + programme["horizon"] - 1}),
        hauteur, data["cantons"],
        tr("programme_inondations_note_carte", {
            "cantons": ui.fr_number(programme["cantons"]),
            "unitaire": ui.compact(programme["unitaire"]),
            "total": ui.compact(programme["total"]),
        }),
        lambda ligne: (
            f'<b>{ligne["canton"]}</b> · {ligne["prefecture"]}<br>'
            f'{tr("col_risque")} : {ui.fr_number(ligne["risque_pts"], 1)}<br>'
            f'{ui.compact(float(ligne["montant"]))} F CFA<br>'
            f'{tr("programme_infobulle_annee")} <b>{int(ligne["annee"])}</b>'),
    )


def carte_deficit_canton(tr, data, hauteur, norme=1000):
    """Les ouvrages manquants canton par canton, au seuil du bourg."""

    cadre = analytics.deficit_par_canton(
        data["cantons"], data["tde"], data["coso"], norme=norme)

    def dessin(h):
        return maps.choroplethe(
            cadre, valeur="manquants", cle="carte_recit_besoin",
            champs=["canton", "prefecture", "population", "manquants"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_population"), tr("col_manquants")],
            height=h, nombre=5, methode="quantiles",
        )

    def pied(resultat):
        bornes, _ = resultat

        if bornes:
            maps.legende_paliers(bornes, libelle=tr("col_manquants"),
                                 decimales=0)

        ui.note(tr("proposition_note_carte", {
            "total": ui.fr_number(int(cadre["manquants"].sum())),
            "norme": ui.fr_number(norme),
            "pire": str(cadre.loc[cadre["manquants"].idxmax(), "canton"]),
            "max": ui.fr_number(int(cadre["manquants"].max())),
        }))

    maps.carte(tr("proposition_carte_map_titre"), cle="recit_besoin",
               dessin=dessin, legende=pied,
               sous_titre=tr("proposition_carte_map_sous_titre",
                             {"n": ui.fr_number(norme)}),
               hauteur=hauteur)


# Hypothèses de coût d'un aménagement de gestion des eaux pluviales, en francs
# CFA par canton. Elles ne viennent PAS du corpus — aucun de ses fichiers ne
# porte le prix d'un tel ouvrage — et couvrent volontairement un ordre de
# grandeur de 1 à 10, du curage de caniveaux au bassin de rétention.
COUTS_INONDATION = (50e6, 100e6, 250e6, 500e6)

# Celle des quatre qui sert à DATER le programme. La médiane des hypothèses,
# et non la plus basse : un calendrier bâti sur l'hypothèse la plus favorable
# se démentirait dès le premier chantier. Elle reste une hypothèse, et le
# tableau des quatre reste affiché au-dessus pour qu'on puisse en changer.
COUT_RETENU = 250e6


def proposition_inondations(tr, data, faits, corpus):
    """Ce qu'il manque pour gérer l'eau qui monte — et le prix qu'on ignore."""

    facture = analytics.facture_inondation(data["cantons"], COUTS_INONDATION)
    prioritaires = analytics.cantons_prioritaires(
        data["cantons"], data["tde"], data["coso"])

    _avertissement(tr, "proposition_inondations_avertissement")

    accroche(
        [tr("proposition_inondations_texte_1", {
            "cantons": ui.fr_number(facture["cantons"]),
            "population": ui.compact(facture["population"]),
            "sans": ui.fr_number(len(prioritaires)),
        }),
         tr("proposition_inondations_texte_2"),
         tr("proposition_inondations_texte_3", {
             "bas": ui.compact(float(facture["scenarios"]["total"].min())),
             "haut": ui.compact(float(facture["scenarios"]["total"].max())),
         })],
        titre=tr("proposition_inondations_titre"), sur_titre=tr("acte_6"),
    )

    ui.stat_tiles([
        {"value": ui.fr_number(facture["cantons"]),
         "label": tr("proposition_inondations_tuile_cantons"),
         "delta": tr("proposition_inondations_tuile_cantons_detail"),
         "good": False, "icon": "flag"},
        {"value": ui.compact(facture["population"]),
         "label": tr("proposition_inondations_tuile_population"),
         "delta": tr("proposition_inondations_tuile_population_detail"),
         "good": False, "icon": "trending-up"},
        {"value": "0", "label": tr("proposition_inondations_tuile_ouvrages"),
         "delta": tr("proposition_inondations_tuile_ouvrages_detail"),
         "good": False, "icon": "search"},
    ])

    with ui.card(tr("proposition_inondations_carte_titre"),
                 tr("proposition_inondations_carte_sous_titre"), "table-2"):
        lisible = facture["scenarios"].assign(
            hypothese=facture["scenarios"]["unitaire"].map(
                lambda cout: tr("proposition_hypothese",
                                {"cout": ui.compact(cout)})))

        charts.bar_h(lisible.assign(milliards=lisible["total"] / 1e9),
                     "hypothese", "milliards", unit=tr("unite_milliards"),
                     trier=False, decimals=2)
        ui.note(tr("proposition_inondations_note", {
            "cantons": ui.fr_number(facture["cantons"]),
        }))
        charts.table_twin(lisible[["hypothese", "cantons", "total"]].rename(
            columns={"hypothese": tr("col_hypothese"),
                     "cantons": tr("col_cantons"), "total": tr("col_cout")}))

    programme = _restreindre(analytics.programme_inondations(
        data["cantons"], data["tde"], data["coso"],
        cout_unitaire=COUT_RETENU, horizon=HORIZON_INONDATIONS,
        debut=PREMIERE_ANNEE))

    _calendrier(tr, programme, "programme_inondations_note", {
        "cantons": ui.fr_number(programme["cantons"]),
        "unitaire": ui.compact(programme["unitaire"]),
    })
    _entretien(tr, programme, data["coso"], "entretien_inondations_note")
    _chantiers(tr, programme, colonnes=["canton", "prefecture", "region",
                                        "risque_pts", "montant", "annee"])

    with ui.card(tr("proposition_inondations_liste_titre"),
                 tr("proposition_inondations_liste_sous_titre"), "flag"):
        charts.sucette_h(facture["liste"], "canton", "population",
                         unit=tr("unite_habitants"))
        ui.note(tr("proposition_inondations_note_liste", {
            "n": ui.fr_number(facture["cantons"]),
            "sans": ui.fr_number(len(prioritaires)),
        }))
        charts.table_twin(facture["liste"].rename(columns={
            "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
            "region": tr("col_region"), "risque_pts": tr("col_risque"),
            "population": tr("col_population")}))


def carte_exposes(tr, data, hauteur):
    """Les cantons à aménager : classes hautes du risque officiel."""

    cadre = analytics.classer_officiel(data["cantons"])
    hautes = cadre["classe_officielle"].isin(analytics.CLASSES_HAUTES)
    cadre = cadre.assign(a_amenager=hautes.astype(int))

    def dessin(h):
        return maps.choroplethe(
            cadre, valeur="a_amenager", cle="carte_recit_exposes",
            champs=["canton", "prefecture", "risque_pts", "population"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_risque"), tr("col_population")],
            height=h, nombre=2, methode="lineaire",
            # Deux teintes seulement : la question posée est binaire — ce
            # canton entre-t-il dans le programme, oui ou non. Une rampe
            # continue y aurait suggéré des degrés d'urgence que la décision
            # ne connaît pas.
            rampe=[BIVARIEE[1], MANQUE], couleur_contour=RISQUE_CONTOUR,
        )

    def pied(_):
        maps.legende_series([
            {"libelle": tr("legende_a_amenager"), "couleur": MANQUE,
             "detail": ui.fr_number(int(hautes.sum()))},
            {"libelle": tr("legende_hors_programme"), "couleur": BIVARIEE[1],
             "detail": ui.fr_number(int((~hautes).sum()))},
        ])
        ui.note(tr("proposition_inondations_note_carte", {
            "cantons": ui.fr_number(int(hautes.sum())),
            "population": ui.compact(float(
                cadre.loc[hautes, "population"].sum())),
        }))

    maps.carte(tr("proposition_inondations_map_titre"), cle="recit_exposes",
               dessin=dessin, legende=pied,
               sous_titre=tr("proposition_inondations_map_sous_titre"),
               hauteur=hauteur)


# ═══ Acte 4 · Et quand l'eau monte ? ═════════════════════════════════════════

def que_classe_le_fri(tr, data, faits, corpus):
    """L'objection retournée contre elle-même — et elle ne tient pas.

    La vue précédente établissait que le FRI corrèle plus fort avec la
    population (ρ = 0,80) qu'avec l'aléa (ρ = 0,54), et il aurait été facile
    d'en conclure que l'indice classe des habitants. Cette vue met la
    conclusion à l'épreuve en retirant la composante, et publie le résultat
    même s'il DÉMENT l'intuition : le classement tient.
    """

    ordonne = econometrie.ce_que_le_fri_ordonne(data["cantons"])
    epreuve = econometrie.fri_sans_population(data["cantons"])
    correlations = ordonne["correlations"]

    def rho(dimension):
        ligne = correlations[correlations["dimension"] == dimension]
        return float(ligne["rho"].iloc[0]) if len(ligne) else float("nan")

    accroche(
        [tr("fri_texte_1", {
            "exposition": ui.fr_number(rho("exposition"), 2),
            "alea": ui.fr_number(rho("alea"), 2),
        }),
         tr("fri_texte_2", {
             "n": ui.fr_number(epreuve["cantons"]),
             "deplacement": ui.fr_number(epreuve["deplacement_median"], 0),
             "renouvellement": ui.fr_number(epreuve["renouvellement"]),
             "sommet": ui.fr_number(epreuve["sommet"]),
         }),
         tr("fri_texte_3", {
             "rho": ui.fr_number(epreuve["rho_ampute"], 2),
             "complet": ui.fr_number(epreuve["rho_complet"], 3),
         })],
        titre=tr("fri_titre"), sur_titre=tr("acte_4"),
    )

    ui.stat_tiles([
        {"value": ui.fr_number(rho("exposition"), 2),
         "label": tr("fri_tuile_exposition"),
         "delta": tr("fri_tuile_exposition_detail"), "good": None,
         "icon": "trending-up"},
        {"value": ui.fr_number(epreuve["deplacement_median"], 0),
         "unit": tr("unite_places"),
         "label": tr("fri_tuile_deplacement"),
         "delta": tr("fri_tuile_deplacement_detail", {
             "n": ui.fr_number(epreuve["cantons"])}),
         "good": None, "icon": "search"},
        {"value": ui.fr_number(epreuve["rho_complet"], 3),
         "label": tr("fri_tuile_reconstitution"),
         "delta": tr("fri_tuile_reconstitution_detail"), "good": True,
         "icon": "table-2"},
    ])

    with ui.card(tr("fri_carte_correlations_titre"),
                 tr("fri_carte_correlations_sous_titre"), "trending-up"):
        lisible = correlations.assign(
            dimension=correlations["dimension"].map(
                lambda cle: tr(f"dimension_{cle}")))

        # Forme DIVERGENTE : la vulnérabilité corrèle NÉGATIVEMENT (−0,12), et
        # une barre partant de zéro vers la droite ne peut pas le montrer. Le
        # signe est ici le résultat — les cantons les plus pauvres ne sont pas
        # les plus exposés, ce qui contredit l'intuition que l'indice porte.
        charts.diverging_bar(lisible["dimension"].tolist(),
                             lisible["rho"].tolist(), unit="", height=170)
        ui.note(tr("fri_note_correlations", {
            "exposition": ui.fr_number(rho("exposition"), 2),
            "alea": ui.fr_number(rho("alea"), 2),
        }))
        charts.table_twin(lisible.rename(columns={
            "dimension": tr("col_dimension"), "rho": tr("col_rho"),
            "p": tr("col_p")}))

    with ui.card(tr("fri_carte_epreuve_titre"), tr("fri_carte_epreuve_sous_titre"),
                 "search"):
        cadre = epreuve["cadre"]

        if cadre.empty:
            ui.note(tr("fri_epreuve_vide"))
            return

        charts.pentes_appariees(
            cadre.head(12), "canton", "rang_publie", "rang_ampute",
            titre_gauche=tr("fri_rang_publie"),
            titre_droite=tr("fri_rang_ampute"),
        )
        ui.note(tr("fri_note_epreuve", {
            "deplacement": ui.fr_number(epreuve["deplacement_median"], 0),
            "max": ui.fr_number(epreuve["deplacement_max"]),
        }))
        charts.table_twin(cadre.head(12).rename(columns={
            "canton": tr("col_canton"), "prefecture": tr("col_prefecture"),
            "population": tr("col_population"), "risque_pts": tr("col_risque"),
            "rang_publie": tr("col_rang_publie"),
            "rang_ampute": tr("col_rang_ampute"),
            "deplacement": tr("col_deplacement")}))


def carte_fri_ampute(tr, data, hauteur):
    """Le FRI recalculé sans sa composante de population.

    Peinte avec la rampe et les seuils du producteur : c'est la même carte que
    l'officielle, à une composante près, et c'est cette comparaison-là qui a du
    sens. Les cantons absents sont ceux qui portent un zéro — ils ne peuvent
    entrer dans aucune moyenne géométrique, et les peindre à zéro inventerait
    une donnée.
    """

    epreuve = econometrie.fri_sans_population(data["cantons"])
    cadre = epreuve["cadre"]

    if cadre.empty:
        maps.carte(tr("fri_carte_map_titre"), cle="recit_fri_ampute",
                   dessin=lambda h: ([], "vide"),
                   legende=lambda _: ui.note(tr("fri_epreuve_vide")),
                   sous_titre=tr("fri_carte_map_sous_titre"), hauteur=hauteur)
        return

    situe = data["cantons"].merge(
        cadre[["cle_canton", "rang_ampute", "rang_publie", "deplacement"]],
        on="cle_canton", how="inner")

    def dessin(h):
        return maps.choroplethe(
            situe, valeur="rang_ampute", cle="carte_recit_fri_ampute",
            champs=["canton", "prefecture", "rang_publie", "rang_ampute"],
            libelles=[tr("col_canton"), tr("col_prefecture"),
                      tr("col_rang_publie"), tr("col_rang_ampute")],
            height=h, nombre=5, methode="quantiles",
            rampe=list(reversed(RISQUE_OFFICIEL)),
            couleur_contour=RISQUE_CONTOUR,
        )

    def pied(resultat):
        bornes, _ = resultat

        if bornes:
            maps.legende_paliers(bornes, rampe=list(reversed(RISQUE_OFFICIEL)),
                                 libelle=tr("fri_legende_rang"), decimales=0)

        ui.note(tr("fri_note_carte", {
            "n": ui.fr_number(epreuve["cantons"]),
            "total": ui.fr_number(len(data["cantons"])),
        }))

    maps.carte(tr("fri_carte_map_titre"), cle="recit_fri_ampute", dessin=dessin,
               legende=pied, sous_titre=tr("fri_carte_map_sous_titre"),
               hauteur=hauteur)


# ═══ Acte 5 · Que faire ? ════════════════════════════════════════════════════

def facture(tr, data, faits, corpus):
    """Ce que coûterait le rattrapage — et pourquoi le lieu compte plus que la somme."""

    addition = analytics.facture_rattrapage(
        data["cantons"], data["tde"], data["coso"])
    cout = econometrie.fonction_de_cout(data["coso"])
    elasticite = cout["estimation"]["termes"]
    ligne = elasticite[elasticite["terme"] == "log_beneficiaires"]

    accroche(
        [tr("facture_texte_1", {
            "ouvrages": ui.fr_number(addition["ouvrages"]),
            "unitaire": ui.compact(addition["unitaire"]),
            "total": ui.compact(addition["total"]),
        }),
         tr("facture_texte_2", {
             # Trois décimales : à deux, un coefficient de −0,0009 s'affichait
             # « −0,00 » — un zéro négatif, qui se lit comme une coquille.
             "coefficient": ui.fr_number(float(ligne["coefficient"].iloc[0]), 3)
             if len(ligne) else "—",
             "r2": ui.fr_number(cout["estimation"]["r2"], 3),
             "n": ui.fr_number(cout["estimation"]["n"]),
         })],
        titre=tr("facture_titre"), sur_titre=tr("acte_5"),
    )

    ui.stat_tiles([
        {"value": ui.compact(addition["total"]), "unit": " F",
         "label": tr("facture_tuile_total"),
         "delta": tr("facture_tuile_total_detail", {
             "ouvrages": ui.fr_number(addition["ouvrages"])}),
         "good": None, "icon": "table-2"},
        {"value": ui.compact(addition["unitaire"]), "unit": " F",
         "label": tr("facture_tuile_unitaire"),
         "delta": tr("facture_tuile_unitaire_detail", {
             "n": ui.fr_number(addition["observations"])}),
         "good": None, "icon": "building-2"},
        {"value": ui.fr_number(cout["estimation"]["r2"], 3),
         "label": tr("facture_tuile_r2"),
         "delta": tr("facture_tuile_r2_detail"), "good": None, "icon": "search"},
    ])

    with ui.card(tr("facture_carte_titre"), tr("facture_carte_sous_titre"),
                 "table-2"):
        charts.bar_h(addition["regions"], "region", "cout",
                     unit=tr("unite_fcfa"))
        ui.note(tr("facture_note", {
            "total": ui.compact(addition["total"]),
            "unitaire": ui.compact(addition["unitaire"]),
        }))
        charts.table_twin(addition["regions"][[
            "region", "manquants", "cout"]].rename(columns={
                "region": tr("col_region"), "manquants": tr("col_manquants"),
                "cout": tr("col_cout")}))

    with ui.card(tr("facture_carte_profil_titre"),
                 tr("facture_carte_profil_sous_titre"), "trending-up"):
        profil = cout["profil"]

        charts.bar_h(
            profil.assign(quintile=profil["quintile"].astype(str)),
            "quintile", "cout_par_beneficiaire", unit=tr("unite_fcfa"),
            trier=False)
        ui.note(tr("facture_note_profil", {
            "haut": ui.fr_number(
                float(profil["cout_par_beneficiaire"].iloc[0]), 0),
            "bas": ui.fr_number(
                float(profil["cout_par_beneficiaire"].iloc[-1]), 0),
        }))
        charts.table_twin(profil.assign(
            quintile=profil["quintile"].astype(str)).rename(columns={
                "quintile": tr("col_quintile"), "ouvrages": tr("col_ouvrages"),
                "beneficiaires_median": tr("col_beneficiaires"),
                "cout_median": tr("col_cout"),
                "cout_par_beneficiaire": tr("col_cout_beneficiaire")}))


def carte_facture(tr, data, hauteur):
    """Le coût du rattrapage, région par région."""

    addition = analytics.facture_rattrapage(
        data["cantons"], data["tde"], data["coso"])

    _carte_par_region(
        tr, data, "cout", "recit_facture",
        tr("facture_carte_map_titre"), tr("facture_carte_map_sous_titre"),
        hauteur, addition["regions"], tr("col_cout"),
        tr("facture_note_carte", {
            "total": ui.compact(addition["total"]),
            "ouvrages": ui.fr_number(addition["ouvrages"])}),
    )
