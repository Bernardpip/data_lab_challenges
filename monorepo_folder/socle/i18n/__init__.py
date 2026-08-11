"""Traductions — chargement des tables JSON du défi.

Un fichier JSON par domaine dans le dossier `locales/` du DÉFI, toujours de la
même forme :

    {
      "titre":      {"fr": "Titre",       "en": "Title"},
      "sous_titre": {"fr": "Sous-titre",  "en": "Subtitle"}
    }

Le JSON plutôt que du Python : une table de traduction n'est pas du code. Sous
cette forme, elle se relit, se compare et se confie à un traducteur sans lui
demander de comprendre la syntaxe d'un dictionnaire Python — et l'oubli d'une
virgule devient une erreur d'analyse claire, pas un tuple silencieux.

Les fichiers sont lus UNE FOIS au premier accès et gardés en mémoire : ils
sont minuscules, et Streamlit rejoue le script à chaque interaction.

**Le dossier est déclaré par le défi, pas déduit d'ici.** Le pilote calculait
`Path(__file__).parent / "locales"` ; ce module vivant maintenant dans le
socle partagé, ce calcul désignerait les locales du socle — qui n'en a pas, et
n'en aura jamais : un texte visible appartient toujours à un corpus.
"""

import json
from pathlib import Path

from socle.i18n.types import LANGUES, LANGUE_PAR_DEFAUT, LIBELLES_LANGUE

# Le socle porte les textes DONT IL A LUI-MÊME BESOIN — « Réduire la barre »,
# « Voir les données », « Aucune donnée ne correspond… ». Sans eux, la coquille
# partagée exigerait de chaque défi qu'il recopie une quinzaine de clés avant
# d'afficher sa première page, et un oubli s'y verrait en clé brute à l'écran.
# Le défi ne réécrit que ce qui lui appartient.
_BASE = Path(__file__).resolve().parent / "base"

_dossier = None
_cache = {}


def configurer(dossier):
    """Déclare le dossier `locales/` du défi. À appeler avant tout rendu.

    Vider le cache est indispensable : un script qui reconfigure (le
    générateur de rapport, un test) doit relire, sinon il servirait les
    tables du défi précédent.
    """

    global _dossier

    _dossier = Path(dossier).resolve()
    _cache.clear()

    return _dossier


def dossier():
    """Dossier des locales, ou l'erreur qui dit quoi écrire.

    Un dossier non configuré est une faute de câblage, pas une donnée
    manquante : elle doit s'arrêter net au démarrage plutôt que de faire
    afficher des clés brutes sur toutes les pages.
    """

    if _dossier is None:
        raise RuntimeError(
            "socle.i18n : dossier des locales non configuré. Dans app.py, "
            "avant tout import de vue :\n\n"
            "    from pathlib import Path\n"
            "    from socle import i18n\n"
            "    i18n.configurer(Path(__file__).parent / 'i18n' / 'locales')\n"
        )

    return _dossier


def _lire(chemin):
    """Contenu d'un fichier de locales, ou une table vide s'il n'existe pas."""

    if not chemin.exists():
        return {}

    return json.loads(chemin.read_text(encoding="utf-8"))


def table(domaine):
    """Table d'un domaine — socle d'abord, défi par-dessus.

    La fusion se fait clé à clé et dans cet ordre, si bien que le défi
    SURCHARGE le socle sans avoir à le recopier : redéfinir `commun.voir_donnees`
    suffit à changer le libellé partout, et ne rien redéfinir laisse la
    formulation de référence.

    Un domaine absent des deux côtés renvoie une table VIDE plutôt que de
    lever : une vue dont le fichier n'existe pas encore doit s'afficher avec
    ses clés brutes, pas planter. Le traducteur signale alors chaque clé
    manquante.
    """

    if domaine not in _cache:
        fusion = _lire(_BASE / f"{domaine}.json")
        fusion.update(_lire(dossier() / f"{domaine}.json"))
        _cache[domaine] = fusion

    return _cache[domaine]


def domaines():
    """Domaines disponibles — utilisé par le contrôle d'intégrité.

    L'union des deux côtés : un domaine que seul le socle porte doit être
    vérifié lui aussi, sinon une clé incomplète du socle passerait le contrôle.
    """

    stems = {p.stem for p in _BASE.glob("*.json")}
    stems |= {p.stem for p in dossier().glob("*.json")}

    return sorted(stems)


__all__ = [
    "LANGUES", "LANGUE_PAR_DEFAUT", "LIBELLES_LANGUE",
    "configurer", "dossier", "table", "domaines",
]
