"""Croisements multi-fichiers — chacun déclare ses ingrédients et sa solidité.

Une « recette » est un croisement que les données AUTORISENT. Deux règles la
gouvernent, et elles font la moitié de la note d'analyse :

  · **aucun croisement que les données n'autorisent pas.** Les ventes d'eau
    (nationales) et le recensement 2010 (libellés incomparables) n'entrent
    dans AUCUNE recette : les faire descendre à la maille canton fabriquerait
    une répartition que les sources ne portent pas ;

  · **chaque recette déclare ses ingrédients, sa clé et son nombre
    d'observations**, avec un seuil de solidité qui lui est propre.

La clé est toujours la même — `cle_canton`, le nom de canton normalisé — parce
que c'est le seul niveau où les trois jeux exploitables se rencontrent. La
jointure est INTERNE : un ouvrage dont le canton ne figure pas au référentiel
disparaît du croisement, il n'est jamais rattaché au hasard.

Un croisement INTRA-fichier n'est pas une recette : la relation entre le débit
et la profondeur des forages COSO vit dans `analytics.coso_technique`.
"""

# pyrefly: ignore [missing-import]
import pandas as pd

from socle.i18n.traduction import t

# Sous dix cantons, une comparaison territoriale n'établit rien : on affiche
# le décompte et l'on s'abstient de conclure. Le seuil est PAR recette, parce
# que dix cantons et dix années ne pèsent pas pareil.
SEUIL_CANTONS = 10


def _ouvrages_unifies(tde, coso):
    """Les deux parcs empilés, chacun gardant sa provenance.

    Empilés, jamais fusionnés : la colonne `parc` reste, et toute vue qui les
    additionne doit pouvoir dire d'où vient chaque unité. Les deux territoires
    étant disjoints, un total sans provenance serait un chiffre orphelin.
    """

    gauche = tde[["cle_canton", "canton", "region"]].copy()
    gauche["parc"] = "TdE"

    droite = coso[["cle_canton", "canton", "region", "plan_maintenance"]].copy()
    droite["parc"] = "COSO"

    return pd.concat([gauche, droite], ignore_index=True)


def croisement_ouvrages_risque(cantons, tde, coso):
    """R1 — où sont les ouvrages par rapport au risque d'inondation.

    C'est l'objectif n°4 de l'énoncé, et le seul croisement que le corpus
    autorise pleinement : les deux parcs portent un canton, le référentiel
    porte le risque pour les 388 cantons du pays.
    """

    tr = t("recettes")
    ouvrages = _ouvrages_unifies(tde, coso)

    par_canton = (
        ouvrages.groupby("cle_canton")
        .agg(ouvrages=("parc", "size"), parcs=("parc", "nunique"))
        .reset_index()
    )

    fusion = pd.merge(
        cantons[["cle_canton", "canton", "prefecture", "region",
                 "risque_pts", "population"]],
        par_canton, on="cle_canton", how="inner",
    )

    if len(fusion) < SEUIL_CANTONS:
        return None

    return {
        "ingredients": [tr("ing_cantons"), tr("ing_tde"), tr("ing_coso")],
        "cle": tr("cle_canton"),
        "observations": len(fusion),
        "seuil": SEUIL_CANTONS,
        "ouvrages": int(par_canton["ouvrages"].sum()),
        "table": fusion.sort_values("risque_pts", ascending=False)
                       .reset_index(drop=True),
    }


def croisement_equipement_population(cantons, tde, coso):
    """R2 — densité d'ouvrages rapportée à la population du canton.

    L'objectif n°3. La population vient de `fri-cantons` (estimation 2022),
    JAMAIS du recensement 2010 : les deux comptages diffèrent de 32 % au
    niveau national et n'ont pas la même maille. Mélanger le numérateur d'un
    millésime au dénominateur d'un autre produirait un ratio faux dont rien
    n'avertirait le lecteur.
    """

    tr = t("recettes")
    ouvrages = _ouvrages_unifies(tde, coso)

    par_canton = (
        ouvrages.groupby("cle_canton").size().reset_index(name="ouvrages")
    )

    fusion = pd.merge(
        cantons[["cle_canton", "canton", "prefecture", "region",
                 "population", "risque_pts"]],
        par_canton, on="cle_canton", how="inner",
    )
    fusion = fusion[fusion["population"] > 0]

    if len(fusion) < SEUIL_CANTONS:
        return None

    fusion["ouvrages_10k"] = 10_000 * fusion["ouvrages"] / fusion["population"]

    return {
        "ingredients": [tr("ing_cantons"), tr("ing_tde"), tr("ing_coso")],
        "cle": tr("cle_canton"),
        "observations": len(fusion),
        "seuil": SEUIL_CANTONS,
        "table": fusion.sort_values("ouvrages_10k").reset_index(drop=True),
    }


