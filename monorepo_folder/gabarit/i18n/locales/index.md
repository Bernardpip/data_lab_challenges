# i18n/locales/ — un JSON par domaine

Forme unique, quel que soit le domaine :

```json
{
  "titre": {"fr": "Cartographie", "en": "Mapping"}
}
```

Les deux langues **côte à côte**, plutôt qu'un fichier par langue : une clé
ajoutée sans sa traduction anglaise se voit immédiatement à la relecture, au
lieu de se découvrir à l'exécution dans l'autre fichier.

## Les domaines

| Fichier | Contenu | Obligatoire |
|---|---|---|
| `commun.json` | `organisation`, `marque` + ce qui sert dans plusieurs vues | oui |
| `nav_sections.json` | un libellé par section de la sidebar | oui |
| `nav_items.json` | un libellé par onglet | oui |
| `filtres.json` | les libellés des champs de filtre | dès la 1ʳᵉ barre |
| `presentation.json` | les textes du rapport PPTX (`fichier`, `pied`, pages) | à la livraison |
| `<vue>.json` | un fichier par vue, du nom de son domaine | une par vue |

## Ce que le socle fournit déjà

Le socle porte ses propres textes dans `socle/i18n/base/` : « Réduire la
barre », « Voir les données », « Aucune donnée ne correspond à la sélection »…
22 clés dans `commun` et `filtres`.

`table()` fusionne **socle puis défi**, clé à clé. Vous ne recopiez donc rien :
redéfinir `commun.voir_donnees` ici change le libellé partout, ne rien
redéfinir laisse la formulation de référence. Un défi tout neuf affiche une
coquille bilingue complète avant d'avoir écrit sa première clé.

La liste exacte de ce que le socle fournit et de ce qui reste à votre charge :
[api-socle.md](../../../monorepo_folder/docs/api-socle.md), section « Le
contrat i18n » — ou `socle/i18n/base/` si le socle a été vendorisé ici.

## Le JSON plutôt que du Python

Une table de traduction n'est pas du code. Sous cette forme, elle se relit, se
compare et se confie à un traducteur sans lui demander de comprendre la
syntaxe d'un dictionnaire Python — et l'oubli d'une virgule devient une erreur
d'analyse claire, pas un tuple silencieux.
