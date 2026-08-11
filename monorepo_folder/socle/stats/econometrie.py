"""Analyses économétriques — estimations, tests et diagnostics.

Principe de rigueur tenu ici : sur des séries de 6 à 38 points, on ne peut PAS
tout estimer. Chaque fonction renvoie donc, en plus du coefficient, de quoi
juger s'il est interprétable — effectif, p-value, R², intervalle de confiance —
et les vues affichent ce diagnostic à côté du résultat.

Trois garde-fous appliqués partout :
  · `n` est toujours retourné : sous 10 observations, un R² élevé ne prouve rien ;
  · corrélation n'est jamais présentée comme causalité (séries non
    expérimentales, variables omises massives) ;
  · aucune extrapolation hors de la plage observée.
"""

import numpy as np
import pandas as pd
from scipy import stats


def ols(x, y):
    """Régression linéaire simple y = a + b·x, avec inférence complète.

    Retourne pente, ordonnée, R², p-value de la pente (H0 : b = 0), erreur
    standard, intervalle de confiance à 95 % et effectif.
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    masque = ~(np.isnan(x) | np.isnan(y))
    x, y = x[masque], y[masque]
    n = len(x)

    if n < 3:
        return None

    resultat = stats.linregress(x, y)

    # Intervalle de confiance à 95 % sur la pente (loi de Student, n-2 ddl).
    marge = resultat.stderr * stats.t.ppf(0.975, n - 2)

    return {
        "pente": float(resultat.slope),
        "ordonnee": float(resultat.intercept),
        "r2": float(resultat.rvalue ** 2),
        "r": float(resultat.rvalue),
        "p_value": float(resultat.pvalue),
        "stderr": float(resultat.stderr),
        "ic_bas": float(resultat.slope - marge),
        "ic_haut": float(resultat.slope + marge),
        "n": int(n),
        "significatif": bool(resultat.pvalue < 0.05),
    }


def tendance_temporelle(serie, colonne_temps="annee", colonne_valeur="valeur"):
    """Tendance annuelle d'une série : de combien d'unités par an ?"""

    data = serie.dropna(subset=[colonne_temps, colonne_valeur])
    modele = ols(data[colonne_temps], data[colonne_valeur])

    if modele is None:
        return None

    modele["par_an"] = modele["pente"]
    modele["par_decennie"] = modele["pente"] * 10
    modele["debut"] = int(data[colonne_temps].min())
    modele["fin"] = int(data[colonne_temps].max())

    return modele


def elasticite(x_serie, y_serie, sur="annee"):
    """Élasticité de y par rapport à x : régression log-log.

    La pente d'une régression log(y) ~ log(x) se lit directement en pourcentage :
    « quand x augmente de 1 %, y varie de b % ». C'est la façon correcte de
    comparer deux séries d'unités différentes (ici un taux de scolarisation et
    une dépense en % du PIB par habitant).
    """

    fusion = pd.merge(
        x_serie[[sur, "valeur"]].rename(columns={"valeur": "x"}),
        y_serie[[sur, "valeur"]].rename(columns={"valeur": "y"}),
        on=sur, how="inner",
    )
    fusion = fusion[(fusion["x"] > 0) & (fusion["y"] > 0)]

    if len(fusion) < 3:
        return None

    modele = ols(np.log(fusion["x"]), np.log(fusion["y"]))

    if modele is None:
        return None

    modele["periode"] = (int(fusion[sur].min()), int(fusion[sur].max()))
    modele["elasticite"] = modele["pente"]

    return modele


def correlation(x_serie, y_serie, sur="annee"):
    """Pearson (linéaire) ET Spearman (monotone) sur la période commune.

    Les deux sont donnés à dessein : un écart marqué entre les deux signale une
    relation monotone mais non linéaire, qu'un seul coefficient masquerait.
    """

    fusion = pd.merge(
        x_serie[[sur, "valeur"]].rename(columns={"valeur": "x"}),
        y_serie[[sur, "valeur"]].rename(columns={"valeur": "y"}),
        on=sur, how="inner",
    ).dropna()

    n = len(fusion)

    if n < 3:
        return None

    pearson_r, pearson_p = stats.pearsonr(fusion["x"], fusion["y"])
    spearman_r, spearman_p = stats.spearmanr(fusion["x"], fusion["y"])

    return {
        "pearson_r": float(pearson_r),
        "pearson_p": float(pearson_p),
        "spearman_r": float(spearman_r),
        "spearman_p": float(spearman_p),
        "n": int(n),
        "periode": (int(fusion[sur].min()), int(fusion[sur].max())),
        "significatif": bool(pearson_p < 0.05),
    }


def rupture_de_tendance(serie, annee_rupture, colonne_temps="annee",
                        colonne_valeur="valeur"):
    """Compare la tendance avant et après une année charnière.

    Test de Chow simplifié : on estime deux droites et on regarde si les pentes
    diffèrent. Utile pour objectiver une « accélération » qu'on croit voir.
    """

    data = serie.dropna(subset=[colonne_temps, colonne_valeur])
    avant = data[data[colonne_temps] < annee_rupture]
    apres = data[data[colonne_temps] >= annee_rupture]

    modele_avant = ols(avant[colonne_temps], avant[colonne_valeur])
    modele_apres = ols(apres[colonne_temps], apres[colonne_valeur])

    if not modele_avant or not modele_apres:
        return None

    return {
        "annee_rupture": annee_rupture,
        "avant": modele_avant,
        "apres": modele_apres,
        "acceleration": modele_apres["pente"] - modele_avant["pente"],
        "rapport": (
            modele_apres["pente"] / modele_avant["pente"]
            if modele_avant["pente"] else None
        ),
    }


def concentration(effectifs):
    """Concentration territoriale : Herfindahl-Hirschman et Gini.

    HHI = somme des carrés des parts (0 = parfaitement réparti, 1 = tout dans
    une seule unité). Gini = inégalité de la répartition (0 = égalité parfaite).
    Deux mesures complémentaires : le HHI réagit surtout au poids du plus gros,
    le Gini à la forme d'ensemble de la distribution.
    """

    valeurs = np.asarray([v for v in effectifs if v is not None], dtype=float)
    valeurs = valeurs[valeurs >= 0]
    total = valeurs.sum()

    if total <= 0 or len(valeurs) < 2:
        return None

    parts = valeurs / total
    hhi = float((parts ** 2).sum())

    # Gini par la formule de la moyenne des écarts absolus.
    tri = np.sort(valeurs)
    n = len(tri)
    index = np.arange(1, n + 1)
    gini = float((2 * (index * tri).sum()) / (n * tri.sum()) - (n + 1) / n)

    # HHI d'une répartition parfaitement égale, pour situer la valeur observée.
    hhi_equilibre = 1 / n

    return {
        "hhi": hhi,
        "hhi_equilibre": hhi_equilibre,
        "hhi_normalise": (hhi - hhi_equilibre) / (1 - hhi_equilibre) if n > 1 else 0,
        "gini": gini,
        "unites": int(n),
        "part_max": float(parts.max()),
    }


def execution_vs_montant(budget):
    """Le taux d'exécution baisse-t-il quand l'enveloppe augmente ?

    Teste l'hypothèse « une hausse brutale des crédits ne peut pas être
    absorbée » sur les données réelles, plutôt que de l'affirmer.
    """

    data = budget.dropna(subset=["es_vote", "es_execute"]).copy()
    data["taux"] = data["es_execute"] / data["es_vote"] * 100
    data["variation_vote"] = data["es_vote"].pct_change() * 100

    valides = data.dropna(subset=["variation_vote"])

    if len(valides) < 3:
        return None

    modele = ols(valides["variation_vote"], valides["taux"])

    if modele:
        modele["observations"] = valides[["annee", "variation_vote", "taux"]]

    return modele
