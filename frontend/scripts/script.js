import { BACKEND_DOMAIN } from "./exports"

// Default page number
const DEFAULT_PAGE = 1

// When page loads, we call the backend to get available tournaments and display them.
function loadPageOfResults(page, replaceState, setDefault) {
    return fetch(BACKEND_DOMAIN + 'get_tournaments/' + page) // Calls backend api for tournaments
    .then(response => response.json()) // Parse response JSON into an array
    .then(data => {
        // Check if there's any entries
        if (data.length == 0) { 
            if (setDefault & page != DEFAULT_PAGE) { // set page count to 1 and reload if attempting to load an empty page. Don't do this if page 1 is empty to avoid loop.
                page = DEFAULT_PAGE
                loadPageOfResults(page)
            }
            return null // Do not proceed any further
        }

        // Get tournament-list div that we will store our entries into
        const list = document.getElementById('tournament-list')

        // Go through each entry of our data and create html for it
        data.forEach((entry, index) => {
            // Create a new div to store event details into
            const newDiv = newElement('event_' + index, 'div')

            // Loop through entry and create/update elements for each value
            for (let category in entry) {
                // Creates new paragraph element
                const newP = newElement(category + '_' + index, 'p')
                
                // Set text of element to category name and value, then append to our entry div
                newP.innerText = category + ': ' + entry[category]
                newDiv.appendChild(newP)
            }

            // Create registration button
            const newButton = newElement('register_' + index, 'button')
            newButton.innerText = "Register"
            
            // Append to entry div
            newDiv.appendChild(newButton)

            // Append our entry div into the main tournament-list div, then add a line break
            list.appendChild(newDiv)
            list.appendChild(newElement('break_' + index, 'br'))
        })

        // Remove html entries if needed. Child count is halved as we consider break and event as 1 item
        for (let i = data.length; i < list.childElementCount / 2; i++) {
            document.getElementById('event_' + i).remove()
            document.getElementById('break_' + i).remove()
        }

        // Update page counter and url
        updateURL('page', page, replaceState)
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
function updateURL(param, value, replace) {
    // Updates URL
    try {
        // Get url and the search parameters
        var url = new URL(window.location.href)
        let params = new URLSearchParams(url.search)

        // Set new parameter
        params.set(param, value)
        
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
        updateURL('page', page)
     }

    return page
}

// When site loads, load page of results
window.onload = function() {
   loadPageOfResults(getPage(), false, true)
   .then(

   )
}

// Update results when using foward and back history arrows on browser
window.onpopstate = function() {
    loadPageOfResults(getPage(), true)
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