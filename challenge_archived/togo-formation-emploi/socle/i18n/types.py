"""Types de traduction — équivalent Python de `translations/types.ts`.

Une entrée traduite porte les DEUX langues côte à côte, comme dans zendho :

    "titre": {"fr": "Cartographie", "en": "Mapping"}

Plutôt qu'un fichier par langue. L'avantage est le même ici que là-bas : une
clé qu'on ajoute sans sa traduction anglaise se voit immédiatement à la
relecture, au lieu de se découvrir à l'exécution dans l'autre fichier.
"""

LANGUES = ("fr", "en")

# Le français fait autorité : c'est la langue de rédaction du tableau de bord
# et des données sources. Toute traduction manquante y retombe.
LANGUE_PAR_DEFAUT = "fr"

LIBELLES_LANGUE = {
    "fr": "Français",
    "en": "English",
}
