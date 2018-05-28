var dialog =
{
	moduleMeta: null,
    moduleType: null,
    module: null,
    modules: [],
    system: null,
    template: null,

    'loadSystemConfig':function(system) {
        if (system != null) {
            this.system = system;
            
            // The modules array needs to be deep cloned, to allow the comparison for changed modules later
            this.modules = JSON.parse(JSON.stringify(system.modules));
        }
        else {
            this.system = null;
            this.modules = [];
        }
        this.template = null;
        this.module = null;
        this.moduleType = null;
        
        this.drawSystemConfig();
    },

    'drawSystemConfig':function() {
        $("#system-modal").modal('show');
        this.adjustSystemModal();
        
        $('#system-name-tooltip').attr("title", 
        		"The name should work as a unique identifier for the system, " +
				"to be able to distinguish e.g. the systems <i>roof</i> and <i>garage</i>.").tooltip({html: true});
        
        $('#system-description-tooltip').attr("title", 
        		"The description provides space for small descriptive comments " +
        		"regarding the specific system and may be left empty").tooltip({html: true});
        
        $('#system-location-tooltip').attr("title", 
        		"The geographic coordinates longitude and latitude of the solar system.<br>" +
        		"Those may be extracted e.g. by using <a href='https://www.google.de/maps'>Google Maps<a>").tooltip({html: true});
        
        if (this.system != null) {
            $('#system-name').val(this.system.name);
            $('#system-description').val(this.system.description);
            $('#system-longitude').val(this.system.longitude);
            $('#system-latitude').val(this.system.latitude);
            $('#system-delete').show();
            $("#system-init").show();
        }
        else {
            $('#system-name').val('');
            $('#system-description').val('');
            $('#system-longitude').val('');
            $('#system-latitude').val('');
            $('#system-delete').hide();
            $("#system-init").hide();
        }
        this.drawSystemModules();
        
        this.loadModuleSidebar();
    },

    'drawSystemModules':function() {
        var table = $("#system-modules-table");
        
        if (dialog.modules.length > 0) {
            table.html("<tr id='system-modules-header'></tr>");
            
            var row = $("#system-modules-header");
            row.append("<th>Manufacturer</th>");
            row.append("<th>Model</th>");
            row.append("<th>Count</th>");
            row.append("<th></th>");
            row.append("<th></th>");
            
            for (var i = 0; i < dialog.modules.length; i++) {
            	var type = dialog.modules[i].type;
            	var module = dialog.getModule(type);
            	
                table.append("<tr id='system-modules-row-"+i+"' row='"+i+"'></tr>");
                row = $("#system-modules-row-"+i);
            	row.append("<td>" + module.Manufacturer + "</td>");
                row.append("<td>" + module.Model_Number + "</td>");
                row.append("<td>" + dialog.modules[i].count + "</td>");
                row.append("<td><a class='module-edit' title='Edit'><i class='icon-wrench' style='cursor:pointer'></i></a></td>");
                row.append("<td><a class='module-remove' title='Remove'><i class='icon-trash' style='cursor:pointer'></i></a></td>");
            }
            $("#system-modules-table").show();
            $("#system-modules-none").hide();
        }
        else {
            table.text("");
            $("#system-modules-table").hide();
            $("#system-modules-none").show();
        }
        
        // Initialize callbacks
        dialog.registerSystemEvents();
    },

    'closeSystemConfig':function(result) {
    	if (typeof result.success !== 'undefined' && !result.success) {
            alert(result.message);
            return false;
        }
        $('#system-modal').modal('hide');
        update();
        
        return true
    },

    'adjustSystemModal':function() {

        var width = $(window).width();
        var height = $(window).height();
        
        if ($("#system-modal").length) {
            var h = height - $("#system-modal").position().top - 180;
            $("#system-body").height(h);
        }
    },

    'registerSystemEvents':function() {

        $("#system-save").off('click').on('click', function() {
            var name = $('#system-name').val();
            var lon = $('#system-longitude').val();
            var lat = $('#system-latitude').val();
            
            if (name && lon && lat && dialog.modules.length > 0) {
                var desc = $('#system-description').val();
                
                if (dialog.system != null) {
                    var fields = {};
                    if (dialog.system.name != name) fields['name'] = name;
                    if (dialog.system.description != desc) fields['description'] = desc;
                    
                    var foo = JSON.stringify(dialog.system.modules);
                    var bar = JSON.stringify(dialog.modules);
                    
                    if (JSON.stringify(dialog.system.modules) != JSON.stringify(dialog.modules)) {
                    	fields['modules'] = dialog.modules;
                    }
                    
                    solar.set(dialog.system.id, fields, dialog.closeSystemConfig);
                }
                else {
                    solar.create(name, desc, lon, lat, dialog.modules, function(result) {
                    	if (dialog.closeSystemConfig(result)) {
//                          init = true;
//                          dialog.device = {
//                                  id: result,
//                                  nodeid: node,
//                                  name: name,
//                                  type: dialog.deviceType
//                          };
//                          dialog.loadInitConfig();
                    	}
                    });
                }
            }
            else {
                alert('System needs to be configured first.');
                return false;
            }
        });
        
        $('#system-modules-table').on('click', '.module-edit', function() {
            var row = $(this).closest('tr').attr('row');
            var module = dialog.modules[row];
            
            $('#system-modal').modal('hide');
            dialog.loadModuleConfig(module);
        });
        
        $('#system-modules-table').on('click', '.module-remove', function() {
            var row = $(this).closest('tr').attr('row');
            dialog.modules.splice(row, 1);
            dialog.drawSystemModules();
        });
        
        $("#system-modules-add").off('click').on('click', function() {
            $('#system-modal').modal('hide');
            dialog.loadModuleConfig();
        });
        
        $("#system-init").off('click').on('click', function() {
            $('#system-modal').modal('hide');
            dialog.loadInitConfig();
        });
        
        $("#system-delete").off('click').on('click', function() {
            $('#system-modal').modal('hide');
            dialog.loadSystemDelete(dialog.system);
        });
    },

    'loadInitConfig': function() {
    	dialog.template = [];
        solar.prepare(dialog.system.id, function(result) {
            if (typeof result.success !== 'undefined' && !result.success) {
                alert('Unable to initialize system:\n'+result.message);
                return false;
            }
            dialog.template = result;
            dialog.drawInitConfig();
        });
        
        // Initialize callbacks
        $("#system-init-confirm").off('click').on('click', function() {
            $('#system-init-modal').modal('hide');
            
            var template = dialog.parseInitTemplate();
            var foo = JSON.stringify(template);
            solar.init(dialog.system.id, template, function(result) {
                if (typeof result.success !== 'undefined' && !result.success) {
                    alert('Unable to initialize system:\n'+result.message);
                    return false;
                }
            });
        });
    },

    'adjustInitModal':function() {
        var width = $(window).width();
        var height = $(window).height();
        
        if ($("#system-init-modal").length) {
            var h = height - $("#system-init-modal").position().top - 180;
            $("#system-init-body").height(h);
        }
    },

    'drawInitConfig': function() {
        $('#system-init-modal').modal('show');
        $('#system-init-modal-label').html('Initialize System: <b>'+dialog.system.name+'</b>');
        dialog.adjustInitModal();
        
        if (typeof dialog.template.feeds !== 'undefined' && dialog.template.feeds.length > 0) {
            $('#system-init-feeds').show();
            var table = "";
            for (var i = 0; i < dialog.template.feeds.length; i++) {
                var feed = dialog.template.feeds[i];
                var row = "";
                if (feed.action.toLowerCase() == "none") {
                    row += "<td><input row='"+i+"' class='input-select' type='checkbox' checked disabled /></td>";
                }
                else {
                    row += "<td><input row='"+i+"' class='input-select' type='checkbox' checked /></td>";
                }
                row += "<td>"+dialog.drawInitAction(feed.action)+"</td>"
                row += "<td>"+feed.tag+"</td><td>"+feed.name+"</td>";
                row += "<td>"+dialog.drawInitProcessList(feed.processList)+"</td>";
                
                table += "<tr>"+row+"</tr>";
            }
            $('#system-init-feeds-table').html(table);
        }
        else {
            $('#system-init-feeds').hide();
        }
        
        if (typeof dialog.template.inputs !== 'undefined' && dialog.template.inputs.length > 0) {
            $('#system-init-inputs').show();
            var table = "";
            for (var i = 0; i < dialog.template.inputs.length; i++) {
                var input = dialog.template.inputs[i];
                var row = "";
                if (input.action.toLowerCase() == "none") {
                    row += "<td><input row='"+i+"' class='input-select' type='checkbox' checked disabled /></td>";
                }
                else {
                    row += "<td><input row='"+i+"' class='input-select' type='checkbox' checked /></td>";
                }
                row += "<td>"+dialog.drawInitAction(input.action)+"</td>"
                row += "<td>"+input.node+"</td><td>"+input.name+"</td><td>"+input.description+"</td>";
                row += "<td>"+dialog.drawInitProcessList(input.processList)+"</td>";
                
                table += "<tr>"+row+"</tr>";
            }
            $('#system-init-inputs-table').html(table);
        }
        else {
            $('#system-init-inputs').hide();
            $('#system-init-inputs-table').html("");
        }
        
        return true;
    },

    'drawInitAction': function(action) {
        action = action.toLowerCase();
        
        var color;
        if (action === 'create' || action === 'set') {
            color = "rgb(0,110,205)";
        }
        else if (action === 'override') {
            color = "rgb(255,125,20)";
        }
        else {
            color = "rgb(50,200,50)";
            action = "exists"
        }
        action = action.charAt(0).toUpperCase() + action.slice(1);
        
        return "<span style='color:"+color+";'>"+action+"</span>";
    },

    'drawInitProcessList': function(processList) {
        if (!processList || processList.length < 1) return "";
        var out = "";
        for (var i = 0; i < processList.length; i++) {
            var process = processList[i];
            if (process['arguments'] != undefined && process['arguments']['value'] != undefined && process['arguments']['type'] != undefined) {
                var name = "<small>"+process["name"]+"</small>";
                var value = process['arguments']['value'];
                
                var title;
                var color = "info";
                switch(process['arguments']['type']) {
                case 0: // VALUE
                    title = "Value: " + value;
                    break;
                    
                case 1: // INPUTID
                    title = "Input: " + value;
                    break;
                    
                case 2: // FEEDID
                    title = "Feed: " + value;
                    break;
                    
                case 4: // TEXT
                    title = "Text: " + value;
                    break;

                case 5: // SCHEDULEID
                    title = "Schedule: " + value;
                    break;

                default:
                    title = value;
                    break;
                }
                out += "<span class='label label-"+color+"' title='"+title+"' style='cursor:default'>"+name+"</span> ";
            }
        }
        return out;
    },

    'parseInitTemplate': function() {
        var template = {};
        
        template['feeds'] = [];
        if (typeof dialog.template.feeds !== 'undefined' && 
                dialog.template.feeds.length > 0) {
            
            var feeds = dialog.template.feeds;
            $("#system-init-feeds-table tr").find('input[type="checkbox"]:checked').each(function() {
                template['feeds'].push(feeds[$(this).attr("row")]); 
            });
        }
        
        template['inputs'] = [];
        if (typeof dialog.template.inputs !== 'undefined' && 
                dialog.template.inputs.length > 0) {
            
            var inputs = dialog.template.inputs;
            $("#system-init-inputs-table tr").find('input[type="checkbox"]:checked').each(function() {
                template['inputs'].push(inputs[$(this).attr("row")]); 
            });
        }
        
        return template;
    },

    'loadSystemDelete': function(system, row) {
        dialog.system = system;
        
        $('#system-delete-modal').modal('show');
        $('#system-delete-modal-label').html('Delete System: <b>'+dialog.system.name+'</b>');
        
        // Initialize callbacks
        dialog.registerDeleteEvents(row);
    },

    'registerDeleteEvents':function(row) {
        
        $("#system-delete-confirm").off('click').on('click', function() {
            solar.remove(dialog.system.id, function() {
                if (row != null) {
                    table.remove(row);
                }
                update();
                $('#system-delete-modal').modal('hide');
            });
        });
    },

    'getModule':function(type) {
        var t = type.split('/');
        if (dialog.moduleMeta.hasOwnProperty(t[0]) &&
        		dialog.moduleMeta[t[0]].hasOwnProperty(t[1]) &&
        		dialog.moduleMeta[t[0]][t[1]].hasOwnProperty(t[2])) {
        	
        	return dialog.moduleMeta[t[0]][t[1]][t[2]];
        }
        return null;
    },

    'loadModuleConfig':function(module) {
    	if (module != null) {
    		dialog.module = module;
    		dialog.moduleType = module.type;
    	}
    	else {
    		dialog.module = null;
    		dialog.moduleType = null;
    	}
    	dialog.drawModuleConfig();
    },

    'loadModuleSidebar':function(module) {
        var table = "";
        var modules = dialog.moduleMeta;
        for (var method in modules) {
            if (modules.hasOwnProperty(method)) {
            	
                for (var manufacturer in modules[method]) {
                    if (modules[method].hasOwnProperty(manufacturer)) {
                    	var header = false;
                    	
                        for (var number in modules[method][manufacturer]) {
                            if (modules[method][manufacturer].hasOwnProperty(number)) {
                            	var module = modules[method][manufacturer][number];
                                var id = [method, manufacturer, number].join('/');
                            	
                            	if (!header) {
                                    header = true;
                                    
                                    table += "<tbody>"
                                    table += "<tr class='module-header' manufacturer='"+manufacturer+"' style='background-color:#ccc; cursor:pointer'>";
                                    table += "<td style='font-size:12px; padding:4px; padding-left:8px; font-weight:bold'>"+module.Manufacturer+"</td>";
                                    table += "</tr>";
                                    table += "</tbody>";
                                    
                                    table += "<tbody class='module-body' manufacturer='"+manufacturer+"' style='display:none'>";
                            	}
                                
                                table += "<tr class='module-row' type='"+id+"'>";
                                table += "<td style='padding-left:12px; cursor:pointer'>"+module.Model_Number+"</td>";
                                table += "</tr>";
                            }
                        }
                        table += "</tbody>";  
                    }
                }
            }
        }
        $("#module-table").html(table);

        // Initialize callbacks
        dialog.registerModuleEvents();
    },

    'drawModuleConfig':function() {
        $("#module-modal").modal('show');
        dialog.adjustModuleModal();

        $('#module-count-tooltip').attr("title", 
        		"The number of solar modules for the specified orientation in the system.").tooltip({html: true});
        
        $('#module-tilt-tooltip').attr("title", 
        		"The modules tilt from horizontal.").tooltip({html: true});
        
        $('#module-azimuth-tooltip').attr("title", 
        		"The modules horizontal angle measured clockwise from north.").tooltip({html: true});
        
        $('#module-albedo-tooltip').attr("title", 
        		"The modules ground reflectance, depending on the ground the system is installed upon.").tooltip({html: true});
        
        if (dialog.module != null) {
            $('#module-count').val(dialog.module.count);
            $('#module-tilt').val(dialog.module.tilt);
            $('#module-azimuth').val(dialog.module.azimuth);
            $('#module-albedo').val(dialog.module.albedo);
            $('#module-delete').show();
            $("#module-save").html("Save");
            $("#module-save").prop('disabled', false);
            $("#module-modal-label").html("Configure Solar Module");
        }
        else {
            $('#module-count').val(1);
            $('#module-tilt').val('');
            $('#module-azimuth').val('');
            $('#module-albedo').val(0);
            $('#module-delete').hide();
            $("#module-save").html("Add");
            $("#module-save").prop('disabled', true);
            $("#module-modal-label").html("Add Solar Module");
        }
        if (dialog.moduleType != null && dialog.moduleType != '') {
            var type = dialog.moduleType.split('/');
            var module = modules[type[0]][type[1]][type[2]];
            
            $(".module-body[manufacturer='"+type[1]+"']").show();
            $(".module-row[type='"+dialog.moduleType+"']").addClass("module-selected");
            
            $('#module-description').html('<em style="color:#888">'+module.Description+'</em>');
        }
        else {
            $(".module-body").hide();
            $(".module-row").removeClass("module-selected");
            
            $('#module-description').text('');
        }
    },

    'adjustModuleModal':function() {
        var width = $(window).width();
        var height = $(window).height();
        
        if ($("#module-modal").length) {
            var h = height - $("#module-modal").position().top - 180;
            $("#module-body").height(h);
        }
        
        $("#module-content").css("transition","0");
        $("#module-sidebar").css("transition","0");
        if (width < 1024) {
            $("#module-content").css("margin-left","0");
            $("#module-sidebar").css("width","0");
            $("#module-sidebar-open").show();

            $("#module-content").css("transition","0.5s");
            $("#module-sidebar").css("transition","0.5s");
        }
        else {
            $("#module-content").css("margin-left","250px");
            $("#module-sidebar").css("width","250px");
            $("#module-sidebar-open").hide();
            $("#module-sidebar-close").hide();
        }
    },

    'registerModuleEvents':function() {

        $('#module-table .module-header').off('click').on('click', function() {
            var manufacturer = $(this).attr("manufacturer");
            
            var e = $(".module-body[manufacturer='"+manufacturer+"']");
            if (e.is(":visible")) {
                e.hide();
            }
            else {
                e.show();
                
                // If a module is selected and in the group to uncollapse, show and select it
                if (dialog.moduleType != null && dialog.moduleType != '') {
                    var type = dialog.moduleType.split('/');
                    var module = dialog.moduleMeta[type[0]][type[1]][type[2]];
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
                
                var module = dialog.getModule(type);
                $('#module-description').html('<em style="color:#888">'+module.Description+'</em>');
                $("#module-save").prop('disabled', false);
            }
            else {
                dialog.moduleType = null;
                $('#module-description').text('');
                $("#module-save").prop('disabled', true);
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

            var count = $('#module-count').val();
            var tilt = $('#module-tilt').val();
            var azimuth = $('#module-azimuth').val();
            var albedo = $('#module-albedo').val();
            
            if (dialog.moduleType && count && tilt && azimuth && albedo) {
            	var module;
            	if (dialog.module != null) {
            		module = dialog.module;
            	}
            	else {
                    module = {
                    		'inverter': '',
                            'type': dialog.moduleType,
                            'count': count,
                            'tilt': tilt,
                            'azimuth': azimuth,
                            'albedo': albedo
                    };
            	}
                
                var index = -1;
                for (var i = 0; i < dialog.modules.length; i++) {
                	if (module.type === dialog.modules[i].type &&
                			module.tilt === dialog.modules[i].tilt &&
                			module.azimuth === dialog.modules[i].azimuth &&
                			module.albedo === dialog.modules[i].albedo) {
                		
                		index = i;
                		break;
                	}
                }
                if (index >= 0) {
                	if (dialog.module != null) {
                        module['type'] = dialog.moduleType;
                        module['count'] = count;
                    	module['tilt'] = tilt;
                		module['azimuth'] = azimuth;
            			module['albedo'] = albedo;
            			
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
        
        $("#module-cancel").off('click').on('click', function() {
            $('#system-modal').modal('show');
            dialog.drawSystemModules();
        });
        
        $("#module-delete").off('click').on('click', function() {
        	var index = dialog.modules.indexOf(dialog.module);
        	if (index >= 0) {
                dialog.modules.splice(index, 1);
    		}
            $('#module-modal').modal('hide');
            $('#system-modal').modal('show');
            dialog.drawSystemModules();
        });
    },

    'adjustModal':function() {
    	dialog.adjustSystemModal();
    	dialog.adjustInitModal();
    	dialog.adjustModuleModal();
    }
}
