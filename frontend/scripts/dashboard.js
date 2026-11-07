// variables
var dashboard_data = null;
const match_div = document.getElementById('tournament-matches')
const registered_list = document.getElementById('registered')
const waitlist_list = document.getElementById('waitlist')
const winner = document.getElementById('winner')
const swap = document.getElementById('swap')
const remove = document.getElementById('remove')

var userDictionary = {}

var selection_enabled = false

// Fetch data from backend needed for dashboard and store it
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

// Creates registered list and waitlist
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

// Creates tournament brackets
function createBrackets() {
    // Will be refactored or replaced later. Right now just used for basic functionality    
    for (const match of dashboard_data.matches) {
        const new_bracket = document.createElement('div')
        new_bracket.id = 'match_' + match.match_number

        const match_id = document.createElement('h3')
        match_id.textContent = 'Match: ' + match.match_number + ', Round: ' + match.round_number

        const player_1 = document.createElement('p')
        player_1.id = 'player_1_' + match.match_number
        const player_2 = document.createElement('p')
        player_2.id = 'player_2_' + match.match_number

        new_bracket.appendChild(match_id)
        new_bracket.appendChild(player_1)
        new_bracket.appendChild(player_2)
        match_div.appendChild(new_bracket)

        updateMatch(match)
    }
}

// Gets the player texts in a bracket
function getPlayers(match_num) {
    const player_1 = document.getElementById('player_1_' + match_num)
    const player_2 = document.getElementById('player_2_' + match_num)

    return { player_1, player_2 }
}

function updateMatch(match) {
    const { player_1, player_2 } = getPlayers(match.match_number)

    player_1.textContent = userDictionary[match.player_1_id] ? userDictionary[match.player_1_id]['username'] : 'Empty'
    player_2.textContent = userDictionary[match.player_2_id] ? userDictionary[match.player_2_id]['username'] : 'Empty'

    if (match.winner_id) {
        if (match.winner_id == match.player_1_id) {
            player_1.style='font-weight: bold;'
        } else if (match.winner_id == match.player_2_id) {
            player_2.style='font-weight: bold;'
        }
    }
}

function updateMatchData(data) {
    for (const match of data) {
        index = dashboard_data.matches.findIndex(element => element.match_number == match.match_number)
        dashboard_data.matches[index] = match
        updateMatch(match)
    }
}

function deselectParticipants() {
    for (const match of dashboard_data.matches) {
        const { player_1, player_2 } = getPlayers(match.match_number)

        player_1.className = null
        player_2.className = null

        player_1.onclick = null
        player_2.onclick = null
    }

    selection_enabled = false
}

function enableDeclareWinner() {
    selection_enabled = true

    for (const match of dashboard_data.matches) {
        // Skips empty matches or matches with winners.
        if (!match.player_1_id && !match.player_2_id) { continue; }
        if (match.winner_id) { continue; }

        const { player_1, player_2 } = getPlayers(match.match_number)
        const next_match = dashboard_data.matches.find(element => element.match_number == match.next_match)

        // local function for button update and functionality
        function updatePlayer(id) {
            let text = eval('player_' + id)
            text.classList.add('clickAllow')
            text.onclick = function() {
                if (!confirm('Declare ' + text.textContent + ' as the winner?')) { return; }
                authFetch(
                    '/api/declare_winner/' + dashboard_data.tournament.tournament_id 
                    + '/' + match.match_number
                    + '/' + eval('match.player_' + id + '_id')
                )
                .then(result => {
                    if (!result.ok) { return }
                    deselectParticipants()
                    updateMatchData(result.data.data)
                })
            }
        }

        if (match.player_1_id) { updatePlayer(1) }
        if (match.player_2_id) { updatePlayer(2) }
    }
}

function enableSwapPlayer() {
    selection_enabled = true
    let swap_user = null

    for (const match of dashboard_data.matches) {
        // Skips matches with winners and non-starting matches
        if (match.winner_id) { continue; }
        if (!match.accepts_registered) { continue; }

        const { player_1, player_2 } = getPlayers(match.match_number)

        // local function for button update and functionality
        function updatePlayer(id) {
            let text = eval('player_' + id)
            let player_id = eval('match.player_' + id + '_id')

            text.classList.add('clickAllow')
            text.onclick = function() {
                if (text.classList.contains('swapSelect')) {
                    text.classList.remove('swapSelect')
                    swap_id = null
                } else if (swap_user) {
                    if (!confirm('Swap ' + text.textContent + ' and ' + swap_user.user + '?')) { return; }
                    authFetch(
                        '/api/swap_participants/' + dashboard_data.tournament.tournament_id 
                        + '/' + player_id
                        + '/' + swap_user.id
                    )
                    .then(result => {
                        if (!result.ok) { return }
                        deselectParticipants()
                        updateMatchData(result.data.data)
                    })
                } else {
                    text.classList.add('swapSelect')
                    swap_user = {'user': text.textContent, 'id': player_id}
                }
            }
        }

        if (match.player_1_id) { updatePlayer(1) }
        if (match.player_2_id) { updatePlayer(2) }
    }
}

window.onload = function() {
    getDashboardData()
    .then(() => {
        let start = new Date(dashboard_data.tournament.start_time).getTime()
        let current = new Date().getTime()
        let started = (start - current) <= 0
        
        // winner.disabled = !started
        swap.disabled = started
        remove.disabled = started

        if (!started) {
            winner.title = "Only available after tournament has begun."
        } else {
            let highlight = "Only available before the tournament has begun."
            swap.title = highlight
            remove.title = highlight
        }


        document.getElementById('tournament-title').textContent = dashboard_data.tournament.title
        document.getElementById('start-time').textContent += formatValue('start_time', dashboard_data.tournament.start_time)
        loadLists()
        createBrackets()
    })
}

document.getElementById('back').onclick = function() {
    history.back()
}

winner.onclick = function() {
    if (selection_enabled) {
        deselectParticipants()
    } else {
        enableDeclareWinner()
    }
}

swap.onclick = function() {
    if (selection_enabled) {
        deselectParticipants()
    } else {
        enableSwapPlayer()
    }
}

remove.onclick = function() {
    if (selection_enabled) {
        deselectParticipants()
    } else {
        enableDeclareWinner()
    }
}

// Get Buttons working
    // Declare winner
    // Swap participants
    // Remove participants

    // Add time checks

// Change how matches are built