"""Montage du rapport PowerPoint — la langue est un ARGUMENT, jamais un état.

Deux différences avec le tableau de bord, imposées par le fait qu'un fichier
généré n'a pas de session :

  · `t()` lit `st.session_state`, qui n'existe pas quand le script tourne en
    ligne de commande — et surtout ne dirait rien de la langue DEMANDÉE quand
    un utilisateur en anglais télécharge la version française ;
  · le formatage des nombres suit la langue du DOCUMENT. Un séparateur de
    milliers en espace et une virgule décimale sont français ; l'anglais
    attend l'inverse. Sans cela, un document anglais se retrouve parsemé de
    « 1 234,5 ».

Le défi fournit sa liste de pages et sa fonction de collecte ; tout le reste
du montage est ici.
"""

from pathlib import Path

# pyrefly: ignore [missing-import]
from pptx import Presentation

from socle.i18n import LANGUES, table
from socle.i18n.traduction import creer_traducteur
from socle.rapport.charte import LARGEUR, HAUTEUR


class Langue:
    """Tout ce qui dépend de la langue du document, en un seul objet.

    Passé à chaque page plutôt que lu dans un état global : deux documents de
    langues différentes peuvent ainsi être produits dans le même processus, ce
    que fait le bouton de téléchargement du tableau de bord.
    """

    def __init__(self, code, domaine="presentation"):
        self.code = code
        self.t = creer_traducteur(table(domaine), code)
        self.commun = creer_traducteur(table("commun"), code)

    def nb(self, valeur, decimales=0):
        """Nombre formaté selon la langue du document."""

        texte = f"{valeur:,.{decimales}f}"

        if self.code == "fr":
            # Passage par un caractère tampon : remplacer la virgule par une
            # espace puis le point par une virgule, dans cet ordre et sans
            # tampon, transformerait les virgules fraîchement écrites.
            return texte.replace(",", "\x00").replace(".", ",").replace("\x00", " ")

        return texte

    def pct(self, valeur, decimales=0):
        """Pourcentage — espace insécable typographique dans les deux langues,
        par cohérence avec le tableau de bord."""

        return f"{self.nb(valeur, decimales)} %"


def construire(pages, langue="fr", chiffres=None, domaine="presentation"):
    """La présentation en mémoire, dans la langue demandée.

    `pages` : liste de fonctions `(prs, chiffres, lg)`, dans l'ordre.
    `chiffres` : ce que la fonction de collecte du défi a produit.

    Sépare le montage de l'écriture sur disque : le tableau de bord sert le
    fichier en flux, sans jamais toucher au système de fichiers du conteneur.
    """

    if langue not in LANGUES:
        raise ValueError(f"Langue inconnue : {langue!r} (attendu {LANGUES})")

    if chiffres is None:
        # Le socle ne sait pas collecter : les agrégations appartiennent au
        # défi. Sans ce garde-fou, `None` traverse jusqu'à la première page et
        # y casse en « 'NoneType' object is not subscriptable », à vingt
        # appels de la vraie cause.
        raise RuntimeError(
            "socle.rapport : aucun chiffre fourni. Le montage ne collecte pas "
            "lui-même — les agrégations appartiennent au défi. Dans "
            "scripts/generer_presentation.py :\n\n"
            "    def construire(langue='fr', chiffres=None):\n"
            "        return socle_construire(\n"
            "            PAGES, langue, chiffres if chiffres is not None else collecter()\n"
            "        )\n\n"
            "Collectez UNE fois et partagez entre les langues : deux "
            "chargements laisseraient les versions diverger."
        )

    lg = Langue(langue, domaine)

    prs = Presentation()
    prs.slide_width = LARGEUR
    prs.slide_height = HAUTEUR

    for page in pages:
        page(prs, chiffres, lg)

    return prs, lg


def octets(pages, langue="fr", chiffres=None, domaine="presentation"):
    """La présentation sérialisée — ce que consomme un bouton de téléchargement."""

    from io import BytesIO

    prs, lg = construire(pages, langue, chiffres, domaine)
    tampon = BytesIO()
    prs.save(tampon)

    return tampon.getvalue(), f"{lg.t('fichier')}.pptx"


def generer(pages, langue="fr", destination=None, chiffres=None,
            domaine="presentation"):
    """Écrit le document et renvoie (chemin, nombre de pages)."""

    prs, lg = construire(pages, langue, chiffres, domaine)

    chemin = Path(destination) if destination else Path("rapport") / f"{lg.t('fichier')}.pptx"
    chemin.parent.mkdir(parents=True, exist_ok=True)
    prs.save(chemin)

    return chemin, len(prs.slides._sldIdLst)


def generer_toutes(pages, chiffres, langues=None, dossier=None,
                   domaine="presentation"):
    """Les deux langues à partir des MÊMES chiffres.

    `chiffres` est calculé une seule fois par l'appelant et partagé : les deux
    documents doivent porter exactement les mêmes valeurs, et un second
    chargement des jeux ne servirait qu'à ouvrir la porte à un écart entre les
    versions.
    """

    produits = []

    for code in (langues or LANGUES):
        destination = None

        if dossier:
            lg = Langue(code, domaine)
            destination = Path(dossier) / f"{lg.t('fichier')}.pptx"

        produits.append((code, *generer(pages, code, destination, chiffres, domaine)))

    return produits
