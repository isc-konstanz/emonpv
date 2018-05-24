<?php

// no direct access
defined('EMONCMS_EXEC') or die('Restricted access');

function solar_controller() {
    global $session, $route, $mysqli, $redis;

    $result = false;

    require_once "Modules/solar/solar_model.php";
    $solar = new Solar($mysqli, $redis);

    if ($route->format == 'html') {
        if ($route->action == "view" && $session['write']) $result = view("Modules/solar/Views/solar_view.php", array());
        else if ($route->action == 'api') $result = view("Modules/solar/Views/solar_api.php", array());
    }
    else if ($route->format == 'json') {
        if ($route->action == 'list') {
            if ($session['userid']>0 && $session['write']) $result = $solar->get_list($session['userid']);
        }
    }

    return array('content'=>$result);
}
