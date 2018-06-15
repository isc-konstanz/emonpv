<?php

// no direct access
defined('EMONCMS_EXEC') or die('Restricted access');

function solar_controller() {
    global $mysqli, $redis, $session, $route, $feed_settings;

    $result = false;

    require_once "Modules/feed/feed_model.php";
    $feed = new Feed($mysqli, $redis, $feed_settings);

    require_once "Modules/solar/solar_model.php";
    $solar = new Solar($mysqli, $redis, $feed);

    if ($route->format == 'html') {
        if ($route->action == "view" && $session['write']) $result = view("Modules/solar/Views/solar_view.php", array());
        else if ($route->action == 'api') $result = view("Modules/solar/Views/solar_api.php", array());
    }
    else if ($route->format == 'json') {
        if ($route->action == "create") {
            if ($session['userid']>0 && $session['write']) $result = $solar->create($session['userid'],prop("name"),prop("description"),prop("location"),prop("modules"));
        }
        else if ($route->action == 'list') {
            if ($session['userid']>0 && $session['write']) $result = $solar->get_list($session['userid']);
        }
        else if ($route->action == 'config') {
            if ($session['admin']) $result = $solar->get_config();
        }
        else if ($route->action == 'forecast') {
            if ($session['userid']>0) $result = $solar->get_data($session['userid'], prop('system'));
        }
        else if (prop('id') !== null) {
            $systemid = intval(prop('id'));
            if ($solar->exist($systemid)) {
                if ($route->action == "init") $result = $solar->init($session['userid'],$systemid,prop('template'));
                else if ($route->action == "prepare") $result = $solar->prepare($session['userid'],$systemid);
                else if ($route->action == "get") $result = $solar->get($systemid);
                else if ($route->action == 'set') $result = $solar->set_fields($systemid,prop('fields'));
                else if ($route->action == "delete") $result = $solar->delete($systemid);
            }
            else {
                $result = array('success'=>false, 'message'=>'System does not exist');
            }
        }
        else if ($route->action == 'module' && $session['userid']>0 && $session['write']) {
            if ($route->subaction == 'meta') $result = $solar->get_module_meta();
            else if ($route->subaction == 'list') $result = $solar->get_module_list();
            else if ($route->subaction == 'get') $result = $solar->get_module(get('type'));
        }
    }

    return array('content'=>$result);
}
