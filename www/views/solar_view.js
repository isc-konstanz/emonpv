const LOCAL_CACHE_KEY = 'solar_systems_collapsed';
const INTERVAL_RESULTS = 5000;
const INTERVAL_REDRAW = 15000;
var redrawTime = new Date().getTime();
var redraw = false;
var scrolled = false;
var updater;
var timeout;

var collapsed = [];

//---------------------------------------------------------------------------------------------
//Configure solar systems
//---------------------------------------------------------------------------------------------
var view = new Vue({
    el: "#solar-view",
    data: {
        systems: {},
        inverters: {},
        modules: {},
        loaded: false
    },
    computed: {
        systemCount: function() {
            return Object.keys(this.systems).length;
        }
    },
    methods: {
        scroll: function() {
            window.clearTimeout(timeout);
            timeout = window.setTimeout(function() {
                scrolled = window.scrollY > 45;
            }, 100);
        },
        toggleCollapse: function(event, id) {
            window.clearTimeout(timeout);
            timeout = window.setTimeout(function() {
                let shown = $('#solar-system'+id).hasClass('in');
                let index = collapsed.indexOf(id);
                if ((index > -1) == shown) {
                    if (shown) {
                        collapsed.splice(index, 1);
                        $('#solar-system'+id+'-icon').html("<use xlink:href='#icon-chevron-up' />");
                    }
                    else {
                        collapsed.push(id);
                        $('#solar-system'+id+'-icon').html("<use xlink:href='#icon-chevron-down' />");
                    }
                    if (!Array.isArray(collapsed)) {
                        collapsed = [];
                    }
                    docCookies.setItem(LOCAL_CACHE_KEY, JSON.stringify(collapsed));
                }
            }, 100);
        },
        isCollapsed: function(id) {
            return collapsed.indexOf(id) > -1
        }
    },
    created() {
        window.addEventListener('scroll', this.scroll);
    },
    destroyed() {
        window.removeEventListener('scroll', this.scroll);
    }
});

setTimeout(function() {
    solar.list(function(result) {
        if (docCookies.hasItem(LOCAL_CACHE_KEY)) {
            var cache = JSON.parse(docCookies.getItem(LOCAL_CACHE_KEY));
            if (Array.isArray(cache)) {
                collapsed = cache;
            }
            else {
                collapsed = [];
            }
        }
        else {
            for (var s in result) {
                var system = result[s];
                if (collapsed.indexOf(system.id) === -1) {
                    collapsed.push(system.id);
                }
            }
        }
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

function draw(result) {
    view.systems = {};
    view.inverters = {};
    view.modules = {};

    for (var s in result) {
        var system = result[s];
        for (var i in system['inverters']) {
            var inverter = system['inverters'][i];
            for (var m in inverter['modules']) {
                var module = inverter['modules'][m];
                view.modules[module.id] = module;
            }
            delete inverter['modules'];
            view.inverters[inverter.id] = inverter;
        }
        delete system['inverters'];
        view.systems[system.id] = system;
    }
    view.loaded = true;

    // TODO: move this to vue section
    $(".solar-inverter-img img").hover(function() {
    	let img = $(this);
    	img.attr('src', img.attr('src').replace("mono", "blue"));
    }, function() {
    	let img = $(this);
    	img.attr('src', img.attr('src').replace("blue", "mono"));
    });
}
