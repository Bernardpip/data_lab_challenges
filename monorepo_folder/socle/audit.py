"""Outils d'audit du corpus — pour COMPTER une absence, jamais l'affirmer.

Le garde-fou méta de la méthode : un indicateur déclaré introuvable doit
l'être par balayage du corpus, pas de mémoire. Sur le pilote, ce contrôle a
révélé qu'une neuvième ressource portait les quatre indicateurs qu'on croyait
manquants — un verdict écrit à la main les aurait déclarés impossibles, et le
travail serait passé à côté de son objectif n°2.

Deux primitives seulement, mais elles sont ce qui rend un audit vérifiable :

    chercher(bruts, r"effectif")     → où le motif apparaît, fichier par fichier
    ecart_dictionnaire(...)          → décrits vs publiés, et par familles

Le reste — la liste des indicateurs de l'énoncé et leurs verdicts — appartient
au défi (`utils/perimetre.py`), puisque l'énoncé change à chaque fois.
"""

import re
import unicodedata

# pyrefly: ignore [missing-import]
import pandas as pd


# Colonnes qui, dans un fichier en format LONG, nomment les séries. Sans ce
# balayage, un indicateur logé en valeur passerait pour absent.
ETIQUETTES_SERIES = ("indicateur", "indicateurs", "indicator", "libelle",
                     "libelles", "libellés", "variable", "mesure")


def normaliser(texte):
    """Minuscules sans accents — chercher un champ sans dépendre de sa graphie.

    « Préfecture », « PREFECTURE » et « prefecture » désignent la même chose ;
    sans normalisation, deux des trois échappent à toute recherche.
    """

    return "".join(
        c for c in unicodedata.normalize("NFD", str(texte).lower())
        if unicodedata.category(c) != "Mn"
    )


def chercher(bruts, motif):
    """Où `motif` apparaît dans le corpus. Liste vide = introuvable partout.

    Cherche à DEUX endroits, et c'est indispensable : un corpus mêle des
    fichiers larges, où un indicateur est une COLONNE, et des fichiers longs,
    où il est une VALEUR de la colonne « indicateur ». Ne regarder que les
    en-têtes ferait passer les seconds pour vides — c'est précisément l'erreur
    que ce garde-fou doit empêcher.

    `bruts` : {nom de fichier: DataFrame NON nettoyé}. Non nettoyé, parce
    qu'un nettoyage a pu renommer ou écarter la colonne recherchée.
    """

    trouves = []

    for nom, cadre in bruts.items():
        colonnes = [
            c for c in cadre.columns.astype(str) if re.search(motif, normaliser(c))
        ]

        valeurs = []

        for etiquette in cadre.columns.astype(str):
            if normaliser(etiquette) not in ETIQUETTES_SERIES:
                continue

            serie = cadre[etiquette].dropna().astype(str).unique()
            valeurs += [v for v in serie if re.search(motif, normaliser(v))]

        if colonnes or valeurs:
            trouves.append({
                "fichier": nom,
                "colonnes": colonnes,
                "series": sorted(set(valeurs)),
            })

    return trouves


def presence(bruts, motifs):
    """{intitulé: fichiers où il apparaît} — le tableau d'un audit d'un coup.

    `motifs` : {intitulé lisible: motif d'expression régulière}.
    """

    return {intitule: chercher(bruts, motif) for intitule, motif in motifs.items()}


def ecart_dictionnaire(dictionnaire, fichier, colonne_nom, familles=None):
    """Champs DÉCRITS par un dictionnaire mais absents du fichier diffusé.

    Souvent le constat le plus fort d'un travail sur données ouvertes : il ne
    s'agit pas d'une donnée jamais collectée mais d'une donnée collectée et
    NON PUBLIÉE. La distinction change la recommandation — republier coûte
    infiniment moins qu'enquêter (pilote : 216 champs décrits, 16 publiés).

    `familles` : {libellé: motif} pour regrouper les champs absents par thème,
    parce qu'une liste de 200 noms de champs ne se lit pas.
    """

    noms = dictionnaire[colonne_nom].dropna().astype(str).str.strip()
    decrits = set(noms)
    publies = set(fichier.columns.astype(str).str.strip())

    groupes = {}

    for libelle, motif in (familles or {}).items():
        groupes[libelle] = sorted(
            noms[noms.map(normaliser).str.contains(motif, regex=True)]
        )

    return {
        "decrits": len(decrits),
        "publies": len(publies),
        "communs": len(decrits & publies),
        "absents": len(decrits - publies),
        "part_publiee": len(decrits & publies) / len(decrits) * 100 if decrits else 0,
        "familles": groupes,
    }


def profil_fichier(cadre):
    """Volumétrie et complétude d'un jeu BRUT — avant tout nettoyage.

    Décrire un fichier après nettoyage le présenterait comme plus propre qu'il
    n'est, et effacerait le travail qu'il a fallu lui appliquer.
    """

    lignes, colonnes = cadre.shape
    remplissage = cadre.notna().mean() * 100

    return {
        "lignes": int(lignes),
        "colonnes": int(colonnes),
        "doublons": int(cadre.duplicated().sum()),
        "completude": float(remplissage.mean()),
        "colonnes_vides": sorted(
            c for c in cadre.columns if cadre[c].notna().sum() == 0
        ),
        "par_colonne": {
            str(c): float(v) for c, v in remplissage.sort_values().items()
        },
    }


def numerique(serie):
    """Série convertie en nombres, valeurs illisibles écartées.

    `errors="coerce"` transforme en `NaN` ce qui n'est pas un nombre : une
    cellule « n.d. » ne doit pas faire échouer tout un calcul, mais elle ne
    doit pas non plus valoir zéro.
    """

    return pd.to_numeric(serie, errors="coerce").dropna()
