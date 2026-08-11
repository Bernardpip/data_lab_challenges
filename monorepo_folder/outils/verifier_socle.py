"""Diagnostic du socle — ZÉRO dépendance, tourne AVANT toute installation.

Même principe que le `verifier.py` d'un défi : il doit pouvoir s'exécuter sur
un poste où rien n'est installé, sinon il ne sert qu'à ceux qui n'en ont plus
besoin. Les modules tiers (streamlit, plotly, folium, pandas, numpy, scipy)
sont donc REMPLACÉS par des doubles inertes quand ils sont absents.

Ce que le contrôle prouve :

  · chaque module du socle s'importe, et le graphe interne est cohérent
    (aucun import circulaire, aucun nom disparu au fil d'un renommage) ;
  · les `__init__` exposent bien ce qu'ils annoncent dans `__all__` ;
  · les textes du socle portent les deux langues et des `{parametres}`
    concordants ;
  · aucun libellé visible n'est resté en dur dans le code du socle.

Ce qu'il ne prouve PAS : que Plotly dessine, que Streamlit se peint. Cela ne
se vérifie qu'en lançant un défi (`streamlit run app.py`).

    python3 outils/verifier_socle.py
"""

import json
import re
import sys
import types
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
VERT, ROUGE, JAUNE, GRIS, RAZ = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m"

anomalies = []


def ok(message):
    print(f"  {VERT}✓{RAZ} {message}")


def ko(message):
    anomalies.append(message)
    print(f"  {ROUGE}✗{RAZ} {message}")


def titre(texte):
    print(f"\n{texte}")


# ── Doubles inertes ──────────────────────────────────────────────────────────

class _Inerte(types.ModuleType):
    """Module qui accepte tout : attribut, appel, itération, contexte.

    Un double qui lèverait sur l'inattendu ferait échouer le contrôle pour la
    mauvaise raison — on veut savoir si le SOCLE tient, pas si le double est
    complet.
    """

    def __getattr__(self, nom):
        if nom.startswith("__") and nom.endswith("__"):
            raise AttributeError(nom)
        return _Inerte(nom)

    def __call__(self, *args, **kwargs):
        return _Inerte("appel")

    def __iter__(self):
        return iter(())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def doubler_absents():
    """Installe un double pour chaque dépendance tierce manquante."""

    tiers = {
        "streamlit": ["streamlit.components", "streamlit.components.v1"],
        "pandas": [],
        "numpy": [],
        "plotly": ["plotly.graph_objects"],
        "folium": [],
        "streamlit_folium": [],
        "scipy": ["scipy.stats"],
        "pptx": ["pptx.dml", "pptx.dml.color", "pptx.enum", "pptx.enum.text",
                 "pptx.enum.chart", "pptx.util", "pptx.chart", "pptx.chart.data"],
    }

    doubles = []

    for paquet, sous_modules in tiers.items():
        try:
            __import__(paquet)
            continue
        except ImportError:
            pass

        doubles.append(paquet)

        for nom in [paquet, *sous_modules]:
            sys.modules[nom] = _Inerte(nom)

        # `import plotly.graph_objects as go` exige que l'attribut existe sur
        # le paquet parent, pas seulement l'entrée dans sys.modules.
        for nom in sous_modules:
            parent, _, enfant = nom.rpartition(".")
            setattr(sys.modules[parent], enfant, sys.modules[nom])

    return doubles


# ── 1. Le graphe d'imports ───────────────────────────────────────────────────

MODULES = [
    "socle",
    "socle.design", "socle.design.tokens", "socle.design.styles", "socle.design.icons",
    "socle.charts", "socle.charts.figures", "socle.charts.maps",
    "socle.ui", "socle.ui.cards", "socle.ui.filters",
    "socle.shell", "socle.shell.nav", "socle.shell.routing", "socle.shell.sidebar",
    "socle.shell.section_tabs", "socle.shell.main_container", "socle.shell.footer",
    "socle.shell.admin_layout", "socle.shell.app_shell",
    "socle.i18n", "socle.i18n.types", "socle.i18n.traduction",
    "socle.stats", "socle.stats.econometrie",
    "socle.rapport", "socle.rapport.charte", "socle.rapport.document",
]


def controler_imports():
    titre("1. Graphe d'imports")

    for nom in MODULES:
        try:
            __import__(nom)
        except Exception as erreur:                       # noqa: BLE001
            ko(f"{nom} — {type(erreur).__name__}: {erreur}")
            return

    ok(f"{len(MODULES)} modules importés, aucun cycle")


def controler_exports():
    titre("2. Ce que les paquets annoncent, ils l'exposent")

    for nom in ("socle.charts", "socle.ui", "socle.shell", "socle.stats",
                "socle.i18n", "socle.rapport"):
        module = sys.modules.get(nom) or __import__(nom, fromlist=["_"])
        attendus = getattr(module, "__all__", [])
        manquants = [a for a in attendus if not hasattr(module, a)]

        if manquants:
            ko(f"{nom}.__all__ annonce sans exposer : {', '.join(manquants)}")
        else:
            ok(f"{nom} — {len(attendus)} symboles exposés")


# ── 3. Les textes du socle ───────────────────────────────────────────────────

MOTIF_PARAM = re.compile(r"\{(\w+)\}")
LANGUES = ("fr", "en")


