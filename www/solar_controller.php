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
    
    require_once("Modules/solar/libs/models/solar_configs.php");
    require_once("Modules/solar/libs/models/solar_inverter.php");
    require_once("Modules/solar/libs/models/solar_system.php");
    $configs = new SolarConfigs($mysqli, $redis);
    $system = new SolarSystem($mysqli, $redis, $configs);
    
    if ($route->format == 'html') {
        if (!$session['read']) {
            // Empty string result forces the user back to login
            return '';
        }
        else if ($route->action == "view" && $session['write']) {
            require_once("Modules/solar/libs/models/solar_module.php");
            $module = new SolarModule();
            $modules = $module->get_list_meta();
            
            return view("Modules/solar/views/solar_view.php", array('modules'=>$modules));
        }
        else if ($route->action == 'api' && $session['write']) {
            return view("Modules/solar/views/solar_api.php", array());
        }
    }
    else if ($route->format == 'json' && $session['userid'] > 0) {
        try {
            if ($route->action == "module") {
                return module_controller();
            }
            if ($route->action == "configs") {
                return configs_controller($system, $configs);
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

function system_controller(SolarSystem $system) {
    global $session, $route;
    
    if ($route->action == "create" && $session['write']) {
        return $system->create($session['userid'], prop('model'), prop('name'), prop('description'), prop('location'), prop('inverters'));
    }
    else if ($route->action == 'list' && $session['read']) {
        return $system->get_list($session['userid']);
    }
    else {
        $id = prop('id');
        if (!empty($id)) {
            $sys = $system->get($id);
            if ($sys['userid'] != $session['userid']) {
                return array('success'=>false, 'message'=>'Invalid permissions to access this system');
            }
            if ($session['read']) {
                if ($route->action == "get") {
                    return $sys;
                }
                if ($route->action == "export") {
                    return $system->export($sys);
                }
                if ($route->action == "download") {
                    return $system->export_results($sys);
                }
            }
            if ($session['write']) {
                if ($route->action == "run") {
                    return $system->run($sys);
                }
                if ($route->action == "update") {
                    return $system->update($sys, prop('fields'));
                }
                if ($route->action == "delete") {
                    return $system->delete($sys);
                }
            }
        }
    }
    return array('content'=>EMPTY_ROUTE);
}

function inverter_controller(SolarSystem $system) {
    global $session, $route;
    
    $id = prop('id');
    if (!empty($id)) {
        $inv = $system->inverter->get($id);
        $sys = $system->get($inv['sysid']);
        if ($sys['userid'] != $session['userid']) {
            return array('success'=>false, 'message'=>'Invalid permissions to access this inverter');
        }
        if ($session['read']) {
            if ($route->subaction == "get") {
                return $inv;
            }
        }
        if ($session['write']) {
            if ($route->subaction == "create") {
                return $system->inverter->create($sys['id']);
            }
            if ($route->subaction == "update") {
                return $system->inverter->update($inv, prop('fields'));
            }
            if ($route->subaction == "delete") {
                return $system->inverter->delete($inv);
            }
        }
    }
    return array('content'=>EMPTY_ROUTE);
}

function configs_controller(SolarSystem $system, SolarConfigs $configs) {
    global $session, $route;
    
    $sysid = prop('sysid');
    if (!empty($sysid)) {
        $sys = $system->get($sysid);
        if ($sys['userid'] != $session['userid']) {
            return array('success'=>false, 'message'=>'Invalid permissions to access this system');
        }
        
        if ($route->subaction == "create" && $session['write']) {
            $invid = prop('invid');
            if (!empty($invid)) {
                $inv = $system->inverter->get($invid);
                if ($inv['sysid'] != $sysid) {
                    return array('success'=>false, 'message'=>'Unable to add configuration for this inverter');
                }
                $cfg = $configs->create($session['userid'], prop('type'), prop('orientation'),
                    prop('rows'), prop('mounting'), prop('tracking'));
                
                return $system->add_configs($sys, $inv, prop('strid'), $cfg);
            }
        }
    }
    
    $id = prop('id');
    if (!empty($id)) {
        $cfg = $configs->get($id);
        if ($cfg['userid'] != $session['userid']) {
            return array('success'=>false, 'message'=>'Invalid permissions to access these configurations');
        }
        if ($session['read']) {
            if ($route->subaction == "get") {
                return $cfg;
            }
            if (!empty($sysid)) {
                if ($route->subaction == "download") {
                    return $system->export_config_results($sys, $cfg);
                }
            }
        }
        if ($session['write']) {
            if ($route->subaction == "update") {
                return $configs->update($cfg, prop('fields'));
            }
            if (!empty($sysid)) {
                if ($route->subaction == "remove" ||
                    $route->subaction == "delete") {
                    
                    $result = $system->remove_configs($sys, $id);
                    if (!$result) {
                        return array('success'=>false, 'message'=>'Unable to remove configuration for this system');
                    }
                    if ($route->subaction == "delete") {
                        return $system->configs->delete($id);
                    }
                }
            }
        }
    }
    return array('content'=>EMPTY_ROUTE);
}

function module_controller() {
    global $session, $route;
    
    require_once("Modules/solar/libs/models/solar_module.php");
    $module = new SolarModule();
    
    if ($session['read']) {
        if ($route->subaction == 'list') {
            return $module->get_list_meta();
        }
        else if ($route->subaction == 'get') {
            return $module->get('type');
        }
    }
    return array('content'=>EMPTY_ROUTE);
}
