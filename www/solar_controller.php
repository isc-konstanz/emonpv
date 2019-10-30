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
            if ($route->action == "modules") {
                return modules_controller($system);
            }
            if ($route->action == "inverter") {
                return inverter_controller($system);
            }
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
            $sys = $system->get($sysid);
            if ($sys['userid'] != $session['userid']) {
                return array('success'=>false, 'message'=>'Invalid permissions to access this system');
            }
            
            if ($route->action == "get") {
                return $sys;
            }
            else if ($route->action == "delete" && $session['write']) {
                return $system->delete($sysid);
            }
        }
    }
    return array('content'=>EMPTY_ROUTE);
}

function inverter_controller($system) {
    global $session, $route;
    
    $sysid = get('sysid');
    if (!empty($sysid)) {
        $sys = $system->get($sysid);
        if ($sys['userid'] != $session['userid']) {
            return array('success'=>false, 'message'=>'Invalid permissions to access this inverter');
        }
        
        if ($route->subaction == "create" && $session['write']) {
            return $system->inverter->create($sysid);
        }
        else if ($session['read']) {
            if ($route->subaction == "get") {
                return $system->inverter->get(get('id'));
            }
            else if ($route->subaction == "update") {
                return $system->inverter->update(get('id'), get('fields'));
            }
            else if ($route->subaction == "delete" && $session['write']) {
                return $system->inverter->delete(get('id'));
            }
        }
    }
    return array('content'=>EMPTY_ROUTE);
}

function modules_controller($system) {
    global $session, $route;
    
    $invid = get('invid');
    if (!empty($invid)) {
        $inv = $system->inverter->get($invid);
        $sys = $system->get($inv['sysid']);
        if ($sys['userid'] != $session['userid']) {
            return array('success'=>false, 'message'=>'Invalid permissions to access these modules');
        }
        
        if ($route->subaction == "create" && $session['write']) {
            return $system->inverter->modules->create($invid, get('azimuth'), get('tilt'), get('type'), get('settings'));
        }
        else if ($session['read']) {
            if ($route->subaction == "get") {
                return $system->inverter->modules->get(get('id'));
            }
            else if ($route->subaction == "update") {
                return $system->inverter->modules->update(get('id'), get('fields'));
            }
            else if ($route->subaction == "delete" && $session['write']) {
                return $system->inverter->modules->delete(get('id'));
            }
        }
    }
    return array('content'=>EMPTY_ROUTE);
}
