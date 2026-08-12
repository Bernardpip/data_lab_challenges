"""Utilisateurs de l'affiche — qui regarde, et ce qu'on lui montre.

**Ce n'est pas une authentification, et le module ne prétend pas l'être.** Il
n'y a ni mot de passe, ni session serveur, ni contrôle d'accès : on choisit son
utilisateur dans une liste, et l'adresse d'une section masquée reste
atteignable. C'est un SÉLECTEUR DE PROFIL D'AFFICHAGE, et la fenêtre le dit en
toutes lettres. Une donnée qu'il ne faut pas montrer ne se range pas ici.

Ce qu'il fait, en revanche : il donne à un tableau de bord de trente vues la
possibilité d'en montrer six à qui n'en veut que six. Un décideur qui ouvre
l'affiche sur le constat et la proposition n'a pas à traverser les recettes de
nettoyage pour les trouver.

Tout tient dans UN fichier JSON, photos comprises, encodées en base64. Un
dossier d'images à côté aurait divisé l'état en deux objets qu'il aurait fallu
déplacer ensemble — et la première photo perdue aurait laissé une carte muette.

Le fichier est local au serveur, non au navigateur : `localStorage` n'est pas
atteignable depuis Streamlit sans écrire un composant. Sur un poste de travail,
il survit aux rechargements ; derrière un déploiement partagé, il est commun à
tous les visiteurs et repart à zéro à chaque livraison. C'est écrit dans le
DEPLOIEMENT, et ce n'est pas un défaut qu'on peut corriger ici.
"""

import base64
import html
import json
import re
import unicodedata
from io import BytesIO
from pathlib import Path

# pyrefly: ignore [missing-import]
import streamlit as st

# Côté du carré d'avatar, en pixels. Les photos sont RECADRÉES à cette taille
# avant d'entrer dans le fichier : une photo de téléphone y pèserait trois
# mégaoctets encodés, pour un rond de vingt-huit pixels à l'écran.
COTE_PHOTO = 96

_CLE_ETAT = "_kg_utilisateurs"
_CLE_ECRAN = "_kg_utilisateurs_ecran"


# ─── Le fichier ──────────────────────────────────────────────────────────────

# L'identifiant du profil et de l'utilisateur que le socle pose lui-même. Tous
# deux sont VERROUILLÉS : ni modifiables, ni supprimables. Sans eux, une
# fenêtre vide n'offrirait aucun moyen de créer le premier profil, et un
# fichier dont on aurait supprimé le dernier profil laisserait ses utilisateurs
# sans autorisations.
PROFIL_ADMIN = "administrateur"
UTILISATEUR_ADMIN = "admin"


def _vide():
    return {"actif": None, "profils": [], "utilisateurs": []}


