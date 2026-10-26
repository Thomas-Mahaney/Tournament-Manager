document.getElementById("login-form").addEventListener("submit", function(event) {
    // prevent automatic page refresh
    event.preventDefault()

    // request the login api and send our form data through
    fetch('http://localhost:5000/api/login', {
        method: 'POST',
        body: new FormData(this),
        credentials: 'include'
    })
    .then(response => response.json()) // parses json response
    .then(data => {
        // If login successful, get our new access token and save it to localstorage
        if (data.success) {
            localStorage.setItem("accessToken", data.access_token)
            // Send back to homepage
            document.location.href = '/'
        } else {
            // Add error message
            document.getElementById('error-message').innerText = "Invalid username or password."
        }
    })
    .catch(error => console.error(error));
})