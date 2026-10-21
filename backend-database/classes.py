class User:
    def __init__(self, username, password, id):
        self.username = username
        self.password = password
        self.id = id

class Tournament:
    def __init__(self, tournament_id, name, description, game, location, start_time, registration_deadline, skill_level, player_cap):
        self.tournament_id = tournament_id
        self.name = name
        self.game = game
        self.start_time = start_time
        self.registration_deadline = registration_deadline
        self.skill_level = skill_level
        self.location = location
        self.player_cap = player_cap
        self.description = description