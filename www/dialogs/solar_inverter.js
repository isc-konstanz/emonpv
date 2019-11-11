var solar_inverter = {

    id: null,
    system: null,

    newConfig: function(system) {
        solar_inverter.id = null;
        solar_inverter.system = system;
        solar_inverter.drawConfig();
    },

    openConfig: function(system, id) {
        solar_inverter.id = id;
        solar_inverter.system = system;
        solar_inverter.drawConfig(system.inverters[id]);
    },

    drawConfig: function(inverter = null) {
        var modal = $("#inverter-config-modal").modal('show');
        if (inverter == null) {
            $('#inverter-config-label').html('Create inverter');
            $('#inverter-config-delete').hide();
            //$('#inverter-config-save').prop('disabled', true);
            $('#inverter-config-save').prop('disabled', false);
            $('#inverter-config-save').html('Create');
        }
        else {
            $('#inverter-config-label').html('Configure inverter');
            $('#inverter-config-delete').show();
            $('#inverter-config-save').prop('disabled', false);
            $('#inverter-config-save').html('Save');
        }
        solar_inverter.registerConfigEvents();
    },

    saveConfig: function() {
        if (solar_inverter.id == null) {
            
            solar.inverter.create(solar_inverter.system, solar_inverter.verifyResult);
        }
        else {
            var fields = {};
            
            solar.system.set(solar_inverter.system, solar_inverter.id, fields, solar_inverter.verifyResult);
        }
        $('#inverter-config-loader').show();
    },

    verifyConfig: function() {
    },

    verifyResult: function(result) {
        $('#inverter-config-loader').hide();
        
        if (typeof result.success !== 'undefined' && !result.success) {
            alert('Solar inverter could not be configured:\n'+result.message);
            return false;
        }
        // TODO: find better way to force reload vue.js
        let systems = view.systems;
        systems[result.sysid].inverters[result.id] = result;
        draw(systems);
        
        $('#inverter-config-modal').modal('hide');
        return true;
    },

    registerConfigEvents: function() {
        $("#inverter-config-delete").off('click').on('click', function () {
            $('#inverter-config-modal').modal('hide');
            
            solar_inverter.openDeletion(solar_inverter.system, solar_inverter.id);
        });

        $("#inverter-config-save").off('click').on('click', function() {
            solar_inverter.saveConfig();
        });
    },

    openDeletion: function(system, id) {
        solar_inverter.id = id;
        solar_inverter.system = system;
        
        $('#inverter-delete-modal').modal('show');
        $('#inverter-delete-label').html('Delete inverter');
        $("#inverter-delete-confirm").off('click').on('click', function() {
            $('#inverter-delete-loader').show();
            
            solar.inverter.remove(solar_inverter.system, solar_inverter.id, function(result) {
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
