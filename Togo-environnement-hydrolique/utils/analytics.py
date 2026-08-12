"""Agrégations métier — une fonction par question du tableau de bord.

C'est ici que se joue la note d'analyse, et nulle part ailleurs : **les vues
ne calculent rien, les graphes ne calculent rien**. Une vue qui ferait un
`groupby` rendrait son chiffre invérifiable et non réutilisable par le rapport
PowerPoint, qui doit produire exactement les mêmes valeurs que l'écran.

Chaque fonction reçoit un cadre DÉJÀ filtré et renvoie soit un DataFrame prêt
à tracer, soit un dictionnaire de faits que la vue se contente d'afficher.
"""

# pyrefly: ignore [missing-import]
import numpy as np
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


# ─── Classes officielles du producteur ───────────────────────────────────────

# Seuils lus sur la PLANCHE du ministère (`fri-cantons.pdf`), et introuvables
# ailleurs : ni le GeoPackage ni la note ne les portent. La planche est une
# image sans un caractère de texte — il a fallu la rendre et la lire.
#
# Ils sont FIXES, là où le tableau de bord classait en quintiles. Les deux
# lectures sont justes et ne répondent pas à la même question : les quintiles
# donnent un CLASSEMENT (quels cantons sont les pires), les seuils donnent une
# INTENSITÉ (à partir de quand le risque est élevé). Publier la nôtre sans
# offrir la sienne exposait le lecteur à croire à une erreur en comparant.
SEUILS_OFFICIELS = [0.01, 0.10, 0.17, 0.29, 0.44, 0.65]
CLASSES_OFFICIELLES = ["tres_faible", "faible", "moyen", "eleve", "tres_eleve"]

# Les deux classes hautes : c'est le périmètre que le rapport appelle
# « exposé », et il vaut mieux le nommer une fois que le réécrire cinq fois.
CLASSES_HAUTES = ["eleve", "tres_eleve"]


def classer_officiel(cantons):
    """Ajoute la classe officielle de risque à chaque canton.

    Le FRI est stocké en POINTS (×100) par le nettoyage, quand les seuils de
    la planche sont exprimés dans l'unité d'origine : la division rétablit
    l'échelle du producteur plutôt que de multiplier ses bornes, pour que les
    nombres écrits ici soient exactement ceux que la planche imprime.
    """

    classes = pd.cut(
        cantons["risque_pts"] / 100,
        bins=SEUILS_OFFICIELS, labels=CLASSES_OFFICIELLES, include_lowest=True,
    )

    return cantons.assign(classe_officielle=classes)


def population_par_classe(cantons):
    """Cantons et population par classe officielle — le chiffre du rapport.

    C'est ici que se lit le fait central du défi : 4 % des cantons abritent
    35 % de la population. Un décompte de cantons seul le manquerait — il
    donnerait 17 sur 388 et laisserait croire à un problème marginal.
    """

    cadre = classer_officiel(cantons)

    agrege = (
        cadre.groupby("classe_officielle", observed=False)
        .agg(cantons=("canton", "size"), population=("population", "sum"))
        .reset_index()
    )
    total = agrege["population"].sum()
    agrege["part_population"] = 100 * agrege["population"] / total if total else 0

    return agrege


def matrice_risque_equipement(cantons, tde, coso):
    """Croise la classe de risque et la présence d'un ouvrage — objectif n°4.

    Jointure par les CLÉS d'ouvrages, sans jamais joindre les tables : un
    canton compte comme équipé dès qu'un ouvrage s'y rattache, quel que soit
    l'inventaire, et un canton sans ouvrage doit rester dans le cadre — c'est
    lui que la matrice cherche.
    """

    equipes = set(tde["cle_canton"]) | set(coso["cle_canton"])
    cadre = classer_officiel(cantons)
    cadre = cadre.assign(equipe=cadre["cle_canton"].isin(equipes))

    agrege = (
        cadre.groupby("classe_officielle", observed=False)
        .agg(cantons=("canton", "size"), equipes=("equipe", "sum"),
             population=("population", "sum"))
        .reset_index()
    )
    agrege["sans_ouvrage"] = agrege["cantons"] - agrege["equipes"]
    agrege["part_equipee"] = (
        100 * agrege["equipes"] / agrege["cantons"].where(agrege["cantons"] > 0)
    ).fillna(0)

    return agrege


def cantons_prioritaires(cantons, tde, coso):
    """Les cantons exposés ET dépourvus d'ouvrage recensé — la recommandation.

    La recommandation du défi n'est pas une phrase, c'est cette liste. Elle
    croise les trois jeux et ne retient que l'intersection des deux critères
    qu'un décideur peut agir : le risque, qu'il subit, et l'absence d'ouvrage,
    qu'il peut corriger.

    Triée par population : à risque égal, le canton le plus peuplé passe
    d'abord — c'est le seul arbitrage que les données autorisent.
    """

    equipes = set(tde["cle_canton"]) | set(coso["cle_canton"])
    cadre = classer_officiel(cantons)

    retenus = cadre[
        cadre["classe_officielle"].isin(CLASSES_HAUTES)
        & ~cadre["cle_canton"].isin(equipes)
    ]

    colonnes = ["canton", "prefecture", "region", "risque_pts", "population"]

    return (
        retenus[colonnes]
        .sort_values("population", ascending=False)
        .reset_index(drop=True)
    )


# ─── Ce que le COSO documente de sa propre exécution ─────────────────────────

def delais(coso):
    """Écart entre la fin PRÉVUE et la fin RÉELLE des travaux, en jours.

    Le fichier porte tout le cycle d'un chantier — signature, lancement, fin
    prévue, fin réelle, réceptions technique et provisoire, remise à la
    communauté. C'est un jeu de données de SUIVI, et le tableau de bord n'en
    lisait que l'année d'achèvement.

    Aucune ligne n'est écartée pour un retard aberrant : un chantier livré
    655 jours avant sa date prévue signale une date mal saisie, et c'est une
    information sur la qualité du suivi, pas un point à effacer.
    """

    prevu = pd.to_datetime(coso["expected_end_date"], errors="coerce")
    reel = pd.to_datetime(coso["date_achevement"], errors="coerce")

    return coso.assign(retard_jours=(reel - prevu).dt.days)


