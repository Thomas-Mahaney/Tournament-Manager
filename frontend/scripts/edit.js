const form = document.getElementById('tournament-form')
const errorMessage = document.getElementById('error-message')
const hint = document.getElementById('hint')
const id = new URLSearchParams(window.location.search).get('id')

// Turns a database time ("2026-11-07" 13:00:00") into what a datetime-local input wants ("2026-11-07T13:00")
function toInputTime(value) {
    return value.slice(0, 16).replace(' ', 'T')
}

// Fills the game suggestions and the skill level dropdown
function loadOptions() {
    return fetch(API_URL + '/api/get_filter_options')
    .then(response => response.json())
    .then(data => {
        const gameOptions = document.getElementById('game-options')
        data.games.forEach(game => {
            const option = document.createElement('option')
            option.value = game
            gameOptions.appendChild(option)
        })

        data.skill_levels.forEach(level => {
            const option = document.createElement('option')
            option.value = level
            option.innerText = level
            form.elements.skill_level.appendChild(option)
        })
    })
}

// Gets the tournament's current details. Gives back null if it doesn't exist.
function loadTournament() {
    return fetch(API_URL + '/api/get_tournament/' + id)
    .then(response => response.ok ? response.json() : null)
}

// Puts the tournament's current details into the form
function fillForm(tournament) {
    for (const field of ['title', 'game', 'description', 'location', 'skill_level', 'player_cap']) {
        form.elements[field].value = tournament[field] || ''
    }
    form.elements.start_time.value = toInputTime(tournament.start_time)
    form.elements.deadline.value = toInputTime(tournament.deadline)
}

// Shows the form, but only to the host of a tournament that hasn't starting yet.
// (The backend checks these things too. This just saves the user from filling out a form that can't be saved.)
function start() {
    Promise.all([loadOptions(), loadTournament(), authFetch('/api/get_id')])
    .then(([loadOptions, tournament, me]) => {
        if (!tournament) {
            errorMessage.innerText = 'Tournament not found.'
        }
        else if (!me.ok) {
            errorMessage.innerText = 'Your login has expired. Please log in again.'
        }
        else if (String(tournament.host_user_id) != String(me.data.id)) {
            errorMessage.innerText = 'Only the host can edit this tournament.'
        }
        else if (new Date() >= new Date(tournament.start_time.replace(' ', 'T'))) {
            errorMessage.innerText = 'This tournament has already started, so it can no longer be edited.'
        }
        else {
            fillForm(tournament)
            hint.innerText = 'Players registered so far: ' + tournament.registered_count + '. The player cap can\'t go lower than that.'
            form.hidden = false
        }
    })
    .catch(error => {
        errorMessage.innerText = 'Could not reach the server.'
        console.error(error)
    })
}

// Sends the form to the backend. On success, goes back to the dashboard.
form.onsubmit = function(event) {
    // Prevent automatic page refresh
    event.preventDefault()
    errorMessage.innerText = ''

    authFetch('/api/edit_tournament/' + id, {method: 'POST', body: new FormData(form) })
    .then(result => {
        if (result.ok) {
            window.location.replace('dashboard.html?id=' + id)
        }
        else if (result.status == 401) {
            errorMessage.innerText = 'Your login has expired. Please log in again'
        }
        else {
            errorMessage.innerText = result.data.msg || 'Something went wrong.'
        }
    })
    .catch(() => {errorMessage.innerText = 'Could not reach the server.'})
}

// Only logged in users can edit tournaments
if(!isLoggedIn()) {
    window.location.href = 'login.html'
}
else {
    start()
}