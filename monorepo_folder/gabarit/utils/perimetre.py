"""Audit de périmètre — ce que l'énoncé demande, ce que les données permettent.

Ce module ne raconte rien : il **compte**. Chaque verdict d'indisponibilité
s'établit en cherchant le champ dans TOUS les fichiers chargés (en-têtes ET
valeurs des colonnes « indicateur »), jamais de mémoire — cf. `socle.audit`.
Sur le pilote, ce contrôle a révélé qu'une neuvième ressource portait les
quatre indicateurs déclarés introuvables.

Les manques se classent par CAUSE, parce qu'ils n'appellent pas la même
recommandation :

    collecté mais non publié      → republier (coût faible)
    inexistant à cette granularité → enquêter ou changer de maille
    nomenclature absente           → produire un référentiel

Chaque indicateur reçoit l'un des trois verdicts, et jamais « à voir ».
"""

from socle.audit import chercher, presence     # noqa: F401

from utils.data import bruts

HONORE = "honore"
PARTIEL = "partiel"
IMPOSSIBLE = "impossible"


# Un motif par indicateur numéroté de l'énoncé. Le motif est une expression
# régulière normalisée (minuscules, sans accents) : cf. `socle.audit.normaliser`.
INDICATEURS = {
    # "1. Nombre de points d'eau par canton": r"point.?d.?eau|forage",
}


def audit():
    """Objectif par objectif : honoré, partiel ou impossible — et la preuve.

    La preuve est la liste des fichiers où le motif a été trouvé : elle
    accompagne le verdict à l'écran, pour qu'un lecteur puisse le contester.
    """

    corpus = bruts()
    resultats = []

    for intitule, motif in INDICATEURS.items():
        traces = chercher(corpus, motif)

        resultats.append({
            "indicateur": intitule,
            "verdict": HONORE if traces else IMPOSSIBLE,
            "traces": traces,
            "fichiers": [t["fichier"] for t in traces],
        })

    return resultats


def compte():
    """Combien d'indicateurs par verdict — le chiffre affiché en tête de vue."""

    resultats = audit()

    return {
        verdict: sum(1 for r in resultats if r["verdict"] == verdict)
        for verdict in (HONORE, PARTIEL, IMPOSSIBLE)
    }
