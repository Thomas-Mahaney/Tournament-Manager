# Import modules
from flask import Flask, json, request
from flask_cors import CORS
from flask_praetorian import Praetorian, auth_required
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# Constant variables used for database functions
DATABASE_NAME = 'test_database.db' # Name of the database the program will interact with
ENTRY_PER_PAGE = 2.0 # How many database entries will appear on each page of the list

# Initialize app
app = Flask(__name__)
guard = Praetorian()
CORS(app)

class User():
    id = 1

# Test api route. Currently used for our mockup login. Will be replaced with proper login api later.
@app.route('/api/test', methods=['POST'])
def api_test():
    data = request.form

    if data.get('username') == "user" and data.get('password') == '1234':
        return {'success': True}
    return {'success': False}

@app.route('/api/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User()
    if username == 'user' and password == '1234':
        token = guard.encode_jwt_token(user)
        return {'success': True}
    return {'success': False}

@app.route('/api/protected', methods=['GET'])
@auth_required

# 
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