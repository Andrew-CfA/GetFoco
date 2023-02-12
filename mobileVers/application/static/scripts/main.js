/*
*This program is free software: you can redistribute it and/or modify
*it under the terms of the GNU General Public License as published by
*the Free Software Foundation, either version 3 of the License, or
*(at your option) any later version
*/

$(document).on('submit', '#account-form', function (e) {
    e.preventDefault();
    $.ajax({
        type: 'POST',
        url: '/application/account',
        data: $('#account-form').serialize(),
        success: function (data) {
            if (data.result === "success") {
                alert('account created!');
                window.location = 'address';
            } else if ("redirect" in data) {
                window.location.href = data.redirect;
            } else {
                alert(data.message)
            }

        },

        error: function (response) {
            console.log(response)
        },
    })
})