# Les intitulés de type du producteur font jusqu'à 64 caractères et PARTAGENT
# leurs 32 premiers : « Forages photovoltaïques dans les communautés… », « …
# dans les établissements scolaires », « … dans les marchés ». Les tronquer
# pour les faire tenir dans un graphe produisait trois libellés IDENTIQUES, et
# plotly, qui range par catégorie, fondait les trois séries en une seule barre.
# On les ramène donc à une clé sur ce qui les DISTINGUE, jamais sur leur début.
MOTIFS_TYPE = [
    ("scolaire", "ecoles"),
    ("maraîch", "maraichage"),
    ("marché", "marches"),
    ("centre communautaire", "centre"),
    ("salle de réunion", "salle"),
    ("communauté", "boisson"),
]


def cle_type_ouvrage(libelle):
    """Clé courte d'un type d'ouvrage COSO, pour l'i18n du défi."""

    texte = str(libelle).lower()

    for motif, cle in MOTIFS_TYPE:
        if motif in texte:
            return cle

    return "autre"


def delais_par_type(coso):
    """Retard médian par type d'ouvrage — la MÉDIANE, jamais la moyenne.

    La distribution des retards porte des valeurs extrêmes des deux côtés
    (−655 à +431 jours) : une moyenne y suivrait les erreurs de saisie plutôt
    que le comportement des chantiers.
    """

    cadre = delais(coso).dropna(subset=["retard_jours"])

    agrege = (
        cadre.assign(cle_type=cadre["type_ouvrage"].map(cle_type_ouvrage))
        .groupby(["cle_type", "type_ouvrage"])
        .agg(ouvrages=("retard_jours", "size"),
             retard_median=("retard_jours", "median"),
             en_retard=("retard_jours", lambda s: int((s > 0).sum())))
        .reset_index()
        .sort_values("retard_median", ascending=True)
    )
    agrege["part_en_retard"] = 100 * agrege["en_retard"] / agrege["ouvrages"]

    return agrege


def chaine_budgetaire(coso):
    """Estimé → contracté → payé, en francs CFA.

    Les trois montants coexistent dans le fichier et ne disent pas la même
    chose : ce qui était prévu, ce qui a été signé après mise en concurrence,
    ce qui a été décaissé. L'écart entre les deux premiers est une marge
    dégagée ; l'écart entre les deux derniers, un dépassement.
    """

    etapes = [
        ("estime", "cout_estime"),
        ("contracte", "contract_amount_work_companies"),
        ("paye", "montant_paye"),
    ]

    return pd.DataFrame([
        {"etape": nom, "montant": float(coso[colonne].sum()),
         "ouvrages": int(coso[colonne].notna().sum())}
        for nom, colonne in etapes if colonne in coso.columns
    ])


def beneficiaires(coso):
    """Bénéficiaires directs, ventilés par sexe.

    Le fichier les compte séparément, ce qui autorise le seul constat de genre
    du corpus. Les deux colonnes sont renseignées ensemble ou pas du tout :
    aucune reconstitution d'un sexe par différence n'est tentée.
    """

    femmes = float(coso["beneficiaires_femmes"].sum())
    hommes = float(coso["beneficiaires_hommes"].sum())
    total = femmes + hommes

    return {
        "femmes": femmes, "hommes": hommes, "total": total,
        "part_femmes": 100 * femmes / total if total else 0.0,
        "renseignes": int(coso["beneficiaires_femmes"].notna().sum()),
    }


def cout_par_beneficiaire(coso):
    """Coût décaissé rapporté aux bénéficiaires directs, ouvrage par ouvrage.

    Le seul ratio du corpus qui rapporte une dépense à une personne — donc le
    seul qui permette de chiffrer ce que coûterait la couverture d'un canton
    de plus. Ne retient que les ouvrages portant LES DEUX mesures : un
    dénominateur nul produirait un infini, et un dénominateur estimé ferait
    passer une hypothèse pour une observation.
    """

    cadre = coso.assign(
        beneficiaires=coso["beneficiaires_femmes"].fillna(0)
        + coso["beneficiaires_hommes"].fillna(0)
    )
    cadre = cadre[(cadre["beneficiaires"] > 0) & cadre["montant_paye"].notna()]
    cadre = cadre.assign(
        cout_beneficiaire=cadre["montant_paye"] / cadre["beneficiaires"]
    )

    colonnes = ["localite", "canton", "region", "type_ouvrage",
                "beneficiaires", "montant_paye", "cout_beneficiaire"]

    return cadre[colonnes].reset_index(drop=True)


def audit_social(coso):
    """Tenue de l'audit social et part des femmes parmi les participants.

    Un audit social est la procédure par laquelle la communauté valide
    l'ouvrage. Son absence n'est pas un manque de donnée : c'est un manque
    d'audit, et les deux se distinguent ici parce que le fichier date ceux qui
    ont eu lieu.
    """

    tenus = coso["number_of_participants_t_in_social_audit"].notna()
    part_femmes = (
        100 * coso["number_of_participants_w_in_social_audit"]
        / coso["number_of_participants_t_in_social_audit"]
    )

    return {
        "tenus": int(tenus.sum()),
        "total": int(len(coso)),
        "part_tenus": 100 * int(tenus.sum()) / len(coso) if len(coso) else 0.0,
        "participants_median": float(
            coso["number_of_participants_t_in_social_audit"].median()
        ),
        "part_femmes_mediane": float(part_femmes.median()),
    }


# ─── Reproductibilité de l'indice publié ─────────────────────────────────────

