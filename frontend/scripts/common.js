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
    p.innerText = FIELD_NAMES[category] + ': ' + formatValue(category, value)
    return p
}


// LOGIN HELPERS
// These do the same job as the ones in exports.js, for the scripts that aren't modules
// TODO: merge with exports.js once every script is a module

// True if there's a login token that hasn't expired yet
// This doesn't prove the token is real, only the server can, it just decides what to show
function isLoggedIn() {
    try {
        const token = localStorage.getItem('accessToken')
        const { exp } = JSON.parse(atob(token.split('.')[1]))
        return Date.now() < exp * 1000
    }
    catch (err) {
        return false
    }
}

function getHeader() {
    var header = {}
    var token = localStorage.getItem('accessToken')
    if (token) { header['Authorization'] = `Bearer ${token}`}

    return header
}

// Calls the backend with the login token attached
// Always gives back { ok, status, data } so callers can check result.ok instead of catching errors
// If the server says the token expired or was logged out, the token is removed
function authFetch(path, options = {}) {
    return fetch(API_URL + path, { ...options, headers: getHeader()})
    .then(response => response.json()
    .catch(() => ({})) // Error pages from the server aren't JSON
        .then(data => {
            if (response.status == 401 && (data.msg == 'Token has expired' || data.msg == 'Token has been revoked')) {
                localStorage.removeItem('accessToken')
            }
            return { ok: response.ok, status: response.status, data: data }
        }))
}

// Used for login/signup pages
function requestUser(api, body) {
    // request api and send our form data through
    return fetch(API_URL + '/api/' + api, {
        method: 'POST',
        body: body,
        headers: getHeader()
    })
    .then(response => response.json()) // parses json response
    .then(data => {
        // If successful, return data
        if (data.success) {
            return data
        } else if (data.msg == 'Token has expired') {
            // If login failed due to an expired token, clear token and try again.
            localStorage.removeItem('accessToken')
            return requestUser(api, body)
        } else {
            // Add error message
            document.getElementById('error-message').innerText = data.msg
        }
    })
    .catch(error => console.error(error))
}