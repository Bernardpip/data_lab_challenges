"""Estimations — ce que les corrélations du corpus permettent d'affirmer.

Ce module va au-delà du décompte. Il ne demande pas « combien d'ouvrages » mais
« qu'est-ce qui explique qu'un canton en reçoive un », et il répond par des
coefficients, des erreurs-types et des tailles d'échantillon.

**Ce que ces estimations sont, et ce qu'elles ne sont pas.** Aucune n'identifie
un effet causal : il n'y a ni assignation aléatoire, ni discontinuité, ni
instrument. Ce sont des ASSOCIATIONS conditionnelles, et elles se lisent comme
telles. Leur force ne vient pas d'une prétention causale mais de leur
robustesse : un coefficient qui survit à l'ajout des effets fixes de région
dit quelque chose ; un coefficient qui s'évanouit avec eux disait surtout le
découpage administratif.

Aucune dépendance ajoutée au livrable : l'estimateur tient en trente lignes de
numpy. Importer `statsmodels` pour un MCO alourdirait l'installation du zip
d'un paquet de 15 Mo, pour une fonctionnalité qu'on écrit soi-même et qu'on
peut alors documenter.
"""

# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
from scipy import stats

from utils import analytics


def mco(y, X, noms):
    """Moindres carrés ordinaires, erreurs-types robustes (HC1).

    HC1 et non les erreurs-types classiques : la variance des résidus n'a
    aucune raison d'être constante ici — un canton de 400 000 habitants et un
    canton de 17 ne se comparent pas terme à terme, et supposer le contraire
    resserrerait artificiellement les intervalles de confiance. La correction
    de White ne coûte rien et retire une hypothèse invérifiable.

    La constante est ajoutée d'office : un modèle sans elle contraint la droite
    à passer par l'origine, ce qui n'a de sens dans aucun des modèles d'ici.
    """

    y = np.asarray(y, dtype=float)
    X = np.c_[np.ones(len(y)), np.asarray(X, dtype=float)]
    noms = ["constante"] + list(noms)

    inverse = np.linalg.pinv(X.T @ X)
    beta = inverse @ X.T @ y
    residus = y - X @ beta
    n, k = X.shape

    # Sandwich de White, corrigé du degré de liberté (HC1).
    pondere = X * residus[:, None]
    variance = inverse @ (pondere.T @ pondere) @ inverse * n / (n - k)

    erreurs = np.sqrt(np.diag(variance))
    t = np.divide(beta, erreurs, out=np.zeros_like(beta),
                  where=erreurs > 0)
    p = 2 * (1 - stats.t.cdf(np.abs(t), n - k))

    total = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (residus @ residus) / total if total else 0.0

    return {
        "termes": pd.DataFrame({"terme": noms, "coefficient": beta,
                                "erreur_type": erreurs, "t": t, "p": p}),
        "r2": float(r2), "n": int(n),
    }


def gini(valeurs):
    """Indice de Gini — 0 = répartition égale, 1 = tout à un seul.

    Employé ici sur des montants PAR HABITANT, jamais sur des montants bruts :
    un canton deux fois plus peuplé qui reçoit deux fois plus n'est pas inégal,
    et un Gini calculé sur les montants le déclarerait pourtant tel.
    """

    x = np.sort(np.asarray(valeurs, dtype=float))
    n = len(x)

    if n == 0 or x.sum() == 0:
        return float("nan")

    rangs = 2 * np.arange(1, n + 1) - n - 1

    return float(rangs @ x / (n * x.sum()))


# ─── Le panel cantonal, socle de toutes les estimations ──────────────────────

def panel(cantons, tde, coso):
    """Un canton par ligne : son besoin, sa dotation, son investissement.

    Jointure GAUCHE sur le référentiel : les cantons sans ouvrage sont la
    moitié du sujet, et une jointure interne les ferait disparaître de
    l'estimation — le modèle n'expliquerait plus « qui reçoit » mais
    « combien reçoivent ceux qui reçoivent », ce qui n'est pas la question.
    """

    argent = (
        coso.groupby("cle_canton")
        .agg(ouvrages_coso=("id", "size"), investi=("montant_paye", "sum"),
             beneficiaires=("beneficiaires_femmes", "sum"))
        .reset_index()
    )
    forages = tde.groupby("cle_canton").size().rename("ouvrages_tde").reset_index()

    cadre = (cantons.merge(argent, on="cle_canton", how="left")
                    .merge(forages, on="cle_canton", how="left"))

    for colonne in ("ouvrages_coso", "investi", "beneficiaires", "ouvrages_tde"):
        cadre[colonne] = cadre[colonne].fillna(0)

    cadre["ouvrages"] = cadre["ouvrages_coso"] + cadre["ouvrages_tde"]
    cadre["equipe"] = (cadre["ouvrages"] > 0).astype(int)
    cadre["fri"] = cadre["risque_pts"] / 100
    cadre["log_population"] = np.log(cadre["population"].clip(lower=1))

    return cadre


