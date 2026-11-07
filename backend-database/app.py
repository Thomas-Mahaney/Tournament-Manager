# Import modules
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import contextmanager
from dotenv import load_dotenv
import sqlite3
import datetime
import os
import math

# Load environment variables
load_dotenv()

# Constant variables used for database functions
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # Folder this file is in, so the database is found no matter where the server is started from
DATABASE_NAME = os.path.join(BASE_DIR, 'test_database.db') # Name of the database the program will interact with
ENTRY_PER_PAGE = 5.0 # How many database entries will appear on each page of the list
#Tournament Rules
SKILL_LEVELS = ['Beginner', 'Intermediate', 'Expert'] # Allowed skill levels, in the order dropdowns show them
MIN_PLAYER_CAP = 2
MAX_PLAYER_CAP = 256
TIME_FORMAT = '%Y-%m-%d %H:%M:%S' # How times are stored in the database (local time)
WITHDRAW_CUTOFF_HOURS = 2   # Within this many hours of the start, players can't withdraw and nobody gets promoted

# Ways the tournament lists can be sorted. ORDER BY can't use ? placeholders, so the url only picks a key and these fixed strings are what go into the SQL.
#   'start' puts tournaments that haven't started yet first, soonest first. Ones that already started come last, most recently started first. (Sorting by distance from the current time allows both)
SORT_OPTIONS = {
    'start': "start_time < datetime('now', 'localtime'), ABS(julianday(start_time) - julianday('now', 'localtime')), tournament_id",
    'newest': 'tournament_id DESC',
}
DEFAULT_SORT = 'start'

# Extra columns added to tournament queries: live player counts and when withdrawals close
# WITHDRAW_CUTOFF_HOURS is a number we set ourselves, so putting it into the SQL is safe
REGISTRATION_COLUMNS = f'''
    datetime(Tournament.start_time, '-{WITHDRAW_CUTOFF_HOURS} hours') AS withdraw_cutoff,
    (SELECT COUNT(*) FROM Participants p
        WHERE p.tournament_id = Tournament.tournament_id AND p.status = 'registered') AS registered_count,
    (SELECT COUNT(*) FROM Participants p
        WHERE p.tournament_id = Tournament.tournament_id AND p.status = 'waitlisted') AS waitlist_count
'''

# A waitlisted player's place in line (1 = next to be promoted). Used inside queries where the player's
# Participants row is named "p". Players who signed up at the same instant are ordered by insert order (rowid).
WAITLIST_POSITION = '''
    (SELECT COUNT(*) FROM Participants w
        WHERE w.tournament_id = p.tournament_id AND w.status = 'waitlisted'
        AND (w.registration_time < p.registration_time
             OR (w.registration_time = p.registration_time AND w.rowid <= p.rowid)))
'''

# Initialize app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)
CORS(app, supports_credentials=True, allow_headers=["Authorization", "Content-Type"])
jwt = JWTManager(app)

#################################
# FUNCTIONS
#################################

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

# Picks the ORDER BY for the lists from the "sort" value in the url. Unknown values use the default
def get_order_by(args):
    return SORT_OPTIONS.get(args.get('sort'), SORT_OPTIONS[DEFAULT_SORT])

# Function for converting a database query into a list of dictionaries
def get_results(query):
    return [dict(entry) for entry in query]

# Standard Error Response: a message for the user plus a matching HTTP status code
def fail(msg, status= 400):
    return jsonify({'success': False, 'msg': msg}), status

# Reads a time from a datetime-local input, '2026-11-05T18:00'
def parse_form_time(value):
    try:
        time = datetime.datetime.fromisoformat((value or '').strip())
    except ValueError:
        return None
    return time.replace(second=0, microsecond=0, tzinfo=None)

