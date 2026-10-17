from flask import Flask
from flask_cors import CORS
import sqlite3

app = Flask(__name__)

@app.route("/")
def main():
    return "Hello, World!"

@app.route("/login")
def login():
    return "Login Page"

@app.route("/user/<str:username>")
def user_profile(username):
    return f"User Profile for {username}"

@app.route("/event/<int:event_id>")
def event_details(event_id):
    return f"Event Details for Event ID: {event_id}"

if __name__ == '__main__':
    app.run(debug=True)