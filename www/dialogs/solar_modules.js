var solar_modules = {

    id: null,
    type: null,
    inverter: null,

    newConfig: function(inverter) {
        solar_modules.id = null;
        solar_modules.type = null;
        solar_modules.inverter = inverter;
        solar_modules.drawConfig();
        solar_modules.adjustConfig();
    },

    openConfig: function(inverter, id, type) {
        solar_modules.id = id;
        solar_modules.type = type;
        solar_modules.inverter = inverter;
        solar_modules.drawConfig(inverter.modules[id]);
        solar_modules.adjustConfig();
    },

    drawConfig: function(modules = null) {
        var modal = $("#modules-config-modal").modal('show');
        if (modules == null) {
            $('#modules-config-label').html('Create modules');
            $('#modules-config-delete').hide();
            //$('#modules-config-save').prop('disabled', true);
            $('#modules-config-save').prop('disabled', false);
            $('#modules-config-save').html('Create');
            $('#modules-config').addClass('sidebar');
            
            $('#modules-count').val(1);
            $('#modules-number').val(1);
            $('#modules-pitch').val('');
            $('#modules-elevation').val('');
            $('#modules-azimuth').val('');
            $('#modules-tilt').val('');
            
            $('#modules-model-name').text('');
            $('#modules-model-description').text('');
            $('#modules-model-manufacturer').text('Select a model type');
            $('#modules-model-menu').data('toggle', 'none').html('<use xlink:href="#icon-checkmark" />');
        }
        else {
            $('#modules-config-label').html('Configure modules');
            $('#modules-config-delete').show();
            $('#modules-config-save').prop('disabled', false);
            $('#modules-config-save').html('Save');
            $('#modules-config').removeClass('sidebar');

            $('#modules-count').val(modules.count);
            $('#modules-number').val(modules.number);
            $('#modules-pitch').val(modules.geometry.pitch);
            $('#modules-elevation').val(modules.geometry.elevation);
            $('#modules-azimuth').val(modules.geometry.azimuth);
            $('#modules-tilt').val(modules.geometry.tilt);
            
            var model = models[modules.type.split('/')[0]][modules.type];
            $('#modules-model-type').text(model.Name);
            $('#modules-model-description').text(model.Description);
            $('#modules-model-manufacturer').html('<b>'+model.Manufacturer+':</b>');
            $('#modules-model-menu').html('<use xlink:href="#icon-dots-vertical" />').data('toggle', 'dropdown');
        }
        $('#modules-pitch-tooltip').tooltip({html:true, container:modal});
        $('#modules-geometry-tooltip').tooltip({html:true, container:modal});
        $('#modules-settings-tooltip').tooltip({html:true, container:modal});
        
        $('#modules-model-menu').off('click').on('click', function(e) {
        	if ($(this).data('toggle') != 'dropdown') {
        		e.stopPropagation();
        		solar_modules.hideSidebar();
        	}
        });

        $("#modules-sidebar-models").off('click').on('click', '.modules-model', function() {
            var type = $(this).data("type");
            
            if (solar_modules.type !== type) {
                solar_modules.type = type;
                $('.modules-model').removeClass("selected");
                $(this).addClass("selected");
                
                var model = models[$(this).data("manufacturer")][type];
                $('#modules-model-type').text(model.Name);
                $('#modules-model-description').text(model.Description);
                $('#modules-model-manufacturer').html('<b>'+model.Manufacturer+':</b>');
            }
            else {
                solar_modules.type = null;
                $(this).removeClass("selected");
                
                $('#modules-model-type').text('');
                $('#modules-model-description').text('');
                $('#modules-model-manufacturer').text('Select a model type');
            }
        });

        $("#modules-config-delete").off('click').on('click', function() {
            $('#modules-config-modal').modal('hide');
            
            solar_modules.openDeletion(solar_modules.inverter, solar_modules.id);
        });

        $("#modules-config-save").off('click').on('click', function() {
            solar_modules.saveConfig();
        });
    },

    adjustConfig:function() {
        if ($("#modules-config-modal").length > 0) {
        	if ($("#modules-config").hasClass('sidebar')) {
                $("#modules-config").height($(window).height() - $("#modules-config-modal").position().top - 180);
        	}
        	else {
                $("#modules-config").height(350);
        	}
        }
    },

    saveConfig: function() {
        var count = $('#modules-count').val();
        var number = $('#modules-number').val();
        
        var pitch = $('#modules-pitch').val();
        var elevation = $('#modules-elevation').val();
        var azimuth = $('#modules-azimuth').val();
        var tilt = $('#modules-tilt').val();
        
        if (solar_modules.id == null) {
            var geometry = {
                    'pitch': pitch,
                    'elevation': elevation,
                    'azimuth': azimuth,
                    'tilt': tilt
            };
            var tracking = {};
            var settings = {};
            
            solar.modules.create(solar_modules.inverter, 1, count, geometry, tracking, solar_modules.type, number, settings, solar_modules.verifyResult);
        }
        else {
        	var modules = solar_modules.inverter.modules[solar_modules.id];
            var fields = {};
            if (modules.type != solar_modules.type) fields['type'] = solar_modules.type;
            
            if (modules.count != count) fields['count'] = count;
            if (modules.number != number) fields['number'] = number;
            if (modules.geometry.pitch != pitch) fields['pitch'] = pitch;
            if (modules.geometry.elevation != elevation) fields['elevation'] = elevation;
            if (modules.geometry.azimuth != azimuth) fields['azimuth'] = azimuth;
            if (modules.geometry.tilt != tilt) fields['tilt'] = tilt;
            
            solar.modules.update(solar_modules.inverter, solar_modules.id, fields, solar_modules.verifyResult);
        }
        $('#modules-config-loader').show();
    	$("#modules-config").removeClass('sidebar');
    },

    verifyConfig: function() {
    },

    verifyResult: function(result) {
        $('#modules-config-loader').hide();
        
        if (typeof result.success !== 'undefined' && !result.success) {
            alert('Solar modules could not be configured:\n'+result.message);
            return false;
        }
        // TODO: find better way to force reload vue.js
        let systems = view.systems;
        systems[solar_modules.inverter.sysid].inverters[result.invid].modules[result.id] = result;
        draw(systems);
        
        $('#modules-config-modal').modal('hide');
        return true;
    },

    drawSidebar:function(models) {
        var html = "";
        for (manufacturer in models) {
            var group = models[manufacturer];
            
            var header = false
            for (id in group) {
                    var model = group[id];
                    if (!header) {
                        header = true;
                        html += "<div class='accordion-group'>" +
	                            "<div class='accordion-heading'>" +
	                                "<span class='accordion-toggle' data-toggle='collapse' " +
	                                    "data-parent='#modules-sidebar-models' data-target='#modules-model-"+manufacturer+"-collapse'>" +
	                                    model.Manufacturer +
	                                "</span>" +
	                            "</div>" +
	                            "<div id='modules-model-"+manufacturer+"-collapse' class='accordion-body collapse'>" +
	                                "<div class='accordion-inner'>";
                    }
                    html += "<div id='modules-model-"+id.replace('/', '-')+"' class='modules-model' data-manufacturer='"+manufacturer+"' data-type='"+id+"'>" +
		                    "<span>"+model.Name+"</span>" +
		                "</div>";
            }
            html += "</div>" +
	        		"</div>" +
	    		"</div>";
        }
        $("#modules-sidebar-models").html(html);
    },

    showSidebar:function() {
        $('#modules-model-menu').html('<use xlink:href="#icon-checkmark" />').data('toggle', 'none');
    	$("#modules-config").addClass('sidebar');
        solar_modules.adjustConfig();
        
//      if (dialog.moduleType != null && dialog.moduleType != '') {
//          var groups = Object.keys(dialog.moduleMeta);
//          var group = dialog.moduleType.split('/')[0];
//          var index = groups.indexOf(group);
//          if (index >= 0) {
//              var module = dialog.moduleMeta[group][dialog.moduleType];
//
//              $('#module-description').html(module.Name+'<br><em style="color:#888">'+module.Description+'</em>');
//              
//              dialog.moduleNavStart = Math.floor(index/10)*10;
//              dialog.moduleNavEnd = dialog.moduleNavStart + 100;
//              dialog.drawModuleSidebar();
//              
//              $(".module-body[group='"+group+"']").show();
//              $(".module-row[type='"+dialog.moduleType+"']").addClass("module-selected");
//              $("#module-sidebar").scrollTop();
//              
//              return;
//          }
//          else {
//              $(".module-body").hide();
//              $(".module-row").removeClass("module-selected");
//              $('#module-description').text('');
//          }
//      }
//      else {
//          $(".module-body").hide();
//          $(".module-row").removeClass("module-selected");
//          $('#module-description').text('');
//      }
    },

    hideSidebar:function() {
        $('#modules-model-menu').html('<use xlink:href="#icon-dots-vertical" />').data('toggle', 'dropdown');
    	$("#modules-config").removeClass('sidebar');
        solar_modules.adjustConfig();
    },

    showAdvanced:function() {
    	alert("Not implemented yet.");
    },

    openDeletion: function(inverter, id) {
        solar_modules.id = id;
        solar_modules.inverter = inverter;
        
        $('#modules-delete-modal').modal('show');
        $('#modules-delete-label').html('Delete modules');
        $("#modules-delete-confirm").off('click').on('click', function() {
            $('#modules-delete-loader').show();
            
            solar.modules.remove(solar_modules.inverter, solar_modules.id, function(result) {
                $('#modules-delete-loader').hide();
                
                if (typeof result.success !== 'undefined' && !result.success) {
                    alert('Unable to delete modules:\n'+result.message);
                    return false;
                }
                let systems = view.systems;
                delete systems[solar_modules.inverter.sysid]
                        .inverters[solar_modules.inverter.id]
                        .modules[solar_modules.id];
                
                draw(systems);
                $('#modules-delete-modal').modal('hide');
            });
        });
    }
}
