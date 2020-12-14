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

    openConfig: function(inverter, id) {
        var configs = inverter.configs[id];
        
        solar_configs.id = id;
        solar_configs.type = configs.type;
        solar_configs.inverter = inverter;
        solar_configs.drawConfig(configs);
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
            $('#module-stack').val('');
            $('#module-stack-gap').val('');
            $("#module-row-icon").html('<use xlink:href="#icon-plus" />').data('show', false);
            $("#module-row-settings .advanced").hide();
            
            $('#module-mounting-settings').addClass('in').height('auto');
            $('#module-tracking-settings').removeClass('in').height(0);
            $('#module-tracking input').prop('checked', false);
            $("#module-tracking-icon").html('<use xlink:href="#icon-chevron-right" />');
            
            $('#module-backtrack input').prop('checked', false);
            $('#module-axis-height').val('');
            $('#module-tilt-max').val('');
            
            $('#module-tilt').val('');
            $('#module-azimuth').val('');
            $('#module-elevation').val('');

            $('#module-losses-settings').removeClass('in').height(0);
            $('#module-loss-constant').val('');
            $('#module-loss-wind').val('');
            
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
                $('#module-tracking-settings').addClass('in').height('auto');
                $('#module-mounting-settings').removeClass('in').height(0);
            }
            else {
                $('#module-backtrack input').prop('checked', false);
                $('#module-axis-height').val('');
                $('#module-tilt-max').val('');
                
                $('#module-tilt').val(configs.mounting.tilt);
                $('#module-azimuth').val(configs.mounting.azimuth);
                $('#module-elevation').val(configs.mounting.elevation);
                
                $("#module-tracking-icon").html('<use xlink:href="#icon-chevron-right" />');
                $('#module-tracking-settings').removeClass('in').height(0);
                $('#module-mounting-settings').addClass('in').height('auto');
            }
            $('#module-tracking input').prop('checked', tracking);
            
            $('#module-rows').val(configs.rows.count);
            $('#module-pitch').val(configs.rows.pitch);
            $('#module-count').val(configs.rows.modules);
            
            var stack = configs.rows.stack != null ? configs.rows.stack : '';
            var gap = configs.rows.gap_y != null ? configs.rows.gap_y : '';
            if (gap !== '' || stack !== '') {
                $('#module-stack').val(stack).show();
                $("#module-stack-gap").val(gap).show();
                $("#module-row-settings .advanced").show();
                $("#module-row-icon").html('<use xlink:href="#icon-cross" />').data('show', true);
            }
            else {
                $('#module-stack').val(stack).hide();
                $("#module-stack-gap").val(gap).hide();
                $("#module-row-settings .advanced").hide();
                $("#module-row-icon").html('<use xlink:href="#icon-plus" />').data('show', false);
            }
            
            var losses = configs.losses !== false;
            if (losses) {
                $('#module-loss-constant').val(configs.losses.constant);
                $('#module-loss-wind').val(configs.losses.wind);
            }
            else {
                $('#module-loss-constant').val('');
                $('#module-loss-wind').val('');
            }
            $('#module-losses-settings').removeClass('in').height(0);
            
            $('#module-orientation').val(configs.orientation.toUpperCase());
        }
        solar_configs.drawModule(configs);
        
        $('#module-tracking-tooltip').tooltip({html:true, container:modal});
        $('#module-mounting-tooltip').tooltip({html:true, container:modal});
        $('#module-losses-tooltip').tooltip({html:true, container:modal});
        
        $('#module-settings-tooltip').tooltip({html:true, container:modal});
        $('#module-params-tooltip').tooltip({html:true, container:modal});
        
        $("#module-tracking-header .settings-collapse").off('click').on('click', function() {
            var tracking = $("#module-tracking input");
            var trackingFlag = !tracking.is(':checked');
            tracking.prop('checked', trackingFlag);
            solar_configs.showTracking(trackingFlag);
        });
        
        $('#module-tracking input').off('change').on('change', function() {
            solar_configs.showTracking($(this).prop('checked'));
        });
        
        $("#module-losses-settings .settings-collapse").off('click').on('click', function() {
            var losses = $("#module-losses-icon");
            var lossesFlag = !losses.data('show');
            if (lossesFlag) {
                losses.html('<use xlink:href="#icon-chevron-down" />');
                $('#module-losses').collapse('show');
            }
            else {
                losses.html('<use xlink:href="#icon-chevron-right" />');
                $('#module-losses').collapse('hide');
            }
            losses.data('show', lossesFlag);
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
        
        $("#module-param-header .settings-collapse").off('click').on('click', function() {
            var advanced = $("#module-advanced-mode input");
            var advancedFlag = !advanced.is(':checked');
            advanced.prop('checked', advancedFlag);
            solar_configs.showAdvanced(advancedFlag);
        });
        
        $('#module-advanced-mode input').off('change').on('change', function() {
            solar_configs.showAdvanced($(this).prop('checked'));
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
                solar.module.get(type, solar_configs.drawAdvanced);
                
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

    drawModule: function(configs) {
        if (configs == null) {
            $('#module-advanced-mode input').prop('checked', false);
            
            $("#module-advanced-icon").html('<use xlink:href="#icon-chevron-right" />');
            $('#module-losses-settings').removeClass('in').height(0);
            $('#module-param-advanced').removeClass('in').height(0);
            $('#module-param-settings').addClass('in').height('auto');
            solar_configs.showSidebar();
            solar_configs.drawAdvanced(null);
            
            $('#module-orientation').val('PORTRAIT');
            
            $('#module-model-type').text('');
            $('#module-model-description').text('');
            $('#module-model-manufacturer').text('Select a module type');
            $('#module-model-menu').data('toggle', 'none').html('<use xlink:href="#icon-checkmark" />');
        }
        else {
            // TODO: Check if type is valid or if is advanced mode
            if (configs.type != null && configs.type !== 'custom') {
                $('#module-advanced-mode input').prop('checked', false);
                
                $("#module-advanced-icon").html('<use xlink:href="#icon-chevron-right" />');
                $('#module-losses-settings').removeClass('in').height(0);
                $('#module-param-advanced').removeClass('in').height(0);
                $('#module-param-settings').addClass('in').height('auto');
                solar_configs.showSidebar();
                
                var module = modules[configs.type.split('/')[0]][configs.type];
                $('#module-model-type').text(module.Name);
                $('#module-model-description').text(module.Description);
                $('#module-model-manufacturer').html('<b>'+module.Manufacturer+'</b>');
                $('#module-model-menu').html('<use xlink:href="#icon-dots-vertical" />').data('toggle', 'dropdown');
                
                solar.module.get(configs.type, solar_configs.drawAdvanced);
            }
            else {
                $('#module-advanced-mode input').prop('checked', true);
                
                $("#module-advanced-icon").html('<use xlink:href="#icon-chevron-down" />');
                $('#module-losses-settings').addClass('in').height('auto');
                $('#module-param-advanced').addClass('in').height('auto');
                $('#module-param-settings').removeClass('in').height(0);
                $('.module-model').removeClass("selected");
                solar_configs.drawAdvanced(configs.module);
                solar_configs.hideSidebar();
                
                $('#module-model-type').text('');
                $('#module-model-description').text('');
                $('#module-model-manufacturer').text('Select a module type');
            }
        }
        
        $("#module-bifi-select input").off('change').on('change', function() {
            if ($(this).prop('checked')) {
                $("#module-bifi-settings .advanced").animate({width:'toggle'}, 250);
            }
            else {
                $("#module-bifi-settings .advanced").animate({width:'toggle'}, 250);
                $("#module-bifi-factor").val("");
            }
        });
        
        $("#module-tech-icon").off('click').on('click', function() {
            if (!$(this).data('show')) {
                $("#module-tech-settings .advanced").animate({width:'toggle'}, 250);
                $(this).html('<use xlink:href="#icon-cross" />').data('show', true);
            }
            else {
                $("#module-tech-settings .advanced").animate({width:'toggle'}, 250).val("");
                $(this).html('<use xlink:href="#icon-plus" />').data('show', false);
            }
        });
    },

    drawAdvanced: function(module) {
        if (module != null && typeof module.success !== 'undefined' && !module.success) {
            alert('Solar module could not be configured:\n'+module.message);
            return false;
        }
        if (module == null) {
            $("#module-param-length").val("");
            $("#module-param-width").val("");
            $("#module-param-cells").val("");
            
            $("#module-bifi-settings .advanced").hide();
            $("#module-bifi-select input").prop('checked', false);
            $("#module-bifi-factor").val("");
            
            $("#module-surface-front").val("");
            $("#module-surface-back").val("");
            $("#module-technology").val("");
            
            $("#module-ideality-factor").val("").hide();
            $("#module-tech-settings .advanced").hide();
            $("#module-tech-icon").html('<use xlink:href="#icon-plus" />').data('show', false);
            
            $("#module-param-vmpp").val("");
            $("#module-param-impp").val("");
            $("#module-param-mu-p").val("");
            
            $("#module-param-voc").val("");
            $("#module-param-isc").val("");
            $("#module-param-alpha-sc").val("");
        }
        else {
            $("#module-param-length").val(module.A_y);
            $("#module-param-width").val(module.A_x);
            $("#module-param-cells").val(module.Cells_in_Series);
            
            if (("Bifi" in module && module.Bifi === "Y") || module.Bifaciality > 0) {
                $("#module-bifi-settings .advanced").show();
                $("#module-bifi-select input").prop('checked', true);
                $("#module-bifi-factor").val(module.Bifaciality);
            }
            else {
                $("#module-bifi-settings .advanced").hide();
                $("#module-bifi-select input").prop('checked', false);
                $("#module-bifi-factor").val("");
            }
            $("#module-surface-front").val(module.Front_type);
            $("#module-surface-back").val(module.Back_type);
            $("#module-technology").val(module.Technology);
            
            if (typeof module.Ideality_factor !== 'undefined') {
                $("#module-ideality-factor").val(module.Ideality_factor).show();
                $("#module-tech-settings .advanced").show();
                $("#module-tech-icon").html('<use xlink:href="#icon-cross" />').data('show', true);
            }
            else {
                $("#module-ideality-factor").val("").hide();
                $("#module-tech-settings .advanced").hide();
                $("#module-tech-icon").html('<use xlink:href="#icon-plus" />').data('show', false);
            }
            
            $("#module-param-vmpp").val(module.V_mp_ref);
            $("#module-param-impp").val(module.I_mp_ref);
            $("#module-param-mu-p").val(module.mu_power);
            
            $("#module-param-voc").val(module.V_oc_ref);
            $("#module-param-isc").val(module.I_sc_ref);
            $("#module-param-alpha-sc").val(module.alpha_sc);
        }
    },

    showAdvanced: function(show) {
        if (show) {
            $("#module-advanced-icon").html('<use xlink:href="#icon-chevron-down" />');
            $('#module-losses-settings').collapse('show');
            $('#module-param-advanced').collapse('show');
            $('#module-param-settings').collapse('hide');
            $('.module-model').removeClass("selected");
            solar_configs.hideSidebar();
            solar_configs.type = null;
            
            $('#module-model-type').text('');
            $('#module-model-description').text('');
            $('#module-model-manufacturer').text('Select a module type');
            solar_configs.verifyConfig();
        }
        else {
            $("#module-advanced-icon").html('<use xlink:href="#icon-chevron-right" />');
            $('#module-losses-settings').collapse('hide');
            $('#module-param-advanced').collapse('hide');
            $('#module-param-settings').collapse('show');
            solar_configs.showSidebar();
        }
    },

    showTracking: function(show) {
        if (show) {
            $("#module-tracking-icon").html('<use xlink:href="#icon-chevron-down" />');
            $('#module-tracking-settings').collapse('show');
            $('#module-mounting-settings').collapse('hide');
        }
        else {
            $("#module-tracking-icon").html('<use xlink:href="#icon-chevron-right" />');
            $('#module-tracking-settings').collapse('hide');
            $('#module-mounting-settings').collapse('show');
        }
    },

    adjustConfig: function() {
        if ($("#module-config-modal").length > 0) {
            $("#module-config").height($(window).height() - $("#module-config-modal").position().top - 180);
        }
    },

    saveConfig: function() {
        var rowCount = parseInt($('#module-rows').val());
        var rowModules = parseInt($('#module-count').val());
        var rowPitch = parseFloat($('#module-pitch').val());
        
        var stackCount = $('#module-stack').val() ? parseFloat($('#module-stack').val()) : null;
        var stackGap = $('#module-stack-gap').val() ? parseFloat($('#module-stack-gap').val()) : null;
        
        var orientation = $('#module-orientation').val();
        
        if (solar_configs.id == null) {
            var rows = {
                'count': rowCount,
                'modules': rowModules,
                'pitch': rowPitch
            };
            if (stackCount) rows['stack'] = stackCount;
            if (stackGap) rows['gap_y'] = stackGap;
            
            var mounting = false;
            var tracking = false;
            var losses = false;
            
            var module = solar_configs.type;
            
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
            solar.configs.create(solar_configs.inverter.sysid, solar_configs.inverter.id, 1, 
                                 rows, mounting, tracking, losses, orientation, module, solar_configs.verifyResult);
        }
        else {
            var configs = solar_configs.inverter.configs[solar_configs.id];
            var fields = {};
            
            var rows = {};
            if (configs.rows.count != rowCount) rows['count'] = rowCount;
            if (configs.rows.modules != rowModules) rows['modules'] = rowModules;
            if (configs.rows.pitch != rowPitch) rows['pitch'] = rowPitch;
            
            if (configs.rows.stack != stackCount) rows['stack'] = stackCount;
            if (configs.rows.gap_y != stackGap) rows['gap_y'] = stackGap;
            
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
            if (configs.orientation.toUpperCase() != orientation) fields['orientation'] = orientation;
            
            if ($('#module-advanced-mode input').is(':checked')) {
                var module = {}
                var losses = {};
                
                var lossConstant = $('#module-loss-constant').val() ? parseFloat($('#module-loss-constant').val()) : null;
                var lossWind = $('#module-loss-wind').val() ? parseFloat($('#module-loss-wind').val()) : null;
                if (lossWind || lossConstant) {
                    if (configs.losses === false) {
                        losses['constant'] = lossConstant;
                        losses['wind'] = lossWind;
                    }
                    else {
                        if (configs.losses.constant != lossConstant && lossConstant) losses['constant'] = lossConstant;
                        if (configs.losses.wind != lossWind && lossWind) losses['wind'] = lossWind;
                    }
                    if (Object.keys(losses).length > 0) {
                        fields['losses'] = losses;
                    }
                }
                else if (configs.losses !== false) {
                    fields['losses'] = false;
                }
                
                module['Name'] = 'Custom';
                module['Technology'] = $("#module-technology").val();
                module['BIPV'] = 'N'
                
                if ($('#module-bifi-select input').is(':checked')) {
                    module['Bifi'] = 'Y';
                    module['Bifaciality'] = $("#module-bifi-factor").val();
                }
                else {
                    module['Bifi'] = 'N';
                    module['Bifaciality'] = 0;
                }
                module['Ideality_factor'] = $("#module-ideality-factor").val();
                module['Cells_in_Series'] = $("#module-param-cells").val();
                module['Front_type'] = $("#module-surface-front").val();
                module['Back_type'] = $("#module-surface-back").val();
                
                module['A_y'] = $("#module-param-length").val();
                module['A_x'] = $("#module-param-width").val();
                
                module['V_mp_ref'] = $("#module-param-vmpp").val();
                module['I_mp_ref'] = $("#module-param-impp").val();
                module['mu_power'] = $("#module-param-mu-p").val();
                
                module['V_oc_ref'] = $("#module-param-voc").val();
                module['I_sc_ref'] = $("#module-param-isc").val();
                module['alpha_sc'] = $("#module-param-alpha-sc").val();
                
                if (configs.type !== 'custom' || !configs.hasOwnProperty('module')) {
                    fields['module'] = module;
                }
                else {
                    for (var key in module) {
                        if (module.hasOwnProperty(key) && (!configs.module.hasOwnProperty(key) ||
                                module[key] != configs.module[key])) {
                            if (!fields.hasOwnProperty('module')) {
                                fields['module'] = {};
                            }
                            fields['module'][key] = module[key];
                        }
                    }
                }
            }
            else if (configs.type != solar_configs.type) fields['module'] = solar_configs.type;
            
            if (Object.keys(fields).length > 0) {
                solar.configs.update(solar_configs.id, fields, solar_configs.verifyResult);
            }
            else {
                $('#module-config-modal').modal('hide');
            }
        }
        $('#module-config-loader').show();
        $("#module-config").removeClass('sidebar');
    },

    verifyConfig: function() {
        if ($('#module-advanced-mode input').is(':checked')) {
            if (!$('#module-param-length')[0].checkValidity() ||
                    !$('#module-param-width')[0].checkValidity() ||
                    !$('#module-param-cells')[0].checkValidity() ||
                    !$('#module-param-vmpp')[0].checkValidity() ||
                    !$('#module-param-impp')[0].checkValidity() ||
                    !$('#module-param-mu-p')[0].checkValidity() ||
                    !$('#module-param-voc')[0].checkValidity() ||
                    !$('#module-param-isc')[0].checkValidity() ||
                    !$('#module-param-alpha-sc')[0].checkValidity()) {
                
                $('#module-config-save').prop("disabled", true);
                return false;
            }
            if ($('#module-bifi-select input').is(':checked') &&
                    !$('#module-bifi-factor')[0].checkValidity()) {
        
                $('#module-config-save').prop("disabled", true);
                return false;
            }
        }
        else if (solar_configs.type == null) {
            $('#module-config-save').prop("disabled", true);
            return false;
        }
        if (!$('#module-rows')[0].checkValidity() ||
                !$('#module-pitch')[0].checkValidity() ||
                !$('#module-count')[0].checkValidity() ||
                !$('#module-stack')[0].checkValidity()) {
            
            $('#module-config-save').prop("disabled", true);
            return false;
        }
        
        if ($('#module-tracking input').is(':checked') &&
                (!$('#module-axis-height')[0].checkValidity() ||
                !$('#module-tilt-max')[0].checkValidity())) {
            
            $('#module-config-save').prop("disabled", true);
            return false;
        }
        else if (!$('#module-elevation')[0].checkValidity() ||
                !$('#module-azimuth')[0].checkValidity() ||
                !$('#module-tilt')[0].checkValidity()) {
            
            $('#module-config-save').prop("disabled", true);
            return false;
        }
        $('#module-config-save').prop("disabled", false);
        return true;
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
        if (solar_configs.type != null && solar_configs.type !== 'custom') {
            $(".module-model[data-type='"+solar_configs.type+"']").addClass("selected");
        }
    },

    hideSidebar: function() {
        $('#module-model-menu').html('<use xlink:href="#icon-dots-vertical" />').data('toggle', 'dropdown');
        $("#module-config").removeClass('sidebar');
        solar_configs.adjustConfig();
    },

    openDeletion: function(inverter, id) {
        solar_configs.id = id;
        solar_configs.inverter = inverter;
        
        $('#module-delete-modal').modal('show');
        $('#module-delete-label').html('Delete configurations');
        $("#module-delete-confirm").off('click').on('click', function() {
            $('#module-delete-loader').show();
            
            solar.configs.remove(solar_configs.id, solar_configs.inverter.sysid, solar_configs.inverter.id, 
                    function(result) {
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
