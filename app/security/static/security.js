const createModal = new bootstrap.Modal(document.getElementById('createModal'), {});
const updateModal = new bootstrap.Modal(document.getElementById('updateModal'), {});

async function reloadTable() {
    let response = await fetch("/accounts/security/", {
        method: "GET",
        headers: {
            'Content-Type': 'application/json',
        }
    });
    let table = document.querySelector("tbody");
    let formatter = new Intl.DateTimeFormat('de-DE', {dateStyle: 'medium', timeStyle: 'medium'});
    // clear table
    table.innerHTML = "";
    let responseBody = await response.json()
    if (responseBody.mfaKeys.length === 0) {
        let row = table.insertRow(-1);
        let message = row.insertCell(0);
        message.colSpan = 10;
        message.style.textAlign = "center";
        message.innerText = "You haven't added any MFA Keys yet.";
    } else {

        responseBody.mfaKeys.forEach(mfaKey => {
            let row = table.insertRow(-1);
            let isEnabled = row.insertCell(0);
            isEnabled.innerHTML = `<i class="fas fa-circle" style="color: #${mfaKey.isEnabled ? "4cb34c" : "e50a0a"};"></i>`;
            let type = row.insertCell(1);
            type.innerText = mfaKey.type;
            let description = row.insertCell(2);
            description.innerText = mfaKey.description;
            let dateAdded = row.insertCell(3);
            dateAdded.innerText = mfaKey.dateAdded ? formatter.format(new Date(mfaKey.dateAdded)) : "";
            let lastUsed = row.insertCell(4);
            lastUsed.innerText = mfaKey.lastUsed ? formatter.format(new Date(mfaKey.lastUsed)) : "";
            let edit = row.insertCell(5);
            edit.innerHTML = `<a href="javascript:void(0)" onclick="update('${mfaKey.uuid}', ${mfaKey.isEnabled}, '${mfaKey.description}');"><i class="fas fa-pen"></i></a>`
        });
    }
}

/**
 * This function instructs the backup, that the user would like to set up totp authentication
 * The function will be invoked (using an event listener), when the user clicks on the totp tab in the "create modal".
 * */
async function loadCreateTotp() {
    // generate a secret key in the backend
    let response = await fetch("/accounts/security/", {
        method: "POST",
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        mode: 'same-origin',  // Do not send CSRF token to another domain.
        body: JSON.stringify({
            type: 'totp',
        }),
    });

    let responseBody = await response.json();
    document.getElementById('createModalUuid').value = responseBody.uuid;
    document.getElementById('totpSecret').innerText = responseBody.totpSecret;
    document.getElementById("totpQr").innerHTML = "";

    // generate qr code, which can be scanned using an mobile authenticator app (e. g. Authy)
    let totpQr = document.getElementById("totpQr");
    new QRCode(totpQr,
        `otpauth://totp/${responseBody.issuer}:${responseBody.username}?secret=${responseBody.totpSecret}&issuer=${responseBody.issuer}`
    );
    // place qr code in the middle of the modal
    totpQr.style.display = "table";
    totpQr.style.margin = "0 auto";
}

/**
 * This function instructs the backup, that the user would like to set up fido2 authentication
 * The function will be invoked (using an event listener), when the user clicks on the totp tab in the "create modal".
 * */
async function loadCreateFIDO2() {
    // request a challenge from the backend
    let response = await fetch(`/accounts/security/`, {
        method: "POST",
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        mode: 'same-origin',  // Do not send CSRF token to another domain.
        body: JSON.stringify({
            type: 'fido2',
        }),
    });
    let responseBody = await response.json();

    // decode the base64 encoded data
    let fido2Data = CBOR.decode(_base64ToArrayBuffer(responseBody.fido2Data));

    // remap id
    fido2Data.publicKey.user.id = new TextEncoder().encode(fido2Data.publicKey.user.id);

    // tell the browser to open up the credentials popup
    let attestation = await navigator.credentials.create(fido2Data);

    await fetch(`/accounts/security/${responseBody.uuid}/`, {
        method: "PUT",
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        mode: 'same-origin',  // Do not send CSRF token to another domain.
        body: JSON.stringify({
            'type': 'fido2',
            'description': prompt("Description", ""),
            'fido2Data': _arrayBufferToBase64(CBOR.encode({
              "attestationObject": new Uint8Array(attestation.response.attestationObject),
              "clientDataJSON": new Uint8Array(attestation.response.clientDataJSON),
            })),
        }),
    });
    createModal.hide();
    reloadTable();
}

