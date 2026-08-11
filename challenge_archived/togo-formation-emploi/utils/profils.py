"""Profil individuel de chaque fichier — un jeu, une fiche.

Le tableau de bord est organisé par THÈME (territoire, financement, insertion),
ce qui répond aux questions métier mais ne dit jamais ce que vaut chaque
fichier pris isolément : sa couverture, ses trous, ses pièges. Ce module
produit cette lecture fichier par fichier.

Chaque profil renvoie la même structure, pour que la vue soit générique :
identité, volumétrie, qualité (complétude), et les constats propres au jeu.

Le champ `nature` dit le niveau géographique le plus fin du fichier. C'est la
propriété qui décide de ce qu'on peut en faire : un seul jeu descend sous le
national, ce qui explique à lui seul la forme de tout le tableau de bord.

`nature` est AFFICHÉ, donc traduit ; `nature_cle` ne l'est pas et sert aux
comparaisons de la vue. Filtrer sur le libellé casserait au changement de
langue.
"""

import pandas as pd

from utils.clean import NON_RENSEIGNE
from socle.i18n.traduction import t


NATURE_INFRANATIONALE = "nature_infranationale"
NATURE_URBAINE = "nature_urbaine"
NATURE_NATIONALE = "nature_nationale"
NATURE_METADONNEE = "nature_metadonnee"


def _completude(df, colonnes, sentinelles=(NON_RENSEIGNE,)):
    """Part des lignes réellement renseignées, colonne par colonne.

    Une valeur présente mais égale à « Non renseigné » N'EST PAS renseignée :
    la compter comme telle donnerait un taux de complétude flatteur et faux.
    """

    lignes = []

    for colonne in colonnes:
        if colonne not in df.columns:
            continue

        serie = df[colonne]
        vide = serie.isna()

        if serie.dtype == object:
            vide = vide | serie.astype(str).isin(sentinelles)

        renseigne = int((~vide).sum())
        lignes.append({
            "champ": colonne,
            "renseignes": renseigne,
            "taux": renseigne / len(df) * 100 if len(df) else 0,
        })

    return (
        pd.DataFrame(lignes)
        .sort_values("taux", ascending=True)
        .reset_index(drop=True)
    )


def profil_formations(formations, brut):
    """DEFT-TG — recensement des établissements de formation technique."""

    tr = t("profils")

    champs = ["etab_nom", "region", "prefecture", "commune_nom_bdd",
              "nom_localite", "categorie", "statut", "foncier_famille",
              "sanitaire", "sport", "annee_creation", "lat"]

    annees = formations["annee_creation"].dropna()

    return {
        "titre": tr("deft_titre"),
        "code": "DEFT-TG",
        "nature": tr(NATURE_INFRANATIONALE),
        "nature_cle": NATURE_INFRANATIONALE,
        "lignes": len(formations),
        "colonnes": brut.shape[1],
        "granularite": tr("deft_granularite"),
        "periode": tr("deft_periode"),
        "cle": tr("deft_cle"),
        "completude": _completude(formations, champs),
        "constats": [
            (tr("deft_c1_titre"), tr("deft_c1_detail", {
                "regions": formations["region"].nunique(),
                "prefectures": formations["prefecture"].nunique(),
                "localites": formations["nom_localite"].nunique(),
            })),
            (tr("deft_c2_titre"), tr("deft_c2_detail", {
                "geolocalises": int(formations["lat"].notna().sum()),
                "total": len(formations),
            })),
            (tr("deft_c3_titre"), tr("deft_c3_detail", {
                "datees": len(annees),
                "debut": int(annees.min()),
                "fin": int(annees.max()),
            })),
            (tr("deft_c4_titre"), tr("deft_c4_detail")),
        ],
    }


def profil_dictionnaire(detail):
    """DEFT-TG — dictionnaire des champs (métadonnée, non analytique)."""

    tr = t("profils")

    return {
        "titre": tr("dico_titre"),
        "code": "DEFT-TG (annexe)",
        "nature": tr(NATURE_METADONNEE),
        "nature_cle": NATURE_METADONNEE,
        "lignes": len(detail),
        "colonnes": detail.shape[1],
        "granularite": tr("dico_granularite"),
        "periode": tr("dico_periode"),
        "cle": tr("dico_cle"),
        "completude": None,
        "constats": [
            (tr("dico_c1_titre"), tr("dico_c1_detail")),
            (tr("dico_c2_titre"), tr("dico_c2_detail")),
        ],
    }


