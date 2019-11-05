
(function (factory) {
    if ( typeof define === 'function' && define.amd ) {
        // AMD. Register as an anonymous module.
        define(['jquery'], factory);
    } else if (typeof exports === 'object') {
        // Node/CommonJS style for Browserify
        module.exports = factory;
    } else {
        // Browser globals
        factory(jQuery);
    }
}(function ($) {

    var toFix  = ['wheel', 'mousewheel', 'DOMMouseScroll', 'MozMousePixelScroll'],
        toBind = ( 'onwheel' in document || document.documentMode >= 9 ) ?
                    ['wheel'] : ['mousewheel', 'DomMouseScroll', 'MozMousePixelScroll'],
        slice  = Array.prototype.slice,
        nullLowestDeltaTimeout, lowestDelta;

    if ( $.event.fixHooks ) {
        for ( var i = toFix.length; i; ) {
            $.event.fixHooks[ toFix[--i] ] = $.event.mouseHooks;
        }
    }

    var special = $.event.special.mousewheel = {
        version: '3.1.12',

        setup: function() {
            if ( this.addEventListener ) {
                for ( var i = toBind.length; i; ) {
                    this.addEventListener( toBind[--i], handler, false );
                }
            } else {
                this.onmousewheel = handler;
            }
            // Store the line height and page height for this particular element
            $.data(this, 'mousewheel-line-height', special.getLineHeight(this));
            $.data(this, 'mousewheel-page-height', special.getPageHeight(this));
        },

        teardown: function() {
            if ( this.removeEventListener ) {
                for ( var i = toBind.length; i; ) {
                    this.removeEventListener( toBind[--i], handler, false );
                }
            } else {
                this.onmousewheel = null;
            }
            // Clean up the data we added to the element
            $.removeData(this, 'mousewheel-line-height');
            $.removeData(this, 'mousewheel-page-height');
        },

        getLineHeight: function(elem) {
            var $elem = $(elem),
                $parent = $elem['offsetParent' in $.fn ? 'offsetParent' : 'parent']();
            if (!$parent.length) {
                $parent = $('body');
            }
            return parseInt($parent.css('fontSize'), 10) || parseInt($elem.css('fontSize'), 10) || 16;
        },

        getPageHeight: function(elem) {
            return $(elem).height();
        },

        settings: {
            adjustOldDeltas: true, // see shouldAdjustOldDeltas() below
            normalizeOffset: true  // calls getBoundingClientRect for each event
        }
    };

    $.fn.extend({
        mousewheel: function(fn) {
            return fn ? this.bind('mousewheel', fn) : this.trigger('mousewheel');
        },

        unmousewheel: function(fn) {
            return this.unbind('mousewheel', fn);
        }
    });


    function handler(event) {
        var orgEvent   = event || window.event,
            args       = slice.call(arguments, 1),
            delta      = 0,
            deltaX     = 0,
            deltaY     = 0,
            absDelta   = 0,
            offsetX    = 0,
            offsetY    = 0;
        event = $.event.fix(orgEvent);
        event.type = 'mousewheel';

        // Old school scrollwheel delta
        if ( 'detail'      in orgEvent ) { deltaY = orgEvent.detail * -1;      }
        if ( 'wheelDelta'  in orgEvent ) { deltaY = orgEvent.wheelDelta;       }
        if ( 'wheelDeltaY' in orgEvent ) { deltaY = orgEvent.wheelDeltaY;      }
        if ( 'wheelDeltaX' in orgEvent ) { deltaX = orgEvent.wheelDeltaX * -1; }

        // Firefox < 17 horizontal scrolling related to DOMMouseScroll event
        if ( 'axis' in orgEvent && orgEvent.axis === orgEvent.HORIZONTAL_AXIS ) {
            deltaX = deltaY * -1;
            deltaY = 0;
        }

        // Set delta to be deltaY or deltaX if deltaY is 0 for backwards compatabilitiy
        delta = deltaY === 0 ? deltaX : deltaY;

        // New school wheel delta (wheel event)
        if ( 'deltaY' in orgEvent ) {
            deltaY = orgEvent.deltaY * -1;
            delta  = deltaY;
        }
        if ( 'deltaX' in orgEvent ) {
            deltaX = orgEvent.deltaX;
            if ( deltaY === 0 ) { delta  = deltaX * -1; }
        }

        // No change actually happened, no reason to go any further
        if ( deltaY === 0 && deltaX === 0 ) { return; }

        // Need to convert lines and pages to pixels if we aren't already in pixels
        // There are three delta modes:
        //   * deltaMode 0 is by pixels, nothing to do
        //   * deltaMode 1 is by lines
        //   * deltaMode 2 is by pages
        if ( orgEvent.deltaMode === 1 ) {
            var lineHeight = $.data(this, 'mousewheel-line-height');
            delta  *= lineHeight;
            deltaY *= lineHeight;
            deltaX *= lineHeight;
        } else if ( orgEvent.deltaMode === 2 ) {
            var pageHeight = $.data(this, 'mousewheel-page-height');
            delta  *= pageHeight;
            deltaY *= pageHeight;
            deltaX *= pageHeight;
        }

        // Store lowest absolute delta to normalize the delta values
        absDelta = Math.max( Math.abs(deltaY), Math.abs(deltaX) );

        if ( !lowestDelta || absDelta < lowestDelta ) {
            lowestDelta = absDelta;

            // Adjust older deltas if necessary
            if ( shouldAdjustOldDeltas(orgEvent, absDelta) ) {
                lowestDelta /= 40;
            }
        }

        // Adjust older deltas if necessary
        if ( shouldAdjustOldDeltas(orgEvent, absDelta) ) {
            // Divide all the things by 40!
            delta  /= 40;
            deltaX /= 40;
            deltaY /= 40;
        }

        // Get a whole, normalized value for the deltas
        delta  = Math[ delta  >= 1 ? 'floor' : 'ceil' ](delta  / lowestDelta);
        deltaX = Math[ deltaX >= 1 ? 'floor' : 'ceil' ](deltaX / lowestDelta);
        deltaY = Math[ deltaY >= 1 ? 'floor' : 'ceil' ](deltaY / lowestDelta);

        // Normalise offsetX and offsetY properties
        if ( special.settings.normalizeOffset && this.getBoundingClientRect ) {
            var boundingRect = this.getBoundingClientRect();
            offsetX = event.clientX - boundingRect.left;
            offsetY = event.clientY - boundingRect.top;
        }

        // Add information to the event object
        event.deltaX = deltaX;
        event.deltaY = deltaY;
        event.deltaFactor = lowestDelta;
        event.offsetX = offsetX;
        event.offsetY = offsetY;
        // Go ahead and set deltaMode to 0 since we converted to pixels
        // Although this is a little odd since we overwrite the deltaX/Y
        // properties with normalized deltas.
        event.deltaMode = 0;

        // Add event and delta to the front of the arguments
        args.unshift(event, delta, deltaX, deltaY);

        // Clearout lowestDelta after sometime to better
        // handle multiple device types that give different
        // a different lowestDelta
        // Ex: trackpad = 3 and mouse wheel = 120
        if (nullLowestDeltaTimeout) { clearTimeout(nullLowestDeltaTimeout); }
        nullLowestDeltaTimeout = setTimeout(nullLowestDelta, 200);

        return ($.event.dispatch || $.event.handle).apply(this, args);
    }

    function nullLowestDelta() {
        lowestDelta = null;
    }

    function shouldAdjustOldDeltas(orgEvent, absDelta) {
        // If this is an older event and the delta is divisable by 120,
        // then we are assuming that the browser is treating this as an
        // older mouse wheel event and that we should divide the deltas
        // by 40 to try and get a more usable deltaFactor.
        // Side note, this actually impacts the reported scroll distance
        // in older browsers and can cause scrolling to be slower than native.
        // Turn this off by setting $.event.special.mousewheel.settings.adjustOldDeltas to false.
        return special.settings.adjustOldDeltas && orgEvent.type === 'mousewheel' && absDelta % 120 === 0;
    }

}));

