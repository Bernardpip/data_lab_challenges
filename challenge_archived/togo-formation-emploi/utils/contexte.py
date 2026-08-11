"""Contexte externe — repères qui ne sont PAS dans les jeux ouverts du portail
mais sans lesquels certains chiffres se lisent de travers.

Règle : chaque repère porte sa source et sa date, et reste séparé des
données du tableau de bord (jamais mélangé à un graphe, jamais recalculé).
Ils servent à interpréter, pas à produire.

Le plus important : le taux de chômage des diplômés (7,1 % en 2022, série
Banque mondiale/OIT) paraît faible. Il l'est en apparence seulement — dans une
économie très informelle, ne pas travailler n'est pas une option finançable,
donc l'ajustement se fait par le SOUS-EMPLOI et l'informalité, pas par le
chômage déclaré. Les enquêtes nationales et Afrobarometer le montrent.
"""

# Chaque repère ne porte plus que son identité et sa source vérifiable : le
# libellé, la valeur et le commentaire vivent dans `i18n/locales/contexte.json`,
# sous `<cle>_libelle`, `<cle>_valeur`, `<cle>_detail` et `<cle>_source`.
REPERES = [
    {
        "cle": "jeunesse",
        "url": "https://inseed.tg/presentation-des-resultats-du-dernier-recensement-general-de-la-population-et-des-donnees-sur-la-pauvrete-au-togo/",
    },
    {
        "cle": "jeunes_sans_emploi",
        "url": "https://www.afrobarometer.org/publication/pp93-education-en-hausse-chomage-en-embuscade-limpasse-de-la-jeunesse-togolaise/",
    },
    {
        "cle": "sous_emploi",
        "url": "https://inseed.tg/",
    },
    {
        "cle": "informel",
        "url": "https://inseed.tg/",
    },
]


def repere(cle):
    """Un repère par sa clé, textes traduits résolus.

    L'import de `traduction` est local : `contexte` est chargé par des modules
    d'analyse qui n'ont pas besoin de Streamlit, et le remonter en tête créerait
    une dépendance inutile.
    """

    from socle.i18n.traduction import t

    for item in REPERES:
        if item["cle"] != cle:
            continue

        tr = t("contexte")

        return {
            "cle": cle,
            "valeur": tr(f"{cle}_valeur"),
            "libelle": tr(f"{cle}_libelle"),
            "detail": tr(f"{cle}_detail"),
            "source": tr(f"{cle}_source"),
            "url": item["url"],
        }

    return None


def citation(cle):
    """Mention de source prête à insérer dans un texte d'analyse."""

    item = repere(cle)
    return f'{item["source"]}' if item else ""
