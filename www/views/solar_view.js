const LOCAL_CACHE_KEY = 'solar_systems_collapsed';
const INTERVAL_RESULTS = 15000;
const INTERVAL_REDRAW = 60000;
var redrawTime = new Date().getTime();
var redraw = false;
var scrolled = false;
var updater;
var timeout;

var running = [];
var collapsed = [];

//---------------------------------------------------------------------------------------------
//Configure solar systems
//---------------------------------------------------------------------------------------------
var view = new Vue({
    el: "#solar-view",
    data: {
        systems: {},
        loaded: false,
        render: false
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
        getModule: function(type) {
            return modules[type.split('/')[0]][type];
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
        isConfigured: function(system) {
            if (system.inverters) {
                for (var i in system.inverters) {
                    if (view.hasConfigs(system.inverters[i])) {
                        return true;
                    }
                }
            }
            return false
        },
        isError: function(system) {
            return system.results.status == 'error';
        },
        isSuccess: function(system) {
            return system.results.status == 'success';
        },
        isRunning: function(system) {
            return system.results.status == 'running';
        },
        isNew: function(system) {
            return system.results.status == 'created';
        },
        getEnergyUnit: function(value) {
            let unit;
            if (value >= 1E7) {
                unit = 'GWh';
            }
            else if (value >= 1E4) {
                unit = 'MWh';
            }
            else {
                unit = 'kWh';
            }
            return unit;
        },
        getEnergy: function(value) {
            let energy = value;
            while (energy > 1E4) {
                energy /= 1000;
            }
            if (energy < value) {
                return Number((energy).toFixed(1));
            }
            return Number((energy).toFixed(0));
        },
        getNumber: function(value, decimals) {
            if (!decimals) {
                if (value > 10) {
                    decimals = 0;
                }
                else if (value > 1) {
                    decimals = 1;
                }
                else {
                    decimals = 2;
                }
            }
            return Number((value).toFixed(decimals));
        },
        hasConfigs: function(inverter) {
            return Object.keys(inverter.configs).length > 0;
        },
        getCount: function(configs) {
            let rows = configs.rows;
            let count = rows.count
                      * rows.modules;
            
            if (rows.stack != null) {
                count *= rows.stack;
            }
            return count;
        },
        setCount: function(event, element, type, field='count') {
            let input = $(event.currentTarget);
            let value = input.val();
            
            input.width((1+value.length)+'ch');
            if (input[0].checkValidity()) {
                element[field] = value;
                window.clearTimeout(timeout);
                timeout = window.setTimeout(function() {
                    let fields = {};
                    fields[field] = value;
                    solar[type].update(element.id, fields);
                    
                }, 250);
            }
        },
        run: function(system) {
            solar.system.run(system.id, function() {
                view.systems[system.id].results = {
                    'status': 'running',
                    'progress': 0,
                    'progressBarWidth': '0%',
                    'progressBarClass': 'progress-info active',
                    'progressBarShow': true
                };
                running.push(system.id);
            });
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
    solar_configs.drawSidebar(modules);
}, 100);

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
    else if (!redraw) {
        if ((time - redrawTime) % INTERVAL_RESULTS < 1000) {
            solar.system.list(updateSystems);
        }
        else if (running.length > 0) {
            for (var i=0; i<running.length; i++) {
                solar.system.get(running[i], updateSystem);
            }
        }
    }
}

function updateSystems(systems) {
    if (systems.hasOwnProperty('success') && !systems.success) return;
    
    running = []
    for (var s in systems) {
        var system = systems[s];
        var results = decodeResults(system);
        if (view.systems.hasOwnProperty(system.id)) {
            view.systems[system.id].results = results;
            
            if (results.status == 'running') {
                running.push(system.id);
            }
        }
    }
}

function updateSystem(system) {
    if (system.hasOwnProperty('success') && !system.success) return;
    
    var results = decodeResults(system);
    if (view.systems.hasOwnProperty(system.id)) {
        view.systems[system.id].results = results;
    }
}

function decodeResults(system) {
    var show = false;
    var type = 'default';
    var progress = 0;
    
    var results = system.results;
    if (results.status == 'success') {
        if (view.systems.hasOwnProperty(system.id) && view.systems[system.id].results.status != 'success') {
            show = true;
        }
        type = 'success';
        progress = 100;
    }
    else if (results.status == 'error') {
        show = true;
        type = 'danger';
        progress = 100;
    }
    else if (results.status == 'running') {
        if (typeof results.progress !== 'undefined') {
            // If the progress value equals zero, set it to 5%, so the user can see the bar already
            progress = results.progress > 1 ? results.progress : 1;
        }
        else {
            progress = 0;
        }
        show = true;
        type = 'info active';
    }
    results.progressBarWidth = progress+'%';
    results.progressBarClass = 'progress-'+type;
    results.progressBarShow = show;
    
    return results;
}

function draw(result) {
    if (result.hasOwnProperty('success') && !result.success) return;
    
    running = [];
    
    var systemIds = [];
    for (var s in result) {
        var system = result[s];
        var inverters = {};
        for (var i in system.inverters) {
            var inverter = system.inverters[i];
            var items = {};
            for (var c in inverter.configs) {
                var configs = inverter.configs[c];
                items[configs.id] = configs;
            }
            inverter.configs = items;
            inverters[inverter.id] = inverter;
        }
        system.inverters = inverters;
        system.results = decodeResults(system);
        systemIds.push(system.id);
        if (system.results.status == 'running') {
            running.push(system.id);
        }
        
        view.$set(view.systems, system.id, system);
    }
    if (systemIds.length != Object.keys(view.systems).length) {
        for (var systemId in Object.keys(view.systems)) {
            if (!systemIds.includes(systemId)) {
                delete view.systems[systemId];
            }
        }
    }
    if (!view.loaded) {
        view.loaded = true;
    }
}
