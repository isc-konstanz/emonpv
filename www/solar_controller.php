<?php
/*
 All Emoncms code is released under the GNU Affero General Public License.
 See COPYRIGHT.txt and LICENSE.txt.
 
 ---------------------------------------------------------------------
 Emoncms - open source energy visualisation
 Part of the OpenEnergyMonitor project:
 http://openenergymonitor.org
 
 */

// no direct access
defined('EMONCMS_EXEC') or die('Restricted access');

class SolarException extends Exception {
    public function getResult() {
        return array('success'=>false, 'message'=>$this->getMessage());
    }
}

function solar_controller() {
    global $mysqli, $redis, $session, $route;
    
    require_once("Modules/solar/libs/models/solar_modules.php");
    require_once("Modules/solar/libs/models/solar_inverter.php");
    require_once("Modules/solar/libs/models/solar_system.php");
    $system = new SolarSystem($mysqli, $redis);
    
    if ($route->format == 'html') {
        if (!$session['read']) {
            // Empty string result forces the user back to login
            return '';
        }
        else if ($route->action == "view" && $session['write']) return view("Modules/solar/views/solar_view.php", array());
        else if ($route->action == 'api' && $session['write']) return view("Modules/solar/views/solar_api.php", array());
    }
    else if ($route->format == 'json' && $session['userid'] > 0) {
        try {
            return system_controller($system);
            
        } catch(SolarException $e) {
            return $e->getResult();
        }
    }
    return array('content'=>EMPTY_ROUTE);
}

function system_controller($system) {
    global $session, $route;
    
    if ($route->action == "create" && $session['write']) {
        return $system->create($session['userid'], get('model'), get('name'), get('description'), get('location'));
    }
    else if ($route->action == 'list' && $session['read']) {
        return $system->get_list($session['userid']);
    }
    else if ($session['read']) {
        $sysid = get('id');
        if (!empty($sysid)) {
            $details = $system->get($sysid);
            if ($details['userid'] != $session['userid']) {
                return array('success'=>false, 'message'=>'Invalid permissions to access this system');
            }
            
            if ($route->action == "get") {
                return $details;
            }
            else if ($route->action == "delete" && $session['write']) {
                return $system->delete($sysid);
            }
        }
    }
    return array('content'=>EMPTY_ROUTE);
}
