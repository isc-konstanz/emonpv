var solar = {

    system: {
        create:function(model, name, description, location, callback) {
            return solar.request(callback, "solar/create.json", "model="+model+"&name="+name+"&description="+description+
                    "&location="+JSON.stringify(location));
        },

        list:function(callback) {
            return solar.request(callback, "solar/list.json");
        }
    },

    inverter: {
        create:function(system, callback) {
            return solar.request(callback, "solar/inverter/create.json", "sysid="+system.id);
        },
        remove:function(system, id, callback) {
            return solar.request(callback, "solar/inverter/delete.json", "sysid="+system.id+"&id="+id);
        }
    },

    modules: {
        create:function(inverter, azimuth, tilt, type, settings, callback) {
            return solar.request(callback, "solar/modules/create.json", "invid="+inverter.id+"&azimuth="+azimuth+"&tilt="+tilt+"&type="+type+
                    "&settings="+JSON.stringify(settings));
        },
        remove:function(inverter, id, callback) {
            return solar.request(callback, "solar/modules/delete.json", "invid="+inverter.id+"&id="+id);
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