$(document).ready(function(){
var native_width = 0;
var native_height = 0;
var loadLocker = true;
var image_object = null;
var zoom = 2;
qc_saved = true;
nodes = Array.prototype.slice.call(document.getElementById('navigation').children);
currentMetric = document.getElementById("navigation").children[0].innerText.replace(/ /g,"_");
dict_metrics = {};
for (let child of document.getElementById("navigation").children){
    dict_metrics[child.innerText.replace(/ /g,"_")] = 0;
}

showTab(dict_metrics[currentMetric]);
function update(mx, my) {
    var rx = Math.round(mx - $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").width()/(2*zoom))*-1;
    var ry = Math.round(my - $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").height()/(2*zoom))*-1;
    var bgp = rx * zoom + "px " + ry * zoom + "px";
    var bgs = ($(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".small").width() * zoom) + "px " + ($(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".small").height() * zoom) + "px";
    //Time to move the magnifying glass with the mouse
    var px = mx - $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").width()/2;
    var py = my - $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").height()/2;
    //Now the glass moves with the mouse
    //The logic is to deduct half of the glass's width and height from the 
    //mouse coordinates to place it with its center at the mouse coordinates
    
    //If you hover on the image now, you should see the magnifying glass in action
    $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").css({left: px, top: py, backgroundPosition: bgp, backgroundSize: bgs});
}


$('.large').on('mousewheel', function(event) {
    loadLocker = false;
    image_object = new Image();
    image_object.src = $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".small").attr("src");
    native_width = image_object.width;
    native_height = image_object.height;
    if (zoom + event.deltaY > 1 && zoom + event.deltaY < 7) {
        zoom += event.deltaY;
        var magnify_offset = $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).offset();
        update(event.pageX - magnify_offset.left, event.pageY - magnify_offset.top);
    }
});

//Now the mousemove function
$(".magnify").mousemove(function(e){
    if ($("#zoom-button").is(":checked")){
        //When the user hovers on the image, the script will first calculate
    //the native dimensions if they don't exist. Only after the native dimensions
    //are available, the script will show the zoomed version.
    if(!native_width && !native_height)
    {
    //This will create a new image object with the same image as that in .small
    //We cannot directly get the dimensions from .small because of the 
    //width specified to 200px in the html. To get the actual dimensions we have
    //created this image object.
    if (loadLocker) {
        loadLocker = false;
        image_object = new Image();
        image_object.src = $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".small").attr("src");
    }
    //This code is wrapped in the .load function which is important.
    //width and height of the object would return 0 if accessed before 
    //the image gets loaded.
    
    native_width = image_object.width;
    native_height = image_object.height;
    }
    else
    {
    //x/y coordinates of the mouse
    //This is the position of .magnify with respect to the document.
    var magnify_offset = $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).offset();
    //We will deduct the positions of .magnify from the mouse positions with
    //respect to the document to get the mouse positions with respect to the 
    //container(.magnify)
    var mx = e.pageX - magnify_offset.left;
    var my = e.pageY - magnify_offset.top;
    
    //Finally the code to fade out the glass if the mouse is outside the container
    if(mx < $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).width() && my < $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).height() && mx > 0 && my > 0)
    {
        $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").fadeIn(100);
    }
    else
    {
        $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").fadeOut(100);
    }
    if($(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").is(":visible"))
    {
        //The background position of .large will be changed according to the position
        //of the mouse over the .small image. So we will get the ratio of the pixel
        //under the mouse pointer with respect to the image and use that to position the 
        //large image inside the magnifying glass
        var rx = Math.round(mx - $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").width()/(2*zoom))*-1;
        var ry = Math.round(my - $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").height()/(2*zoom))*-1;
        var bgp = rx * zoom + "px " + ry * zoom + "px";
        var bgs = ($(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".small").width() * zoom) + "px " + ($(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".small").height() * zoom) + "px";
        
        //Time to move the magnifying glass with the mouse
        var px = mx - $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").width()/2;
        var py = my - $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").height()/2;
        //Now the glass moves with the mouse
        //The logic is to deduct half of the glass's width and height from the 
        //mouse coordinates to place it with its center at the mouse coordinates
        
        //If you hover on the image now, you should see the magnifying glass in action
        $(document.getElementById(currentMetric).getElementsByClassName('magnify')[dict_metrics[currentMetric]]).children(".large").css({left: px, top: py, backgroundPosition: bgp, backgroundSize: bgs});
    }
    }
    }
}).on("mouseleave", function(){
    native_width = 0;
    native_height = 0;
    loadLocker = true;
});

document.addEventListener("keydown", function(e){
    if (e.ctrlKey && e.which == 37){
        idx = nodes.indexOf(document.getElementById("navigation").getElementsByClassName("active")[0]);
        if (idx - 1 >= 0){
            currentMetric = document.getElementById("navigation").children[idx - 1].innerText.replace(/ /g,"_");
            showTab(dict_metrics[currentMetric]);
            document.getElementById("navigation").children[idx - 1].classList.add("active");
            document.getElementById("navigation").children[idx].classList.remove("active");
            document.getElementsByClassName("tab-pane")[idx - 1].classList.add("active", "in");
            document.getElementsByClassName("tab-pane")[idx].classList.remove("active", "in");
        }
    }
    else if (e.ctrlKey && e.which == 39){
        idx = nodes.indexOf(document.getElementById("navigation").getElementsByClassName("active")[0]);
        if (idx + 1 < document.getElementById("navigation").children.length){
            currentMetric = document.getElementById("navigation").children[idx + 1].innerText.replace(/ /g,"_");
            showTab(dict_metrics[currentMetric]);
            document.getElementById("navigation").children[idx + 1].classList.add("active");
            document.getElementById("navigation").children[idx].classList.remove("active");
            document.getElementsByClassName("tab-pane")[idx + 1].classList.add("active", "in");
            document.getElementsByClassName("tab-pane")[idx].classList.remove("active", "in");
        }
    }
    else if (e.which == 37){
        nextPrev(-1);
    }
    else if (e.which == 39){
        nextPrev(1);
    }
    else if (e.which == 80 || e.which == 49)
    {
        var tab = document.getElementById(currentMetric);
        var subj_id = tab.getElementsByClassName("tab")[dict_metrics[currentMetric]].id;
        update_status(document.getElementById(subj_id + "_pass"));
        qc_saved=false;
    }
    else if (e.which == 87 || e.which == 50)
    {
        var tab = document.getElementById(currentMetric);
        var subj_id = tab.getElementsByClassName("tab")[dict_metrics[currentMetric]].id;
        update_status(document.getElementById(subj_id + "_warning"));
        qc_saved=false;
    }
    else if (e.which == 70 || e.which == 51)
    {
        var tab = document.getElementById(currentMetric);
        var subj_id = tab.getElementsByClassName("tab")[dict_metrics[currentMetric]].id;
        update_status(document.getElementById(subj_id + "_fail"));
        qc_saved=false;
    }
});

$(".js-dropdown").change(function(){
    var x = document.getElementById(currentMetric).getElementsByClassName("tab");
    x[dict_metrics[currentMetric]].style.display = "none";
    x[dict_metrics[currentMetric]].getElementsByClassName("small")[0].removeAttribute("src");
    dict_metrics[currentMetric] = document.getElementById(currentMetric).getElementsByClassName('js-dropdown')[0].selectedIndex;
    showTab(dict_metrics[currentMetric])
});

$(document).on('click', '[data-toggle="lightbox"]', function(event) {
    event.preventDefault();
    $(this).ekkoLightbox();
});
})

