"""Menu déclaratif de l'affiche — un seul objet décrit toute la navigation.

Le menu se construisait jusqu'ici par arguments épars : une liste de sections,
une liste de vues, deux fonctions de rendu, quatre couleurs, un routage. Sept
choses à tenir cohérentes à la main, et rien n'empêchait d'oublier la vue d'une
section ou de nommer deux entrées de la même façon.

Tout tient désormais dans une configuration :

    {
      "menu_active_color": "#006A4E",
      "menu_inactive_color": "#FFFFFF",
      "tab_active_color": "#FFFFFF",
      "tab_inactive_color": "transparent",
      "menu_items": [
        {
          "id": "synthese",
          "name": {"fr": "Synthèse", "en": "Summary"},
          "is_default": True,
          "url": "?s=affiche",              # facultatif — cf. plus bas
          "tab_items": [
            {
              "id": "diagnostic",
              "name": {"fr": "Home", "en": "Home"},
              "is_default": True,
              "component": peindre,          # ou {"gauche": …, "droite": …}
            },
          ],
        },
      ],
    }

Deux choix que la forme ne dicte pas :

  · `url` est FACULTATIF. L'`id` suffit à router — c'est lui qui part dans
    `?sec=` et `?v=`. L'URL, quand elle est donnée, sert de lien canonique :
    une entrée peut ainsi pointer hors de l'affiche, et c'est ce qui permet
    aux sorties de vivre dans le même menu que les vues sans être des vues.

  · `can_view` masque une entrée ou un onglet SANS le supprimer. Il vaut vrai
    par défaut. C'est une autorisation d'affichage, jamais une sécurité : le
    composant n'est pas rendu, mais rien n'empêche d'atteindre son URL. Une
    donnée qu'il ne faut pas montrer ne se cache pas dans un menu.

    La configuration en donne la valeur INITIALE ; l'utilisateur la change
    depuis la fenêtre de réglages, et son choix vit dans la session. Les deux
    ne se contredisent pas — la session l'emporte, et un rechargement rend la
    configuration.

  · `component` accepte une FONCTION ou un COUPLE `{gauche, droite}`. L'affiche
    a deux colonnes ; une entrée qui ne déclare qu'une fonction peint la
    gauche, et la droite retombe sur la carte de référence de sa section.
    Exiger le couple partout obligerait à répéter la même carte vingt fois.

Les libellés vivent dans la configuration, et non dans un fichier i18n séparé,
parce que la configuration EST une donnée : elle porte déjà l'ordre, les
identifiants et les défauts. Séparer les noms en obligerait à tenir deux
fichiers alignés pour un même objet.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

PARAM_MENU = "sec"
PARAM_ONGLET = "v"

_CLE_MENU = "_menu_actif"
_CLE_ONGLET = "_onglet_actif"

# Préfixe des clés de session qui portent les autorisations d'affichage. Une
# clé par entrée et par onglet, nommée depuis son identifiant : deux onglets de
# même identifiant dans deux sections différentes partageraient sinon leur
# visibilité.
_PREFIXE_VU = "_menu_vu_"

# Couleurs par défaut : celles du socle. Une configuration qui n'en passe
# aucune garde exactement la charte commune.
COULEURS = {
    "menu_active_color": "var(--kg-color-primary)",
    "menu_inactive_color": "transparent",
    "tab_active_color": "var(--kg-color-surface)",
    "tab_inactive_color": "transparent",
    # La bascule de langue prend place dans le même rang que le menu, et se
    # règle donc au même endroit. Elle garde pourtant sa propre paire : elle ne
    # mène nulle part — elle traduit — et lui donner la teinte d'une section
    # laisserait croire qu'on peut « aller » en anglais comme on va au Risque.
    "lang_active_color": "var(--kg-color-surface)",
    "lang_inactive_color": "transparent",
}


def _texte(nom, langue):
    """Le libellé dans la langue demandée, sans jamais rendre None.

    Un nom manquant affiche l'identifiant plutôt qu'un vide : sur un menu, une
    case sans texte est un cul-de-sac que rien ne signale.
    """

    if isinstance(nom, str):
        return nom

    if isinstance(nom, dict):
        return nom.get(langue) or nom.get("fr") or next(iter(nom.values()), "")

    return ""


# Le nom PUBLIC de la traduction d'un libellé. La fenêtre de réglages du shell
# affiche les mêmes noms que le rail, et doit donc les résoudre de la même
# façon — passer par le nom privé aurait été un aveu de couche mal découpée.
texte = _texte


def verifier(config):
    """Anomalies de la configuration, en clair — avant tout rendu.

    Une configuration fausse se manifeste sinon par un symptôme sans rapport
    avec sa cause : deux entrées de même identifiant donnent une navigation qui
    « ne répond pas », un onglet sans composant une colonne vide. On préfère
    une liste de reproches nommés.
    """

    reproches = []
    entrees = config.get("menu_items") or []

    if not entrees:
        reproches.append("`menu_items` est vide : le menu n'a rien à afficher.")

    vus = set()

    for entree in entrees:
        cle = entree.get("id")

        if not cle:
            reproches.append("Une entrée de menu n'a pas d'`id`.")
            continue

        if cle in vus:
            reproches.append(f"L'identifiant « {cle} » est utilisé deux fois.")

        vus.add(cle)

        onglets = entree.get("tab_items") or []

        if not onglets and not entree.get("url"):
            reproches.append(
                f"« {cle} » n'a ni onglet ni URL : elle ne mène nulle part."
            )

        vus_onglets = set()

        for onglet in onglets:
            cle_onglet = onglet.get("id")

            if not cle_onglet:
                reproches.append(f"Un onglet de « {cle} » n'a pas d'`id`.")
                continue

            if cle_onglet in vus_onglets:
                reproches.append(
                    f"L'onglet « {cle_onglet} » apparaît deux fois dans "
                    f"« {cle} »."
                )

            vus_onglets.add(cle_onglet)

            if not onglet.get("component") and not onglet.get("url"):
                reproches.append(
                    f"L'onglet « {cle_onglet} » n'a ni composant ni URL : "
                    f"il afficherait une page vide."
                )

    return reproches


def cle_visibilite(element, parent=None):
    """La clé de session qui porte l'autorisation d'un élément."""

    identifiant = element.get("id", "")

    return f"{_PREFIXE_VU}{parent + '.' if parent else ''}{identifiant}"


# Le fichier d'utilisateurs de l'application, quand elle en déclare un. Posé
# par `render_affiche` au début du rendu : `visible()` est appelée par le rail,
# par le routage et par la fenêtre, et lui passer le chemin à chaque fois
# aurait traversé six signatures pour un réglage qui ne change jamais en cours
# de page.
_FICHIER_UTILISATEURS = None


def brancher_utilisateurs(fichier):
    """Déclare d'où viennent les autorisations. `None` rend la main à la session."""

    global _FICHIER_UTILISATEURS
    _FICHIER_UTILISATEURS = fichier


