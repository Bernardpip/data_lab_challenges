"""Nettoyage des données ouvertes — sans ça les graphes affichent des catégories
fantômes ("{Construit et Utilise,En construction}", "Nsp", "N/a", et le doublon
de casse "Formation profesionnelle autre").

Chaque fonction renvoie une copie : les DataFrames chargés restent intacts.
"""

import re

import pandas as pd

NON_RENSEIGNE = "Non renseigné"

# Valeurs sentinelles de non-réponse rencontrées dans les fichiers.
_MISSING = {"nsp", "n/a", "na", "ne sait pas", "neant", "néant", "", "nan", "autre"}


def _strip_braces(value):
    """`{Construit et Utilise,En construction}` → ['Construit et Utilise', ...]."""

    if pd.isna(value):
        return []

    text = str(value).strip()
    text = re.sub(r"^\{|\}$", "", text)

    parts = [p.strip().strip('"').strip() for p in text.split(",")]
    return [p for p in parts if p]


def _normalize_label(label):
    """Casse/accents harmonisés + sentinelles repliées sur « Non renseigné »."""

    clean = re.sub(r"\s+", " ", str(label)).strip()

    if clean.lower() in _MISSING:
        return NON_RENSEIGNE

    # Le fichier mélange "Formation Professionnelle autre" et la coquille
    # "Formation profesionnelle autre" → une seule modalité.
    if clean.lower().startswith("formation prof"):
        return "Formation professionnelle (autre)"

    return clean[0].upper() + clean[1:] if clean else NON_RENSEIGNE


def statut_principal(value):
    """Statut d'activité en UNE modalité.

    Le champ est un ensemble (un même établissement peut être « construit et
    utilisé » ET « en construction » pour une extension). Pour un axe
    catégoriel il faut une modalité par établissement : on prend la plus
    avancée selon l'ordre d'usage réel.
    """

    parts = [_normalize_label(p) for p in _strip_braces(value)]
    parts = [p for p in parts if p != NON_RENSEIGNE]

    if not parts:
        return NON_RENSEIGNE

    for priorite in ("Construit et utilise", "En construction", "Inacheve", "Ferme"):
        for part in parts:
            if part.lower() == priorite.lower():
                return {
                    "construit et utilise": "Construit et utilisé",
                    "en construction": "En construction",
                    "inacheve": "Inachevé",
                    "ferme": "Fermé",
                }[priorite.lower()]

    return parts[0]


def clean_formations(df):
    """Normalise le fichier des établissements de formation technique."""

    out = df.copy()

    out["statut"] = out["activite_statut"].map(statut_principal)
    out["categorie"] = out["etablissement_categorie"].map(_normalize_label)
    out["foncier"] = out["terrain"].map(_normalize_label)
    out["region"] = out["region_nom_bdd"].map(_normalize_label)
    out["prefecture"] = out["prefecture_nom_bdd"].map(_normalize_label)

    # "Nsp" traîne dans une colonne d'années → numérique, hors-bornes écartées.
    annee = pd.to_numeric(out["etab_creation_date"], errors="coerce")
    out["annee_creation"] = annee.where(annee.between(1900, 2025))

    out["sport"] = out["terrain_sport"].map(
        lambda v: {"oui": "Oui", "non": "Non"}.get(str(v).strip().lower(), NON_RENSEIGNE)
    )

    # Statut foncier ramené à 4 familles : le champ brut mélange les casses
    # (« Domaine public de l'etat » / « de l'Etat ») et 12 libellés pour
    # 4 réalités.
    out["foncier_famille"] = out["terrain"].map(_famille_fonciere)

    # Assainissement : champ multi-valué comme le statut d'activité. On retient
    # l'équipement le plus abouti — c'est lui qui qualifie l'établissement.
    out["sanitaire"] = out["toilette_type"].map(_sanitaire_principal)

    # Nombre de jours d'ouverture par semaine (le champ liste les jours).
    out["jours_ouverture"] = out["etab_jour"].map(_nombre_de_jours)

    # `POINT (lon lat)` → deux colonnes numériques, pour la carte.
    coords = out["geometry"].str.extract(
        r"POINT\s*\(\s*(?P<lon>-?\d+\.?\d*)\s+(?P<lat>-?\d+\.?\d*)\s*\)"
    )
    out["lon"] = pd.to_numeric(coords["lon"], errors="coerce")
    out["lat"] = pd.to_numeric(coords["lat"], errors="coerce")

    return out


