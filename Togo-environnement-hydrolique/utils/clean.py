"""Nettoyage — une fonction par jeu, un commentaire par anomalie traitée.

Le commentaire est la seule trace de ce qui a été décidé sur les données.
« Sans ça, 73 forages s'affichent au large du Ghana » se relit ; un
`dropna()` nu, non.

Deux règles priment sur la propreté apparente :

  · **aucune donnée fabriquée** — pas d'interpolation, pas de coordonnée
    devinée depuis le nom du village ;
  · **les non-réponses restent visibles** sous `NON_RENSEIGNE` plutôt que
    supprimées. Les supprimer embellirait chaque répartition et effacerait
    le constat que ce défi doit précisément porter : ce corpus est troué.
"""

import re
import unicodedata

# pyrefly: ignore [missing-import]
import pandas as pd

NON_RENSEIGNE = "Non renseigné"

# Sentinelles du corpus : elles signifient « absent », pas « zéro » ni un nom.
# « Nsp » apparaît 7 fois dans le nom d'ouvrage TdE.
SENTINELLES = ("", "Nsp", "NSP", "N/a", "NA", "n/a", "-", "--", "ND", "nd")

# Les cinq niveaux que porte la colonne `hierarchy` du COSO, du plus fin au
# plus large : « ALEGBA > BALANKA > TCHAMBA 3 > TCHAMBA > CENTRALE ».
NIVEAUX_COSO = ["village", "canton", "commune", "prefecture", "region"]


def normaliser_cle(valeur):
    """Majuscules sans accents ni ponctuation — pour APPARIER, pas pour afficher.

    Les mêmes cantons s'écrivent « Agoè-Nyivé » dans le référentiel et
    « AGOE NYIVE » dans le COSO. Sans cette normalisation, la jointure au
    canton perd les deux tiers des ouvrages, et le tableau de bord conclurait
    à un désert d'équipement là où il n'y a qu'une différence de graphie.
    """

    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", str(valeur).upper())
        if unicodedata.category(c) != "Mn"
    )

    return re.sub(r"[^A-Z0-9]+", " ", sans_accent).strip()


def normaliser_texte(serie):
    """Espaces rognés, sentinelles ramenées à l'absence."""

    nettoyee = serie.astype("string").str.strip()

    return nettoyee.replace(list(SENTINELLES), pd.NA)


def combler(cadre, colonnes):
    """`NON_RENSEIGNE` sur les colonnes NOMINALES seulement.

    Jamais sur une colonne numérique : une non-réponse n'est pas un zéro, et
    la transformer en texte ferait basculer toute la colonne en `object`.
    """

    for colonne in colonnes:
        cadre[colonne] = cadre[colonne].fillna(NON_RENSEIGNE)

    return cadre


# ─── ISRI-TG · les 388 cantons, pivot de tout le tableau de bord ─────────────

def nettoyer_cantons(brut):
    """Le référentiel territorial : 388 cantons, risque d'inondation, population.

    C'est le seul jeu du corpus qui couvre le pays entier à une maille fine.
    Tout le reste s'y raccroche par `cle_canton`.
    """

    cadre = brut.copy()

    # `prefecture` porte le CODE (« A01 ») et `prefectu_1` le NOM — un
    # tronquage de « prefecture_nom » à dix caractères, hérité du format
    # Shapefile. Renommer le second sans renommer le premier créerait deux
    # colonnes du même nom, et toute lecture renverrait un DataFrame.
    cadre = cadre.rename(columns={"prefecture": "prefecture_id"})

    cadre = cadre.rename(columns={
        "region_nom": "region",
        "prefectu_1": "prefecture",
        "commune_no": "commune",
        "canton_nom": "canton",
        "total_pop": "population",
        "max_fsi": "susceptibilite",
        "min_rwi": "richesse_relative",
        "urban_ratio": "part_urbaine",
        "building_count": "batiments",
        "min_dist_basin": "distance_bassin",
        "FRI": "risque",
    })

    for colonne in ("region", "prefecture", "commune", "canton"):
        cadre[colonne] = normaliser_texte(cadre[colonne])

    cadre["cle_canton"] = cadre["canton"].map(normaliser_cle)

    # Deux cantons distincts portent le même nom (387 noms pour 388 entités) :
    # `canton_id` reste donc la seule clé sûre à l'intérieur du référentiel,
    # et `cle_canton` ne sert qu'à rattacher les jeux d'ouvrages, qui ne
    # connaissent que des noms.
    cadre["canton_unique"] = ~cadre["cle_canton"].duplicated(keep=False)

    # Le risque arrive entre 0 et 1 ; l'exprimer en points de 0 à 100 évite
    # d'afficher « 0,079 » dans une tuile, que personne ne sait situer.
    cadre["risque_pts"] = cadre["risque"] * 100

    return cadre


