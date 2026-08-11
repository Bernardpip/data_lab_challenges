"""Analyses — ce que les données disent réellement, calculé une fois et
réutilisé par les vues (les graphes ne recalculent rien).

Fil conducteur du tableau de bord :
  massification de l'accès (inscriptions ×34 depuis 1971)
  + effondrement de la dépense publique par étudiant (−72 % depuis 1998)
  + concentration territoriale extrême (Maritime, Grand Lomé)
  = inadéquation entre l'offre de formation, les moyens publics et l'insertion.
"""

import pandas as pd

from utils.clean import NON_RENSEIGNE


# ─── Territoire ─────────────────────────────────────────────────────────────

def par_region(formations):
    """Nombre d'établissements techniques par région, + part du total."""

    out = (
        formations.groupby("region")
        .size()
        .reset_index(name="etablissements")
        .sort_values("etablissements", ascending=False)
    )
    out["part"] = out["etablissements"] / out["etablissements"].sum() * 100

    return out


def par_prefecture(formations, top=12):
    out = (
        formations.groupby(["prefecture", "region"])
        .size()
        .reset_index(name="etablissements")
        .sort_values("etablissements", ascending=False)
    )

    return out.head(top)


def concentration(formations):
    """Indicateurs de concentration territoriale."""

    regions = par_region(formations)
    prefs = par_prefecture(formations, top=2)

    return {
        "region_tete": regions.iloc[0]["region"],
        "part_region_tete": regions.iloc[0]["part"],
        "part_deux_prefectures": prefs["etablissements"].sum() / len(formations) * 100,
        "region_queue": regions.iloc[-1]["region"],
        "etab_region_queue": int(regions.iloc[-1]["etablissements"]),
        "total": len(formations),
        "regions": len(regions),
        "prefectures": formations["prefecture"].nunique(),
    }


