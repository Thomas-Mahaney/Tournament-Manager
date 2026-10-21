// When page loads, we call the backend to get available tournaments and display them.
window.onload = function() {
    // Gets json of tournaments from backend and parses them
    fetch('http://localhost:5000/api/get_tournaments')
    .then(response => response.json())
    .then(data => {
        // Constructs new sections on the page showing each tournament and it's info.
        // This code is a bit messy. Will clean later as things get more serious.
        for (let i = 0; i < data.length; i++) {
            const newDiv = document.createElement("div")
            newDiv.id = "event_" + i
            console.log(data[i].length)
            for (let item in data[i]) {
                const newP = document.createElement("p")
                newP.innerText = item
                newDiv.appendChild(newP)
            }
            document.getElementById("tournament-list").appendChild(newDiv)
            document.getElementById("tournament-list").appendChild(document.createElement("br"))
        }
    })
    .catch(error => console.error(error))
}