# Checks the create tournament form. Returns (data, None) if it's valid, or (None, error msg) if not.
def validate_tournament_form(form):
    data = {}

    # Required text fields, with a maximum length for each
    for field, label, max_length in [('title', 'Title', 100), ('game', 'Game', 50), ('skill_level', 'Skill level', 20)]:
        value = (form.get(field) or '').strip()
        if not value:
            return None, label + ' is required.'
        if len(value) > max_length:
            return None, f'{label} must be {max_length} characters or less.'
        data[field] = value

    if data['skill_level'] not in SKILL_LEVELS:
        return None, 'Skill level must be one of: ' + ', '.join(SKILL_LEVELS) + '.'

    # Optional text fields are stored as NULL when left empty, so the frontend shows "TBD"
    for field, label, max_length in [('description', 'Description', 2000), ('location', 'Location', 100)]:
        value = (form.get(field) or '').strip()
        if len(value) > max_length:
            return None, f'{label} must be {max_length} characters or less.'
        data[field] = value or None

    try:
        data['player_cap'] = int(form.get('player_cap', ''))
    except (TypeError, ValueError):
        return None, 'Player cap must be a whole number.'
    if not MIN_PLAYER_CAP <= data['player_cap'] <= MAX_PLAYER_CAP:
        return None, f'Player cap must be between {MIN_PLAYER_CAP} and {MAX_PLAYER_CAP}'

    now = datetime.datetime.now()
    start_time = parse_form_time(form.get('start_time'))
    deadline = parse_form_time(form.get('deadline'))
    if not start_time or not deadline:
        return None, 'Start time and registration deadline must both be valid dates.'
    if start_time <= now:
        return None, 'Start time must be in the future.'
    if deadline <= now:
        return None, 'Registration deadline must be in the future.'
    if deadline > start_time:
        return None, 'Registration deadline must be before the start time.'
    data['start_time'] = start_time.strftime(TIME_FORMAT)
    data['deadline'] = deadline.strftime(TIME_FORMAT)

    return data, None

# Opens a connection for changes that have to happen together (count players, then save).
# BEGIN IMMEDIATE locks the database for writing straight away, so two people grabbing the last
# spot at the same time are handled one after the other. Commits at the end, undoes everything on an error.
# Usage: with write_transaction() as cursor: ...
@contextmanager
def write_transaction():
    connection = get_connection()
    connection.isolation_level = None # We send BEGIN/COMMIT ourselves
    cursor = connection.cursor()
    try:
        cursor.execute('BEGIN IMMEDIATE')
        yield cursor
        cursor.execute('COMMIT')
    except Exception:
        cursor.execute('ROLLBACK')
        raise
    finally:
        connection.close()

# Converts a time from the database ("YYYY-MM-DD HH:MM:SS") into a datetime
def from_db_time(text):
    return datetime.datetime.strptime(text[:19], TIME_FORMAT)

# The moment withdrawals (and waitlist promotions) stop for a tournament
def withdraw_cutoff(tournament):
    return from_db_time(tournament['start_time']) - datetime.timedelta(hours=WITHDRAW_CUTOFF_HOURS)

# Gets the raw tournament row, or None if it doesn't exist
def get_tournament_row(cursor, tournament_id):
    cursor.execute('SELECT * FROM Tournament WHERE tournament_id = ?', (tournament_id,))
    return cursor.fetchone()

# How many players are confirmed for a tournament
def count_registered(cursor, tournament_id):
    cursor.execute("SELECT COUNT(*) FROM Participants WHERE tournament_id = ? AND status = 'registered'", (tournament_id,))
    return cursor.fetchone()[0]

# A user's place on a tournament's waitlist
def waitlist_position(cursor, tournament_id, user_id):
    cursor.execute('SELECT ' + WAITLIST_POSITION + ' FROM Participants p WHERE p.tournament_id = ? AND p.user_id = ?',
                   (tournament_id, user_id))
    return cursor.fetchone()[0]

# Fills any open spots with the players who have waited longest.
# Only runs before the withdrawal cutoff. Returns how many players were promoted.
def promote_from_waitlist(cursor, tournament):
    if datetime.datetime.now() >= withdraw_cutoff(tournament):
        return 0

    open_spots = tournament['player_cap'] - count_registered(cursor, tournament['tournament_id'])
    if open_spots <= 0:
        return 0

    cursor.execute('''
        SELECT user_id FROM Participants
        WHERE tournament_id = ? AND status = 'waitlisted'
        ORDER BY registration_time, rowid
        LIMIT ?
    ''', (tournament['tournament_id'], open_spots))
    promoted = [row['user_id'] for row in cursor.fetchall()]

    for user_id in promoted:
        cursor.execute("UPDATE Participants SET status = 'registered' WHERE tournament_id = ? AND user_id = ?",
                       (tournament['tournament_id'], user_id))
        # Add user to a match since they're now registered
        add_to_match(cursor, user_id, tournament['tournament_id'])
    return len(promoted)

