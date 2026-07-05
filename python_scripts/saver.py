import sqlite3
import gspread
from google.oauth2.service_account import Credentials
from tokens import *
import os

class Saver:

    def __init__(self, db_path="data/pynumstore.db"):
        self.conn = sqlite3.connect(db_path)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def insert_creator(self, creator, data={}):
        keys = " name,"
        values = (creator, )
        text = "?, "
        for key in data.keys():
            keys += f" {key},"
            values += (data[key],)
            text += "?, "
        self.conn.execute(
            f"""
            INSERT INTO creators ({keys[:-1]})
            VALUES ({text[:-2]})
            """,
            values 
        )

    def insert_script(self, creator, name, data={}):
        keys = "creator, name,"
        values = (creator, name)
        text = "?, ?, "
        for key in data.keys():
            keys += f" {key},"
            values += (data[key],)
            text += "?, "
        self.conn.execute(
            f"""
            INSERT INTO scripts ({keys[:-1]})
            VALUES ({text[:-2]})
            """,
            values 
        )

    def update_creator_data(self, creator, data):
        keys = ""
        values = ()
        for key in data.keys():
            keys += f" {key} = ?,"
            values += (data[key],)
        self.conn.execute(
            f"""
            UPDATE creators
            SET {keys[:-1]}
            WHERE name = ?
            """,
            values + (creator,)
        )

    def update_script_data(self, creator, name, data):
        keys = ""
        values = ()
        for key in data.keys():
            keys += f" {key} = ?,"
            values += (data[key],)
        self.conn.execute(
            f"""
            UPDATE scripts
            SET {keys[:-1]}
            WHERE creator = ? AND name = ?
            """,
            values + (creator, name)
        )

    def delete_creator(self, creator):
        self.conn.execute(
            "DELETE FROM creators WHERE name = ?",
            (creator,)
        )
        scripts = self.conn.execute(
            "SELECT name FROM scripts WHERE creator = ?",
            (creator,)
        ).fetchall()
        for script in scripts:
            self.delete_thumbnail(creator, script[0])
        self.conn.execute(
            "DELETE FROM scripts WHERE creator = ?",
            (creator,)
        )

    def delete_script(self, creator, name):
        self.delete_thumbnail(creator, name)
        self.conn.execute(
            "DELETE FROM scripts WHERE creator = ? AND name = ?",
            (creator, name)
        )

    def get_creator_hash(self, creator):
        row = self.conn.execute(
            "SELECT body_hash FROM creators WHERE name = ?",
            (creator,)
        ).fetchone()

        return row[0] if row else None
    
    def get_scripts_list(self, creator):
        row = self.conn.execute(
            "SELECT name FROM scripts WHERE creator = ?",
            (creator,)
        ).fetchall()

        return [r[0] for r in row]

    def get_script_hash(self, creator, name):
        row = self.conn.execute(
            "SELECT body_hash FROM scripts WHERE creator = ? AND name = ?",
            (creator, name)
        ).fetchone()

        return row[0] if row else None

    def creator_exists(self, creator):
        row = self.conn.execute(
            "SELECT body_hash FROM creator WHERE name = ?",
            (creator,)
        ).fetchone()

        return row != None
    
    def script_exists(self, creator, name):
        row = self.conn.execute(
            "SELECT body_hash FROM scripts WHERE creator = ? AND name = ?",
            (creator, name)
        ).fetchone()

        return row != None
    
    def get_creators_db(self):
        row = self.conn.execute("SELECT name FROM creators").fetchall()
        return [r[0] for r in row]
    
    def get_creators_as(self):

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
    
    def set_creators_as(self, creators):
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
    
    def delete_thumbnail(self, creator, name):
        try:
            os.remove(f"data/thumbnails/{creator}_{name}.png")
        except FileNotFoundError:
            pass
    
    def update_creator_hash(self, creator, hash):
        self.conn.execute(
            "UPDATE creators SET body_hash = ? WHERE name = ?",
            (hash, creator)
        )