function matchCustom(params, data) {
    // If there are no search terms, return all of the data
    if ($.trim(params.term) === '') {
        return data;
    }

    // Do not display the item if there is no 'text' property
    if (typeof data.text === 'undefined') {
        return null;
    }

    // `params.term` should be the term that is used for searching
    // `data.text` is the text that is displayed for the data object
    var index = data.text.toUpperCase().indexOf(params.term.toUpperCase());
    if (index > -1) {
        var modifiedData = $.extend({}, data, true);

        // You can return modified objects from here
        // This includes matching the `children` how you want in nested data sets
        return modifiedData;
    }

    // Return `null` if the term should not be displayed
    return null;
}

function showTab(n) {
    // This function will display the specified tab of the form...
    var tab = document.getElementById(currentMetric);
    var x = tab.getElementsByClassName("tab");
    x[n].style.display = "block";
    curr_subj = document.getElementById("curr_subj");
    curr_subj.innerText = "";
    counter = document.getElementById("counter");
    counter.innerText = "";
    counter.style.backgroundColor = "";
    document.getElementById("curr_subj").style.backgroundColor = "";
    //... and fix the Previous/Next buttons:
    if (tab.getElementsByTagName("button").length > 0){
        curr_subj.innerText = "Current subject: " + x[n].id;
        counter.innerText = (n + 1) + "/" + x.length;
        counter.style.backgroundColor = "#19568b";
        document.getElementById("curr_subj").style.backgroundColor = document.getElementById(x[n].id + "_status").style.backgroundColor;

        var img = x[n].getElementsByClassName("small")[0];

        img.src = img.getAttribute('data-src');

        img.onload = function(){
            max_h = parseInt(img.style.maxHeight.replace("px", ''));
            max_w = parseInt(img.style.maxWidth.replace("px", ''));
            height_diff = max_h - this.height;
            width_diff = max_w - this.width;
            ratio_height = height_diff / this.height;
            ratio_width = width_diff / this.width;
            if (this.width + ratio_height * this.width <= max_w && this.height + ratio_height * this.height <= max_h){
                this.width = this.width + ratio_height * this.width;
                this.height = this.height + ratio_height * this.height;
            }
            else if(this.width + ratio_width * this.width <= max_w && this.height + ratio_width * this.height <= max_h){
                this.width = this.width + ratio_width * this.width;
                this.height = this.height + ratio_width * this.height;
            }
            else{
                console.log("ERROR");
            }
        }

        if (n == 0) {
            tab.getElementsByTagName("button")[0].disabled = true;
        } else {
            tab.getElementsByTagName("button")[0].disabled = false;
        }
        if (n == (x.length - 1)) {
            tab.getElementsByTagName("button")[1].disabled = true;
        } else {
            tab.getElementsByTagName("button")[1].disabled = false;
        }
    }
}

