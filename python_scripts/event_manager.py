import time
from datetime import datetime, timezone, timedelta
import json
from dbg import update
import requests
import traceback
from generate_sitemap import generate_sitemap
from tokens import CHAT_TOKEN, CHAT_ID

class TelegramBot:

    def __init__(self, token, chat_id):
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
            "text": text,
            "parse_mode": "HTML"
        }
        r = requests.post(self.url + "sendMessage", json=data)
        return r.json()
    
    def send_file(self, text):
        url = f"https://api.telegram.org/bot{self.token}/sendDocument"
        files = {
            "document": ("ERROR.txt", text.encode("utf-8"))
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


class DebugHandler:

    def __init__(self, bot):
        self.bot = bot

    def pull(self, debug_type, *args):
        if debug_type == "status":
            msg = f"Time before next update: {format_monotonic(args[0])}"
            print(msg)
            bot.send_message(msg)
        elif debug_type == "update":
            msg = "| Update started... |"
            print(msg)
            bot.send_message(msg)
        elif debug_type == "endUpdate":
            msg = "| Update ended. |"
            print(msg)
            bot.send_message(msg)
        elif debug_type == "nbScripts":
            msg = f"Found {args[0]} scripts..."
            print("  "+msg)
            bot.send_message(msg)
        elif debug_type == "errorCreator2":
            msg = f"{args[0]} creator doesn't exist on the Numworks website, so it has been removed."
            print("  "+msg)
            bot.send_message(msg)
        elif debug_type == "errorScript":
            msg = f"{args[1]} script by {args[0]} creator no longer exists on the Numworks website, so its file has been deleted!"
            print("  "+msg)
            bot.send_message(msg)
        elif debug_type == "errorScript2":
            msg = f"{args[1]} script by {args[0]} creator can't be scanned, so its was skipped!"
            print("  "+msg)
            bot.send_message(msg)
        elif debug_type == "errorCreator":
            msg = f"{args[0]} creator no longer exists on the Numworks website, so its file has been deleted!"
            print("  "+msg)
            bot.send_message(msg)
        elif debug_type == "errorDescription":
            msg = f"{args[1]} script by {args[0]} creator has an unexpected description markup, so it was skipped! Reason: {args[2]}"
            print("  "+msg)
            bot.send_message(msg)
        elif debug_type == "scanScript":
            t = time.monotonic()
            if args[2] == 0:
                msg = [
                    f"Scanning {args[1]} script by {args[0]} creator...",
                    f"Scanning in progress: 0 % ; 0 / inf"
                    ]
            else:
                msg = [
                    f"Scanning {args[1]} script by {args[0]} creator...",
                    f"Scanning in progress: {str(args[2]/args[3]*100)[:5]} % ; {format_monotonic(t-args[4])} / {format_monotonic((t-args[4])/args[2]*args[3])}"
                    ]
            print("  "+msg[0])
            print("  "+msg[1])
        


def format_monotonic(time):
    days = int(time // (3600*24))
    hours = int((time // 3600) % 24)
    minutes = int((time // 60) % 60)
    seconds = int(time) % 60
    if days>0:
        return f"{days}d {hours}:{minutes}:{seconds}"
    elif hours>0:
        return f"{hours}:{minutes}:{seconds}"
    elif minutes>0:
        return f"{minutes}:{seconds}"
    else:
        return f"{seconds}"


bot = TelegramBot(CHAT_TOKEN, CHAT_ID)
debugHandler = DebugHandler(bot)

while True:

    try:

        time.sleep(10)

        msgs = bot.get_messages()
        with open("python_scripts/settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            last_update = datetime.fromisoformat(data["last_update"])
            last_update = last_update.replace(tzinfo=timezone.utc)
            update_interval = data["update_interval"]
            now = datetime.now(timezone.utc)

        if "/update" in msgs or (now - last_update).total_seconds() > update_interval:
            update(debugHandler)
            generate_sitemap()
            with open("python_scripts/settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            data["last_update"] = now.isoformat()
            with open("python_scripts/settings.json", "w", encoding="utf-8") as f:
                json.dump(data, f)
        
        elif "/status" in msgs:
            debugHandler.pull("status",
                            (timedelta(seconds=update_interval) - (now - last_update)).total_seconds()
                            )

    except Exception as e:
        
        try:
            bot.send_message(f"ERROR: {type(e).__name__}: {e}")
            bot.send_file(traceback.format_exc())
            print(traceback.format_exc())
        except requests.ConnectionError as e:
            print("ConnectionError")
        except Exception as e:
            print(traceback.format_exc())