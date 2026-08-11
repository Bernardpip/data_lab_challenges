"""Recettes — analyses qui NÉCESSITENT plusieurs fichiers.

Une recette est un croisement : elle ne produit rien qu'un fichier seul
pourrait donner. Chacune déclare explicitement ses ingrédients, sa clé de
jointure et le nombre d'observations conservées après jointure — cette
dernière information étant décisive, une jointure sur 3 années communes ne
permettant pas les mêmes conclusions qu'une jointure sur 10.

Deux règles tenues ici :
  · jointure INTERNE uniquement — pas de remplissage des années manquantes ;
  · le rapprochement géographique passe par une table de correspondance
    explicite et vérifiable, jamais par un appariement flou de noms.
"""

import pandas as pd

from socle.i18n.traduction import t


# Chef-lieu → région. Cinq correspondances sont attestées par le fichier des
# formations techniques (la ville y figure avec sa région) ; les trois autres
# le sont par leur préfecture, elle aussi présente dans ce fichier :
# Ogou → Plateaux, Zio et Lacs → Maritime.
VILLE_REGION = {
    "Lomé": "Maritime",
    "Tsévié": "Maritime",
    "Afangnan": "Maritime",
    "Atakpamé": "Plateaux",
    "Kpalimé": "Plateaux",
    "Sokodé": "Centrale",
    "Kara": "Kara",
    "Dapaong": "Savanes",
}

# Chef-lieu → préfecture. Sert à POSITIONNER les villes du supérieur, qui ne
# portent aucune coordonnée : le fichier des formations techniques, lui, est
# géolocalisé et couvre les 32 préfectures. Chaque ville est donc placée au
# barycentre des établissements techniques de sa préfecture — une position
# CALCULÉE sur les données, jamais une coordonnée saisie à la main.
VILLE_PREFECTURE = {
    "Lomé": "Golfe",
    "Tsévié": "Zio",
    "Afangnan": "Lacs",
    "Atakpamé": "Ogou",
    "Kpalimé": "Kloto",
    "Sokodé": "Tchaoudjo",
    "Kara": "Kozah",
    "Dapaong": "Tône",
}


# Comment chaque correspondance ville → région est établie. Clés de traduction :
# la vue les affiche, elles doivent suivre la langue.
VILLE_SOURCE = {
    "Lomé": "source_attestee",
    "Kpalimé": "source_attestee",
    "Sokodé": "source_attestee",
    "Kara": "source_attestee",
    "Dapaong": "source_attestee",
    "Atakpamé": "source_ogou",
    "Tsévié": "source_zio",
    "Afangnan": "source_lacs",
}


def _joindre_annees(gauche, droite, nom_gauche, nom_droite):
    """Jointure interne sur l'année, avec traçabilité du nombre de points."""

    fusion = pd.merge(
        gauche[["annee", "valeur"]].rename(columns={"valeur": nom_gauche}),
        droite[["annee", "valeur"]].rename(columns={"valeur": nom_droite}),
        on="annee", how="inner",
    ).dropna()

    return fusion.sort_values("annee").reset_index(drop=True)


# ─── Recette 1 : accès et moyens ────────────────────────────────────────────

def acces_et_moyens(inscriptions, depenses):
    """Inscriptions × dépenses par étudiant — l'effet ciseaux.

    Les deux séries n'ont ni la même unité ni la même échelle : elles sont
    ramenées à un indice base 100 sur leur première année COMMUNE, ce qui
    autorise un seul axe et rend l'écart mesurable.
    """

    tr = t("recettes")

    fusion = _joindre_annees(inscriptions, depenses, "acces", "depense")

    if len(fusion) < 3:
        return None

    base = fusion.iloc[0]
    fusion["acces_indice"] = fusion["acces"] / base["acces"] * 100
    fusion["depense_indice"] = fusion["depense"] / base["depense"] * 100
    fusion["ecart"] = fusion["acces_indice"] - fusion["depense_indice"]

    return {
        "ingredients": [tr("ing_inscriptions"), tr("ing_depenses")],
        "cle": tr("cle_annee"),
        "observations": len(fusion),
        "periode": (int(fusion["annee"].min()), int(fusion["annee"].max())),
        "table": fusion,
        "acces_final": float(fusion["acces_indice"].iloc[-1]),
        "depense_finale": float(fusion["depense_indice"].iloc[-1]),
        "ecart_final": float(fusion["ecart"].iloc[-1]),
    }


# ─── Recette 2 : budget rapporté à l'accès ──────────────────────────────────

