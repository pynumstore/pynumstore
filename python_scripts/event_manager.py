import json
import schedule
from updater import Updater
from telegram_bot import TelegramBot
import threading
import time
from git import Repo

bot = TelegramBot()
updater = Updater()
update_thread = None
repo = Repo(".")
update = False

def change_update():
    global update
    update = True
schedule.every().days.at("12:00").do(change_update)

while True:

    try:

        schedule.run_pending()
        msgs = bot.get_messages()
        for msg in msgs+[""]:

            if msg[:7] == "/update" or update:
                if update_thread is None or not update_thread.is_alive():
                    update_thread = threading.Thread(target=updater.update)
                    update_thread.start()
                else:
                    bot.send_message("An update is currently running.")
                update = False

            elif msg[:12] == "/full_update":
                if update_thread is None or not update_thread.is_alive():
                    update_thread = threading.Thread(target=updater.full_update)
                    update_thread.start()
                else:
                    bot.send_message("An update is currently running.")
            
            elif msg[:15] == "/creator_update":
                if update_thread is None or not update_thread.is_alive():
                    creators_name = msg[16:].split(" ")
                    if creators_name:
                        update_thread = threading.Thread(target=updater.creator_update, args=(creators_name,))
                        update_thread.start()
                    else:
                        bot.send_message("Please provide a creator name after the command.")
                else:
                    bot.send_message("An update is currently running.")

            elif msg[:7] == "/status":
                if update_thread is None or not update_thread.is_alive():
                    bot.send_message("No update is currently running.")
                else:
                    bot.send_message("An update is currently running.")

            elif msg[:11] == "/git_status":
                try:
                    status = repo.git.status()
                    if len(status) > 4000:
                        bot.send_file("git_status.txt", status)
                    else:
                        bot.send_message(f"Repository status:\n{status}")
                except Exception as e:
                    bot.send_message(f"Failed to get repository status: {e}")
            
            elif msg[:4] == "/add":
                try:
                    repo.git.add(A=True)
                    bot.send_message("All changes added to the staging area.")
                except Exception as e:
                    bot.send_message(f"Failed to add changes: {e}")

            elif msg[:5] == "/push":
                try:
                    repo.git.add(A=True)
                    repo.git.commit(m=f"{time.strftime('%Y-%m-%d %H:%M:%S')} Update")
                    repo.git.push()
                    bot.send_message("Changes pushed to the repository.")
                except Exception as e:
                    bot.send_message(f"Failed to push changes: {e}")

            elif msg[:11] == "/reset_soft":
                try:
                    repo.git.reset('--soft', 'HEAD~1')
                    bot.send_message("Soft reset to the previous commit completed.")
                except Exception as e:
                    bot.send_message(f"Failed to perform soft reset: {e}")

            elif msg[:11] == "/reset_hard":
                try:
                    repo.git.reset('--hard', 'HEAD~1')
                    bot.send_message("Hard reset to the previous commit completed.")
                except Exception as e:
                    bot.send_message(f"Failed to perform hard reset: {e}")

            elif msg[:11] == "/push_force":
                try:
                    repo.git.push('--force')
                    bot.send_message("Force push completed.")
                except Exception as e:
                    bot.send_message(f"Failed to perform force push: {e}")

            else:
                if not msg == "":
                    bot.send_message("Unknown command.")
    
    except Exception as e:
        bot = TelegramBot()
        updater = Updater()
        update_thread = None
        repo = Repo(".")
        update = False
        bot.send_message("An error occurred. The bot has been reset.")
        bot.send_file("error_log.txt", str(e))
        print(f"Error: {e}")
    
    time.sleep(1)