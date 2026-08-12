"""Traduction — transposition Streamlit de `hooks/useTranslation.ts`.

Le hook zendho lit la langue dans un store Zustand persisté et renvoie une
fonction de traduction par domaine (`tCommon`, `tNav`, …). Le contrat est
repris tel quel :

  · une entrée porte les deux langues, `{"fr": …, "en": …}` ;
  · une clé absente renvoie la clé elle-même, avec un avertissement en
    développement — jamais une chaîne vide, qui laisserait un trou muet ;
  · une langue absente pour une clé existante retombe sur le français ;
  · les paramètres `{nom}` sont interpolés.

Trois différences, imposées par la plateforme :

1. **Pas de hook.** `traducteurs()` est une fonction ordinaire, appelée en
   tête de vue. Streamlit rejoue tout le script à chaque interaction : il n'y
   a ni cycle de rendu ni mémoïsation à gérer, donc pas d'équivalent de
   `useCallback`.

2. **Le store est `st.session_state` + l'URL.** Zustand persiste dans le
   stockage local ; ici la langue s'écrit aussi dans le paramètre `?lang=`,
   comme la route. Un lien partagé transporte donc sa langue, ce que le
   stockage local ne permet pas.

3. **Un domaine par vue.** Aucun texte visible ne reste dans les vues : chaque
   fichier de `views/` a son JSON dans `i18n/locales/`, plus les domaines
   partagés `commun`, `filtres`, `nav_sections`, `nav_items`. Les valeurs
   calculées passent en paramètres `{nom}` — un commentaire d'analyse cite ses
   chiffres, il ne peut donc pas être une chaîne figée.
"""

import os
import re

# pyrefly: ignore [missing-import]
import streamlit as st

from socle.i18n import LANGUES, LANGUE_PAR_DEFAUT, table, domaines


PARAM_LANGUE = "lang"
_CLE_SESSION = "_langue_active"

# Un avertissement de clé manquante n'a de sens qu'au développement. En ligne,
# il polluerait les journaux du conteneur à chaque rerun.
_EN_DEV = os.environ.get("STREAMLIT_ENV", "development") != "production"

_MOTIF_PARAM = re.compile(r"\{(\w+)\}")


# ─── Le « store » ────────────────────────────────────────────────────────────

def init_langue():
    """Aligne la langue sur l'URL. À appeler une fois, avec `init_route()`.

    L'URL fait autorité quand elle porte `?lang=`, pour la même raison que la
    route : Streamlit restaure la session au rechargement, donc n'amorcer
    qu'une fois par session ferait ignorer un lien partagé.
    """

    demandee = st.query_params.get(PARAM_LANGUE)

    if demandee in LANGUES:
        st.session_state[_CLE_SESSION] = demandee
    elif _CLE_SESSION not in st.session_state:
        st.session_state[_CLE_SESSION] = LANGUE_PAR_DEFAUT


def langue():
    """Langue active — toujours l'une de LANGUES.

    Tant qu'`init_langue` n'a pas tourné, l'URL fait foi. Ce repli n'est pas
    théorique : une page qui traduit AVANT de monter sa coquille — c'est le
    cas de l'affiche, dont le titre et le sous-titre sont calculés pour être
    passés au socle — lisait une session encore vide, retombait sur le
    français, et n'affichait l'anglais qu'au premier rerun. Un lien partagé
    en `?lang=en` s'ouvrait donc en français.
    """

    if _CLE_SESSION not in st.session_state:
        demandee = st.query_params.get(PARAM_LANGUE)

        return demandee if demandee in LANGUES else LANGUE_PAR_DEFAUT

    return st.session_state.get(_CLE_SESSION, LANGUE_PAR_DEFAUT)


