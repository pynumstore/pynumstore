import requests
import json
from tokens import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramBot:

    def __init__(self, token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID):
        self.token = token
        self.chat_id = chat_id
        self.url = f"https://api.telegram.org/bot{token}/"
        self.usr_id = chat_id
        with open("python_scripts/settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.offset = data["telegram_offset"]

    def send_message(self, text):
        data = {
            "chat_id": self.chat_id,
            "text": text
        }
        r = requests.post(self.url + "sendMessage", json=data)
        return r.json()
    
    def send_file(self, name, text):
        url = f"https://api.telegram.org/bot{self.token}/sendDocument"
        files = {
            "document": (name, text.encode("utf-8"))
        }
        data = {"chat_id": self.chat_id}
        requests.post(url, data=data, files=files)

    def get_messages(self):
        r = requests.get(self.url + "getUpdates", params={"offset": self.offset})
        data = r.json()
        messages = []
        for result in data["result"]:
            if "message" in result and str(result["message"]["chat"]["id"]) == self.chat_id and str(result["message"]["from"]["id"]) == self.usr_id:
                messages.append(result["message"]["text"])
                self.offset = result["update_id"] + 1
        self.save_offset()
        return messages
    
    def save_offset(self):
        with open("python_scripts/settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        data["telegram_offset"] = self.offset
        with open("python_scripts/settings.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)