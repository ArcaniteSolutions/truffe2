/*
 * VARIABLES
 * Description: All Global Vars
 */
// Impacts the responce rate of some of the responsive elements (lower value affects CPU but improves speed)

$.throttle_delay = 350;

// The rate at which the menu expands revealing child elements on click
$.menu_speed = 235;

// Note: You will also need to change this variable in the "variable.less" file.
$.navbar_height = 49; 

/*
 * APP DOM REFERENCES
 * Description: Obj DOM reference, please try to avoid changing these
 */     
$.root_ = $('body');
$.left_panel = $('#left-panel');
$.shortcut_dropdown = $('#shortcut');
$.bread_crumb = $('#ribbon ol.breadcrumb');

// desktop or mobile
$.device = null;

// Please make sure you have included "jarvis.widget.js" for this below feature to work
$.enableJarvisWidgets = true;

/*
 * DETECT MOBILE DEVICES
 * Description: Detects mobile device - if any of the listed device is detected
 * a class is inserted to $.root_ and the variable $.device is decleard. 
 */     

/* so far this is covering most hand held devices */
var ismobile = (/iphone|ipad|ipod|android|blackberry|mini|windows\sce|palm/i.test(navigator.userAgent.toLowerCase()));

if (!ismobile) {
    // Desktop
    $.root_.addClass("desktop-detected");
    $.device = "desktop";
} else {
    // Mobile
    $.root_.addClass("mobile-detected");
    $.device = "mobile";

    // Removes the tap delay in idevices
    // dependency: js/plugin/fastclick/fastclick.js 
    //FastClick.attach(document.body);
}

/* ~ END: CHECK MOBILE DEVICE */

/*
 * DOCUMENT LOADED EVENT
 * Description: Fire when DOM is ready
 */

$(document).ready(function() {
    /*
     * Fire tooltips
     */
    if ($("[rel=tooltip]").length) {
        $("[rel=tooltip]").tooltip();
    }

    $(document).arrive("[rel=tooltip]", function() {
        $(this).tooltip();
    });

    //TODO: was moved from window.load due to IE not firing consist
    nav_page_height()

        // INITIALIZE LEFT NAV
        if (!null) {
            $('nav ul').jarvismenu({
                accordion : true,
                speed : $.menu_speed,
                closedSign : '<em class="fa fa-expand-o"></em>',
                openedSign : '<em class="fa fa-collapse-o"></em>'
            });
        } else {
            alert("Error - menu anchor does not exist");
        }

    // COLLAPSE LEFT NAV
    $('.minifyme').click(function(e) {
        $('body').toggleClass("minified");
        $(this).effect("highlight", {}, 500);
        e.preventDefault();
    });

    // HIDE MENU
    $('#hide-menu >:first-child > a').click(function(e) {
        $('body').toggleClass("hidden-menu");
        e.preventDefault();
    });

    // SHOW & HIDE MOBILE SEARCH FIELD
    $('#search-mobile').click(function() {
        $.root_.addClass('search-mobile');
    });

    $('#cancel-search-js').click(function() {
        $.root_.removeClass('search-mobile');
    });

    // ACTIVITY
    // ajax drop
    $('#activity').click(function(e) {
        var $this = $(this);

        // if ($this.find('.badge').hasClass('bg-color-red')) {
        //      $this.find('.badge').removeClassPrefix('bg-color-');
        //      $this.find('.badge').text("0");
        //      // console.log("Ajax call for activity")
        // }

        if (!$this.next('.ajax-dropdown').is(':visible')) {
            $this.next('.ajax-dropdown').fadeIn(150);
            $this.addClass('active');
        } else {
            $this.next('.ajax-dropdown').fadeOut(150);
            $this.removeClass('active')
        }

        var mytest = $this.next('.ajax-dropdown').find('.btn-group > .active > input').attr('id');
        //console.log(mytest)
        //
        //
        url = $this.attr('url');
        container = $this.next('.ajax-dropdown');

        $.ajax(url, {'script': true}).done(function(data) { container.html(data); });

        e.preventDefault();
    });

    $('input[name="activity"]').change(function() {
        //alert($(this).val())
        var $this = $(this);

        url = $this.attr('id');
        container = $('.ajax-notifications');

        loadURL(url, container);

    });

    // NOTIFICATION IS PRESENT

    function notification_check() {
        $this = $('#activity > .badge');

        if (parseInt($this.text()) > 0) {
            $this.addClass("bg-color-red bounceIn animated")
        }
    }

    notification_check();

    // LOGOUT BUTTON
    $('#logout a').click(function(e) {
        //get the link
        var $this = $(this);
        $.loginURL = $this.attr('href');
        $.logoutMSG = $this.data('logout-msg');

        // ask verification
        $.SmartMessageBox({
            title : "<i class='fa fa-sign-out txt-color-orangeDark'></i> Logout <span class='txt-color-orangeDark'><strong>" + $('#show-shortcut').text() + "</strong></span> ?",
            content : $.logoutMSG || "Tu peux améliorer ta sécurité encore plus après la déconnexion en fermant ton navigateur.",
            buttons : '[No][Yes]'

        }, function(ButtonPressed) {
            if (ButtonPressed == "Yes") {
                $.root_.addClass('animated fadeOutUp');
                setTimeout(logout, 1000)
            }

        });
        e.preventDefault();
    });

    /*
     * LOGOUT ACTION
     */

    function logout() {
        window.location = $.loginURL;
    }

});