def visible(element, parent=None):
    """L'élément doit-il être affiché ?

    Trois sources, dans cet ordre :

      1. l'UTILISATEUR actif, quand l'application en déclare — c'est lui qui
         porte les autorisations, et elles survivent au rechargement ;
      2. la SESSION, sinon : le choix vient d'être fait dans la fenêtre, et le
         reprendre au rendu suivant serait incompréhensible ;
      3. la CONFIGURATION du défi — `can_view`, vrai par défaut.
    """

    identifiant = element.get("id")

    if _FICHIER_UTILISATEURS:
        # pyrefly: ignore [missing-import]
        from socle.shell import utilisateurs

        # Le PROFIL de l'utilisateur actif, non l'utilisateur : deux personnes
        # du même profil voient la même chose, et c'est là tout l'intérêt d'un
        # profil.
        porteur = utilisateurs.profil_actif(_FICHIER_UTILISATEURS)

        if porteur is not None:
            return utilisateurs.autorise(
                porteur, parent or identifiant,
                identifiant if parent else None,
                defaut=bool(element.get("can_view", True)),
            )

    # pyrefly: ignore [missing-attribute]
    retenu = st.session_state.get(cle_visibilite(element, parent))

    if retenu is None:
        return bool(element.get("can_view", True))

    return bool(retenu)


def autoriser(element, valeur, parent=None):
    """Écrit l'autorisation d'un élément dans la session."""

    st.session_state[cle_visibilite(element, parent)] = bool(valeur)