# Les sept composantes normalisées que le GeoPackage publie à côté du FRI.
COMPOSANTES_FRI = ["norm_fsi", "norm_pop", "norm_rwi", "norm_urban",
                   "norm_build", "norm_dist_basin", "norm_crop"]


def reconstitution_fri(cantons):
    """Le FRI publié est-il reproductible à partir des composantes publiées ?

    La note du producteur annonce « une moyenne géométrique normalisée ». Cette
    fonction met l'affirmation à l'épreuve : elle ajuste plusieurs formes et
    renvoie, pour chacune, la part de variance expliquée.

    Les cantons portant un ZÉRO sur une composante sont ÉCARTÉS des formes
    multiplicatives, et leur nombre est renvoyé. Un zéro annule un produit et
    rend le logarithme indéfini ; le remplacer par une valeur minuscule
    « marche », mais le résultat dépend alors de la valeur choisie — mesuré,
    le R² passait de 0,86 à 0,92 selon qu'on écrivait 1e-9 ou 1e-6. Un chiffre
    qui bouge avec une constante d'implémentation n'est pas un chiffre.
    """

    X = cantons[COMPOSANTES_FRI].to_numpy(dtype=float)
    y = (cantons["risque_pts"] / 100).to_numpy(dtype=float)

    def part_expliquee(prediction, cible=None):
        cible = y if cible is None else cible
        # Un ajustement sur matrice singulière renvoie des coefficients non
        # finis : la forme est alors déclarée non concluante plutôt que de
        # laisser un NaN se propager jusqu'au tableau affiché.
        if not np.all(np.isfinite(prediction)):
            return float("nan")

        residus = ((cible - prediction) ** 2).sum()
        total = ((cible - cible.mean()) ** 2).sum()
        return 1 - residus / total if total else 0.0

    formes = []

    moindres, *_ = np.linalg.lstsq(X, y, rcond=None)
    formes.append({"forme": "somme_ponderee", "r2": part_expliquee(X @ moindres),
                   "cantons": len(y)})

    avec_constante = np.c_[X, np.ones(len(y))]
    p2, *_ = np.linalg.lstsq(avec_constante, y, rcond=None)
    formes.append({"forme": "somme_constante",
                   "r2": part_expliquee(avec_constante @ p2), "cantons": len(y)})

    positifs = (X > 0).all(axis=1) & (y > 0)
    Xp, yp = X[positifs], y[positifs]

    if positifs.sum() > len(COMPOSANTES_FRI):
        geo = Xp.prod(axis=1) ** (1 / len(COMPOSANTES_FRI))
        formes.append({"forme": "moyenne_geometrique",
                       "r2": part_expliquee(geo, yp),
                       "cantons": int(positifs.sum())})

        journal = np.c_[np.log(Xp), np.ones(len(yp))]
        p3, *_ = np.linalg.lstsq(journal, np.log(yp), rcond=None)
        formes.append({"forme": "produit_puissances",
                       "r2": part_expliquee(np.exp(journal @ p3), yp),
                       "cantons": int(positifs.sum())})

    return pd.DataFrame(formes)


def _par_region(cadre, **agregats):
    """Agrégation régionale triée, sans jamais perdre une région à zéro."""

    return (
        cadre.groupby("region", dropna=False)
        .agg(**agregats)
        .reset_index()
    )


def plan_de_maintenance(coso):
    """Part des ouvrages COSO dotés d'un plan de maintenance, par région.

    **C'est la seule mesure d'entretien de tout le corpus.** Le fichier TdE ne
    porte ni état, ni panne, ni date de mise en service ; le COSO porte ce
    booléen. L'objectif « analyser les taux de fonctionnalité » n'est donc pas
    calculable, et ce qui suit n'en est pas la mesure mais le SUBSTITUT le plus
    proche : non pas « l'ouvrage fonctionne-t-il », mais « a-t-on prévu de le
    faire fonctionner ».

    La distinction n'est pas une prudence de forme. Un ouvrage sans plan de
    maintenance peut très bien couler aujourd'hui ; un ouvrage avec plan peut
    être à l'arrêt. Le premier a seulement une probabilité plus forte de le
    rester dans cinq ans, et c'est tout ce que ces données autorisent à dire.
    """

    agrege = _par_region(
        coso,
        ouvrages=("id", "size"),
        avec_plan=("plan_maintenance", "sum"),
    )
    agrege["avec_plan"] = agrege["avec_plan"].astype(int)
    agrege["sans_plan"] = agrege["ouvrages"] - agrege["avec_plan"]
    agrege["part"] = 100 * agrege["avec_plan"] / agrege["ouvrages"]

    return agrege.sort_values("part", ascending=False).reset_index(drop=True)


# Débit sous lequel un forage est réputé FRAGILE, en m³/h. C'est le premier
# quartile observé (3,0), et c'est aussi l'ordre de grandeur en dessous duquel
# un forage à pompe solaire ne tient plus une communauté entière aux heures de
# pointe. Les deux lectures se rejoignant, le seuil ne dépend pas du choix.
SEUIL_DEBIT = 3.0

# Bornes de plausibilité PHYSIQUE. Le forage d'eau le plus profond du monde
# n'atteint pas 3 000 m ; un forage villageois ouest-africain dépasse rarement
# 150 m. Un débit de 8 500 m³/h serait celui d'un fleuve, non d'un forage.
# Ces bornes ne « nettoient » pas les données : elles NOMMENT ce qui ne peut
# pas être vrai, et le comptage de ce qui est écarté fait partie du résultat.
PROFONDEUR_MAXIMALE = 300.0
DEBIT_MAXIMAL = 100.0


