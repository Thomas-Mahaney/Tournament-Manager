# Import modules
from flask import Flask, json, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime

#TODO: Add tournament filtering
#TODO: Add registration
#TODO: Add tournament creation
#TODO: Add list of tournaments owned by user that they can view
#TODO: Add dashboard for tournament that shows matches, registrations, and waitlist
#TODO: Add tournament functionality
#TODO: Add manual logout
#TODO: Polish frontend interface

# Constant variables used for database functions
DATABASE_NAME = 'test_database.db' # Name of the database the program will interact with
ENTRY_PER_PAGE = 2.0 # How many database entries will appear on each page of the list

# Initialize app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = '1uBu3qG7XwkiUzX98V_a0pCYumvPRYD70Dq5OG9unAw'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=2)
CORS(app, supports_credentials=True, allow_headers=["Authorization", "Content-Type"])
jwt = JWTManager(app)

# Function for quickly setting up database connection
def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection

# Function for converting a database query into a list of dictionaries
def get_results(query):
    return [dict(entry) for entry in query]

# Handles signing up a new user
@app.route('/api/signup', methods=['POST'])
@jwt_required(True)
def signup():
    # Check if user is already signed in
    current_user = get_jwt_identity()
    if current_user == None:
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
    if current_user == None:
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
    if user and check_password_hash(user['password'], password):\
        # Creates a token tied to this user and send it to the frontend.
        # Frontend will store this token in localstorage.
        access_token = create_access_token(identity=str(user['user_id']))
        return {'success': True, 'access_token': access_token}
    
    # Login failed. Return false so frontend can respond appropriately.
    return {'success': False, 'msg': 'Invalid username or password.'}

@app.route('/api/get_owned_tournaments')
@jwt_required()
def get_owned():
    # Get id of user
    current_user = int(get_jwt_identity())
    print(current_user)

    # Query database for all tournaments containing an identical host_id
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Tournament WHERE host_user_id = ? ORDER BY tournament_id DESC", (current_user,))
    results = get_results(cursor.fetchall())

    # Convert to json string and send to requester
    return json.dumps(results)

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

# Gets a page of tournaments from database and returns them.
# Implement filters [sort-by?]
@app.route('/api/get_tournaments/<int:page>')
def get_tournaments(page):
    # Connect to database
    connection = get_connection()
    cursor = connection.cursor()

    # Query current page of tournaments
    cursor.execute('''
        SELECT title, game, description, skill_level, location, start_time, deadline, player_cap
        FROM Tournament 
        ORDER BY tournament_id DESC
        LIMIT ? OFFSET ?;
    ''', (ENTRY_PER_PAGE, ENTRY_PER_PAGE * (page - 1)))

    # Get all results and convert them into a list of dictionaries
    results = get_results(cursor.fetchall())

    # close connection
    connection.close()

    # Convert results into a JSON string and send it back to frontend
    return json.dumps(results)

if __name__ == '__main__':
    app.run(debug=True)