import { getHeader } from "./exports.js";

function isTokenValid(token) {
  try {
    const { exp } = JSON.parse(atob(token.split('.')[1]))
    return Date.now() < exp * 1000
  } catch (err) {
    return false;
  }
}

function displayButtons() {
    // Check if user is logged in
    let is_logged_in = isTokenValid(localStorage.getItem('accessToken'))
    console.log(is_logged_in)

    // toggle button visibility
    document.getElementById('not-logged').hidden = is_logged_in
    document.getElementById('is-logged').hidden = !is_logged_in
}

window.addEventListener('load', displayButtons())

document.getElementById('logout').onclick = function() {
    fetch('http://localhost:5000/api/logout', {
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