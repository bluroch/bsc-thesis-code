function createNewUser(email){
    let randomPassword = Math.random().toString(36).slice(-8);
    $.ajax({
        url: '/api/users',
        type: 'POST',
        data: JSON.stringify({
            email: email,
            password: randomPassword
        }),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        success: function(result){
            console.log(result);
            alert("User created with password: " + randomPassword);
        }
    });
}

function deleteUser(id){
    $.ajax({
        url: '/api/users/' + id,
        type: 'DELETE',
        success: function(result){
            console.log(result);
            alert("User deleted");
        }
    });
}