"""Fiche par ressource — décrite AVANT nettoyage.

Ce que chaque fiche relève vient de la lecture RÉELLE des fichiers, jamais
d'une supposition : volumétrie brute, granularité la plus fine, période,
format, pièges rencontrés — et surtout **ce que la ressource ne permet pas**.

Ce dernier champ est le plus utile du tableau de bord : c'est lui qui empêche
d'attendre du corpus ce qu'il ne contient pas.
"""

from socle.audit import profil_fichier

from utils.data import bruts, poids

# Ce qui ne se calcule pas — relevé à la main en ouvrant les fichiers.
# Les libellés sont des CLÉS i18n, jamais des phrases : la vue les traduit.
FICHES = {
    "cantons": {
        "code": "ISRI-TG",
        "granularite": "canton",
        "periode": "2016-2023",
        "format": "geo",
        "charge": True,
    },
    "tde": {
        "code": "DCEF-TG",
        "granularite": "point",
        "periode": "non_date",
        "format": "large",
        "charge": True,
    },
    "tde_dictionnaire": {
        "code": "DCEF-TG",
        "granularite": "sans_objet",
        "periode": "non_date",
        "format": "dictionnaire",
        "charge": True,
    },
    "coso": {
        "code": "PCIAEPH-TG",
        "granularite": "point",
        "periode": "2023-2026",
        "format": "large",
        "charge": True,
    },
    "coso_geo": {
        "code": "PCIAEPH-TG",
        "granularite": "point",
        "periode": "2023-2026",
        "format": "geo",
        "charge": True,
    },
    "ventes": {
        "code": "DVECA-TG",
        "granularite": "national",
        "periode": "2018-2022",
        "format": "long",
        "charge": True,
    },
    "population": {
        "code": "DPSSA-TG",
        "granularite": "heterogene",
        "periode": "2010",
        "format": "long",
        "charge": True,
    },
}

# Les trois ressources CITÉES et non chargées, avec la raison chiffrée.
# Les taire donnerait l'impression d'un corpus plus mince qu'il n'est.
CITEES = {
    "fri_grid_1km": {"code": "ISRI-TG", "entites": 57_738, "granularite": "grille_1km"},
    "fri_grid_500m": {"code": "ISRI-TG", "entites": 228_953, "granularite": "grille_500m"},
    "fsi_raster": {"code": "ISRI-TG", "entites": None, "granularite": "pixel_30m"},
    "fsi_raster_zip": {"code": "ISRI-TG", "entites": None, "granularite": "pixel_30m"},
}


def profils():
    """Les fiches, complétées par la volumétrie mesurée sur le fichier BRUT."""

    corpus = bruts()
    tailles = poids()

    fiches = []

    for cle, fiche in FICHES.items():
        if cle not in corpus:
            continue

        cadre = corpus[cle]
        mesure = profil_fichier(
            cadre.drop(columns="geometry") if "geometry" in cadre.columns else cadre
        )

        fiches.append({**fiche, "cle": cle, "octets": tailles.get(cle, 0), **mesure})

    return fiches


def citees():
    """Les ressources non chargées, avec leur poids réel et leur présence.

    `presente` est faux quand le fichier n'est pas là. L'archive livrée écarte
    les plus lourdes — deux cent vingt-trois mégaoctets que rien n'ouvre — et
    sans ce drapeau la vue les annonçait à « 0 Mo », ce qui se lit comme un
    fichier vide plutôt que comme un fichier absent. Un poids nul est une
    mesure ; une absence est une autre chose, et elle se dit.
    """

    tailles = poids()

    return [
        {**fiche, "cle": cle, "octets": tailles.get(cle, 0),
         "presente": tailles.get(cle, 0) > 0}
        for cle, fiche in CITEES.items()
    ]


def doublon_raster():
    """Le raster est livré DEUX fois : en `.tif` et zippé.

    Constat de volumétrie, pas de contenu : les deux pèsent 82 537 919 octets,
    le zip ne contenant qu'une entrée du même nom et de la même taille. Le
    signaler évite de croire à deux ressources là où il n'y en a qu'une.
    """

    tailles = poids()
    tif, zippe = tailles.get("fsi_raster", 0), tailles.get("fsi_raster_zip", 0)

    return {
        "octets_tif": tif,
        "octets_zip": zippe,
        "identique": tif > 0 and abs(tif - zippe) / tif < 0.05,
    }
