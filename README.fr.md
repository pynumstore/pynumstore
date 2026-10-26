![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-GPLv3-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

[English](README.md) · **Français**

# PyNumStore

PyNumStore est une plateforme alternative qui indexe et met en valeur les scripts Python publiés sur le site officiel de NumWorks.

Elle permet de découvrir, rechercher et parcourir plus facilement les scripts Python NumWorks, grâce à un backend automatisé qui maintient la base de données à jour.

🌐 **Site en ligne :** https://pynumstore.github.io/pynumstore

## Fonctionnalités

### Site web

Le site est entièrement statique (HTML/CSS/JS), disponible en **français et en anglais**, et permet de :

- Découvrir des scripts sur la page d'accueil (sélection aléatoire)
- Rechercher des scripts avec une syntaxe avancée (voir [Syntaxe de recherche](#syntaxe-de-recherche)), trier les résultats et les filtrer par période et par taille
- Parcourir tous les scripts d'un créateur
- Consulter le détail d'un script : description, miniature, date de création, taille et tags
- Voir des chiffres globaux sur la page **Statistiques** (nombre de scripts et de créateurs, moyenne de scripts par créateur, part de scripts avec description, top 10 des créateurs)
- Proposer un nom d'utilisateur NumWorks à ajouter à la base (formulaire protégé par Cloudflare Turnstile)

#### Syntaxe de recherche

| Préfixe | Recherche dans | Exemple |
|---------|----------------|---------|
| *(aucun)* | nom, créateur et description | `snake` |
| `@` | créateur | `@gradient01` |
| `#` | tags | `#game` |
| `%` | nom du script | `%tetris` |
| `$` | description | `$physics` |

Entoure une valeur de guillemets doubles pour une correspondance exacte (ex. `#"game"`). Plusieurs termes peuvent être combinés. Les résultats sont paginés (30 par page).

### Backend

Le backend est un ensemble de scripts Python qui :

- Synchronise la liste des créateurs suivis avec une feuille **Google Sheets**
- Détecte les scripts modifiés grâce à des vérifications légères par hash **SHA-256** (`curl_cffi`, imitation de Chrome)
- Ne lance un navigateur headless (`playwright`) que pour les scripts nouveaux ou modifiés, afin de récupérer les métadonnées et de prendre une capture d'écran
- Stocke tout dans une base **SQLite** (`data/pynumstore.db`)
- Régénère `data/version.json` (cache busting) et `sitemap.xml` après chaque mise à jour
- Exécute un **protocole quotidien** et envoie des notifications via un **bot Telegram**

## Installation

### Prérequis

- Python 3.10 ou supérieur
- Module `venv`
- Navigateurs Playwright (`playwright install chromium`)
- `screen` (uniquement pour le script du protocole quotidien)

### Mise en place

```bash
git clone https://github.com/pynumstore/pynumstore.git
cd pynumstore

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

> Toutes les commandes Python doivent être lancées **depuis la racine du dépôt** (les chemins comme `data/pynumstore.db` et `python_scripts/credentials.json` sont relatifs à celle-ci).

### Configuration

Crée `python_scripts/tokens.py` (non versionné) avec tes identifiants :

```python
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID   = "your_telegram_chat_id"
SHEET_ID           = "your_google_sheet_id"
```

Place la clé de ton compte de service Google dans `python_scripts/credentials.json` (non versionné). Le compte de service doit avoir accès à la feuille ; la première colonne de sa première feuille contient la liste des noms d'utilisateur des créateurs.

Copie le fichier de paramètres d'exemple (non versionné une fois copié) :

```bash
cp python_scripts/settings.example.json python_scripts/settings.json
```

`settings.json` conserve l'offset des mises à jour Telegram.

## Utilisation

Le point d'entrée unique est `python_scripts/updater.py` :

```bash
python python_scripts/updater.py [option]
```

| Commande | Description |
|----------|-------------|
| *(aucune option)* | Mise à jour standard : détecte les changements, puis met à jour les scripts signalés |
| `--get-scripts-to-update` | Phase 1 uniquement : synchronise créateurs/scripts et signale les scripts modifiés |
| `--update-scripts` | Phase 2 uniquement : rescanne complètement les scripts marqués `to_update` |
| `--full-update` | Marque **tous** les scripts puis les rescanne (ignore les hashes) |
| `--update-creators <nom1> <nom2> …` | Marque tous les scripts des créateurs indiqués puis les rescanne |
| `--daily-protocol` | Phase 1, puis phase 2 seulement s'il y a des changements, avec notifications Telegram |
| `--help` | Affiche les options disponibles |

### Protocole quotidien

`daily-protocol.sh` est prévu pour être lancé chaque jour à 12h00 par `cron`. Il récupère les derniers changements (`git-pull.sh`), puis lance `updater.py --daily-protocol` dans une session `screen` détachée nommée `pynumstore_screen` (pour s'y rattacher : `screen -r pynumstore_screen`).

Une fois la mise à jour terminée, un message Telegram te demande de vérifier les logs et de pousser les changements :

- `check-changes.sh` — active l'environnement et ouvre au choix `logs/lupdater.log`
- `git-push.sh` — commit de tout avec un message horodaté, puis push

## Fonctionnement de la mise à jour

Le backend procède en deux phases pour limiter l'usage du navigateur :

1. **Vérification des hashes** (rapide, `curl_cffi`) — `get_scripts_to_update()`
   - Charge la liste des créateurs depuis Google Sheets ; les nouveaux créateurs sont insérés, ceux qui ne figurent plus dans la liste sont supprimés (avec leurs scripts et miniatures)
   - Pour chaque créateur, récupère sa page et compare la liste des scripts avec la base (les nouveaux scripts sont insérés, les scripts disparus sont supprimés)
   - Calcule un hash SHA-256 de chaque script (description + code) et le compare au `body_hash` stocké ; les scripts dont le hash a changé passent à `to_update = 1`
2. **Scan complet** (lent, `playwright`) — `update_scripts()`
   - Ouvre chaque script signalé dans un Chromium headless (seules les requêtes vers `numworks.com` sont autorisées), extrait la date, la taille, la description (nettoyée avec `bleach`) et les tags, et enregistre une capture du canvas comme miniature
   - Enregistre les nouvelles données et le nouveau hash, puis remet `to_update` à `0`
   - Écrit un nouveau `data/version.json` et régénère `sitemap.xml`

Chaque étape réseau ou d'analyse est retentée jusqu'à 3 fois avant que le créateur ou le script soit ignoré (ou supprimé s'il est introuvable). Tout est consigné dans `logs/lupdater.log`.

## Structure du projet

```
pynumstore/
├── css/                          # Feuilles de style du site
├── data/
│   ├── pynumstore.db             # Base SQLite (scripts + créateurs)
│   ├── version.json              # Tag de version de la base (cache busting)
│   ├── i18n/
│   │   ├── en.json               # Traductions anglaises
│   │   └── fr.json               # Traductions françaises
│   └── thumbnails/               # Miniatures (captures d'écran des scripts)
├── js/
│   ├── db.js                     # Chargeur sql.js et helpers de requêtes (partagé)
│   ├── utils.js                  # Utilitaires d'interface partagés (construction des cartes)
│   ├── i18n.js                   # Détection, changement de langue et helpers de traduction
│   ├── index.js                  # Logique de la page d'accueil
│   ├── search.js                 # Logique de la page de recherche
│   ├── creator.js                # Logique de la page créateur
│   ├── script.js                 # Logique de la page de détail d'un script
│   ├── statistics.js             # Logique de la page statistiques
│   ├── forcreators.js            # Logique du formulaire de soumission
│   ├── 404.js, legal.js          # Petits scripts de pages
│   └── google_apps_script_api.js # API Apps Script (côté serveur, non servie)
├── python_scripts/
│   ├── updater.py                # Point d'entrée : orchestration des mises à jour et CLI
│   ├── utils.py                  # SQLite, Google Sheets, curl_cffi, Playwright, parseurs, Telegram
│   ├── bleach_allowed.py         # Balises/attributs HTML autorisés pour le nettoyage
│   ├── generate_sitemap.py       # Générateur de sitemap (lit SQLite)
│   └── settings.example.json     # Modèle de paramètres
├── static/                       # Favicons et icônes d'application
├── daily-protocol.sh             # Mise à jour quotidienne dans une session screen (cron)
├── check-changes.sh              # Ouvre le log de la dernière mise à jour
├── git-pull.sh                   # Récupère les derniers changements
├── git-push.sh                   # Commit et push de tous les changements
├── 404.html
├── creator.html
├── forcreators.html
├── index.html
├── legal.html
├── script.html
├── search.html
├── statistics.html
├── robots.txt
├── sitemap.xml
└── requirements.txt
```

## Schéma de la base de données

Toutes les données sont stockées dans `data/pynumstore.db` (SQLite).

```sql
CREATE TABLE creators (
    name TEXT PRIMARY KEY
);

CREATE TABLE scripts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    creator          TEXT NOT NULL REFERENCES creators(name),
    updated_at       TEXT,      -- date de création, AAAA-MM-JJ
    size             INTEGER,   -- taille en octets
    thumbnail        TEXT,      -- chemin de la capture PNG, ou "default_thumbnail"
    description      TEXT,      -- HTML nettoyé (bleach), pour l'affichage
    description_text TEXT,      -- texte brut, pour la recherche
    body_hash        TEXT,      -- SHA-256 de la description + du code du script
    tags             TEXT,      -- tags en minuscules, séparés par des virgules
    to_update        INTEGER,   -- 1 = nécessite un rescan complet
    UNIQUE(creator, name)
);
```

## Frontend

Le site est entièrement statique et hébergé sur GitHub Pages. Il n'y a aucun rendu côté serveur.

Toutes les données sont chargées depuis `data/pynumstore.db` via [sql.js](https://github.com/sql-js/sql.js) : la base SQLite complète est téléchargée une fois puis interrogée dans le navigateur grâce à WebAssembly. `data/version.json` sert au cache busting, pour que les navigateurs chargent toujours la dernière base après une mise à jour.

Les descriptions des scripts sont affichées en HTML nettoyé (traité par `bleach` côté backend). Les blocs `<code>` multilignes sont automatiquement stylisés comme des boîtes de code.

### Internationalisation

L'interface est disponible en français et en anglais. La langue est détectée à la première visite (français si le navigateur est en français, anglais sinon) et peut être changée avec le bouton de langue. Le choix est mémorisé dans un cookie `pns_lang` (un an). Les traductions se trouvent dans `data/i18n/en.json` et `data/i18n/fr.json`, et les éléments sont traduits via les attributs `data-i18n` / `data-i18n-html` (voir `js/i18n.js`).

Pour ajouter un texte, ajoute la même clé dans les deux fichiers JSON et référence-la dans le HTML avec `data-i18n="section.cle"`.

### Formulaire de soumission des créateurs

La page « Pour les créateurs » permet à n'importe qui de demander le suivi d'un nom d'utilisateur NumWorks. Le formulaire est protégé par [Cloudflare Turnstile](https://www.cloudflare.com/products/turnstile/) et envoie sa requête à une application web Google Apps Script (`js/google_apps_script_api.js`) qui :

1. Vérifie le jeton Turnstile
2. Applique un court délai de blocage par nom d'utilisateur
3. Valide le format du nom d'utilisateur
4. Vérifie que l'utilisateur existe sur le site de NumWorks
5. Ajoute le nom à la feuille `creators_index` (en vérifiant les doublons) — la même feuille de calcul que lit le backend, donc cette feuille doit être la **première** (le backend lit `sheet1`)

Le script lit `TURNSTILE_SECRET_KEY` et `SHEET_ID` dans les **propriétés du script** Apps Script.

## Confidentialité

PyNumStore n'a pas de comptes et ne collecte aucune donnée personnelle. Les statistiques de visite sont mesurées avec [Cloudflare Web Analytics](https://www.cloudflare.com/web-analytics/), et le seul cookie est la préférence de langue `pns_lang`. Voir `legal.html` pour les mentions légales complètes.

## Contribuer

Les contributions sont les bienvenues. Tu peux aider en :

- Signalant des bugs ou des comportements inattendus
- Proposant de nouvelles fonctionnalités
- Améliorant la documentation ou les traductions
- Soumettant des pull requests

### Comment contribuer

1. Fork le dépôt
2. Crée une branche : `git checkout -b feature/ma-fonctionnalite`
3. Commit tes changements : `git commit -m "Add my feature"`
4. Push et ouvre une Pull Request

---

## Avertissement

PyNumStore est un projet indépendant, **non affilié à NumWorks**.

Toutes les marques, y compris « NumWorks », appartiennent à leurs propriétaires respectifs.

Ce projet se contente d'indexer et d'afficher des scripts publics du site officiel de NumWorks, à des fins éducatives et informatives. Si tu es l'auteur d'un script et souhaites son retrait, contacte l'auteur du projet ci-dessous.

## Auteur

**gradient01** — gradient01.dev@gmail.com

## Licence

PyNumStore est distribué sous licence GNU General Public License v3.0 (GPL-3.0).
