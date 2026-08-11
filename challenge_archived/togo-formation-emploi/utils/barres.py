"""Les barres de filtres de CE défi — leurs champs et leurs libellés.

Le socle fournit la mécanique (`socle.ui.filters`) : la grille à deux unités,
le lien parent-enfant, le décompte des mesures survivantes. Il ignore
volontairement quelles colonnes ce corpus porte et comment elles se nomment —
c'est ce qui lui permet de servir le défi suivant.

Ce fichier fait la jonction, et il la fait UNE fois : les quatre vues qui
filtrent les établissements techniques appellent toutes `territoriale()`, avec
les mêmes clés de session. C'est ce partage qui fait qu'une région choisie sur
la Vue d'ensemble suit l'utilisateur jusqu'aux Recommandations.

Avant l'extraction du socle, ces libellés étaient écrits en dur dans
`components/filters.py` : « Région », « Préfecture », « Filière », « Statut »
ne se traduisaient pas, et la barre ne pouvait servir qu'à ce corpus-ci.
"""

from socle.ui import filters
from socle.i18n.traduction import t


def territoriale(formations):
    """Barre du fichier des établissements techniques.

    Région et préfecture sont LIÉES (`parent`) : choisir une région restreint
    la liste des préfectures à celles qu'elle contient. Sans ce lien, on peut
    composer une sélection vide (« Savanes » + « Golfe ») et croire à un bug
    de données.
    """

    tf, tc = t("filtres"), t("commun")

    return filters.territoriale(
        formations,
        champs=[
            {"colonne": "region", "cle": "filtre_region",
             "libelle": tf("region"), "placeholder": tc("toutes")},

            {"colonne": "prefecture", "cle": "filtre_prefecture",
             "libelle": tf("prefecture"), "placeholder": tc("toutes"),
             "parent": "filtre_region", "aide": tf("aide_prefecture")},

            {"colonne": "categorie", "cle": "filtre_categorie",
             "libelle": tf("filiere"), "placeholder": tc("toutes")},

            {"colonne": "statut", "cle": "filtre_statut",
             "libelle": tf("statut"), "placeholder": tc("tous")},
        ],
        intervalle={
            "colonne": "annee_creation", "cle": "filtre_annee",
            "libelle": tf("annees"),
            # Resserrer l'intervalle écarte mécaniquement les établissements
            # sans année de création. Le dire, plutôt que de laisser croire à
            # un écart de couverture territoriale.
            "note": lambda debut, fin, nombre: tf("annees_exclues", {
                "debut": debut, "fin": fin, "nombre": nombre,
            }),
        },
    )


def periode(series, cle, aide=None, extras=None):
    """Barre des séries nationales annuelles.

    Injecte les deux libellés que le socle ne peut pas connaître : le titre du
    curseur et l'amorce du décompte (« Mesures retenues : »). Le pilote les
    portait en dur dans le socle, ce qui laissait « Période » en français dans
    la version anglaise.
    """

    tf = t("filtres")

    return filters.periode(
        series, cle,
        libelle=tf("periode"),
        libelle_mesures=tf("mesures_retenues"),
        aide=aide,
        extras=extras,
    )