# Function that adds a user to the first available match entry in a tournament
def add_to_match(cursor, user_id, tournament_id):
    cursor.execute('''
        UPDATE Matches
        SET player_1_id = CASE WHEN player_1_id IS NULL THEN ? ELSE player_1_id END,
            player_2_id = CASE 
                WHEN player_1_id IS NOT NULL 
                AND player_2_id IS NULL 
                AND accepts_registered = 2 THEN ?
                ELSE player_2_id END
        WHERE match_number = (
            SELECT match_number FROM Matches 
            WHERE tournament_id = ? AND (accepts_registered = 2 AND (player_1_id IS NULL OR player_2_id IS NULL))
            OR (accepts_registered = 1 AND player_1_id IS NULL)
            ORDER BY match_number ASC
            LIMIT 1
        )
    ''', (user_id, user_id, tournament_id))

# Checks if the given user owns the given tournament.
def is_owner(user_id, tournament_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT host_user_id FROM Tournament WHERE tournament_id = ? AND host_user_id = ?",
                   (tournament_id, user_id))
    result = cursor.fetchone()
    connection.close()

    if result:
        return True
    return False

# Checks if user is registered for tournament
def is_in_tournament(user_id, tournament_id):
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT user_id FROM Participants
        WHERE tournament_id = ? 
        AND user_id = ? 
        AND status <> 'withdrawn'
    ''', (tournament_id, user_id))
    result = cursor.fetchone()
    connection.close()
    
    if result:
        return True
    return False

# Withdraws user from tournament.
# Separated from API so it can be used by withdraw and remove_particpant APIs
def withdraw_user(tournament_id, user_id):
    with write_transaction() as cursor:
        tournament = get_tournament_row(cursor, tournament_id)
        if not tournament:
            return fail('Tournament not found.', 404)
        if datetime.datetime.now() >= withdraw_cutoff(tournament):
            return fail(f'Withdrawals close {WITHDRAW_CUTOFF_HOURS} hours before the tournament starts.')

        cursor.execute('SELECT status FROM Participants WHERE tournament_id = ? AND user_id = ?', (tournament_id, user_id))
        existing = cursor.fetchone()
        if not existing or existing['status'] == 'withdrawn':
            return fail('You are not signed up for this tournament.', 409)

        # Keep the row as history instead of deleting it
        cursor.execute("UPDATE Participants SET status = 'withdrawn' WHERE tournament_id = ? AND user_id = ?",
                       (tournament_id, user_id))

        # Remove user from any match they were in
        cursor.execute('''
            UPDATE Matches
            SET player_1_id = CASE WHEN player_1_id = ? THEN NULL ELSE player_1_id END,
                player_2_id = CASE WHEN player_2_id = ? THEN NULL ELSE player_2_id END
            WHERE tournament_id = ?
        ''', (user_id, user_id, tournament_id,))

        # Promotes waitlisted users (and adds them to match if possible)
        promoted = promote_from_waitlist(cursor, tournament)

    return jsonify({'success': True, 'promoted': promoted})

##########################
# USER AUTHENTICATION APIS
##########################

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

@app.route('/api/get_id', methods=['GET'])
@jwt_required()
def get_id():
    user_id = get_jwt_identity()
    return {'id': user_id}

###############################
# TOURNAMENT CREATION
###############################

@app.route('/api/create_tournament', methods=['POST'])
@jwt_required()
def create_tournament():
    # The host is whoever is logged in. Never trust a host id sent from the form
    host_id = int(get_jwt_identity())

    # Check the form, and send back the first problem found
    data, error = validate_tournament_form(request.form)
    if error:
        return fail(error)

    # Do math for match creation
    rounds = math.ceil(math.log2(data['player_cap'])) # number of rounds in tournament
    player_log = (2 ** rounds) # Get next largest power of 2. Used for bye calculation
    pullovers = math.ceil((player_log - data['player_cap']) / 2) # Calculate byes and check how many round 2 matches will pull these leftover players.
    match_count = data['player_cap'] - 1

    # Insert the new tournament
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''
        INSERT INTO Tournament (host_user_id, title, game, description, skill_level, start_time, deadline, location, player_cap)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (host_id, data['title'], data['game'], data['description'], data['skill_level'],
          data['start_time'], data['deadline'], data['location'], data['player_cap']))
    tournament_id = cursor.lastrowid    # This is the id SQLite gave the new row

    # Create match array to store for later use
    matches = []

    # build our match list in reverse (start at the final and work our way back)
    for iteration in range(rounds):
        next_range = 2 ** iteration # How many matches will be in the next iteration
        round_max = match_count - (next_range - 1) # Highest match in the current round. Used to calculate current match.
        current_round = rounds - iteration # The current round.
        
        for until_next_round in range(next_range, 0, -1):
            current_match = round_max - (until_next_round - 1)

            # Skip if match is less than 1 [Usually for byes]
            if current_match < 1:
                continue

            # Check if the current match will accept registered players. If not, then a player can only be added to a match by winning another.
            # Since player counts can sometimes be unequal, we need to sometimes start players at round 2.
            # Accept all matches in round 1 or any match in round 2 that is within the number of pullovers.
            # The given number equals the amount of registered users the match will accept.
            accepts_registered = 0
            if (current_round == 2 and until_next_round <= pullovers) or (current_round == 1):
                if current_round == 2 and until_next_round == pullovers and (data['player_cap'] % 2 == 1):
                    accepts_registered = 1
                else:
                    accepts_registered = 2

            # Gets next match.
            parent_entry = math.floor((len(matches) + 1) / 2)
            next_match = None
            if parent_entry != 0:
                next_match = matches[parent_entry - 1][1]

            # Build match tuple.
            matches.append((tournament_id, current_match, current_round, accepts_registered, next_match))

    # Add matches to database.
    cursor.executemany(("INSERT INTO Matches (tournament_id, match_number, round_number, accepts_registered, next_match) VALUES (?, ?, ?, ?, ?)"), matches)

    # Commit and close connection
    connection.commit()
    connection.close()

    # 201 means "created". The frontend uses the id to open the new tournament's page.
    return jsonify({'success': True, 'tournament_id': tournament_id}), 201

###################################
# TOURNAMENT GETTERS
###################################

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
        SELECT *,
        ''' + REGISTRATION_COLUMNS + '''
        FROM Tournament
        ''' + where + '''
        ORDER BY ''' + get_order_by(request.args) + '''
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
    
    connection.close()
    
    return jsonify({'games': games, 'skill_levels': SKILL_LEVELS})

# Gets all details for a single tournament. Used by the tournament viewer page.
@app.route("/api/get_tournament/<int:tournament_id>")
def get_tournament(tournament_id):
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT *,
        ''' + REGISTRATION_COLUMNS + '''
        FROM Tournament
        WHERE tournament_id = ?;
    ''', (tournament_id,))
    result = cursor.fetchone()
    
    connection.close()

    #Send back a 404 if no tournament has that id
    if result is None:
        return {'error': 'Tournament not found'}, 404
    return jsonify(dict(result))

