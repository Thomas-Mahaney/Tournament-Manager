// Register / Withdraw buttons for a tournament. Used by both the list page and the viewer page.
// Load this after common.js (it uses API_URL, isLoggedIn, and authFetch) and before the page's own script

// Turns a database time ("YYYY-MM-DD HH:MM:SS") into a Date
function toDate(value) {
    return new Date(value.replace(' ', 'T'))
}

// Create a paragraph like "Players: 8 / 10 · 2 on waitlist"
function newPlayerCount(tournament) {
    const p = document.createElement('p')
    let text = 'Players: ' + tournament.registered_count + ' / ' + tournament.player_cap
    if (tournament.waitlist_count > 0) {
        text += ' · ' + tournament.waitlist_count + ' on waitlist'
    }
    p.innerText = text
    return p
}

// Gets the user's status for every tournament they're in, as {tournament_id" {status, position}}
// One request covers a whole page of results. Logged out users get an empty object
function getMyRegistrations() {
    if (!isLoggedIn()) {
        return Promise.resolve({})
    }
    
    return authFetch('/api/my_registrations')
    .then(result => {
        const registrations = {}
        if (result.ok) {
            result.data.forEach(entry => { registrations[entry.tournament_id] = entry })
        }
        return registrations
    })
    .catch(() => ({})) // Still show the tournaments if this fails
}

// Builds the registration area for one tournament.
// mine: the user's {status, position} for this tournament, or nothing if they aren't in it
// onChange: called after registering/withdrawing so the page can reload its data
function buildRegistrationArea(tournament, mine, onChange) {
    const area = document.createElement('div')
    area.className = 'registration'

    const message = document.createElement('p')
    message.className = 'registration-message'

    const now = new Date()
    const registrationClosed = now >= toDate(tournament.deadline)
    const withdrawalsClosed = now >= toDate(tournament.withdraw_cutoff)
    const status = mine ? mine.status : null

    function addLabel(text) {
        const label = document.createElement('span')
        label.className = 'registration-status'
        label.innerText = text
        area.appendChild(label)
    }

    // Adds a button. If disabledReason is given, the button is greyed out and hovering shows why.
    function addButton(text, action, disabledReason) {
        const button = document.createElement('button')
        button.innerText = text
        if (disabledReason) {
            button.disabled = true
            button.title = disabledReason
        }
        else {
            button.onclick = action
        }
        area.appendChild(button)
    }

    if (status == 'registered' || status == 'waitlisted') {
        addLabel(status == 'registered' ? 'Registered ✓' : 'Waitlisted (#' + mine.position + ')')
        const cutoff = toDate(tournament.withdraw_cutoff).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
        addButton(status == 'registered' ? 'Withdraw' : 'Leave waitlist',
            () => sendRegistration('withdraw', tournament, message, onChange),
            withdrawalsClosed ? 'Withdrawals closed at ' + cutoff : null)
    } else if (registrationClosed) {
        addButton('Registration closed', null, 'The registration deadline has passed')
    } else if (!isLoggedIn()) {
        addButton('Log in to register', () => { location.href = 'login.html' })
    } else {
        const full = tournament.registered_count >= tournament.player_cap
        addButton(full ? 'Join waitlist' : 'Register', () => sendRegistration('register', tournament, message, onChange))
    }

    area.appendChild(message)
    return area
}

// Sends a register or withdraw request, then lets the page refresh
function sendRegistration(action, tournament, message, onChange) {
    if (action == 'withdraw') {
        const sure = confirm('Withdraw from "' + tournament.title + '"? If you sign up again later, you go to the back of the line.')
        if (!sure) {return}
    }

    authFetch('/api/' + action + '/' + tournament.tournament_id, { method: 'POST' })
    .then(result => {
        if (result.ok) {
            onChange()
        } else if (result.status == 401) {
            message.innerText = 'Your login has expired. Please log in again.'
        } else {
            message.innerText = result.data.msg || 'Something went wrong.'
        }
    })
    .catch(() => { message.innerText = 'Could not reach the server.' })
}
