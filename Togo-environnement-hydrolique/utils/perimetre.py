"""Audit de périmètre — les cinq objectifs de l'énoncé, verdict CALCULÉ.

Ce module ne raconte rien : il **compte**. Chaque verdict d'indisponibilité
s'établit en cherchant le champ dans tous les fichiers BRUTS — en-têtes **et**
valeurs des colonnes qui nomment des séries — jamais de mémoire.

Le garde-fou vaut ici plus qu'ailleurs : l'objectif n°2 réclame les taux de
fonctionnalité, et l'affirmation « c'est introuvable » serait invérifiable si
elle n'était pas adossée à un balayage. Elle l'est.

Les manques se classent par CAUSE, parce qu'ils n'appellent pas la même
recommandation :

    collecte_non_publie  → republier          (coût quasi nul)
    hors_maille          → enquêter à la bonne granularité
    hors_corpus          → produire la donnée
"""

from socle.audit import chercher, ecart_dictionnaire

from utils.data import bruts, datasets

HONORE, PARTIEL, IMPOSSIBLE = "honore", "partiel", "impossible"

COLLECTE_NON_PUBLIE = "collecte_non_publie"
HORS_MAILLE = "hors_maille"
HORS_CORPUS = "hors_corpus"


# Un motif par notion cherchée. Normalisés : minuscules sans accents.
MOTIFS = {
    "fonctionnalite": r"fonctionn|functional|operationnel",
    "panne": r"panne|hors.?service|breakdown|broken",
    "abandon": r"abandon|desaffect|disused",
    "mise_en_service": r"mise.?en.?service|commissioning",
    "debit": r"debit|flow.?rate",
    "profondeur": r"profondeur|depth",
    "population": r"population|habitant|pop\b",
    "risque_inondation": r"fri|flood|inondation|risque",
    "maintenance": r"maintenance|entretien",
}


def preuves():
    """Où chaque notion apparaît dans le corpus brut. Vide = introuvable."""

    corpus = bruts()

    # Les DataFrames géographiques passent sans leur géométrie : la colonne
    # ne porte aucun nom d'indicateur et son balayage coûterait cher.
    plats = {
        nom: (cadre.drop(columns="geometry") if "geometry" in cadre.columns else cadre)
        for nom, cadre in corpus.items()
    }

    return {notion: chercher(plats, motif) for notion, motif in MOTIFS.items()}


def ecart_publication():
    """Le dictionnaire TdE face au fichier publié.

    33 champs décrits, 8 publiés. C'est le constat central du travail : la
    donnée de fonctionnement des ouvrages EXISTE — elle est décrite, donc
    collectée — et n'est simplement pas diffusée.
    """

    corpus = bruts()

    return ecart_dictionnaire(
        corpus["tde_dictionnaire"], corpus["tde"], "Nom du champ",
        familles={
            "fonctionnement": r"fonctionn|etat",
            "capacite": r"debit|profondeur|volume",
            "responsabilite": r"societe|responsable|maintenance|operation",
            "tracabilite": r"date|id\b|serie",
        },
    )


def audit():
    """Les cinq objectifs, chacun avec son verdict et sa preuve.

    Aucun verdict n'est écrit à la main : chacun découle de `preuves()` ou
    d'un décompte sur les jeux nettoyés.
    """

    p = preuves()
    data = datasets()
    ecart = ecart_publication()

    cantons, tde, coso = data["cantons"], data["tde"], data["coso"]

    cles_equipees = set(tde["cle_canton"]) | set(coso["cle_canton"])
    couverts = int(cantons["cle_canton"].isin(cles_equipees).sum())

    fonctionnement_publie = bool(p["fonctionnalite"] or p["panne"] or p["abandon"])

    return [
        {
            "cle": "obj1",
            "verdict": PARTIEL,
            "cause": COLLECTE_NON_PUBLIE,
            "mesures": {
                "ouvrages": int(len(tde) + len(coso)),
                "situes": int(tde["lat"].notna().sum() + coso["situe"].sum()),
                "parcs": 2,
                "regions_tde": int(tde["region"].nunique()),
                "regions_coso": int(coso["region"].nunique()),
            },
            "preuve": p["fonctionnalite"],
        },
        {
            "cle": "obj2",
            "verdict": HONORE if fonctionnement_publie else IMPOSSIBLE,
            "cause": COLLECTE_NON_PUBLIE,
            "mesures": {
                "decrits": ecart["decrits"],
                "publies": ecart["publies"],
                "absents": ecart["absents"],
                "part_publiee": ecart["part_publiee"],
                "champs_fonctionnement": len(ecart["familles"]["fonctionnement"]),
            },
            "preuve": p["fonctionnalite"] + p["panne"] + p["abandon"],
        },
        {
            "cle": "obj3",
            "verdict": HONORE,
            "cause": None,
            "mesures": {
                "cantons": int(len(cantons)),
                "population": float(cantons["population"].sum()),
                "cantons_equipes": couverts,
            },
            "preuve": p["population"],
        },
        {
            "cle": "obj4",
            "verdict": HONORE,
            "cause": None,
            "mesures": {
                "cantons": int(len(cantons)),
                "ouvrages_rattaches": int(
                    tde["cle_canton"].isin(set(cantons["cle_canton"])).sum()
                    + coso["cle_canton"].isin(set(cantons["cle_canton"])).sum()
                ),
                "cantons_croises": couverts,
            },
            "preuve": p["risque_inondation"],
        },
        {
            "cle": "obj5",
            "verdict": HONORE,
            "cause": None,
            "mesures": {
                "sans_plan": int((~coso["plan_maintenance"]).sum()),
                "cantons_sans_ouvrage": int(len(cantons)) - couverts,
                "debit_connu": int(coso["debit"].notna().sum()),
            },
            "preuve": p["maintenance"],
        },
    ]


def compte():
    """Combien d'objectifs par verdict — le chiffre affiché en tête de vue."""

    resultats = audit()

    return {
        verdict: sum(1 for r in resultats if r["verdict"] == verdict)
        for verdict in (HONORE, PARTIEL, IMPOSSIBLE)
    }
