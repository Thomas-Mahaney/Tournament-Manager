document.getElementById("signup-form").addEventListener("submit", function(event) {
    event.preventDefault();

    fetch('http://localhost:5000/api/signup', {
        method: 'POST',
        body: new FormData(this),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.success)
    })
    .catch(error => console.error(error));
})