# ─── Modèle 1 : qui reçoit un ouvrage ? ──────────────────────────────────────

def qui_est_equipe(cantons, tde, coso):
    """Probabilité qu'un canton porte un ouvrage — avant et après région.

    Deux estimations, et c'est leur ÉCART qui informe. Sans les effets fixes
    de région, on mesure ce qui distingue un canton équipé d'un autre. Avec
    eux, on ne compare plus que des cantons de la même région — et si le
    pouvoir explicatif bondit alors que les variables de besoin restent
    muettes, c'est que la dotation suit le découpage des programmes, non le
    besoin qu'ils invoquent.

    Modèle de probabilité linéaire plutôt que logit : sur une variable
    binaire, ses coefficients se lisent directement en points de pourcentage,
    et l'enjeu ici est la COMPARAISON de deux spécifications, pas la
    prédiction.
    """

    cadre = panel(cantons, tde, coso)
    besoin = np.c_[cadre["log_population"], cadre["fri"], cadre["richesse_relative"]]
    noms = ["log_population", "risque", "richesse_relative"]

    sans = mco(cadre["equipe"], besoin, noms)

    muettes = pd.get_dummies(cadre["region"], drop_first=True).astype(float)
    avec = mco(cadre["equipe"], np.c_[besoin, muettes.values],
               noms + list(muettes.columns))

    return {"sans_region": sans, "avec_region": avec}


# ─── Modèle 2 : l'argent suit-il les habitants ? ─────────────────────────────

def elasticite_investissement(cantons, coso):
    """Élasticité de l'investissement à la population, dans le périmètre doté.

    Estimée en logarithmes : le coefficient se lit alors comme une élasticité
    — de combien de pour cent l'investissement varie quand la population varie
    de un pour cent. C'est la seule forme qui rende le résultat interprétable
    sans référence à l'échelle des montants.

    Une élasticité de 1 signifierait une dotation strictement proportionnelle.
    En dessous, la dotation est RÉGRESSIVE : les cantons peuplés reçoivent
    moins par habitant que les petits.

    Restreinte aux cantons effectivement dotés : y mêler les cantons à zéro
    mesurerait l'éligibilité au programme, pas la règle de répartition à
    l'intérieur de celui-ci.
    """

    argent = (coso.groupby("cle_canton")
              .agg(investi=("montant_paye", "sum")).reset_index())
    cadre = cantons.merge(argent, on="cle_canton", how="inner")
    cadre = cadre[(cadre["investi"] > 0) & (cadre["population"] > 0)]

    y = np.log(cadre["investi"])
    simple = mco(y, np.c_[np.log(cadre["population"])], ["log_population"])
    complet = mco(y, np.c_[np.log(cadre["population"]), cadre["risque_pts"] / 100,
                           cadre["richesse_relative"]],
                  ["log_population", "risque", "richesse_relative"])

    return {"simple": simple, "complet": complet, "cantons": int(len(cadre))}


# ─── Modèle 3 : le coût dépend-il de ceux qu'il sert ? ───────────────────────

def fonction_de_cout(coso):
    """Élasticité du coût d'un ouvrage au nombre de ses bénéficiaires.

    C'est le résultat qui commande tous les autres. Si l'élasticité est nulle,
    le coût d'un forage ne dépend pas du nombre de personnes qu'il dessert :
    le coût par habitant n'est alors PLUS une caractéristique de l'ouvrage,
    mais du lieu où on l'a posé. Placer le même ouvrage ailleurs change le
    coût par personne sans rien changer à la dépense.
    """

    cadre = coso.assign(
        beneficiaires=coso["beneficiaires_femmes"].fillna(0)
        + coso["beneficiaires_hommes"].fillna(0)
    )
    cadre = cadre[(cadre["beneficiaires"] > 0) & (cadre["montant_paye"] > 0)]

    estimation = mco(np.log(cadre["montant_paye"]),
                     np.c_[np.log(cadre["beneficiaires"])],
                     ["log_beneficiaires"])

    quintiles = cadre.assign(
        quintile=pd.qcut(cadre["beneficiaires"], 5,
                         labels=[f"q{i}" for i in range(1, 6)])
    )
    profil = (
        quintiles.groupby("quintile", observed=False)
        .agg(ouvrages=("beneficiaires", "size"),
             beneficiaires_median=("beneficiaires", "median"),
             cout_median=("montant_paye", "median"))
        .reset_index()
    )
    profil["cout_par_beneficiaire"] = (
        profil["cout_median"] / profil["beneficiaires_median"]
    )

    return {"estimation": estimation, "profil": profil,
            "cout_median": float(cadre["montant_paye"].median())}


