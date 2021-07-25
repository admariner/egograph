// Enable all bootstrap tooltips
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})

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
        $('#search_button').click();
});

// On search button click
$('#search_button').click(function () {
    // Get website
    let query = $('#query_input').val();
    // If nothing entered, show alert
    if (query == "") {
        alert.hide();
        alert.show('Please enter a search query.');
    } else {
        alert.hide();
        window.location = '/search/' + query + '/'
    }
});
