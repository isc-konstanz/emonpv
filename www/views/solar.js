var solar = {

    system: {
        create:function(model, name, description, location, inverters, callback) {
            return solar.request(callback, "solar/create.json", 
                    "model="+model+
                    "&name="+name+
                    "&description="+description+
                    "&inverters="+inverters+
                    "&location="+JSON.stringify(location));
        },
        run:function(id, callback) {
            return solar.request(callback, "solar/run.json", "id="+id);
        },
        list:function(callback) {
            return solar.request(callback, "solar/list.json");
        },
        get:function(id, callback) {
            return solar.request(callback, "solar/get.json", "id="+id);
        },
        download:function(id) {
        	window.open(path+"solar/download.json?id="+id);
        },
        update:function(id, fields, callback) {
            return solar.request(callback, "solar/update.json", "id="+id+
                    "&fields="+JSON.stringify(fields));
        },
        remove:function(id, callback) {
            return solar.request(callback, "solar/delete.json", "id="+id);
        },
        configs: {
            download:function(id, cfgid) {
                window.open(path+"solar/configs/download.json?id="+id+"&cfgid="+cfgid);
            }
        }
    },

    inverter: {
        create:function(system, callback) {
            return solar.request(callback, "solar/inverter/create.json", "sysid="+system.id);
        },
        update:function(id, fields, callback) {
            return solar.request(callback, "solar/inverter/update.json", "id="+id+
                    "&fields="+JSON.stringify(fields));
        },
        remove:function(id, callback) {
            return solar.request(callback, "solar/inverter/delete.json", "id="+id);
        },
        configs: {
            create:function(inverter, strid, type, orientation, rows, mounting, tracking, callback) {
                if (mounting !== false) {
                    mounting = JSON.stringify(mounting);
                }
                if (tracking !== false) {
                    tracking = JSON.stringify(tracking);
                }
                return solar.request(callback, "solar/inverter/configs/create.json", 
                        "id="+inverter.id+
                        "&strid="+strid+
                        "&type="+type+
                        "&orientation="+orientation+
                        "&rows="+JSON.stringify(rows)+
                        "&mounting="+mounting+
                        "&tracking="+tracking);
            },
            remove:function(inverter, cfgid, callback) {
                return solar.request(callback, "solar/inverter/configs/delete.json", "id="+inverter.id+"&cfgid="+cfgid);
            }
        }
    },

    configs: {
        download:function(sysid, id) {
            window.open(path+"solar/configs/download.json?sysid="+sysid+"&id="+id);
        },
        update:function(id, fields, callback) {
            return solar.request(callback, "solar/configs/update.json", "id="+id+
                    "&fields="+JSON.stringify(fields));
        }
    },

    request:function(callback, action, data) {
        var request = {
            'url': path+action,
            'dataType': 'json',
            'async': true,
            'success': callback,
            'error': function(error) {
                var message = "Failed to request server";
                if (typeof error !== 'undefined') {
                    message += ": ";
                    
                    if (typeof error.responseText !== 'undefined') {
                        message += error.responseText;
                    }
                    else if (typeof error !== 'string') {
                        message += JSON.stringify(error);
                    }
                    else {
                        message += error;
                    }
                }
                console.warn(message);
                if (typeof callback === 'function') {
                    callback({
                        'success': false,
                        'message': message
                    });
                }
//                return solar.request(callback, action, data);
            }
        }
        if (typeof data !== 'undefined') {
            request['data'] = data;
        }
        return $.ajax(request);
    }
}