# ─── Modèle 4 : ce que le FRI classe réellement ──────────────────────────────

def ce_que_le_fri_ordonne(cantons):
    """Corrélation de rang entre le FRI et chacune de ses trois dimensions.

    L'indice combine aléa, exposition et vulnérabilité. Savoir LAQUELLE
    commande son classement n'est pas une curiosité méthodologique : un indice
    dominé par l'exposition désigne les endroits où une inondation ferait le
    plus de victimes, un indice dominé par l'aléa désigne les endroits où elle
    surviendra. Les deux appellent des politiques différentes — protéger des
    personnes, ou aménager un bassin — et la carte ne dit pas laquelle elle
    porte.

    Corrélation de SPEARMAN, sur les rangs : le FRI est très dissymétrique, et
    une corrélation de Pearson y suivrait les quelques cantons extrêmes.
    """

    dimensions = [
        ("alea", "susceptibilite"),
        ("exposition", "population"),
        ("vulnerabilite", "richesse_relative"),
    ]

    lignes = []

    for cle, colonne in dimensions:
        rho, p = stats.spearmanr(cantons["risque_pts"], cantons[colonne])
        lignes.append({"dimension": cle, "rho": float(rho), "p": float(p)})

    classement = cantons.nlargest(7, "risque_pts")[
        ["canton", "prefecture", "risque_pts", "susceptibilite", "population"]
    ].copy()
    # Le rang d'ALÉA du canton, pour montrer qu'un canton peut être premier au
    # risque et cent-cinquantième à l'aléa.
    classement["rang_alea"] = classement["susceptibilite"].map(
        lambda valeur: int((cantons["susceptibilite"] > valeur).sum()) + 1
    )

    return {"correlations": pd.DataFrame(lignes), "sommet": classement}


# ─── Modèle 5 : la couverture, région par région ─────────────────────────────

def couverture_par_region(cantons, tde, coso):
    """Habitants par ouvrage recensé, et concentration de la couverture.

    Le rapport habitants/ouvrage n'a de sens que rapporté à sa dispersion :
    une moyenne nationale de 31 545 habitants par ouvrage cache un rapport de
    1 à 245 entre les Savanes et les Plateaux.
    """

    cadre = panel(cantons, tde, coso)

    agrege = (
        cadre.groupby("region")
        .agg(cantons=("canton", "size"), population=("population", "sum"),
             ouvrages=("ouvrages", "sum"),
             cantons_couverts=("equipe", "sum"))
        .reset_index()
    )
    agrege["habitants_par_ouvrage"] = (
        agrege["population"] / agrege["ouvrages"].replace(0, np.nan)
    )
    agrege["part_couverte"] = 100 * agrege["cantons_couverts"] / agrege["cantons"]

    dotes = cadre[cadre["ouvrages"] > 0]

    return {
        "regions": agrege.sort_values("habitants_par_ouvrage"),
        "national": float(cadre["population"].sum() / cadre["ouvrages"].sum()),
        "gini_couverture": gini(dotes["ouvrages"] / dotes["population"]),
    }


# ─── Contrefactuel : et si la clé avait été démographique ? ──────────────────

def contrefactuel_demographique(cantons, coso):
    """Écart entre l'investissement observé et une répartition par habitant.

    Ce n'est pas une recommandation de répartir au prorata : un forage dessert
    un village, pas un canton, et les besoins ne sont pas uniformes. C'est un
    ÉTALON — la référence la plus neutre qu'on puisse construire — qui rend
    l'écart mesurable au lieu de le laisser à l'appréciation.
    """

    argent = (coso.groupby("cle_canton")
              .agg(investi=("montant_paye", "sum")).reset_index())
    cadre = cantons.merge(argent, on="cle_canton", how="inner")
    cadre = cadre[(cadre["investi"] > 0) & (cadre["population"] > 0)].copy()

    total = float(cadre["investi"].sum())
    cadre["par_habitant"] = cadre["investi"] / cadre["population"]
    cadre["equitable"] = total * cadre["population"] / cadre["population"].sum()
    cadre["ecart"] = cadre["investi"] - cadre["equitable"]

    colonnes = ["canton", "prefecture", "population", "investi", "equitable",
                "ecart", "par_habitant"]

    return {
        "cadre": cadre[colonnes].sort_values("ecart"),
        "total": total,
        "gini": gini(cadre["par_habitant"]),
        "mediane": float(cadre["par_habitant"].median()),
        "rapport_interdecile": float(
            cadre["par_habitant"].quantile(0.9)
            / cadre["par_habitant"].quantile(0.1)
        ),
    }
