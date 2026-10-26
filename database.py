import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
''')

c.execute("INSERT INTO users (username, password) VALUES ('admin', '1234')")

conn.commit()
conn.close()

print("Database created")