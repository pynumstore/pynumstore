import re
import os
import shutil
import bleach
import time
import json
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError
import tqdm
import gspread
from google.oauth2.service_account import Credentials
from tokens import SHEET_ID

ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr', 'pre', 'blockquote', 'code', 'kbd', 'samp', 'var',
    'b', 'i', 'u', 's', 'del', 'ins', 'em', 'strong', 'mark',
    'small', 'sub', 'sup', 'abbr', 'cite', 'q', 'dfn', 'time',
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    'a', 'img',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
    'div', 'span', 'section', 'article', 'aside', 'header', 'footer',
    'main', 'nav', 'figure', 'figcaption', 'details', 'summary',
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'title', 'lang', 'dir', 'aria-label',
          'aria-describedby', 'aria-hidden', 'role'],
    'a': ['href', 'title', 'target', 'rel', 'download', 'hreflang'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'loading', 'srcset', 'sizes'],
    'th': ['scope', 'colspan', 'rowspan', 'headers'],
    'td': ['colspan', 'rowspan', 'headers'],
    'col': ['span'],
    'colgroup': ['span'],
    'time': ['datetime'],
    'abbr': ['title'],
    'q': ['cite'],
    'blockquote': ['cite'],
    'del': ['cite', 'datetime'],
    'ins': ['cite', 'datetime'],
    'details': ['open'],
    'div': ['align'],
    'p': ['align'],
    'h1': ['align'], 'h2': ['align'], 'h3': ['align'],
    'h4': ['align'], 'h5': ['align'], 'h6': ['align']
}

ALLOWED_PROTOCOLS = [
    'http',
    'https',
    'mailto',
    'tel',
    'sms',
    'ftp',
    'sftp',
    '#',
]


def update(debug=None):

    if debug is not None: debug.pull("update")
    creators = generate_creators_index()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://my.numworks.com")
        page.wait_for_load_state("networkidle")
        page.locator("#pi_tracking_opt_in_no").click()

        scripts = generate_scripts_index(creators, page, debug)
        if debug is not None: debug.pull("nbScripts", len(scripts))

        scan_and_save_scripts(scripts, page, debug)

        for creator in os.listdir("data/"):
            if (not creator in creators) and (not creator[-5:] == ".json"):
                shutil.rmtree(f"data/{creator}")
                if debug is not None: debug.pull("errorCreator", creator)
                continue
            elif creator[-5:] == ".json":
                continue
            for script in os.listdir(f"data/{creator}/"):
                if not {"name":script, "creator": creator} in scripts:
                    shutil.rmtree(f"data/{creator}/{script}")
                    if debug is not None: debug.pull("errorScript", creator, script)
                    continue
    
    with open(f"data/creators_index.json", "w", encoding="utf-8") as f:
        json.dump(creators, f, indent=4)
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(
        "python_scripts/credentials.json",
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    sheet.clear()
    sheet.update(
        range_name=f"A1:A{len(creators)}",
        values=[[item] for item in creators]
    )
    if debug is not None: debug.pull("endUpdate")


def generate_creators_index():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(
        "python_scripts/credentials.json",
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    creators = sheet.col_values(1)
    return creators


def generate_scripts_index(creators, page, debug=None):

    scripts = []
    for creator in creators.copy():
            s = scan_creator(creator, page)
            if s is None:
                creators.remove(creator)
                if debug is not None: debug.pull("errorCreator2", creator)
                continue
            for script in s:
                scripts.append({"name": script, "creator": creator})
    with open(f"data/scripts_index.json", "w", encoding="utf-8") as f:
        json.dump(scripts, f, indent=4)
    return scripts


def scan_creator(creator, page):

    page.goto(f"https://my.numworks.com/python/{creator}")
    page.wait_for_load_state("networkidle")
    if page.title() == "404. Not found.":
        return None
        
    rows = page.locator("tbody").locator("tr").all()
    scripts = [row.locator("a").text_content()[:-3] for row in rows]
    
    return scripts


def scan_and_save_scripts(scripts, page, debug=None):

    t=time.monotonic()
    n=len(scripts)
    for script in tqdm.tqdm(scripts):
        #if debug is not None:
        #    debug.pull("scanScript", script["creator"], script["name"], scripts.index(script), n, t)
        metadata = scan_script(script["creator"], script["name"], page, debug)
        if metadata is None:
            continue
        with open(f"data/{script["creator"]}/{script["name"]}/metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)


def scan_script(creator, name, page, debug=None):

    nb_of_try = 0
    ok = False
    while not ok and nb_of_try < 3:
        
        try:

            page.goto(f"https://my.numworks.com/python/{creator}/{name}")
            page.wait_for_load_state("networkidle")
            if page.title() == "404. Not found.":
                return None

            canvas = page.locator(".screen-container")
            canvas.click()

            container = page.locator("div.col-description")
            created_at = container.locator("p").nth(1).inner_text()[11:]
            size = container.locator("p").nth(2).inner_text()

            html = page.content()
            match = re.search(r'class="text-justify">(.*)<hr', html, re.DOTALL)
            i = 0
            match = match.group(1)
            while match[i] == "\n" or match[i] == " " and i < len(match):
                i += 1
            match = match[i+4:]
            i = len(match) - 1
            while (match[i] == "\n" or match[i] == " ") and i >= 0:
                i -= 1
            description = match[:i+1]
            code_blocks = {}
            def save_code(m):
                key = f"__CODE_{len(code_blocks)}__"
                code_blocks[key] = m.group(0)
                return key

            description = re.sub(r'<(code|pre)[^>]*>.*?</\1>', save_code, description, flags=re.DOTALL)
            description = " ".join(description.split())
            for key, value in code_blocks.items():
                description = description.replace(key, value)
            description = bleach.clean(description, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, protocols=ALLOWED_PROTOCOLS, strip=True, strip_comments=True)

            stripped_description = re.sub(r'<(code|pre)[^>]*>.*?</\1>', '', description, flags=re.DOTALL)
            tags = re.findall(r'#(\w+)', stripped_description)

            if not os.path.exists(f"data/{creator}/"):
                os.makedirs(f"data/{creator}/")
            if not os.path.exists(f"data/{creator}/{name}/"):
                os.makedirs(f"data/{creator}/{name}/")

            time.sleep(0.5)
            canvas.screenshot(path=f"data/{creator}/{name}/{creator}_{name}.png")
            ok = True

        except TimeoutError:

            nb_of_try += 1

    if not ok:
        if debug is not None:
            debug.pull("errorScript2", creator, name)
        return None

    return {
        "name": name,
        "creator": creator,
        "created_at": created_at,
        "size": size,
        "image": f"data/{creator}/{name}/{creator}_{name}.png",
        "tags": tags,
        "description": description
    }