# Déploiement — Accès à l'eau potable au Togo

## Pourquoi Railway, et pas Vercel

Streamlit exige un **processus permanent** et un **WebSocket** : chaque clic
rejoue le script côté serveur et renvoie le résultat sur une connexion
ouverte. Une plateforme de fonctions éphémères sert la première page puis
laisse l'interface morte — les filtres ne répondent plus.

Railway exécute un conteneur : le processus reste vivant, le WebSocket tient,
et le cache `@st.cache_data` survit d'une visite à l'autre.

## Avant tout déploiement : vendoriser le socle

Le socle est installé en paquet pendant le développement. Railway ne clone que
**ce dépôt** — un chemin relatif vers un dossier voisin n'y existe pas, et le
build échouerait à l'installation.

```bash
python3 ../monorepo_folder/outils/vendoriser.py .
git add socle && git commit -m "Socle vendorisé"
```

La copie atterrit à côté d'`app.py`, donc importable sans réglage. Elle porte
un fichier `socle/VENDORISE` qui dit sa version et sa date : sans lui,
personne ne sait si le socle déployé date d'avant ou d'après le dernier
correctif. **À refaire après chaque correctif du socle**, sinon la production
reste sur l'ancienne version sans que rien ne le signale.

## Mise en ligne

1. pousser le dépôt sur GitHub ;
2. Railway → *New Project* → *Deploy from GitHub repo* ;
3. rien à configurer : `railway.toml` porte la commande de démarrage, le
   healthcheck et la politique de redémarrage.

Le port n'est **pas** figé dans `.streamlit/config.toml` : Railway l'impose
par `$PORT` et le change à chaque démarrage. Il est passé en ligne de commande.
L'adresse `0.0.0.0` est indispensable — sur `127.0.0.1`, le conteneur ne serait
joignable que depuis lui-même.

## Réglages de production

Dans les variables Railway :

```
STREAMLIT_ENV = production
```

Ce qui coupe les avertissements de clés i18n manquantes, qui pollueraient les
journaux du conteneur à chaque rerun.

Passer aussi `showErrorDetails` à `false` : en ligne, une trace d'exception
affichée au visiteur ne l'aide pas et expose la structure du code. En local
elle reste précieuse, d'où le réglage à `true` dans le fichier versionné.

## Domaine

Un sous-domaine à **un seul niveau** (`eau.exemple.tg`, pas
`eau.defis.exemple.tg`) : le certificat Universal SSL de Cloudflare ne couvre
qu'un niveau, et un sous-domaine plus profond servirait un certificat invalide.

## Le seul test qui compte

Ouvrir l'URL déployée et **actionner un filtre**. La page se charge même quand
le WebSocket ne s'établit pas ; seul un filtre qui met à jour un graphe prouve
que la connexion tient.
