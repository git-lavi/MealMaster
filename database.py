import sqlite3

# DB
def connect_to_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    return conn, cursor


def commit_close_db(conn: sqlite3.Connection):
    conn.commit()
    conn.close()
