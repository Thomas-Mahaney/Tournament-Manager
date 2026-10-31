// Handles the create tournament form. Load common.js before this file.

const form = document.getElementById('tournament-form')
const errorMessage = document.getElementById('error-message')

// Fills the game suggestions and the skill level dropdown
function loadOptions() {
    return fetch(API_URL + '/api/get_filter_options')
    .then(response => response.json())
    .then(data => {
        // Suggesting existing games keeps names consistent, so the game filter groups them together
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

// Sends the form to the backend. On success, opens the new tournament's page
form.onsubmit = function(event) {
    // Prevent automatic page refresh
    event.preventDefault()
    errorMessage.innerText = ''

    authFetch('/api/create_tournament', { method: 'POST', body: new FormData(form) })
    .then(result => {
        if (result.ok) {
            window.location.href = 'tournament.html?id=' + result.data.tournament_id
        }
        else if (result.status == 401) {
            errorMessage.innerText = 'Your login has expired. Please log in again'
        }
        else {
            errorMessage.innerText = result.data.msg || 'Something went wrong.'
        }
    })
    .catch(() => { errorMessage.innerText = 'Could not reach the server.'})
}

// Only logged in users can create tournaments
if (!isLoggedIn()) {
    window.location.href = 'login.html'
}
else {
    loadOptions().catch(error => {
        errorMessage.innerText = 'Could not reach the server.'
        console.error(error)
    })
}