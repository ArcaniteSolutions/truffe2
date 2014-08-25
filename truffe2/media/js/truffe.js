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
$('nav > ul > li > ul').each(function(__, elem) {

    if ($(elem).children().length === 0) {
        $(elem).parent().hide();
    }

});

function activate_menu(id) {
    $('#' + id).addClass('active');
    $('#' + id).parent().parent().addClass('open').addClass('active');
}