# ─── DCEF-TG · forages et châteaux d'eau de la TdE ───────────────────────────

_POINT_WKT = re.compile(r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)")


def nettoyer_tde(brut):
    """67 ouvrages, dont 65 en Maritime — pas un inventaire national.

    La géométrie arrive en WKT dans une colonne texte, pas en géométrie : le
    fichier est un CSV exporté d'une vue PostGIS, et `geopandas` ne le lit pas
    tout seul.
    """

    cadre = brut.copy()

    cadre = cadre.rename(columns={
        "region_nom_bdd": "region",
        "prefecture_nom_bdd": "prefecture",
        "commune_nom_bdd": "commune",
        "canton_nom_bdd": "canton",
        "forage_chateau_nom": "ouvrage",
    })

    for colonne in ("region", "prefecture", "commune", "canton", "ouvrage"):
        cadre[colonne] = normaliser_texte(cadre[colonne])

    coords = cadre["geometry"].astype(str).str.extract(_POINT_WKT)
    cadre["lon"] = pd.to_numeric(coords[0], errors="coerce")
    cadre["lat"] = pd.to_numeric(coords[1], errors="coerce")

    # Le nom de l'ouvrage sert aussi de nature : « Forage … », « Château … ».
    # Les 7 « Nsp » sont devenus absents ci-dessus ; ils restent COMPTÉS sous
    # « Non renseigné » plutôt que d'être écartés, sinon la répartition par
    # nature laisserait croire à un parc entièrement identifié.
    premier_mot = cadre["ouvrage"].str.split().str[0]
    cadre["nature"] = premier_mot.where(
        premier_mot.isin(["Forage", "Château"]), other=pd.NA
    )

    cadre["cle_canton"] = cadre["canton"].map(normaliser_cle)

    return combler(cadre, ["region", "prefecture", "commune", "canton",
                           "ouvrage", "nature"])


def nettoyer_dictionnaire_tde(brut):
    """Les 33 champs que le producteur décrit — dont 26 qu'il ne publie pas."""

    cadre = brut.copy()
    cadre.columns = [c.strip() for c in cadre.columns]

    return cadre.rename(columns={
        "Nom du champ": "champ",
        "Question": "question",
        "Type du champ": "type",
    })


# ─── PCIAEPH-TG · microprojets COSO ──────────────────────────────────────────

# Colonnes intégralement vides dans le fichier livré : les garder ferait
# apparaître six variables qu'aucune vue ne pourra jamais remplir.
COLONNES_VIDES_COSO = [
    "has_latrine_blocs", "storage_capacity", "length_of_the_track",
    "extension_length", "has_fence",
]


