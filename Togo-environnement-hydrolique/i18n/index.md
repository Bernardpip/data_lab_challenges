# i18n/ — tous les textes visibles

| Dossier | Contenu |
|---|---|
| [locales/](locales/index.md) | un JSON par domaine, français et anglais côte à côte |

Le moteur (chargement, traducteur, contrôle d'intégrité) vient du socle
(`socle.i18n`). Ce dossier ne porte que **les textes de ce défi**.

`app.py` déclare l'emplacement avant tout import de vue :

```python
i18n.configurer(Path(__file__).parent / "i18n" / "locales")
```

## Aucun texte visible ailleurs

Ni dans les vues, ni dans les composants, ni dans les scripts. Un défi qui
laisse une chaîne dans le code perd sa version anglaise sans que rien ne le
signale — et `verifier_traductions()` ne peut pas la voir.

## Aucun chiffre figé dans une phrase

Les valeurs calculées passent en `{param}` :

```json
"note_part": {
  "fr": "{region} concentre {part} % des ouvrages recensés.",
  "en": "{region} holds {part}% of the recorded facilities."
}
```

C'est ce qui fait que les commentaires d'analyse **se recalculent sur la
sélection**. Un nombre écrit dans la phrase devient faux au premier filtre
actionné, et personne ne s'en aperçoit.

## Le contrôle

```python
from socle.i18n.traduction import verifier_traductions
verifier_traductions()      # doit renvoyer une liste vide
```

Il détecte les deux défauts qu'une relecture laisse passer : une langue
manquante (repli silencieux sur le français) et un `{parametre}` présent d'un
côté mais pas de l'autre — la version traduite afficherait alors une accolade
brute au lecteur.