def oublier_autorisations(config):
    """Rend la main à la configuration — le bouton « tout réafficher »."""

    for entree in config.get("menu_items") or []:
        st.session_state.pop(cle_visibilite(entree), None)

        for onglet in entree.get("tab_items") or []:
            st.session_state.pop(cle_visibilite(onglet, entree.get("id")), None)


def entrees_visibles(config):
    """Les entrées de menu que l'utilisateur a le droit de voir.

    Une section dont TOUS les onglets sont coupés disparaît avec eux : elle
    mènerait à une colonne vide, et un onglet de menu qui n'ouvre rien est
    pire qu'un onglet absent.

    Si TOUT est masqué, on rend la liste entière plutôt qu'un écran vide : un
    menu sans entrée n'est pas un menu, et l'utilisateur n'aurait plus aucun
    moyen de rouvrir la fenêtre qui lui rendrait ses sections.
    """

    entrees = config.get("menu_items") or []
    retenues = []

    for entree in entrees:
        if not visible(entree):
            continue

        onglets = entree.get("tab_items") or []

        if onglets and not any(visible(o, entree.get("id")) for o in onglets):
            continue

        retenues.append(entree)

    return retenues or entrees


def onglets_visibles(entree):
    """Les onglets affichables d'une entrée.

    Aucun repli ici, à la différence des entrées : une section sans onglet
    visible a déjà été écartée par `entrees_visibles`, et lui rendre ses
    onglets la ferait réapparaître par la bande.
    """

    return [o for o in (entree.get("tab_items") or [])
            if visible(o, entree.get("id"))]


def _defaut(elements):
    """Le premier élément marqué par défaut, sinon le premier tout court."""

    for element in elements:
        if element.get("is_default"):
            return element.get("id")

    return elements[0].get("id") if elements else None


def _actif(elements, parametre, cle_session):
    """Élément retenu — l'URL fait autorité, la session complète.

    L'URL d'abord : Streamlit restaure la session au rechargement, si bien
    qu'une amorce faite une seule fois par session ferait ignorer un lien
    partagé — on rouvrirait la page sur l'entrée mémorisée, pas sur celle du
    lien reçu.
    """

    cles = [element.get("id") for element in elements]

    if not cles:
        return None

    demande = st.query_params.get(parametre)

    if demande in cles:
        st.session_state[cle_session] = demande
    elif st.session_state.get(cle_session) not in cles:
        st.session_state[cle_session] = _defaut(elements)

    return st.session_state[cle_session]


def _aller(cle, parametre, cle_session, defaut, effacer=()):
    """Change d'entrée et reflète le choix dans l'URL.

    L'entrée par DÉFAUT ne s'écrit pas dans l'URL : une adresse nue doit rester
    l'adresse canonique de la page, sinon deux liens différents désignent le
    même écran.
    """

    st.session_state[cle_session] = cle

    for autre in effacer:
        st.session_state.pop(autre, None)
        st.query_params.pop(PARAM_ONGLET, None)

    if cle == defaut:
        st.query_params.pop(parametre, None)
    else:
        st.query_params[parametre] = cle

    st.rerun()


def styles(config, portee_menu="kgaffsections", portee_onglets="kgaffvues",
           portee_langue="kgafflang"):
    """Feuille des six couleurs — n'écrit QUE ce qui est demandé."""

    couleurs = {**COULEURS, **{c: v for c, v in config.items()
                               if c in COULEURS and v}}

    actif = '[data-testid="stBaseButton-segmented_controlActive"]'
    inactif = '[data-testid="stBaseButton-segmented_control"]'

    return (
        "<style>"
        f".st-key-{portee_menu} {actif} {{"
        f" background: {couleurs['menu_active_color']}; }}"
        f".st-key-{portee_menu} {inactif} {{"
        f" background: {couleurs['menu_inactive_color']}; }}"
        f".st-key-{portee_onglets} {actif} {{"
        f" background: {couleurs['tab_active_color']}; }}"
        f".st-key-{portee_onglets} {inactif} {{"
        f" background: {couleurs['tab_inactive_color']}; }}"
        # La bascule est faite de deux `st.button`, non d'un groupe segmenté :
        # ses deux cases sont des ACTIONS, pas un choix parmi une liste.
        f'.st-key-{portee_langue} [data-testid="stButton"] > button[kind="primary"] {{'
        f" background: {couleurs['lang_active_color']}; }}"
        f'.st-key-{portee_langue} [data-testid="stButton"] > button {{'
        f" background: {couleurs['lang_inactive_color']}; }}"
        "</style>"
    )


