"""Les adresses externes du défi, déclarées en un seul endroit.

Une URL écrite dans la vue qui l'affiche se retrouve dupliquée dès qu'un
deuxième écran la cite — le pied de page et l'en-tête portent tous deux celle
du laboratoire — et les deux copies divergent au premier changement de domaine.

Chaque entrée porte son libellé D'AFFICHAGE en plus de son adresse : le texte
d'un lien externe n'est pas traduisible. « LinkedIn » et « Portfolio » sont des
noms propres, et « Togo AI Lab » est une marque ; les faire passer par l'i18n
créerait des clés dont les deux langues seraient identiques, et qu'il faudrait
pourtant maintenir.
"""

from socle.design.icons import icon, lab_logo

URL_CONFIGS = {
    "LinkedIn_url": {
        "icon": "linkedin",
        "display_value": "LinkedIn",
        "url": "https://www.linkedin.com/in/kokou-b-pipi-30084a137/",
    },
    "Portfolio_url": {
        # Un portfolio est une personne, pas un site : l'icône de silhouette
        # dit à qui l'on va, là où un globe ne disait que « web ».
        "icon": "user",
        "display_value": "Portfolio",
        "url": "https://portfolio.bernardpip.com/",
    },
    "data_lab_url": {
        "icon": "datalab",
        "display_value": "Togo AI Lab",
        "url": "https://datalab.gouv.tg/",
    },
    "data_lab_challenge_url": {
        "icon": "flag",
        "display_value": "Environnement | Defi 1",
        "url": ("https://datalab.gouv.tg/data-challenges/defis/"
                "environnement-defi-1"),
    },
}


def lien(cle, classe="kg-foot-link"):
    """Une ancre HTML prête à poser, ou une chaîne vide si la clé est inconnue.

    La forme est celle du pied de la CONSOLE — icône puis libellé, sans
    soulignement, encre en retrait qui fonce au survol. Les deux surfaces
    signent ainsi de la même manière ; un pied d'affiche avec ses propres
    liens soulignés donnait deux grammaires pour une même mention.

    Renvoyer du vide plutôt que lever : un lien absent doit faire disparaître
    sa mention, pas la page qui la porte.

    `target="_blank"` avec `rel="noopener noreferrer"` — sans ce dernier, la
    page ouverte garde une référence sur celle-ci et peut la faire naviguer.
    """

    entree = URL_CONFIGS.get(cle)

    if not entree:
        return ""

    # Le laboratoire porte son LOGO, les autres une icône d'interface : c'est
    # une marque, et une marque ne se remplace pas par un pictogramme.
    if entree.get("icon") == "datalab":
        vignette = f'<span class="kg-foot-lab-icon">{lab_logo(14)}</span>'
        classe = "kg-foot-lab"
    else:
        vignette = icon(entree.get("icon") or "folder", 13)

    return (
        f'<a class="{classe}" href="{entree["url"]}" target="_blank"'
        f' rel="noopener noreferrer">{vignette}'
        f'<span>{entree["display_value"]}</span></a>'
    )


def adresse(cle):
    """L'URL seule — pour les composants qui construisent leur propre ancre."""

    return (URL_CONFIGS.get(cle) or {}).get("url", "")


def libelle(cle):
    """Le libellé d'affichage seul."""

    return (URL_CONFIGS.get(cle) or {}).get("display_value", "")
