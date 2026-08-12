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
