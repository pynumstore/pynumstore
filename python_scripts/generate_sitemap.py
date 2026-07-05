from xml.etree.ElementTree import Element, SubElement, tostring
from urllib.parse import quote
from datetime import date
import sqlite3
import os

BASE_URL = "https://pynumstore.github.io/pynumstore"
DB_PATH  = "data/pynumstore.db"


def generate_sitemap():

    today  = date.today().isoformat()
    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # ── Pages statiques ───────────────────────────────────────────────────
    for page, freq, priority in [
        ("index.html",       "daily",   "0.9"),
        ("search.html",      "daily",   "0.9"),
        ("forcreators.html", "monthly", "0.6"),
    ]:
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text        = f"{BASE_URL}/{page}"
        SubElement(url, "lastmod").text    = today
        SubElement(url, "changefreq").text = freq
        SubElement(url, "priority").text   = priority

    if not os.path.exists(DB_PATH):
        print(f"Warning: {DB_PATH} not found — skipping creator and script URLs.")
        _write(urlset)
        return

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    creators = con.execute("SELECT name FROM creators ORDER BY name").fetchall()
    for row in creators:
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text        = f"{BASE_URL}/creator.html?name={quote(row['name'])}"
        SubElement(url, "lastmod").text    = today
        SubElement(url, "changefreq").text = "weekly"
        SubElement(url, "priority").text   = "0.7"

    scripts = con.execute("SELECT creator, name FROM scripts ORDER BY creator, name").fetchall()
    for row in scripts:
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = (
            f"{BASE_URL}/script.html"
            f"?creator={quote(row['creator'])}"
            f"&name={quote(row['name'])}"
        )
        SubElement(url, "lastmod").text    = today
        SubElement(url, "changefreq").text = "monthly"
        SubElement(url, "priority").text   = "0.5"

    con.close()

    _write(urlset)
    print(f"Sitemap generated: {3 + len(creators) + len(scripts)} URLs "
          f"({len(creators)} creators, {len(scripts)} scripts)")


def _write(urlset):
    xml_body = tostring(urlset, encoding="unicode")
    xml_str  = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_body

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)

if __name__ == "__main__":
    generate_sitemap()