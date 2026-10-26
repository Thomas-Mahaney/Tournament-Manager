document.getElementById("login-form").addEventListener("submit", function(event) {
    event.preventDefault();

    fetch('http://localhost:5000/api/login', {
        method: 'POST',
        body: new FormData(this),
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        console.log(data)
        if (data.access_key) {
            console.log(data.access_key)
        }
    })
    .catch(error => console.error(error));
})

document.getElementById("test").onclick = function() {
    fetch('http://localhost:5000/api/protected', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.text())
    .then(data => {
        console.log(data)
    })
    .catch(error => console.error(error));
}