def fragilite_debit(coso):
    """Distribution du débit des forages, et ce qui n'y est pas croyable.

    Faute d'un état de fonctionnement, le débit est le meilleur prédicteur de
    panne que le corpus offre : un forage faible s'assèche en saison sèche, se
    fait surexploiter, et tombe. Il ne dit pas qui est en panne — il dit qui le
    sera.

    Les valeurs aberrantes sont écartées du calcul ET comptées. Les laisser
    porterait la moyenne à 132 m³/h pour une médiane de 5 ; les retirer en
    silence laisserait croire à un fichier propre alors que deux lignes y
    portent 8 500 m³/h et 9 239 m de profondeur.
    """

    mesures = coso[["localite", "canton", "region", "type_ouvrage",
                    "profondeur", "debit"]]

    debits = mesures.dropna(subset=["debit"])
    aberrants = debits[debits["debit"] > DEBIT_MAXIMAL]
    retenus = debits[debits["debit"] <= DEBIT_MAXIMAL]

    profondeurs = mesures.dropna(subset=["profondeur"])
    profondeurs_aberrantes = profondeurs[
        profondeurs["profondeur"] > PROFONDEUR_MAXIMALE
    ]

    par_region = _par_region(
        retenus,
        forages=("debit", "size"),
        debit_median=("debit", "median"),
        fragiles=("debit", lambda serie: int((serie < SEUIL_DEBIT).sum())),
    )
    par_region["part_fragiles"] = (
        100 * par_region["fragiles"] / par_region["forages"]
    )

    return {
        "mesures": retenus.reset_index(drop=True),
        "regions": par_region.sort_values("part_fragiles", ascending=False)
                             .reset_index(drop=True),
        "renseignes": int(len(debits)),
        "total": int(len(coso)),
        "fragiles": int((retenus["debit"] < SEUIL_DEBIT).sum()),
        "median": float(retenus["debit"].median()) if len(retenus) else 0.0,
        "aberrants": int(len(aberrants)),
        "profondeurs_aberrantes": int(len(profondeurs_aberrantes)),
        "seuil": SEUIL_DEBIT,
    }


def relation_profondeur_debit(coso):
    """Forer plus profond donne-t-il plus d'eau ? — la droite, et sa portée.

    La droite est ajustée ICI et non dans la vue : `scatter_fit` la trace, il
    ne l'estime pas, et une vue qui la calculerait rendrait sa pente
    invérifiable par le rapport.

    Les valeurs physiquement impossibles sont écartées avant l'ajustement. Un
    forage de 9 239 m entraînerait la droite à lui seul, et la relation
    affichée décrirait alors une faute de frappe.
    """

    cadre = coso[["localite", "canton", "region", "profondeur", "debit"]].dropna(
        subset=["profondeur", "debit"])
    cadre = cadre[(cadre["profondeur"] <= PROFONDEUR_MAXIMALE)
                  & (cadre["debit"] <= DEBIT_MAXIMAL)]

    if len(cadre) < 3:
        return {"cadre": cadre.reset_index(drop=True), "modele": None,
                "r2": float("nan"), "n": int(len(cadre))}

    x = cadre["profondeur"].to_numpy(dtype=float)
    y = cadre["debit"].to_numpy(dtype=float)

    pente, ordonnee = np.polyfit(x, y, 1)
    residus = y - (ordonnee + pente * x)
    total = ((y - y.mean()) ** 2).sum()

    return {
        "cadre": cadre.reset_index(drop=True),
        "modele": {"ordonnee": float(ordonnee), "pente": float(pente)},
        "r2": float(1 - (residus ** 2).sum() / total) if total else 0.0,
        "n": int(len(cadre)),
    }


def mise_en_service(coso):
    """Le trajet d'un ouvrage entre sa réception technique et sa remise.

    Un ouvrage réceptionné n'est pas un ouvrage en service : il l'est le jour
    où la communauté en reçoit la charge. Entre les deux, il existe, il est
    payé, il figure dans les inventaires — et personne n'y puise.

    Trois faits sortent de ces deux colonnes, et aucun n'était visible dans le
    décompte des ouvrages : le délai médian, le nombre d'ouvrages réceptionnés
    et TOUJOURS PAS remis, et le nombre de remises datées sans réception —
    lesquelles ne sont pas un scandale mais un défaut de saisie, et disent la
    fiabilité de ce suivi.
    """

    recu = pd.to_datetime(coso["date_of_technical_acceptance_of_work"],
                          errors="coerce")
    remis = pd.to_datetime(coso["official_handover_date_to_community"],
                           errors="coerce")

    cadre = coso.assign(
        recu=recu, remis=remis, attente_jours=(remis - recu).dt.days,
        en_attente=recu.notna() & remis.isna(),
    )

    par_region = _par_region(
        cadre,
        ouvrages=("id", "size"),
        receptionnes=("recu", "count"),
        remis=("remis", "count"),
        en_attente=("en_attente", "sum"),
    )
    par_region["en_attente"] = par_region["en_attente"].astype(int)

    delais = cadre["attente_jours"].dropna()

    return {
        "regions": par_region.sort_values("en_attente", ascending=False)
                             .reset_index(drop=True),
        "receptionnes": int(recu.notna().sum()),
        "remis": int(remis.notna().sum()),
        "en_attente": int(cadre["en_attente"].sum()),
        "sans_reception": int((remis.notna() & recu.isna()).sum()),
        "delai_median": float(delais.median()) if len(delais) else 0.0,
        "delais": delais.reset_index(drop=True),
        "mesures": int(len(delais)),
        "anterieurs": int((delais < 0).sum()),
    }


# ─── Le déficit, et ce qu'il coûterait ───────────────────────────────────────