/*
 * RESIZER WITH THROTTLE
 * Source: http://benalman.com/code/projects/jquery-resize/examples/resize/
 */

(function($, window, undefined) {

    var elems = $([]), jq_resize = $.resize = $.extend($.resize, {}), timeout_id, str_setTimeout = 'setTimeout', str_resize = 'resize', str_data = str_resize + '-special-event', str_delay = 'delay', str_throttle = 'throttleWindow';

    jq_resize[str_delay] = $.throttle_delay;

    jq_resize[str_throttle] = true;

    $.event.special[str_resize] = {

        setup : function() {
            if (!jq_resize[str_throttle] && this[str_setTimeout]) {
                return false;
            }

            var elem = $(this);
            elems = elems.add(elem);
            $.data(this, str_data, {
                w : elem.width(),
                h : elem.height()
            });
            if (elems.length === 1) {
                loopy();
            }
        },
        teardown : function() {
            if (!jq_resize[str_throttle] && this[str_setTimeout]) {
                return false;
            }

            var elem = $(this);
            elems = elems.not(elem);
            elem.removeData(str_data);
            if (!elems.length) {
                clearTimeout(timeout_id);
            }
        },

        add : function(handleObj) {
            if (!jq_resize[str_throttle] && this[str_setTimeout]) {
                return false;
            }
            var old_handler;

            function new_handler(e, w, h) {
                var elem = $(this), data = $.data(this, str_data);
                data.w = w !== undefined ? w : elem.width();
                data.h = h !== undefined ? h : elem.height();

                old_handler.apply(this, arguments);
            };
            if ($.isFunction(handleObj)) {
                old_handler = handleObj;
                return new_handler;
            } else {
                old_handler = handleObj.handler;
                handleObj.handler = new_handler;
            }
        }
    };

    function loopy() {
        timeout_id = window[str_setTimeout](function() {
            elems.each(function() {
                var elem = $(this), width = elem.width(), height = elem.height(), data = $.data(this, str_data);
                if (width !== data.w || height !== data.h) {
                    elem.trigger(str_resize, [data.w = width, data.h = height]);
                }

            });
            loopy();

        }, jq_resize[str_delay]);

    };

})(jQuery, this);

/*
 * NAV OR #LEFT-BAR RESIZE DETECT
 * Description: changes the page min-width of #CONTENT and NAV when navigation is resized.
 * This is to counter bugs for min page width on many desktop and mobile devices.
 * Note: This script uses JSthrottle technique so don't worry about memory/CPU usage
 */

