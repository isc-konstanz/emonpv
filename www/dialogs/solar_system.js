var solar_system = {

    map: null,
    system: null,

    newConfig: function() {
        solar_system.system = null;
        solar_system.drawConfig();
        solar_system.adjustConfig();
    },

    openConfig: function(system) {
        solar_system.system = system;
        solar_system.drawConfig(system);
        solar_system.adjustConfig();
    },

    drawConfig: function(system = null) {
        var modal = $("#system-config-modal").modal('show');
        if (system == null) {
            $('#system-config-label').html('Create project site');
            $('#system-config-delete').hide();
            $('#system-config-save').prop('disabled', true);
            $('#system-config-save').html('Create');
            
            //$('#system-model').val('').addClass('select-default');
            $('#system-model').val('ViewFactor').removeClass('select-default');
            $('#system-name').val('');
            $('#system-description').val('').hide();
            $("#system-description-icon").html('<use xlink:href="#icon-plus" />').data('show', false);
            
            solar_system.drawCoordinates(system);
        }
        else {
            $('#system-config-label').html('Configure project site: <b>'+system.name+'</b>');
            $('#system-config-delete').show();
            $('#system-config-save').prop('disabled', false);
            $('#system-config-save').html('Save');
            
            $('#system-model').val(system.model).removeClass('select-default');
            $('#system-name').val(system.name);
            
            var description = system.description != null ? system.description : '';
            if (description != '') {
                $("#system-description").val(description).show();
                $("#system-description-icon").html('<use xlink:href="#icon-cross" />').data('show', true);
            }
            else {
                $("#system-description").val(description).hide();
                $("#system-description-icon").html('<use xlink:href="#icon-plus" />').data('show', false);
            }
            solar_system.drawCoordinates(system);
        }
        $('#system-name-tooltip').tooltip({html:true, container:modal});
        $('#system-model-tooltip').tooltip({html:true, container:modal});
        $('#system-location-tooltip').tooltip({html:true, container:modal});
        
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
                $("#system-description").animate({width:'toggle'}, 250);
                $(this).html('<use xlink:href="#icon-cross" />').data('show', true);
            }
            else {
                $("#system-description").animate({width:'toggle'}, 250).val("");
                $(this).html('<use xlink:href="#icon-plus" />').data('show', false);
            }
        });
        
        $("#system-file-input").off('change').on('change', function() {
            if (this.files.length > 0) {
                var file = this.files[0].name;
                $("#system-file-name").width(file.length+'ch').val(file);
                
                solar_system.verifyConfig();
            }
        });
        
        $("#system-coordinates-header .settings-collapse").off('click').on('click', function() {
	        var coordinates = $("#system-coordinates-mode input");
			var coordinatesFlag = !coordinates.is(':checked');
            coordinates.prop('checked', coordinatesFlag);
            solar_system.showCoordinates(coordinatesFlag)
	    });
        
        $("#system-coordinates-mode").off('change').on('change', function() {
	        solar_system.showCoordinates($(this).find('input').is(':checked'));
        });
        
        $("#system-coordinates-icon").off('click').on('click', function() {
            if (!$(this).data('show')) {
                $("#system-coordinates-icon").html('<use xlink:href="#icon-cross" />');
                $("#system-coordinates .advanced").animate({width:'toggle'}, 250);
                $(this).data('show', true);
            }
            else {
                $("#system-coordinates-icon").html('<use xlink:href="#icon-plus" />');
                $("#system-coordinates .advanced").animate({width:'toggle'}, 250).val("");
                $(this).data('show', false);
            }
        });
        
        $("#system-config-modal").off('input').on('input', 'input[required]', function() {
            if (solar_system.timeout != null) {
                clearTimeout(solar_system.timeout);
            }
            solar_system.timeout = setTimeout(function() {
                solar_system.timeout = null;
                solar_system.verifyConfig();
                
            }, 250);
        });
        
        $("#system-config-delete").off('click').on('click', function () {
            $('#system-config-modal').modal('hide');
            
            solar_system.openDeletion(solar_system.system);
        });
        
        $("#system-config-save").off('click').on('click', function() {
            solar_system.saveConfig();
        });
    },

    drawCoordinates: function(system) {
        if (system == null) {
            $('#system-albedo').val('');
            $('#system-latitude').val('');
            $('#system-longitude').val('');
            $('#system-altitude').val('');
            
            $("#system-coordinates-icon").html('<use xlink:href="#icon-plus" />').data('show', false);
            $("#system-coordinates .advanced").hide();

            $("#system-map").hide();
        }
        else {
            $('#system-albedo').val(system.location.albedo);
            $('#system-latitude').val(system.location.latitude);
            $('#system-longitude').val(system.location.longitude);
            
            var altitude = system.location.altitude != null ? system.location.altitude : '';
            if (altitude != '') {
                $("#system-coordinates-icon").html('<use xlink:href="#icon-cross" />').data('show', true);
                $("#system-coordinates .advanced").show();
                $("#system-altitude").show();
            }
            else {
                $("#system-coordinates-icon").html('<use xlink:href="#icon-plus" />').data('show', false);
                $("#system-coordinates .advanced").hide();
                $("#system-altitude").hide();
            }
            $('#system-altitude').val(altitude);

            $("#system-map").show();
        }
        $("#system-collapse-icon").html('<use xlink:href="#icon-chevron-right" />');
        $("#system-coordinates-mode input").prop('checked', false);
        $("#system-coordinates").hide();
        $("#system-file").show();
        $("#system-file-input").val('')
        $("#system-file-name").val('').width('210px');
        
        solar_system.drawMap(false);
    },

    showCoordinates: function(show) {
        if (show) {
            $("#system-collapse-icon").html('<use xlink:href="#icon-chevron-down" />');
            $("#system-coordinates").show();
            $("#system-file").hide();
            $("#system-map").show();
            solar_system.drawMap(true);
        }
        else {
            $("#system-collapse-icon").html('<use xlink:href="#icon-chevron-right" />');
            $("#system-coordinates").hide();
            $("#system-file").show();
            if (solar_system.system == null) $("#system-map").hide();
            solar_system.drawMap(false);
        }
    },

    adjustConfig: function() {
        if ($("#system-config-modal").length > 0) {
            $("#system-config").height($(window).height() - $("#system-config-modal").position().top - 180);
        }
    },

    saveConfig: function() {
        var model = $('#system-model').val();
        var name = $('#system-name').val();
        var description = $('#system-description').val();
        
        var albedo = parseFloat($('#system-albedo').val());
        var invs = true;
        
        if (solar_system.system == null) {
            var location = {
                    'albedo': albedo
            };
            if ($('#system-coordinates-mode').find('input').is(':checked')) {
                var longitude = parseFloat($('#system-longitude').val());
                var latitude = parseFloat($('#system-latitude').val());
                var altitude = $('#system-altitude').val() ? parseFloat($('#system-altitude').val()) : null;
                
                location['longitude'] = longitude;
                location['latitude'] = latitude;
                if (altitude) {
                    location['altitude'] = altitude;
                }
            }
            else {
                location['file'] = 'TMY3'; //$('#system-file-name').val();
            }
            solar.system.create(model, name, description, location, invs, solar_system.closeConfig);
        }
        else {
            var fields = {};
            if (solar_system.system.model != model) fields['model'] = model;
            if (solar_system.system.name != name) fields['name'] = name;
            if (solar_system.system.description != description) fields['description'] = description;
            
            if (solar_system.system.location.albedo != albedo) fields['albedo'] = albedo;
            
            if ($('#system-coordinates-mode').find('input').is(':checked')) {
                var longitude = parseFloat($('#system-longitude').val());
                var latitude = parseFloat($('#system-latitude').val());
                var altitude = $('#system-altitude').val() ? parseFloat($('#system-altitude').val()) : null;
                
                if (solar_system.system.location.latitude != latitude) fields['latitude'] = latitude;
                if (solar_system.system.location.longitude != longitude) fields['longitude'] = longitude;
                if (solar_system.system.location.altitude != altitude) fields['altitude'] = altitude;
            }
            else {
                fields['file'] = 'TMY3';
            }
            if (Object.keys(fields).length > 0) {
                solar.system.update(solar_system.system.id, fields, solar_system.closeConfig);
            }
            else {
                $('#system-config-modal').modal('hide');
            }
        }
    },

    verifyConfig: function() {
        let result = false;
        
        if (document.getElementById('system-model').checkValidity() &&
                document.getElementById('system-name').checkValidity() &&
                document.getElementById('system-albedo').checkValidity()) {
            
            if (($('#system-coordinates-mode').find('input').is(':checked') &&
                    document.getElementById('system-latitude').checkValidity() &&
                    document.getElementById('system-longitude').checkValidity()) ||
                    (document.getElementById('system-file-input').files.length > 0 ||
                    solar_system.system != null)) {
                
                result = true;
            }
        }
        $('#system-config-save').prop("disabled", !result);
        return result;
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
                view.$delete(view.systems, solar_system.system.id);
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
                if (solar_system.mapTimeout != null) {
                    clearTimeout(solar_system.mapTimeout);
                }
                solar_system.mapTimeout = setTimeout(function() {
                    solar_system.mapTimeout = null;
                    
                    var lat = $('#system-latitude').val();
                    var lng = $('#system-longitude').val();
                    if (lat != '' && lat > 0 && 
                        lng != '' && lng > 0) {
                        
                        var latlng = {
                            lat: $('#system-latitude').val(),
                            lng: $('#system-longitude').val()
                        };
                        solar_system.map.setView(latlng, 12);
                        solar_system.drawMapMarker(latlng);
                    }
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
        
        var location = {
            lat: parseFloat($('#system-latitude').val()),
            lng: parseFloat($('#system-longitude').val())
        };
        if (isNaN(location.lat) || isNaN(location.lng)) {
            // If nothing can be found, use ISC Konstanz as default location
            location.lat = 47.67158;
            location.lng = 9.15179;
            
            if (solar_system.system != null 
                    && typeof solar_system.system.location !== 'undefined') {
                location.lat = solar_system.system.location.latitude;
                location.lng = solar_system.system.location.longitude;
            }
            else if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    location.lat = position.coords.latitude;
                    location.lng = position.coords.longitude;
                    location.alt = position.coords.altitude;
                    
                    solar_system.map.setView(location, 12);
                },
                function() {
                    solar_system.map.setView(location, 12);
                });
                
                if (solar_system.mapMarker != null) {
                    solar_system.map.removeLayer(solar_system.mapMarker);
                }
                return;
            }
        }
        solar_system.drawMapMarker(location);
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
        
        solar_system.verifyConfig();
    },

    onMapClick: function(e) {
        solar_system.onMapLocation(e.latlng);
    }
}
