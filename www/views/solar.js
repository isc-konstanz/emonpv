var solar = {

    create:function(model, name, description, location, callback) {
        return solar.request(callback, "solar/create.json", "model="+model+"&name="+name+"&description="+description+
        		"&location="+JSON.stringify(location));
    },

    list:function(callback) {
        return solar.request(callback, "solar/list.json");
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
//	        	return solar.request(callback, action, data);
	        }
	    }
		if (typeof data !== 'undefined') {
			request['data'] = data;
		}
	    return $.ajax(request);
    }
}
