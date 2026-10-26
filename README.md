![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-GPLv3-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

**English** · [Français](README.fr.md)

# PyNumStore

PyNumStore is an alternative platform that indexes and showcases Python scripts published on the official NumWorks website.

It lets users discover, search and browse NumWorks Python scripts more easily, while an automated backend keeps the database up to date.

🌐 **Live site:** https://pynumstore.github.io/pynumstore

## Features

### Website

The website is fully static (HTML/CSS/JS), available in **English and French**, and lets users:

- Discover scripts on the home page (randomised selection)
- Search scripts with an advanced query syntax (see [Search syntax](#search-syntax)), sort results and filter them by date range and size
- Browse all scripts from a specific creator
- View script details: description, thumbnail, creation date, size and tags
- See global figures on the **Statistics** page (number of scripts and creators, average scripts per creator, share of scripts with a description, top 10 creators)
- Submit a NumWorks username to be added to the database (protected by Cloudflare Turnstile)

#### Search syntax

| Prefix | Searches in | Example |
|--------|-------------|---------|
| *(none)* | name, creator and description | `snake` |
| `@` | creator | `@gradient01` |
| `#` | tags | `#game` |
| `%` | script name | `%tetris` |
| `$` | description | `$physics` |

Wrap a value in double quotes for an exact match (e.g. `#"game"`). Several terms can be combined. Results are paginated (30 per page).

### Backend

The backend is a set of Python scripts that:

- Syncs the list of tracked creators with a **Google Sheets** spreadsheet
- Detects changed scripts with lightweight **SHA-256** hash checks (`curl_cffi`, Chrome impersonation)
- Only launches a headless browser (`playwright`) for scripts that are new or have changed, to scrape metadata and take a screenshot
- Stores everything in a **SQLite** database (`data/pynumstore.db`)
- Regenerates `data/version.json` (cache busting) and `sitemap.xml` after each update
- Runs a **daily protocol** and sends progress notifications through a **Telegram bot**

## Installation

### Requirements

- Python 3.10 or newer
- `venv` module
- Playwright browsers (`playwright install chromium`)
- `screen` (only for the daily protocol script)

### Setup

```bash
git clone https://github.com/pynumstore/pynumstore.git
cd pynumstore

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium

mkdir logs
```

> All Python commands must be run **from the repository root** (paths such as `data/pynumstore.db` and `python_scripts/credentials.json` are relative to it).

### Configuration

Create `python_scripts/tokens.py` (not versioned) with your credentials:

```python
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID   = "your_telegram_chat_id"
SHEET_ID           = "your_google_sheet_id"
```

Place your Google service account key at `python_scripts/credentials.json` (not versioned). The service account needs access to the spreadsheet; the first column of its first sheet is the list of creator usernames.

Copy the example settings file (not versioned once copied):

```bash
cp python_scripts/settings.example.json python_scripts/settings.json
```

`settings.json` stores the Telegram update offset.

## Usage

The updater is a single entry point, `python_scripts/updater.py`:

```bash
python python_scripts/updater.py [option]
```

| Command | Description |
|---------|-------------|
| *(no option)* | Standard update: detect changes, then update the flagged scripts |
| `--get-scripts-to-update` | Phase 1 only: sync creators/scripts and flag the scripts that changed |
| `--update-scripts` | Phase 2 only: fully re-scan every script flagged `to_update` |
| `--full-update` | Flag **all** scripts, then re-scan them (ignores hashes) |
| `--update-creators <name1> <name2> …` | Flag all scripts of the given creators, then re-scan them |
| `--daily-protocol` | Phase 1, then phase 2 only if something changed, with Telegram notifications |
| `--help` | Show the available options |

### Daily protocol

`daily-protocol.sh` is meant to be run every day at 12:00 by `cron`. It pulls the latest changes (`git-pull.sh`), then launches `updater.py --daily-protocol` in a detached `screen` session named `pynumstore_screen` (reattach with `screen -r pynumstore_screen`).

When the update is finished, a Telegram message asks you to review the logs and push the changes:

- `check-changes.sh` — activates the environment and optionally opens `logs/lupdater.log`
- `git-push.sh` — commits everything with a timestamped message and pushes

## How the update works

The backend uses a two-phase approach to minimise browser usage:

1. **Hash check** (fast, `curl_cffi`) — `get_scripts_to_update()`
   - Loads the creators list from Google Sheets; new creators are inserted, creators no longer listed are deleted (with their scripts and thumbnails)
   - For each creator, fetches the creator page and compares the list of scripts with the database (new scripts are inserted, removed scripts are deleted)
   - Computes a SHA-256 hash of each script (description + code) and compares it with the stored `body_hash`; scripts whose hash changed get `to_update = 1`
2. **Full scan** (slow, `playwright`) — `update_scripts()`
   - Opens each flagged script page in a headless Chromium (only `numworks.com` requests are allowed), extracts date, size, description (sanitised with `bleach`) and tags, and saves a screenshot of the canvas as thumbnail
   - Stores the new data and the new hash, and resets `to_update` to `0`
   - Writes a new `data/version.json` and regenerates `sitemap.xml`

Each network or parsing step is retried up to 3 times before the creator or script is skipped (or deleted when it is no longer found). Everything is logged to `logs/lupdater.log`.

## Project structure

```
pynumstore/
├── css/                          # Website stylesheets
├── data/
│   ├── pynumstore.db             # SQLite database (scripts + creators)
│   ├── version.json              # Database version tag (cache busting)
│   ├── i18n/
│   │   ├── en.json               # English translations
│   │   └── fr.json               # French translations
│   └── thumbnails/               # Script screenshot thumbnails
├── js/
│   ├── db.js                     # sql.js loader and query helpers (shared)
│   ├── utils.js                  # Shared UI utilities (card builder)
│   ├── i18n.js                   # Language detection, switching and translation helpers
│   ├── index.js                  # Home page logic
│   ├── search.js                 # Search page logic
│   ├── creator.js                # Creator page logic
│   ├── script.js                 # Script detail page logic
│   ├── statistics.js             # Statistics page logic
│   ├── forcreators.js            # Creator submission form logic
│   ├── 404.js, legal.js          # Small page scripts
│   └── google_apps_script_api.js # Apps Script API (server-side, not served)
├── python_scripts/
│   ├── updater.py                # Entry point: update orchestration and CLI
│   ├── utils.py                  # SQLite, Google Sheets, curl_cffi, Playwright, parsers, Telegram
│   ├── bleach_allowed.py         # Allowed HTML tags/attributes for sanitisation
│   ├── generate_sitemap.py       # Sitemap generator (reads from SQLite)
│   └── settings.example.json     # Settings template
├── static/                       # Favicons and app icons
├── daily-protocol.sh             # Daily update in a detached screen session (cron)
├── check-changes.sh              # Open the last update log
├── git-pull.sh                   # Pull the latest changes
├── git-push.sh                   # Commit and push all changes
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

## Database schema

All data is stored in `data/pynumstore.db` (SQLite).

```sql
CREATE TABLE creators (
    name TEXT PRIMARY KEY
);

CREATE TABLE scripts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    creator          TEXT NOT NULL REFERENCES creators(name),
    updated_at       TEXT,      -- creation date, YYYY-MM-DD
    size             INTEGER,   -- size in bytes
    thumbnail        TEXT,      -- path to the PNG screenshot, or "default_thumbnail"
    description      TEXT,      -- sanitised HTML (bleach), for display
    description_text TEXT,      -- plain text, for search
    body_hash        TEXT,      -- SHA-256 of the script description + code
    tags             TEXT,      -- comma-separated, lowercase tags
    to_update        INTEGER,   -- 1 = needs a full re-scan
    UNIQUE(creator, name)
);
```

## Frontend

The website is fully static and hosted on GitHub Pages. There is no server-side rendering.

All data is loaded from `data/pynumstore.db` via [sql.js](https://github.com/sql-js/sql.js): the whole SQLite database is fetched once and queried in the browser using WebAssembly. `data/version.json` is used for cache busting, so browsers always load the latest database after an update.

Script descriptions are rendered as sanitised HTML (cleaned by `bleach` on the backend). Multi-line `<code>` blocks are automatically styled as code boxes.

### Internationalisation

The interface is available in English and French. The language is detected on the first visit (French if the browser is set to French, English otherwise) and can be changed with the language button. The choice is remembered in a `pns_lang` cookie (one year). Translations live in `data/i18n/en.json` and `data/i18n/fr.json`, and elements are translated through `data-i18n` / `data-i18n-html` attributes (see `js/i18n.js`).

To add a string, add the same key to both JSON files and reference it from the HTML with `data-i18n="section.key"`.

### Creator submission form

The "For creators" page lets anyone ask for a NumWorks username to be tracked. The form is protected by [Cloudflare Turnstile](https://www.cloudflare.com/products/turnstile/) and posts to a Google Apps Script web app (`js/google_apps_script_api.js`) that:

1. Verifies the Turnstile token
2. Applies a short per-username cooldown
3. Validates the username format
4. Checks that the user exists on the NumWorks website
5. Appends the username to the `creators_index` sheet (checking for duplicates) — the same spreadsheet the backend reads, so this sheet must be the **first** one (the backend reads `sheet1`)

The script reads `TURNSTILE_SECRET_KEY` and `SHEET_ID` from the Apps Script **Script properties**.

## Privacy

PyNumStore has no accounts and collects no personal data. Visit statistics are measured with [Cloudflare Web Analytics](https://www.cloudflare.com/web-analytics/), and the only cookie is the `pns_lang` language preference. See `legal.html` for the full legal notice.

## Contributing

Contributions are welcome. You can help by:

- Reporting bugs or unexpected behaviour
- Suggesting new features
- Improving documentation or translations
- Submitting pull requests

### How to contribute

1. Fork the repository
2. Create a branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push and open a Pull Request

---

## Disclaimer

PyNumStore is an independent project and is **not affiliated with NumWorks**.

All trademarks, including "NumWorks", belong to their respective owners.

This project only indexes and displays publicly available scripts from the official NumWorks website for educational and informational purposes. If you are the author of a script and want it removed, contact the author below.

## Author

**gradient01** — gradient01.dev@gmail.com

## License

PyNumStore is licensed under the GNU General Public License v3.0 (GPL-3.0).
