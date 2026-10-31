# Import modules
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime
import os

#TODO: Add tournament filtering
#TODO: Add tournament creation
#TODO: Add tournament registration
#TODO: Add waitlist functionality
#TODO: Add ability for user to see list of owned tournaments
#TODO: Add dashboard for tournament that shows matches, registrations, and waitlist
#TODO: Add tournament functionality
#TODO: Polish frontend interface

#TODO: DASHBOARD
    # Lets users see tournaments they're in
    # Lets users see tournaments they own
    # Subpage: Tournament-specific dashboard
        # Shows matchs, registrations, waitlist
        # Lets host edit tournament details
        # Lets host change user positions
        # Lets host declare match winner

# Constant variables used for database functions
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # Folder this file is in, so the database is found no matter where the server is started from
ENTRY_PER_PAGE = 2.0 # How many database entries will appear on each page of the list

# Initialize app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = '1uBu3qG7XwkiUzX98V_a0pCYumvPRYD70Dq5OG9unAw'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)
CORS(app, supports_credentials=True, allow_headers=["Authorization", "Content-Type"])
jwt = JWTManager(app)

# FUNCTIONS

# Function for quickly setting up database connection
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
        values.append(args.get('game'))

    if args.get('skill_level'):
        conditions.append('skill_level = ?')
        values.append(args.get('skill_level'))    

    # Only show tournaments that are still taking registrations
    if args.get('open') == 'true':
        conditions.append("deadline > datetime('now', 'localtime')")

    if not conditions:
        return '', values

    return 'WHERE ' + ' AND '.join(conditions), values

# Function for converting a database query into a list of dictionaries
def get_results(query):
    return [dict(entry) for entry in query]

# USER AUTHENTICATION APIS

# Handles signing up a new user
@app.route('/api/signup', methods=['POST'])
@jwt_required(True)
def signup():
    # Check if user is already signed in
    current_user = get_jwt_identity()
    if current_user != None:
        return {'success': False, 'msg': 'You are already signed in.'}

    # Connect to database
    connection = get_connection()
    cursor = connection.cursor()

    # Get form data
    username = request.form.get('username')
    password = request.form.get('password')

    # Check if account exists, do not proceed if it does
    cursor.execute("SELECT username FROM Users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user:
        return {'success': False, 'msg': 'Username is already taken.'}

    # Create new account if user doesn't exist
    password_hash = generate_password_hash(password)
    cursor.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password_hash))
    connection.commit()
    connection.close()

    return {'success': True}

# Handles logging in users
@app.route('/api/login', methods=['POST'])
@jwt_required(True)
def login():
    # Check if user is already signed in
    current_user = get_jwt_identity()
    if current_user != None:
        return {'success': False, 'msg': 'You are already signed in.'}

    # Connect to database
    connection = get_connection()
    cursor = connection.cursor()

    # Get form data
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Attempt to get user
    cursor.execute("SELECT user_id, username, password FROM Users WHERE username = ?", (username,))
    user = cursor.fetchone()

    # Check if user exists and password is correct.
    if user and check_password_hash(user['password'], password):
        # Creates a token tied to this user and send it to the frontend.
        # Frontend will store this token in localstorage.
        access_token = create_access_token(identity=str(user['user_id']))
        return {'success': True, 'access_token': access_token}

    connection.close()
    # Login failed. Return false so frontend can respond appropriately.
    return {'success': False, 'msg': 'Invalid username or password.'}

@jwt.token_in_blocklist_loader
def check_blocklist(jwt_header, jwt_payload):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT token FROM Blocked_Tokens WHERE token = ?', (jwt_payload['jti'],))
    token = cursor.fetchone()
    connection.close()

    if token:
        return True
    return False

@app.route('/api/logout', methods=['GET'])
@jwt_required()
def logout():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Blocked_Tokens (token) VALUES (?)', (get_jwt()['jti'],))
    connection.commit()
    connection.close()
    return {'success': True}

# TOURNAMENT CREATION [EDIT?] [REMOVE?]
@app.route('/api/create_tournament', methods=['POST'])
def create_tournament():
    # Get form data
    # Create tournament with data and insert into database
    pass

# TOURNAMENT GETTERS

# Gets a page of tournaments from database and returns them.
# Implement filters [sort-by?]
@app.route('/api/get_tournaments/<int:page>')
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
    results = get_results(cursor.fetchall())

    # Close connection
    connection.close()

    # Convert results into a JSON string and send it back to frontend
    return jsonify(results)

# Gets every option the filter dropdowns can use, based on what's in the database
@app.route("/api/get_filter_options")
def get_filter_options():
    connection = get_connection()
    cursor = connection.cursor()
    
    games = [row['game'] for row in cursor.execute('SELECT DISTINCT game FROM Tournament ORDER BY game;')]
    skill_levels = [row['skill_level'] for row in cursor.execute('SELECT DISTINCT skill_level FROM Tournament ORDER BY skill_level;')]
    
    connection.close()
    
    return jsonify({'games': games, 'skill_levels': skill_levels})

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
    return jsonify(dict(result))


@app.route('/api/get_joined_tournaments')
@jwt_required()
def get_joined(): # UNTESTED
     # Get id of user
    current_user = int(get_jwt_identity())

    # Query database for every tournament the user is in
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute('''SELECT Tournament.*, Participants.status FROM Participants INNER JOIN Tournament
        ON Participants.user_id = ? AND Participants.tournament_id = Tournament.tournament_id
    ''', (current_user,))
    results = get_results(cursor.fetchall())
    connection.close()

    # Convert to json string and send to requester
    return jsonify(results), 200
    

@app.route('/api/get_owned_tournaments')
@jwt_required()
def get_owned():
    # Get id of user
    current_user = int(get_jwt_identity())

    # Query database for all tournaments containing an identical host_id
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Tournament WHERE host_user_id = ? ORDER BY tournament_id DESC", (current_user,))
    results = get_results(cursor.fetchall())
    connection.close()

    # Convert to json string and send to requester
    return jsonify(results), 200

# DASHBOARD ROUTES

@app.route('/api/get_dashboard_data/<int:tournament_id>')
@jwt_required()
def get_dashboard(tournament_id):
    # Connect to database
    connection = get_connection()
    cursor = connection.cursor()

    # Get user
    current_user = int(get_jwt_identity())

    # Get tournament from id and host id
    cursor.execute("SELECT * FROM Tournament WHERE tournament_id = ? AND host_user_id = ?", (tournament_id, current_user))
    tournament = cursor.fetchone()

    # Throw an error if unable to fetch tournament (usually means the tournament doesn't belong to user)
    if not tournament:
        return {'success': False}

    # Fetch participants

    # Fetch matches

    # Merge all data and return to client
    return 'DATA'


##############################
if __name__ == '__main__':
    app.run(debug=True)
##############################