def creation_par_decennie(formations):
    """Rythme de création des établissements techniques, par décennie.

    Le fichier date chaque création : c'est la seule série longue
    INFRANATIONALE du corpus — les autres séries longues sont nationales.
    """

    annees = formations["annee_creation"].dropna()

    if annees.empty:
        return pd.DataFrame(columns=["decennie", "creations", "cumul"])

    out = (
        (annees // 10 * 10).astype(int)
        .value_counts()
        .sort_index()
        .reset_index()
    )
    out.columns = ["decennie", "creations"]
    out["cumul"] = out["creations"].cumsum()
    out["libelle"] = out["decennie"].astype(str) + "s"

    return out


def creation_par_region_decennie(formations, depuis=1990):
    """Créations par décennie ET par région — montre QUAND la concentration
    territoriale s'est installée, ce qu'un total ne peut pas dire."""

    data = formations.dropna(subset=["annee_creation"]).copy()
    data = data[data["annee_creation"] >= depuis]
    data["decennie"] = (data["annee_creation"] // 10 * 10).astype(int).astype(str) + "s"

    matrice = pd.crosstab(data["region"], data["decennie"])
    ordre = matrice.sum(axis=1).sort_values(ascending=False).index

    return matrice.loc[ordre]


def infrastructures(formations):
    """État des équipements : assainissement, terrain de sport, foncier.

    Le jeu de données annonce documenter « la qualité des infrastructures et
    des équipements » — ces trois champs sont les seuls qui la mesurent.
    """

    total = max(len(formations), 1)

    sanitaire = (
        formations.groupby("sanitaire").size()
        .reset_index(name="etablissements")
        .sort_values("etablissements", ascending=False)
    )
    foncier = (
        formations.groupby("foncier_famille").size()
        .reset_index(name="etablissements")
        .sort_values("etablissements", ascending=False)
    )

    avec_sport = int((formations["sport"] == "Oui").sum())
    sans_sport = int((formations["sport"] == "Non").sum())
    prive = int((formations["foncier_famille"] == "Privé (individuel ou entreprise)").sum())
    wc = int((formations["sanitaire"] == "WC").sum())
    non_renseigne_sanitaire = int((formations["sanitaire"] == NON_RENSEIGNE).sum())

    return {
        "sanitaire": sanitaire,
        "foncier": foncier,
        "part_sport": avec_sport / total * 100,
        "sans_sport": sans_sport,
        "part_prive": prive / total * 100,
        "part_wc": wc / total * 100,
        "part_sanitaire_inconnu": non_renseigne_sanitaire / total * 100,
        "total": total,
    }


def amplitude_ouverture(formations):
    """Jours d'ouverture par semaine — proxy d'intensité de service."""

    jours = formations["jours_ouverture"].dropna()

    if jours.empty:
        return None

    out = (
        jours.astype(int).value_counts().sort_index().reset_index()
    )
    out.columns = ["jours", "etablissements"]
    out["libelle"] = out["jours"].astype(str) + " jours"

    return {
        "distribution": out,
        "mediane": float(jours.median()),
        "part_5_jours": (jours == 5).sum() / len(jours) * 100,
        "au_dela_de_5": int((jours > 5).sum()),
    }


def maillage(formations):
    """Finesse du maillage territorial : combien d'échelons sont couverts."""

    return {
        "regions": formations["region"].nunique(),
        "prefectures": formations["prefecture"].nunique(),
        "communes": formations["commune_nom_bdd"].nunique(),
        "cantons": formations["canton_nom_bdd"].nunique(),
        "localites": formations["nom_localite"].nunique(),
    }


def grille_region_categorie(formations, top_categories=5):
    """Matrice filière × région (magnitude sur grille).

    Les filières portent des libellés longs : elles vont en LIGNES, où le texte
    se lit à plat. Mises en colonnes, elles devraient être pivotées à 45° et
    déborderaient du cadre.
    """

    top = formations["categorie"].value_counts().head(top_categories).index.tolist()
    data = formations[formations["categorie"].isin(top)]

    matrice = pd.crosstab(data["categorie"], data["region"])

    lignes = matrice.sum(axis=1).sort_values(ascending=False).index
    colonnes = matrice.sum(axis=0).sort_values(ascending=False).index

    return matrice.loc[lignes, colonnes]


# ─── Enseignement supérieur ─────────────────────────────────────────────────

def superieur_par_ville(superieur):
    """Établissements du supérieur par ville, ventilés public / privé."""

    out = (
        superieur.pivot_table(
            index="ville", columns="statut", values="valeur", aggfunc="sum"
        )
        .fillna(0)
        .reset_index()
    )

    for col in ("Public", "Privé"):
        if col not in out.columns:
            out[col] = 0

    out["total"] = out["Public"] + out["Privé"]

    # Une ville à 0 établissement produirait une barre de longueur nulle.
    out = out[out["total"] > 0]

    return out.sort_values("total", ascending=False)


def superieur_synthese(superieur):
    villes = superieur_par_ville(superieur)
    total = villes["total"].sum()
    lome = villes.loc[villes["ville"].str.lower() == "lomé", "total"]

    return {
        "total": int(total),
        "part_prive": villes["Privé"].sum() / total * 100 if total else 0,
        "part_lome": (lome.iloc[0] / total * 100) if total and len(lome) else 0,
        "villes": int((villes["total"] > 0).sum()),
        "annee": int(superieur["annee"].max()),
    }


# ─── Financement ────────────────────────────────────────────────────────────

def execution_budgetaire(budget):
    """Taux d'exécution du budget de l'enseignement supérieur et écart au voté.

    L'écart (en points de %) est une mesure de POLARITÉ : au-dessus ou en
    dessous de l'enveloppe votée.
    """

    out = budget.dropna(subset=["es_vote", "es_execute"]).copy()
    out["taux"] = out["es_execute"] / out["es_vote"] * 100
    out["ecart"] = out["taux"] - 100
    out["part_national"] = out["es_vote"] / out["national_vote"] * 100
    out["part_education"] = out["es_vote"] / out["educ_vote"] * 100
    out["annee"] = out["annee"].astype(int)

    return out


def execution_comparee(budget):
    """Taux d'exécution comparé : enseignement supérieur / éducation / État.

    Isole ce qui relève du supérieur de ce qui est un travers budgétaire
    général — sans ce point de comparaison, on attribuerait au supérieur une
    sous-exécution qui touche peut-être tout le budget.
    """

    out = budget.dropna(subset=["es_vote", "es_execute"]).copy()

    out["taux_es"] = out["es_execute"] / out["es_vote"] * 100
    out["taux_educ"] = out["educ_execute"] / out["educ_vote"] * 100
    out["taux_national"] = out["national_execute"] / out["national_vote"] * 100
    out["annee"] = out["annee"].astype(int)

    return out[["annee", "taux_es", "taux_educ", "taux_national"]]


def subvention_prive(budget):
    """Subvention de l'État aux établissements PRIVÉS du supérieur.

    Constat brut : elle est à zéro sur toute la période documentée, alors que
    le privé porte l'essentiel du réseau. Rapporté au réseau, c'est le
    chiffre le plus parlant du jeu budgétaire.
    """

    out = budget.dropna(subset=["subvention_prive"]).copy()
    out["annee"] = out["annee"].astype(int)

    return {
        "serie": out[["annee", "subvention_prive"]],
        "total": float(out["subvention_prive"].sum()),
        "annees": len(out),
        "toujours_nulle": bool((out["subvention_prive"] == 0).all()),
    }


def poids_education(budget):
    """Part de l'éducation et du supérieur dans le budget national voté."""

    out = budget.dropna(subset=["educ_vote", "national_vote"]).copy()

    out["part_educ_national"] = out["educ_vote"] / out["national_vote"] * 100
    out["part_es_educ"] = out["es_vote"] / out["educ_vote"] * 100
    out["part_es_national"] = out["es_vote"] / out["national_vote"] * 100
    out["annee"] = out["annee"].astype(int)

    return out[["annee", "part_educ_national", "part_es_educ", "part_es_national"]]


def credits_non_consommes(budget):
    """Écart voté − exécuté en MONTANTS, pas en taux.

    Un taux d'exécution de 92 % ne dit rien de l'enjeu financier : selon
    l'enveloppe, il représente 1,7 milliard ou 190 milliards de FCFA. Cette
    vue ramène les trois niveaux à la même échelle monétaire.
    """

    out = budget.dropna(subset=["es_vote", "es_execute"]).copy()

    out["non_consomme_es"] = out["es_vote"] - out["es_execute"]
    out["non_consomme_educ"] = out["educ_vote"] - out["educ_execute"]
    out["non_consomme_national"] = out["national_vote"] - out["national_execute"]
    out["annee"] = out["annee"].astype(int)

    colonnes = ["annee", "non_consomme_es", "non_consomme_educ", "non_consomme_national"]

    return {
        "serie": out[colonnes],
        "cumul_national": float(out["non_consomme_national"].sum()),
        "cumul_educ": float(out["non_consomme_educ"].sum()),
        "cumul_es": float(out["non_consomme_es"].sum()),
        # Années où le secteur a dépensé PLUS que voté (écart négatif).
        "surexecution_educ": out.loc[out["non_consomme_educ"] < 0, "annee"].tolist(),
    }


def croissance_budgetaire(budget):
    """Croissance des enveloppes votées entre le premier et le dernier exercice.

    Répond à une question que les taux d'exécution ne traitent pas : le
    supérieur a-t-il été priorisé, ou simplement porté par la hausse générale
    du budget de l'État ?
    """

    out = budget.dropna(subset=["es_vote", "educ_vote", "national_vote"]).copy()
    out["annee"] = out["annee"].astype(int)

    debut, fin = out.iloc[0], out.iloc[-1]

    def evolution(colonne):
        return (fin[colonne] / debut[colonne] - 1) * 100

    return {
        "periode": (int(debut["annee"]), int(fin["annee"])),
        "es": evolution("es_vote"),
        "educ": evolution("educ_vote"),
        "national": evolution("national_vote"),
        "montants": out[["annee", "es_vote", "educ_vote", "national_vote"]],
    }


def poids_dans_le_pib(budget):
    """Part du PIB consacrée à chaque niveau — uniquement les années où le PIB
    est renseigné (deux seulement : le fichier ne le fournit pas ailleurs)."""

    out = budget.dropna(subset=["pib"]).copy()

    if out.empty:
        return None

    out["annee"] = out["annee"].astype(int)
    out["part_national"] = out["national_vote"] / out["pib"] * 100
    out["part_educ"] = out["educ_vote"] / out["pib"] * 100
    out["part_es"] = out["es_vote"] / out["pib"] * 100

    return out[["annee", "part_national", "part_educ", "part_es"]]


def ciseaux(inscriptions, depenses, base=1998):
    """Les deux courbes indexées à 100 sur l'année de base commune.

    Deux mesures d'unités différentes (% brut d'inscription vs % du PIB par
    habitant) : les indexer sur une base commune permet de les lire sur UN
    SEUL axe, au lieu d'un double axe qui inventerait une corrélation.

    La base doit être une année où les DEUX séries ont une mesure : indexer
    chacune sur son propre premier point comparerait des trajectoires parties
    d'endroits différents, et l'écart lu ne voudrait plus rien dire. `base`
    n'est donc qu'un plancher — la base retenue est la première année commune
    à partir de là. Renvoie une liste vide si elles n'en partagent aucune.
    """

    communes = sorted(
        set(inscriptions[inscriptions["annee"] >= base]["annee"])
        & set(depenses[depenses["annee"] >= base]["annee"])
    )

    if not communes:
        return []

    reference_annee = communes[0]

    def index_serie(df, nom):
        data = df[df["annee"] >= reference_annee]
        reference = data[data["annee"] == reference_annee].iloc[0]["valeur"]

        return {
            "name": nom,
            "x": data["annee"].tolist(),
            "y": (data["valeur"] / reference * 100).tolist(),
        }

    # Les deux noms sont affichés en légende : ils viennent du domaine
    # partagé, pas d'une chaîne écrite ici.
    from socle.i18n.traduction import t
    tc = t("commun")

    return [
        index_serie(inscriptions, tc("serie_inscriptions")),
        index_serie(depenses, tc("serie_depense_etudiant")),
    ]


def annee_de_base(inscriptions, depenses, base=1998):
    """Année sur laquelle `ciseaux` indexe réellement — pour l'afficher."""

    communes = sorted(
        set(inscriptions[inscriptions["annee"] >= base]["annee"])
        & set(depenses[depenses["annee"] >= base]["annee"])
    )

    return int(communes[0]) if communes else None


# ─── Score de priorité territoriale ─────────────────────────────────────────

def score_territorial(formations):
    """Classement des régions à renforcer.

    Score = couverture en établissements (60 %) + étendue préfectorale
    couverte (40 %), ramené sur 100. Un score bas = territoire prioritaire.
    Le chômage des diplômés n'est disponible qu'au niveau NATIONAL : il ne
    peut pas entrer dans un score régional sans inventer de la donnée.
    """

    base = (
        formations.groupby("region")
        .agg(
            etablissements=("etab_nom", "count"),
            prefectures=("prefecture", "nunique"),
        )
        .reset_index()
    )

    def normalise(colonne):
        span = colonne.max() - colonne.min()
        return (colonne - colonne.min()) / span * 100 if span else colonne * 0 + 100

    base["score"] = (
        normalise(base["etablissements"]) * 0.6
        + normalise(base["prefectures"]) * 0.4
    )

    base["niveau"] = pd.cut(
        base["score"],
        bins=[-0.01, 25, 60, 100],
        labels=["critical", "warning", "good"],
    ).astype(str)

    return base.sort_values("score")


# ─── Indicateurs clés du supérieur (DICES-TG) ────────────────────────────────

def evolution_sup(indicateurs, cle):
    """Début, fin et variation d'une série de DICES-TG.

    Renvoie None si la série a moins de deux points : une variation calculée
    sur une seule mesure n'existe pas.
    """

    serie = indicateurs[indicateurs["cle"] == cle].sort_values("annee")

    if len(serie) < 2:
        return None

    debut, fin = serie.iloc[0], serie.iloc[-1]

    return {
        # Identifiants stables : la vue les traduit (`ind_<cle>` et l'unité).
        "cle": cle,
        "unite_cle": fin["unite_cle"],
        "serie": serie,
        "annee_debut": int(debut["annee"]),
        "annee_fin": int(fin["annee"]),
        "valeur_debut": float(debut["valeur"]),
        "valeur_fin": float(fin["valeur"]),
        "variation_pct": (fin["valeur"] / debut["valeur"] - 1) * 100,
        "variation_points": float(fin["valeur"] - debut["valeur"]),
        "n": len(serie),
    }


def enseignants_implicites(indicateurs):
    """Nombre d'enseignants des universités publiques, reconstitué.

    Le fichier ne publie pas les effectifs enseignants, mais il publie de quoi
    les retrouver EXACTEMENT — sans hypothèse :

      · les effectifs étudiants totaux ;
      · deux densités pour 100 000 habitants (tous étudiants, puis ceux du
        public seul). Leur rapport donne la part du public, car les deux
        densités partagent le même denominateur de population ;
      · le ratio étudiant/enseignant des universités publiques.

    D'où : enseignants = effectifs × part du public ÷ ratio.

    C'est un indicateur DÉRIVÉ, et il est présenté comme tel. Il n'est calculé
    que pour les années où les quatre séries coïncident.
    """

    besoin = ["effectifs", "densite_etudiants", "densite_publique",
              "ratio_encadrement"]

    large = (
        indicateurs[indicateurs["cle"].isin(besoin)]
        .pivot_table(index="annee", columns="cle", values="valeur")
        .dropna()
        .reset_index()
    )

    if large.empty:
        return None

    large["part_publique"] = large["densite_publique"] / large["densite_etudiants"] * 100
    large["effectifs_publics"] = large["effectifs"] * large["part_publique"] / 100
    large["enseignants"] = large["effectifs_publics"] / large["ratio_encadrement"]
    large["annee"] = large["annee"].astype(int)

    return large[["annee", "effectifs", "part_publique", "effectifs_publics",
                  "ratio_encadrement", "enseignants"]]


def depense_totale(indicateurs):
    """Masse financière consacrée aux étudiants : effectifs × dépense unitaire.

    Un montant par étudiant stable ne veut pas dire un effort stable : si les
    effectifs croissent, la dépense TOTALE croît d'autant. Ce croisement — que
    seul ce fichier rend possible, puisqu'il porte à la fois des effectifs
    absolus et des francs — sépare les deux lectures.
    """

    large = (
        indicateurs[indicateurs["cle"].isin(["effectifs", "depense_fcfa"])]
        .pivot_table(index="annee", columns="cle", values="valeur")
        .dropna()
        .reset_index()
    )

    if len(large) < 2:
        return None

    # En millions de FCFA : des francs par étudiant multipliés par 100 000
    # étudiants donnent des ordres de grandeur illisibles autrement.
    large["total_millions"] = large["effectifs"] * large["depense_fcfa"] / 1e6
    large["annee"] = large["annee"].astype(int)

    debut, fin = large.iloc[0], large.iloc[-1]

    return {
        "table": large,
        "periode": (int(debut["annee"]), int(fin["annee"])),
        "var_unitaire": (fin["depense_fcfa"] / debut["depense_fcfa"] - 1) * 100,
        "var_effectifs": (fin["effectifs"] / debut["effectifs"] - 1) * 100,
        "var_totale": (fin["total_millions"] / debut["total_millions"] - 1) * 100,
    }


def ecart_feminisation(indicateurs):
    """Part des femmes dans l'ensemble du supérieur vs dans le scientifique.

    Les deux séries n'ont que deux années communes, mais l'écart y est trop
    large pour être un artefact : c'est le seul endroit du corpus où une
    inégalité de parcours devient visible.
    """

    large = (
        indicateurs[indicateurs["cle"].isin(["feminite", "filles_scientifiques"])]
        .pivot_table(index="annee", columns="cle", values="valeur")
        .dropna()
        .reset_index()
    )

    if large.empty:
        return None

    large["ecart_points"] = large["feminite"] - large["filles_scientifiques"]
    large["annee"] = large["annee"].astype(int)

    return large
