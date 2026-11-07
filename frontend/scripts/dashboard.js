// variables
var dashboard_data = null;
const match_div = document.getElementById('tournament-matches')
const registered_list = document.getElementById('registered')
const waitlist_list = document.getElementById('waitlist')

var userDictionary = {}

function getDashboardData() {
    // Get the tourney id from the url
    const params = new URLSearchParams(window.location.search)
    const id = params.get('id')

    // fetch all required data for the dashboard. If not owned the page will error.
    return authFetch('/api/get_dashboard_data/' + id)
    .then(result => {
        if (result.ok) {
            dashboard_data = result.data

            // store participants in a user table to more easily handle users
            for (const participant of dashboard_data.participants) {
                userDictionary[participant.user_id] = {'status': participant.status, 'username': participant.username}
            }
        }

        // Shows the error message or page depending on if fetch was successful.
        // Doesn't matter if user makes the allowed div visible as it will not load properly and won't function anyway.
        document.getElementById('disallowed').hidden = result.ok
        document.getElementById('allowed').hidden = !result.ok
    })
    .catch(error => console.error(error))
}

function loadLists() {
    for (const user of dashboard_data.participants) {
        // Create list item
        const list_item = document.createElement('li')
        list_item.textContent = user.username

        // Add to appropriate list
        if (user.status === 'registered') {
            registered_list.appendChild(list_item)
        } else if (user.status === 'waitlisted') {
            waitlist_list.appendChild(list_item)
        }
    }
}

function createBrackets() {
    // Will be refactored or replaced later. Right now just used for basic functionality    
    for (const match of dashboard_data.matches) {
        const new_bracket = document.createElement('div')
        new_bracket.id = 'match_' + match.match_number

        const match_id = document.createElement('h3')
        match_id.textContent = 'Match: ' + match.match_number + ', Round: ' + match.round_number

        const player_1 = document.createElement('p')
        player_1.textContent = userDictionary[match.player_1_id] ? userDictionary[match.player_1_id]['username'] : null
        const player_2 = document.createElement('p')
        player_2.textContent = userDictionary[match.player_2_id] ? userDictionary[match.player_2_id]['username'] : null

        if (match.winner == match.player_1_id) {
            player_1.style='font-weight: bold;'
        } else if (match.winner == match.player_2_id) {
            player_2.style='font-weight: bold;'
        }

        new_bracket.appendChild(match_id)
        new_bracket.appendChild(player_1)
        new_bracket.appendChild(player_2)
        match_div.appendChild(new_bracket)
    }
}

window.onload = function() {
    getDashboardData()
    .then(() => {
        console.log(dashboard_data)

        // Temp
        let start = new Date(dashboard_data.tournament.start_time).getTime()
        let current = new Date().getTime()
        console.log(current - start)

        document.getElementById('tournament-title').textContent = dashboard_data.tournament.title
        loadLists()
        createBrackets()
    })
}

document.getElementById('back').onclick = function() {
    history.back()
}