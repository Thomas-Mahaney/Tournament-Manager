# Import modules
from flask import Flask, json, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime

# Constant variables used for database functions
DATABASE_NAME = 'test_database.db' # Name of the database the program will interact with
ENTRY_PER_PAGE = 2.0 # How many database entries will appear on each page of the list

# Initialize app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = '1uBu3qG7XwkiUzX98V_a0pCYumvPRYD70Dq5OG9unAw'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(seconds=10)
app.config['JWT_TOKEN_LOCATION'] = ["headers", "cookies"]
CORS(app, supports_credentials=True, allow_headers=["Authorization", "Content-Type"])
jwt = JWTManager(app)

@app.route('/api/signup', methods=['POST'])
def signup():
    # Connect to database
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Get form data
    username = request.form.get('username')
    password = request.form.get('password')

    # Check if account exists
    cursor.execute("SELECT username FROM Users WHERE username = ?", (username,))
    user = cursor.fetchone()

    # Return if account exists
    if user:
        return {'success': False}

    # Create new account
    password_hash = generate_password_hash(password)
    cursor.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password_hash))
    connection.commit()
    connection.close()

    return {'success': True}

# Will update these 2 later. Placeholder.
@app.route('/api/login', methods=['POST'])
def login():
    # Get form data
    # Check if account exists
    # If so, create access token

    username = request.form.get('username')
    password = request.form.get('password')

    if username == 'user' and password == '1234':
        access_token = create_access_token(identity=username)
        response = jsonify({'success': True, 'access-token': access_token})
        return response, 200
    return {'success': False}

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return f'Logged in as {current_user}'

# Gets a page of tournaments from database and returns them.
@app.route('/api/get_tournaments/<int:page>')
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