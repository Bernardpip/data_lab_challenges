"""Repères externes — sourcés, cliquables, et SÉPARÉS du corpus.

Quelques chiffres qui situent le constat. Ils rendent lisible un ordre de
grandeur que le tableau de bord seul ne donne pas : 64,5 points de risque sur
Bè-Est ne dit rien tant qu'on ignore ce que les inondations ont déjà coûté au
pays.

La règle qui les accompagne est stricte : **un repère externe ne se recalcule
jamais et n'entre dans aucun graphe du corpus.** Il s'affiche dans un visuel
distinct (`ui.repere_externe`), avec sa source et son millésime.

Tous ceux qui suivent proviennent de la documentation méthodologique publiée
avec le jeu ISRI-TG sur opendata.gouv.tg, qui les attribue elle-même à EM-DAT
et aux bilans nationaux. Ils décrivent le contexte du risque, pas les données
que ce tableau de bord manipule — d'où leur place à part.
"""

SOURCE_ISRI = (
    "https://opendata.gouv.tg/fr/datasets/"
    "indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/"
)

REPERES = [
    {
        "cle": "victimes",
        "valeur": "500 000",
        "source": "EM-DAT, cité par la documentation ISRI-TG",
        "annee": 2023,
        "url": SOURCE_ISRI,
    },
    {
        "cle": "deces",
        "valeur": "82",
        "source": "EM-DAT, cité par la documentation ISRI-TG",
        "annee": 2023,
        "url": SOURCE_ISRI,
    },
    {
        "cle": "pertes_agricoles",
        "valeur": "26 Md FCFA",
        "source": "Bilan national, cité par la documentation ISRI-TG",
        "annee": 2020,
        "url": SOURCE_ISRI,
    },
    {
        "cle": "pauvrete_savanes",
        "valeur": "65,1 %",
        "source": "Documentation ISRI-TG",
        "annee": 2023,
        "url": SOURCE_ISRI,
    },
    {
        "cle": "auc_modele",
        "valeur": "92 %",
        "source": "Validation ROC du modèle FSI, documentation ISRI-TG",
        "annee": 2023,
        "url": SOURCE_ISRI,
    },
]


def reperes():
    """Les repères, tels quels. Aucun n'est recalculé ni agrégé."""

    return REPERES
