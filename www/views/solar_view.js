const INTERVAL_RESULTS = 5000;
const INTERVAL_REDRAW = 15000;
var redrawTime = new Date().getTime();
var redraw = false;
var updater;
var timeout;

var systems = {};
var inverters = {};
var modules = {};

var collapsed = {};

setTimeout(function() {
    solar.list(function(result) {
        draw(result);
        updaterStart();
    });
}, 100);

function update() {
    solar.list(draw);
}

function updateView() {
    var time = new Date().getTime();
    if (time - redrawTime >= INTERVAL_REDRAW) {
        redrawTime = time;
        redraw = true;
        
        solar.list(function(result) {
            draw(result);
            redraw = false;
        });
    }
//    else if (!redraw) {
//        if ((time - redrawTime) % INTERVAL_RESULTS < 1000) {
//            // TODO: draw simulation results
//        }
//    }
}

function updaterStart() {
    if (updater != null) {
        clearInterval(updater);
    }
    updater = setInterval(updateView, 1000);
}

function updaterStop() {
    clearInterval(updater);
    updater = null;
}

//---------------------------------------------------------------------------------------------
// Draw solar systems
//---------------------------------------------------------------------------------------------
function draw(result) {
    $('#solar-loader').hide();
    $("#solar-systems").empty();
    
    if (typeof result.success !== 'undefined' && !result.success) {
        //alert("Error:\n" + result.message);
        return;
    }
    else if (result.length == 0) {
        $("#solar-header").hide();
        $("#solar-actions").hide();
        $("#solar-footer").show();
        $("#solar-none").show();
        
        return;
    }
    
    $("#solar-header").show();
    $("#solar-actions").show();
    $("#solar-footer").show();
    $("#solar-none").hide();
    
    systems = {};
    inverters = {};
    modules = {};
    
    for (var i in result) {
        drawSystem(result[i]);
    }
    registerEvents();
}

function drawSystem(system) {
    if (typeof collapsed[system.id] === 'undefined') {
        collapsed[system.id] = true;
    }
    
    $("#solar-systems").append(
        "<div class='system group'>" +
            "<div id='solar-system"+system.id+"-header' class='group-header' data-toggle='collapse' data-target='#solar-system"+system.id+"'>" +
                "<div class='group-item' data-id='"+system.id+"'>" +
                    "<div class='group-collapse'>" +
                        "<svg id='solar-system"+system.id+"-icon' class='icon icon-collapse'>" +
	                        "<use xlink:href='#icon-chevron-right' />" +
	                    "</svg>" +
                    "</div>" +
                    "<div class='name'><span>"+system.name+(system.description.length>0 ? ":" : "")+"</span></div>" +
                    "<div class='description'><span>"+system.description+"</span></div>" +
                    "<div class='group-grow'></div>" +
                    "<div class='group-menu dropdown action'>" +
                        "<svg class='dropdown-toggle icon icon-menu' data-toggle='dropdown'>" +
	                        "<use xlink:href='#icon-dots-vertical' />" +
	                    "</svg>" +
	                    "<ul class='dropdown-menu pull-right'>" +
                            "<li><a class='system-config'>Edit system</a></li>" +
	                        "<li><a class='system-export' disabled>Export results</a></li>" +
	                    "</ul>" +
                    "</div>" +
                "</div>" +
            "</div>" +
            "<div id='solar-system"+system.id+"' class='group-body collapse "+(collapsed[system.id] ? '' : 'in')+"'>" +
	            "<div class='alert alert-comment'>" +
	            	"Placeholder" +
	            "</div>" +
    		"</div>" +
        "</div>"
    );
    for (var i in systems['inverters']) {
        drawInverter(systems['inverters'][i]);
    }
    delete systems['inverters'];
    systems[systems.id] = systems;
}

function drawInverter(inverter) {
	
}

function registerEvents() {
    
}

$("#system-new").on('click', function () {
    solar_system.newSystem();
});
