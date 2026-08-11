"""Agrégations métier — une fonction par question du tableau de bord.

C'est ici que se joue la note d'analyse, et nulle part ailleurs : **les vues
ne calculent rien, les graphes ne calculent rien**. Une vue qui ferait un
`groupby` rendrait son chiffre invérifiable et non réutilisable par le rapport
PowerPoint, qui doit produire exactement les mêmes valeurs que l'écran.

Chaque fonction reçoit un cadre DÉJÀ filtré et renvoie soit un DataFrame prêt
à tracer, soit un dictionnaire de faits que la vue se contente d'afficher.
"""

# pyrefly: ignore [missing-import]
import pandas as pd

from utils.clean import NON_RENSEIGNE

# Les cinq composantes normalisées du risque, telles que le producteur les a
# publiées. Les intitulés restent en i18n ; ici on ne manipule que des clés.
COMPOSANTES = {
    "norm_fsi": "alea",
    "norm_pop": "population",
    "norm_urban": "urbanisation",
    "norm_build": "bati",
    "norm_rwi": "vulnerabilite",
}


# ─── Risque d'inondation — les 388 cantons ───────────────────────────────────

def risque_par_region(cantons):
    """Risque médian et population exposée, région par région.

    La MÉDIANE, pas la moyenne : la distribution du risque est très
    dissymétrique (médiane 7,9 pts pour un maximum de 64,5), et une moyenne y
    serait tirée par une poignée de cantons littoraux jusqu'à décrire une
    région qui n'existe pas.
    """

    agrege = (
        cantons.groupby("region", dropna=False)
        .agg(cantons=("canton", "size"),
             risque_median=("risque_pts", "median"),
             risque_max=("risque_pts", "max"),
             population=("population", "sum"))
        .reset_index()
        .sort_values("risque_median", ascending=False)
    )

    return agrege


def cantons_plus_exposes(cantons, nombre=15):
    """Les cantons au risque le plus élevé, avec leur population."""

    colonnes = ["canton", "prefecture", "region", "risque_pts", "population"]

    return (
        cantons[colonnes]
        .sort_values("risque_pts", ascending=False)
        .head(nombre)
        .reset_index(drop=True)
    )


def repartition_par_classe(cantons, bornes, etiquettes):
    """Nombre de cantons et population par classe de risque.

    `bornes` vient de `socle.charts.maps.paliers` : les classes affichées sont
    donc EXACTEMENT celles que la carte a peintes. Les recalculer ici les
    ferait diverger au premier changement de méthode.
    """

    if len(bornes) < 2:
        return pd.DataFrame(columns=["classe", "cantons", "population"])

    classes = pd.cut(cantons["risque_pts"], bins=bornes,
                     labels=etiquettes[:len(bornes) - 1], include_lowest=True)

    agrege = (
        cantons.assign(classe=classes)
        .groupby("classe", observed=False)
        .agg(cantons=("canton", "size"), population=("population", "sum"))
        .reset_index()
    )

    return agrege


def composantes_du_risque(cantons):
    """Poids moyen de chaque composante du risque, sur la sélection.

    Les cinq variables sont déjà normalisées entre 0 et 1 par le producteur :
    elles se comparent donc entre elles, ce qui n'aurait aucun sens sur les
    valeurs brutes (une densité de bâtiments et un indice de richesse ne
    partagent aucune unité).
    """

    lignes = [
        {"composante": nom, "valeur": float(cantons[colonne].mean())}
        for colonne, nom in COMPOSANTES.items()
        if colonne in cantons.columns and cantons[colonne].notna().any()
    ]

    return pd.DataFrame(lignes).sort_values("valeur", ascending=True)


def susceptibilite_vs_risque(cantons):
    """Les deux indices, canton par canton — pour le nuage de points.

    Le FSI mesure la prédisposition PHYSIQUE, le FRI y ajoute l'exposition
    humaine et la vulnérabilité. Les opposer montre les cantons où le risque
    réel s'écarte de l'aléa : c'est là que la population fait la différence.
    """

    colonnes = ["canton", "region", "susceptibilite", "risque_pts", "population"]
    cadre = cantons[colonnes].dropna(subset=["susceptibilite", "risque_pts"])

    return cadre.reset_index(drop=True)