###################################
# REGISTRATION APIS
###################################

# Signs the logged in user up. Confirmed if there's space, otherwise added to the waitlist.
@app.route('/api/register/<int:tournament_id>', methods=['POST'])
@jwt_required()
def register(tournament_id):
    user_id = int(get_jwt_identity())

    with write_transaction() as cursor:
        tournament = get_tournament_row(cursor, tournament_id)
        if not tournament:
            return fail('Tournament not found.', 404)
        if tournament['host_user_id'] == user_id:
            return fail('Cannot join tournament you own.')
        if datetime.datetime.now() >= from_db_time(tournament['deadline']):
            return fail('Registration for this tournament has closed.')
        
        # A withdrawn row is history, so that user is allowed to sign up again
        cursor.execute('SELECT status FROM Participants WHERE tournament_id = ? AND user_id = ?', (tournament_id, user_id))
        existing = cursor.fetchone()
        if existing and existing['status'] != 'withdrawn':
            return fail('You are already signed up for this tournament.', 409)

        # Counting and saving happen inside the same locked transaction, so the cap can't be overfilled
        if count_registered(cursor, tournament_id) < tournament['player_cap']:
            status = 'registered'
        else:
            status = 'waitlisted'

        # Microseconds keep the waitlist order exact when people sign up in the same second
        signed_up_at = datetime.datetime.now().strftime(TIME_FORMAT + '.%f')
        if existing:
            # Signing up again after withdrawing goes to the back of the line
            cursor.execute('UPDATE Participants SET status = ?, registration_time = ? WHERE tournament_id = ? AND user_id = ?',
                           (status, signed_up_at, tournament_id, user_id))
        else:
            cursor.execute('INSERT INTO Participants (tournament_id, user_id, status, registration_time) VALUES (?, ?, ?, ?)',
                           (tournament_id, user_id, status, signed_up_at))

        position = waitlist_position(cursor, tournament_id, user_id) if status == 'waitlisted' else None

        # Add to tournament match list if registered.
        if status == 'registered':
            add_to_match(cursor, user_id, tournament_id)
        # GET Matches of tournament where accepts_registered is true and at least 1 user slot is empty. Sort by match number ascending.
        # Add user to first match meeting criteria, in whichever slot is empty. 

    return jsonify({'success': True, 'status': status, 'position': position})