def deficit_ouvrages(cantons, tde, coso):
    """Ouvrages manquants pour amener chaque région à la médiane nationale.

    Le rapport « habitants par ouvrage » se lit mal : il dit qu'une région est
    huit fois moins bien dotée qu'une autre, et un décideur ne peut rien
    commander avec un rapport. Le convertir en NOMBRE D'OUVRAGES rend l'écart
    exécutable — et vérifiable, puisque le calcul tient en une division.

    L'étalon est la MÉDIANE régionale, non la meilleure région : aligner tout
    le pays sur la Savane la mieux dotée produirait une facture si grande
    qu'elle ne serait pas lue. La médiane est le niveau que la moitié du pays
    atteint déjà — donc atteignable, par construction.

    Ce n'est pas un besoin technique. Un ouvrage dessert un village, pas un
    quotient ; le vrai besoin dépend de l'habitat, du débit et de la nappe. Ce
    chiffre mesure une INÉGALITÉ, et la ramène à l'unité dans laquelle on
    budgète.
    """

    equipes = pd.concat([tde[["cle_canton"]], coso[["cle_canton"]]])
    par_canton = equipes.groupby("cle_canton").size().rename("ouvrages")

    cadre = cantons.merge(par_canton, on="cle_canton", how="left")
    cadre["ouvrages"] = cadre["ouvrages"].fillna(0).astype(int)

    agrege = _par_region(
        cadre,
        cantons=("canton", "size"),
        population=("population", "sum"),
        ouvrages=("ouvrages", "sum"),
    )
    agrege["habitants_par_ouvrage"] = (
        agrege["population"] / agrege["ouvrages"].replace(0, np.nan)
    )

    etalon = float(agrege["habitants_par_ouvrage"].median())

    # Le plafond : une région sans aucun ouvrage n'a pas de ratio, et son
    # déficit est alors la totalité de ce que l'étalon lui prescrirait.
    requis = np.ceil(agrege["population"] / etalon) if etalon else 0
    agrege["ouvrages_requis"] = requis.astype(int)
    agrege["manquants"] = (
        (agrege["ouvrages_requis"] - agrege["ouvrages"]).clip(lower=0).astype(int)
    )

    return {
        "regions": agrege.sort_values("manquants", ascending=False)
                         .reset_index(drop=True),
        "etalon": etalon,
        "manquants": int(agrege["manquants"].sum()),
        "national": float(cadre["population"].sum() / cadre["ouvrages"].sum())
        if cadre["ouvrages"].sum() else float("nan"),
    }


def facture_rattrapage(cantons, tde, coso):
    """Ce que coûterait le rattrapage, région par région, en francs CFA.

    Le prix unitaire est la MÉDIANE des montants réellement payés par le COSO
    pour un ouvrage — pas un devis, pas une estimation, une dépense constatée.
    C'est aussi ce qui rend le total défendable : il ne suppose aucune économie
    d'échelle, aucun surcoût d'accès, seulement que le prochain ouvrage coûtera
    ce qu'a coûté le précédent.

    Le résultat se lit avec `econometrie.fonction_de_cout` et pas sans lui : le
    coût d'un ouvrage n'étant pas lié au nombre de ses bénéficiaires, la même
    facture achète des couvertures très différentes selon les endroits où on la
    dépense. C'est la seule marge de manœuvre gratuite du dossier.
    """

    deficit = deficit_ouvrages(cantons, tde, coso)
    paye = coso.loc[coso["montant_paye"] > 0, "montant_paye"]
    unitaire = float(paye.median()) if len(paye) else 0.0

    regions = deficit["regions"].copy()
    regions["cout"] = regions["manquants"] * unitaire

    return {
        "regions": regions.sort_values("cout", ascending=False)
                          .reset_index(drop=True),
        "unitaire": unitaire,
        "ouvrages": int(regions["manquants"].sum()),
        "total": float(regions["cout"].sum()),
        "observations": int(len(paye)),
        "etalon": deficit["etalon"],
    }


# ─── Ce qu'il faudrait construire, et ce que ça coûterait ────────────────────
#
# Les fonctions qui suivent CHIFFRENT UNE PROPOSITION. Elles sortent donc du
# régime des autres : partout ailleurs, ce module ne fait que résumer ce que le
# corpus contient ; ici, il faut poser un objectif de service que les données
# ne portent pas.
#
# La règle qu'on s'impose : **toute hypothèse est un ARGUMENT de fonction, avec
# sa valeur écrite en clair, et jamais une constante enfouie.** Un lecteur qui
# conteste le seuil doit pouvoir le déplacer et voir la facture bouger, plutôt
# que d'avoir à nous croire.

# Seuils de desserte, en habitants par ouvrage. Ils sont POSÉS, non tirés du
# corpus, et chacun correspond à un objet technique différent :
#
#   ·   300 — la norme villageoise classique d'un point d'eau à pompe manuelle ;
#   · 1 000 — l'ordre de grandeur d'un forage photovoltaïque comme ceux du
#             COSO, qui dessert un bourg ;
#   · 5 000 — un plancher volontairement bas, pour montrer que même une
#             ambition minimale laisse un déficit.
#
# Le quatrième scénario n'est pas ici : c'est la MÉDIANE régionale observée,
# calculée par `deficit_ouvrages`, et c'est le seul qui ne suppose rien.
NORMES_DESSERTE = (300, 1000, 5000)


def prix_unitaire_observe(coso):
    """Prix médian réellement payé pour un ouvrage COSO, en francs CFA.

    Une dépense CONSTATÉE, jamais un devis. C'est ce qui rend les factures de
    cette section défendables : elles ne supposent ni économie d'échelle, ni
    surcoût d'accès — seulement que le prochain forage coûtera ce qu'a coûté
    le précédent.
    """

    paye = coso.loc[coso["montant_paye"] > 0, "montant_paye"]

    return float(paye.median()) if len(paye) else 0.0


def besoin_par_norme(cantons, tde, coso, normes=NORMES_DESSERTE):
    """Ouvrages à construire et facture, pour chaque seuil de desserte.

    Un tableau de SCÉNARIOS plutôt qu'un chiffre unique. Le nombre d'ouvrages
    manquants n'existe pas dans l'absolu : il dépend entièrement du service
    qu'on vise, et publier une seule valeur reviendrait à faire passer ce choix
    politique pour un résultat de calcul.
    """

    population = float(cantons["population"].sum())
    existants = int(len(tde) + len(coso))
    unitaire = prix_unitaire_observe(coso)

    lignes = []

    for norme in normes:
        requis = int(np.ceil(population / norme)) if norme else 0
        manquants = max(0, requis - existants)

        lignes.append({
            "norme": int(norme),
            "requis": requis,
            "existants": existants,
            "manquants": manquants,
            "cout": manquants * unitaire,
        })

    return {
        "scenarios": pd.DataFrame(lignes),
        "unitaire": unitaire,
        "existants": existants,
        "population": population,
    }


