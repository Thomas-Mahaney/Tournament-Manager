const button = document.getElementsByName("but")[0]
button.addEventListener("click", async function() {
    try {
        const response = await fetch('http://localhost:5000/api/test')
        if (!response.ok) {
            throw new Error('Error: ${response.status}')
        }

        const data = await response.text()

        document.getElementsByName("response")[0].innerText = data
    } catch (error) {
        console.error(error);
    }
})