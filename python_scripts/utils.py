from datetime import datetime
import time
import hashlib
import re
import sqlite3
import bleach
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
from google.oauth2.service_account import Credentials
from curl_cffi import requests
from bs4 import BeautifulSoup, Tag
from bleach_allowed import *
import gspread
import os
import json
from tokens import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SHEET_ID
from typing import Any
import logging

class NetworkError(Exception):
    """
    Exception raised for network-related errors.
    """
    pass

class NotFoundError(Exception):
    """
    Exception raised when an item is not found.
    """
    pass

class SQLDatabase:
    """
    A class to interact with the SQLite database for storing script and creator information.
    """

    def __init__(self, db_path: str = "data/pynumstore.db") -> None:
        """
        Initializes the SQLDatabase instance and establishes a connection to the SQLite database.
        """
        self.conn = sqlite3.connect(db_path)

    def close(self) -> None:
        """
        Closes the connection to the SQLite database.
        """
        self.conn.close()

    def commit(self) -> None:
        """
        Commits the current transaction.
        """
        self.conn.commit()

    def get_scripts_to_update(self) -> list:
        """
        Retrieves a list of scripts that are marked for update.
        """
        row = self.conn.execute(
            "SELECT creator, name FROM scripts WHERE to_update=1"
        ).fetchall()
        return [(r[0], r[1]) for r in row]

    def delete_script(self, creator: str, name: str) -> None:
        """
        Deletes a script from the database based on the creator and name.
        """
        self.conn.execute(
            "DELETE FROM scripts WHERE creator=? AND name=?",
            (creator, name)
        )

    def insert_script(self, creator: str, name: str) -> None:
        """
        Inserts a new script into the database.
        """
        self.conn.execute(
            f"""
            INSERT INTO scripts (creator, name)
            VALUES (?, ?)
            """,
            (creator, name)
            )

    def update_script(self, creator: str, name: str, data: dict) -> None:
        """
        Updates an existing script in the database.
        """
        self.conn.execute(
            "UPDATE scripts SET updated_at=?, size=?, thumbnail=?, tags=?, description=?, description_text=?, body_hash=?, to_update=? WHERE creator=? AND name=?",
            (data["updated_at"], data["size"], data["thumbnail"], data["tags"], data["description"], data["description_text"], data["body_hash"], data["to_update"], creator, name)
        )

    def get_creators(self) -> list:
        """
        Retrieves a list of all creators.
        """
        row = self.conn.execute("SELECT name FROM creators").fetchall()
        return [r[0] for r in row]

    def insert_creator(self, creator: str) -> None:
        """
        Inserts a new creator into the database.
        """
        self.conn.execute(
            f"""
            INSERT INTO creators (name)
            VALUES (?)
            """,
            (creator,)
            )

    def delete_creator(self, creator: str) -> None:
        """
        Deletes a creator from the database.
        """
        self.conn.execute(
            "DELETE FROM creators WHERE name = ?",
            (creator,)
        )
        scripts = self.creator_scripts(creator)
        for script in scripts:
            try:
                os.remove(f"data/thumbnails/{creator}_{script}.png")
            except FileNotFoundError:
                pass
        self.conn.execute(
            "DELETE FROM scripts WHERE creator = ?",
            (creator,)
        )

    def creator_scripts(self, creator: str) -> list:
        """
        Retrieves a list of scripts associated with a specific creator.
        """
        row = self.conn.execute(
            "SELECT name FROM scripts WHERE creator = ?",
            (creator,)
        ).fetchall()
        return [r[0] for r in row]

    def get_all_scripts(self) -> list:
        """
        Retrieves a list of all scripts.
        """
        row = self.conn.execute("SELECT creator, name FROM scripts").fetchall()
        return [(r[0], r[1]) for r in row]

    def get_script_hash(self, creator: str, name: str) -> str | None:
        """
        Retrieves the hash of a specific script.
        """
        row = self.conn.execute(
            "SELECT body_hash FROM scripts WHERE creator = ? AND name = ?",
            (creator, name)
        ).fetchone()
        return row[0] if row else None

    def set_to_update(self, creator: str, name: str, to_update: bool) -> None:
        """
        Sets the 'to_update' flag for a specific script.
        """
        if to_update:
            self.conn.execute(
                "UPDATE scripts SET to_update=? WHERE creator=? AND name=?",
                (1, creator, name)
            )
        else:
            self.conn.execute(
                "UPDATE scripts SET to_update=? WHERE creator=? AND name=?",
                (0, creator, name)
            )


