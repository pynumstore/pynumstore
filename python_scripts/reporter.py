from telegram_bot import TelegramBot
import time


class Reporter:

    def __init__(self):
        self.bot = TelegramBot()
    
    def start_update(self, type="update"):
        if type == "update":
            self.bot.send_message("Starting update...")
        elif type == "full_update":
            self.bot.send_message("Starting full update...")
        elif type == "creator_update":
            self.bot.send_message("Starting creator update...")
    
    def end_update(self, type="update"):
        if type == "update":
            self.bot.send_message("Update finished.")
        elif type == "full_update":
            self.bot.send_message("Full update finished.")
        elif type == "creator_update":
            self.bot.send_message("Creator update finished.")

    def generate_and_send_report(self, type="update", *args):
        report = ""
        if type == "update":
            report += f"Update report:\n"
            report += f"Date and time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"Length of creators to check: {len(args[0])}\n"
            report += f"{len(args[1])} new creators found:\n"
            for creator in args[1]:
                report += f"  - {creator}\n"
            report += f"{len(args[2])} creators deleted:\n"
            for creator in args[2]:
                report += f"  - {creator}\n"
            report += f"{len(args[3])} creators unchanged.\n"
            report += f"{len(args[4])} creators updated:\n"
            for creator in args[4]:
                report += f"  - {creator}\n"
            report += f"{len(args[5])+len(args[6])} scripts found.\n"
            report += f"{len(args[6])} new scripts found:\n"
            for script in args[6]:
                report += f"  - {script[0]}/{script[1]}\n"
            report += f"{len(args[7])} scripts deleted:\n"
            for script in args[7]:
                report += f"  - {script[0]}/{script[1]}\n"
            report += f"{len(args[8])} scripts updated:\n"
            for script in args[8]:
                report += f"  - {script[0]}/{script[1]}\n"
        elif type == "full_update":
            report += f"Full update report:\n"
            report += f"Date and time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"{len(args[0])} creators updated.\n"
            report += f"{len(args[1])} scripts updated.\n"
        elif type == "creator_update":
            report += f"Creator update report:\n"
            report += f"Date and time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"{len(args[0])} creators updated:\n"
            for creator in args[0]:
                report += f"  - {creator}\n"
            report += f"{len(args[1])} scripts updated:\n"
            for script in args[1]:
                report += f"  - {script[0]}/{script[1]}\n"
        self.bot.send_file("report.txt", report)

    def send_error(self, error):
        self.bot.send_message(f"An error occurred: {error.__class__.__name__}")
        self.bot.send_file("error.txt", error.__str__())