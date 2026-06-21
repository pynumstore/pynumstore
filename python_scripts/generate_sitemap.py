from xml.etree.ElementTree import Element, SubElement, ElementTree, indent
import json

def generate_sitemap():

    urls = [
        "https://pynumstore.github.io/pynumstore/",
        "https://pynumstore.github.io/pynumstore/index.html",
        "https://pynumstore.github.io/pynumstore/search.html",
        "https://pynumstore.github.io/pynumstore/forcreators.html",
        "https://pynumstore.github.io/pynumstore/404.html"
    ]

    with open("data/scripts_index.json", "r") as f:
        scripts = json.load(f)
    for script in scripts:
        urls.append(f"https://pynumstore.github.io/pynumstore/script.html?creator={script['creator']}&name={script['name']}")
    del scripts
    
    with open("data/creators_index.json", "r") as f:
        creators = json.load(f)
    for creator in creators:
        urls.append(f"https://pynumstore.github.io/pynumstore/creator.html?name={creator}")
    del creators

    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in urls:
        url_element = SubElement(urlset, "url")
        loc = SubElement(url_element, "loc")
        loc.text = url

    indent(urlset, space="    ")

    tree = ElementTree(urlset)
    tree.write("sitemap.xml", encoding="utf-8", xml_declaration=True)