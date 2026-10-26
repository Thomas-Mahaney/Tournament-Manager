document.getElementById("signup-form").addEventListener("submit", function(event) {
    // prevent automatic page refresh
    event.preventDefault()

    // request the signup api and send our form data through
    fetch('http://localhost:5000/api/signup', {
        method: 'POST',
        body: new FormData(this),
    })
    .then(response => response.json()) // parse json response
    .then(data => {
        // If successful, redirect to home
        // If unsuccessful, add error message
        if (data.success) {
            window.location.href = '/'
        } else {
            document.getElementById('error-message').innerText = "Username already exists."
        }
    })
    .catch(error => console.error(error));
})