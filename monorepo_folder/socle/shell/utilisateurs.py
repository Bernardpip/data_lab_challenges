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

def _vide():
    return {"actif": None, "utilisateurs": []}


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
    etat.setdefault("utilisateurs", [])
    st.session_state[_CLE_ETAT] = etat

    return etat


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


def ajouter(fichier, prenom, nom, profil, email, photo=None, profils=None):
    """Crée une personne et lui donne les autorisations de son profil."""

    etat = charger(fichier)
    existants = {u.get("id") for u in etat["utilisateurs"]}
    identifiant = _identifiant(prenom, nom, existants)

    etat["utilisateurs"].append({
        "id": identifiant,
        "prenom": prenom.strip(),
        "nom": nom.strip(),
        "profil": profil,
        "email": email.strip(),
        "photo": photo,
        # Les autorisations du PROFIL sont copiées, non référencées : changer
        # un profil plus tard ne doit pas redistribuer en silence ce que
        # chacun voit.
        "autorisations": dict((profils or {}).get(profil, {}).get(
            "autorisations", {})),
    })

    if not etat.get("actif"):
        etat["actif"] = identifiant

    enregistrer(fichier)

    return identifiant


def supprimer(fichier, identifiant):
    etat = charger(fichier)
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


def autorise(utilisateur, section, onglet=None, defaut=True):
    """Cette personne voit-elle cet élément ?"""

    if not utilisateur:
        return defaut

    table = utilisateur.get("autorisations") or {}

    return bool(table.get(cle(section, onglet), defaut))


def autoriser(fichier, identifiant, section, valeur, onglet=None):
    """Écrit une autorisation et la persiste."""

    personne = trouver(fichier, identifiant)

    if personne is None:
        return

    personne.setdefault("autorisations", {})[cle(section, onglet)] = bool(valeur)
    enregistrer(fichier)


def tout_autoriser(fichier, identifiant):
    """Vide la table : la personne retrouve la configuration du défi."""

    personne = trouver(fichier, identifiant)

    if personne is not None:
        personne["autorisations"] = {}
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
