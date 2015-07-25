function update_body_class() {

    if ($('body').attr('class').indexOf('minified') !== -1)
        $.ajax('/users/set_body/m');
    else if ($('body').attr('class').indexOf('hidden-menu') !== -1)
        $.ajax('/users/set_body/h');
    else
        $.ajax('/users/set_body/_');

}

//Monitor body change
$('.minifyme, #hide-menu >:first-child > a').click(function(e) {
    setTimeout(update_body_class, 100);
});

//Hide useless menus
$(document).ready(function() {

    $('nav > ul > li > ul').each(function(__, elem) {

        if ($(elem).children().length === 0) {
            $(elem).parent().hide();
        }

    });
});

function activate_menu(id) {
    $('#' + id).addClass('active');
    $('#' + id).parent().parent().children('a').click();

    if ($('#' + id).parent().hasClass('subsub-menu'))
        $('#' + id).parent().parent().parent().parent().children('a').click();
//.addClass('open').addClass('active');
}

$(function () {
    $('[data-toggle="tooltip"]').tooltip({'container': 'body'});
})

function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++) {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == sParam) {
            return sParameterName[1];
        }
    }

    return ''
}

$.fn.pulse = function(options) {

    var options = $.extend({
        times: 1,
        duration: 500
    }, options);

    var period = function(callback) {
        $(this).animate({opacity: 0.25}, options.duration, function() {
            $(this).animate({opacity: 1}, options.duration, callback);
        });
    };
    return this.each(function() {
        var i = +options.times, self = this,
        repeat = function() { --i && period.call(self, repeat) };
        period.call(this, repeat);
    });
};


function escape_html(html) {
    return html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