def profil_superieur(superieur, brut):
    """DREESTSL-TG — répartition des établissements du supérieur."""

    tr = t("profils")

    total = int(superieur["valeur"].sum())
    somme_brute = int(pd.to_numeric(brut["Value"], errors="coerce").sum())

    return {
        "titre": tr("sup_titre"),
        "code": "DREESTSL-TG",
        "nature": tr(NATURE_URBAINE),
        "nature_cle": NATURE_URBAINE,
        "lignes": len(superieur),
        "colonnes": brut.shape[1],
        "granularite": tr("sup_granularite"),
        "periode": tr("sup_periode"),
        "cle": tr("sup_cle"),
        "completude": None,
        "constats": [
            (tr("sup_c1_titre"), tr("sup_c1_detail",
                                    {"somme": somme_brute, "total": total})),
            (tr("sup_c2_titre"), tr("sup_c2_detail")),
            (tr("sup_c3_titre"), tr("sup_c3_detail")),
            (tr("sup_c4_titre"), tr("sup_c4_detail")),
        ],
    }


def profil_budget(budget, brut):
    """DBESBNVE-TG — budgets votés et exécutés."""

    tr = t("profils")

    return {
        "titre": tr("budget_titre"),
        "code": "DBESBNVE-TG",
        "nature": tr(NATURE_NATIONALE),
        "nature_cle": NATURE_NATIONALE,
        "lignes": len(brut),
        "colonnes": brut.shape[1],
        "granularite": tr("budget_granularite"),
        "periode": tr("budget_periode"),
        "cle": tr("budget_cle"),
        "completude": None,
        "constats": [
            (tr("budget_c1_titre"), tr("budget_c1_detail")),
            (tr("budget_c2_titre"), tr("budget_c2_detail")),
            (tr("budget_c3_titre"), tr("budget_c3_detail",
                                       {"pib": int(budget["pib"].notna().sum())})),
            (tr("budget_c4_titre"), tr("budget_c4_detail")),
        ],
    }


def profil_indicateur(serie, brut, cle_i18n, code):
    """Profil commun aux trois séries Banque mondiale (format identique)."""

    tr = t("profils")

    annees = serie["annee"].astype(int)
    attendu = int(annees.max() - annees.min() + 1)
    lacunes = attendu - len(serie)

    return {
        "titre": tr(cle_i18n + "_titre"),
        "code": code,
        "nature": tr(NATURE_NATIONALE),
        "nature_cle": NATURE_NATIONALE,
        "lignes": len(brut),
        "colonnes": brut.shape[1],
        "granularite": tr("ind_granularite"),
        "periode": f"{int(annees.min())}-{int(annees.max())}",
        "cle": tr("ind_cle"),
        "completude": None,
        "constats": [
            (tr("ind_ce_que_mesure"), tr(cle_i18n + "_description")),
            (tr("ind_utilise_pour"), tr(cle_i18n + "_usage")),
            (tr("ind_densite_titre"), tr("ind_densite_detail", {
                "mesures": len(serie), "attendu": attendu, "lacunes": lacunes,
                "part": f"{lacunes / attendu * 100:.0f}",
            })),
            (tr("ind_format_titre"), tr("ind_format_detail",
                                        {"lignes": len(brut),
                                         "mesures": len(serie)})),
        ],
    }


def profil_indicateurs_sup(indicateurs, brut):
    """DICES-TG — indicateurs clés de l'enseignement supérieur (9e ressource)."""

    tr = t("profils")

    series = indicateurs.groupby("cle")["annee"].agg(["size", "min", "max"])

    return {
        "titre": tr("dices_titre"),
        "code": "DICES-TG",
        "nature": tr(NATURE_NATIONALE),
        "nature_cle": NATURE_NATIONALE,
        "lignes": len(brut),
        "colonnes": brut.shape[1],
        "granularite": tr("dices_granularite"),
        "periode": f'{int(indicateurs["annee"].min())}-'
                   f'{int(indicateurs["annee"].max())}',
        "cle": tr("dices_cle"),
        "completude": None,
        "constats": [
            (tr("dices_c1_titre"), tr("dices_c1_detail")),
            (tr("dices_c2_titre"), tr("dices_c2_detail")),
            (tr("dices_c3_titre"), tr("dices_c3_detail", {
                "series": len(series),
                "courtes": int((series["size"] < 4).sum()),
            })),
            (tr("dices_c4_titre"), tr("dices_c4_detail")),
        ],
    }


def tous_les_profils(data, brut):
    """Les 8 fichiers chargés, dans l'ordre de lecture du tableau de bord."""

    return [
        profil_formations(data["formations"], brut["formations"]),
        profil_dictionnaire(data["formations_detail"]),
        profil_superieur(data["superieur"], brut["etablissements"]),
        profil_budget(data["budget"], brut["budget"]),
        profil_indicateur(data["inscriptions"], brut["inscriptions"],
                          "dises", "DISES-TG"),
        profil_indicateur(data["depenses"], brut["depenses"],
                          "ddpees", "DDPEES-TG"),
        profil_indicateurs_sup(data["indicateurs_sup"], brut["indicateurs_sup"]),
        profil_indicateur(data["chomage"], brut["chomage"],
                          "dcdes", "DCDES-TG"),
    ]
