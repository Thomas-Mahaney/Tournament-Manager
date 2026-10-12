from flask import Flask
from flask_cors import CORS
import sqlite3

app = Flask(__name__)

@app.route("/")
def main():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(debug=True)