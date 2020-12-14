var solar = {

    system: {
        create:function(model, name, description, location, inverters, callback) {
            let route = "solar/create.json";
            let params = "model="+model+
                    "&name="+name+
                    "&description="+description+
                    "&inverters="+inverters+
                    "&location="+JSON.stringify(location);
            
            if (typeof location.file !== "undefined") {
                let file = document.getElementById("system-file-input").files[0];
                let data = new FormData();
                data.append(location.file, file);
                
                return solar.fetch(callback, "POST", route+'?'+params, data);
            }
            return solar.post(callback, route, params);
        },
        run:function(id, callback) {
            return solar.post(callback, "solar/run.json", "id="+id);
        },
        list:function(callback) {
            return solar.get(callback, "solar/list.json");
        },
        get:function(id, callback) {
            return solar.get(callback, "solar/get.json", "id="+id);
        },
        export:function(id) {
            window.open(path+"solar/export.json?id="+id);
        },
        download:function(id) {
            window.open(path+"solar/download.json?id="+id);
        },
        update:function(id, fields, callback) {
            let route = "solar/update.json?id="+id+"&fields="+JSON.stringify(fields);
            
            if (typeof fields.file !== "undefined") {
                let file = document.getElementById("system-file-input").files[0];
                let data = new FormData();
                data.append(fields.file, file);
                
                return solar.fetch(callback, "POST", route, data);
            }
            return solar.put(callback, route);
        },
        remove:function(id, callback) {
            return solar.delete(callback, "solar/delete.json?id="+id);
        }
    },

    inverter: {
        create:function(system, callback) {
            return solar.post(callback, "solar/inverter/create.json", "sysid="+system.id);
        },
        update:function(id, fields, callback) {
            return solar.put(callback, "solar/inverter/update.json?id="+id+
                    "&fields="+JSON.stringify(fields));
        },
        remove:function(id, callback) {
            return solar.delete(callback, "solar/inverter/delete.json?id="+id);
        }
    },

    configs: {
		create:function(sysid, invid, strid, rows, mounting, tracking, losses, orientation, module, callback) {
			if (mounting !== false) {
				mounting = JSON.stringify(mounting);
			}
			if (tracking !== false) {
				tracking = JSON.stringify(tracking);
			}
			if (losses !== false) {
				losses = JSON.stringify(losses);
			}
			return solar.post(callback, "solar/configs/create.json", 
					"sysid="+sysid+
					"&invid="+invid+
					"&strid="+strid+
					"&rows="+JSON.stringify(rows)+
					"&mounting="+mounting+
					"&tracking="+tracking+
					"&losses="+losses+
					"&orientation="+orientation+
					"&module="+JSON.stringify(module));
		},
        download:function(id, sysid) {
            window.open(path+"solar/configs/download.json?id="+id+"&sysid="+sysid);
        },
        update:function(id, fields, callback) {
            return solar.put(callback, "solar/configs/update.json?id="+id+
                    "&fields="+JSON.stringify(fields));
        },
		remove:function(id, sysid, invid, callback) {
			return solar.delete(callback, "solar/configs/delete.json?id="+id+"&sysid="+sysid+"&invid="+invid);
		}
    },

    module: {
        list:function(callback) {
            return solar.get(callback, "solar/module/list.json");
        },
        get:function(type, callback) {
            return solar.get(callback, "solar/module/get.json", "type="+type);
        }
    },

    get:function(callback, route, data) {
        return $.ajax(solar.request(callback, 'GET', route, data));
    },

    post:function(callback, route, data) {
        return $.ajax(solar.request(callback, 'POST', route, data));
    },

    put:function(callback, route, data) {
        return $.ajax(solar.request(callback, 'PUT', route, data));
    },

    delete:function(callback, route, data) {
        return $.ajax(solar.request(callback, 'DELETE', route, data));
    },

    request:function(callback, method, route, data) {
        var request = {
            'url': path+route,
            'method': method,
            'dataType': 'json',
            'async': true,
            'success': callback,
            'error': function(error) { solar.error(callback, error); }
        }
        if (typeof data !== 'undefined') {
            request['data'] = data;
        }
        return request;
    },

    fetch:function(callback, method, route, data) {
        let options = {
            method: method
        };
        if (typeof data !== 'undefined') {
            options['body'] = data;
        }
        return fetch(path+route, options)
                .then(response => response.text())
                .then(function(result) {
					try {
						callback(JSON.parse(result));
					} catch(error) {
						solar.error(callback, result);
					}
                })
                .catch(function(error) { solar.error(callback, error); });
    },

    error:function(callback, error) {
        var message = "Failed to request server";
        if (typeof error !== 'undefined') {
            message += ": ";
            
            if (typeof error.responseText !== 'undefined') {
                message += error.responseText;
            }
            else if (typeof error.message !== 'undefined') {
                message += error.message;
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
    }
}
