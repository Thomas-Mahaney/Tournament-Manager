// This script handles signups

// Import our requester
import { requestUser } from "./exports.js";

// Runs when form is submitted
document.getElementById("signup-form").addEventListener("submit", function(event) {
    // Prevent automatic page refresh
    event.preventDefault()

    // Request the signup api and send our form data through
    requestUser('signup', new FormData(this))
    .then(data => {
        // If signup successful, return to home.
        if (!data.success) {return}
        window.location.href = '/'
    })
})