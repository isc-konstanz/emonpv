var solar_modules = {

    id: null,
    type:null,
    inverter: null,

    newConfig: function(inverter) {
        solar_modules.id = null;
        solar_modules.inverter = inverter;
        solar_modules.drawConfig();
    },

    openConfig: function(inverter, id) {
        solar_modules.id = id;
        solar_modules.inverter = inverter;
        solar_modules.drawConfig(inverter.modules[id]);
    },

    drawConfig: function(modules = null) {
        var modal = $("#modules-config-modal").modal('show');
        if (modules == null) {
            $('#modules-config-label').html('Create modules');
            $('#modules-config-delete').hide();
            //$('#modules-config-save').prop('disabled', true);
            $('#modules-config-save').prop('disabled', false);
            $('#modules-config-save').html('Create');

            $('#modules-count').val(1);
            $('#modules-pitch').val('');
            $('#modules-elevation').val('');
            $('#modules-azimuth').val('');
            $('#modules-tilt').val('');
        }
        else {
            $('#modules-config-label').html('Configure modules');
            $('#modules-config-delete').show();
            $('#modules-config-save').prop('disabled', false);
            $('#modules-config-save').html('Save');

            $('#modules-count').val(modules.count);
            $('#modules-pitch').val(modules.geometry.pitch);
            $('#modules-elevation').val(modules.geometry.elevation);
            $('#modules-azimuth').val(modules.geometry.azimuth);
            $('#modules-tilt').val(modules.geometry.tilt);
        }
        $('#modules-pitch-tooltip').tooltip({html:true, container:modal});
        $('#modules-geometry-tooltip').tooltip({html:true, container:modal});
        $('#modules-settings-tooltip').tooltip({html:true, container:modal});
        
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
        
        solar_modules.registerConfigEvents();
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
                    html += "<div id='modules-model-"+id.replace('/', '-')+"' data-manufacturer='"+manufacturer+"' data-type='"+id+"'>" +
		                    "<span>"+model.Name+"</span>" +
		                "</div>";
            }
            html += "</div>" +
	        		"</div>" +
	    		"</div>";
        }
        $("#modules-sidebar-models").html(html);
        
        // Initialize callbacks
        //dialog.registerModuleEvents();
    },

    saveConfig: function() {
        var type = "Placeholder";

        var azimuth = $('#modules-azimuth').val();
        var tilt = $('#modules-tilt').val();

        if (solar_modules.modules == null) {
            var geometry = {
                    'pitch': 0,
                    'elevation': 0,
                    'azimuth': azimuth,
                    'tilt': tilt
            };
            var tracking = {};
            var settings = {};
            
            solar.modules.create(solar_modules.inverter, 1, 1, geometry, tracking, type, 1, settings, solar_modules.closeConfig);
        }
        else {
            var fields = {};
            
            solar.modules.set(solar_modules.id, fields, solar_modules.closeConfig);
        }
    },

    registerConfigEvents:function() {

        $('#module-table .module-header').off('click').on('click', function() {
            var group = $(this).attr("group");
            
            var e = $(".module-body[group='"+group+"']");
            if (e.is(":visible")) {
                e.hide();
            }
            else {
                e.show();
                
                // If a module is selected and in the group to uncollapse, show and select it
                if (dialog.moduleType != null && dialog.moduleType != '') {
                    var module = dialog.moduleMeta[group][dialog.moduleType];
                    if (module && type[1] == module.Manufacturer) {
                        $(".module-row[type='"+dialog.moduleType+"']").addClass("module-selected");
                    }
                }
            }
        });

        $("#module-table .module-row").off('click').on('click', function() {
            var type = $(this).attr("type");
            
            $(".module-row[type='"+dialog.moduleType+"']").removeClass("module-selected");
            if (dialog.moduleType !== type) {
                $(this).addClass("module-selected");
                dialog.moduleType = type;

                var group = $(this).attr("group");
                var module = dialog.moduleMeta[group][type];
                $('#module-description').html(module.Name+'<br><em style="color:#888">'+module.Description+'</em>');
                $("#module-save").prop('disabled', false);
            }
            else {
                dialog.moduleType = null;
                $('#module-type').text('');
                $('#module-description').text('');
                $("#module-save").prop('disabled', true);
            }
        });

        $("#module-sidebar").off('scroll').on('scroll', function (e) {
            e.stopPropagation();
            e.preventDefault();
            
            var navigation = $(this);
            var height = (navigation.scrollTop() + navigation.innerHeight())/navigation.prop('scrollHeight')*100;
            if ((height == 0 && dialog.moduleNavStart > 0) || height == 100) {
                if (!navigation.data('redraw')) {
                    navigation.data('redraw', true);
                    
                    var alreadyRedrawnTimeout = setTimeout(function() {
                        var length = Object.keys(dialog.moduleMeta).length;
                        if (height == 0) {
                            dialog.moduleNavStart = Math.max(0, dialog.moduleNavStart-10);
                            if (dialog.moduleNavEnd - dialog.moduleNavStart > 250) {
                                dialog.moduleNavEnd = dialog.moduleNavStart + 250;
                            }
                        }
                        else if (height== 100) {
                            dialog.moduleNavEnd = Math.min(dialog.moduleNavEnd+10, length);
                            if (dialog.moduleNavEnd - dialog.moduleNavStart > 250) {
                                dialog.moduleNavStart = dialog.moduleNavEnd - 250;
                            }
                        }
                        dialog.drawModuleSidebar();
                        
//                        navigation.animate({ scrollTop: navigation.scrollTop()+offset }, 250);
                        navigation.data('redraw', false); // reset when it happens
                        
                    }, 250); // tolerance
                    navigation.data('alreadyRedrawnTimeout', alreadyRedrawnTimeout); // store this id to clear if necessary
                }
            }
        });

        $("#module-sidebar-open").off('click').on('click', function() {
            $("#module-sidebar").css("width","250px");
            $("#module-sidebar-close").show();
        });

        $("#module-sidebar-close").off('click').on('click', function() {
            $("#module-sidebar").css("width","0");
            $("#module-sidebar-close").hide();
        });

        $("#module-save").off('click').on('click', function() {
            var name = $('#module-name').val();
            var tilt = $('#module-tilt').val();
            var azimuth = $('#module-azimuth').val();
            var albedo = $('#module-albedo').val();
            var strings = $('#module-strings').val();
            var modules = $('#module-number').val();
            
            if (name && dialog.moduleType && tilt && azimuth && albedo && strings && modules) {
                var module;
                if (dialog.module != null) {
                    module = dialog.module;
                }
                else {
                    module = {
                            'name': name,
                            'type': dialog.moduleType,
                            'inverter': '',
                            'tilt': tilt,
                            'azimuth': azimuth,
                            'albedo': albedo,
                            'modules_per_string': modules,
                            'strings_per_inverter': strings
                    };
                }
                
                var index = -1;
                for (var i = 0; i < dialog.modules.length; i++) {
                    if (module.name === dialog.modules[i].name &&
                            module.type === dialog.modules[i].type &&
                            module.tilt === dialog.modules[i].tilt &&
                            module.azimuth === dialog.modules[i].azimuth &&
                            module.albedo === dialog.modules[i].albedo &&
                            module.modules_per_string === dialog.modules[i].modules_per_string &&
                            module.strings_per_inverter === dialog.modules[i].strings_per_inverter) {
                        
                        index = i;
                        break;
                    }
                }
                if (index >= 0) {
                    if (dialog.module != null) {
                        module['name'] = name;
                        module['type'] = dialog.moduleType;
                        module['tilt'] = tilt;
                        module['azimuth'] = azimuth;
                        module['albedo'] = albedo;
                        module['modules_per_string'] = strings;
                        module['strings_per_inverter'] = modules;
                        
                        dialog.modules[index] = module;
                    }
                    else {
                        alert('Modules for this configuration already exist.');
                        return false;
                    }
                }
                else {
                    dialog.modules.push(module);
                }
                
                $('#module-modal').modal('hide');
                $('#system-modal').modal('show');
                dialog.drawSystemModules();
            }
            else {
                alert('Modules need to be configured first.');
                return false;
            }
        });

        $("#modules-config-delete").off('click').on('click', function () {
            $('#modules-config-modal').modal('hide');
            
            solar_modules.openDeletion(solar_modules.inverter, solar_modules.id);
        });

        $("#modules-config-save").off('click').on('click', function() {
            solar_modules.saveConfig();
        });
    },

    closeConfig: function(result) {
        $('#modules-config-loader').hide();
        
        if (typeof result.success !== 'undefined' && !result.success) {
            alert('Solar modules could not be configured:\n'+result.message);
            return false;
        }
        update();
        $('#modules-config-modal').modal('hide');
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
