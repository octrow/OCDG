# data_access.py
import sqlite3

class Database:
    def __init__(self, db_name="commits.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS commits
                     (hash text PRIMARY KEY, author text, date text, message text, status boolean)''')
        print("Created commits table")

    def update_commit(self, commit):
        self.cursor.execute("UPDATE commits SET message = ?, status = ? WHERE hash = ?",
                            (commit.message, commit.status, commit.hash))
        self.conn.commit()
