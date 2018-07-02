var solar = {

    'create':function(name, desc, location, modules, callback) {
        return $.ajax({
            url: path+"solar/create.json",
            data: "name="+name+"&description="+desc+"&location="+JSON.stringify(location)+"&modules="+JSON.stringify(modules), 
            dataType: 'json',
            async: true,
            success: callback
        });
    },

    'init':function(id, template, callback) {
        return $.ajax({
            url: path+"solar/init.json",
            type: 'POST',
            data: "id="+id+"&template="+JSON.stringify(template),
            dataType: 'json',
            async: true,
            success: callback
        });
    },

    'prepare':function(id, callback) {
        return $.ajax({
            url: path+"solar/prepare.json",
            data: "id="+id,
            dataType: 'json',
            async: true,
            success: callback
        });
    },

    'meta':function(callback) {
        return $.ajax({
            url: path+"solar/module/meta.json",
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
