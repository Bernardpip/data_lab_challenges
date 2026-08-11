"""Périmètre du travail — ce que le cahier des charges demande, et ce que les
données ouvertes permettent réellement d'honorer.

Ce module ne raconte rien : il **compte**. Chaque verdict d'indisponibilité est
établi en cherchant le champ dans les 8 fichiers chargés, jamais affirmé de
mémoire. Les chiffres cités dans le rapport en découlent, ce qui garantit qu'ils
ne peuvent pas dériver si un fichier change.

Deux faits en ressortent, et ils ne portent pas sur le même niveau d'études.

1. Pour l'enseignement SUPÉRIEUR, les quatre indicateurs de l'objectif n°2 —
   effectifs, féminisation, filières scientifiques, ratio étudiant/enseignant —
   sont tous disponibles, mais dans une NEUVIÈME ressource (DICES-TG) absente
   de la liste initiale de huit. Les huit premières ne les portaient pas.

2. Pour la formation TECHNIQUE, les mêmes grandeurs restent hors de portée — et
   pour une raison différente : elles ont été collectées mais non publiées. Le
   dictionnaire des champs décrit un questionnaire de 216 champs, dont les
   effectifs d'élèves, le nombre d'enseignants et leur ventilation par sexe. Le
   fichier diffusé n'en expose que 16.
"""

import re
import unicodedata

import pandas as pd

from socle.i18n.traduction import t


HONORE = "honore"
PARTIEL = "partiel"
IMPOSSIBLE = "impossible"


def _norm(texte):
    """Minuscules sans accents — pour chercher un champ sans dépendre de sa casse."""

    return "".join(
        c for c in unicodedata.normalize("NFD", str(texte).lower())
        if unicodedata.category(c) != "Mn"
    )


def _cherche(brut, motif):
    """Où le motif apparaît dans le corpus. Liste vide = introuvable partout.

    Cherche à DEUX endroits, et c'est indispensable : le corpus mêle des
    fichiers larges, où un indicateur est une colonne, et des fichiers longs,
    où il est une VALEUR de la colonne « indicateur ». Ne regarder que les
    en-têtes ferait passer les seconds pour vides — c'est précisément l'erreur
    que ce garde-fou doit empêcher.
    """

    trouves = []

    for nom, cadre in brut.items():
        colonnes = [
            c for c in cadre.columns.astype(str) if re.search(motif, _norm(c))
        ]

        # Colonnes qui NOMMENT les séries d'un fichier en format long.
        valeurs = []

        for etiquette in ("indicateur", "indicator", "libellés", "libelles"):
            if etiquette in cadre.columns:
                serie = cadre[etiquette].dropna().astype(str).unique()
                valeurs += [v for v in serie if re.search(motif, _norm(v))]

        if colonnes or valeurs:
            trouves.append({
                "fichier": nom,
                "colonnes": colonnes,
                "series": sorted(set(valeurs)),
            })

    return trouves


def ecart_dictionnaire(brut):
    """Champs décrits par le dictionnaire mais absents du fichier diffusé.

    C'est le cœur du diagnostic sur les indicateurs manquants : il ne s'agit
    pas d'une donnée jamais collectée mais d'une donnée collectée et non
    publiée. La distinction change la recommandation — republier coûte
    infiniment moins qu'enquêter.
    """

    dictionnaire = brut["formations_detail"]
    fichier = brut["formations"]

    decrits = set(dictionnaire["Nom du champ"].dropna().astype(str).str.strip())
    publies = set(fichier.columns.astype(str).str.strip())

    noms = dictionnaire["Nom du champ"].dropna().astype(str).str.strip()

    def famille(motif):
        return sorted(noms[noms.map(_norm).str.contains(motif, regex=True)])

    return {
        "decrits": len(decrits),
        "publies": len(publies),
        "communs": len(decrits & publies),
        "absents": len(decrits - publies),
        "part_publiee": len(decrits & publies) / len(decrits) * 100 if decrits else 0,
        "familles": {
            "Effectifs d'élèves": famille(r"^eleve"),
            "Personnel enseignant": famille(r"enseignant"),
            "Ventilation par sexe": famille(
                r"femme|homme|genre|_fem$|_hom$|femmenbr|hommenbr"
            ),
        },
    }


