"""Marque Data AI Lab — la composition logo + mot-marque.

Le TRACÉ vit dans `icons.lab_logo`, avec les autres actifs de marque : il en
existait deux versions — une redessinée à la main pour la console, l'officielle
pour l'affiche — et deux tracés d'un même logo finissent toujours par diverger.

Ce module ne porte que la mise en forme : le lion, puis « Togo / AI Lab » sur
deux lignes, comme le site les compose.

Les paramètres sont nommés en FRANÇAIS, comme partout ailleurs dans le socle —
`hauteur`, `couleur`, `libelle`, `cle`. Un `url=` et un `size=` au milieu de
`silhouette_svg(fond, hauteur=…)` obligeraient à se souvenir de quelle langue
parle chaque fonction.
"""

from socle.design.icons import lab_logo

# Corps du mot-marque, en proportion de la hauteur du lion — avec un PLANCHER.
#
# Le site compose un logo de 120 px avec un texte de 32, soit un rapport de
# 0,27. Appliqué tel quel à une marque d'interface de 30 px, il donne 8 px :
# mesuré, et illisible. Ce rapport vaut pour un lockup d'accueil, pas pour un
# coin d'en-tête. On garde donc une proportion plus généreuse et un plancher
# sous lequel le mot cesserait d'être un mot.
_RAPPORT_TEXTE = 0.40
_CORPS_MINIMAL = 11


def datalab_marque(taille=28, libelle=None, adresse=None, avec_texte=True):
    """Le logo et son mot-marque, éventuellement en lien.

    `taille`      hauteur du lion, en pixels ; le corps du texte suit.
    `libelle`     remplace « Togo\\nAI Lab » ; le saut de ligne est signifiant.
    `adresse`     en fait un lien, ouvert dans un onglet neuf.
    `avec_texte`  à faux, ne rend que le lion — pour les emplacements étroits
                  où le mot-marque ne tiendrait pas, comme un pied de page.

    `rel="noopener"` est obligatoire avec `target="_blank"` : sans lui, la page
    ouverte conserve une référence sur celle-ci et peut la faire naviguer.
    """

    corps = max(_CORPS_MINIMAL, round(taille * _RAPPORT_TEXTE))
    contenu = f'<span class="kg-marque-icone">{lab_logo(taille)}</span>'

    if avec_texte:
        mot = "<br>".join((libelle or "Togo\nAI Lab").split("\n"))
        contenu += (
            f'<span class="kg-marque-mot" style="font-size:{corps}px;">'
            f"{mot}</span>"
        )

    if not adresse:
        return f'<span class="kg-marque">{contenu}</span>'

    return (
        f'<a class="kg-marque" href="{adresse}" target="_blank"'
        f' rel="noopener noreferrer">{contenu}</a>'
    )