// Fix page and nav height
function nav_page_height() {
    var setHeight = $('#main').height();
    //menuHeight = $.left_panel.height();

    var windowHeight = $(window).height() - $.navbar_height;
    //set height

    if (setHeight > windowHeight) {// if content height exceedes actual window height and menuHeight
        $.left_panel.css('min-height', setHeight + 'px');
        $.root_.css('min-height', setHeight + $.navbar_height + 'px');

    } else {
        $.left_panel.css('min-height', windowHeight + 'px');
        $.root_.css('min-height', windowHeight + 'px');
    }
}

$('#main').resize(function() {
    nav_page_height();
    check_if_mobile_width();
})

$('nav').resize(function() {
    nav_page_height();
})

function check_if_mobile_width() {
    if ($(window).width() < 979) {
        $.root_.addClass('mobile-view-activated')
    } else if ($.root_.hasClass('mobile-view-activated')) {
        $.root_.removeClass('mobile-view-activated');
    }
}

/* ~ END: NAV OR #LEFT-BAR RESIZE DETECT */

/*
 * DETECT IE VERSION
 * Description: A short snippet for detecting versions of IE in JavaScript
 * without resorting to user-agent sniffing
 * RETURNS:
 * If you're not in IE (or IE version is less than 5) then:
 * //ie === undefined
 *
 * If you're in IE (>=5) then you can determine which version:
 * // ie === 7; // IE7
 *
 * Thus, to detect IE:
 * // if (ie) {}
 *
 * And to detect the version:
 * ie === 6 // IE6
 * ie > 7 // IE8, IE9 ...
 * ie < 9 // Anything less than IE9
 */

// TODO: delete this function later on - no longer needed (?)
var ie = ( function() {

    var undef, v = 3, div = document.createElement('div'), all = div.getElementsByTagName('i');

    while (div.innerHTML = '<!--[if gt IE ' + (++v) + ']><i></i><![endif]-->', all[0]);

    return v > 4 ? v : undef;

}()); // do we need this? 

/* ~ END: DETECT IE VERSION */

/*
 * CUSTOM MENU PLUGIN
 */

$.fn.extend({

    //pass the options variable to the function
    jarvismenu : function(options) {

        var defaults = {
            accordion : 'true',
            speed : 200,
            closedSign : '[+]',
            openedSign : '[-]'
        };

        // Extend our default options with those provided.
        var opts = $.extend(defaults, options);
        //Assign current element to variable, in this case is UL element
        var $this = $(this);

        //add a mark [+] to a multilevel menu
        $this.find("li").each(function() {
            if ($(this).find("ul").size() != 0) {
                //add the multilevel sign next to the link
                $(this).find("a:first").append("<b class='collapse-sign'>" + opts.closedSign + "</b>");

                //avoid jumping to the top of the page when the href is an #
                if ($(this).find("a:first").attr('href') == "#") {
                    $(this).find("a:first").click(function() {
                        return false;
                    });
                }
            }
        });

        //open active level
        $this.find("li.active").each(function() {
            $(this).parents("ul").slideDown(opts.speed);
            $(this).parents("ul").parent("li").find("b:first").html(opts.openedSign);
            $(this).parents("ul").parent("li").addClass("open")
        });

        $this.find("li a").click(function() {

            if ($(this).parent().find("ul").size() != 0) {

                if (opts.accordion) {
                    //Do nothing when the list is open
                    if (!$(this).parent().find("ul").is(':visible')) {
                        parents = $(this).parent().parents("ul");
                        visible = $this.find("ul:visible");
                        visible.each(function(visibleIndex) {
                            var close = true;
                            parents.each(function(parentIndex) {
                                if (parents[parentIndex] == visible[visibleIndex]) {
                                    close = false;
                                    return false;
                                }
                            });
                            if (close) {
                                if ($(this).parent().find("ul") != visible[visibleIndex]) {
                                    $(visible[visibleIndex]).slideUp(opts.speed, function() {
                                        $(this).parent("li").find("b:first").html(opts.closedSign);
                                        $(this).parent("li").removeClass("open");
                                    });

                                }
                            }
                        });
                    }
                }// end if
                if ($(this).parent().find("ul:first").is(":visible") && !$(this).parent().find("ul:first").hasClass("active")) {
                    $(this).parent().find("ul:first").slideUp(opts.speed, function() {
                        $(this).parent("li").removeClass("open");
                        $(this).parent("li").find("b:first").delay(opts.speed).html(opts.closedSign);
                    });

                } else {
                    $(this).parent().find("ul:first").slideDown(opts.speed, function() {
                        /*$(this).effect("highlight", {color : '#616161'}, 500); - disabled due to CPU clocking on phones*/
                        $(this).parent("li").addClass("open");
                        $(this).parent("li").find("b:first").delay(opts.speed).html(opts.openedSign);
                    });
                } // end else
            } // end if
        });
    } // end function
});

