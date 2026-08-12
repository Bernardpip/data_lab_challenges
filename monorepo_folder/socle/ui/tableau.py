"""Coquille de LISTE — un en-tête de colonnes, des lignes réglées, un état vide.

Transposition de `List_Shell.tsx` du paquet partagé : mêmes partis pris, mêmes
proportions, adaptés à ce que Streamlit permet.

Ce qu'on garde de la référence :

  · un CADRE unique, arrondi, qui contient l'en-tête et les lignes — au lieu
    d'une pile de cartes flottantes, où chaque élément se lit comme un objet
    séparé et où rien ne dit qu'ils partagent des colonnes ;
  · un EN-TÊTE de colonnes collant, en petites capitales, sur fond de surface
    secondaire ;
  · des LIGNES séparées par un filet, survolées d'une teinte, avec la première
    colonne en « visuel + libellé + sous-libellé » ;
  · un ÉTAT VIDE centré, qui dit ce qui manque plutôt que de laisser un cadre
    blanc.

Ce qu'on ne peut pas garder : un vrai `<table>`. Une cellule doit pouvoir
contenir un BOUTON, et un bouton de Streamlit est un composant à part entière
qui se place dans une colonne — pas une chaîne qu'on interpole. Les lignes sont
donc des `st.columns` réglées sur les mêmes poids que l'en-tête, et c'est la
feuille de style qui leur donne l'apparence d'un tableau.

    tab = tableau("mesgens", [
        {"cle": "nom", "libelle": "Nom", "poids": 6},
        {"cle": "action", "libelle": "", "poids": 2, "align": "right"},
    ])

    for personne in gens:
        nom, action = tab.ligne(personne["id"])
        with nom:
            tab.cellule(personne["nom"], sous=personne["email"])
        with action:
            st.button("Activer", key=…)
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle.design.tokens import COLORS


def _styles(nom, hauteur_ligne):
    """La feuille du tableau — écrite une fois par tableau, sous sa clé."""

    return (
        "<style>"
        # Le CADRE : un seul objet, comme la carte de contenu de la référence.
        f".st-key-{nom} {{"
        f" border: 1px solid {COLORS['borderLight']}; border-radius: 12px;"
        f" background: {COLORS['surface']}; overflow: hidden; }}"
        # L'EN-TÊTE est une SEULE rangée en flex, écrite d'un bloc — et non une
        # rangée de colonnes Streamlit. Mesuré : entre la colonne et le libellé,
        # Streamlit intercale trois conteneurs dont l'un tombait à 2,75 px de
        # haut ; le texte, lui, en fait seize, et débordait par le bas d'une
        # bande qui semblait le couper. Aucun réglage de centrage n'y pouvait
        # rien — c'est la chaîne qu'il fallait retirer.
        #
        # L'alignement sur les lignes tient à trois nombres partagés : le
        # rembourrage horizontal, l'écart entre colonnes, et les poids. Les
        # mêmes ici et dans `st.columns`, qui répartit lui aussi l'espace
        # restant au prorata.
        f".st-key-{nom}entete {{"
        f" background: {COLORS['surfaceSecondary']};"
        f" border-bottom: 1px solid {COLORS['border']};"
        f" display: flex; align-items: center; gap: 10px;"
        f" min-height: 34px; padding: 0 14px; }}"
        f".st-key-{nom}entete span {{"
        f" font-size: 10.5px; font-weight: 700; letter-spacing: .04em;"
        f" line-height: 1.4; text-transform: uppercase;"
        f" color: {COLORS['textMuted']}; min-width: 0;"
        f" overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}"
        # Les LIGNES : filet en bas, sauf la dernière, et survol.
        f'.st-key-{nom} [class*="st-key-{nom}ligne"] {{'
        f" border-bottom: 1px solid {COLORS['borderLight']};"
        f" padding: 8px 14px !important;"
        f" min-height: {hauteur_ligne}px;"
        f" transition: background .12s; }}"
        f'.st-key-{nom} [class*="st-key-{nom}ligne"]:hover {{'
        f" background: {COLORS['surfaceSecondary']}; }}"
        f'.st-key-{nom} [class*="st-key-{nom}ligne"]:last-child {{'
        f" border-bottom: none; }}"
        # Les colonnes d'une ligne ne s'enroulent JAMAIS : c'est ce qui
        # distingue un tableau d'une pile de cartes, et Streamlit leur impose
        # sinon 160 px de largeur minimale, ce qui les fait passer à la ligne
        # dès qu'une colonne est étroite.
        f'.st-key-{nom} [data-testid="stHorizontalBlock"] {{'
        f" flex-wrap: nowrap; gap: 10px; }}"
        f'.st-key-{nom} [data-testid="stColumn"] {{ min-width: 0; }}'
        "</style>"
    )


class Tableau:
    """L'objet rendu par `tableau()` — porte ses colonnes et sait poser une ligne."""

    def __init__(self, nom, colonnes, hauteur_ligne):
        self.nom = nom
        self.colonnes = colonnes
        self.poids = [c.get("poids", 1) for c in colonnes]
        self.hauteur_ligne = hauteur_ligne
        self._rang = 0

    def ligne(self, cle=None):
        """Une ligne du tableau — renvoie une colonne par en-tête déclaré."""

        self._rang += 1
        identifiant = cle or self._rang

        with st.container(key=f"{self.nom}ligne_{identifiant}"):
            return st.columns(self.poids, vertical_alignment="center")

    def cellule(self, libelle, sous=None, visuel=None, pastille=None):
        """La première colonne type : visuel, libellé, sous-libellé, pastille.

        `visuel` est du HTML déjà composé — un avatar, une pastille d'icône :
        la coquille ne sait pas ce qu'une ligne met en tête, et le deviner
        l'obligerait à connaître le domaine.
        """

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;'
            f'min-width:0;">'
            + (visuel or "")
            + f'<div style="min-width:0;">'
            f'<div style="font-size:13.5px;font-weight:650;line-height:1.3;'
            f'color:{COLORS["text"]};overflow:hidden;text-overflow:ellipsis;'
            f'white-space:nowrap;">{libelle}</div>'
            + (f'<div style="font-size:11.5px;color:{COLORS["textMuted"]};'
               f'line-height:1.35;overflow:hidden;text-overflow:ellipsis;'
               f'white-space:nowrap;">{sous}</div>' if sous else "")
            + (pastille or "")
            + "</div></div>",
            unsafe_allow_html=True,
        )

    def vide(self, message):
        """L'état vide — au centre du cadre, comme dans la référence."""

        st.markdown(
            f'<div style="padding:28px 14px;text-align:center;'
            f'font-size:13px;color:{COLORS["textMuted"]};">{message}</div>',
            unsafe_allow_html=True,
        )


