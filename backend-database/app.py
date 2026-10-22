# Import modules
from flask import Flask, json, request
from flask_cors import CORS
import sqlite3
from classes import User, Tournament

# Initialize app
app = Flask(__name__)
CORS(app)

# Hardcoded tournament classes for testing purposes!
# In the future, tournaments will be stored in database, then constructed into class using database entries.
events = []
for i in range(5):
    new = Tournament(i, "Tournament" + str(i), "test", "game", "location", "starttime", "deadline", "beginner", 20)
    events.append(new)

# Default route. Can probably remove later.
@app.route("/")
def main():
    return "Hello, World!"

@app.route("/api/test", methods=['POST'])
def api_test():
    data = request.form

    if data.get('username') == "user" and data.get('password') == '1234':
        return {'success': True}
    return {'success': False}

# Loads and gets tournaments. Will probably add page functionality later so we don't get everything.
@app.route("/api/get_tournaments")
def get_tournaments():
    return json.dumps([e.__dict__ for e in events])

if __name__ == '__main__':
    app.run(debug=True)