def charger(fichier):
    """L'état des utilisateurs, lu une fois par session puis mémorisé.

    Le fichier absent n'est pas une erreur : c'est le premier lancement. Un
    fichier ILLISIBLE, lui, est signalé plutôt qu'écrasé — il contient peut-être
    le travail de quelqu'un, et le remplacer en silence par un état vide serait
    la pire des réponses.
    """

    if _CLE_ETAT in st.session_state:
        return st.session_state[_CLE_ETAT]

    chemin = Path(fichier)
    etat = _vide()

    if chemin.exists():
        try:
            etat = json.loads(chemin.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as erreur:
            st.warning(f"{chemin.name} : {erreur}")

    etat.setdefault("actif", None)
    etat.setdefault("profils", [])
    etat.setdefault("utilisateurs", [])
    st.session_state[_CLE_ETAT] = etat

    return etat


def _aujourdhui():
    from datetime import date

    return date.today().isoformat()


def initialiser(fichier, defauts=None):
    """Pose le profil et l'utilisateur d'origine, s'ils manquent.

    Appelée à chaque rendu, elle n'écrit qu'au premier : c'est le seul moment
    où le fichier n'existe pas encore, et le seul où l'application aurait
    autrement une fenêtre sans rien dedans.

    Les deux sont VERROUILLÉS. L'administrateur voit tout et ne se règle pas :
    c'est le profil de recours, celui qui reste quand tous les autres ont été
    coupés. Le supprimer laisserait un tableau de bord dont plus personne ne
    peut rouvrir les sections.
    """

    defauts = defauts or {}
    etat = charger(fichier)
    ecrire = False

    if not any(p.get("id") == PROFIL_ADMIN for p in etat["profils"]):
        etat["profils"].insert(0, {
            "id": PROFIL_ADMIN,
            "nom": defauts.get("profil_nom") or "Administrateur",
            "cree_le": _aujourdhui(),
            "verrouille": True,
            "autorisations": {},
        })
        ecrire = True

    if not any(u.get("id") == UTILISATEUR_ADMIN for u in etat["utilisateurs"]):
        prenom = defauts.get("prenom") or "Admin"
        nom = defauts.get("nom") or ""
        etat["utilisateurs"].insert(0, {
            "id": UTILISATEUR_ADMIN,
            "prenom": prenom,
            "nom": nom,
            "email": defauts.get("email") or "",
            # Une photo POSÉE, non téléversée : le premier utilisateur doit
            # avoir un visage comme les autres, sans qu'on ait à lui en
            # demander un.
            "photo": photo_par_defaut(f"{prenom[:1]}{nom[:1]}".upper() or "A"),
            "profil": PROFIL_ADMIN,
            "verrouille": True,
        })
        ecrire = True

    if not etat.get("actif"):
        etat["actif"] = UTILISATEUR_ADMIN
        ecrire = True

    if ecrire:
        enregistrer(fichier)


def enregistrer(fichier):
    """Écrit l'état sur le disque, en créant le dossier au besoin."""

    chemin = Path(fichier)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(
        json.dumps(st.session_state.get(_CLE_ETAT, _vide()),
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ─── Les personnes ───────────────────────────────────────────────────────────

def _identifiant(prenom, nom, existants):
    """Un identifiant lisible et stable, tiré du nom.

    Lisible parce qu'il se retrouve dans le fichier JSON, qu'un humain ouvrira
    un jour ; stable parce qu'il sert de clé aux autorisations, et qu'un
    identifiant qui changerait avec le nom les perdrait toutes.
    """

    brut = f"{prenom}-{nom}".strip("- ").lower()
    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", brut)
        if unicodedata.category(c) != "Mn"
    )
    base = re.sub(r"[^a-z0-9]+", "-", sans_accent).strip("-") or "utilisateur"

    if base not in existants:
        return base

    rang = 2

    while f"{base}-{rang}" in existants:
        rang += 1

    return f"{base}-{rang}"


def profils(fichier):
    return charger(fichier).get("profils") or []


def profil(fichier, identifiant):
    return next((p for p in profils(fichier) if p.get("id") == identifiant),
                None)


def ajouter_profil(fichier, nom):
    """Crée un profil vide — il voit tout tant qu'on ne lui a rien coupé."""

    etat = charger(fichier)
    existants = {p.get("id") for p in etat["profils"]}
    identifiant = _identifiant(nom, "", existants)

    etat["profils"].append({
        "id": identifiant,
        "nom": nom.strip(),
        "cree_le": _aujourdhui(),
        "verrouille": False,
        "autorisations": {},
    })
    enregistrer(fichier)

    return identifiant


def supprimer_profil(fichier, identifiant):
    """Retire un profil et REND ses utilisateurs à l'administrateur.

    Les laisser pointer sur un profil disparu les priverait de toute
    autorisation — donc de tout menu — sans que rien ne l'explique.
    """

    etat = charger(fichier)
    vise = profil(fichier, identifiant)

    if vise is None or vise.get("verrouille"):
        return

    etat["profils"] = [p for p in etat["profils"]
                       if p.get("id") != identifiant]

    for personne in etat["utilisateurs"]:
        if personne.get("profil") == identifiant:
            personne["profil"] = PROFIL_ADMIN

    enregistrer(fichier)


def porteurs(fichier, identifiant):
    """Combien d'utilisateurs portent ce profil — ce que sa carte annonce."""

    return sum(1 for u in liste(fichier) if u.get("profil") == identifiant)


def liste(fichier):
    return charger(fichier).get("utilisateurs") or []


def trouver(fichier, identifiant):
    return next((u for u in liste(fichier) if u.get("id") == identifiant), None)


def actif(fichier):
    """L'utilisateur actif, ou le premier, ou aucun.

    Le repli sur le PREMIER est délibéré : un fichier dont l'actif a été
    supprimé rendrait sinon une affiche sans utilisateur, donc sans avatar,
    donc sans porte vers la fenêtre qui aurait permis d'en choisir un.
    """

    etat = charger(fichier)
    gens = etat.get("utilisateurs") or []

    if not gens:
        return None

    return trouver(fichier, etat.get("actif")) or gens[0]


def definir_actif(fichier, identifiant):
    charger(fichier)["actif"] = identifiant
    enregistrer(fichier)


def ajouter(fichier, prenom, nom, profil_id, email, photo=None):
    """Crée une personne et la RATTACHE à un profil.

    Rattachée, non copiée : les autorisations vivent désormais dans le profil,
    et régler celui-ci règle d'un coup tous ceux qui le portent. C'est tout
    l'intérêt d'un profil — sans quoi il ne serait qu'un modèle de départ.
    """

    etat = charger(fichier)
    existants = {u.get("id") for u in etat["utilisateurs"]}
    identifiant = _identifiant(prenom, nom, existants)

    etat["utilisateurs"].append({
        "id": identifiant,
        "prenom": prenom.strip(),
        "nom": nom.strip(),
        "profil": profil_id or PROFIL_ADMIN,
        "email": email.strip(),
        "photo": photo,
        "verrouille": False,
    })

    if not etat.get("actif"):
        etat["actif"] = identifiant

    enregistrer(fichier)

    return identifiant


def supprimer(fichier, identifiant):
    etat = charger(fichier)
    vise = trouver(fichier, identifiant)

    if vise is None or vise.get("verrouille"):
        return

    etat["utilisateurs"] = [u for u in etat["utilisateurs"]
                            if u.get("id") != identifiant]

    if etat.get("actif") == identifiant:
        etat["actif"] = (etat["utilisateurs"][0]["id"]
                         if etat["utilisateurs"] else None)

    enregistrer(fichier)


# ─── Les autorisations ───────────────────────────────────────────────────────
#
# Elles vivent DANS la personne, sous forme d'une table plate `{clé: bool}` où
# la clé est l'identifiant d'une section, ou « section.onglet » pour un onglet.
# Une table plate plutôt que deux niveaux imbriqués : c'est la forme que le
# menu interroge, et l'imbrication n'aurait servi qu'à l'écriture du fichier.
#
# Seules les EXCEPTIONS sont écrites. Une section absente de la table est
# visible : un fichier n'enregistre donc que les décisions prises, et une vue
# ajoutée demain apparaît chez tout le monde au lieu de rester cachée chez
# ceux dont le fichier date d'avant.

def cle(section, onglet=None):
    return f"{section}.{onglet}" if onglet else str(section)


def autorise(porteur, section, onglet=None, defaut=True):
    """Ce PROFIL laisse-t-il voir cet élément ?

    `porteur` est un profil, non un utilisateur : deux personnes du même
    profil voient exactement la même chose, et c'est la raison d'être d'un
    profil. Régler l'un règle les autres.
    """

    if not porteur:
        return defaut

    table = porteur.get("autorisations") or {}

    return bool(table.get(cle(section, onglet), defaut))


def profil_actif(fichier):
    """Le profil de l'utilisateur actif — ce que le menu interroge."""

    personne = actif(fichier)

    if personne is None:
        return None

    return profil(fichier, personne.get("profil")) or profil(
        fichier, PROFIL_ADMIN)


def autoriser(fichier, profil_id, section, valeur, onglet=None):
    """Écrit une autorisation dans un profil et la persiste.

    Un profil VERROUILLÉ ne bouge pas : l'administrateur est le recours, et
    un recours qu'on peut couper n'en est pas un.
    """

    vise = profil(fichier, profil_id)

    if vise is None or vise.get("verrouille"):
        return

    vise.setdefault("autorisations", {})[cle(section, onglet)] = bool(valeur)
    enregistrer(fichier)


def autoriser_plusieurs(fichier, profil_id, valeurs):
    """Écrit d'un coup toute la table d'un profil — un seul passage au disque.

    `valeurs` : {(section, onglet|None): bool | None}. Poser les quarante-six
    autorisations d'un écran une par une rouvrait et réécrivait le fichier
    quarante-six fois pour un seul geste de l'utilisateur.

    Une valeur NULLE efface la ligne. C'est ainsi que la table ne garde que
    les exceptions : ce qui suit la configuration du défi n'y figure pas, et
    une vue ajoutée demain apparaîtra chez tout le monde au lieu de rester
    cachée chez ceux dont le fichier date d'avant.
    """

    vise = profil(fichier, profil_id)

    if vise is None or vise.get("verrouille"):
        return

    table = vise.setdefault("autorisations", {})

    for (section, onglet), valeur in valeurs.items():
        if valeur is None:
            table.pop(cle(section, onglet), None)
        else:
            table[cle(section, onglet)] = bool(valeur)

    enregistrer(fichier)


def tout_autoriser(fichier, profil_id):
    """Vide la table : le profil retrouve la configuration du défi."""

    vise = profil(fichier, profil_id)

    if vise is not None and not vise.get("verrouille"):
        vise["autorisations"] = {}
        enregistrer(fichier)


# ─── L'avatar ────────────────────────────────────────────────────────────────

# Une image de données, et RIEN D'AUTRE. Le fichier des utilisateurs
# s'édite à la main : une valeur de photo forgée sortirait sinon de son
# `url("…")` pour écrire n'importe quelle règle dans la feuille de style, ou
# de son attribut `src` pour poser un gestionnaire d'événement. On ne
# désinfecte pas la chaîne — on refuse tout ce qui n'a pas exactement cette
# forme.
_IMAGE_DONNEES = re.compile(
    r"^data:image/(png|jpe?g|webp);base64,[A-Za-z0-9+/]+={0,2}$")


def photo_sure(personne):
    """La photo si elle est une image de données valide, sinon rien.

    Appelée par TOUS les rendus — l'avatar, la carte, le fond du bouton
    d'en-tête. Une seule porte d'entrée : la validation faite à l'écriture
    seule ne protégerait pas un fichier arrivé d'ailleurs.
    """

    photo = (personne or {}).get("photo")

    if not isinstance(photo, str) or not _IMAGE_DONNEES.match(photo):
        return None

    return photo


def initiales(personne):
    if not personne:
        return "··"

    lettres = [(personne.get("prenom") or " ")[:1],
               (personne.get("nom") or " ")[:1]]

    # ÉCHAPPÉES : ce sont des caractères saisis par un humain, et ils partent
    # dans du HTML. Une initiale « < » y ouvrirait une balise.
    return html.escape("".join(lettres).upper().strip()) or "··"


def avatar(personne, taille=28, bordure=None):
    """Le rond de l'utilisateur — sa photo, ou ses initiales.

    Les initiales et non un pictogramme générique : dans une liste de trois
    personnes, trois silhouettes identiques ne distinguent rien, et c'est
    précisément ce qu'un avatar doit faire.
    """

    trait = (f"box-shadow:0 0 0 2px {bordure};" if bordure else "")
    commun = (
        f"width:{taille}px;height:{taille}px;border-radius:50%;"
        f"flex:none;display:inline-flex;align-items:center;"
        f"justify-content:center;overflow:hidden;{trait}"
    )

    photo = photo_sure(personne)

    if photo:
        return (
            f'<span style="{commun}">'
            f'<img src="{html.escape(photo, quote=True)}" alt="" '
            f'style="width:100%;height:100%;object-fit:cover;"></span>'
        )

    return (
        f'<span style="{commun}background:var(--kg-color-surface-secondary);'
        f"color:var(--kg-color-text-secondary);font-weight:650;"
        f'font-size:{max(9, round(taille * 0.38))}px;letter-spacing:.02em;">'
        f"{initiales(personne)}</span>"
    )


# La teinte du visage posé d'office — le vert du drapeau togolais. Le socle
# n'a pas de charte, mais il faut bien une couleur : celle-ci se remplace en
# passant `couleur` à la fonction.
_VERT_DEFAUT = (0, 106, 78)


def photo_par_defaut(initiales_="A", couleur=_VERT_DEFAUT):
    """Un avatar DESSINÉ, pour l'utilisateur que le socle pose lui-même.

    Une image plutôt qu'un repli sur les initiales : le premier utilisateur
    doit avoir un visage comme les autres, sinon sa carte se distingue par un
    manque qu'aucune règle n'explique. Elle est produite ici, à la même taille
    et au même format que les photos téléversées, et passe donc la même
    validation qu'elles.
    """

    try:
        # pyrefly: ignore [missing-import]
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    image = Image.new("RGB", (COTE_PHOTO, COTE_PHOTO), couleur)
    dessin = ImageDraw.Draw(image)
    texte = (initiales_ or "A")[:2].upper()

    # La police par défaut de Pillow est une image bitmap de onze pixels :
    # dessinée telle quelle sur un carré de 96, elle donnait deux lettres
    # minuscules perdues au milieu. `load_default(size=…)` rend une police
    # vectorielle depuis Pillow 10.1 ; en dessous, on garde la petite plutôt
    # que d'échouer.
    try:
        police = ImageFont.load_default(size=round(COTE_PHOTO * 0.42))
    except TypeError:
        police = ImageFont.load_default()

    boite = dessin.textbbox((0, 0), texte, font=police)
    largeur, hauteur = boite[2] - boite[0], boite[3] - boite[1]
    dessin.text(((COTE_PHOTO - largeur) / 2 - boite[0],
                 (COTE_PHOTO - hauteur) / 2 - boite[1]),
                texte, fill=(255, 255, 255), font=police)

    tampon = BytesIO()
    image.save(tampon, format="PNG", optimize=True)

    return "data:image/png;base64," + base64.b64encode(
        tampon.getvalue()).decode("ascii")


def texte_sur(valeur):
    """Un champ saisi, rendu inoffensif pour l'interpolation dans du HTML.

    Les vues de ce socle composent leur mise en forme à la main et rendent
    avec `unsafe_allow_html` : un nom, un prénom ou une adresse qui y entre
    sans passer par ici s'exécute chez tous ceux qui ouvrent la fenêtre.
    """

    return html.escape(str(valeur or ""))


def photo_encodee(fichier_televerse):
    """Une photo téléversée, recadrée en carré et encodée pour le JSON.

    Recadrée au CENTRE plutôt que déformée : un visage étiré est pire qu'un
    visage rogné. Pillow arrive avec Streamlit — aucune dépendance ajoutée.
    """

    if fichier_televerse is None:
        return None

    # pyrefly: ignore [missing-import]
    from PIL import Image

    image = Image.open(fichier_televerse).convert("RGB")
    cote = min(image.size)
    gauche = (image.width - cote) // 2
    haut = (image.height - cote) // 2

    image = image.crop((gauche, haut, gauche + cote, haut + cote))
    image = image.resize((COTE_PHOTO, COTE_PHOTO), Image.LANCZOS)

    tampon = BytesIO()
    image.save(tampon, format="PNG", optimize=True)

    return "data:image/png;base64," + base64.b64encode(
        tampon.getvalue()).decode("ascii")


# ─── L'écran courant de la fenêtre ───────────────────────────────────────────

def ecran():
    """Quel écran la fenêtre montre — liste, création, ou droits d'une personne.

    L'état vit en session et non dans une variable du module : Streamlit rejoue
    le script à chaque interaction, et une variable ne survivrait pas au clic
    qui vient de la poser.
    """

    return st.session_state.get(_CLE_ECRAN) or ("liste", None)


def aller_a(nom, identifiant=None):
    st.session_state[_CLE_ECRAN] = (nom, identifiant)