def deficit_par_canton(cantons, tde, coso, norme=1000):
    """Ouvrages manquants CANTON PAR CANTON, pour un seuil de desserte donné.

    La maille cantonale est celle des cartes et celle où se décide un chantier.
    L'agrégat régional dit combien il en faut ; celui-ci dit où.
    """

    ouvrages = (
        pd.concat([tde[["cle_canton"]], coso[["cle_canton"]]])
        .groupby("cle_canton").size().rename("ouvrages").reset_index()
    )

    cadre = cantons.merge(ouvrages, on="cle_canton", how="left")
    cadre["ouvrages"] = cadre["ouvrages"].fillna(0).astype(int)
    cadre["requis"] = np.ceil(cadre["population"] / norme).astype(int)
    cadre["manquants"] = (cadre["requis"] - cadre["ouvrages"]).clip(lower=0)

    return cadre


def parc_par_nature(tde):
    """Forages, châteaux d'eau, et ce que le fichier ne nomme pas.

    Le château est l'ouvrage qui STOCKE et met en pression ; le forage est
    celui qui puise. Un réseau sans château distribue au débit de sa pompe, et
    s'arrête avec elle. L'inventaire publié en compte deux — le chiffre est si
    petit qu'il faut le dire séparément plutôt que de le noyer dans un total.
    """

    compte = _compte(tde, "nature")
    lecture = {str(ligne["nature"]): int(ligne["ouvrages"])
               for _, ligne in compte.iterrows()}

    return {
        "detail": compte,
        "forages": lecture.get("Forage", 0),
        "chateaux": lecture.get("Château", 0),
        "non_renseignes": lecture.get(NON_RENSEIGNE, 0),
        "total": int(len(tde)),
    }


def facture_inondation(cantons, couts_unitaires, classes=None):
    """Facture d'un aménagement par canton exposé — à coût unitaire POSÉ.

    **Le corpus ne porte aucun prix d'ouvrage de gestion des eaux pluviales.**
    Ni le COSO, dont les 218 sous-projets sont tous des forages, ni le fichier
    TdE, ni la couche de risque. Transposer le prix d'un forage à un bassin de
    rétention serait inventer un chiffre en lui donnant l'apparence d'une
    mesure.

    La facture est donc rendue PARAMÉTRIQUE : une ligne par hypothèse de coût,
    et le lecteur choisit celle qu'il peut défendre. C'est la seule forme
    honnête d'estimation quand le prix manque — elle affiche son ignorance au
    lieu de la masquer derrière une moyenne.
    """

    cadre = classer_officiel(cantons)
    retenus = cadre[cadre["classe_officielle"].isin(classes or CLASSES_HAUTES)]

    lignes = [
        {"unitaire": float(cout), "cantons": int(len(retenus)),
         "total": float(cout) * len(retenus)}
        for cout in couts_unitaires
    ]

    return {
        "scenarios": pd.DataFrame(lignes),
        "cantons": int(len(retenus)),
        "population": float(retenus["population"].sum()),
        "liste": retenus[["canton", "prefecture", "region", "risque_pts",
                          "population"]]
        .sort_values("risque_pts", ascending=False).reset_index(drop=True),
    }


# ─── Du besoin au PROGRAMME : où, combien, et quand ──────────────────────────
#
# Un besoin chiffré n'est pas encore une proposition. Tant qu'on écrit « il
# manque 1 350 ouvrages pour 22,5 milliards », personne ne peut ni contester ni
# exécuter : ni le lieu, ni l'ordre, ni l'année n'y figurent.
#
# Ce qui suit transforme le besoin en CALENDRIER. Trois décisions, toutes
# exposées en arguments :
#
#   · l'ORDRE — par urgence, et l'urgence se lit dans le corpus : un canton à
#     risque élevé qui n'a aucun ouvrage passe avant tout le monde ;
#   · le RYTHME — un budget annuel, obtenu en étalant la facture sur un
#     horizon. Un programme qui ne dit pas son rythme n'est pas datable ;
#   · le LIEU — un point à l'intérieur du canton, et rien de plus fin : le
#     corpus ne porte aucune donnée d'habitat, de nappe ou de foncier, et
#     prétendre placer un forage au mètre serait une fiction.

# Rang d'urgence, du plus au moins pressant. L'ordre est LEXICOGRAPHIQUE et non
# une somme pondérée : des poids inventés (« le risque vaut 3, l'absence
# d'ouvrage 2 ») donneraient un classement invérifiable, alors qu'une
# succession de critères se relit et se conteste ligne à ligne.
URGENCES = ["expose_sans_ouvrage", "expose", "sans_ouvrage", "autres"]


def _urgence(ligne):
    """La classe d'urgence d'un canton — cf. `URGENCES`."""

    expose = ligne["classe_officielle"] in CLASSES_HAUTES
    sans = ligne["ouvrages"] == 0

    if expose and sans:
        return "expose_sans_ouvrage"

    if expose:
        return "expose"

    return "sans_ouvrage" if sans else "autres"


