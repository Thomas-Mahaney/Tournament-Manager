// Loads a single tournament using the id in the url (tournament.html?id=3) and shows all of it's data
function loadTournament() {
    const params = new URLSearchParams(window.location.search)
    const id = params.get('id')
    const details = document.getElementById('tournament-details')

    const tournamentRequest = fetch(API_URL + '/api/get_tournament/' + id)
    .then(response => {
        // Backend sends a 404 if the tournament doesn't exist
        if (!response.ok) {
            throw new Error('Tournament not found')
        }
        return response.json()
    })
    Promise.all([tournamentRequest, getMyRegistrations()])
    .then(([tournament, registrations]) => {
        // Clear old content, since this also runs again after registering or withdrawing
        details.replaceChildren()
        document.getElementById('tournament-title').innerText = tournament.title
        document.title = tournament.title

        // Description gets it's own paragraph above the other details
        const description = document.createElement('p')
        description.innerText = tournament.description || 'No description given.'
        details.appendChild(description)

        // Add a line for each fiend we want to show the user
        for (let category in FIELD_NAMES){
            details.appendChild(newField(category, tournament[category]))
        }

        // Player count, then register / withdraw buttons. After a change, reload this tournament.
        details.appendChild(newPlayerCount(tournament))
        authFetch('/api/get_id')
        .then(result => {
            details.appendChild(buildRegistrationArea(tournament, result.data.id, registrations[tournament.tournament_id], loadTournament))
        })
    })
    .catch(error => {
        document.getElementById('tournament-title').innerText = 'Tournament not found.'
        console.error(error)
    })
}

// If we came from the tournament list, go back to the same page and filters the user had
const backLink = document.getElementById('back-link')
if (document.referrer.includes('index.html')) {
    backLink.href = document.referrer
}

window.onload = loadTournament