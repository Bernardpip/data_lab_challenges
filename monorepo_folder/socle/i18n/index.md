# socle/i18n/ — le moteur, et les textes du socle

```python
from socle import i18n
i18n.configurer(Path(__file__).parent / "i18n" / "locales")   # dans app.py

from socle.i18n.traduction import t, traducteurs, verifier_traductions
tr = t("synthese")
tr("part_region", {"region": "Maritime", "part": "60"})
```

| Fichier | Rôle |
|---|---|
| `__init__.py` | chargement et FUSION des tables, `configurer()` |
| `types.py` | `LANGUES`, `LANGUE_PAR_DEFAUT`, `LIBELLES_LANGUE` |
| `traduction.py` | le traducteur, le « store » de langue, `verifier_traductions()` |
| [base/](base/index.md) | les textes dont le socle a lui-même besoin |

## Le dossier est DÉCLARÉ, pas déduit

Le pilote calculait `Path(__file__).parent / "locales"`. Ce module vivant
maintenant dans le socle, ce calcul désignerait les locales du socle — qui n'en
a pas au sens d'un défi, et n'en aura jamais : un texte visible appartient
toujours à un corpus. Sans l'appel à `configurer()`, `table()` lève une erreur
qui dit exactement quoi écrire.

## La fusion socle → défi

`table(domaine)` lit `base/<domaine>.json` puis écrase clé à clé avec
`<locales>/<domaine>.json`. Le défi **surcharge sans recopier** : redéfinir
`commun.voir_donnees` change le libellé partout, ne rien redéfinir laisse la
formulation de référence. Un défi tout neuf affiche donc une coquille
bilingue complète avant d'avoir écrit une seule clé.

## Deux règles

**Aucun chiffre figé dans un texte.** Les valeurs calculées passent en
`{param}` — c'est ce qui fait que les commentaires d'analyse se recalculent
sur la sélection. Un nombre écrit dans la phrase devient faux au premier clic.

**Une langue absente retombe sur le français**, et une clé absente renvoie la
clé elle-même. À l'écran, un identifiant technique se remarque et se corrige ;
un blanc, non.

`verifier_traductions()` détecte les langues manquantes et les `{params}`
discordants entre versions — le second défaut ne se voit qu'à l'exécution, et
affiche une accolade brute au lecteur.