# ─── Parc d'ouvrages ─────────────────────────────────────────────────────────

def _compte(cadre, colonne, nom="ouvrages"):
    """Décompte trié, valeurs absentes CONSERVÉES sous « Non renseigné »."""

    return (
        cadre.groupby(colonne, dropna=False)
        .size().reset_index(name=nom)
        .sort_values(nom, ascending=False)
        .reset_index(drop=True)
    )


def tde_par_nature(tde):
    """Forages, châteaux, et ce que le fichier ne nomme pas.

    Les 8 « Non renseigné » restent comptés : les écarter laisserait croire à
    un parc entièrement identifié, alors que la sentinelle « Nsp » occupe un
    ouvrage sur huit.
    """

    return _compte(tde, "nature")


def tde_par_region(tde):
    return _compte(tde, "region")


def coso_par_type(coso):
    return _compte(coso, "type_ouvrage")


def coso_par_avancement(coso):
    return _compte(coso, "avancement")


def coso_par_region(coso):
    return _compte(coso, "region")


def coso_technique(coso):
    """Profondeur et débit des forages — pour la relation entre les deux.

    Jointure interne implicite : seuls les forages qui portent LES DEUX
    mesures entrent. Le nombre d'observations est renvoyé, parce qu'une
    droite d'ajustement sur 76 points ne dit pas la même chose que sur 218.
    """

    cadre = coso[["localite", "canton", "region", "type_ouvrage",
                  "profondeur", "debit"]].dropna(subset=["profondeur", "debit"])

    return cadre.reset_index(drop=True)


def completude_coso(coso):
    """Ce que le fichier COSO renseigne, champ par champ, en part de lignes.

    Le tableau de bord doit pouvoir dire « le débit n'est connu que pour 36 %
    des ouvrages » avec le chiffre exact, pas avec un adverbe.
    """

    champs = {
        "situe": coso["situe"].sum(),
        "debit": coso["debit"].notna().sum(),
        "profondeur": coso["profondeur"].notna().sum(),
        "population_desservie": coso["population_desservie"].notna().sum(),
        "cout_estime": coso["cout_estime"].notna().sum(),
        "fonds_entretien": coso["fonds_entretien"].notna().sum(),
        "plan_maintenance": int(coso["plan_maintenance"].sum()),
    }

    lignes = [
        {"champ": nom, "renseignes": int(n), "total": len(coso),
         "part": 100 * int(n) / len(coso) if len(coso) else 0}
        for nom, n in champs.items()
    ]

    return pd.DataFrame(lignes).sort_values("part", ascending=True)


def maintenance(coso):
    """Présence d'un plan de maintenance — la variable de l'objectif n°5."""

    cadre = coso.assign(
        plan=coso["plan_maintenance"].map({True: "avec", False: "sans"})
    )

    return _compte(cadre, "plan")


def couverture(cantons, tde, coso):
    """Chaque canton du référentiel, avec le nombre d'ouvrages recensés.

    Jointure GAUCHE, à rebours des recettes qui joignent en interne : ici les
    ZÉROS sont la donnée. La carte de l'angle mort n'existe que si les 330
    cantons sans ouvrage restent dans le cadre — une jointure interne les
    ferait disparaître, et la carte montrerait un pays entièrement équipé.

    `couvert` est un indicateur 0/1 pour la choroplèthe binaire : la valeur
    brute d'`ouvrages` ne se cartographie pas en classes, 85 % des cantons
    étant à zéro (des quantiles dégénéreraient en une classe unique).
    """

    ouvrages = (
        pd.concat([tde[["cle_canton"]], coso[["cle_canton"]]])
        .groupby("cle_canton").size().rename("ouvrages").reset_index()
    )

    cadre = cantons.merge(ouvrages, on="cle_canton", how="left")
    cadre["ouvrages"] = cadre["ouvrages"].fillna(0).astype(int)
    cadre["couvert"] = (cadre["ouvrages"] > 0).astype(int)

    return cadre