# Takes the logged in user out of a tournament (or off its waitlist) and promotes the next waiting player
@app.route('/api/withdraw/<int:tournament_id>', methods=['POST'])
@jwt_required()
def withdraw(tournament_id):
    user_id = int(get_jwt_identity())

    return withdraw_user(tournament_id, user_id)

# The logged in user's status in every tournament they're signed up for (not withdrawn),
# with their waitlist position. The list and viewer pages use this to pick which buttons to show.
@app.route('/api/my_registrations')
@jwt_required()
def my_registrations():
    user_id = int(get_jwt_identity())

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT p.tournament_id, p.status,
            CASE WHEN p.status = 'waitlisted' THEN ''' + WAITLIST_POSITION + ''' END AS position
        FROM Participants p
        WHERE p.user_id = ? AND p.status != 'withdrawn'
    ''', (user_id,))
    results = get_results(cursor.fetchall())
    connection.close()

    return jsonify(results)


@app.route('/api/get_joined_tournaments/<int:page>')
@jwt_required()
def get_joined(page):
     # Get id of user
    current_user = int(get_jwt_identity())

    # Query database for every tournament the user is in
    connection = get_connection()
    cursor = connection.cursor()

    where, values = build_filters(request.args)
    cursor.execute('''SELECT Tournament.*, Participants.status,
    ''' + REGISTRATION_COLUMNS + '''
    FROM Tournament INNER JOIN Participants
    ON Participants.user_id = ? AND Participants.tournament_id = Tournament.tournament_id AND Participants.status <> 'withdrawn'
    ''' + where + '''
    ORDER BY ''' + get_order_by(request.args) + '''
    LIMIT ? OFFSET ?;
    ''', [current_user] + values + [ENTRY_PER_PAGE, ENTRY_PER_PAGE * (page - 1)])
    results = get_results(cursor.fetchall())
    connection.close()

    # Convert to json string and send to requester
    return jsonify(results), 200
    

@app.route('/api/get_owned_tournaments/<int:page>')
@jwt_required()
def get_owned(page):
    # Get id of user
    current_user = int(get_jwt_identity())

    # Connect to database
    connection = get_connection()
    cursor = connection.cursor()
    
    # Query current page of tournaments
    where, values = build_filters(request.args)
    keyword = 'AND'
    if (where == ''):
        keyword = 'WHERE'
    cursor.execute('''
        SELECT *,
        ''' + REGISTRATION_COLUMNS + '''
        FROM Tournament
        ''' + where + keyword + '''
        host_user_id = ? 
        ORDER BY ''' + get_order_by(request.args) + '''
        LIMIT ? OFFSET ?;
    ''', values + [current_user] + [ENTRY_PER_PAGE, ENTRY_PER_PAGE * (page - 1)])
    
    # Get all results and convert them into a list of dictionaries
    results = get_results(cursor.fetchall())

    # Close connection
    connection.close()

    # Convert results into a JSON string and send it back to frontend
    return jsonify(results)



#######################################
# DASHBOARD ROUTES
#######################################

@app.route('/api/get_dashboard_data/<int:tournament_id>')
@jwt_required()
def get_dashboard(tournament_id):
    # Connect to database
    connection = get_connection()
    cursor = connection.cursor()

    # Get user
    current_user = int(get_jwt_identity())

    # Get tournament from id and host id
    cursor.execute('''
        SELECT * FROM Tournament
        WHERE Tournament.tournament_id = ? AND Tournament.host_user_id = ?
    ''', (tournament_id, current_user))
    tournament = cursor.fetchone()

    # Throw an error if unable to fetch tournament (usually means the tournament doesn't belong to user)
    if not tournament:
        return {'success': False, 'msg': 'Tournament not found or you are not the host.'}, 404

    # Fetch all participants
    cursor.execute(''' 
        SELECT Participants.*, Users.username FROM Participants
        JOIN Users ON Participants.user_id = Users.user_id
        WHERE tournament_id = ?
        AND status <> 'withdrawn'
        ORDER BY registration_time ASC
    ''', (tournament_id,))
    participants = get_results(cursor.fetchall())

    # Fetch all matches
    cursor.execute('''
        SELECT * FROM Matches
        WHERE tournament_id = ?
    ''', (tournament_id,))
    matches = get_results(cursor.fetchall())

    # Close connection
    connection.close()

    # Get all the info from the queries
    return jsonify({
        'success': True,
        'tournament': dict(tournament),
        'participants': participants,
        'matches': matches,
    }), 200

# Allows host to declare the winner of a tournament match.
# Only works when the tournament has started.
@app.route('/api/declare_winner/<int:tournament_id>/<int:match_number>/<int:user_id>')
@jwt_required()
def declare_winner(tournament_id, match_number, user_id):
    # Check for ownership
    if not is_owner(int(get_jwt_identity()), tournament_id):
        return {'success': False, 'msg': 'You do not own this tournament.'}
    
    # Check for participant
    if not is_in_tournament(user_id, tournament_id):
        return {'success': False, 'msg': 'User is not in tournament.'}

    # Create connection
    connection = get_connection()
    cursor = connection.cursor()

    # Check if tournament has started
    tournament = get_tournament_row(cursor, tournament_id)
    if datetime.datetime.now() < from_db_time(tournament['start_time']):
        return {'success': False, 'msg': 'Tournament has not started.'}

    # Start transaction
    cursor.execute('BEGIN TRANSACTION')

    # Declare winner for match
    cursor.execute('''
        UPDATE Matches
            SET winner_id = CASE WHEN winner_id IS NULL THEN ? ELSE winner_id END
        WHERE tournament_id = ? AND match_number = ?
    ''', (user_id, tournament_id, match_number))

    # Add winner to next match

    next_match_string = "(SELECT next_match FROM Matches WHERE tournament_id = ? AND match_number = ?)"

    cursor.execute('''
        UPDATE Matches
            SET player_1_id = CASE 
                    WHEN player_1_id IS NULL THEN ?
                    ELSE player_1_id END,
                player_2_id = CASE
                    WHEN player_1_id IS NOT NULL AND player_2_id IS NULL AND player_1_id <> ? THEN ?
                    ELSE player_2_id END
        WHERE match_number = ''' + next_match_string + ''' AND tournament_id = ?
    ''', (user_id, user_id, user_id, tournament_id, match_number, tournament_id))

    # Commit changes
    connection.commit()

    # Get matches to return then close connection
    cursor.execute('''
        SELECT * FROM Matches 
        WHERE tournament_id = ? AND (match_number = ?
        OR match_number = ''' + next_match_string + ''')
    ''', (tournament_id, match_number, tournament_id, match_number))
    results = get_results(cursor.fetchall())
    connection.close()

    return {'success': True, 'data': results}

# Next two APIs only work when the tournament hasn't started.

# Allows host to swap the placement of two participants in the available start matches.
@app.route('/api/swap_participants/<int:tournament_id>/<int:user_id_1>/<int:user_id_2>')
@jwt_required()
def swap_participants(tournament_id, user_id_1, user_id_2):
    # Check for ownership
    if not is_owner(int(get_jwt_identity()), tournament_id):
        return {'success': False, 'msg': 'You do not own this tournament.'}
    
    # Check for participants
    if not (is_in_tournament(user_id_1, tournament_id) and is_in_tournament(user_id_2, tournament_id)):
        return {'success': False, 'msg': 'User is not in tournament.'}

    # Start connection
    connection = get_connection()
    cursor = connection.cursor()

    # Check if tournament hasn't started
    tournament = get_tournament_row(cursor, tournament_id)
    if datetime.datetime.now() >= from_db_time(tournament['start_time']):
        return {'success': False, 'msg': 'Tournament has already started.'}

    # Swaps users. Bit convoluted but whatever.
    # Checks if id is equal to user 1, then swaps to user 2 and vice versa.
    # Keeps the id the same if neither condition is met
    # Performs this action for both player_1_id and player_2_id
    # Only performs this action on starting rounds [rounds that accepts registrations rather than winners]
    cursor.execute('''
        UPDATE Matches
            SET player_1_id = CASE
                    WHEN player_1_id = ? THEN ?
                    WHEN player_1_id = ? THEN ?
                    ELSE player_1_id END,
                player_2_id = CASE 
                    WHEN player_2_id = ? THEN ?
                    WHEN player_2_id = ? THEN ?
                    ELSE player_2_id END
        WHERE accepts_registered > 0
    ''', 
    (
        user_id_1, user_id_2,
        user_id_2, user_id_1,
        user_id_1, user_id_2,
        user_id_2, user_id_1
    ))

    # Commit changes
    connection.commit()

    # Get matches to return then close connection
    cursor.execute('''
        SELECT * FROM Matches 
        WHERE tournament_id = ? AND accepts_registered > 0
        AND ((player_1_id = ? OR player_2_id = ?) OR (player_1_id = ? OR player_2_id = ?))
    ''', (tournament_id, user_id_1, user_id_1, user_id_2, user_id_2))
    results = get_results(cursor.fetchall())
    connection.close()

    return {'success': True, 'data': results}

# Force withdraws a registered user
@app.route('/api/remove_participant/<int:tournament_id>/<int:user_id>')
@jwt_required()
def remove_participants(tournament_id, user_id):
    # Check for ownership
    if not is_owner(int(get_jwt_identity()), tournament_id):
        return {'success': False, 'msg': 'You do not own this tournament.'}

    # Check for participant
    if not is_in_tournament(user_id, tournament_id):
        return {'success': False, 'msg': 'User is not in tournament.'}

    # Open connection
    connection = get_connection()
    cursor = connection.cursor()

    # Check if tournament hasn't started
    tournament = get_tournament_row(cursor, tournament_id)
    if datetime.datetime.now() >= from_db_time(tournament['start_time']):
        return {'success': False, 'msg': 'Tournament has already started.'}

    # Force withdraw
    withdraw_success = withdraw_user(tournament_id, user_id)

    if not withdraw_success:
        return {'success': False, 'msg': 'An error occurred during withdrawl.'}

    # Get matches to return
    cursor.execute('''
        SELECT * FROM Matches 
        WHERE tournament_id = ? AND accepts_registered > 0
    ''', (tournament_id,))
    matches = get_results(cursor.fetchall())

    # Get participants to return
    cursor.execute(''' 
        SELECT Participants.*, Users.username FROM Participants
        JOIN Users ON Participants.user_id = Users.user_id
        WHERE tournament_id = ?
        AND status <> 'withdrawn'
        ORDER BY registration_time ASC
    ''', (tournament_id,))
    participants = get_results(cursor.fetchall())

    connection.close()
    
    return {'success': True, 'matches': matches, 'participants': participants}

##############################
if __name__ == '__main__':
    app.run(debug=True)
##############################