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
                if ($route->action == "download") {
                    return $system->export_results($sys);
                }
            }
            if ($session['write']) {
                if ($route->action == "run") {
                    return $system->run($sys);
                }
                else if ($route->action == "update") {
                    return $system->update($sys, prop('fields'));
                }
                else if ($route->action == "delete") {
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
            else if ($route->subaction == "update") {
                return $system->inverter->update($inv, prop('fields'));
            }
            else if ($route->subaction == "delete") {
                return $system->inverter->delete($inv);
            }
            else if ($route->subaction == "configs") {
                if ($route->subaction2 == "create") {
                    $configs = $system->configs->create($session['userid'], prop('type'), prop('orientation'), 
                        prop('rows'), prop('mounting'), prop('tracking'));
                    
                    return $system->inverter->add_configs($id, prop('strid'), $configs);
                }
                else if ($route->subaction2 == "remove" ||
                        $route->subaction2 == "delete") {
                    
                    $result = $system->inverter->remove_configs($id, prop('cfgid'));
                    if (!$result) {
                        return array('success'=>false, 'message'=>'Unable to remove configuration for this inverter');
                    }
                    if ($route->subaction2 == "delete") {
                        return $system->configs->delete(prop('cfgid'));
                    }
                }
            }
        }
    }
    return array('content'=>EMPTY_ROUTE);
}

function configs_controller(SolarSystem $system, SolarConfigs $configs) {
    global $session, $route;
    
    $id = prop('id');
    if (!empty($id)) {
        $config = $configs->get($id);
        if ($config['userid'] != $session['userid']) {
            return array('success'=>false, 'message'=>'Invalid permissions to access these configurations');
        }
        if ($session['read']) {
            if ($route->subaction == "get") {
                return $config;
            }
            else if ($route->subaction == "download") {
                $sysid = get('sysid');
                if (!empty($sysid)) {
                    return $system->export_configs($sysid, $config);
                }
            }
        }
        if ($session['write']) {
            if ($route->subaction == "update") {
                return $configs->update($config, prop('fields'));
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
