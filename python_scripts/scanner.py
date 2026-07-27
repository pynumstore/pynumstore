from curl_cffi import requests as curl_requests
import hashlib
from bs4 import BeautifulSoup, Tag
import bleach
from bleach_allowed import *
import re
import time
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError
from datetime import datetime


class Scanner:


    def __init__(self):
        
        p = sync_playwright().start()
        self.browser = p.chromium.launch(headless=True)
        self.page = self.browser.new_page()
        self.page.goto("https://my.numworks.com")
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#pi_tracking_opt_in_no").click()
        self.session = curl_requests.Session(impersonate="chrome120")
    

    def close(self):

        self.browser.close()
        self.session.close()


    def get_creator_hash(self, creator):

        try:
            r = self.session.get(f"https://my.numworks.com/python/{creator}", timeout=30)
        except:
            return None, "network_error"

        if r.status_code != 200:
            return None, "network_error"

        html = r.text

        start = html.lower().find("<body")
        if start == -1:
            return None, ""

        start = html.find(">", start) + 1
        end = html.lower().find("</body>", start)

        if end == -1:
            return None, ""

        body = html[start:end]

        return hashlib.sha256(body.encode()).hexdigest(), ""


    def get_script_hash(self, creator, name):

        try:
            r = self.session.get(f"https://my.numworks.com/python/{creator}/{name}", timeout=120)
        except:
            return None, "network_error"

        if r.status_code != 200:
            return None, "network_error"

        html = r.text

        start = html.lower().find("<body")
        if start == -1:
            return None, ""

        start = html.find(">", start) + 1
        end = html.lower().find("</body>", start)

        if end == -1:
            return None, ""

        body = html[start:end]

        return hashlib.sha256(body.encode()).hexdigest(), ""


    def full_creator_scan(self, creator):

        try:
            r = self.session.get(f"https://my.numworks.com/python/{creator}", timeout=30)
        except:
            return None, "network_error"

        if r.status_code != 200:
            return None, "network_error"

        names = []

        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        names_td = soup.find_all("td", class_="name")
        if names_td is None:
            return None, "td_not_found"
        for name_td in names_td:
            a = name_td.find("a")
            if a is None:
                return None, "a_not_found"
            name = a.get_text()
            names.append(name[:-3])

        return names, ""


    def full_script_scan(self, creator, name):

        nb_of_try = 0
        ok = False
        while not ok and nb_of_try < 3:
            try:

                self.page.goto(f"https://my.numworks.com/python/{creator}/{name}")
                self.page.wait_for_load_state("networkidle")
                if self.page.title() == "404. Not found.":
                    return None, "script_not_found"

                canvas = self.page.locator(".screen-container")
                canvas.click()

                container = self.page.locator("div.col-description")
                raw_date = container.locator("p").nth(1).inner_text()[11:]
                try:
                    created_at = datetime.strptime(raw_date.strip(), "%B %d, %Y").strftime("%Y-%m-%d")
                except ValueError:
                    created_at = raw_date
                size = self.parse_size(container.locator("p").nth(2).inner_text())

                html = self.page.content()
                description, tags, fail_reason = self.extract_tags_and_description(html)
                if description is None:
                    return None, fail_reason
                description = bleach.clean(description,
                                        tags=ALLOWED_TAGS,
                                        attributes=ALLOWED_ATTRIBUTES,
                                        protocols=ALLOWED_PROTOCOLS,
                                        strip=True,
                                        strip_comments=True
                                        )

                time.sleep(0.5)
                canvas.screenshot(path=f"data/thumbnails/{creator}_{name}.png")

                ok = True
            
            except TimeoutError:

                nb_of_try += 1
        
        if not ok:
            return None, "too_many_attempts"

        return {
            "name": name,
            "creator": creator,
            "created_at": created_at,
            "size": size,
            "thumbnail": f"data/thumbnails/{creator}_{name}.png",
            "tags": ", ".join([tag.lower() for tag in tags]),
            "description": description,
            "description_text": re.sub(r'<[^>]+>', '', description).strip()
        }, ""


    def extract_tags_and_description(self, html):
        
        soup = BeautifulSoup(html, "html.parser")

        div = soup.find("div", class_="pynumstore-tags")
        if div:
            try:
                tags = [tag.strip() for tag in div.get("title", "").split(",") if tag.strip()]
            except:
                tags = []
        else:
            tags = []

        content_div = soup.find("div", class_="content")
        if content_div is None:
            return None, None, "content_div_not_found"

        marker = content_div.find("p", class_="text-justify")
        if marker is None:
            return None, None, "marker_not_found"

        elements = []
        for sibling in marker.next_siblings:
            if isinstance(sibling, str) and not sibling.strip():
                continue
            if isinstance(sibling, Tag) and sibling.name == "pre" and sibling.get("id") == "script":
                break
            elements.append(sibling)
        
        if len(elements) == 1 and isinstance(elements[0], Tag) and elements[0].name == "hr":
            elements = []
        else:
            if len(elements) < 2:
                return None, None, "unexpected_structure"
            elements.pop()
            elements.pop()

        fragment = "".join(str(e) for e in elements).strip()

        return fragment, tags, None

    def parse_size(self, text):
        m = re.match(r'^(\d+(?:\.\d+)?)\s*(Bytes|KB|MB)$', text.strip())
        if not m:
            return None
        value, unit = float(m.group(1)), m.group(2)
        if unit == "Bytes": return int(value)
        if unit == "KB":    return int(value * 1024)
        if unit == "MB":    return int(value * 1024 * 1024)