var solar_system = {

    map: null,
    system: null,

    newConfig: function() {
        solar_system.system = null;
        solar_system.drawConfig();
    },

    openConfig: function(system) {
        solar_system.system = system;
        solar_system.drawConfig(system);
    },

    drawConfig: function(system = null) {
        var modal = $("#system-config-modal").modal('show');
        if (system == null) {
            $('#system-config-label').html('Create system');
            $('#system-config-delete').hide();
            $('#system-config-save').prop('disabled', true);
            $('#system-config-save').html('Create');

            $('#system-model').val('').addClass('select-default');
            $('#system-model-tooltip').hide();
            $('#system-name').val('');
            $('#system-description').val('').hide();
            $('#system-latitude').val('');
            $('#system-longitude').val('');
            $('#system-altitude').val('');
            $('#system-albedo').val('');
            
            $("#settings-collapse-icon").html('<use xlink:href="#icon-chevron-down" />');
            $("#system-location-icon").html('<use xlink:href="#icon-checkmark" />');
            $("#system-location .advanced").hide();
            $("#system-location").show();
            solar_system.drawMap(true);
        }
        else {
            $('#system-config-label').html('Configure system: <b>'+system.name+'</b>');
            $('#system-config-delete').show();
            $('#system-config-save').prop('disabled', false);
            $('#system-config-save').html('Save');
            
            $('#system-model').val(system.model).removeClass('select-default');
            $('#system-model-tooltip').tooltip({title: "Placeholder description for the <b>"+$('#system-model option:selected', this).text()+"</b> model.", 
                                                html:true, container:modal}).show();
            
            $('#system-name').val(system.name);
            
            var description = system.description != null ? system.description : '';
            $('#system-description').val(description).toggle(description != '');
            
            $('#system-latitude').val(system.location.latitude);
            $('#system-longitude').val(system.location.longitude);
            
            var altitude = system.location.altitude != null ? system.location.altitude : '';
            var albedo = system.location.albedo != null ? system.location.albedo : '';
            $("#system-location .advanced").toggle(altitude != '' || albedo != '');
            $('#system-altitude').val(altitude);
            $('#system-albedo').val(albedo);
            
            $("#settings-collapse-icon").html('<use xlink:href="#icon-chevron-right" />');
            $("#system-location-icon").html('<use xlink:href="#icon-cog" />');
            $("#system-location").hide();
            solar_system.drawMap(false);
        }
        $('#system-name-tooltip').tooltip({html:true, container:modal});
        $('#system-location-tooltip').tooltip({html:true, container:modal});
        
        solar_system.registerConfigEvents();
    },

    saveConfig: function() {
        var model = $('#system-model').val();
        var name = $('#system-name').val();
        var desc = $('#system-description').val();
        
        var lat = $('#system-latitude').val();
        var lng = $('#system-longitude').val();
        var alt = $('#system-altitude').val();
        var alb = $('#system-albedo').val();
        
        if (solar_system.system == null) {
            var location = {
                    longitude: lng,
                    latitude: lat,
                    altitude: alt,
                    albedo: alb
            };
            solar.system.create(model, name, desc, location, solar_system.closeConfig);
        }
        else {
            var fields = {};
            if (dialog.system.model != model) fields['model'] = model;
            if (dialog.system.name != name) fields['name'] = name;
            if (dialog.system.description != desc) fields['description'] = desc;
            
            if (dialog.system.latitude != lat) fields['latitude'] = lat;
            if (dialog.system.longitude != lng) fields['longitude'] = lng;
            if (dialog.system.altitude != alt) fields['altitude'] = alt;
            if (dialog.system.albedo != alb) fields['albedo'] = alb;
            
            solar.system.set(solar_system.system.id, fields, solar_system.closeConfig);
        }
    },

    verifyConfig: function() {
        if ($('#system-model')[0].checkValidity() &&
                $('#system-name')[0].checkValidity() &&
                $('#system-latitude')[0].checkValidity() &&
                $('#system-longitude')[0].checkValidity()) {
            
            $('#system-config-save').prop("disabled", false);
            return true;
        }
        else {
            $('#system-config-save').prop("disabled", true);
            return false;
        }
    },

    registerConfigEvents: function() {

        $("#system-model").off('change').on('change', function() {
            var title = $('#system-model option:selected', this).text();
            var tooltip = $('#system-model-tooltip').tooltip({title: "Placeholder description for the <b>"+title+"</b> model.",
                        html:true,
                        container:'#system-config-modal'})
            
            if (!tooltip.is(":visible")) {
                tooltip.animate({width:'toggle'}, 250);
                $(this).removeClass('select-default');
            }
            solar_system.verifyConfig();
        });

        $("#system-description-icon").off('click').on('click', function() {
            if (!$(this).data('show')) {
                $("#system-description-icon").html('<use xlink:href="#icon-cross" />');
                $("#system-description").animate({width:'toggle'}, 250);
                $(this).data('show', true);
            }
            else {
                $("#system-description-icon").html('<use xlink:href="#icon-plus" />');
                $("#system-description").animate({width:'toggle'}, 250).val("");
                $(this).data('show', false);
            }
        });

        $("#system-location-icon").off('click').on('click', function() {
            if (!$(this).data('show')) {
                $("#settings-collapse-icon").html('<use xlink:href="#icon-chevron-down" />');
                $("#system-location-icon").html('<use xlink:href="#icon-checkmark" />');
                $("#system-location").animate({height:'toggle'}, 250);
                solar_system.drawMap(true);
                $(this).data('show', true);
            }
            else {
                $("#settings-collapse-icon").html('<use xlink:href="#icon-chevron-right" />');
                $("#system-location-icon").html('<use xlink:href="#icon-cog" />');
                $("#system-location").animate({height:'toggle'}, 250).val("");
                solar_system.drawMap(false);
                $(this).data('show', false);
            }
        });

        $("#system-coordinates-icon").off('click').on('click', function() {
            if (!$(this).data('show')) {
                $("#system-coordinates-icon").html('<use xlink:href="#icon-cross" />');
                $("#system-location .advanced").animate({width:'toggle'}, 250);
                $(this).data('show', true);
            }
            else {
                $("#system-coordinates-icon").html('<use xlink:href="#icon-plus" />');
                $("#system-location .advanced").animate({width:'toggle'}, 250).val("");
                $(this).data('show', false);
            }
        });

        $("#system-config-modal").off('input').on('input', 'input[required]', function() {
            var self = this;
            if (solar_system.timeout != null) {
                clearTimeout(solar_system.timeout);
            }
            solar_system.timeout = setTimeout(function() {
                solar_system.timeout = null;
                solar_system.verifyConfig();
                
            }, 250);
        });

        $("#system-config-save").off('click').on('click', function() {
            solar_system.saveConfig();
        });
    },

    closeConfig: function(result) {
        $('#system-config-loader').hide();
        
        if (typeof result.success !== 'undefined' && !result.success) {
            alert('Solar system could not be configured:\n'+result.message);
            return false;
        }
        update();
        $('#system-config-modal').modal('hide');
    },

    openDeletion: function(system) {
        solar_system.system = system;
        
        $('#system-delete-modal').modal('show');
        $('#system-delete-label').html('Delete system');
        $("#system-delete-confirm").off('click').on('click', function() {
            $('#system-delete-loader').show();
            
            solar.system.remove(solar_system.system.id, function(result) {
                $('#system-delete-loader').hide();
                
                if (typeof result.success !== 'undefined' && !result.success) {
                    alert('Unable to delete system:\n'+result.message);
                    return false;
                }
                let systems = view.systems;
                delete systems[solar_system.system.id];
                draw(systems);
                $('#system-delete-modal').modal('hide');
            });
        });
    },

    drawMap: function(advanced=false) {
        if (solar_system.map == null) {
            var map = L.map('system-map');
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);
            map.addControl(new L.Control.Search({
                url: 'https://nominatim.openstreetmap.org/search?format=json&q={s}',
                jsonpParam: 'json_callback',
                propertyName: 'display_name',
                propertyLoc: ['lat','lon'],
                autoCollapse: true,
                autoResize: true,
                minLength: 2,
                marker: false,
                moveToLocation: solar_system.onMapLocation
            }));
            
            $("#system-latitude, #system-longitude").off('keyup').on('keyup', function(e) {
                var self = this;
                if (solar_system.timeout != null) {
                    clearTimeout(solar_system.timeout);
                }
                solar_system.timeout = setTimeout(function() {
                    solar_system.timeout = null;
                    
                    var latlng = {
                        lat: $('#system-latitude').val(),
                        lng: $('#system-longitude').val()
                    };
                    solar_system.map.setView(latlng, 12);
                    solar_system.drawMapMarker(latlng);
                    
                }, 250);
            });
            solar_system.map = map;
        }
        if (advanced) {
            $("#system-map").addClass('advanced');
            
            solar_system.map.on('click', solar_system.onMapClick);
            solar_system.map.dragging.enable();
            solar_system.map.touchZoom.enable();
            solar_system.map.doubleClickZoom.enable();
            solar_system.map.scrollWheelZoom.enable();
            solar_system.map.boxZoom.enable();
            solar_system.map.keyboard.enable();
            if (solar_system.map.tap) {
                solar_system.map.tap.enable();
            }
        }
        else {
            $("#system-map").removeClass('advanced');
            
            solar_system.map.off('click');
            solar_system.map.dragging.disable();
            solar_system.map.touchZoom.disable();
            solar_system.map.doubleClickZoom.disable();
            solar_system.map.scrollWheelZoom.disable();
            solar_system.map.boxZoom.disable();
            solar_system.map.keyboard.disable();
            if (solar_system.map.tap) {
                map.tap.disable();
            }
        }
        setTimeout(function() { solar_system.drawMapLocation() }, 250);
    },

    drawMapLocation: function() {
        solar_system.map.invalidateSize();
        
        // If nothing can be found, use ISC Konstanz as default location
        var location = {
            lat: $('#system-latitude').val(),
            lng: $('#system-longitude').val()
        };
        if (location.lat == '' || location.lng == '') {
            if (solar_system.system != null 
                    && typeof solar_system.system.location !== 'undefined') {
                location.lat = solar_system.system.location.latitude;
                location.lng = solar_system.system.location.longitude;
                solar_system.drawMapMarker(location);
            }
            else if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    location.lat = position.coords.latitude;
                    location.lng = position.coords.longitude;
                    location.al = position.coords.altitude;
                    
                    solar_system.map.setView(location, 12);
                });
                return;
            }
            else {
                // If nothing can be found, use ISC Konstanz as default location
                location.lat = 47.67158;
                location.lng = 9.15179;
            }
        }
        solar_system.map.setView(location, 12);
    },

    drawMapMarker: function(latlng, title='System location') {
        if (solar_system.mapMarker != null) {
            solar_system.map.removeLayer(solar_system.mapMarker);
        }
        solar_system.mapMarker = L.marker(latlng, {
            draggable: true,
            title: title
        }).addTo(solar_system.map);
    },

    onMapLocation: function(latlng, title='System location', map=solar_system.map) {
        solar_system.map.setView(latlng);
        solar_system.drawMapMarker(latlng, title);
        $('#system-latitude').val(parseFloat(latlng['lat'].toFixed(5)));
        $('#system-longitude').val(parseFloat(latlng['lng'].toFixed(5)));
    },

    onMapClick: function(e) {
        solar_system.onMapLocation(e.latlng);
    }
}
