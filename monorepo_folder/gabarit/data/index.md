# data/ — le corpus

Les fichiers tels que téléchargés depuis le portail, **sous leur nom
d'origine**. Ne les renommez pas : ce nom est la trace de la ressource sur le
portail, et c'est lui qui rend le corpus retrouvable et vérifiable par un tiers.

## Déclarer un fichier — deux endroits

```python
# utils/loader.py
FICHIERS = {
    "eaux": "chateaux-deau-forages-tde.csv",
}
```

```python
# verifier.py
FICHIERS_DONNEES = [
    "chateaux-deau-forages-tde.csv",
]
```

Le second n'est pas un doublon : `verifier.py` tourne **avant** toute
installation, sans pandas ni Streamlit, pour dire à qui décompresse le
livrable ce qui manque et quoi taper. Il ne peut donc pas importer le loader.

## Ce qui n'entre pas ici

Un raster de plusieurs dizaines de mégaoctets ne se versionne pas. On charge
sa version **agrégée** (cantons, grille) et l'on **cite** le raster en source,
en le disant. La même règle vaut pour tout jeu trop lourd : le tableau de bord
travaille sur ce qu'il peut porter, et déclare le reste.

## Avant d'écrire la moindre vue

Chaque fichier doit avoir été **ouvert et compté** — jamais « ce fichier doit
contenir… ». Une fiche par ressource dans `utils/profils.py` : volumétrie
brute, granularité la plus fine, période réelle avec ses trous, format
(large / long / géo), pièges (sentinelles, doublons de casse, totaux
embarqués), et surtout ce que le fichier **ne permet pas**.

La sortie décisive de cette lecture : **combien de jeux descendent sous le
national ?** C'est cette réponse — et elle seule — qui détermine la forme du
tableau de bord et ce qu'il devra se refuser à affirmer.
