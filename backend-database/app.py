from flask import Flask, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

@app.route("/")
def main():
    return "Hello, World!"

@app.route("/api/test", methods=['POST'])
def api_test():
    data = request.form

    if data.get('username') == "pee" and data.get('password') == '1234':
        return {'success': True}
    return {'success': False}

if __name__ == '__main__':
    app.run(debug=True)