def budget_par_acces(budget, inscriptions):
    """Budget du supérieur × inscriptions — l'effort en FRANCS par point d'accès.

    Complète la recette 1, qui raisonne en pourcentage du PIB par habitant.
    Ici le budget est en millions de FCFA : on mesure donc l'effort en
    monnaie, ce que l'indicateur international ne permet pas.
    """

    tr = t("recettes")

    gauche = budget[["annee", "es_vote", "es_execute"]].dropna()
    fusion = pd.merge(
        gauche,
        inscriptions[["annee", "valeur"]].rename(columns={"valeur": "taux_acces"}),
        on="annee", how="inner",
    )

    if len(fusion) < 3:
        return None

    fusion["budget_par_point"] = fusion["es_vote"] / fusion["taux_acces"]
    fusion["annee"] = fusion["annee"].astype(int)

    debut, fin = fusion.iloc[0], fusion.iloc[-1]

    return {
        "ingredients": [tr("ing_budget"), tr("ing_inscriptions")],
        "cle": tr("cle_annee"),
        "observations": len(fusion),
        "periode": (int(debut["annee"]), int(fin["annee"])),
        "table": fusion,
        "evolution_budget": (fin["es_vote"] / debut["es_vote"] - 1) * 100,
        "evolution_acces": (fin["taux_acces"] / debut["taux_acces"] - 1) * 100,
        "evolution_ratio": (fin["budget_par_point"] / debut["budget_par_point"] - 1) * 100,
    }


# ─── Recette 3 : cohérence des deux mesures de financement ──────────────────

def coherence_financement(budget, depenses):
    """Budget national (FCFA) × dépense par étudiant (% du PIB/hab.).

    Deux sources décrivent le même effort public avec des unités différentes.
    Les confronter permet de vérifier qu'elles racontent la même histoire — et
    ici, elles divergent : c'est ce qui impose la précision de lecture sur
    l'indicateur international.
    """

    tr = t("recettes")

    gauche = budget[["annee", "es_vote"]].dropna()
    fusion = pd.merge(
        gauche,
        depenses[["annee", "valeur"]].rename(columns={"valeur": "depense_pib"}),
        on="annee", how="inner",
    )

    if len(fusion) < 3:
        return None

    fusion["annee"] = fusion["annee"].astype(int)
    base = fusion.iloc[0]
    fusion["budget_indice"] = fusion["es_vote"] / base["es_vote"] * 100
    fusion["depense_indice"] = fusion["depense_pib"] / base["depense_pib"] * 100

    debut, fin = fusion.iloc[0], fusion.iloc[-1]

    return {
        "ingredients": [tr("ing_budget"), tr("ing_depenses")],
        "cle": tr("cle_annee"),
        "observations": len(fusion),
        "periode": (int(debut["annee"]), int(fin["annee"])),
        "table": fusion,
        "budget_evolution": (fin["es_vote"] / debut["es_vote"] - 1) * 100,
        "depense_evolution": (fin["depense_pib"] / debut["depense_pib"] - 1) * 100,
        "divergent": bool(
            (fin["es_vote"] > debut["es_vote"]) != (fin["depense_pib"] > debut["depense_pib"])
        ),
    }


# ─── Recette 4 : deux réseaux sur un même territoire ────────────────────────

def reseaux_par_region(formations, superieur):
    """Formations techniques × établissements du supérieur, par région.

    Le seul croisement GÉOGRAPHIQUE possible du corpus. Le fichier du
    supérieur ne connaît que des villes : elles sont ramenées à leur région
    via une table de correspondance explicite (cf. VILLE_REGION).
    """

    tr = t("recettes")

    technique = (
        formations.groupby("region").size()
        .reset_index(name="technique")
    )

    sup = superieur.copy()
    sup["region"] = sup["ville"].map(VILLE_REGION)
    non_apparies = sup[sup["region"].isna()]["ville"].unique().tolist()

    sup_region = (
        sup.dropna(subset=["region"])
        .groupby("region")["valeur"].sum()
        .reset_index(name="superieur")
    )

    fusion = pd.merge(technique, sup_region, on="region", how="outer").fillna(0)
    fusion["technique"] = fusion["technique"].astype(int)
    fusion["superieur"] = fusion["superieur"].astype(int)
    fusion["total"] = fusion["technique"] + fusion["superieur"]

    total_tech = fusion["technique"].sum()
    total_sup = fusion["superieur"].sum()

    fusion["part_technique"] = fusion["technique"] / total_tech * 100
    fusion["part_superieur"] = fusion["superieur"] / total_sup * 100
    # Écart de traitement : la région est-elle mieux servie en technique
    # qu'en supérieur, ou l'inverse ?
    fusion["ecart_points"] = fusion["part_technique"] - fusion["part_superieur"]

    fusion = fusion.sort_values("total", ascending=False).reset_index(drop=True)

    return {
        "ingredients": [tr("ing_formations"), tr("ing_superieur")],
        "cle": tr("cle_region"),
        "observations": len(fusion),
        "table": fusion,
        "non_apparies": non_apparies,
        "total_technique": int(total_tech),
        "total_superieur": int(total_sup),
        "correspondance": VILLE_REGION,
        "sources_correspondance": VILLE_SOURCE,
        "millesimes": tr("millesimes_reseaux"),
    }


# ─── Recette 5 : accès et insertion ─────────────────────────────────────────