# ─── Ventes d'eau — national ─────────────────────────────────────────────────

def ventes_series(ventes):
    """Une série annuelle par catégorie d'abonnés, pour les courbes.

    Les catégories n'apparaissent pas toutes chaque année : 5 mesures en 2018,
    8 en 2022. Aucune valeur n'est complétée — une courbe interrompue dit
    quelque chose de vrai sur la collecte, une courbe recousue ment.
    """

    series = []

    for categorie, groupe in ventes.groupby("categorie"):
        trie = groupe.sort_values("annee")
        series.append({
            "name": categorie,
            "x": trie["annee"].astype(int).tolist(),
            "y": trie["volume_m3"].tolist(),
        })

    return sorted(series, key=lambda s: -sum(s["y"]))


def ventes_par_annee(ventes):
    """Volume total et nombre de catégories renseignées, par millésime."""

    return (
        ventes.groupby("annee")
        .agg(volume_m3=("volume_m3", "sum"), categories=("categorie", "nunique"))
        .reset_index()
    )


def ventes_derniere_annee(ventes):
    """Répartition par catégorie sur le millésime le plus récent."""

    if ventes.empty:
        return pd.DataFrame(columns=["categorie", "volume_m3"])

    derniere = int(ventes["annee"].max())
    cadre = ventes[ventes["annee"] == derniere][["categorie", "volume_m3"]]

    return cadre.sort_values("volume_m3", ascending=False).reset_index(drop=True)


# ─── Faits de synthèse ───────────────────────────────────────────────────────

def synthese(cantons, tde, coso, ventes):
    """Les chiffres de la vue d'ensemble, calculés une seule fois.

    Volontairement, AUCUN total d'ouvrages « national » n'est produit ici :
    les deux parcs couvrent des territoires disjoints — 65 des 67 ouvrages TdE
    sont en Maritime, les 218 microprojets COSO sont au Nord — et les
    additionner fabriquerait un inventaire qui n'existe pas.
    """

    cles_equipees = set(tde["cle_canton"]) | set(coso["cle_canton"])
    couverts = cantons["cle_canton"].isin(cles_equipees)

    return {
        "cantons": int(len(cantons)),
        "regions": int(cantons["region"].nunique()),
        "population": float(cantons["population"].sum()),
        "risque_median": float(cantons["risque_pts"].median()),
        "risque_max": float(cantons["risque_pts"].max()),
        "canton_le_plus_expose": str(
            cantons.loc[cantons["risque_pts"].idxmax(), "canton"]
        ) if len(cantons) else NON_RENSEIGNE,

        "tde_total": int(len(tde)),
        "tde_regions": int(tde["region"].nunique()),
        "tde_part_maritime": float(
            100 * (tde["region"] == "Maritime").sum() / len(tde)
        ) if len(tde) else 0.0,

        "coso_total": int(len(coso)),
        "coso_situes": int(coso["situe"].sum()),
        "coso_sans_plan": int((~coso["plan_maintenance"]).sum()),
        "coso_part_sans_plan": float(
            100 * (~coso["plan_maintenance"]).sum() / len(coso)
        ) if len(coso) else 0.0,

        "cantons_couverts": int(couverts.sum()),
        "cantons_sans_ouvrage": int((~couverts).sum()),
        "part_sans_ouvrage": float(100 * (~couverts).sum() / len(cantons))
        if len(cantons) else 0.0,

        "ventes_debut": int(ventes["annee"].min()) if len(ventes) else 0,
        "ventes_fin": int(ventes["annee"].max()) if len(ventes) else 0,
        "ventes_volume_dernier": float(
            ventes.loc[ventes["annee"] == ventes["annee"].max(), "volume_m3"].sum()
        ) if len(ventes) else 0.0,
    }
