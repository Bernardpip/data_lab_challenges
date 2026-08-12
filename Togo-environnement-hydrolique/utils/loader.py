"""Lecture BRUTE des huit ressources du corpus. Aucun nettoyage ici.

La séparation lecture/nettoyage n'est pas cosmétique : les profils de fichiers
décrivent la volumétrie et les anomalies AVANT traitement. Si le loader
nettoyait, on présenterait comme propre un jeu qui ne l'était pas — et le
constat central de ce défi porte précisément sur ce que les fichiers ne
contiennent pas.

Ce qui est chargé, et ce qui est seulement CITÉ :

  · chargés — les cinq tabulaires, le GeoJSON des microprojets et la couche
    des 388 cantons. Tout tient en mémoire et se dessine dans un navigateur ;
  · cités — les grilles à 1 km (57 738 mailles) et à 500 m (228 953), et le
    raster de susceptibilité (79 Mo, pixel 30 m). Folium s'effondre bien avant
    ces volumes, et un raster ne se versionne pas. Ils restent référencés dans
    les sources, avec leur URL : le tableau de bord dit ce qu'il n'affiche pas.
"""

from pathlib import Path

# pyrefly: ignore [missing-import]
import geopandas as gpd
# pyrefly: ignore [missing-import]
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Les cantons et les microprojets sont en EPSG:32631 (UTM 31N) ou en degrés
# selon la source. Folium n'accepte que le WGS 84 : la reprojection se fait ici,
# une fois, plutôt que dans chaque vue.
CRS_AFFICHAGE = "EPSG:4326"


def chemin(nom):
    """Le fichier `nom`, où qu'il se trouve SOUS `data/`.

    Les ressources ont d'abord vécu à plat, puis ont été rangées en
    `map/`, `planches/`, `projets/`, `series/`. Une déclaration qui figerait
    le sous-dossier casserait au prochain rangement — et elle a cassé : plus
    aucun jeu ne se chargeait, sans que rien ne dise pourquoi avant le premier
    `FileNotFoundError`.

    Le nom de fichier, lui, vient du producteur et ne change pas : c'est donc
    lui la clé. La recherche descend l'arborescence, et l'erreur, quand il n'y
    a rien, NOMME ce qui a été cherché plutôt que de citer un chemin qui
    n'existe pas.
    """

    direct = DATA_DIR / nom

    if direct.exists():
        return direct

    for trouve in DATA_DIR.rglob(nom):
        return trouve

    raise FileNotFoundError(
        f"« {nom} » est introuvable sous {DATA_DIR}. "
        f"Sous-dossiers présents : "
        f"{sorted(d.name for d in DATA_DIR.iterdir() if d.is_dir()) or 'aucun'}."
    )


FICHIERS = {
    # DCEF-TG — châteaux d'eau et forages de la TdE. 67 ouvrages, dont 65 en
    # région Maritime : ce n'est pas un inventaire national.
    "tde": "file-chateaux-deau-forages-tde-19-12-2024-18-55-00.csv",

    # DCEF-TG — le DICTIONNAIRE des champs du jeu précédent. 33 champs décrits
    # pour 8 publiés : c'est la pièce qui permet de prouver ce qui manque.
    "tde_dictionnaire": "chateaux-deau-forages-tde.csv",

    # PCIAEPH-TG — microprojets COSO. Le CSV et le GeoJSON portent les mêmes
    # 218 lignes ; seul le GeoJSON a la géométrie, d'où le chargement séparé.
    "coso": "subprojects-sector-eau-hydraulique.csv",

    # DVECA-TG — ventes d'eau par catégorie d'abonnés, 2018-2022. NATIONAL.
    "ventes": "observationdata-mfcialc.csv",

    # DPSSA-TG — population par subdivision, recensement 2010. Une seule année.
    "population": "observationdata-sapxctg.csv",
}

FICHIERS_GEO = {
    # PCIAEPH-TG — mêmes données que "coso", avec les points.
    "coso_geo": "projet-coso-eau.geojson",

    # ISRI-TG — LE pivot du tableau de bord : 388 cantons couvrant tout le
    # pays, portant à la fois l'indice de risque d'inondation et la population.
    "cantons": "fri-cantons.gpkg",
}

# Cités, jamais chargés — cf. le module `utils/profils.py`, qui les décrit.
FICHIERS_CITES = {
    "fri_grid_1km": "fri-grid-1km.gpkg",
    "fri_grid_500m": "fri-grid-500m.gpkg",
    "fsi_raster": "fsi_brut.tif",
    "fsi_raster_zip": "fsi-brut-geotiff.zip",
}


def lire_csv(nom, **kwargs):
    """Un CSV du corpus, tel quel.

    `low_memory=False` force pandas à lire la colonne entière avant d'en
    inférer le type : le fichier COSO a 84 colonnes dont plusieurs mêlent
    nombres et vides, et une lecture par morceaux leur donnerait des types
    différents d'un bloc à l'autre.
    """

    return pd.read_csv(chemin(nom), encoding="utf-8", low_memory=False, **kwargs)


def lire_geo(nom):
    """Une couche géographique, reprojetée en WGS 84.

    `fri-cantons.gpkg` arrive en EPSG:32631 — des mètres UTM. Affichée telle
    quelle, la carte placerait le Togo quelque part dans l'Atlantique : Folium
    interprète toute coordonnée comme des degrés.
    """

    couche = gpd.read_file(chemin(nom))

    if couche.crs is not None and couche.crs.to_string() != CRS_AFFICHAGE:
        couche = couche.to_crs(CRS_AFFICHAGE)

    return couche


def charger_tout():
    """Les sept ressources exploitables, indexées par leur clé courte."""

    donnees = {cle: lire_csv(nom) for cle, nom in FICHIERS.items()}
    donnees.update({cle: lire_geo(nom) for cle, nom in FICHIERS_GEO.items()})

    return donnees


def poids_des_fichiers():
    """Taille sur disque de CHAQUE ressource, citée comprise.

    Sert le profil des fichiers : c'est le poids qui justifie qu'on ait renoncé
    à charger les grilles et le raster, et l'affirmer sans le chiffrer serait
    une commodité.
    """

    tous = {**FICHIERS, **FICHIERS_GEO, **FICHIERS_CITES}

    def poids(nom):
        # Un fichier absent pèse 0 plutôt que de lever : ce profil doit
        # s'afficher même quand une ressource CITÉE n'a pas été téléchargée.
        try:
            return chemin(nom).stat().st_size
        except FileNotFoundError:
            return 0

    return {cle: poids(nom) for cle, nom in tous.items()}