def definir_langue(nouvelle):
    """Change la langue et reflète le choix dans l'URL.

    Sans effet si la langue demandée est déjà active : un `st.rerun()` inutile
    ferait clignoter la page à chaque affichage du sélecteur.
    """

    if nouvelle not in LANGUES or nouvelle == langue():
        return

    st.session_state[_CLE_SESSION] = nouvelle

    if nouvelle == LANGUE_PAR_DEFAUT:
        # Le français étant la langue par défaut, ne pas encombrer l'URL.
        if PARAM_LANGUE in st.query_params:
            del st.query_params[PARAM_LANGUE]
    else:
        st.query_params[PARAM_LANGUE] = nouvelle

    st.rerun()


# ─── Le traducteur ───────────────────────────────────────────────────────────

def creer_traducteur(traductions, langue_active):
    """Fabrique la fonction `(cle, params) -> texte` d'un domaine.

    Transposition directe de `createTranslator` : même ordre de repli, même
    interpolation.
    """

    def traduire(cle, params=None):
        entree = traductions.get(cle)

        if entree is None:
            if _EN_DEV:
                print(f"[i18n] Clé de traduction absente : « {cle} »")
            # Renvoyer la clé plutôt qu'une chaîne vide : à l'écran, un
            # identifiant technique se remarque et se corrige ; un blanc, non.
            return str(cle)

        texte = entree.get(langue_active) or entree.get(LANGUE_PAR_DEFAUT, str(cle))

        if params:
            for nom, valeur in params.items():
                texte = texte.replace("{" + nom + "}", str(valeur))

        return texte

    return traduire


def t(domaine):
    """Traducteur d'un domaine, pour la langue active.

    C'est le point d'entrée de toutes les vues :

        tr = t("synthese")
        tr("titre")
        tr("part_region", {"region": "Maritime", "part": "60"})

    Le domaine est le nom du fichier JSON, sans extension. Chaque vue a le
    sien : `synthese`, `technique`, `financement`… plus les domaines partagés
    `commun`, `filtres`, `nav_sections`, `nav_items`.
    """

    return creer_traducteur(table(domaine), langue())


def traducteurs():
    """Raccourci pour les domaines de la coquille, utilisé par le shell."""

    active = langue()

    return {
        "langue": active,
        "commun": creer_traducteur(table("commun"), active),
        "filtres": creer_traducteur(table("filtres"), active),
        "nav_section": creer_traducteur(table("nav_sections"), active),
        "nav_item": creer_traducteur(table("nav_items"), active),
    }


# ─── Contrôle d'intégrité ────────────────────────────────────────────────────

def verifier_traductions():
    """Clés incomplètes et paramètres discordants, sur tous les domaines.

    Deux défauts qu'une relecture laisse passer et qui ne se voient qu'à
    l'exécution : une langue manquante (repli silencieux sur le français) et
    un `{parametre}` présent d'un côté mais pas de l'autre — la version
    traduite afficherait alors une accolade brute.

    Renvoie la liste des anomalies ; vide si tout est cohérent.
    """

    anomalies = []

    for domaine in domaines():
        for cle, entree in table(domaine).items():
            if not isinstance(entree, dict):
                anomalies.append(
                    f"{domaine}.{cle} : la valeur devrait être un objet "
                    "{{fr, en}}"
                )
                continue

            manquantes = [lg for lg in LANGUES if not entree.get(lg)]

            if manquantes:
                anomalies.append(
                    f"{domaine}.{cle} : langue(s) absente(s) — "
                    f'{", ".join(manquantes)}'
                )
                continue

            params = {lg: set(_MOTIF_PARAM.findall(entree[lg])) for lg in LANGUES}
            reference = params[LANGUE_PAR_DEFAUT]

            for lg in LANGUES:
                if params[lg] != reference:
                    anomalies.append(
                        f"{domaine}.{cle} : paramètres différents entre "
                        f"{LANGUE_PAR_DEFAUT} {sorted(reference)} et "
                        f"{lg} {sorted(params[lg])}"
                    )

    return anomalies