/**
* Event listener to hide the "add mfa key" button
* */
document.getElementById('toggle-overview-tab').addEventListener('click', async () => {
    document.getElementById('createModalFooter').style.display = 'none';
});

/**
 * Event listener to invoke the loadCreateTotp() function,
 * also the "add mfa key" button in the footer of the modal gets visible.
 * */
document.getElementById('toggle-totp-tab').addEventListener('click', async () => {
    document.getElementById('createModalFooter').style.display = 'flex';
    await loadCreateTotp();
});

/**
 * Event listener to invoke the loadCreateFIDO2() function and hide the "add mfa key" button
 * */
document.getElementById('toggle-fido2-tab').addEventListener('click', async () => {
    document.getElementById('createModalFooter').style.display = 'none';
    await loadCreateFIDO2();
});

/**
 * This function will be called, when the user would like to add a new mfa key.
 * Usually you would open the modal using the html attributes data-bs-toggle="modal" and data-bs-target="#createModal",
 * in our case, we'd like to prevent re-requesting a new mfa key configuration (e.g. totp secret key or fido2 challenge)
 * */
function openCreateModal() {
    let overviewTab = new bootstrap.Tab(document.querySelector('#toggle-overview-tab'));
    overviewTab.show();

    createModal.show();
}

// open update modal and fill in the values into the field
function update(uuid, enabled, description) {
    document.getElementById('updateModalUuid').value = uuid;
    document.getElementById('updateModalEnabled').checked = enabled;
    document.getElementById('updateModalDescription').value = description;
    updateModal.show();
}

/**
 * Event listener for the add key button in the "create modal".
 * Currently, this is only required for totp authentication
 * */
document.getElementById('createModalConfirm').addEventListener('click', async e => {
    e.preventDefault();

    // check which tab is active
    let requestData;
    switch (document.querySelector(".active").id) {
        case 'toggle-totp-tab':
            requestData = {
                type: 'totp',
                description: document.getElementById('createModalTotpDescription').value,
                token: document.getElementById('createModalTotpToken').value,
            }
            break;
        default:
            // unhandled error - unknown tab or no save required
            return;
    }

    let response = await fetch(`/accounts/security/${document.getElementById('createModalUuid').value}/`, {
        method: "PUT",
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        mode: 'same-origin',  // Do not send CSRF token to another domain.
        body: JSON.stringify(requestData),
    });

    if (response.status === 200) {
        reloadTable();
        createModal.hide();
    } else {
        let messageField = document.getElementById('createModalMessageField');
        messageField.innerText = (await response.json()).message;
        messageField.style.display = "block";
    }
});

document.getElementById('updateModalSave').addEventListener('click', async e => {
    e.preventDefault();

    let response = await fetch(`/accounts/security/${document.getElementById('updateModalUuid').value}/`, {
        method: "PUT",
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        mode: 'same-origin',  // Do not send CSRF token to another domain.
        body: JSON.stringify({
            description: document.getElementById('updateModalDescription').value,
            enabled: document.getElementById('updateModalEnabled').checked,
        }),
    });

    if (response.status === 200) {
        reloadTable();
        updateModal.hide();
    } else {
        let messageField = document.getElementById('updateModalMessageField');
        messageField.innerText = (await response.json()).message;
        messageField.style.display = "block";
    }
});

document.getElementById('updateModalDelete').addEventListener('click', async e => {
    e.preventDefault();

    let response = await fetch(`/accounts/security/${document.getElementById('updateModalUuid').value}/`, {
        method: "DELETE",
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        mode: 'same-origin',  // Do not send CSRF token to another domain.
    });

    if (response.status === 204) {
        reloadTable();
        updateModal.hide();
    } else {
        let messageField = document.getElementById('updateModalMessageField');
        messageField.innerText = (await response.json()).message;
        messageField.style.display = "block";
    }
});

reloadTable();
