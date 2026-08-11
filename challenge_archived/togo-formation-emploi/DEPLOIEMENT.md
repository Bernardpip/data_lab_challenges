# Déploiement en ligne

**En production :** https://togo-dashboard-production.up.railway.app
**Cible :** `tg-datalab-education-challenge2.bernardpip.com`

| Élément | Valeur |
|---|---|
| Dépôt | `Bernardpip/togo-formation-emploi` (privé) |
| Hébergeur | Railway — projet `togo-formation-emploi`, service `togo-dashboard` |
| DNS | Cloudflare, zone `bernardpip.com` |

---

## Pourquoi pas Vercel

Vercel exécute des **fonctions serverless** : sans état, de durée bornée,
réveillées à chaque requête. Streamlit a besoin de l'inverse :

| Streamlit exige | Vercel fournit |
|---|---|
| Un processus Tornado **permanent** | Une fonction réveillée par requête |
| Un **WebSocket** ouvert par onglet | Requête / réponse HTTP uniquement |
| Un **état de session** côté serveur | Aucun état entre deux appels |
| Un **cache en mémoire** (`@st.cache_data`) | Mémoire perdue à chaque invocation |

Ce n'est pas un réglage à trouver : les deux modèles sont incompatibles. Vercel
reste parfait pour `bernardpip.com` lui-même — seul le tableau de bord doit
vivre ailleurs.

**Railway** exécute un conteneur : le processus reste vivant, le WebSocket tient,
et il n'y a **pas de mise en veille** — un correcteur qui ouvre le lien n'attend
pas le réveil du service. `render.yaml` est conservé à la racine comme
solution de repli : Render fonctionne aussi, au prix d'une veille après
15 minutes d'inactivité sur son offre gratuite.

---

## 1 · Le dépôt

```bash
git add -A
git commit -m "…"
git push
```

`.gitignore` écarte `.venv/`, `__pycache__/`, `.DS_Store` et le `.zip`, qui se
régénère depuis le dépôt (`git archive`). **Les 8 CSV sont versionnés** — 156 Ko,
publics : l'application doit démarrer sans dépendre du réseau.

---

## 2 · Le service Railway

Déjà créé. Pour redéployer depuis la machine locale :

```bash
railway up --service togo-dashboard
```

`railway.toml` porte toute la configuration : Railway le lit et ne demande rien.

| Réglage | Valeur | Pourquoi |
|---|---|---|
| Démarrage | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0` | `$PORT` est imposé par Railway et change à chaque démarrage ; `0.0.0.0` rend le conteneur joignable de l'extérieur |
| Sonde | `/_stcore/health` | Un déploiement raté ne remplace jamais un déploiement qui marche |
| Python | 3.11.9 | `runtime.txt` et `.python-version` — toutes les roues épinglées existent |

**Une variable à ajouter** dans Railway → Variables :

| Clé | Valeur | Pourquoi |
|---|---|---|
| `STREAMLIT_CLIENT_SHOW_ERROR_DETAILS` | `false` | Une trace d'exception n'aide pas un visiteur et expose la structure du code |

### Redéploiement automatique au push

Le déploiement actuel a été fait depuis la machine (`railway up`). Pour que
chaque `git push` redéclenche une construction, lier le dépôt dans
**Railway → Settings → Source → Connect Repo**. Cette étape passe par
l'interface web.

---

## 3 · Le sous-domaine

Le domaine est déjà déclaré côté Railway. **Deux enregistrements** sont à créer
dans Cloudflare → DNS → Add record.

### Enregistrement 1 — le trafic

| Champ | Valeur |
|---|---|
| Type | `CNAME` |
| Name | `tg-datalab-education-challenge2` |
| Target | `h236cld4.up.railway.app` |
| Proxy status | **DNS only** (nuage gris) |
| TTL | Auto |

### Enregistrement 2 — la preuve de propriété

| Champ | Valeur |
|---|---|
| Type | `TXT` |
| Name | `_railway-verify.tg-datalab-education-challenge2` |
| Content | `railway-verify=cbc5abb4ff41e7a9b0b199c36e1629110a635bb5b2343a7ad5dfa4a73443f52c` |
| TTL | Auto |

Sans le TXT, Railway ne valide pas le domaine et n'émettra jamais son
certificat. Il peut être supprimé une fois la validation passée.

> **La cible du CNAME est propre à ce domaine.** Railway génère un sous-domaine
> dédié (`h236cld4.up.railway.app`), différent de l'URL publique du service
> (`togo-dashboard-production.up.railway.app`). Pointer sur cette dernière ne
> fonctionnerait pas.

### Le nuage gris d'abord, l'orange ensuite

Tant que Railway n'a pas émis son certificat, le CNAME doit rester en **DNS
only** : proxifié, Cloudflare masque la cible et la validation échoue.

Une fois le certificat émis, le nuage orange peut être activé — le mode SSL doit
alors être **Full (strict)**, jamais *Flexible* : en Flexible, Cloudflare
appellerait Railway en HTTP et Streamlit bouclerait en redirections.

### Pourquoi un seul niveau de sous-domaine

Le nom retenu — `tg-datalab-education-challenge2` — n'a **qu'un seul niveau**,
avec des tirets là où l'on aurait pu mettre des points. Ce n'est pas cosmétique :
le certificat Universal SSL de Cloudflare couvre `*.bernardpip.com`, c'est-à-dire
**un seul niveau**. La documentation Cloudflare est explicite :

> Un certificat pour `*.example.com` couvre `www.example.com` et
> `api.example.com` mais **pas** `api.staging.example.com`.

`tg.datalab.education.challenge2.bernardpip.com` aurait donc exigé l'add-on
**Advanced Certificate Manager** (10 $/mois) pour être proxifiable, ou serait
resté bloqué en DNS only. Avec des tirets, tout fonctionne sur l'offre gratuite,
proxy compris.

---

## 4 · Vérifier

```bash
# Le DNS pointe-t-il sur Railway ?
dig +short tg-datalab-education-challenge2.bernardpip.com CNAME

# La preuve de propriété est-elle en place ?
dig +short _railway-verify.tg-datalab-education-challenge2.bernardpip.com TXT

# Où en est le certificat, côté Railway ?
railway domain status fc53dbec-f2ec-467a-8948-1ca329379df1

# Le service répond-il ?
curl -s https://tg-datalab-education-challenge2.bernardpip.com/_stcore/health
```

Puis, dans le navigateur, ouvrir une vue avec carte —
`?s=technique&t=carto` — et **actionner un filtre**. C'est le seul test qui
compte : si le décompte change, le WebSocket passe et toute la chaîne
fonctionne. Sans lui, la page s'affiche mais se fige.

---

## Récapitulatif de la chaîne

```
   Visiteur
      │  https://tg-datalab-education-challenge2.bernardpip.com
      ▼
   Cloudflare  ──── DNS (+ proxy une fois le certificat émis)
      │  CNAME → h236cld4.up.railway.app
      ▼
   Railway  ──── conteneur permanent, aucune mise en veille
      │  streamlit run app.py --server.port $PORT
      ▼
   Tornado :$PORT  ──── WebSocket ouvert par onglet
```
