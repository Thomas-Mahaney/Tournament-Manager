// This file holds code that both the list page and the viewer page use.
// Load this before the page's own script file, so that the page's script can use the functions defined here.

// Address of the backend server
const API_URL = 'http://localhost:5000'

// Names for each tournament field, in the order shown
const FIELD_NAMES = {
    game: 'Game',
    skill_level: 'Skill Level',
    location: 'Location',
    start_time: 'Starts',
    deadline: 'Registration Deadline',
    player_cap: 'Player Cap',
}

// Turns a database value into something readable for the user 
function formatValue(category, value) {
    // Missing values, like an empty location, get a placeholder instead of "null"
    if (value === null || value === '') {
        return 'TBD'
    }

    // Dates come from the database as "YYYY-MM-DD HH:MM:SS", so convert them into the user's local format
    if (category == 'start_time' || category == 'deadline') {
        const date = new Date(value.replace(' ', 'T'))
        return date.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
    }

    return value
}

// Create a paragragh like "Game: Chess" for one tournament field
function newField(category, value) {
    const p = document.createElement('p')
    p.innerText = FIELD_LABELS[category] + ': ' + formatValue(category, value)
    return p
}