_ORDRE_SANITAIRE = ["WCs", "Latrines a eau", "Latrines seches", "Pissotieres", "Douches"]

_LIBELLE_SANITAIRE = {
    "wcs": "WC",
    "latrines a eau": "Latrines à eau",
    "latrines seches": "Latrines sèches",
    "pissotieres": "Pissotières",
    "douches": "Douches seules",
}


def _sanitaire_principal(value):
    """Équipement sanitaire le plus abouti déclaré par l'établissement."""

    parts = [p.strip().lower() for p in _strip_braces(value)]
    parts = [p for p in parts if p and p not in _MISSING]

    if not parts:
        return NON_RENSEIGNE

    for reference in _ORDRE_SANITAIRE:
        if reference.lower() in parts:
            return _LIBELLE_SANITAIRE[reference.lower()]

    return NON_RENSEIGNE


def _famille_fonciere(value):
    """12 libellés bruts → 4 familles de statut foncier."""

    if pd.isna(value):
        return NON_RENSEIGNE

    texte = str(value).strip().lower()

    if texte in _MISSING or texte == "ne sait pas":
        return NON_RENSEIGNE

    if texte.startswith("domaine public"):
        return "Domaine public"

    if texte.startswith("domaine prive") or texte.startswith("foncier national"):
        return "Domaine privé de l'État"

    if texte.startswith("prive"):
        return "Privé (individuel ou entreprise)"

    return NON_RENSEIGNE


def _nombre_de_jours(value):
    """Nombre de jours d'ouverture par semaine, depuis la liste des jours."""

    parts = [p.strip() for p in _strip_braces(value)]
    parts = [p for p in parts if p and p.lower() not in _MISSING]

    return len(parts) if parts else None


def clean_superieur(df):
    """Répartition des établissements du supérieur (type × statut × ville).

    Le fichier embarque ses propres totaux (`type == 'Total'`, `villes ==
    'TOTAL'`) : on les écarte pour ne pas double-compter, les agrégats sont
    recalculés côté analyse.
    """

    out = df.copy()
    out = out[(out["type"] != "Total") & (out["villes"] != "TOTAL")].copy()

    out["ville"] = out["villes"].str.strip().str.title()
    out["statut"] = out["statut"].replace({"Prive": "Privé"})
    out["valeur"] = pd.to_numeric(out["Value"], errors="coerce").fillna(0).astype(int)
    out["annee"] = pd.to_numeric(out["Date"], errors="coerce")

    return out[["ville", "type", "statut", "valeur", "annee"]]


def clean_indicateur(df):
    """Série Banque mondiale (`date`, `value`) — années sans mesure retirées."""

    out = df.copy()
    out["annee"] = pd.to_numeric(out["date"], errors="coerce")
    out["valeur"] = pd.to_numeric(out["value"], errors="coerce")

    return out.dropna(subset=["annee", "valeur"]).sort_values("annee")[["annee", "valeur"]]


def clean_budget(df):
    """Budgets (millions FCFA) en table large : une colonne par libellé."""

    out = df.copy()
    out["annee"] = pd.to_numeric(out["Date"], errors="coerce")
    out["valeur"] = pd.to_numeric(out["Value"], errors="coerce")

    wide = out.pivot_table(index="annee", columns="libellés", values="valeur")

    return wide.rename(columns={
        "BUDGET DE L'ENSEIGNEMENT SUPÉRIEUR VOTÉ": "es_vote",
        "BUDGET DE L'ENSEIGNEMENT SUPÉRIEUR EXÉCUTÉ": "es_execute",
        "BUDGET DU SECTEUR DE L'ÉDUCATION VOTÉ": "educ_vote",
        "BUDGET DU SECTEUR DE L'ÉDUCATION EXÉCUTÉ": "educ_execute",
        "BUDGET NATIONAL VOTÉ": "national_vote",
        "BUDGET NATIONAL EXÉCUTÉ": "national_execute",
        "SUBVENTION DE L'ETAT ALLOUÉE AUX ÉTABLISSEMENTS PRIVÉS D'ENSEIGNEMENT SUPÉRIEUR": "subvention_prive",
        "PRODUIT INTÉRIEUR BRUT (PIB)": "pib",
    }).reset_index()


# ─── Indicateurs clés du supérieur (DICES-TG) ────────────────────────────────

