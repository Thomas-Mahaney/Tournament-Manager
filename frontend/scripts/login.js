// This script handles logins

// Runs when form is submitted
document.getElementById("login-form").addEventListener("submit", function(event) {
    // Prevent automatic page refresh
    event.preventDefault()

    // Request the login api and send our form data through
    requestUser('login', new FormData(this))
    .then(data => {
        // If login successful, save token and return to home.
        if (!data.success) {return}
        localStorage.setItem("accessToken", data.access_token)
        window.location.href = '/'
    })
})