from utils import CurlRequest, HTMLParser, NotFoundError, PageParser, SQLDatabase, Page, NetworkError, GoogleSheetsDatabase, TelegramBot
import logging
import tqdm
from datetime import datetime, timezone
import json
import os
import sys
from generate_sitemap import generate_sitemap


os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/lupdater.log"),
        logging.StreamHandler()
    ]
)


def get_scripts_to_update() -> None:
    """
    This function retrieves the list of creators from Google Sheets and the local SQL database,
    compares them, and updates the local database accordingly. It also checks for scripts that need to be updated based on their hash values.
    """

    logging.info("Starting get scripts to update process...")

    sqlDatabase = SQLDatabase()
    googleSheetsDatabase = GoogleSheetsDatabase()
    try:
        curlRequest = CurlRequest()
    except Exception as e:
        logging.error("Failed to initialize curl session: %s", e)
        sqlDatabase.close()
        return
    htmlParser = HTMLParser()

    try:
        creators_gs = googleSheetsDatabase.get_creators()
    except NetworkError as e:
        logging.error("Failed to load creators list from Google Sheets: %s", e)
        sqlDatabase.close()
        curlRequest.close()
        return
    creators_db = sqlDatabase.get_creators()

    creators_gs_set = set(creators_gs)
    creators_db_set = set(creators_db)
    creators_in_both = list(creators_db_set & creators_gs_set)
    creators_to_insert = list(creators_gs_set - creators_db_set)
    creators_to_delete = list(creators_db_set - creators_gs_set)
    creators_to_scan = creators_in_both + creators_to_insert

    for creator in creators_to_insert:
        sqlDatabase.insert_creator(creator)
    for creator in creators_to_delete:
        sqlDatabase.delete_creator(creator)
    sqlDatabase.commit()

    if len(creators_to_insert) > 1:
        logging.info("%s new creators found and inserted: %s", len(creators_to_insert), creators_to_insert)
    elif len(creators_to_insert) == 1:
        logging.info("%s new creator found and inserted: %s", len(creators_to_insert), creators_to_insert)
    if len(creators_to_delete) > 1:
        logging.info("%s creators not found and deleted: %s", len(creators_to_delete), creators_to_delete)
    elif len(creators_to_delete) == 1:
        logging.info("%s creator not found and deleted: %s", len(creators_to_delete), creators_to_delete)
    if len(creators_to_scan) > 1:
        logging.info("%s creators to scan...", len(creators_to_scan))
    elif len(creators_to_scan) == 1:
        logging.info("%s creator to scan...", len(creators_to_scan))

    for creator in tqdm.tqdm(creators_to_scan):

        error_occurred = False

        nb_of_try = 0
        while nb_of_try < 3:
            try:
                html = curlRequest.get_creator_html(creator)
                break
            except NetworkError as e:
                if nb_of_try < 2:
                    logging.warning("Network error while fetching creator %s (%d): %s", creator, nb_of_try + 1, e)
                else:
                    logging.error("Network error while fetching creator %s after 3 attempts: %s", creator, e)
                    sqlDatabase.delete_creator(creator)
                    sqlDatabase.commit()
                    error_occurred = True
            nb_of_try += 1
        if error_occurred:
            continue

        nb_of_try = 0
        while nb_of_try < 3:
            try:
                scripts_current = htmlParser.get_scripts(html, creator) # pyright: ignore[reportPossiblyUnboundVariable]
                break
            except Exception as e:
                if nb_of_try < 2:
                    logging.warning("Error while getting %s creator's scripts (%d): %s", creator, nb_of_try + 1, e)
                else:
                    logging.error("Error while getting %s creator's scripts after 3 attempts: %s", creator, e)
                    sqlDatabase.delete_creator(creator)
                    sqlDatabase.commit()
                    error_occurred = True
            nb_of_try += 1
        if error_occurred:
            continue

        scripts_db = sqlDatabase.creator_scripts(creator)

        scripts_current_set = set(scripts_current) # pyright: ignore[reportPossiblyUnboundVariable]
        scripts_db_set = set(scripts_db)
        scripts_in_both = list(scripts_db_set & scripts_current_set)
        scripts_to_insert = list(scripts_current_set - scripts_db_set)
        scripts_to_delete = list(scripts_db_set - scripts_current_set)
        scripts_to_scan = scripts_in_both + scripts_to_insert

        for script in scripts_to_insert:
            sqlDatabase.insert_script(creator, script)
        for script in scripts_to_delete:
            sqlDatabase.delete_script(creator, script)
            try:
                os.remove(f"data/thumbnails/{script[0]}_{script[1]}.png")
            except FileNotFoundError:
                pass
        sqlDatabase.commit()

        if len(scripts_to_insert) > 1:
            logging.info("%s new scripts found and inserted: %s", len(scripts_to_insert), [(creator, s) for s in scripts_to_insert])
        elif len(scripts_to_insert) == 1:
            logging.info("%s new script found and inserted: %s", len(scripts_to_insert), [(creator, s) for s in scripts_to_insert])
        if len(scripts_to_delete) > 1:
            logging.info("%s scripts not found and deleted: %s", len(scripts_to_delete), [(creator, s) for s in scripts_to_delete])
        elif len(scripts_to_delete) == 1:
            logging.info("%s script not found and deleted: %s", len(scripts_to_delete), [(creator, s) for s in scripts_to_delete])

        for script in scripts_to_scan:

            error_occurred = False

            nb_of_try = 0
            while nb_of_try < 3:
                try:
                    hash_current = htmlParser.get_script_hash(html, creator, script) # pyright: ignore[reportPossiblyUnboundVariable]
                    break
                except Exception as e:
                    if nb_of_try < 2:
                        logging.warning("Error while hashing script %s/%s (%d): %s", creator, script, nb_of_try + 1, e)
                    else:
                        logging.error("Error while hashing script %s/%s after 3 attempts: %s", creator, script, e)
                        error_occurred = True
                nb_of_try += 1
            if error_occurred:
                continue

            hash_db = sqlDatabase.get_script_hash(creator, script)
            if hash_db is None or hash_db != hash_current: # pyright: ignore[reportPossiblyUnboundVariable]
                sqlDatabase.set_to_update(creator, script, True)
                sqlDatabase.commit()
                
    sqlDatabase.close()
    curlRequest.close()
    logging.info("Get scripts to update process completed.")