def controler_textes():
    titre("3. Textes du socle (fr/en et paramètres)")

    base = RACINE / "socle" / "i18n" / "base"
    fichiers = sorted(base.glob("*.json"))

    if not fichiers:
        ko("socle/i18n/base/ ne contient aucune table")
        return

    total = 0

    for chemin in fichiers:
        table = json.loads(chemin.read_text(encoding="utf-8"))
        total += len(table)

        for cle, entree in table.items():
            if not isinstance(entree, dict):
                ko(f"{chemin.stem}.{cle} : la valeur devrait être un objet {{fr, en}}")
                continue

            absentes = [lg for lg in LANGUES if not entree.get(lg)]

            if absentes:
                ko(f"{chemin.stem}.{cle} : langue(s) absente(s) — {', '.join(absentes)}")
                continue

            params = {lg: set(MOTIF_PARAM.findall(entree[lg])) for lg in LANGUES}

            for lg in LANGUES[1:]:
                if params[lg] != params["fr"]:
                    ko(
                        f"{chemin.stem}.{cle} : paramètres différents entre "
                        f"fr {sorted(params['fr'])} et {lg} {sorted(params[lg])}"
                    )

    ok(f"{total} clés sur {len(fichiers)} domaines, deux langues complètes")


# ── 4. Aucun libellé en dur ──────────────────────────────────────────────────

# Des mots qui ne peuvent apparaître que dans un texte destiné à l'écran.
# Un faux positif se règle en écrivant le mot autrement dans le commentaire ;
# un faux négatif laisserait un libellé non traduit en production.
SUSPECTS = re.compile(
    r'["\'](?:[^"\']*\b(?:Toutes|Tous|Région|Régions|Préfecture|Filière|Statut|'
    r'Années|Période|Aucun|Aucune|Voir|Passer|Réduire|Déployer)\b[^"\']*)["\']'
)


def controler_libelles():
    titre("4. Aucun libellé visible en dur dans le code du socle")

    fuites = []

    for chemin in sorted((RACINE / "socle").rglob("*.py")):
        lignes = chemin.read_text(encoding="utf-8").splitlines()
        dans_docstring = False

        for numero, ligne in enumerate(lignes, 1):
            # Docstrings et commentaires ont le droit de parler français.
            if ligne.count('"""') == 1:
                dans_docstring = not dans_docstring
                continue

            if dans_docstring or ligne.lstrip().startswith("#"):
                continue

            if SUSPECTS.search(ligne):
                fuites.append(f"{chemin.relative_to(RACINE)}:{numero} — {ligne.strip()}")

    if fuites:
        for fuite in fuites:
            ko(fuite)
    else:
        ok("aucune chaîne visible hors des tables i18n")


# ── 5. Le socle ne connaît aucun corpus ──────────────────────────────────────

def controler_agnosticisme():
    titre("5. Le socle ignore tout d'un corpus")

    interdits = ("loader", "clean", "analytics", "recettes", "profils", "perimetre")
    trouves = [
        str(p.relative_to(RACINE))
        for p in (RACINE / "socle").rglob("*.py")
        if p.stem in interdits
    ]

    if trouves:
        ko("modules métier présents dans le socle : " + ", ".join(trouves))
    else:
        ok("aucun chargement de données ni agrégation métier")

    donnees = [
        str(p.relative_to(RACINE))
        for motif in ("*.csv", "*.geojson", "*.gpkg", "*.xlsx")
        for p in (RACINE / "socle").rglob(motif)
    ]

    if donnees:
        ko("fichiers de données dans le socle : " + ", ".join(donnees))
    else:
        ok("aucun fichier de données")


# ── 6. Chaque dossier porte son index ────────────────────────────────────────

def controler_index():
    """Un `index.md` par dossier — la convention du dépôt.

    Sans contrôle, une convention documentaire tient trois semaines : le
    dossier ajouté un vendredi n'a jamais son index, et l'absence ne se
    remarque que le jour où quelqu'un le cherche.
    """

    titre("6. Chaque dossier porte son index.md")

    surveilles = [RACINE / "socle", RACINE / "gabarit", RACINE / "outils",
                  RACINE / "docs"]
    dossiers = []

    for racine in surveilles:
        dossiers.append(racine)
        dossiers += [
            d for d in sorted(racine.rglob("*"))
            if d.is_dir() and not d.name.startswith((".", "__"))
        ]

    absents = [
        str(d.relative_to(RACINE)) for d in dossiers
        if not (d / "index.md").exists()
    ]

    if absents:
        for chemin in absents:
            ko(f"{chemin}/ — pas d'index.md")
    else:
        ok(f"{len(dossiers)} dossiers, tous indexés")


def main():
    print(f"\n{GRIS}Socle DataLab — diagnostic{RAZ}")

    sys.path.insert(0, str(RACINE))
    doubles = doubler_absents()

    if doubles:
        print(f"  {JAUNE}!{RAZ} dépendances absentes, remplacées par des doubles : "
              f"{GRIS}{', '.join(doubles)}{RAZ}")
        print(f"    {GRIS}le rendu réel ne se vérifie qu'en lançant un défi{RAZ}")

    controler_imports()
    controler_exports()
    controler_textes()
    controler_libelles()
    controler_agnosticisme()
    controler_index()

    print()

    if anomalies:
        print(f"{ROUGE}{len(anomalies)} anomalie(s).{RAZ}\n")
        return 1

    print(f"{VERT}Socle conforme.{RAZ}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