function nextPrev(n) {
    // This function will figure out which tab to display
    var x = document.getElementById(currentMetric).getElementsByClassName("tab");
    // Increase or decrease the current tab by 1:
    if (dict_metrics[currentMetric] + n >= x.length || dict_metrics[currentMetric] + n < 0) {
    // ... the form gets submitted:
    return false;
    }
    
    // Hide the current tab:
    x[dict_metrics[currentMetric]].style.display = "none";
    x[dict_metrics[currentMetric]].getElementsByClassName("small")[0].removeAttribute("src");
    dict_metrics[currentMetric] = dict_metrics[currentMetric] + n;
    // if you have reached the end of the form...
    
    // Otherwise, display the correct tab:
    showTab(dict_metrics[currentMetric]);
    document.getElementById(currentMetric).getElementsByClassName('js-dropdown')[0].selectedIndex = dict_metrics[currentMetric];
    $(document.getElementById(currentMetric).getElementsByClassName('js-dropdown')[0]).trigger("change")
}

/* Set the width of the sidebar to 250px and the left margin of the page content to 250px */
function openNav() {
    document.getElementById("mySidebar").style.width = "35%";
    document.getElementById("main").style.marginLeft = "35%";
}

/* Set the width of the sidebar to 0 and the left margin of the page content to 0 */
function closeNav() {
    document.getElementById("mySidebar").style.width = "0%";
    document.getElementById("main").style.marginLeft = "0%";
}

