# socle/rapport/ — le rapport PowerPoint

```python
from socle.rapport import charte, generer_toutes

chiffres = collecter()          # UNE fois, partagé entre les deux langues
generer_toutes(PAGES, chiffres, dossier=RACINE / "rapport")
```

| Fichier | Contenu |
|---|---|
| `charte.py` | couleurs, `titre_page`, `pied`, `bloc_constat`, `bloc_analyse`, `style_graphe`, `rgb()` |
| `document.py` | objet `Langue`, `construire`, `octets`, `generer`, `generer_toutes` |

Dépend de `python-pptx`, installé par l'extra : `pip install -e "../monorepo_folder[rapport]"`.

## Ce qui monte ici, et ce qui reste au défi

Les **10 pages** appartiennent au défi (`scripts/generer_presentation.py`) :
elles racontent SON constat. Ne monte ici que ce qui se répète — bandeau de
titre, pied, tuile de chiffre-clé, bloc d'analyse, style des graphes natifs,
langue et assemblage.

Trame des 10 pages : couverture · données et démarche · le constat structurant
· sa dynamique · l'effet mis en évidence · économétrie · moyens publics · le
croisement attendu (et ce qu'il ne permet pas) · leviers · conclusion et limites.

## Trois choix qui ne se renégocient pas

**Les graphiques sont NATIFS** (`add_chart`), donc éditables et
redimensionnables par le lecteur — pas des images figées.

**Les chiffres viennent des mêmes fonctions que le tableau de bord**, collectés
une seule fois et partagés entre les deux langues. Deux chargements
laisseraient les versions diverger sur un arrondi ; le rapport ne peut alors
plus servir de preuve de l'écran.

**La langue est un ARGUMENT, jamais l'état de session.** `t()` lit
`st.session_state`, qui n'existe pas en ligne de commande — et surtout ne
dirait rien de la langue demandée quand un utilisateur en anglais télécharge
la version française. Le formatage des nombres suit la langue du document,
sinon un document anglais se retrouve parsemé de « 1 234,5 ».

## La charte dérive, elle ne recopie pas

`charte.py` convertit les valeurs de `socle.design.tokens` en `RGBColor`. Le
pilote les retapait sous un commentaire « reprise de tokens.py » : changer une
teinte à l'écran laissait le PPTX sur l'ancienne, et les deux livrables
cessaient silencieusement de se ressembler. Une couleur propre au défi se
déclare avec `charte.rgb("#006A4E")` dans le fichier du défi.
