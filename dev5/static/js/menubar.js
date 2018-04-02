var submitCredentials = function() {
    $.ajax({
        'url' : 'credentials/set_ssh_username',
        'data' : {'username' : document.getElementById('ssh_id').value},
        'method': 'POST'
    });

    $.ajax({
        'url' : 'credentials/set_mysql_username',
        'data' : {'username' : document.getElementById('sql_id').value},
        'method': 'POST'
    });

    $.ajax({
        'url' : 'credentials/set_ssh_password',
        'data' : {'b64str' : window.btoa(document.getElementById('ssh_pwd').value)},
        'method': 'POST'
    });

    $.ajax({
        'url' : 'credentials/set_mysql_password',
        'data' : {'b64str' : window.btoa(document.getElementById('sql_pwd').value)},
        'method': 'POST'
    });
    
    $.ajax({
        'url' : 'credentials/set_password',
        'data' : {'b64str' : window.btoa(document.getElementById('app_pwd').value)},
        'method': 'POST'
    });
    
    closeModal();
}

var closeModal = function() {
    $('#credModal').modal('toggle'); 
}