def nettoyer_coso(brut, geo=None):
    """218 microprojets d'eau du projet COSO, Nord-Togo.

    `geo` — le GeoJSON, qui porte les mêmes lignes AVEC la géométrie. Le CSV
    et lui ne diffèrent que par là ; on lit le CSV pour les attributs et on
    récupère les coordonnées du second quand il est fourni.
    """

    cadre = (geo if geo is not None else brut).copy()

    if "geometry" in cadre.columns and hasattr(cadre, "geometry"):
        cadre["lon"] = cadre.geometry.x
        cadre["lat"] = cadre.geometry.y
        cadre = pd.DataFrame(cadre.drop(columns="geometry"))
    else:
        cadre["lon"] = pd.to_numeric(cadre.get("longitude"), errors="coerce")
        cadre["lat"] = pd.to_numeric(cadre.get("latitude"), errors="coerce")

    # 73 ouvrages portent POINT(0 0) — l'« île nulle », au large du Ghana.
    # Ce n'est pas une position, c'est une absence encodée en zéro : traitée
    # comme une coordonnée, elle planterait 73 marqueurs dans l'Atlantique et
    # ferait mentir le cadrage de toutes les cartes.
    hors_pays = (cadre["lat"].abs() < 0.01) & (cadre["lon"].abs() < 0.01)
    cadre.loc[hors_pays, ["lat", "lon"]] = pd.NA
    cadre["situe"] = cadre["lat"].notna() & cadre["lon"].notna()

    # La hiérarchie est la vraie richesse du jeu : elle place 217 ouvrages sur
    # 218 dans la chaîne village → canton → commune → préfecture → région,
    # y compris ceux que la géolocalisation a perdus.
    parts = cadre["hierarchy"].astype(str).str.split(" > ", expand=True)
    for index, niveau in enumerate(NIVEAUX_COSO):
        cadre[niveau] = normaliser_texte(parts[index]) if index < parts.shape[1] else pd.NA

    # Les régions du COSO arrivent EN MAJUSCULES (« SAVANES ») quand le
    # référentiel écrit « Savanes » : sans normalisation, un graphe qui
    # empile les deux parcs compte « CENTRALE » et « Centrale » comme deux
    # régions distinctes. Les cinq noms de région sont sans accent, la
    # capitalisation suffit — on ne touche NI aux cantons NI aux villages,
    # dont les accents perdus ne se reconstruisent pas.
    cadre["region"] = cadre["region"].str.lower().str.capitalize()

    cadre["cle_canton"] = cadre["canton"].map(normaliser_cle)

    cadre = cadre.rename(columns={
        "type": "type_ouvrage",
        "works_type": "travaux",
        "current_status_of_the_site": "avancement",
        "existence_of_maintenance_plan": "plan_maintenance",
        "depth_of_drilling": "profondeur",
        "drilling_flow_rate": "debit",
        "estimated_cost": "cout_estime",
        "total_contract_amount_paid": "montant_paye",
        "care_and_maintenance_amount_on_village_account": "fonds_entretien",
        "amount_of_the_care_and_maintenance_fund_expected": "fonds_entretien_prevu",
        "population": "population_desservie",
        "direct_beneficiaries_women": "beneficiaires_femmes",
        "direct_beneficiaries_men": "beneficiaires_hommes",
        "location_name": "localite",
        "work_completion_date": "date_achevement",
    })

    cadre["annee_achevement"] = pd.to_datetime(
        cadre["date_achevement"], errors="coerce"
    ).dt.year

    # `number_of_classrooms` ne contient que des zéros et `number_of_infrastructures`
    # que des uns : deux colonnes qui n'encodent aucune variation.
    cadre = cadre.drop(columns=[c for c in COLONNES_VIDES_COSO if c in cadre.columns],
                       errors="ignore")

    return combler(cadre, ["region", "prefecture", "commune", "canton", "village",
                           "type_ouvrage", "travaux", "avancement", "localite"])


# ─── DVECA-TG · ventes d'eau, national ───────────────────────────────────────

def nettoyer_ventes(brut):
    """Ventes d'eau par catégorie d'abonnés, en m³, 2018-2022. Format long.

    Aucune maille territoriale : ces volumes valent pour le pays entier. Ils
    ne descendront donc JAMAIS dans un graphe régional — ce serait inventer
    une répartition que la source ne porte pas.
    """

    cadre = brut.copy()
    cadre = cadre.rename(columns={"indicateur": "categorie", "Date": "annee",
                                  "Value": "volume_m3", "Unit": "unite"})
    cadre["categorie"] = normaliser_texte(cadre["categorie"])
    cadre["annee"] = pd.to_numeric(cadre["annee"], errors="coerce").astype("Int64")
    cadre["volume_m3"] = pd.to_numeric(cadre["volume_m3"], errors="coerce")

    return cadre.dropna(subset=["annee", "volume_m3"])


# ─── DPSSA-TG · population, recensement 2010 ─────────────────────────────────

def nettoyer_population(brut):
    """Population par subdivision, RGPH 2010 — une seule année.

    Les 555 libellés mêlent des niveaux incomparables : le pays, des villes,
    des arrondissements, des quartiers, des cantons. Il n'existe aucune
    colonne de niveau pour les départager, donc aucun total partiel ne peut
    être recomposé sans risque de double compte.

    Ce jeu sert à UN seul usage dans le tableau de bord : montrer que le
    recensement de 2010 (6,19 M) et l'estimation portée par les cantons
    (8,17 M) ne se recouvrent pas. Il n'alimente aucun ratio.
    """

    cadre = brut.copy()
    cadre = cadre.rename(columns={"indicateurs": "libelle", "Date": "annee",
                                  "Value": "habitants"})
    cadre["libelle"] = normaliser_texte(cadre["libelle"])
    cadre["cle_canton"] = cadre["libelle"].map(normaliser_cle)
    cadre["habitants"] = pd.to_numeric(cadre["habitants"], errors="coerce")

    # `Unit` est vide sur les 555 lignes : la colonne ne porte rien.
    return cadre.drop(columns=[c for c in ("Unit", "unite") if c in cadre.columns])
