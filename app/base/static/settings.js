document.getElementById('saveSettings').addEventListener('click', async e => {
    e.preventDefault();

    let response = await fetch("/accounts/profile/", {
        method: "POST",
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        mode: 'same-origin',  // Do not send CSRF token to another domain.
        body: JSON.stringify({
            firstName: document.getElementById('firstName').value,
            lastName: document.getElementById('lastName').value,
            email: document.getElementById('email').value,
        }),
    })

    if (response.redirected) {
        window.location = response.url;
    }
});