class GoogleSheetsDatabase:
    """
    A class to interact with Google Sheets for retrieving creator information.
    """

    def get_creators(self) -> list:
        """
        Retrieves a list of creators from a Google Sheet.
        """
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(
            "python_scripts/credentials.json",
            scopes=scopes
        )
        try:
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SHEET_ID).sheet1
            creators = sheet.col_values(1)
        except Exception as e:
            raise NetworkError("Error while loading creators list:" + str(e))
        return creators


class Page:
    """
    A class to interact with the NumWorks website using a headless browser.
    """

    def __init__(self) -> None:
        """
        Initializes the Page instance and sets up a headless browser using Playwright.
        """
        try:
            p = sync_playwright().start()
            self.browser = p.chromium.launch(headless=True)

            def filter_requests(route):
                request = route.request
                host = urlparse(request.url).hostname or ""
                if not (
                    host == "numworks.com"
                    or host.endswith(".numworks.com")
                ):
                    route.abort()
                    return
                route.continue_()

            self.context = self.browser.new_context(
                service_workers="block"
            )
            self.context.route("**/*", filter_requests)

            self.page = self.context.new_page()
            self.page.goto("https://my.numworks.com")
            self.page.wait_for_load_state("networkidle")
        except Exception as e:
            raise NetworkError("Failed to initialize browser: " + str(e))
        try:
            self.page.locator("#pi_tracking_opt_in_no").click(timeout=5000)
        except Exception:
            logging.warning("Cookie banner not found, continuing")

    def close(self) -> None:
        """
        Closes the headless browser.
        """
        self.browser.close()

    def goto(self, creator: str, name: str) -> None:
        """
        Navigates to the specified script page on the NumWorks website.
        """
        try:
            self.page.goto(f"https://my.numworks.com/python/{creator}/{name}")
            self.page.wait_for_load_state("networkidle")
        except Exception as e:
            raise NetworkError("Failed to navigate to script: " + str(e))
        if "404" in self.page.title():
            raise NotFoundError("Script not found")



