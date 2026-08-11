# outils/ — scaffold, vendorisation, diagnostic

Trois scripts, tous sans dépendance tierce : ils doivent tourner sur un poste
où rien n'est encore installé.

| Script | Quand |
|---|---|
| `nouveau_defi.py` | au démarrage d'un défi |
| `vendoriser.py` | avant chaque déploiement, et après chaque correctif du socle |
| `verifier_socle.py` | après toute modification du socle |

## `nouveau_defi.py`

```bash
python3 outils/nouveau_defi.py ../togo-eau-potable \
    --titre "Accès à l'eau potable au Togo" \
    --titre-en "Access to drinking water in Togo" \
    --defi "Data Challenge Environnement · Défi 1"
```

Copie `gabarit/`, remplace les jetons `{{...}}`, rappelle les trois gestes
suivants. Il n'installe rien, ne crée pas de dépôt git, ne télécharge aucune
donnée : un script qui enchaîne tout cela masque l'endroit exact où ça casse.

Un jeton sans valeur est **laissé en place** plutôt que vidé — `{{DEFI}}`
visible à l'écran se remarque et se corrige, une chaîne vide non.

## `vendoriser.py`

```bash
python3 outils/vendoriser.py ../togo-eau-potable
```

Copie `socle/` à côté d'`app.py`. Indispensable dans deux situations : le
**déploiement** (Railway ne clone que le dépôt du défi, un chemin relatif vers
un dossier voisin n'y existe pas) et l'**archive livrable** (un jury qui
décompresse doit pouvoir lancer `streamlit run app.py`).

La copie porte un fichier `socle/VENDORISE` daté. Sans lui, personne ne sait
si le socle déployé date d'avant ou d'après le dernier correctif — et
`verifier.py` d'un défi annonce laquelle des deux formes est active, la copie
locale l'emportant toujours sur le paquet installé.

## `verifier_socle.py`

```bash
python3 outils/verifier_socle.py
```

Remplace les modules tiers absents par des doubles inertes, puis contrôle :
les 28 modules et leur graphe d'imports, ce que les `__all__` annoncent, la
complétude fr/en des textes du socle, l'absence de libellé en dur, l'absence
de tout module métier ou fichier de données.

Ce qu'il ne prouve pas : que Plotly dessine, que Streamlit se peint. Cela ne
se vérifie qu'en lançant un défi — et, en ligne, qu'en actionnant un filtre.