def resoudre(config, langue):
    """L'état de navigation : entrée retenue, onglet retenu, et son composant.

    Ne peint rien — la résolution doit précéder le rendu, puisque c'est elle
    qui dit quelle liste d'onglets le menu affichera.
    """

    # Les entrées MASQUÉES sortent du rail comme du routage : une section
    # cachée dont l'URL resterait active reviendrait au premier clic.
    entrees = entrees_visibles(config)
    menu = _actif(entrees, PARAM_MENU, _CLE_MENU)
    entree = next((e for e in entrees if e.get("id") == menu),
                  entrees[0] if entrees else {})

    onglets = onglets_visibles(entree)
    onglet = _actif(onglets, PARAM_ONGLET, _CLE_ONGLET)
    courant = next((o for o in onglets if o.get("id") == onglet),
                   onglets[0] if onglets else {})

    return {
        "menu": menu,
        "entree": entree,
        "onglet": onglet,
        "courant": courant,
        "entrees": [{"key": e.get("id"), "label": _texte(e.get("name"), langue),
                     "url": e.get("url")} for e in entrees],
        "onglets": [{"key": o.get("id"), "label": _texte(o.get("name"), langue),
                     "url": o.get("url")} for o in onglets],
        "defaut_menu": _defaut(entrees),
        "defaut_onglet": _defaut(onglets),
    }


def peindre(etat, cle):
    """Le composant de l'onglet retenu, dans la colonne demandée.

    `cle` vaut « gauche » ou « droite ». Un composant déclaré comme simple
    fonction peint la GAUCHE : c'est la colonne du propos, et une entrée qui
    n'a rien de particulier à montrer à droite doit pouvoir se taire plutôt
    que de répéter la carte de sa section.

    Renvoie True si quelque chose a été peint — l'appelant sait alors s'il
    doit poser sa carte de référence.
    """

    composant = (etat.get("courant") or {}).get("component")

    if composant is None:
        return False

    if isinstance(composant, dict):
        fonction = composant.get(cle)
    else:
        fonction = composant if cle == "gauche" else None

    if fonction is None:
        return False

    fonction()

    return True


def aller_au_menu(cle, etat):
    """Change d'entrée de menu, et retombe sur son onglet par défaut."""

    if st.session_state.get(_CLE_MENU) == cle:
        return

    _aller(cle, PARAM_MENU, _CLE_MENU, etat["defaut_menu"],
           effacer=(_CLE_ONGLET,))


def aller_a_l_onglet(cle, etat):
    """Change d'onglet à l'intérieur de l'entrée courante."""

    if st.session_state.get(_CLE_ONGLET) == cle:
        return

    _aller(cle, PARAM_ONGLET, _CLE_ONGLET, etat["defaut_onglet"])


def reference(etat):
    """Le peintre de repli de la colonne droite, déclaré par l'ENTRÉE.

    Une entrée de menu porte souvent une carte qui vaut pour tous ses onglets.
    La déclarer une fois sur l'entrée évite de la répéter sur chacun d'eux —
    et surtout évite qu'un onglet ajouté plus tard l'oublie et laisse la
    colonne droite vide.
    """

    return (etat.get("entree") or {}).get("reference")


def parametres(url):
    """Les paramètres d'URL d'une sortie, qu'elle soit écrite en chaîne ou en dict.

    La configuration peut donner une adresse complète — telle qu'on la copie
    depuis la barre du navigateur — ou directement les paramètres. La première
    forme est celle qu'on écrit naturellement, la seconde celle qu'on relit
    sans se tromper : les deux sont acceptées.
    """

    if isinstance(url, dict):
        return dict(url)

    if not isinstance(url, str):
        return {}

    from urllib.parse import urlparse, parse_qsl

    return dict(parse_qsl(urlparse(url).query))


def est_sortie(element):
    """Une entrée qui porte une URL et aucun composant QUITTE l'affiche."""

    return bool(element.get("url")) and not element.get("component")