def acces_et_insertion(inscriptions, chomage):
    """Inscriptions × chômage des diplômés.

    Recette volontairement conservée malgré sa faiblesse : cinq années
    communes seulement. Elle sert à montrer que le croisement le plus attendu
    du sujet est précisément celui que les données ne permettent pas de
    trancher.
    """

    tr = t("recettes")

    fusion = _joindre_annees(inscriptions, chomage, "acces", "chomage")

    if len(fusion) < 3:
        return None

    return {
        "ingredients": [tr("ing_inscriptions"), tr("ing_chomage")],
        "cle": tr("cle_annee"),
        "observations": len(fusion),
        "periode": (int(fusion["annee"].min()), int(fusion["annee"].max())),
        "table": fusion,
        "suffisant": len(fusion) >= 10,
    }


def villes_situees(superieur, formations):
    """Villes du supérieur, positionnées à partir du fichier technique.

    Le fichier du supérieur n'a aucune coordonnée ; celui des formations
    techniques en a pour ses 256 établissements. La position d'une ville est
    donc le barycentre des établissements techniques de SA PRÉFECTURE.

    C'est une approximation, et elle est annoncée comme telle : le point ne
    marque pas le centre exact de la ville mais le centre de gravité de
    l'offre technique alentour. L'écart est de quelques kilomètres là où la
    préfecture compte beaucoup d'établissements, davantage là où elle n'en
    compte qu'un ou deux — la colonne `appuis` permet de le juger.
    """

    positions = (
        formations.dropna(subset=["lat", "lon"])
        .groupby("prefecture")
        .agg(lat=("lat", "mean"), lon=("lon", "mean"), appuis=("lat", "size"))
        .reset_index()
    )

    par_ville = (
        superieur.pivot_table(
            index="ville", columns="statut", values="valeur", aggfunc="sum"
        )
        .fillna(0)
        .reset_index()
    )

    for colonne in ("Public", "Privé"):
        if colonne not in par_ville.columns:
            par_ville[colonne] = 0

    par_ville["total"] = par_ville["Public"] + par_ville["Privé"]
    par_ville["prefecture"] = par_ville["ville"].map(VILLE_PREFECTURE)
    par_ville["region"] = par_ville["ville"].map(VILLE_REGION)

    situees = par_ville.merge(positions, on="prefecture", how="left")

    # Une ville sans position ne doit pas disparaître silencieusement de la
    # carte : elle est signalée à l'appelant.
    sans_position = situees[situees["lat"].isna()]["ville"].tolist()

    return situees.dropna(subset=["lat", "lon"]), sans_position


def acces_et_effectifs(inscriptions, indicateurs):
    """Taux brut d'inscription × effectifs absolus — le contrôle qui manquait.

    Pendant huit ressources, l'accès n'était mesurable qu'en TAUX : un
    pourcentage de la classe d'âge, dont on ne pouvait pas dire s'il montait
    parce que les étudiants étaient plus nombreux ou parce que la classe d'âge
    était plus petite. Le neuvième jeu donne les effectifs absolus : les
    confronter tranche la question.
    """

    tr = t("recettes")

    effectifs = indicateurs[indicateurs["cle"] == "effectifs"][["annee", "valeur"]]

    fusion = pd.merge(
        inscriptions[["annee", "valeur"]].rename(columns={"valeur": "taux"}),
        effectifs.rename(columns={"valeur": "effectifs"}),
        on="annee", how="inner",
    ).dropna().sort_values("annee").reset_index(drop=True)

    if len(fusion) < 3:
        return None

    base = fusion.iloc[0]
    fusion["taux_indice"] = fusion["taux"] / base["taux"] * 100
    fusion["effectifs_indice"] = fusion["effectifs"] / base["effectifs"] * 100
    fusion["annee"] = fusion["annee"].astype(int)

    debut, fin = fusion.iloc[0], fusion.iloc[-1]

    return {
        "ingredients": [tr("ing_inscriptions"), tr("ing_indicateurs")],
        "cle": tr("cle_annee"),
        "observations": len(fusion),
        "periode": (int(debut["annee"]), int(fin["annee"])),
        "table": fusion,
        "var_taux": (fin["taux"] / debut["taux"] - 1) * 100,
        "var_effectifs": (fin["effectifs"] / debut["effectifs"] - 1) * 100,
        # Si les effectifs croissent PLUS vite que le taux, la classe d'âge
        # s'est elle aussi élargie : la massification est démographique autant
        # que scolaire.
        "ecart_points": float(fin["effectifs_indice"] - fin["taux_indice"]),
    }


def inventaire(data):
    """Toutes les recettes, avec leur solidité — pour la vue de synthèse."""

    r1 = acces_et_moyens(data["inscriptions"], data["depenses"])
    r2 = budget_par_acces(data["budget"], data["inscriptions"])
    r3 = coherence_financement(data["budget"], data["depenses"])
    r4 = reseaux_par_region(data["formations"], data["superieur"])
    r5 = acces_et_insertion(data["inscriptions"], data["chomage"])
    r6 = acces_et_effectifs(data["inscriptions"], data["indicateurs_sup"])

    return {
        "acces_et_moyens": r1,
        "budget_par_acces": r2,
        "coherence_financement": r3,
        "reseaux_par_region": r4,
        "acces_et_insertion": r5,
        "acces_et_effectifs": r6,
    }