/* ~ END: CUSTOM MENU PLUGIN */

/*
 * ELEMENT EXIST OR NOT
 * Description: returns true or false
 * Usage: $('#myDiv').doesExist();
 */

jQuery.fn.doesExist = function() {
    return jQuery(this).length > 0;
};

/* ~ END: ELEMENT EXIST OR NOT */

/*
 * FULL SCREEN FUNCTION
 */

// Find the right method, call on correct element
function launchFullscreen(element) {

    if (!$.root_.hasClass("full-screen")) {

        $.root_.addClass("full-screen");

        if (element.requestFullscreen) {
            element.requestFullscreen();
        } else if (element.mozRequestFullScreen) {
            element.mozRequestFullScreen();
        } else if (element.webkitRequestFullscreen) {
            element.webkitRequestFullscreen();
        } else if (element.msRequestFullscreen) {
            element.msRequestFullscreen();
        }

    } else {

        $.root_.removeClass("full-screen");

        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        }

    }

}

/*
 * ~ END: FULL SCREEN FUNCTION
 */

/*
 * INITIALIZE FORMS
 * Description: Select2, Masking, Datepicker, Autocomplete
 */

function runAllForms() {

    /*
     * SELECT2 PLUGIN
     * Usage:
     * Dependency: js/plugin/select2/
     */
    if ($.fn.select2) {
        $('.select2').each(function() {
            var $this = $(this);
            var width = $this.attr('data-select-width') || '100%';
            //, _showSearchInput = $this.attr('data-select-search') === 'true';
            $this.select2({
                //showSearchInput : _showSearchInput,
                allowClear : true,
                width : width
            })
        })
    }

    /*
     * JQUERY UI DATE
     * Dependency: js/libs/jquery-ui-1.10.3.min.js
     * Usage:
     */
    if ($.fn.datepicker) {
        $('.datepicker').each(function() {

            var $this = $(this);
            var dataDateFormat = $this.attr('data-dateformat') || 'dd.mm.yy';

            $this.datepicker({
                dateFormat : dataDateFormat,
                prevText : '<i class="fa fa-chevron-left"></i>',
                nextText : '<i class="fa fa-chevron-right"></i>',
            });
        })
    }

}

/* ~ END: INITIALIZE FORMS */


/*
 * INITIALIZE JARVIS WIDGETS
 */

