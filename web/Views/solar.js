var solar = {

    'list':function(callback) {
    	return $.ajax({                                      
	        url: path+"solar/list.json",
	        dataType: 'json',
	        async: true,
	        success: callback
	    });
    }

}
