"""Les barres de filtres de CE défi — leurs champs et leurs libellés.

Le socle fournit la mécanique (`socle.ui.filters`) : la grille à deux unités,
le lien parent-enfant, le décompte des mesures survivantes. Il ignore
volontairement quelles colonnes ce corpus porte — c'est ce qui lui permet de
servir le défi suivant.

Ce fichier fait la jonction, et il la fait UNE fois. Les clés de session sont
délibérément **partagées** entre les vues qui portent la même matière :
`filtre_region` est le même sur le risque, le parc d'ouvrages et les
croisements, si bien qu'une région choisie une fois suit l'utilisateur d'une
page à l'autre.

Un piège propre à ce corpus : les trois jeux n'ont pas les mêmes régions.
Le référentiel en a 5, le parc TdE 3 (dont 97 % en Maritime), le COSO 3 autres
(au Nord). Chaque barre propose donc les modalités **du jeu qu'elle cadre**,
jamais une liste unifiée qui laisserait choisir une région où le jeu n'a rien.
"""

from socle.ui import filters
from socle.i18n.traduction import t


def _spec(colonne, cle, libelle, placeholder, parent=None, aide=None):
    spec = {"colonne": colonne, "cle": cle, "libelle": libelle,
            "placeholder": placeholder}

    if parent:
        spec["parent"] = parent
    if aide:
        spec["aide"] = aide

    return spec


def territoriale(cadre, avec_commune=False, reliquat=True):
    """Barre territoriale — région → préfecture → commune, liées en chaîne.

    Choisir une région restreint la liste des préfectures à celles qu'elle
    contient, et ainsi de suite. Sans ce lien, on peut composer une sélection
    vide (« Savanes » + « Golfe ») et croire à un trou dans les données.
    """

    tf, tc = t("filtres"), t("commun")

    champs = [
        _spec("region", "filtre_region", tf("region"), tc("toutes")),
        _spec("prefecture", "filtre_prefecture", tf("prefecture"), tc("toutes"),
              parent="filtre_region", aide=tf("restreint_au_parent")),
    ]

    if avec_commune:
        champs.append(
            _spec("commune", "filtre_commune", tf("commune"), tc("toutes"),
                  parent="filtre_prefecture", aide=tf("restreint_au_parent"))
        )

    return filters.territoriale(cadre, champs=champs, reliquat=reliquat)


def zone_territoriale(cadre, cle="affiche"):
    """La barre territoriale, posée dans la zone « Filtres » du socle.

    Les clés de session restent celles des autres vues : une région choisie
    ici suit l'utilisateur jusqu'au tableau de bord complet, et le bouton de
    remise à zéro les vide toutes les deux.
    """

    tf, tc = t("filtres"), t("commun")
    cles = ["filtre_region", "filtre_prefecture"]

    # Aucun sous-titre : une zone nommée « Filtres » n'a pas besoin qu'on
    # explique ce que fait un filtre.
    with filters.zone(cle=cle, titre=tf("zone_titre"),
                      cles_session=cles, libelle_reset=tc("reinitialiser")):
        # Colonne de 62 % : pas de colonne d'appui, elle se replierait.
        return territoriale(cadre, reliquat=False)


def parc_tde(cadre):
    """Barre du parc TdE — territoire plus nature de l'ouvrage."""

    tf, tc = t("filtres"), t("commun")

    return filters.territoriale(cadre, champs=[
        _spec("region", "filtre_region", tf("region"), tc("toutes")),
        _spec("prefecture", "filtre_prefecture", tf("prefecture"), tc("toutes"),
              parent="filtre_region", aide=tf("restreint_au_parent")),
        _spec("canton", "filtre_canton", tf("canton"), tc("tous"),
              parent="filtre_prefecture", aide=tf("restreint_au_parent")),
        _spec("nature", "filtre_nature", tf("nature"), tc("toutes")),
    ])


def parc_coso(cadre, avec_annee=True):
    """Barre des microprojets COSO — territoire, type d'ouvrage, travaux.

    L'intervalle porte sur l'année d'ACHÈVEMENT des travaux. À pleine
    amplitude il ne filtre rien : les ouvrages dont la date manque restent
    comptés, sinon l'ouverture de la page amputerait le parc sans que
    personne n'ait rien demandé.
    """

    tf, tc = t("filtres"), t("commun")

    champs = [
        _spec("region", "filtre_region", tf("region"), tc("toutes")),
        _spec("prefecture", "filtre_prefecture", tf("prefecture"), tc("toutes"),
              parent="filtre_region", aide=tf("restreint_au_parent")),
        _spec("type_ouvrage", "filtre_type", tf("type_ouvrage"), tc("tous")),
        _spec("travaux", "filtre_travaux", tf("travaux"), tc("tous")),
    ]

    intervalle = None

    if avec_annee and cadre["annee_achevement"].notna().any():
        intervalle = {
            "colonne": "annee_achevement",
            "cle": "filtre_annee",
            "libelle": tf("annee_achevement"),
            "note": lambda debut, fin, nombre: tf("intervalle_exclut", {
                "debut": debut, "fin": fin, "nombre": nombre,
                "champ": tf("annee_achevement"),
            }),
        }

    return filters.territoriale(cadre, champs=champs, intervalle=intervalle)


def periode(series, cle, aide=None, extras=None):
    """Barre des séries annuelles nationales.

    Injecte les deux libellés que le socle ne peut pas connaître : le titre du
    curseur et l'amorce du décompte (« Mesures retenues : »).
    """

    tf = t("filtres")

    return filters.periode(
        series, cle,
        libelle=tf("periode"),
        libelle_mesures=tf("mesures_retenues"),
        aide=aide,
        extras=extras,
    )