# Libellé du fichier → clé courte, libellé d'affichage et unité.
#
# L'unité est reprise ici parce que le fichier ne la donne pas toujours : elle
# manque pour le ratio étudiant/enseignant et pour le taux d'inscription des
# bacheliers. Elle est déduite de la nature de la mesure, pas devinée — un
# ratio d'encadrement s'exprime en étudiants par enseignant, un taux en %.
# Libellé du fichier → (clé courte, clé d'unité). Les intitulés affichés ne
# sont PAS ici : ils vivent dans `i18n/locales/superieur.json`, sous
# `ind_<cle>`. Ce module ne produit que des identifiants stables.
#
# L'unité est portée ici parce que le fichier ne la donne pas toujours : elle
# manque pour le ratio étudiant/enseignant et pour le taux d'inscription des
# bacheliers. Elle est déduite de la nature de la mesure, pas devinée — un
# ratio d'encadrement s'exprime en étudiants par enseignant, un taux en %.
INDICATEURS_SUP = {
    "Evolution des effectifs des étudiants inscrits":
        ("effectifs", "unite_etudiants"),
    "Rapport de féminité des étudiants":
        ("feminite", "unite_pourcent"),
    "Proportion de femmes":
        ("feminite_courte", "unite_pourcent"),
    "%d’étudiants dans les filières scientifiques et technologiques":
        ("scientifiques", "unite_pourcent"),
    "%de filles dans les filières scientifiques et technologiques":
        ("filles_scientifiques", "unite_pourcent"),
    "ratio étudiant/ enseignants dans les universités publiques":
        ("ratio_encadrement", "unite_ratio"),
    "Dépenses annuelles par étudiants":
        ("depense_fcfa", "unite_fcfa"),
    "Part du Budget alloué à l'enseignement (%)":
        ("part_education", "unite_pourcent"),
    "Proportion du Budget de l’enseignement supérieur dans le Budget National "
    "et par rapport au PIB":
        ("part_superieur_pib", "unite_pourcent"),
    "Nombre d'étudiant  pour 100000 hbts":
        ("densite_etudiants", "unite_etudiants"),
    "Nombre d'étudiant des universités publiques pour 100000 hbts":
        ("densite_publique", "unite_etudiants"),
    "Taux d’inscription immédiat des nouveaux bacheliers dans les UPT":
        ("inscription_bacheliers", "unite_pourcent"),
}


# « Proportion de femmes » et « Rapport de féminité des étudiants » donnent des
# valeurs IDENTIQUES sur 2015-2017 (42,6 / 44,6 / 45,7) : c'est le même
# indicateur publié deux fois. La série courte s'arrête en 2017, la longue va
# jusqu'en 2019. On retient la longue et l'on écarte le doublon des analyses,
# sans le supprimer du profil du fichier — la redondance est un fait sur la
# qualité de la publication.
DOUBLON_SUP = "feminite_courte"


def clean_indicateurs_sup(df):
    """Indicateurs clés du supérieur — format long, une ligne par mesure.

    Renvoie un cadre à colonnes `cle`, `libelle`, `unite`, `annee`, `valeur`.
    Le format long est conservé plutôt que pivoté : les douze séries n'ont ni
    la même période ni la même unité, et une table large les alignerait de
    force en fabriquant des trous là où il n'y a que des calendriers
    différents.
    """

    out = df.copy()
    out["annee"] = pd.to_numeric(out["Date"], errors="coerce")
    out["valeur"] = pd.to_numeric(out["Value"], errors="coerce")

    # Un libellé inconnu ne doit pas disparaître en silence : il garde son
    # intitulé d'origine et une clé dérivée, afin d'être visible si le fichier
    # gagne une série.
    def decrire(libelle):
        # Un libellé inconnu ne doit pas disparaître en silence : il garde un
        # identifiant dérivé de son intitulé, visible si le fichier gagne une
        # série. Son unité reste vide plutôt que devinée.
        return INDICATEURS_SUP.get(
            str(libelle).strip(),
            (str(libelle).strip().lower().replace(" ", "_"), ""),
        )

    decrit = out["indicateur"].map(decrire)
    out["cle"] = [d[0] for d in decrit]
    out["unite_cle"] = [d[1] for d in decrit]

    return (
        out.dropna(subset=["annee", "valeur"])
        .sort_values(["cle", "annee"])
        [["cle", "unite_cle", "annee", "valeur"]]
        .reset_index(drop=True)
    )


def serie_sup(indicateurs, cle):
    """Une série de DICES-TG, prête à tracer. Cadre vide si la clé est absente."""

    return indicateurs[indicateurs["cle"] == cle].reset_index(drop=True)