def _etaler(cadre, horizon, debut, colonne="montant"):
    """Répartit les lignes DÉJÀ ORDONNÉES sur `horizon` années.

    Le critère est le BUDGET, non le nombre de chantiers : on avance dans la
    liste jusqu'à épuiser l'enveloppe de l'année, puis on passe à la suivante.
    Découper en tranches d'effectif égal aurait mis la même année un canton à
    un ouvrage et un canton à quarante.

    La dernière année absorbe les arrondis : sans ce plafond, un centime de
    dépassement créerait une sixième année à un seul chantier.
    """

    total = float(cadre[colonne].sum())

    if not len(cadre) or total <= 0 or horizon < 1:
        return cadre.assign(annee=debut)

    enveloppe = total / horizon
    cumul = cadre[colonne].cumsum()

    # `ceil(cumul / enveloppe)` donne le rang de l'année, 1 pour la première.
    rangs = np.ceil(cumul / enveloppe).clip(1, horizon).astype(int)

    return cadre.assign(annee=debut + rangs - 1)


def programme_ouvrages(cantons, tde, coso, norme=5000, horizon=5, debut=2027):
    """Le programme d'ouvrages : un chantier par canton, daté et chiffré.

    `norme`   habitants par ouvrage visés — c'est l'ambition, et elle est POSÉE.
    `horizon` nombre d'années du programme.
    `debut`   première année.

    Chaque ligne porte un point SITUÉ à l'intérieur du canton — son point
    représentatif, choisi parce qu'un centroïde tombe hors du polygone sur les
    cantons en croissant, et qu'un chantier hors de son canton ne veut rien
    dire.
    """

    cadre = deficit_par_canton(cantons, tde, coso, norme=norme)
    cadre = classer_officiel(cadre)
    cadre = cadre[cadre["manquants"] > 0].copy()

    if cadre.empty:
        return {"cadre": cadre, "annees": pd.DataFrame(), "total": 0.0,
                "unitaire": prix_unitaire_observe(coso), "ouvrages": 0,
                "horizon": horizon, "debut": debut, "norme": norme}

    unitaire = prix_unitaire_observe(coso)
    cadre["montant"] = cadre["manquants"] * unitaire
    cadre["urgence"] = cadre.apply(_urgence, axis=1)
    cadre["rang_urgence"] = cadre["urgence"].map(
        {nom: rang for rang, nom in enumerate(URGENCES)})

    # À urgence égale, le canton le plus peuplé d'abord : c'est le seul
    # arbitrage que les données autorisent, et il maximise le nombre de
    # personnes servies à budget donné — le coût d'un ouvrage ne dépendant pas
    # de ceux qu'il sert (cf. `econometrie.fonction_de_cout`).
    cadre = cadre.sort_values(["rang_urgence", "population"],
                              ascending=[True, False]).reset_index(drop=True)
    cadre = _etaler(cadre, horizon, debut)

    cadre = _situer(cadre)

    return {
        "cadre": cadre,
        "annees": _par_annee(cadre, "manquants"),
        "total": float(cadre["montant"].sum()),
        "ouvrages": int(cadre["manquants"].sum()),
        "unitaire": unitaire,
        "horizon": horizon, "debut": debut, "norme": norme,
    }


def programme_inondations(cantons, tde, coso, cout_unitaire=250e6, horizon=3,
                          debut=2027):
    """Le programme d'aménagement des cantons exposés, daté et chiffré.

    `cout_unitaire` est une HYPOTHÈSE — le corpus ne porte aucun prix
    d'ouvrage de gestion des eaux pluviales — et c'est pour cela qu'il est le
    premier argument : le lecteur doit pouvoir le remplacer par le sien et
    voir le calendrier entier se recalculer.

    Trois ans et non cinq : dix-sept cantons ne justifient pas un programme
    décennal, et l'aléa, lui, n'attend pas.
    """

    ouvrages = (
        pd.concat([tde[["cle_canton"]], coso[["cle_canton"]]])
        .groupby("cle_canton").size().rename("ouvrages").reset_index()
    )

    cadre = classer_officiel(cantons).merge(ouvrages, on="cle_canton",
                                            how="left")
    cadre["ouvrages"] = cadre["ouvrages"].fillna(0).astype(int)
    cadre = cadre[cadre["classe_officielle"].isin(CLASSES_HAUTES)].copy()

    if cadre.empty:
        return {"cadre": cadre, "annees": pd.DataFrame(), "total": 0.0,
                "unitaire": cout_unitaire, "cantons": 0,
                "horizon": horizon, "debut": debut}

    cadre["montant"] = float(cout_unitaire)
    cadre["urgence"] = cadre.apply(_urgence, axis=1)
    cadre["rang_urgence"] = cadre["urgence"].map(
        {nom: rang for rang, nom in enumerate(URGENCES)})

    # Le RISQUE départage ici, non la population : le programme traite un aléa,
    # et le canton le plus exposé passe d'abord quel que soit son poids
    # démographique. C'est l'inverse de l'arbitrage retenu pour les forages, et
    # c'est voulu — les deux programmes ne poursuivent pas le même but.
    cadre = cadre.sort_values(["rang_urgence", "risque_pts"],
                              ascending=[True, False]).reset_index(drop=True)
    cadre = _etaler(cadre, horizon, debut)

    cadre = _situer(cadre)
    cadre["manquants"] = 1

    return {
        "cadre": cadre,
        "annees": _par_annee(cadre, "manquants"),
        "total": float(cadre["montant"].sum()),
        "cantons": int(len(cadre)),
        "unitaire": float(cout_unitaire),
        "horizon": horizon, "debut": debut,
    }


def _situer(cadre):
    """Ajoute à chaque ligne un point situé DANS son canton.

    Le point REPRÉSENTATIF, jamais le centroïde : sur un canton en croissant —
    les cantons lagunaires du sud en sont —, le centroïde tombe hors du
    polygone, et un chantier posé hors de son propre canton ne veut rien dire.

    Le point est pris sur le cadre lui-même, sans passer par une jointure :
    `cle_canton` n'est PAS unique — deux cantons nommés Gamé, l'un dans le Zio,
    l'autre dans l'Amou, partagent la même clé — et indexer dessus lève une
    erreur de réindexation. Le corpus le signale par sa colonne
    `canton_unique`, qui vaut faux pour ces deux lignes.
    """

    points = cadre.geometry.representative_point()

    return cadre.assign(lon=points.x.to_numpy(), lat=points.y.to_numpy())


