var solar_configs = {

    id: null,
    type: null,
    inverter: null,

    newConfig: function(inverter) {
        solar_configs.id = null;
        solar_configs.type = null;
        solar_configs.inverter = inverter;
        solar_configs.drawConfig();
        solar_configs.adjustConfig();
    },

    openConfig: function(inverter, id, type) {
        solar_configs.id = id;
        solar_configs.type = type;
        solar_configs.inverter = inverter;
        solar_configs.drawConfig(inverter.configs[id]);
        solar_configs.adjustConfig();
    },

    drawConfig: function(configs = null) {
        var modal = $("#module-config-modal").modal('show');
        if (configs == null) {
            $('#module-config-label').html('Create configurations');
            $('#module-config-delete').hide();
            $('#module-config-save').html('Create').prop('disabled', true);
            $('#module-config').addClass('sidebar');
            
            $('#module-rows').val('');
            $('#module-pitch').val('');
            $('#module-count').val('');
            $('#module-stack').val(1);
            $('#module-gap').val('');
            $("#module-row-icon").html('<use xlink:href="#icon-plus" />').data('show', false);
            $("#module-row-settings .advanced").hide();
            
            $('#module-mounting-settings').addClass('in');
            $('#module-tracking-settings').removeClass('in');
            $('#module-tracking input').prop('checked', false);
            $("#module-tracking-icon").html('<use xlink:href="#icon-chevron-right" />');
            
            $('#module-backtrack input').prop('checked', false);
            $('#module-axis-height').val('');
            $('#module-tilt-max').val('');
            
            $('#module-tilt').val('');
            $('#module-azimuth').val('');
            $('#module-elevation').val('');
            
            $('#module-orientation').val('PORTRAIT');
            
            $('#module-model-type').text('');
            $('#module-model-description').text('');
            $('#module-model-manufacturer').text('Select a module type');
            $('#module-model-menu').data('toggle', 'none').html('<use xlink:href="#icon-checkmark" />');
        }
        else {
            $('#module-config-label').html('Configurations');
            $('#module-config-delete').show();
            $('#module-config-save').html('Save').prop('disabled', false);
            $('#module-config').removeClass('sidebar');
            
            var tracking = configs.tracking !== false;
            if (tracking) {
                $('#module-backtrack input').prop('checked', configs.tracking.backtrack);
                $('#module-axis-height').val(configs.tracking.axis_height);
                $('#module-tilt-max').val(configs.tracking.tilt_max);

                $('#module-tilt').val('');
                $('#module-azimuth').val('');
                $('#module-elevation').val('');
                
                $("#module-tracking-icon").html('<use xlink:href="#icon-chevron-down" />');
                $('#module-tracking-settings').addClass('in');
                $('#module-mounting-settings').removeClass('in');
            }
            else {
                $('#module-backtrack input').prop('checked', false);
                $('#module-axis-height').val('');
                $('#module-tilt-max').val('');
                
                $('#module-tilt').val(configs.mounting.tilt);
                $('#module-azimuth').val(configs.mounting.azimuth);
                $('#module-elevation').val(configs.mounting.elevation);
                
                $("#module-tracking-icon").html('<use xlink:href="#icon-chevron-right" />');
                $('#module-tracking-settings').removeClass('in');
                $('#module-mounting-settings').addClass('in');
            }
            $('#module-tracking input').prop('checked', tracking);
            
            $('#module-rows').val(configs.rows.count);
            $('#module-pitch').val(configs.rows.pitch);
            $('#module-count').val(configs.rows.modules);
            $('#module-stack').val(configs.rows.stack);
            
            var gap = configs.rows.gap_y != null ? configs.rows.gap_y : '';
            if (gap !== '') {
                $("#module-gap").val(gap).show();
                $("#module-row-settings .advanced").show();
                $("#module-row-icon").html('<use xlink:href="#icon-cross" />').data('show', true);
            }
            else {
                $("#module-gap").val(gap).hide();
                $("#module-row-settings .advanced").hide();
                $("#module-row-icon").html('<use xlink:href="#icon-plus" />').data('show', false);
            }
            
            $('#module-orientation').val(configs.orientation.toUpperCase());
            
            var module = modules[configs.type.split('/')[0]][configs.type];
            $('#module-model-type').text(module.Name);
            $('#module-model-description').text(module.Description);
            $('#module-model-manufacturer').html('<b>'+module.Manufacturer+'</b>');
            $('#module-model-menu').html('<use xlink:href="#icon-dots-vertical" />').data('toggle', 'dropdown');
        }
        $('#module-rows-tooltip').tooltip({html:true, container:modal});
        $('#module-row-tooltip').tooltip({html:true, container:modal});
        $('#module-settings-tooltip').tooltip({html:true, container:modal});
        
        $('#module-tracking input').off('change').on('change', function(e) {
            var tracking = $(this).prop('checked');
            if (tracking) {
                $("#module-tracking-icon").html('<use xlink:href="#icon-chevron-down" />');
                $('#module-tracking-settings').collapse('show');
                $('#module-mounting-settings').collapse('hide');
            }
            else {
                $("#module-tracking-icon").html('<use xlink:href="#icon-chevron-right" />');
                $('#module-tracking-settings').collapse('hide');
                $('#module-mounting-settings').collapse('show');
            }
        });
        
        $("#module-row-icon").off('click').on('click', function() {
            if (!$(this).data('show')) {
                $("#module-row-settings .advanced").animate({width:'toggle'}, 250);
                $(this).html('<use xlink:href="#icon-cross" />').data('show', true);
            }
            else {
                $("#module-row-settings .advanced").animate({width:'toggle'}, 250).val("");
                $(this).html('<use xlink:href="#icon-plus" />').data('show', false);
            }
        });
        
        $('#module-model-menu').off('click').on('click', function(e) {
            if ($(this).data('toggle') != 'dropdown') {
                e.stopPropagation();
                solar_configs.hideSidebar();
            }
        });
        
        $("#module-sidebar-modules").off('click').on('click', '.module-model', function() {
            var type = $(this).data("type");
            
            if (solar_configs.type !== type) {
                solar_configs.type = type;
                $('.module-model').removeClass("selected");
                //$(this).addClass("selected");
                
                var module = modules[$(this).data("manufacturer")][type];
                $('#module-model-type').text(module.Name);
                $('#module-model-description').text(module.Description);
                $('#module-model-manufacturer').html('<b>'+module.Manufacturer+'</b>');
                
                solar_configs.hideSidebar();
            }
            else {
                solar_configs.type = null;
                $(this).removeClass("selected");
                
                $('#module-model-type').text('');
                $('#module-model-description').text('');
                $('#module-model-manufacturer').text('Select a module type');
            }
            solar_configs.verifyConfig();
        });
        
        $("#module-config-modal").off('input').on('input', 'input[required]', function() {
            if (solar_configs.timeout != null) {
                clearTimeout(solar_configs.timeout);
            }
            solar_configs.timeout = setTimeout(function() {
                solar_configs.timeout = null;
                solar_configs.verifyConfig();
                
            }, 250);
        });
        
        $("#module-config-delete").off('click').on('click', function() {
            $('#module-config-modal').modal('hide');
            
            solar_configs.openDeletion(solar_configs.inverter, solar_configs.id);
        });
        
        $("#module-config-save").off('click').on('click', function() {
            solar_configs.saveConfig();
        });
    },

    adjustConfig: function() {
        if ($("#module-config-modal").length > 0) {
            $("#module-config").height($(window).height() - $("#module-config-modal").position().top - 180);
        }
    },

    saveConfig: function() {
        var rowCount = parseInt($('#module-rows').val());
        var rowModules = parseInt($('#module-count').val());
        var rowStack = parseInt($('#module-stack').val());
        var rowPitch = parseFloat($('#module-pitch').val());
        
        var orientation = $('#module-orientation').val();
        
        if (solar_configs.id == null) {
            var rows = {
                'count': rowCount,
                'modules': rowModules,
                'stack': rowStack,
                'pitch': rowPitch
            };
            if ($('#module-gap').val() != '') {
                rows['gap_y'] = parseFloat($('#module-gap').val());
            }
            var mounting = false;
            var tracking = false;
            
            if ($('#module-tracking input').is(':checked')) {
                tracking = {
                    'backtrack': $('#module-backtrack input').is(':checked'),
                    'axis_height': parseFloat($('#module-axis-height').val()),
                    'tilt_max': parseFloat($('#module-tilt-max').val())
                };
            }
            else {
                mounting = {
                    'tilt': parseFloat($('#module-tilt').val()),
                    'azimuth': parseFloat($('#module-azimuth').val()),
                    'elevation': parseFloat($('#module-elevation').val())
                };
            }
            solar.inverter.configs.create(solar_configs.inverter, 1, solar_configs.type, orientation, 
                                          rows, mounting, tracking, solar_configs.verifyResult);
        }
        else {
            var configs = solar_configs.inverter.configs[solar_configs.id];
            var fields = {};
            if (configs.type != solar_configs.type) fields['type'] = solar_configs.type;
            if (configs.orientation.toUpperCase() != orientation) fields['orientation'] = orientation;
            
            var rows = {};
            if (configs.rows.count != rowCount) rows['count'] = rowCount;
            if (configs.rows.modules != rowModules) rows['modules'] = rowModules;
            if (configs.rows.stack != rowStack) rows['stack'] = rowStack;
            if (configs.rows.pitch != rowPitch) rows['pitch'] = rowPitch;
            
            if ($('#module-gap').val() != '') {
                var gapStack = parseFloat($('#module-gap').val());
                if (configs.rows.gap_y != gapStack) rows['gap_y'] = gapStack;
            }
            
            if (Object.keys(rows).length > 0) {
                fields['rows'] = rows;
            }
            
            if ($('#module-tracking input').is(':checked')) {
                var tracking = {};
                
                var backtrack = $('#module-backtrack input').is(':checked');
                var axisHeight = parseFloat($('#module-axis-height').val());
                var tiltMax = parseFloat($('#module-tilt-max').val());
                
                if (configs.mounting !== false) {
                    fields['mounting'] = false;
                }
                if (configs.tracking === false) {
                    tracking['backtrack'] = backtrack;
                    tracking['axis_height'] = axisHeight;
                    tracking['tilt_max'] = tiltMax;
                }
                else {
                    if (configs.tracking.backtrack != backtrack) tracking['backtrack'] = backtrack;
                    if (configs.tracking.axis_height != axisHeight) tracking['axis_height'] = axisHeight;
                    if (configs.tracking.tilt_max != tiltMax) tracking['tilt_max'] = tiltMax;
                }
                if (Object.keys(tracking).length > 0) {
                    fields['tracking'] = tracking;
                }
            }
            else {
                var mounting = {};
                
                var tilt = parseFloat($('#module-tilt').val());
                var azimuth = parseFloat($('#module-azimuth').val());
                var elevation = parseFloat($('#module-elevation').val());
                
                if (configs.tracking !== false) {
                    fields['tracking'] = false;
                }
                if (configs.mounting === false) {
                    mounting['tilt'] = tilt;
                    mounting['azimuth'] = azimuth;
                    mounting['elevation'] = elevation;
                }
                else {
                    if (configs.mounting.tilt != tilt) mounting['tilt'] = tilt;
                    if (configs.mounting.azimuth != azimuth) mounting['azimuth'] = azimuth;
                    if (configs.mounting.elevation != elevation) mounting['elevation'] = elevation;
                }
                if (Object.keys(mounting).length > 0) {
                    fields['mounting'] = mounting;
                }
            }
            
            if (Object.keys(fields).length > 0) {
                solar.configs.update(solar_configs.id, fields, solar_configs.verifyResult);
            }
        }
        $('#module-config-loader').show();
        $("#module-config").removeClass('sidebar');
    },

    verifyConfig: function() {
        if (solar_configs.type != null &&
                $('#module-rows')[0].checkValidity() &&
                $('#module-pitch')[0].checkValidity() &&
                $('#module-count')[0].checkValidity() &&
                $('#module-stack')[0].checkValidity()) {
            
            if ($('#module-tracking input').is(':checked') &&
                    $('#module-axis-height')[0].checkValidity() &&
                    $('#module-tilt-max')[0].checkValidity()) {
                
                $('#module-config-save').prop("disabled", false);
                return true;
            }
            else if ($('#module-elevation')[0].checkValidity() &&
                    $('#module-azimuth')[0].checkValidity() &&
                    $('#module-tilt')[0].checkValidity()) {
                
                $('#module-config-save').prop("disabled", false);
                return true;
            }
        }
        $('#module-config-save').prop("disabled", true);
        return false;
    },

    verifyResult: function(result) {
        $('#module-config-loader').hide();
        
        if (typeof result.success !== 'undefined' && !result.success) {
            alert('Solar module could not be configured:\n'+result.message);
            return false;
        }
        var system = view.systems[solar_configs.inverter.sysid];
        
        if (typeof result.invid !== 'undefined') {
            system.inverters[result.invid].configs[result.id] = result;
        }
        else {
            for (var invid in system.inverters) {
                var inverter = system.inverters[invid];
                if (typeof inverter.configs[result.id] !== 'undefined') inverter.configs[result.id] = result;
            }
        }
        // TODO: verify if there is a better way to trigger vue.js redraw after deletion
        draw(view.systems);
        
        $('#module-config-modal').modal('hide');
        return true;
    },

    drawSidebar:function(modules) {
        var html = "";
        for (manufacturer in modules) {
            var group = modules[manufacturer];
            
            var header = false
            for (id in group) {
                    var module = group[id];
                    if (!header) {
                        header = true;
                        html += "<div class='accordion-group'>" +
                                "<div class='accordion-heading'>" +
                                    "<span class='accordion-toggle' data-toggle='collapse' " +
                                        "data-parent='#module-sidebar-modules' data-target='#module-model-"+manufacturer+"-collapse'>" +
                                        module.Manufacturer +
                                    "</span>" +
                                "</div>" +
                                "<div id='module-model-"+manufacturer+"-collapse' class='accordion-body collapse in'>" +
                                    "<div class='accordion-inner'>";
                    }
                    html += "<div id='module-model-"+id.replace('/', '-')+"' class='module-model' data-manufacturer='"+manufacturer+"' data-type='"+id+"'>" +
                            "<span>"+module.Name+"</span>" +
                        "</div>";
            }
            html += "</div>" +
                    "</div>" +
                "</div>";
        }
        $("#module-sidebar-modules").html(html);
    },

    showSidebar: function() {
        $('#module-model-menu').html('<use xlink:href="#icon-checkmark" />').data('toggle', 'none');
        $("#module-config").addClass('sidebar');
        solar_configs.adjustConfig();
        
        $(".module-model").removeClass("selected");
        if (solar_configs.type != null) {
            $(".module-model[data-type='"+solar_configs.type+"']").addClass("selected");
        }
    },

    hideSidebar: function() {
        $('#module-model-menu').html('<use xlink:href="#icon-dots-vertical" />').data('toggle', 'dropdown');
        $("#module-config").removeClass('sidebar');
        solar_configs.adjustConfig();
    },

    showAdvanced: function() {
        alert("Not implemented yet.");
    },

    openDeletion: function(inverter, id) {
        solar_configs.id = id;
        solar_configs.inverter = inverter;
        
        $('#module-delete-modal').modal('show');
        $('#module-delete-label').html('Delete configurations');
        $("#module-delete-confirm").off('click').on('click', function() {
            $('#module-delete-loader').show();
            
            solar.inverter.configs.remove(solar_configs.inverter, solar_configs.id, function(result) {
                $('#module-delete-loader').hide();
                
                if (typeof result.success !== 'undefined' && !result.success) {
                    alert('Unable to delete configurations:\n'+result.message);
                    return false;
                }
                delete view.systems[solar_configs.inverter.sysid]
                        .inverters[solar_configs.inverter.id]
                        .configs[solar_configs.id];
                
                // TODO: verify if there is a better way to trigger vue.js redraw after deletion
                draw(view.systems);
                
                $('#module-delete-modal').modal('hide');
            });
        });
    }
}
