// variables
var dashboard_data = null;
const registered_list = document.getElementById('registered')
const waitlist_list = document.getElementById('waitlist')

function getDashboardData() {
    const params = new URLSearchParams(window.location.search)
    const id = params.get('id')

    return authFetch('/api/get_dashboard_data/' + id)
    .then(result => {
        if (result.ok) {
            dashboard_data = result.data
        }
    })
    .catch(error => console.error(error))
}

function loadLists() {
    for (const participant of dashboard_data.participants) {
        // Create list item
        const list_item = document.createElement('li')
        list_item.textContent = participant.username

        // Add to appropriate list
        if (participant.status === 'registered') {
            registered_list.appendChild(list_item)
        } else if (participant.status === 'waitlisted') {
            waitlist_list.appendChild(list_item)
        }
    }
}

window.onload = function() {
    getDashboardData()
    .then(() => {
        loadLists()
    })
}

document.getElementById('back').onclick = function() {
    history.back()
}