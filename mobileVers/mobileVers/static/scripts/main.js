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

// Check for when the document is ready
$(document).ready(function () {
    // Check if any of the input[type=checkbox] are checked when the page
    // is ready.
    toggleBtnState();

    // When a checkbox is clicked, call the toggleBtnState() function
    $("input[type=checkbox]").click(function () {
        toggleBtnState();
    });
});

// toggleBtnState() is called when a checkbox is clicked
function toggleBtnState() {
    // Check if any of the input[type=checkbox] are checked, except for the
    // one with the id of "id_Identification"
    // If they are, enable the button and change the text to "Continue"
    // If they are not, disable the button and change the text to "Select a Program"
    if ($("input[type=checkbox]:checked").not("#id_Identification").length > 0) {
        $("#btnContinue").prop("disabled", false);
        $("#btnContinue").html("CONTINUE");
    } else {
        $("#btnContinue").prop("disabled", true);
        $("#btnContinue").html("SELECT A PROGRAM");
    }
}