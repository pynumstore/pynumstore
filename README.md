![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-GPLv3-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

# PyNumStore

PyNumStore is an alternative platform that indexes and showcases Python scripts published on the official NumWorks website.

It allows users to discover, search, and browse NumWorks Python scripts more easily, while providing an automated backend that keeps the database up to date.

## Features

### Website

PyNumStore provides a web interface that allows users to:

* Discover new scripts on the home page (randomized selection)
* Search for scripts by name, creator or description
* Browse all scripts from a specific creator
* View script details: description, thumbnail, creation date, size and tags
* Submit their username to be added to the database

### Backend

The backend is a Python application that:

* Scrapes the NumWorks website using `curl_cffi` (lightweight hash checks) and `playwright` (full scans with screenshots)
* Detects changes efficiently using SHA-256 hashes — Playwright is only launched for scripts that have actually changed
* Stores all data in a SQLite database (`data/pynumstore.db`)
* Syncs the list of tracked creators with a Google Sheets spreadsheet
* Sends update reports and accepts commands via a Telegram bot

## Installation

### Requirements

* Python 3.10 or newer
* `venv` module
* Playwright browsers (`playwright install chromium`)

### Setup

```bash
git clone <repository-url>
cd pynumstore

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### Configuration

Create `python_scripts/tokens.py` (not versioned) with your credentials:

```python
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID   = "your_telegram_chat_id"
SHEET_ID           = "your_google_sheet_id"
```

Place your Google service account key at `python_scripts/credentials.json` (not versioned).

Copy the example settings file:

```bash
cp python_scripts/settings.example.json python_scripts/settings.json
```

## Project Structure

```text
pynumstore/
├── css/                        # Website stylesheets
├── data/
│   ├── pynumstore.db           # SQLite database (scripts + creators)
│   └── thumbnails/             # Script screenshot thumbnails
├── js/
│   ├── db.js                   # sql.js loader and query helpers (shared)
│   ├── utils.js                # Shared UI utilities (card builder)
│   ├── index.js                # Home page logic
│   ├── search.js               # Search page logic
│   ├── creator.js              # Creator page logic
│   ├── script.js               # Script detail page logic
│   ├── forcreators.js          # Creator submission form logic
│   ├── google_apps_script_api.js  # Apps Script API (server-side, not served)
│   └── analytics.js            # Google Analytics initialisation
├── python_scripts/
│   ├── scanner.py              # Scraping logic (curl_cffi + Playwright)
│   ├── saver.py                # Database read/write operations
│   ├── updater.py              # Update orchestration (3 modes)
│   ├── reporter.py             # Telegram report generation
│   ├── telegram_bot.py         # Telegram bot (messages + file sending)
│   ├── event_manager.py        # Main loop (scheduler + command handler)
│   ├── bleach_allowed.py       # Allowed HTML tags/attributes for sanitisation
│   ├── generate_sitemap.py     # Sitemap generator (reads from SQLite)
│   └── settings.example.json  # Settings template
├── static/                     # Favicons and app icons
├── 404.html
├── creator.html
├── forcreators.html
├── index.html
├── robots.txt
├── script.html
├── search.html
├── sitemap.xml
└── requirements.txt
```

## Database Schema

All data is stored in `data/pynumstore.db` (SQLite).

```sql
CREATE TABLE creators (
    name      TEXT PRIMARY KEY,
    body_hash TEXT              -- SHA-256 of the creator page body
);

CREATE TABLE scripts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    creator          TEXT NOT NULL REFERENCES creators(name),
    created_at       TEXT,
    size             TEXT,
    thumbnail        TEXT,      -- path to the PNG screenshot
    description      TEXT,      -- sanitised HTML (bleach), for display
    description_text TEXT,      -- plain text, for search
    body_hash        TEXT,      -- SHA-256 of the script page body
    tags             TEXT,      -- comma-separated tags extracted from description
    UNIQUE(creator, name)
);
```

## Update System

The backend uses a two-phase approach to minimise Playwright usage:

1. **Hash check** (fast, `curl_cffi`) — fetches each creator page and compares the SHA-256 hash of the body with the stored value. Only creators whose hash has changed proceed to the next phase.
2. **Full scan** (slow, `playwright`) — navigates to each changed script page, takes a screenshot, extracts metadata and description.

### Update Modes

| Command | Description |
|---|---|
| `/update` | Standard update: checks all creator hashes, full scan only for changed scripts |
| `/full_update` | Full scan of all scripts for all creators (ignores hashes) |
| `/creator_update <name1> <name2>` | Full scan of specific creators only |

### Telegram Commands

| Command | Description |
|---|---|
| `/update` | Run a standard update |
| `/full_update` | Run a full update |
| `/creator_update <names>` | Update specific creators |
| `/status` | Check if an update is running |
| `/git_status` | Show `git status` output |
| `/add` | Stage all changes (`git add -A`) |
| `/push` | Stage, commit and push all changes |
| `/reset_soft` | Soft reset to previous commit |
| `/reset_hard` | Hard reset to previous commit |
| `/push_force` | Force push to remote |

## Frontend

The website is fully static (HTML/CSS/JS) and hosted on GitHub Pages. There is no server-side rendering.

All data is loaded from `data/pynumstore.db` via [sql.js](https://github.com/sql-js/sql.js) — the entire SQLite database is fetched once and queried in-browser using WebAssembly. Search uses SQL `LIKE` queries across name, creator and description.

Script descriptions are rendered as sanitised HTML (processed by `bleach` on the backend). Multi-line `<code>` blocks are automatically styled as code boxes.

## Roadmap

The following features are planned for future releases.

### Legal notices

A legal notices page will be added to the website, covering the terms of use, data sources, disclaimer regarding the relationship with NumWorks, and any other legal information required.

### Creation date parsing

Currently, script creation dates are stored as raw text scraped from NumWorks (e.g. `"October 16, 2021"`). A future update will parse these into a standardised ISO 8601 format (`2021-10-16`), enabling chronological sorting and date range filtering in search.

### Statistics page

A dedicated page will display live statistics computed directly from the SQLite database, including the total number of indexed scripts and creators, the average number of scripts per creator, the most prolific creator, and the proportion of scripts that have a description. The page will feature animated counters.

### Advanced search

The search page will support a prefix-based syntax for fine-grained queries:

| Prefix | Searches in | Example |
|---|---|---|
| `@` | Creator name | `@gradient01` |
| `#` | Tags | `#game` |
| `%` | Script name | `%maze_generator` |
| `$` | Description | `$fun` |

Prefixes can be combined in a single query. Without a prefix, the search applies to all fields simultaneously.

## Contributing

Contributions are welcome. You can help by:

* Reporting bugs or unexpected behaviour
* Suggesting new features
* Improving documentation
* Submitting pull requests

### How to contribute

1. Fork the repository
2. Create a branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push and open a Pull Request

---

## Disclaimer

PyNumStore is an independent project and is **not affiliated with NumWorks**.

All trademarks, including "NumWorks", belong to their respective owners.

This project only indexes and displays publicly available scripts from the official NumWorks website for educational and informational purposes.

## Author

**gradient01** — [gradient01.dev@gmail.com](mailto:gradient01.dev@gmail.com)

## License

PyNumStore is licensed under the GNU General Public License v3.0 (GPL-3.0).
