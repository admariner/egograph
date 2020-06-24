// Bootstrap alert
alert = function () { }
alert.show = function (message) {
    $('#alert_placeholder').html('<div class="alert alert-danger m-0" role="alert"><span class="fas fa-exclamation-circle" aria-hidden="true"></span> ' + message + '</div>');
}
alert.hide = function () {
    $('#alert_placeholder').html('');
}

// Click button when hitting "enter"
$('#query_input').keypress(function (e) {
    if (e.keyCode == 13)
        $('#website_button').click();
});

// On button click
$('#website_button').click(function () {
    // Get website
    let query = $('#query_input').val();
    // If nothing entered, show alert
    if (query == "") {
        alert.hide();
        alert.show('Please enter a search query.');
    } else {
        alert.hide();
        window.location = '/graph/' + query
    }
});
