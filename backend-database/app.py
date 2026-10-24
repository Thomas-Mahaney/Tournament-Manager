# Import modules
from flask import Flask, json, request
from flask_cors import CORS
import sqlite3
from classes import User, Tournament # Currently unused, will likely be changed over time

# Initialize app
app = Flask(__name__)
CORS(app)

# Constant variables used for database functions
DATABASE_NAME = 'test_database.db' # Name of the database the program will interact with
ENTRY_PER_PAGE = 2.0 # How many database entries will appear on each page of the list

# TEMPORARY. Creates dummy tournament classes to be shown in list.
events = []
for i in range(5):
    new = Tournament(i, "Tournament" + str(i), "test", "game", "location", "starttime", "deadline", "beginner", 20)
    events.append(new)

# Default route. Can probably remove later.
@app.route("/")
def main():
    return "Hello, World!"

# Test api route. Currently used for our mockup login. Will be replaced with proper login api later.
@app.route("/api/test", methods=['POST'])
def api_test():
    data = request.form

    if data.get('username') == "user" and data.get('password') == '1234':
        return {'success': True}
    return {'success': False}

# 
@app.route("/api/get_tournaments/<int:page>")
def get_tournaments(page):
    # Connect to database
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Query current page of tournaments
    cursor.execute('''
        SELECT title, game, description, skill_level, location, start_time, deadline, player_cap
        FROM Tournament 
        ORDER BY tournament_id DESC
        LIMIT ? OFFSET ?;
    ''', (ENTRY_PER_PAGE, ENTRY_PER_PAGE * (page - 1)))

    # Get all results and convert them into a list of dictionaries
    results = [dict(entry) for entry in cursor.fetchall()]

    # close connection
    connection.close()

    # Convert results into a JSON string and send it back to frontend
    return json.dumps(results)

if __name__ == '__main__':
    app.run(debug=True)