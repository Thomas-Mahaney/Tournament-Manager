# Import modules
from flask import Flask, json
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

# Basic test route for frontend backend communication. Will be removed later.
@app.route("/api/test")
def api_test():
    return "hi!"

# Loads and gets tournaments. Will probably add page functionality later so we don't get everything.
@app.route("/api/get_tournaments")
def get_tournaments():
    return json.dumps([e.__dict__ for e in events])

if __name__ == '__main__':
    app.run(debug=True)