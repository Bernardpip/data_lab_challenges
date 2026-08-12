"""Géographie du manque — la distance, et non plus le décompte.

Les agrégations de `analytics` répondent à « combien d'ouvrages ». Ce module
répond à « à quelle distance », et ce n'est pas la même question : un canton
équipé de trois forages groupés dans son chef-lieu compte comme couvert, alors
que ses hameaux marchent autant que ceux du canton voisin qui n'a rien.

Trois mesures, du plus simple au plus exigeant :

  · la DISTANCE au point d'eau le plus proche, canton par canton ;
  · la population dans un RAYON de marche, en franchissant les limites ;
  · la CONCENTRATION du parc, pour dire si les points sont groupés ou étalés.

Toutes travaillent en mètres, dans la projection UTM 31N (EPSG:32631) qui
couvre le Togo entier (0°–1,8° E). Mesurer une distance en degrés produirait
une erreur de 11 % entre le nord et le sud du pays — un degré de longitude vaut
111 km à l'équateur et 110 km à la latitude de Dapaong, mais un degré de
latitude et un degré de longitude ne valent pas la même chose, et une distance
euclidienne calculée sur les deux mélange deux unités.
"""

# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import streamlit as st

# Projection métrique du Togo. Le pays tient entièrement dans le fuseau 31
# nord : aucune déformation de bord à corriger.
METRIQUE = 32631

# Rayons de marche, en mètres. 1 km est le seuil de l'ODD 6.1 pour un service
# « élémentaire » (aller-retour et attente sous trente minutes) ; 2,5 km et
# 5 km encadrent ce que la littérature retient comme distance effectivement
# parcourue en milieu rural ouest-africain.
RAYONS = (1000, 2500, 5000)


def _points(*inventaires):
    """Les coordonnées de tous les ouvrages situés, en un seul tableau.

    Les deux parcs sont RÉUNIS : un habitant ne demande pas qui a foré. Les
    lignes sans coordonnées sont écartées ici, et leur nombre remonte par les
    fonctions appelantes — un ouvrage non situé existe, mais il ne peut pas
    entrer dans un calcul de distance.
    """

    morceaux = []

    for cadre in inventaires:
        if cadre is None or not len(cadre):
            continue

        cadre = cadre[["lon", "lat"]].dropna()

        if len(cadre):
            morceaux.append(cadre)

    if not morceaux:
        return np.empty((0, 2))

    return pd.concat(morceaux).to_numpy(dtype=float)


def _projete(lon_lat):
    """Longitudes/latitudes en mètres UTM 31N."""

    if not len(lon_lat):
        return np.empty((0, 2))

    # pyrefly: ignore [missing-import]
    from pyproj import Transformer

    transformeur = Transformer.from_crs(4326, METRIQUE, always_xy=True)
    x, y = transformeur.transform(lon_lat[:, 0], lon_lat[:, 1])

    return np.c_[x, y]


@st.cache_data(show_spinner=False)
def _distances(_cantons, _tde, _coso, cle):
    """Le calcul brut, mis en cache — cf. `distance_au_point_deau`."""

    ouvrages = _projete(_points(_tde, _coso[_coso["situe"]]))

    if not len(ouvrages):
        return pd.DataFrame(columns=["canton", "distance_km"])

    # Le POINT REPRÉSENTATIF, non le centroïde : sur un canton en croissant —
    # les cantons lagunaires du sud en sont —, le centroïde tombe hors du
    # polygone, et la distance mesurée partirait d'un lieu où personne
    # n'habite.
    metrique = _cantons.to_crs(METRIQUE)
    ancres = metrique.geometry.representative_point()
    depuis = np.c_[ancres.x.to_numpy(), ancres.y.to_numpy()]

    # pyrefly: ignore [missing-import]
    from scipy.spatial import cKDTree

    distances, _index = cKDTree(ouvrages).query(depuis, k=1)

    return pd.DataFrame({
        "canton": _cantons["canton"].to_numpy(),
        "cle_canton": _cantons["cle_canton"].to_numpy(),
        "prefecture": _cantons["prefecture"].to_numpy(),
        "region": _cantons["region"].to_numpy(),
        "population": _cantons["population"].to_numpy(),
        "risque_pts": _cantons["risque_pts"].to_numpy(),
        "distance_km": distances / 1000,
    })


def distance_au_point_deau(cantons, tde, coso):
    """Distance du canton au point d'eau le plus proche, en kilomètres.

    La distance ignore les LIMITES administratives : le point le plus proche
    peut appartenir au canton voisin, et c'est le seul calcul honnête — l'eau
    ne s'arrête pas à une frontière que le marcheur ne voit pas.

    Ce que la mesure suppose, et qu'il faut dire : elle part d'un point unique
    par canton. Un canton de 50 km de long est réduit à son milieu, et la
    distance qu'on lui prête vaut pour ce milieu, pas pour ses écarts. Elle
    donne donc un ORDRE DE GRANDEUR comparable entre cantons, pas un temps de
    marche individuel.
    """

    cle = (len(cantons), len(tde), len(coso),
           float(cantons["population"].sum()))

    return _distances(cantons, tde, coso, cle)


