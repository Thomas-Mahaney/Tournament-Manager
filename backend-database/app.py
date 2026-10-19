from flask import Flask
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

@app.route("/")
def main():
    return "Hello, World!"

@app.route("/api/test")
def api_test():
    return "hi!"

if __name__ == '__main__':
    app.run(debug=True)