![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-GPLv3-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

# PyNumStore

PyNumStore is an alternative platform that indexes and showcases Python scripts published on the official NumWorks website.

It allows users to discover, search, and share NumWorks Python scripts more easily while also providing tools to access and process script metadata.

## Features

### Website

PyNumStore provides a web interface that allows users to:

* Discover new creators and scripts
* Search for NumWorks Python scripts
* Browse scripts by creator
* Share and promote their own scripts

### Developer Tools

PyNumStore also provides tools that can:

* Parse the NumWorks website
* Retrieve the complete index of creators
* Retrieve the complete index of scripts
* Automatically update the local database

## Installation

### Requirements

* Python 3.10 or newer
* `venv` module

### Setup

```bash
git clone <repository-url>
cd pynumstore

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## Project Structure

```text
pynumstore/
├── css/              # Website stylesheets
├── data/             # Scripts and creators data
├── js/               # JavaScript files
├── python_scripts/   # Python backend and utility scripts
├── static/           # Website assets and logos
├── 404.html          # 404 error page
├── creator.html      # Creator page
├── forcreators.html  # Information page for creators
├── index.html        # Home page
├── script.html       # Script page
├── search.html       # Search page
└── requirements.txt  # Python dependencies
```

### Data Directory

The `data/` directory contains:

* `creators_index.json`: index of all creators
* `scripts_index.json`: index of all scripts

Each creator has its own directory, which contains one directory for each of their scripts.

Each script directory contains:

* `metadata.json`, which stores:

  * script name
  * creator name
  * creation date
  * description
  * file size
  * image path
  * tags
* the script thumbnail image

### JavaScript Directory

The `js/` directory contains:

* One JavaScript file for each HTML page
* `google_apps_script_api.js`, which handles communication with the project's Google Apps Script API

### Python Scripts Directory

The `python_scripts/` directory contains:

* `dbg.py`: scrapes and parses the NumWorks website
* `event_manager.py`: manages updates and scans
* `settings.json`: stores project settings and configuration data

## Contributing

Contributions are welcome! If you would like to improve PyNumStore, you can help in several ways:

* Report bugs or issues
* Suggest new features
* Improve documentation
* Submit pull requests with enhancements or fixes

### How to contribute

1. Fork the repository
2. Create a new branch for your changes:

   ```bash
   git checkout -b feature/my-feature
   ```
3. Make your modifications
4. Commit your changes:

   ```bash
   git commit -m "Add my feature"
   ```
5. Push your branch:

   ```bash
   git push origin feature/my-feature
   ```
6. Open a Pull Request

Please make sure your code follows the existing style and does not break existing functionality.

---

## Disclaimer

PyNumStore is an independent project and is **not affiliated with NumWorks**.

All trademarks, including "NumWorks", belong to their respective owners.

This project only indexes and displays publicly available scripts from the official NumWorks website for educational and informational purposes.

## Author

**gradient01**

Email: [gradient01.dev@gmail.com](mailto:gradient01.dev@gmail.com)

## License

PyNumStore is licensed under the GNU General Public License v3.0 (GPL-3.0).
