// Our backend domain that we'll use for all fetch requests
export const BACKEND_DOMAIN = 'http://localhost:5000/api/'

// Simple function used to create a header that's dependent on whether a token exists
export function getHeader() {
    var header = {}
    var token = localStorage.getItem('accessToken')
    if (token) { header['Authorization'] = `Bearer ${token}`}

    return header
}

// Used for logins/signups. Gets the relevant api and handles errors.
// If success, send data back for the other script to handle
export function requestUser(api, body) {
    // request api and send our form data through
    return fetch(BACKEND_DOMAIN + api, {
        method: 'POST',
        body: body,
        headers: getHeader()
    })
    .then(response => response.json()) // parses json response
    .then(data => {
        // If successful, return data
        if (data.success) {
            return data
        } else if (data.msg == 'Token has expired') {
            // If login failed due to an expired token, clear token and try again.
            localStorage.removeItem('accessToken')
            return requestUser(api, body)
        } else {
            // Add error message
            document.getElementById('error-message').innerText = data.msg
        }
    })
    .catch(error => console.error(error))
}