// Default page number
const DEFAULT_PAGE = 1
// URL parameters used for filtering. These match the names of the inputs in the filter form.
const FILTERS = ['search', 'game', 'skill_level', 'open']

// When page loads, we call the backend to get available tournaments and display them.
function loadPageOfResults(page, replaceState, setDefault) {
        // Calls backend api for tournaments matching the filters, and the user's registrations, at the same time
    const tournaments = fetch(API_URL + '/api/get_tournaments/' + page + '?' + getFilters())
    .then(response => response.json()) // Parse response JSON into an array

    Promise.all([tournaments, getMyRegistrations()])
    .then(([data, registrations]) => {

        // Do not show an empty page past the end of the results
        if (data.length == 0 && page != DEFAULT_PAGE) {
            if (setDefault) { // set page count to 1 and reload if attempting to load an empty page
                loadPageOfResults(DEFAULT_PAGE, true)
            }
            return null // Do not go any further
        }

        // Get tournament-list div that we will store our entries into, and clear out the previous page
        const list = document.getElementById('tournament-list')
        list.replaceChildren()

        // Let the user know if nothing matched their filters
        if (data.length == 0) {
            const message = document.createElement('p')
            message.innerText = 'No tournaments match your filters.'
            list.appendChild(message)
        }

        // Go through each entry of our data and create html for it
        data.forEach(entry => {
            // Create a new div to store event details into
            const newDiv = document.createElement('div')
            newDiv.className = 'tournament'

            // Title links to the tournament viewer page
            const title = document.createElement('h3')
            const link = document.createElement('a')
            link.href = 'tournament.html?id=' + entry.tournament_id
            link.innerText = entry.title
            title.appendChild(link)
            newDiv.appendChild(title)

            // Add a line for each field we want to show the user
            for (let category in FIELD_NAMES) {
                newDiv.appendChild(newField(category, entry[category]))
            }

            // Player count, then register/withdraw buttons. After a change, reload the same page
            newDiv.appendChild(newPlayerCount(entry))
            buildRegistrationArea(entry, registrations[entry.tournament_id], () => loadPageOfResults(getPage(), true))
            .then( data => {
                newDiv.appendChild(data)
            })
            
            
            // Append our entry div into the main tournament-list div
            list.appendChild(newDiv)
        })

        updateURL({ page: page }, replaceState)
        document.getElementById('page-counter').innerText = page
    })
    .catch(message => console.error(message)) // Catch any errors and output them in the console
}

function newElement(id, elementType) {
    // Get the element from the html page using its id.
    // If the element doesn't exist, it should return null.
    var element = document.getElementById(id)

    // If element doesn't exist, create it and give it the given id.
    if (!element) {
        element = document.createElement(elementType)
        element.id = id
    }

    // Return our element
    return element
}

// Might update later
function updateURL(values, replace) {
    // Updates URL
    try {
        // Get url and the search parameters
        var url = new URL(window.location.href)
        let params = new URLSearchParams(url.search)

        // Set new parameters
        for (let param in values) {
            if (values[param]) {
                params.set(param, values[param])
            }
            else {
                params.delete(param)
            }
        }
        
        // Update url and push it to client
        url.search = params.toString()
        if (replace) {
            window.history.replaceState({}, '', url)
        } else {
            window.history.pushState({}, '', url)
        }
    } catch (error) {
        console.error(error)
    }
}

function getPage() {
    // Get url parameters and get page if it exists
    const params = new URLSearchParams(window.location.search)
    var page = Number(params.get('page'))
    
    // If page doesn't exist or out of bounds, set to default
    if (!page || page < 1) { 
        page = DEFAULT_PAGE
        updateURL({ page: page }, true)
    }

    return page
}

// Gets only the filter parameters from the url, ready to send to the backend
function getFilters() {
    const params = new URLSearchParams(window.location.search)
    const filters = new URLSearchParams()

    FILTERS.forEach(filter => {
        if (params.get(filter)) {
            filters.set(filter, params.get(filter))
        }
    })
    return filters.toString()
}

// Fills in the filter form using the url, so filters stay set after a refresh or using back/forward
function showFiltersInForm() {
    const params = new URLSearchParams(window.location.search)
    const inputs = document.getElementById('filter-form').elements

    inputs.search.value = params.get('search') || ''
    inputs.game.value = params.get('game') || ''
    inputs.skill_level.value = params.get('skill_level') || ''
    inputs.open.checked = params.get('open') == 'true'
}

// Adds an option to a dropdown in the filter form
function addOption(select, value) {
    const option = document.createElement('option')
    option.value = value
    option.innerText = value
    select.appendChild(option)
}

// Get the games and skill levels from the backend and puts them into the dropdowns
function loadFilterOptions() {
    return fetch(API_URL + '/api/get_filter_options')
    .then(response => response.json())
    .then(data => {
        const inputs = document.getElementById('filter-form').elements
        data.games.forEach(game => addOption(inputs.game, game))
        data.skill_levels.forEach(level => addOption(inputs.skill_level, level))
    })
    .catch(message => console.error(message))
}

// When site loads, load page of results
window.onload = function() {
    loadFilterOptions().then(() => {
        showFiltersInForm()
        loadPageOfResults(getPage(), true, true)
    })
}

// Update results when using foward and back history arrows on browser
window.onpopstate = function() {
    showFiltersInForm()
    loadPageOfResults(getPage(), true)
}

// Apply filters when the form is submitted. Goes back to page 1 since the results have changed.
document.getElementById('filter-form').onsubmit = function(event) {
    event.preventDefault()

    const inputs = this.elements
    updateURL({
        search: inputs.search.value.trim(),
        game: inputs.game.value,
        skill_level: inputs.skill_level.value,
        open: inputs.open.checked ? 'true' : '',
        page: DEFAULT_PAGE,
    })
    loadPageOfResults(DEFAULT_PAGE, true)
}

// Clear all filters and show every tournament again
document.getElementById('filter-clear').onclick = function() {
    updateURL({ search: '', game: '', skill_level: '', open: '', page: DEFAULT_PAGE})
    showFiltersInForm()
    loadPageOfResults(DEFAULT_PAGE, true)
}

// Change page using page select arrows on bottom of page.
document.getElementById('page-back').onclick = function() {
    let page = getPage() - 1
    if (page < 1) { return null}
    loadPageOfResults(page)
}

document.getElementById('page-next').onclick = function() {
    let page = getPage() + 1
    loadPageOfResults(page)
}