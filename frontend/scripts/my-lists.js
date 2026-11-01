PAGE_API = 'get_owned_tournaments'

owned = document.getElementById('owned-button')
joined = document.getElementById('joined-button')

owned.onclick = function() {
    PAGE_API = 'get_owned_tournaments'
    owned.disabled = true
    joined.disabled = false

    loadFilterOptions().then(() => {
        showFiltersInForm()
        loadPageOfResults(PAGE_API, getPage(), true, true)
    })
}

joined.onclick = function() {
    PAGE_API = 'get_joined_tournaments'
    owned.disabled = false
    joined.disabled = true

    loadFilterOptions().then(() => {
        showFiltersInForm()
        loadPageOfResults(PAGE_API, getPage(), true, true)
    })
}