class PageParser:
    """
    A class to parse the content of a script page and extract relevant information.
    """
    def __init__(self) -> None:
        """
        Initializes the PageParser instance.
        """
        self.current_creator = None
        self.current_name = None
        self.soup = None

    def parse_page(self, page: Page, creator: str, name: str) -> dict:
        """
        Parses the content of a script page and extracts relevant information.
        """
        playright_page = page.page
        if self.current_creator != creator or self.current_name != name or self.soup is None:
            try:
                activator = playright_page.locator(".activator-play")
                activator.click()
            except Exception as e:
                raise NotFoundError("Failed to click canvas: " + str(e))

            html = playright_page.content()
            self.soup = BeautifulSoup(html, "html.parser")
            self.current_creator = creator
            self.current_name = name
        soup = self.soup
        metadata_div = soup.find("div", class_="col-description")
        if not metadata_div:
            raise NotFoundError("Metadata div not found")
        all_p = metadata_div.find_all("p")
        updated_at = None
        size = None
        for p in all_p:
            if "Created on" in p.text:
                updated_at = self.parse_date(p.text.strip())
            elif "KB" in p.text or "MB" in p.text or "Bytes" in p.text:
                size = self.parse_size(p.text.strip())
        if not updated_at or not size:
            raise NotFoundError("Failed to parse updated_at or size")

        try:
            description = self.parse_description(soup)
        except NotFoundError as e:
            raise NotFoundError("Failed to parse description: " + str(e))

        try:
            tags = self.parse_tags(soup)
        except NotFoundError as e:
            raise NotFoundError("Failed to parse tags: " + str(e))

        time.sleep(1.5)
        loader = playright_page.locator(".loader")
        if loader.count() > 0:
            thumbnail = "default_thumbnail"
        else:
            try:
                thumbnail = f"data/thumbnails/{creator}_{name}.png"
                canvas = playright_page.locator("canvas")
                canvas.screenshot(path=thumbnail)
            except Exception as e:
                raise NotFoundError("Failed to take screenshot: " + str(e))

        return {
            "name": name,
            "creator": creator,
            "updated_at": updated_at,
            "size": size,
            "thumbnail": thumbnail,
            "tags": ", ".join([tag.lower() for tag in tags]),
            "description": description,
            "description_text": re.sub(r'<[^>]+>', '', description).strip(),
            "to_update": 0
        }

    def parse_date(self, text: str) -> str:
        """
        Parses a date string in the format "Created on Month Day, Year" and returns it in the format "YYYY-MM-DD".
        """
        raw_date = text[11:]
        try:
            updated_at = datetime.strptime(raw_date.strip(), "%B %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            updated_at = raw_date
        return updated_at

    def parse_size(self, text: str) -> int | None:
        """
        Parses a size string in the format "X KB" or "X MB" and returns it in bytes.
        """
        m = re.match(r'^(\d+(?:\.\d+)?)\s*(Bytes|KB|MB)$', text.strip())
        if not m:
            return None
        value, unit = float(m.group(1)), m.group(2)
        if unit == "Bytes": return int(value)
        if unit == "KB":    return int(value * 1024)
        if unit == "MB":    return int(value * 1024 * 1024)

    def parse_description(self, soup: BeautifulSoup) -> str:
        """
        Parses the description of a script from the BeautifulSoup object.
        """
        content_div = soup.find("div", class_="content")
        if content_div is None:
            raise NotFoundError("Content div not found")
        descr = content_div.find("div", class_="text-justify")
        if descr is None:
            raise NotFoundError("Marker not found in content div")
        fragment = descr.decode_contents()
        fragment = bleach.clean(fragment,
                                tags=ALLOWED_TAGS,
                                attributes=ALLOWED_ATTRIBUTES,
                                protocols=ALLOWED_PROTOCOLS,
                                strip=True,
                                strip_comments=True
                                )
        return fragment

    def parse_tags(self, soup: BeautifulSoup) -> list:
        """
        Parses the tags of a script from the BeautifulSoup object.
        """
        div = soup.find("div", class_="pynumstore-tags")
        if div:
            try:
                tags = [tag.strip() for tag in str(div.get("title", "")).split(",") if tag.strip()]
            except:
                tags = []
        else:
            tags = []
        return tags


class CurlRequest:
    """
    A class to handle HTTP requests using the curl_cffi library.
    """

    def __init__(self) -> None:
        """
        Initializes the CurlRequest instance and sets up a requests session with impersonation.
        """
        self.session = requests.Session(impersonate="chrome120")
        self.current_url = None
        self.current_html = None

    def close(self) -> None:
        """
        Closes the requests session.
        """
        self.session.close()

    def get_creator_html(self, creator: str) -> str:
        """
        Fetches the HTML content of a creator's page from the NumWorks website.
        """
        if self.current_url == f"https://my.numworks.com/python/{creator}" and self.current_html is not None:
            return self.current_html
        try:
            r = self.session.get(f"https://my.numworks.com/python/{creator}", timeout=120)
        except Exception as e:
            raise NetworkError("Failed to fetch creator HTML: " + str(e))
        if r.status_code == 404:
            raise NotFoundError(f"Creator {creator} not found")
        if r.status_code != 200:
            raise NetworkError(f"Failed to fetch creator HTML, status code: {r.status_code}")
        self.current_url = f"https://my.numworks.com/python/{creator}"
        self.current_html = r.text
        return r.text


class HTMLParser:
    """
    A class to parse HTML content and extract script information.
    """

    def __init__(self) -> None:
        """
        Initializes the HTMLParser instance.
        """
        self.current_creator = None
        self.beautifulsoup = None

    def get_script_hash(self, html: str, creator: str, name: str) -> str:
        """
        Parses the HTML content of a creator's page and retrieves the hash of a specific script.
        """
        if self.current_creator != creator or self.beautifulsoup is None:
            self.current_creator = creator
            self.beautifulsoup = BeautifulSoup(html, "html.parser")
        soup = self.beautifulsoup
        scripts = soup.find_all("tr")
        if not scripts:
            raise NotFoundError("No scripts found in the HTML")
        for script in scripts:
            name_td = script.find("td", class_="name")
            if not name_td:
                name_th = script.find("th", class_="name")
                if not name_th:
                    raise NotFoundError("No name column found in the script row")
                else:
                    continue
            a = name_td.find("a")
            if not a:
                raise NotFoundError("No link found in the name column")
            if a.text.strip() == name+".py":
                description_td = script.find("td", class_="descr")
                if not description_td:
                    raise NotFoundError("No description column found in the script row")
                description = description_td.text.strip()
                code_td = script.find("send-to-calculator")
                if not code_td:
                    raise NotFoundError("No code column found in the script row")
                code = str(code_td["script-content"]).strip()
                hash_input = description + code
                return hashlib.sha256(hash_input.encode()).hexdigest()
        raise NotFoundError(f"Script '{name}' not found for creator '{creator}'")

    def get_scripts(self, html: str, creator: str) -> list[str]:
        """
        Parses the HTML content of a creator's page and retrieves a list of script names.
        """
        if self.current_creator != creator or self.beautifulsoup is None:
            self.current_creator = creator
            self.beautifulsoup = BeautifulSoup(html, "html.parser")
        soup = self.beautifulsoup
        names = []
        names_td = soup.find_all("td", class_="name")
        if not names_td and soup.find("th", class_="name") is None:
            raise NotFoundError("Unexpected page structure")
        for name_td in names_td:
            a = name_td.find("a")
            if a is None:
                raise NotFoundError("Error while parsing: <a> not found")
            name = a.get_text()
            names.append(name[:-3])
        return names


class TelegramBot:
    """
    A class to interact with a telegram bot with the curl_cffi library.
    """

    def __init__(self, token: str = TELEGRAM_BOT_TOKEN, chat_id: str = TELEGRAM_CHAT_ID) -> None:
        """
        Initializes the TelegramBot instance.
        """
        self.token = token
        self.chat_id = chat_id
        self.url = f"https://api.telegram.org/bot{token}/"
        self.usr_id = chat_id
        with open("python_scripts/settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.offset = data["telegram_offset"]

    def send_message(self, text: str) -> Any:
        """
        Send a message to the telegram bot.
        """
        data = {
            "chat_id": self.chat_id,
            "text": text
        }
        r = requests.post(self.url + "sendMessage", json=data)
        return r.json()
    
    def send_file(self, name: str, text: str) -> None:
        """
        Send a file to the telegram bot, useful for too long message.
        """
        url = f"https://api.telegram.org/bot{self.token}/sendDocument"
        files = {
            "document": (name, text.encode("utf-8"))
        }
        data = {"chat_id": self.chat_id}
        requests.post(url, data=data, files=files)

    def get_messages(self) -> list:
        """
        Get messages from the telegram bot.
        Offset is used to retrieve only unread messages.
        """
        r = requests.get(self.url + "getUpdates", params={"offset": self.offset})
        data = r.json()
        messages = []
        for result in data["result"]:
            if "message" in result and str(result["message"]["chat"]["id"]) == self.chat_id and str(result["message"]["from"]["id"]) == self.usr_id:
                messages.append(result["message"]["text"])
                self.offset = result["update_id"] + 1
        self.save_offset()
        return messages
    
    def save_offset(self) -> None:
        """
        Save the new offset.
        Offset is used to retrieve only unread messages.
        """
        with open("python_scripts/settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        data["telegram_offset"] = self.offset
        with open("python_scripts/settings.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
