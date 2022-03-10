const mfaSelectorModal = new bootstrap.Modal(document.getElementById('mfaSelectorModal'), {});
const messageField = document.getElementById('message');
const tokenField = document.getElementById('token');

async function performMfa(type) {
    switch (type) {
        case 'TOTP':
            showTotpField();
            break;
        case 'FIDO2':
            let requestBody = getInputs();
            // initiate fido2 auth
            let fido2Response = await doLoginRequest({...requestBody, mfaType: 'fido2'});
            let fido2ResponseBody = await fido2Response.json();

            // decode the base64 encoded data
            let fido2Data = CBOR.decode(_base64ToArrayBuffer(fido2ResponseBody.fido2Data));

            // tell the browser to open up the credentials popup
            let assertion = await navigator.credentials.get(fido2Data);

            // complete fido2 auth
            let {redirected, url} = await doLoginRequest({
                ...requestBody,
                mfaType: 'fido2',
                fido2Data: _arrayBufferToBase64(CBOR.encode({
                    "credentialId": new Uint8Array(assertion.rawId),
                    "authenticatorData": new Uint8Array(assertion.response.authenticatorData),
                    "clientDataJSON": new Uint8Array(assertion.response.clientDataJSON),
                    "signature": new Uint8Array(assertion.response.signature),
                })),
            });
            if (redirected) {
                window.location = url;
                return;
            }
            break;
    }
}

function showMessage(message) {
    messageField.innerText = message;
    messageField.style.display = "block";
}

function showTotpField() {
    document.getElementById("totpTokenDiv").style.display = "block";
    mfaSelectorModal.hide();
    tokenField.focus();
}

async function doLoginRequest(requestBody) {
    return fetch("/accounts/login/", {
        method: "POST",
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        mode: 'same-origin',  // Do not send CSRF token to another domain.
        body: JSON.stringify(requestBody),
    });
}

function getInputs() {
    let username = document.getElementById('username').value;
    let password = document.getElementById('password').value;

    if (username.length === 0 || password.length === 0) {
        showMessage("Please enter username and password!");
        return;
    }

    let requestBody = {
        username: username,
        password: password,
    };

    // if totp token field is visible, the token should be included in the request
    if (document.getElementById("totpTokenDiv").style.display === "block") {
        requestBody["token"] = tokenField.value;
        requestBody["mfaType"] = 'totp';
        tokenField.value = "";
    }
    return requestBody;
}

document.getElementById('login').addEventListener('click', async e => {
    e.preventDefault();

    // authenticate using username and password (optional also with token)
    let response = await doLoginRequest(getInputs());

    // if login was successful you will be redirected to the home page
    if (response.redirected) {
        window.location = response.url;
        return;
    }

    if (response.status !== 401) {
        return;
    }
    // unauthorized / failed logins
    let responseBody = await response.json();
    switch (responseBody.error) {
        case 'invalid_credentials':
            showMessage(responseBody.message);
            break;
        case 'mfa_required':
            // if the backend only offers one mfa option pick this one
            if (responseBody.type.length === 1) {
                if (responseBody.type[0] !== 'TOTP' && responseBody.type[0] !== 'FIDO2') {
                    showMessage(responseBody.message ? responseBody.message : "Unknown MFA type");
                } else {
                    await performMfa(responseBody.type[0]);
                }
            } else {
                // if the backend offers multiple options for mfa let the user decide which option he'd like to pick
                document.getElementById('mfaSelectorModalFooter').innerHTML = "";
                responseBody.type.forEach(mfaType => {
                    document.getElementById('mfaSelectorModalFooter').innerHTML += `<button type="button" class="btn btn-primary" onclick="performMfa('${mfaType}')">${mfaType}</button>`
                });
                mfaSelectorModal.show();
                break;
            }
            break;
        default:
            showMessage("Unknown Error");
            break;
        }
});
