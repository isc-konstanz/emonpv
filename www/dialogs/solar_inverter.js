var solar_inverter = {

    id: null,
    type: null,
    system: null,

    newConfig: function(system) {
        solar_inverter.id = null;
        solar_inverter.type = null;
        solar_inverter.system = system;
        solar_inverter.drawConfig();
        solar_inverter.adjustConfig();
    },

    openConfig: function(system, id) {
        var inverter = system.inverters[id];
        
        solar_inverter.id = id;
        solar_inverter.type = inverter.type;
        solar_inverter.system = system;
        solar_inverter.drawConfig(inverter);
        solar_inverter.adjustConfig();
    },

    drawConfig: function(inverter = null) {
        var modal = $("#inverter-config-modal").modal('show');
        if (inverter == null) {
            $('#inverter-config-label').html('Create inverter');
            $('#inverter-config-delete').hide();
            $('#inverter-config-save').prop('disabled', true);
            $('#inverter-config-save').html('Create');
            
            $('#inverter-count').val('');
        }
        else {
            $('#inverter-config-label').html('Configure inverter');
            $('#inverter-config-delete').show();
            $('#inverter-config-save').prop('disabled', false);
            $('#inverter-config-save').html('Save');
            
            var count = inverter.count != null ? inverter.count : 1;
            $('#inverter-count').val(count);
            
        }
        solar_inverter.drawModel(inverter);
        solar_inverter.verifyConfig();
        
        $('#inverter-count-tooltip').tooltip({html:true, container:modal});
        $('#inverter-settings-tooltip').tooltip({html:true, container:modal});
        
        $("#inverter-config-modal").off('input').on('input', 'input[required]', function() {
            if (solar_inverter.timeout != null) {
                clearTimeout(solar_inverter.timeout);
            }
            solar_inverter.timeout = setTimeout(function() {
                solar_inverter.timeout = null;
                solar_inverter.verifyConfig();
                
            }, 250);
        });
        
        $("#inverter-config-delete").off('click').on('click', function () {
            $('#inverter-config-modal').modal('hide');
            
            solar_inverter.openDeletion(solar_inverter.system, solar_inverter.id);
        });
        
        $("#inverter-config-save").off('click').on('click', function() {
            solar_inverter.saveConfig();
        });
    },

    drawModel: function(inverter) {
        if (inverter == null) {
            solar_inverter.drawAdvanced(null);
        }
        else {
            if (inverter.type != null && inverter.type !== 'custom') {
                solar_inverter.drawAdvanced(null);
                // TODO: Check if type is valid and implement inverter models
            }
            else {
                solar_inverter.drawAdvanced(inverter.model);
            }
        }
    },

    drawAdvanced: function(model) {
        if (model != null && typeof model.success !== 'undefined' && !model.success) {
            alert('Solar inverter could not be configured:\n'+model.message);
            return false;
        }
        if (model == null) {
            $("#inverter-param-power").val("");
        }
        else {
            $("#inverter-param-power").val(model.pdc0/1000);
        }
    },

    parseAdvanced: function() {
        var inverter = {};
        
        inverter['Name'] = 'Custom';
        inverter['pdc0'] = parseFloat($("#inverter-param-power").val())*1000;
        
        return inverter;
    },

    adjustConfig: function() {
        if ($("#inverter-config-modal").length > 0) {
            $("#inverter-config").height($(window).height() - $("#inverter-config-modal").position().top - 180);
        }
    },

    saveConfig: function() {
        var count = $('#inverter-count').val() ? parseInt($('#inverter-count').val()) : null;
        
        if (solar_inverter.id == null) {
            var model;
            //if ($('#inverter-advanced-mode input').is(':checked')) {
                model = solar_inverter.parseAdvanced();
            //}
            //else {
            //    module = solar_inverter.type;
            //}
            solar.inverter.create(solar_inverter.system, count, model, solar_inverter.verifyResult);
        }
        else {
            var inverter = solar_inverter.system.inverters[solar_inverter.id];
            var fields = {};
            
            if (inverter.count != count) fields['count'] = count;
            
            //if ($('#inverter-advanced-mode input').is(':checked')) {
                var model = solar_inverter.parseAdvanced();
                
                if (inverter.type !== 'custom' || (inverter.type === 'custom' && !inverter.hasOwnProperty('module'))) {
                    fields['type'] = 'custom';
                    fields['model'] = model;
                }
                else {
                    for (var key in model) {
                        if (model.hasOwnProperty(key) && (!inverter.model.hasOwnProperty(key) ||
                                (model[key] && model[key] != inverter.model[key]))) {
                            if (!fields.hasOwnProperty('model')) {
                                fields['model'] = {};
                            }
                            fields['model'][key] = model[key];
                        }
                    }
                }
            //}
            //else if (inverter.type != solar_inverter.type) fields['type'] = solar_inverter.type;
            
            if (Object.keys(fields).length > 0) {
                solar.inverter.update(solar_inverter.id, fields, solar_inverter.verifyResult);
            }
            else {
                $('#inverter-config-modal').modal('hide');
            }
        }
        $('#inverter-config-loader').show();
    },

    verifyConfig: function() {
        if (!$('#inverter-count')[0].checkValidity()) {
            $('#inverter-config-save').prop("disabled", true);
            return false;
        }
        if (!$('#inverter-param-power')[0].checkValidity()) {
            $('#inverter-config-save').prop("disabled", true);
            return false;
        }
        $('#inverter-config-save').prop("disabled", false);
        return true;
    },

    verifyResult: function(result) {
        $('#inverter-config-loader').hide();
        
        if (typeof result.success !== 'undefined' && !result.success) {
            alert('Solar inverter could not be configured:\n'+result.message);
            return false;
        }
        let systems = view.systems;
        systems[result.sysid].inverters[result.id] = result;
        
        // TODO: verify if there is a better way to trigger vue.js redraw after deletion
        draw(systems);
        
        $('#inverter-config-modal').modal('hide');
        return true;
    },

    openDeletion: function(system, id) {
        solar_inverter.id = id;
        solar_inverter.system = system;
        
        $('#inverter-delete-modal').modal('show');
        $('#inverter-delete-label').html('Delete inverter');
        $("#inverter-delete-confirm").off('click').on('click', function() {
            $('#inverter-delete-loader').show();
            
            solar.inverter.remove(solar_inverter.id, function(result) {
                $('#inverter-delete-loader').hide();
                
                if (typeof result.success !== 'undefined' && !result.success) {
                    alert('Unable to delete inverter:\n'+result.message);
                    return false;
                }
                let systems = view.systems;
                delete systems[solar_inverter.system.id]
                        .inverters[solar_inverter.id];
                draw(systems);
                $('#inverter-delete-modal').modal('hide');
            });
        });
    }

}
