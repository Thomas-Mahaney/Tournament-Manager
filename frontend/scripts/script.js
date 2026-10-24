// When page loads, we call the backend to get available tournaments and display them.
function loadPageOfResults(page) {
    fetch('http://localhost:5000/api/get_tournaments/' + page) // Calls backend api for tournaments
    .then(response => response.json()) // Parse response JSON into an array
    .then(data => {
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

            // Add button functionality (currently placeholder)
            newButton.onclick = function() {
                console.log('hello')
            }
            
            // Append to entry div
            newDiv.appendChild(newButton)

            // Append our entry div into the main tournament-list div, then add a line break
            list.appendChild(newDiv)
            list.appendChild(document.createElement('br'))
        })
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
function updateURL(param, value) {
    // Updates URL
    try {
        // Get url and the search parameters
        var url = new URL(window.location.href)
        let params = new URLSearchParams(url.search)

        // Set new parameter
        params.set(param, value)
        
        // Update url and push it to client
        url.search = params.toString()
        window.history.pushState({}, '', url)
    } catch (error) {
        console.error(error)
    }
}

// When site loads, load page of results
window.onload = function() {
    // Get url parameters and get page if it exists
    const params = new URLSearchParams(window.location.search)
    var page = params.get('page')
    
    // If page doesn't exist, set to default
    if (!page) { 
        page = 1
        updateURL('page', page)
    }

    // Get current page
    loadPageOfResults(page)
}