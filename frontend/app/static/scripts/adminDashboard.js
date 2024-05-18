const CURRENT_USER_ID = "{{ user.id }}";

async function openUserManagement() {
    resetContainerContents();
    getTitle().innerHTML = "Users";
    document.getElementById("user-btn").classList.toggle("active");
    getContainer().innerHTML = createUsersTable(await getUsers());
}

function openApiKeyManagement() {
    resetContainerContents();
    getTitle().innerHTML = "API keys";
    document.getElementById("apikey-btn").classList.toggle("active");

}

function openTagManagement() {
    resetContainerContents();
    getTitle().innerHTML = "Tags";
    document.getElementById("tag-btn").classList.toggle("active");

}

function getContainer() {
    return document.getElementById("dashboard-content");
}

function getTitle() {
    return document.getElementById("dashboard-title");
}

function resetContainerContents() {
    getContainer().innerHTML = "";
    getTitle().innerText = "Select an item";
    document.querySelectorAll(".dashboard-btn").forEach(btn => {
        btn.classList.remove("active");
    });
}

async function getUsers() {
    return await fetch("/admin/users", {
        credentials: "same-origin",
    }).then(resp => resp.json());
}

function deleteUser(id) {
    fetch(`/admin/users/${id}`, {
        method: 'DELETE',
        credentials: "same-origin",
    }).then(resp => {
        // document.getElementById("deleteUserModal").style.display = 'none';
        if (resp.ok) {
            openUserManagement();
        }
        else {
            console.log(resp.status);
        }
    });
}

function disableUser(id) {
    fetch(`/admin/users/${id}`, {
        method: 'POST',
        credentials: "same-origin",
    }).then(resp => {
        // document.getElementById("deactivateUserModal").style.display = 'none';
        if (resp.ok) {
            openUserManagement();
        }
        else {
            console.log(resp.status);
        }
    });
}

function createUsersTable(users) {
    // Create table
    let table = document.createElement('table');
    table.classList.add('table', 'table-striped', 'table-dark');

    // Create table header
    let thead = document.createElement('thead');
    let headerRow = document.createElement('tr');
    ['ID', 'Email', 'Delete', 'Disable'].forEach(text => {
        let th = document.createElement('th');
        th.textContent = text;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create table body
    let tbody = document.createElement('tbody');
    users.forEach(user => {
        let row = document.createElement('tr');
        ['id', 'email'].forEach(key => {
            let td = document.createElement('td');
            td.textContent = user[key];
            row.appendChild(td);
        });

        // Add delete button
        let deleteTd = document.createElement('td');
        let deleteButton = document.createElement('button');
        let deleteConfirmButton = document.getElementById("confirmUserDeleteButton");
        deleteButton.textContent = 'Delete';
        deleteButton.classList.add('btn', 'btn-danger');
        deleteButton.setAttribute('data-bs-toggle', 'modal');
        deleteButton.setAttribute('data-bs-target', '#deleteUserModal');
        deleteConfirmButton.addEventListener('click', () => deleteUser(user.id));
        deleteTd.appendChild(deleteButton);
        row.appendChild(deleteTd);

        // Add disable button
        let disableTd = document.createElement('td');
        let disableButton = document.createElement('button');
        let disableConfirmButton = document.getElementById("confirmUserDeactivateButton");
        disableButton.textContent = 'Disable';
        disableButton.classList.add('btn', 'btn-danger');
        disableButton.setAttribute('data-bs-toggle', 'modal');
        disableButton.setAttribute('data-bs-target', '#deactivateUserModal');
        disableConfirmButton.addEventListener('click', () => disableUser(user.id));
        disableTd.appendChild(disableButton);
        row.appendChild(disableTd);

        tbody.appendChild(row);
    });
    table.appendChild(tbody);

    return table.outerHTML;
}

function getApiKeys() {

}

// async function getTags() {
//     return await fetch("/admin/tags", {
//         credentials: "same-origin",
//     }).then(resp => resp.json());
// }