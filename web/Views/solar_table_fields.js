/*
  table.js is released under the GNU Affero General Public License.
  See COPYRIGHT.txt and LICENSE.txt.

  Part of the OpenEnergyMonitor project: http://openenergymonitor.org
  2016-12-20 - Expanded tables by : Nuno Chaveiro  nchaveiro(a)gmail.com  
*/

var solartablefields = {
    'iconview': {
        'draw': function (t,row,child_row,field) {
            var icon = 'icon-eye-open'; if (t.fields[field].icon) icon = t.fields[field].icon;
            return "<a href='"+t.fields[field].link+t.data[row]['feedid']+"' ><i class='"+icon+"' ></i></a>" 
        }
    },

    'modulelist': {
        'draw': function (t,row,child_row,field) {
            return parse_module_label(t.data[row][field]);
        }
    }
}

function parse_module_label(modules) {
    if (!modules) return "";
    
    var out = "";
    for (i in modules) {
        var name = modules[i]['name'];
        var feedid = modules[i]['feedid'];
        
        var title = name + " forecast";
        var type;
        var link = ""
        if (feedid > 0) {
            link = " href='"+path+"graph/"+feedid+"'";
            
            title += " (Feed " + feedid + ")";
            type = "info";
        }
        else {
            title += " not available"
            type = "comment";
        }
        out += "<a target='_blank'"+link+"<span class='label label-"+type+"' title='"+title+"' style='cursor:pointer'><small>"+name+"</small></span></a> "; 
    }
    return out;
}
