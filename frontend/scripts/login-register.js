document.getElementById("login-form").addEventListener("submit", function(event) {
    event.preventDefault();

    fetch('http://localhost:5000/api/test', {
        method: 'POST',
        body: new FormData(this)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.href = "index.html"
        }
    })
    .catch(error => console.error(error));
})