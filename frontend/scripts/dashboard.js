// variables
var dashboard_data = null;
const match_div = document.getElementById('tournament-matches')
const registered_list = document.getElementById('registered')
const waitlist_list = document.getElementById('waitlist')
const winner = document.getElementById('winner')
const swap = document.getElementById('swap')
const remove = document.getElementById('remove')
const edit = document.getElementById('edit')
const tourney_winner = document.getElementById('tourney-winner')

var selection_enabled = false

// Fetch data from backend needed for dashboard and store it
function getDashboardData() {
    // Get the tourney id from the url
    const params = new URLSearchParams(window.location.search)
    const id = params.get('id')

    if (id == null) {
        document.getElementById('disallowed').hidden = false
        document.getElementById('allowed').hidden = true
        return null
    }

    // fetch all required data for the dashboard. If not owned the page will error.
    return authFetch('/api/get_dashboard_data/' + id)
    .then(result => {
        if (result.ok) {
            dashboard_data = result.data   
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
    // Clear lists
    registered_list.replaceChildren()
    waitlist_list.replaceChildren()

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
    // Sort matches so that they're in order
    dashboard_data.matches.sort((a, b) => a.match_number - b.match_number)
    
    // Element that stores round headers
    const rounds = document.getElementById('Rounds')
    
    // Counter for second pass of first rounds. Incrments for every first round match present.
    var existing_matches = 0

    // Loop through all matches and visualize them
    for (const match of dashboard_data.matches) {
        // Check if we've entered a new round
        var round_container = document.getElementById('round_' + match.round_number)
        if (!round_container) {
            // Create new round container if it doesn't exist
            round_container = document.createElement('td')
            round_container.id = 'round_' + match.round_number
            round_container.classList.add('round')
            match_div.appendChild(round_container)

            // Create new round header
            const round_num = document.createElement('th')
            round_num.textContent = 'Round: ' + match.round_number
            rounds.appendChild(round_num)
        }

        // Increment counter if needed
        if (match.round_number == 1) {
            existing_matches += 1
        }

        // Create new match container
        const new_bracket = document.createElement('div')
        new_bracket.id = 'match_' + match.match_number
        new_bracket.classList.add('match')

        // Display both players in match
        const player_1 = document.createElement('p')
        player_1.id = 'player_1_' + match.match_number
        const player_2 = document.createElement('p')
        player_2.id = 'player_2_' + match.match_number

        // Create match header
        const match_num = document.createElement('h3')
        match_num.textContent = 'Match: ' + match.match_number

        // Append elements
        new_bracket.appendChild(match_num)
        new_bracket.appendChild(player_1)
        new_bracket.appendChild(player_2)
        round_container.appendChild(new_bracket)

        // Updates inside of match display.
        updateMatch(match)
    }

    // Add special hidden divs to first round so that elements are spaced correctly
    // Get total number of rounds that can be fit in round 1
    var total_matches = (2 ** Math.ceil(Math.log2(dashboard_data.tournament.player_cap))) / 2
    
    // Add blank matches for each match that doesn't exist in round 1.
    for (i = 0; i < total_matches - existing_matches; i++) {
        const new_bracket = document.createElement('div')
        new_bracket.classList.add('match')
        new_bracket.style = 'visibility: hidden;'

        // Display both players in match
        const match_num = document.createElement('h3')
        match_num.textContent = 'Empty'
        
        const player_1 = document.createElement('p')
        const player_2 = document.createElement('p')
        player_1.textContent = 'Empty'
        player_2.textContent = 'Empty'

        new_bracket.appendChild(match_num)
        new_bracket.appendChild(player_1)
        new_bracket.appendChild(player_2)
        document.getElementById('round_1').appendChild(new_bracket)
    }

    // move winner section to the end
    match_div.appendChild(tourney_winner.parentElement)
    rounds.appendChild(document.getElementById('winner-header'))
}

// Gets the player texts in a bracket
function getPlayers(match_num) {
    const player_1 = document.getElementById('player_1_' + match_num)
    const player_2 = document.getElementById('player_2_' + match_num)

    return { player_1, player_2 }
}

// Updates match display
function updateMatch(match) {
    // get players
    const { player_1, player_2 } = getPlayers(match.match_number)

    // find users using participant ids
    const user1 = dashboard_data.participants.find(user => user.user_id == match.player_1_id)
    const user2 = dashboard_data.participants.find(user => user.user_id == match.player_2_id)

    // update usernames
    player_1.textContent = user1 ? user1['username'] : 'Empty'
    player_2.textContent = user2 ? user2['username'] : 'Empty'

    // check if match has winner
    if (match.winner_id) {
        // holds winner's name
        var winner_name = null

        // makes winner's name bold
        if (match.winner_id == match.player_1_id) {
            player_1.style='font-weight: bold;'
            winner_name = player_1.textContent
        } else if (match.winner_id == match.player_2_id) {
            player_2.style='font-weight: bold;'
            winner_name = player_2.textContent
        }

        // updates winner section if this is the final match
        if (match.match_number == dashboard_data.matches.length) {
            tourney_winner.innerText = winner_name

            // disable button
            winner.disabled = true
            winner.title = "A user has won the tournament."
        }
    }
}

// Updates match data and refreshes match visuals
function updateMatchData(data) {
    for (const match of data) {
        index = dashboard_data.matches.findIndex(element => element.match_number == match.match_number)
        dashboard_data.matches[index] = match
        updateMatch(match)
    }
}

// Update participant data and refreshes lists
function updateParticipants(data) {
    dashboard_data.participants = data
    loadLists()
}

// Resets all participant selections in bracket
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
                    // If successful, disable selection and update dashboard
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
                        // If successful, disable selection and update dashboard
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

function enableRemovePlayer() {
    selection_enabled = true

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
                // Call api if confirmed
                if (!confirm('Remove ' + text.textContent + '?')) { return; }
                authFetch(
                    '/api/remove_participant/' + dashboard_data.tournament.tournament_id 
                    + '/' + player_id
                )
                .then(result => {
                    if (!result.ok) { return }

                    // If successful, disable selection and update dashboard
                    deselectParticipants()
                    updateMatchData(result.data.matches)
                    updateParticipants(result.data.participants)
                })
            }
        }

        if (match.player_1_id) { updatePlayer(1) }
        if (match.player_2_id) { updatePlayer(2) }
    }
}

window.onload = function() {
    try {
        // Gets data for tournament
        getDashboardData()
        .then(() => {
            let start = new Date(dashboard_data.tournament.start_time).getTime()
            let current = new Date().getTime()
            let started = (start - current) <= 0
            
            // Check if tournament is started and toggle appropriate buttons
            winner.disabled = !started
            swap.disabled = started
            remove.disabled = started
            edit.disabled = started

            // Add hover text for disabled buttons
            if (!started) {
                winner.title = "Only available after tournament has begun."
            } else {
                let highlight = "Only available before the tournament has begun."
                swap.title = highlight
                remove.title = highlight
                edit.title = highlight
            }

            // Update title and time
            document.getElementById('tournament-title').textContent = dashboard_data.tournament.title
            document.getElementById('start-time').textContent += formatValue('start_time', dashboard_data.tournament.start_time)
            
            // Fill lists and bracket
            loadLists()
            createBrackets()
        })
    } catch(error) {
        console.error(error)
    }
}

document.getElementById('back').onclick = function() {
    location.href = sessionStorage.getItem('last_page') || '/'
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
        enableRemovePlayer()
    }
}

// Opens the page for editing this tournament
edit.onclick = function() {
    location.href = 'edit.html?id=' + new URLSearchParams(window.location.search).get('id')
}
