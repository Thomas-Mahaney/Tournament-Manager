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

# Build a WHERE clause from the filters given in the url
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
@app.route("/api/get_tournaments/<int:page>")
def get_tournaments(page):
    # Connect to database
    connection = get_connection()
    cursor = connection.cursor()
    
    # Query current page of tournaments
    where, values = build_filters(request.args)
    cursor.execute('''
        SELECT tournament_id, title, game, description, skill_level, location, start_time, deadline, player_cap
        FROM Tournament
        ''' + where + '''
        ORDER BY tournament_id DESC
        LIMIT ? OFFSET ?;
    ''', values + [ENTRY_PER_PAGE, ENTRY_PER_PAGE * (page - 1)])
    
    # Get all results and convert them into a list of dictionaries
    results = [dict(entry) for entry in cursor.fetchall()]

    # Close connection
    connection.close()

    # Convert results into a JSON string and send it back to frontend
    return json.dumps(results)

# Gets every option the filter dropdowns can use, based on what's in the database
@app.route("/api/get_filter_options")
def get_filter_options():
    connection = get_connection()
    cursor = connection.cursor()
    
    games = [row['game'] for row in cursor.execute('SELECT DISTINCT game FROM Tournament ORDER BY game;')]
    skill_levels = [row['skill_level'] for row in cursor.execute('SELECT DISTINCT skill_level FROM Tournament ORDER BY skill_level;')]
    
    connection.close()
    
    return json.dumps({'games': games, 'skill_levels': skill_levels})

# Gets all details for a single tournament. Used by the tournament viewer page.
@app.route("/api/get_tournament/<int:tournament_id>")
def get_tournament(tournament_id):
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT tournament_id, title, game, description, skill_level, location, start_time, deadline, player_cap
        FROM Tournament
        WHERE tournament_id = ?;
    ''', (tournament_id,))
    result = cursor.fetchone()
    
    connection.close()

    #Send back a 404 if no tournament has that id
    if result is None:
        return {'error': 'Tournament not found'}, 404
    return json.dumps(dict(result))

# Changes to the backend
#   1. get_tournaments() now applies the filters and also returns tournament_id, so the list can link to each tournament
#   2. get_filter_options() fills the dropdown menus
#   3. get_tournament() returns a single tournament
#   4. get_connection() keeps the connection code in one place, and makes it easy to change values later (I think)



# I don't want to delete this function yet, but it is redundant with the new additions above since it's the same but without the filters. 
# It can be safely removed once the frontend is updated to use the new functions
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