def audit(brut):
    """Objectif par objectif, indicateur par indicateur : honoré ou non.

    Les six objectifs sont ceux du cahier des charges, éclatés en indicateurs
    élémentaires — un objectif « partiellement honoré » ne dit rien d'utile si
    l'on ne sait pas lequel de ses indicateurs manque.
    """

    ecart = ecart_dictionnaire(brut)
    familles = ecart["familles"]

    # Extraits sortis des f-strings : une apostrophe échappée y est interdite.
    champs_eleves = ", ".join(familles["Effectifs d'élèves"][:2])

    # Effectifs réels du 9e jeu — le verdict « honoré » doit être adossé aux
    # valeurs, pas affirmé.
    effectifs = brut["indicateurs_sup"]
    effectifs = effectifs[
        effectifs["indicateur"].astype(str).str.strip()
        == "Evolution des effectifs des étudiants inscrits"
    ]
    valeurs = pd.to_numeric(effectifs["Value"], errors="coerce").dropna()
    nb_effectifs = len(valeurs)
    eff_debut = int(valeurs.iloc[0]) if nb_effectifs else 0
    eff_fin = int(valeurs.iloc[-1]) if nb_effectifs else 0

    def fr(nombre):
        """Espace insécable fine comme séparateur de milliers."""

        return f"{nombre:,}".replace(",", "\u202f")

    tr = t("perimetre")

    # Une entrée par indicateur : son objectif, son verdict, et le préfixe de
    # ses trois textes (`i5_indicateur`, `i5_source`, `i5_motif`). Les valeurs
    # calculées passent en paramètres — un motif cite ses chiffres.
    lignes = [
        {"objectif": "obj1", "i18n": "i1", "verdict": HONORE},
        {"objectif": "obj1", "i18n": "i2", "verdict": IMPOSSIBLE},
        {"objectif": "obj1", "i18n": "i3", "verdict": IMPOSSIBLE,
         "params_source": {"champs": champs_eleves}},
        {"objectif": "obj1", "i18n": "i4", "verdict": PARTIEL},

        # Les quatre indicateurs de l'objectif n°2 étaient hors de portée des
        # huit premières ressources. Ils sont tous portés par la neuvième
        # (DICES-TG) — d'où des séries courtes (2014-2019) mais réelles.
        {"objectif": "obj2", "i18n": "i5", "verdict": HONORE,
         "params_motif": {"mesures": nb_effectifs,
                          "debut": fr(eff_debut), "fin": fr(eff_fin)}},
        {"objectif": "obj2", "i18n": "i6", "verdict": HONORE},
        {"objectif": "obj2", "i18n": "i7", "verdict": HONORE},
        {"objectif": "obj2", "i18n": "i8", "verdict": PARTIEL},

        {"objectif": "obj3", "i18n": "i9", "verdict": HONORE},
        {"objectif": "obj4", "i18n": "i10", "verdict": HONORE},
        {"objectif": "obj5", "i18n": "i11", "verdict": HONORE},
        {"objectif": "obj5", "i18n": "i12", "verdict": HONORE},
        {"objectif": "obj5", "i18n": "i13", "verdict": IMPOSSIBLE},
        {"objectif": "obj6", "i18n": "i14", "verdict": HONORE},
    ]

    # Résolution des textes : la vue reçoit des chaînes prêtes à afficher.
    lignes = [
        {
            "objectif": tr(entree["objectif"]),
            "indicateur": tr(entree["i18n"] + "_indicateur"),
            "verdict": entree["verdict"],
            "source": tr(entree["i18n"] + "_source",
                         entree.get("params_source")),
            "motif": tr(entree["i18n"] + "_motif", entree.get("params_motif")),
        }
        for entree in lignes
    ]

    compte = {
        HONORE: sum(1 for l in lignes if l["verdict"] == HONORE),
        PARTIEL: sum(1 for l in lignes if l["verdict"] == PARTIEL),
        IMPOSSIBLE: sum(1 for l in lignes if l["verdict"] == IMPOSSIBLE),
    }

    return {"lignes": lignes, "compte": compte, "total": len(lignes),
            "ecart": ecart}


def localise_indicateurs(brut):
    """Où chaque indicateur sensible se trouve réellement dans le corpus.

    Garde-fou du tableau d'audit : celui-ci affirme des présences et des
    absences, et une affirmation non vérifiée vieillit mal. Cette fonction
    balaie les 8 fichiers — en-têtes de colonnes ET intitulés de séries — et
    renvoie ce qu'elle trouve. Une entrée vide vaut absence confirmée.

    C'est ce contrôle qui a révélé que les indicateurs de l'objectif n°2,
    déclarés introuvables tant que le corpus comptait huit ressources, sont
    tous portés par la neuvième.
    """

    motifs = {
        "Féminisation": r"sexe|genre|femme|feminin|feminite|fille|female|gender",
        "Effectifs étudiants": r"effectif|inscrit|eleve|apprenant|etudiants inscrits",
        "Personnel enseignant": r"enseignant|professeur|formateur|teacher",
        "Filière / discipline": r"filiere|discipline|specialite|scientifique|science",
    }

    return {
        libelle: _cherche(brut, motif)
        for libelle, motif in motifs.items()
    }
