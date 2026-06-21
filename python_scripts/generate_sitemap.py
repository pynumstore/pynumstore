from xml.etree.ElementTree import Element, SubElement, ElementTree, indent
import json
import os

def generate_sitemap():

    urls = []

    for file in os.listdir():
        if file.endswith(".html") and file != "404.html":
            urls.append(f"https://pynumstore.github.io/pynumstore/{file}")

    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in urls:
        url_element = SubElement(urlset, "url")
        loc = SubElement(url_element, "loc")
        loc.text = url

    indent(urlset, space="    ")

    tree = ElementTree(urlset)
    tree.write("sitemap.xml", encoding="utf-8", xml_declaration=True)