def tableau(cle, colonnes, hauteur_ligne=48, entete=True):
    """Ouvre un tableau et écrit son en-tête. À employer dans un `with`.

    `colonnes` : [{cle, libelle, poids, align}] — `poids` suit la grille de
    `st.columns`, et l'en-tête comme les lignes s'y règlent, ce qui garantit
    que les colonnes restent alignées d'une ligne à l'autre.
    """

    nom = f"kgtab{cle}"
    st.markdown(_styles(nom, hauteur_ligne), unsafe_allow_html=True)

    boite = st.container(key=nom)

    with boite:
        if entete and any(c.get("libelle") for c in colonnes):
            # La BASE de chaque case reprend celle que Streamlit donne à ses
            # colonnes — mesuré dans le navigateur : `1 1 calc(P% - 13px)`, où
            # les treize pixels sont sa constante d'écart. Répartir au simple
            # prorata décalait les en-têtes de sept pixels sur leur colonne,
            # parce que le reste d'espace, lui, se partage à parts égales.
            total = sum(c.get("poids", 1) for c in colonnes) or 1
            cases = "".join(
                f'<span style="flex:1 1 calc('
                f'{c.get("poids", 1) / total * 100:.4f}% - 13px);'
                f'text-align:{c.get("align", "left")};">'
                f'{c.get("libelle", "")}</span>'
                for c in colonnes
            )
            st.markdown(f'<div class="st-key-{nom}entete">{cases}</div>',
                        unsafe_allow_html=True)

    return boite, Tableau(nom, colonnes, hauteur_ligne)