def deserts(cantons, tde, coso, seuil_km=10.0):
    """Les cantons dont le point d'eau le plus proche est au-delà du seuil.

    10 km par défaut : quatre fois le rayon de marche communément retenu, et
    l'ordre de grandeur au-delà duquel la corvée d'eau cesse d'être quotidienne
    pour devenir une expédition. Le seuil est un ARGUMENT, pas une constante
    cachée — un lecteur qui le juge trop généreux doit pouvoir le déplacer.
    """

    cadre = distance_au_point_deau(cantons, tde, coso)
    loin = cadre[cadre["distance_km"] >= seuil_km]

    return {
        "cadre": cadre,
        "cantons": loin.sort_values("distance_km", ascending=False)
                       .reset_index(drop=True),
        "population": float(loin["population"].sum()),
        "part_cantons": 100 * len(loin) / len(cadre) if len(cadre) else 0.0,
        "part_population": (
            100 * loin["population"].sum() / cadre["population"].sum()
            if cadre["population"].sum() else 0.0
        ),
        "mediane_km": float(cadre["distance_km"].median()) if len(cadre) else 0.0,
        "seuil_km": seuil_km,
    }


@st.cache_data(show_spinner=False)
def _rayons(_cantons, _tde, _coso, cle, rayons):
    """Population dans chaque rayon — cf. `rayons_de_marche`."""

    ouvrages = _points(_tde, _coso[_coso["situe"]])

    if not len(ouvrages):
        return pd.DataFrame(columns=["rayon_km", "population", "part"])

    # pyrefly: ignore [missing-import]
    import geopandas as gpd
    # pyrefly: ignore [missing-import]
    from shapely.geometry import MultiPoint

    metrique = _cantons.to_crs(METRIQUE)
    semis = gpd.GeoSeries([MultiPoint(ouvrages)], crs=4326).to_crs(METRIQUE)
    total = float(metrique["population"].sum())

    lignes = []

    for rayon in rayons:
        atteint = semis.buffer(rayon).union_all()

        # L'aire de l'INTERSECTION rapportée à celle du canton, multipliée par
        # sa population : c'est une hypothèse de densité UNIFORME à l'intérieur
        # du canton, et elle est fausse — les gens se groupent, souvent là où
        # est l'eau. Elle sous-estime donc probablement la population couverte,
        # et le sens du biais est connu, ce qui vaut mieux qu'un chiffre sans
        # hypothèse.
        part_aire = (
            metrique.geometry.intersection(atteint).area
            / metrique.geometry.area.replace(0, np.nan)
        ).fillna(0).clip(0, 1)

        couverte = float((part_aire * metrique["population"]).sum())

        lignes.append({
            "rayon_km": rayon / 1000,
            "population": couverte,
            "part": 100 * couverte / total if total else 0.0,
        })

    return pd.DataFrame(lignes)


def rayons_de_marche(cantons, tde, coso, rayons=RAYONS):
    """Population vivant à moins de 1, 2,5 et 5 km d'un point d'eau.

    Une APPROXIMATION ARÉALE, et elle est assumée : le corpus ne publie aucune
    grille de population, seulement un total par canton. Faute de mieux, la
    part d'un canton couverte par les rayons est prise comme la part de sa
    population — ce qui revient à supposer les habitants répartis uniformément.

    Le chiffre qui en sort ne doit pas être lu comme un taux d'accès. Il donne
    l'ORDRE DE GRANDEUR de ce que 285 points d'eau peuvent desservir dans un
    pays de 6,2 millions d'habitants, et cet ordre de grandeur suffit à la
    conclusion — il est petit.
    """

    cle = (len(cantons), len(tde), len(coso),
           float(cantons["population"].sum()))

    return _rayons(cantons, tde, coso, cle, tuple(rayons))


def concentration(cantons, tde, coso):
    """Les ouvrages sont-ils groupés, étalés, ou posés au hasard ?

    Indice de Clark-Evans : distance moyenne observée entre plus proches
    voisins, rapportée à celle qu'on attendrait d'un semis aléatoire de même
    densité. Sous 1, les points sont AGRÉGÉS ; à 1, indiscernables du hasard ;
    au-dessus, régulièrement espacés.

    Pourquoi le mesurer plutôt que le montrer : « les forages sont concentrés
    autour de Lomé » est une impression de lecture de carte, et une impression
    ne se conteste pas. Un R de 0,3 avec son écart réduit se conteste, se
    reproduit, et se compare entre les deux inventaires — ce qui révèle qu'ils
    ne sont pas concentrés de la même façon.

    L'aire de référence est celle du PÉRIMÈTRE affiché, non celle du pays : à
    périmètre filtré, comparer un semis local à la densité nationale déclarerait
    agrégé tout ce qui est simplement local.
    """

    metrique = cantons.to_crs(METRIQUE)
    aire = float(metrique.geometry.area.sum())

    resultats = []

    for cle, cadre in (("tde", tde), ("coso", coso[coso["situe"]]),
                       ("ensemble", pd.concat([tde, coso[coso["situe"]]]))):
        semis = _projete(_points(cadre))
        n = len(semis)

        # Trois points suffisent à un plus proche voisin, mais l'écart réduit
        # de Clark-Evans n'a de sens qu'à partir d'une poignée d'observations.
        if n < 5 or aire <= 0:
            continue

        # pyrefly: ignore [missing-import]
        from scipy.spatial import cKDTree

        # k=2 : le premier voisin d'un point est lui-même.
        distances, _ = cKDTree(semis).query(semis, k=2)
        observee = float(distances[:, 1].mean())

        densite = n / aire
        attendue = 0.5 / np.sqrt(densite)
        erreur = 0.26136 / np.sqrt(n * densite)

        resultats.append({
            "inventaire": cle,
            "ouvrages": n,
            "voisin_observe_km": observee / 1000,
            "voisin_attendu_km": attendue / 1000,
            "R": observee / attendue if attendue else float("nan"),
            "z": (observee - attendue) / erreur if erreur else float("nan"),
        })

    return pd.DataFrame(resultats)
