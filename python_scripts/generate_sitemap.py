from xml.etree.ElementTree import Element, SubElement, tostring, indent
from urllib.parse import quote
import json
import os
from datetime import date

BASE_URL = "https://pynumstore.github.io/pynumstore"


def generate_sitemap():

    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    today = date.today().isoformat()

    for page in ["index.html", "search.html", "forcreators.html"]:
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = f"{BASE_URL}/{page}"
        SubElement(url, "lastmod").text = today
        SubElement(url, "changefreq").text = "daily"
        SubElement(url, "priority").text = "0.9"

    try:
        with open("data/creators_index.json", "r", encoding="utf-8") as f:
            creators = json.load(f)
        for creator in creators:
            url = SubElement(urlset, "url")
            SubElement(url, "loc").text = f"{BASE_URL}/creator.html?name={quote(creator)}"
            SubElement(url, "lastmod").text = today
            SubElement(url, "changefreq").text = "weekly"
            SubElement(url, "priority").text = "0.7"
    except FileNotFoundError:
        print("Warning: data/creators_index.json not found, skipping creator URLs.")

    try:
        with open("data/scripts_index.json", "r", encoding="utf-8") as f:
            scripts = json.load(f)
        for script in scripts:
            url = SubElement(urlset, "url")
            SubElement(url, "loc").text = (
                f"{BASE_URL}/script.html"
                f"?creator={quote(script['creator'])}"
                f"&name={quote(script['name'])}"
            )
            SubElement(url, "lastmod").text = today
            SubElement(url, "changefreq").text = "monthly"
            SubElement(url, "priority").text = "0.5"
    except FileNotFoundError:
        print("Warning: data/scripts_index.json not found, skipping script URLs.")

    indent(urlset, space="  ")

    xml_body = tostring(urlset, encoding="unicode")
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_body

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)

    print(f"Sitemap generated: {1 + len(creators) + len(scripts)} URLs")