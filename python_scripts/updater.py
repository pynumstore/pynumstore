import json
import time
from saver import Saver
from scanner import Scanner
from reporter import Reporter
import tqdm

class Updater:
    
    def update(self):
        print(f"Starting update at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
        self.saver = Saver()
        self.scanner = Scanner()
        self.reporter = Reporter()
        try:
            self.reporter.start_update()
            creators_db = self.saver.get_creators_db()
            creators_as = self.saver.get_creators_as()
            print(f"Checking {len(creators_as)} creators...")
            creators_to_check, creators_to_insert = self.get_creators_to_check_and_insert(creators_db, creators_as)
            creators_to_update, creators_to_delete, creators_unchanged = self.check_creators(creators_to_check)
            print(f"{len(creators_to_insert)} new creators found:")
            for creator in creators_to_insert:
                print(f"  - {creator}")
            print(f"{len(creators_to_delete)} creators deleted:")
            for creator in creators_to_delete:
                print(f"  - {creator}")
            print(f"{len(creators_unchanged)} creators unchanged.")
            print(f"Getting scripts for {len(creators_to_update)} creators...")
            scripts_ws_to_check = []
            scripts_db_to_check = []
            for creator in tqdm.tqdm(creators_to_update):
                scripts, comment = self.scanner.full_creator_scan(creator)
                if scripts is not None:
                    scripts_ws_to_check += [[creator, script] for script in scripts]
                scripts = self.saver.get_scripts_list(creator)
                if scripts is not None:
                    scripts_db_to_check += [[creator, script] for script in scripts]
                hash, comment = self.scanner.get_creator_hash(creator)
                if hash is not None:
                    self.saver.update_creator_hash(creator, hash)
            scripts_to_insert, scripts_to_delete, scripts_to_check = self.compare_scripts_lists(scripts_ws_to_check, scripts_db_to_check)
            self.delete_scripts(scripts_to_delete)
            print(f"{len(scripts_to_insert)} new scripts found:")
            for script in scripts_to_insert:
                print(f"  - {script[0]}/{script[1]}")
            print(f"{len(scripts_to_delete)} scripts deleted:")
            for script in scripts_to_delete:
                print(f"  - {script[0]}/{script[1]}")
            print(f"{len(scripts_to_check)+len(scripts_to_insert)} scripts found.")
            print(f"Checking {len(scripts_to_check)+len(scripts_to_insert)} scripts...")
            scripts_to_update = self.check_scripts(scripts_to_check) + self.insert_scripts(scripts_to_insert)
            print(f"Updating {len(scripts_to_update)} scripts...")
            self.update_scripts(scripts_to_update)
            self.saver.commit()
            self.saver.set_creators_as(self.saver.get_creators_db())
            self.saver.close()
            self.scanner.close()
            self.reporter.generate_and_send_report(
                "update",
                creators_to_check,
                creators_to_insert,
                creators_to_delete,
                creators_unchanged,
                creators_to_update,
                scripts_to_check,
                scripts_to_insert,
                scripts_to_delete,
                scripts_to_update
            )
            self.reporter.end_update()
            print(f"Update complete at {time.strftime('%Y-%m-%d %H:%M:%S')}.")
        except Exception as e:
            self.saver.close()
            self.scanner.close()
            self.reporter.end_update()
            self.reporter.end_update()
            self.reporter.send_error(e)
            raise e
    
    def creator_update(self, creators_to_update):
        print(f"Starting an creator update at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
        self.saver = Saver()
        self.scanner = Scanner()
        self.reporter = Reporter()
        try:
            self.reporter.start_update(type="creator_update")
            print(f"Updating {len(creators_to_update)} creators...")
            scripts_to_update = []
            for creator in tqdm.tqdm(creators_to_update):
                scripts, comment = self.scanner.full_creator_scan(creator)
                hash, comment = self.scanner.get_creator_hash(creator)
                if hash is not None:
                    self.saver.update_creator_data(creator, {"body_hash": hash})
                if scripts is not None:
                    scripts_to_update += [[creator, script] for script in scripts]
            print(f"Found {len(scripts_to_update)} scripts to update.")
            print(f"Updating {len(scripts_to_update)} scripts...")
            self.update_scripts(scripts_to_update)
            self.saver.commit()
            self.saver.close()
            self.scanner.close()
            self.reporter.generate_and_send_report("creator_update", creators_to_update, scripts_to_update)
            self.reporter.end_update(type="creator_update")
            print(f"Update complete at {time.strftime('%Y-%m-%d %H:%M:%S')}.")
        except Exception as e:
            self.saver.close()
            self.scanner.close()
            self.reporter.end_update(type="creator_update")
            self.reporter.send_error(e)
            raise e
    
    def full_update(self):
        print(f"Starting a full update at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
        self.saver = Saver()
        self.scanner = Scanner()
        self.reporter = Reporter()
        try:
            self.reporter.start_update(type="full_update")
            creators_db = self.saver.get_creators_db()
            print(f"Updating {len(creators_db)} creators...")
            scripts_to_update = []
            for creator in tqdm.tqdm(creators_db):
                scripts, comment = self.scanner.full_creator_scan(creator)
                hash, comment = self.scanner.get_creator_hash(creator)
                if hash is not None:
                    self.saver.update_creator_data(creator, {"body_hash": hash})
                if scripts is not None:
                    scripts_to_update += [[creator, script] for script in scripts]
            print(f"Found {len(scripts_to_update)} scripts to update.")
            print(f"Updating {len(scripts_to_update)} scripts...")
            self.update_scripts(scripts_to_update)
            self.saver.commit()
            self.saver.close()
            self.scanner.close()
            self.reporter.generate_and_send_report("full_update", creators_db, scripts_to_update)
            self.reporter.end_update(type="full_update")
            print(f"Update complete at {time.strftime('%Y-%m-%d %H:%M:%S')}.")
        except Exception as e:
            self.saver.close()
            self.scanner.close()
            self.reporter.end_update(type="full_update")
            self.reporter.send_error(e)
            raise e
    
    def get_creators_to_check_and_insert(self, creators_db, creators_as):
        creators_to_insert = []
        for creator_as in creators_as:
            if not creator_as in creators_db:
                self.saver.insert_creator(creator_as)
                creators_to_insert.append(creator_as)
        return creators_as, creators_to_insert
    
    def check_creators(self, creators_to_check):
        creators_to_update = []
        creators_to_delete = []
        creators_unchanged = []
        for creator in tqdm.tqdm(creators_to_check):
            creator_db_hash = self.saver.get_creator_hash(creator)
            creator_ws_hash, comment = self.scanner.get_creator_hash(creator)
            if creator_ws_hash is None:
                self.saver.delete_creator(creator)
                creators_to_delete.append(creator)
            elif creator_db_hash != creator_ws_hash:
                creators_to_update.append(creator)
            else:
                creators_unchanged.append(creator)
        return creators_to_update, creators_to_delete, creators_unchanged
    
    def compare_scripts_lists(self, scripts_ws_to_check, scripts_db_to_check):
        scripts_to_insert = []
        scripts_to_delete = []
        scripts_to_check = []
        for script in scripts_ws_to_check:
            if not script in scripts_db_to_check:
                scripts_to_insert.append(script)
        for script in scripts_db_to_check:
            if not script in scripts_ws_to_check:
                scripts_to_delete.append(script)
        for script in scripts_db_to_check + scripts_ws_to_check:
            if not script in scripts_to_check and not script in scripts_to_insert and not script in scripts_to_delete:
                scripts_to_check.append(script)
        return scripts_to_insert, scripts_to_delete, scripts_to_check
    
    def check_scripts(self, scripts_to_check):
        scripts_to_update = []
        for script in tqdm.tqdm(scripts_to_check):
            script_db_hash = self.saver.get_script_hash(script[0], script[1])
            script_ws_hash, comment = self.scanner.get_script_hash(script[0], script[1])
            if script_ws_hash is None:
                self.saver.delete_script(script[0], script[1])
            elif script_db_hash is None:
                self.saver.insert_script(script[0], script[1])
            elif script_db_hash != script_ws_hash:
                scripts_to_update.append(script)
            else:
                continue
        return scripts_to_update
    
    def delete_scripts(self, scripts_to_delete):
        for script in tqdm.tqdm(scripts_to_delete):
            self.saver.delete_script(script[0], script[1])
    
    def insert_scripts(self, scripts_to_insert):
        for script in scripts_to_insert:
            self.saver.insert_script(script[0], script[1])
        return scripts_to_insert
    
    def update_scripts(self, scripts_to_update):
        for script in tqdm.tqdm(scripts_to_update):
            data, comment = self.scanner.full_script_scan(script[0], script[1])
            hash, comment = self.scanner.get_script_hash(script[0], script[1])
            if data is not None and hash is not None:
                data["body_hash"] = hash
                self.saver.update_script_data(script[0], script[1], data)


if __name__ == "__main__":
    updater = Updater()
    updater.update()