def croisement_maintenance_risque(cantons, coso):
    """R3 — les ouvrages sans plan d'entretien, situés face au risque.

    Ne mobilise que le COSO : c'est le seul jeu qui porte une variable
    d'entretien. Le parc TdE en est absent, non par oubli mais parce que le
    champ `maintenance_societe` de son dictionnaire n'est pas publié.
    """

    tr = t("recettes")

    sans_plan = coso[~coso["plan_maintenance"]]
    par_canton = (
        sans_plan.groupby("cle_canton").size().reset_index(name="sans_plan")
    )

    fusion = pd.merge(
        cantons[["cle_canton", "canton", "prefecture", "region", "risque_pts",
                 "population"]],
        par_canton, on="cle_canton", how="inner",
    )

    if len(fusion) < SEUIL_CANTONS:
        return None

    return {
        "ingredients": [tr("ing_cantons"), tr("ing_coso")],
        "cle": tr("cle_canton"),
        "observations": len(fusion),
        "seuil": SEUIL_CANTONS,
        "ouvrages": int(sans_plan.shape[0]),
        "table": fusion.sort_values(["risque_pts", "sans_plan"],
                                    ascending=False).reset_index(drop=True),
    }


def score_de_priorisation(cantons, tde, coso):
    """R4 — un ordre de priorité pour les futurs aménagements.

    Trois composantes, TOUTES issues de la maille canton, chacune ramenée
    entre 0 et 1 par son rang :

      · le risque d'inondation (FRI) — un ouvrage exposé se dégrade plus vite ;
      · la population du canton — plus d'habitants, plus d'urgence ;
      · le déficit d'équipement — nombre d'ouvrages recensés pour 10 000 hab.,
        inversé.

    Ce score n'est pas un modèle : c'est une somme de rangs, pondérée à parts
    égales et affichée comme telle. Le dire évite de lui prêter une autorité
    qu'il n'a pas — et les trois composantes restent visibles dans la table,
    pour qu'un lecteur puisse le contester.

    Le déficit d'équipement se lit sur un corpus INCOMPLET : 329 cantons n'y
    portent aucun ouvrage, ce qui traduit surtout l'absence d'inventaire
    national. Un canton mal classé n'est donc pas nécessairement démuni.
    """

    tr = t("recettes")

    ouvrages = _ouvrages_unifies(tde, coso)
    par_canton = ouvrages.groupby("cle_canton").size().reset_index(name="ouvrages")

    base = pd.merge(
        cantons[["cle_canton", "canton", "prefecture", "region",
                 "risque_pts", "population"]],
        par_canton, on="cle_canton", how="left",
    )
    base["ouvrages"] = base["ouvrages"].fillna(0)
    base["ouvrages_10k"] = 10_000 * base["ouvrages"] / base["population"].where(
        base["population"] > 0
    )
    base["ouvrages_10k"] = base["ouvrages_10k"].fillna(0)

    base["rang_risque"] = base["risque_pts"].rank(pct=True)
    base["rang_population"] = base["population"].rank(pct=True)
    base["rang_deficit"] = (-base["ouvrages_10k"]).rank(pct=True)

    base["score"] = (
        base["rang_risque"] + base["rang_population"] + base["rang_deficit"]
    ) / 3

    return {
        "ingredients": [tr("ing_cantons"), tr("ing_tde"), tr("ing_coso")],
        "cle": tr("cle_canton"),
        "observations": len(base),
        "seuil": SEUIL_CANTONS,
        "equipes": int((base["ouvrages"] > 0).sum()),
        "table": base.sort_values("score", ascending=False).reset_index(drop=True),
    }


def toutes(cantons, tde, coso):
    """Les quatre recettes, avec leur nom — pour la vue « Croisements »."""

    return [
        {"cle": "R1", "recette": croisement_ouvrages_risque(cantons, tde, coso)},
        {"cle": "R2", "recette": croisement_equipement_population(cantons, tde, coso)},
        {"cle": "R3", "recette": croisement_maintenance_risque(cantons, coso)},
        {"cle": "R4", "recette": score_de_priorisation(cantons, tde, coso)},
    ]