function doMouseWheel(event) {
    event.preventDefault();
}

function zoom()
{
    var check = document.getElementById("zoom-button").checked;
    if (check)
    {
        $(".magnify").mousewheel(doMouseWheel);
    }
    else
    {
        $(".magnify").unmousewheel(doMouseWheel);
        $(".magnify").children(".large").fadeOut(100);
    }
}

function update_status(object) {
    document.getElementById(object.name+"_status").innerText = object.innerText;
    document.getElementById(object.name+"_status").style.backgroundColor = object.style.backgroundColor;
    document.getElementById("curr_subj").style.backgroundColor = object.style.backgroundColor;
    qc_saved=false;
}

function load_qc(){
    color_dict = {"Pass": "green", "Warning": "orange", "Fail": "red"};
    var selectedFile = document.getElementById('load_file').files[0];
    var reader = new FileReader();
    reader.onload = function(event) { 
        let importedJSON = JSON.parse(event.target.result);
        for (let key in importedJSON){
            document.getElementById(key + "_comments").value = importedJSON[key]["comments"];
            document.getElementById(key + "_status").innerText = importedJSON[key]["status"];
            document.getElementById(key + "_status").style.backgroundColor = color_dict[importedJSON[key]["status"]];
        }
        showTab(dict_metrics[currentMetric])
    };
    reader.readAsText(selectedFile);
}

function save_qc(){
    data = {};
    for (let metrics of document.getElementsByClassName("tab-pane")){
        for (let subject of metrics.getElementsByClassName("tab")){
            if (document.getElementById(subject.id + "_status")){
                data[subject.id] = {}
                data[subject.id]["status"] = document.getElementById(subject.id + "_status").innerText;
                data[subject.id]["comments"] = document.getElementById(subject.id + "_comments").value;
            }
        }
    }
    var jsons = JSON.stringify(data);
    var blob = new Blob([jsons], {type: "application/json"});
    saveAs(blob, "data.json");
    qc_saved = true;
}

function comment_update(){
    qc_saved=false;
}

$(document).ready(function(){
    $(".nav-tabs a").click(function(){
      $(this).tab('show');
    });
    $('#navigation li a').click(function() {
        currentMetric = this.innerText.replace(/ /g,"_");
        showTab(dict_metrics[currentMetric]);
    });
});

window.onbeforeunload = function (e) {
    e = e || window.event;
    if (qc_saved == false) {
        // For IE and Firefox prior to version 4
        if (e) {
            e.returnValue = 'Sure?';
        }

        // For Safari
        return 'Sure?';
    }
};