def set_all_scripts_to_update() -> None:
    """
    Sets all scripts in the database to be updated.
    """

    sqlDatabase = SQLDatabase()
    scripts = sqlDatabase.get_all_scripts()
    for creator, name in scripts:
        sqlDatabase.set_to_update(creator, name, True)
    sqlDatabase.commit()
    sqlDatabase.close()


def set_all_scripts_of_some_creators_to_update(creators: list) -> None:
    """
    Sets all scripts of some creators in the database to be updated.
    """

    sqlDatabase = SQLDatabase()
    for creator in creators:
        scripts = sqlDatabase.creator_scripts(creator)
        for name in scripts:
            sqlDatabase.set_to_update(creator, name, True)
    sqlDatabase.commit()
    sqlDatabase.close()


def update_scripts() -> bool:
    """
    This function retrieves the list of scripts that need to be updated from the local SQL database,
    fetches their content from the NumWorks website, and updates the local database with the new information.
    Returns True if the process went through to the end, False if it was interrupted
    (initialization failure or network error): remaining scripts keep to_update=1.
    """

    logging.info("Starting script update process...")

    sqlDatabase = SQLDatabase()
    try:
        page = Page()
    except NetworkError as e:
        logging.error("Failed to initialize browser: %s", e)
        sqlDatabase.close()
        return False
    pageParser = PageParser()
    try:
        curlRequest = CurlRequest()
    except Exception as e:
        logging.error("Failed to initialize curl session: %s", e)
        page.close()
        sqlDatabase.close()
        return False
    htmlParser = HTMLParser()

    scripts_to_update = sqlDatabase.get_scripts_to_update()
    if len(scripts_to_update) > 1:
        logging.info("%s scripts to update found...", len(scripts_to_update))
    elif len(scripts_to_update) == 1:
        logging.info("%s script to update found...", len(scripts_to_update))
    elif len(scripts_to_update) == 0:
        logging.info("No scripts to update found...")

    aborted = False

    for script in tqdm.tqdm(scripts_to_update):

        error_occurred = False

        nb_of_try = 0
        while nb_of_try < 3:
            try:
                page.goto(script[0], script[1])
                break
            except NetworkError as e:
                logging.error("Network error while accessing script %s/%s: %s", script[0], script[1], e)
                logging.error("Aborting the update: the remaining scripts keep to_update=1 and will be retried next time.")
                aborted = True
                break
            except NotFoundError:
                if nb_of_try < 2:
                    logging.warning("Script %s/%s not found (%d)", script[0], script[1], nb_of_try + 1)
                else:
                    sqlDatabase.delete_script(script[0], script[1])
                    try:
                        os.remove(f"data/thumbnails/{script[0]}_{script[1]}.png")
                    except FileNotFoundError:
                        pass
                    sqlDatabase.commit()
                    logging.warning("Script %s/%s not found after 3 attempts, so it has been deleted", script[0], script[1])
                    error_occurred = True
            nb_of_try += 1
        if aborted:
            break
        if error_occurred:
            continue

        nb_of_try = 0
        while nb_of_try < 3:
            try:
                data = pageParser.parse_page(page, script[0], script[1])
                break
            except Exception as e:
                if nb_of_try < 2:
                    logging.warning("Error while parsing script %s/%s (%d): %s", script[0], script[1], nb_of_try + 1, e)
                else:
                    logging.error("Error while parsing script %s/%s after 3 attempts: %s", script[0], script[1], e)
                    error_occurred = True
            nb_of_try += 1
        if error_occurred:
            continue
                    
        nb_of_try = 0
        while nb_of_try < 3:
            try:
                html = curlRequest.get_creator_html(script[0])
                break
            except NetworkError as e:
                if nb_of_try < 2:
                    logging.warning("Network error while fetching script %s/%s (%d): %s", script[0], script[1], nb_of_try + 1, e)
                else:
                    logging.error("Network error while fetching script %s/%s after 3 attempts: %s", script[0], script[1], e)
                    error_occurred = True
            nb_of_try += 1
        if error_occurred:
            continue

        nb_of_try = 0
        while nb_of_try < 3:
            try:
                hash = htmlParser.get_script_hash(html, script[0], script[1]) # pyright: ignore[reportPossiblyUnboundVariable]
                break
            except Exception as e:
                if nb_of_try < 2:
                    logging.warning("Error while hashing script %s/%s (%d): %s", script[0], script[1], nb_of_try + 1, e)
                else:
                    logging.error("Error while hashing script %s/%s after 3 attempts: %s", script[0], script[1], e)
                    error_occurred = True
            nb_of_try += 1
        if error_occurred:
            continue

        data["body_hash"] = hash # pyright: ignore[reportPossiblyUnboundVariable]
        sqlDatabase.update_script(script[0], script[1], data) # pyright: ignore[reportPossiblyUnboundVariable]
        sqlDatabase.commit()

    with open("data/version.json", "w") as f:
        json.dump({"v": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")}, f)
    generate_sitemap()
    page.close()
    sqlDatabase.close()
    curlRequest.close()
    if aborted:
        logging.warning("Script update process aborted because of a network error.")
        return False
    logging.info("Script update process completed.")
    return True


if __name__ == "__main__":

    args = sys.argv[1:]
    
    if len(args) == 0:
        get_scripts_to_update()
        update_scripts()

    elif args[0] == "--full-update":
        set_all_scripts_to_update()
        update_scripts()

    elif args[0] == "--update-creators":
        if len(args) < 2:
            logging.error("Please provide at least one creator name after --update-creators")
            sys.exit(1)
        creators = args[1:]
        set_all_scripts_of_some_creators_to_update(creators)
        update_scripts()

    elif args[0] == "--get-scripts-to-update":
        get_scripts_to_update()

    elif args[0] == "--update-scripts":
        update_scripts()

    elif args[0] == "--daily-protocol":
        """
        Daily protocol is launched every day by an external program: "daily-protocol.sh"
        """
        logging.info("Starting daily protocol...")
        get_scripts_to_update()
        sqlDatabase = SQLDatabase()
        telegramBot = TelegramBot()
        scripts_to_update = sqlDatabase.get_scripts_to_update()
        sqlDatabase.close()
        if len(scripts_to_update) > 0:
            logging.info("Daily protocol: %s scripts to update found...", len(scripts_to_update))
            telegramBot.send_message(f"Daily protocol: {len(scripts_to_update)} scripts to update found...")
            telegramBot.send_message("Starting script update process...")
            if update_scripts():
                telegramBot.send_message("Script update process completed, please check the logs and push the changes to the repository if everything is fine.")
            else:
                telegramBot.send_message("Script update process interrupted (initialization or network error). Some scripts may have been updated, the others will be retried at the next run. Please check the logs before pushing anything.")
        else:
            logging.info("Daily protocol: No script to update found...")
        logging.info("Daily protocol completed.")

    elif args[0] == "--help":
        print("Usage:")
        print("  python updater.py                 # Get scripts to update and update them")
        print("  python updater.py --full-update   # Set all scripts to update and update them")
        print("  python updater.py --update-creators <creator1> <creator2> ...  # Set all scripts of specified creators to update and update them")
        print("  python updater.py --get-scripts-to-update  # Only get scripts to update")
        print("  python updater.py --update-scripts   # Only update scripts")
        print("  python updater.py --daily-protocol  # Get scripts to update and update them if any")
        print("  python updater.py --help           # Show this help message")

    else:
        logging.error("Unknown argument: %s", args[0])
        sys.exit(1)