def _par_annee(cadre, colonne_ouvrages):
    """Le calendrier vu par année : chantiers, ouvrages, montant."""

    agrege = (
        cadre.groupby("annee")
        .agg(cantons=("canton", "size"),
             ouvrages=(colonne_ouvrages, "sum"),
             montant=("montant", "sum"))
        .reset_index()
        .sort_values("annee")
    )
    agrege["cumul"] = agrege["montant"].cumsum()

    return agrege


# ─── L'entretien de ce qu'on construit ───────────────────────────────────────
#
# Un programme d'investissement qui ne budgète pas son entretien construit des
# ouvrages qui tomberont. C'est le sujet de l'acte 2 — 173 microprojets sur 218
# n'ont aucun plan de maintenance déclaré — et une proposition qui répéterait
# cette omission ne vaudrait pas mieux que ce qu'elle critique.

# Taux d'entretien annuel, en part du coût d'investissement. Le premier est
# OBSERVÉ dans le corpus ; les trois autres sont posés, et couvrent la
# fourchette que la littérature retient pour l'hydraulique rurale.
TAUX_ENTRETIEN = (0.03, 0.05, 0.08)


def taux_entretien_observe(coso):
    """Ce que le COSO provisionne réellement pour l'entretien d'un ouvrage.

    Le fichier porte deux colonnes rarement lues — `fonds_entretien` et
    `fonds_entretien_prevu` — et c'est le seul ancrage empirique du corpus sur
    la question. La médiane des provisions vaut 250 000 F, soit 1,35 % du
    montant payé.

    Ce que ce chiffre est, et ce qu'il n'est pas : une DOTATION constituée à la
    remise de l'ouvrage, pas un budget annuel. Le corpus ne dit ni sa
    périodicité ni ce qu'elle couvre. Le prendre pour un taux d'entretien
    annuel serait une erreur de lecture — il sert ici de PLANCHER, et le fait
    qu'il soit très inférieur aux taux usuels est précisément le résultat.
    """

    provisions = coso.loc[coso["fonds_entretien"] > 0, "fonds_entretien"]
    ratio = (coso["fonds_entretien"] / coso["montant_paye"]).replace(
        [np.inf, -np.inf], np.nan).dropna()

    return {
        "provision_mediane": float(provisions.median()) if len(provisions) else 0.0,
        "part_mediane": float(ratio.median()) if len(ratio) else 0.0,
        "ouvrages": int(len(provisions)),
        "total": int(len(coso)),
    }


def entretien_previsionnel(programme, taux, apres=5):
    """Coût annuel d'entretien du parc que le programme livre, année par année.

    L'entretien porte sur le parc CUMULÉ : un ouvrage livré en 2027 s'entretient
    aussi en 2031. La courbe monte donc mécaniquement pendant la construction,
    puis se stabilise — et c'est ce plateau, non le pic d'investissement, qui
    engage durablement un budget.

    `apres` prolonge la projection au-delà du programme, à parc constant. Sans
    ces années-là, le tableau s'arrêterait juste avant de montrer la charge
    récurrente qu'il crée.
    """

    annees = programme.get("annees")

    if annees is None or annees.empty:
        return pd.DataFrame(columns=["annee", "parc", "capex_cumule",
                                     "entretien"])

    lignes = []
    parc = capex = 0.0

    derniere = int(annees["annee"].max())

    for _, ligne in annees.iterrows():
        parc += float(ligne["ouvrages"])
        capex += float(ligne["montant"])
        lignes.append({"annee": int(ligne["annee"]), "parc": parc,
                       "capex_cumule": capex, "entretien": capex * taux})

    for pas in range(1, apres + 1):
        lignes.append({"annee": derniere + pas, "parc": parc,
                       "capex_cumule": capex, "entretien": capex * taux})

    return pd.DataFrame(lignes)


def entretien_scenarios(programme, taux=TAUX_ENTRETIEN, observe=None, apres=5):
    """Charge d'entretien à l'horizon, pour chaque taux envisagé.

    Le taux OBSERVÉ ouvre la liste quand il est fourni : la comparaison entre
    ce que le programme provisionne aujourd'hui et ce qu'un entretien réel
    coûterait est le seul résultat que cette section produise.
    """

    total = float(programme.get("total") or 0.0)
    valeurs = list(taux)

    if observe:
        valeurs = [observe, *valeurs]

    lignes = []

    for valeur in valeurs:
        courbe = entretien_previsionnel(programme, valeur, apres=apres)
        lignes.append({
            "taux": float(valeur),
            "annuel_plateau": float(courbe["entretien"].max())
            if len(courbe) else 0.0,
            "cumul": float(courbe["entretien"].sum()) if len(courbe) else 0.0,
            "part_investissement": (
                100 * float(courbe["entretien"].sum()) / total if total else 0.0
            ),
        })

    return pd.DataFrame(lignes)


def zeros_composantes(cantons):
    """Combien de cantons portent un zéro, et sur quelle composante.

    C'est la clé de lecture de `reconstitution_fri` : la moyenne géométrique
    annoncée par le producteur restitue son indice presque exactement là où
    toutes les composantes sont non nulles — mais un zéro annule un produit,
    et 346 cantons sur 388 en portent au moins un, essentiellement parce
    qu'ils n'ont ni zone urbaine ni bâti recensé. Le FRI y est pourtant publié
    et non nul : un traitement des zéros existe donc, qui n'est écrit nulle
    part.
    """

    X = cantons[COMPOSANTES_FRI]
    zeros = (X == 0)

    detail = pd.DataFrame({
        "composante": COMPOSANTES_FRI,
        "cantons_a_zero": [int(zeros[c].sum()) for c in COMPOSANTES_FRI],
    }).sort_values("cantons_a_zero", ascending=False).reset_index(drop=True)

    return detail, int(zeros.any(axis=1).sum()), int(len(cantons))
