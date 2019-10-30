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
                let shown = $('#system'+id).hasClass('in');
                let index = collapsed.indexOf(id);
                if ((index > -1) == shown) {
                    if (shown) {
                        collapsed.splice(index, 1);
                        $('#system'+id+'-icon').html("<use xlink:href='#icon-chevron-up' />");
                    }
                    else {
                        collapsed.push(id);
                        $('#system'+id+'-icon').html("<use xlink:href='#icon-chevron-down' />");
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
        },
        setCount: function(event, parent, element, type) {
            let input = $(event.currentTarget);
            let value = input.val();
            if (value >= 1000) {
                input.width(40);
            }
            else if (value >= 100) {
                input.width(30);
            }
            else if (value >= 10) {
                input.width(20);
            }
            else {
                input.width(14);
            }
            if (input[0].checkValidity()) {
                element.count = value;
                window.clearTimeout(timeout);
                timeout = window.setTimeout(function() {
                	solar[type].update(parent, element.id, {count: value});
                	
                }, 250);
            }
        },
        run: function(system) {
        	$("#system"+system.id+"-results").show();
        }
    },
    created() {
        $(document).on({
            mouseenter: function() {
                let img = $(this).find('.clipart img');
                img.attr('src', img.attr('src').replace("mono", "blue"));
            },
            mouseleave: function() {
                let img = $(this).find('.clipart').find('img');
                img.attr('src', img.attr('src').replace("blue", "mono"));
            }
        }, ".inverter");
        window.addEventListener('scroll', this.scroll);
    },
    destroyed() {
        window.removeEventListener('scroll', this.scroll);
    }
});

setTimeout(function() {
    solar.system.list(function(result) {
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
    solar.system.list(draw);
}

function updateView() {
    var time = new Date().getTime();
    if (time - redrawTime >= INTERVAL_REDRAW) {
        redrawTime = time;
        redraw = true;
        
        solar.system.list(function(result) {
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
    for (var s in result) {
        var system = result[s];
        var inverters = {};
        for (var i in system.inverters) {
            var inverter = system.inverters[i];
            var modules = {};
            for (var m in inverter.modules) {
                var module = inverter.modules[m];
                modules[module.id] = module;
            }
            inverter.modules = modules;
            inverters[inverter.id] = inverter;
        }
        system.inverters = inverters;
        
        view.systems[system.id] = system;
    }
    view.loaded = true;
}
