var solar = {

    'create':function(name, desc, lon, lat, modules, callback) {
    	return $.ajax({
	        url: path+"solar/create.json",
	        data: "name="+name+"&description="+desc+"&longitude="+lon+"&latitude="+lat+"&modules="+JSON.stringify(modules), 
	        dataType: 'json',
	        async: true,
	        success: callback
	    });
    },

    'list':function(callback) {
    	return $.ajax({
	        url: path+"solar/list.json",
	        dataType: 'json',
	        async: true,
	        success: callback
	    });
    },

    'get':function(id, callback) {
    	return $.ajax({
	        url: path+"solar/get.json",
	        data: "id="+id,
	        dataType: 'json',
	        async: true,
	        success: callback
	    });
    },

    'set':function(id, fields, callback) {
    	return $.ajax({
	        url: path+"solar/set.json",
	        data: "id="+id+"&fields="+JSON.stringify(fields),
	        dataType: 'json',
	        async: true,
	        success: callback
	    });
    },

    'remove':function(id, callback) {
    	return $.ajax({
	        url: path+"solar/delete.json",
	        data: "id="+id,
	        dataType: 'json',
	        async: true,
	        success: callback
	    });
    }

}
