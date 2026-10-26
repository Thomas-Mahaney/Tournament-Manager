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

# Opens a connection to the database where rows can be accessed like dictionaries
def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection

# Build a 'where' clause from the filters given in the url
# Values are passed separately as ? parameters so user input never ends up inside the SQL itself
def build_filters(args):
    conditions = []
    values = []

    # Search matches anywhere in the title or description
    search = args.get('search', '').strip()
    if search:
        conditions.append('(title LIKE ? OR description LIKE ?)')
        values += ['%' + search + '%', '%' + search + '%']

    # Exact match filters picked from dropdowns
    if args.get('game'):
        conditions.append('game = ?')
        values.append(args.get('game = ?'))

    if args.get('skill_level'):
        conditions.append('skill_level = ?')
        values.append(args.get('skill_level'))    

    # Only show tournaments that are still taking registrations
    if args.get('open') == 'true':
        conditions.append("deadline > datetime('now, 'localtime')")

    if not conditions:
        return '', values

    return 'WHERE ' + ' AND '.join(conditions), values


# Gets a page of tournaments, narrows down by any filters in the url

    # Connect to database

    # Query current page of tournaments

    # Get all results and convert them into a list of dictionaries

    # Close connection

    # Convert results into a JSON string and send it back to frontend

# Gets every option the filter dropdowns can use, based on what's in the database

# Gets all details for a single tournament. Used by the tournament viewer page.

    #Send back a 404 if no tournament has that id




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