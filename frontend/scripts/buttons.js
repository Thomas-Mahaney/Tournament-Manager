function displayButtons() {
    // toggle button visibility
    document.getElementById('not-logged').hidden = isLoggedIn()
    document.getElementById('is-logged').hidden = !isLoggedIn()
}

window.addEventListener('load', displayButtons())

document.getElementById('logout').onclick = function() {
    fetch(API_URL + '/api/logout', {
        method: 'GET',
        headers: getHeader()
    })
    .then(response => response.json())
    .then(data => {
        localStorage.removeItem('accessToken')
        displayButtons()
    })
    .catch(error => console.error(error))
}