# This file is here purely for testing purposes with the database.
# Currently using it to create the Tournament table (if it's not already up) and some dummy entries
# This file doesn't interact with app.py, just the database it will interact with.

import sqlite3

conn = sqlite3.connect('test_database.db')
c = conn.cursor()

# Creates Tournament table [only if it's not present in database]
c.execute('''CREATE TABLE IF NOT EXISTS Tournament (
    tournament_id INTEGER PRIMARY KEY,
    host_user_id INT NOT NULL,
    title TEXT NOT NULL,
    game TEXT NOT NULL,
    description TEXT,
    skill_level TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    deadline DATETIME NOT NULL,
    location TEXT,
    player_cap INT NOT NULL
);''')

c.execute('''CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);''')

# Creates 4 dummy entries into table that can be used for testing.
#c.execute('''INSERT INTO Tournament (host_user_id, title, game, description, skill_level, start_time, deadline, location, player_cap) VALUES
#(0, 'Tournament 1', 'Game', 'Example Description', 'Beginner', '2026-10-22 00:00:00', '2026-10-29 12:00:00', 'Earth', 10),
#(0, 'Tournament 2', 'Dame', 'Description Example', 'Beginner', '2026-10-22 00:00:00', '2026-10-29 12:00:00', 'Mercury', 5),
#(0, 'Tournament 3', 'Lame', 'Description Description', 'Intermediate', '2026-10-22 00:00:00', '2026-10-29 12:00:00', 'Venus', 12),
#(0, 'Tournament 4', 'Same', 'Example Example', 'Expert', '2026-10-22 00:00:00', '2026-10-29 12:00:00', 'Mars', 26);
#''')

conn.commit()
conn.close()