# scripts/ — les deux livrables produits

| Script | Produit |
|---|---|
| `generer_presentation.py` | le rapport PowerPoint, dans les deux langues |
| `faire_zip.py` | l'archive livrable |

```bash
python3 scripts/generer_presentation.py        # les deux langues
python3 scripts/generer_presentation.py fr     # une seule
python3 scripts/faire_zip.py                   # regénère le PPTX, puis archive
```

## Le rapport ne peut pas diverger de l'écran

`collecter()` appelle les **mêmes fonctions** que le tableau de bord
(`utils.analytics`, `utils.recettes`) et n'écrit aucun calcul de son côté. Un
chiffre recalculé à deux endroits finit toujours par diverger.

Il est appelé **une seule fois** pour les deux langues : deux chargements
laisseraient les versions s'écarter sur un arrondi, et le rapport cesserait de
prouver ce que l'écran montre.

Ce fichier ne porte que les 10 pages. Le bandeau de titre, le pied, la tuile
de chiffre-clé, le bloc d'analyse et l'assemblage bilingue viennent de
`socle.rapport`.

## L'archive dérive du dépôt

`faire_zip.py` construit sa liste depuis `git ls-files`, **jamais** d'une
énumération écrite à la main. C'est tout son objet : sur le pilote, une
archive composée à la main avait perdu `i18n/` et `utils/traduction.py`,
ajoutés au dépôt après coup et nulle part ailleurs.

Deux pièces échappent au dépôt et sont ajoutées explicitement :

- **le PowerPoint**, regénéré juste avant — seule pièce qui soit un produit
  des données plutôt qu'une source ;
- **le socle**, vendorisé. Installé en paquet pendant le développement, il est
  invisible de `git ls-files` : sans cet ajout, le jury décompresserait une
  application qui ne démarre pas.

L'archive porte **un seul dossier racine**. `unzip` en ligne de commande
n'enveloppe rien et déverserait son contenu dans le répertoire courant de qui
l'exécute ; le Finder et l'Explorateur, eux, créent un dossier d'accueil. Un
dossier racine unique se comporte pareil partout.