// Setup Desktop Widgets
function setup_widgets_desktop() {

    if ($.fn.jarvisWidgets && $.enableJarvisWidgets) {

        $('#widget-grid').jarvisWidgets({

            grid : 'article',
            widgets : '.jarviswidget',
            localStorage : true,
            deleteSettingsKey : '#deletesettingskey-options',
            settingsKeyLabel : 'Reset settings?',
            deletePositionKey : '#deletepositionkey-options',
            positionKeyLabel : 'Reset position?',
            sortable : true,
            buttonsHidden : false,
                // toggle button
            toggleButton : true,
            toggleClass : 'fa fa-minus | fa fa-plus',
            toggleSpeed : 200,
            onToggle : function() {
            },
                // delete btn
            deleteButton : true,
            deleteClass : 'fa fa-times',
            deleteSpeed : 200,
            onDelete : function() {
            },
                // edit btn
            editButton : true,
            editPlaceholder : '.jarviswidget-editbox',
            editClass : 'fa fa-cog | fa fa-save',
            editSpeed : 200,
            onEdit : function() {
            },
                // color button
            colorButton : true,
                // full screen
            fullscreenButton : true,
            fullscreenClass : 'fa fa-resize-full | fa fa-resize-small',
            fullscreenDiff : 3,
            onFullscreen : function() {
            },
                // custom btn
            customButton : false,
            customClass : 'folder-10 | next-10',
            customStart : function() {
                alert('Hello you, this is a custom button...')
            },
            customEnd : function() {
                alert('bye, till next time...')
            },
                // order
            buttonOrder : '%refresh% %custom% %edit% %toggle% %fullscreen% %delete%',
            opacity : 1.0,
            dragHandle : '> header',
            placeholderClass : 'jarviswidget-placeholder',
            indicator : true,
            indicatorTime : 600,
            ajax : true,
            timestampPlaceholder : '.jarviswidget-timestamp',
            timestampFormat : 'Last update: %m%/%d%/%y% %h%:%i%:%s%',
            refreshButton : true,
            refreshButtonClass : 'fa fa-refresh',
            labelError : 'Sorry but there was a error:',
            labelUpdated : 'Last Update:',
            labelRefresh : 'Refresh',
            labelDelete : 'Delete widget:',
            afterLoad : function() {
            },
            rtl : false, // best not to toggle this!
            onChange : function() {

            },
            onSave : function() {

            },
            ajaxnav : $.navAsAjax // declears how the localstorage should be saved

        });

    }

}

// Setup Desktop Widgets
function setup_widgets_mobile() {

    if ($.enableMobileWidgets && $.enableJarvisWidgets) {
        setup_widgets_desktop();
    }

}

/* ~ END: INITIALIZE JARVIS WIDGETS */

/*
 * LOAD SCRIPTS
 * Usage:
 * Define function = myPrettyCode ()...
 * loadScript("js/my_lovely_script.js", myPrettyCode);
 */

var jsArray = {};

function loadScript(scriptName, callback) {

    if (!jsArray[scriptName]) {
        jsArray[scriptName] = true;

        // adding the script tag to the head as suggested before
        var body = document.getElementsByTagName('body')[0];
        var script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = scriptName;

        // then bind the event to the callback function
        // there are several events for cross browser compatibility
        //script.onreadystatechange = callback;
        script.onload = callback;

        // fire the loading
        body.appendChild(script);

    } else if (callback) {// changed else to else if(callback)
        //console.log("JS file already added!");
        //execute function
        callback();
    }

}

/* ~ END: LOAD SCRIPTS */


/*
 * PAGE SETUP
 * Description: fire certain scripts that run through the page
 * to check for form elements, tooltip activation, popovers, etc...
 */
function pageSetUp() {

    if ($.device === "desktop"){
        // is desktop

        // activate tooltips
        $("[rel=tooltip]").tooltip();

        // activate popovers
        $("[rel=popover]").popover({container: 'body'});

        // activate popovers with hover states
        $("[rel=popover-hover]").popover({
            trigger : "hover",
            container: 'body',
        });


        // setup widgets
        setup_widgets_desktop();

        //setup nav height (dynamic)
        nav_page_height();

        // run form elements
        runAllForms();

    } else {

        // is mobile

        // activate popovers
        $("[rel=popover]").popover();

        // activate popovers with hover states
        $("[rel=popover-hover]").popover({
            trigger : "hover"
        });

        // setup widgets
        setup_widgets_mobile();

        //setup nav height (dynamic)
        nav_page_height();

        // run form elements
        runAllForms();

    }

}

// Keep only 1 active popover per trigger - also check and hide active popover if user clicks on document
$('body').on('click', function(e) {
    $('[rel="popover"]').each(function() {
        //the 'is' for buttons that trigger popups
        //the 'has' for icons within a button that triggers a popup
        if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
            $(this).popover('hide');
        }
    });
}); 
