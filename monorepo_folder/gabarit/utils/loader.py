"""Lecture BRUTE des fichiers du corpus. Aucun nettoyage ici.

La séparation lecture/nettoyage n'est pas cosmétique : les profils de fichiers
(`utils/profils.py`) décrivent la volumétrie et les anomalies AVANT traitement.
Si le loader nettoyait, on présenterait comme propre un jeu qui ne l'était pas.

Une entrée de `FICHIERS` par ressource, la clé étant le sigle court utilisé
partout ensuite.
"""

from pathlib import Path

# pyrefly: ignore [missing-import]
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# clé courte → nom de fichier tel que téléchargé (ne pas renommer les
# fichiers : le nom d'origine est la trace de la ressource sur le portail).
FICHIERS = {
    # "eaux": "chateaux-deau-forages-tde.csv",
}


def lire_csv(nom, **kwargs):
    """Un CSV du corpus, tel quel.

    `low_memory=False` force pandas à lire la colonne entière avant d'en
    inférer le type : sans cela, une colonne dont les 10 000 premières lignes
    sont numériques et la suivante textuelle est lue en deux morceaux de types
    différents, et le `dtype` final devient `object` sans prévenir.
    """

    return pd.read_csv(DATA_DIR / nom, encoding="utf-8", low_memory=False, **kwargs)


def charger_tout():
    """Tous les fichiers déclarés, indexés par leur clé courte."""

    return {cle: lire_csv(nom) for cle, nom in FICHIERS.items()}
