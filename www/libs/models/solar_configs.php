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

define("CONFIGS_STRID_MAX",     20);
define("CONFIGS_PITCH_MAX",     100);
define("CONFIGS_ELEVATION_MAX", 100);
define("CONFIGS_ANGLE_MAX",     359.9);
define("CONFIGS_TILT_MAX",      90);

class SolarConfigs {

    private $log;

    private $redis;
    private $mysqli;

    public function __construct($mysqli, $redis) {
        $this->log = new EmonLogger(__FILE__);
        $this->redis = $redis;
        $this->mysqli = $mysqli;
    }

    private function exist($id) {
        $result = $this->mysqli->query("SELECT id FROM solar_configs WHERE id = '$id'");
        if ($result->num_rows>0) {
            return true;
        }
        return false;
    }

    public function create($userid, $type, $orientation, $rows, $mounting, $tracking) {
        $userid = intval($userid);
        
        if (!isset($orientation) || !Orientation::is_valid($orientation)) {
            throw new SolarException("The orientation specification is missing or invalid");
        }
        if (!is_numeric($orientation)) {
            $orientation = Orientation::get_code($orientation);
        }
        
        if (!empty($type)) {
            $type = preg_replace('/[^\/\|\,\w\s\-\:]/','', $type);
            // TODO: check if module exists
        }
        else {
            $type = null;
        }
        
        // TODO: Make row configs optional
        if (empty($rows)) {
            throw new SolarException("The rows configuration need to be specified");
        }
        $rows = json_decode(stripslashes($rows), true);
        
        if (!isset($rows['count']) || !is_numeric($rows['count']) ||
            !isset($rows['pitch']) || !is_numeric($rows['pitch'])||
            !isset($rows['modules']) || !is_numeric($rows['modules']) ||
            !isset($rows['stack']) || !is_numeric($rows['stack']) ||
            (isset($rows['gap_x']) && !is_numeric($rows['gap_x'])) ||
            (isset($rows['gap_y']) && !is_numeric($rows['gap_y'])) ||
            (isset($rows['pos_x']) && !is_numeric($rows['pos_x'])) ||
            (isset($rows['pos_y']) && !is_numeric($rows['pos_y']))) {
            
            throw new SolarException("The rows configuration is invalid");
        }
        else {
            // TODO: verify parameter boundaries
        }
        $rows['gap_x'] = isset($rows['gap_x']) ? $rows['gap_x'] : null;
        $rows['gap_y'] = isset($rows['gap_y']) ? $rows['gap_y'] : null;
        $rows['pos_x'] = isset($rows['pos_x']) ? $rows['pos_x'] : null;
        $rows['pos_y'] = isset($rows['pos_y']) ? $rows['pos_y'] : null;
        
        if (!empty($mounting)) {
            $mounting = json_decode(stripslashes($mounting), true);
        }
        else {
            $mounting = false;
        }
        if ($mounting !== false) {
            if (!isset($mounting['tilt']) || !is_numeric($mounting['tilt']) ||
                !isset($mounting['azimuth']) || !is_numeric($mounting['azimuth']) ||
                !isset($mounting['elevation']) || !is_numeric($mounting['elevation'])) {
                
                throw new SolarException("The mounting configuration is invalid");
            }
            else {
                // TODO: verify parameter boundaries
            }
        }
        
        if (!empty($tracking)) {
            $tracking = json_decode(stripslashes($tracking), true);
        }
        else {
            $tracking = false;
        }
        if ($tracking !== false) {
            if (!isset($tracking['axis_height']) || !is_numeric($tracking['axis_height']) ||
                !isset($tracking['tilt_max']) || !is_numeric($tracking['tilt_max']) ||
                !isset($tracking['backtrack'])) {
                
                throw new SolarException("The tracking configuration is invalid");
            }
            else {
                // TODO: verify parameter boundaries
            }
            $tracking['axis'] = 1;
        }
        
        $stmt = $this->mysqli->prepare("INSERT INTO solar_configs (userid,type,orientation) VALUES (?,?,?)");
        $stmt->bind_param("iss", $userid, $type, $orientation);
        $stmt->execute();
        $stmt->close();
        
        $id = $this->mysqli->insert_id;
        if ($id < 1) {
            throw new SolarException("Unable to create configs");
        }
        $configs = array(
            'id' => $id,
            'userid' => $userid,
            'type' => $type,
            'orientation' => $orientation
        );
        $rows = $this->create_rows($id, $rows['count'], $rows['pitch'], $rows['modules'], $rows['stack'], $rows['gap_x'], $rows['gap_y'], $rows['pos_x'], $rows['pos_y']);
        if ($mounting !== false) {
            $mounting = $this->create_mounting($id, $mounting['tilt'], $mounting['azimuth'], $mounting['elevation']);
        }
        if ($tracking !== false) {
            $tracking = $this->create_tracking($id, $tracking['axis'], $tracking['axis_height'], $tracking['tilt_max'], $tracking['backtrack']);
        }
        $configs = $this->decode($configs);
        $configs['rows'] = $rows;
        $configs['mounting'] = $mounting;
        $configs['tracking'] = $tracking;
        
        return $configs;
    }

    private function create_rows($id, $count, $pitch, $modules, $stack, $gap_x, $gap_y, $pos_x, $pos_y) {
        $stack = intval($stack);
        $count = intval($count);
        $modules = intval($modules);
        
        if (empty($pitch) || !is_numeric($pitch)) {
            throw new SolarException("The configs row pitch specification is missing or invalid");
        }
        $pitch = intval($pitch);
        
        $gap_x = is_numeric($gap_x) ? floatval($gap_x) : null;
        $gap_y = is_numeric($gap_y) ? floatval($gap_y) : null;
        $pos_x = is_numeric($pos_x) ? floatval($pos_x) : null;
        $pos_y = is_numeric($pos_y) ? floatval($pos_y) : null;
        
        $stmt = $this->mysqli->prepare("INSERT INTO solar_rows (id,count,pitch,modules,stack,gap_x,gap_y,pos_x,pos_y) VALUES (?,?,?,?,?,?,?,?,?)");
        try {
            $stmt->bind_param("iidiidddi", $id, $count, $pitch, $modules, $stack, $gap_x, $gap_y, $pos_x, $pos_y);
            if ($stmt->execute() === false) {
                throw new SolarException("Unable to create row configurations");
            }
        } finally {
            $stmt->close();
        }
        return array(
            "count" => $count,
            "pitch" => $pitch,
            "modules" => $modules,
            "stack" => $stack,
            "gap_x" => $gap_x,
            "gap_y" => $gap_y,
            "pos_x" => $pos_x,
            "pos_y" => $pos_y
        );
    }

    private function create_mounting($id, $tilt, $azimuth, $elevation) {
        $tilt = floatval($tilt);
        $azimuth = floatval($azimuth);
        $elevation = floatval($elevation);
        
        $stmt = $this->mysqli->prepare("INSERT INTO solar_mounting (id,tilt,azimuth,elevation) VALUES (?,?,?,?)");
        try {
            $stmt->bind_param("iddd", $id, $tilt, $azimuth, $elevation);
            if ($stmt->execute() === false) {
                throw new SolarException("Unable to create mounting configurations");
            }
        } finally {
            $stmt->close();
        }
        return array(
            "tilt" => $tilt,
            "azimuth" => $azimuth,
            "elevation" => $elevation
        );
    }

    private function create_tracking($id, $axis, $axis_height, $tilt_max, $backtrack) {
        $axis = intval($axis);
        $axis_height = floatval($axis_height);
        $tilt_max = floatval($tilt_max);
        $backtrack = (is_string($backtrack) && !is_numeric($backtrack) && $backtrack === 'true') || boolval($backtrack);
        
        $stmt = $this->mysqli->prepare("INSERT INTO solar_tracking (id,axis,axis_height,tilt_max,backtrack) VALUES (?,?,?,?,?)");
        try {
            $stmt->bind_param("iiddi", $id, $axis, $axis_height, $tilt_max, $backtrack);
            if ($stmt->execute() === false) {
                throw new SolarException("Unable to create tracking configurations");
            }
        } finally {
            $stmt->close();
        }
        return array(
            "axis" => $axis,
            "axis_height" => $axis_height,
            "tilt_max" => $tilt_max,
            "backtrack" => $backtrack
        );
    }

    public function get($id) {
        $id = intval($id);
        if (!$this->exist($id)) {
            throw new SolarException("Configuratiuons for id $id do not exist");
        }
        $result = $this->mysqli->query("SELECT * FROM solar_configs WHERE id = '$id'");
        $configs = $result->fetch_array();
        
        return $this->parse($configs);
    }

    private function get_rows($id) {
        $result = $this->mysqli->query("SELECT * FROM solar_rows WHERE id = '$id'");
        $rows = $result->fetch_array();
        
        return array(
            "count" => intval($rows['count']),
            "pitch" => floatval($rows['pitch']),
            "modules" => intval($rows['modules']),
            "stack" => intval($rows['stack']),
            "gap_x" => isset($rows['gap_x']) ? floatval($rows['gap_x']) : null,
            "gap_y" => isset($rows['gap_y']) ? floatval($rows['gap_y']) : null,
            "pos_x" => isset($rows['pos_x']) ? floatval($rows['pos_x']) : null,
            "pos_y" => isset($rows['pos_y']) ? floatval($rows['pos_y']) : null
        );
    }

    private function get_mounting($id) {
        $result = $this->mysqli->query("SELECT * FROM solar_mounting WHERE id = '$id'");
        if ($result->num_rows < 1) {
            return false;
        }
        $mounting = $result->fetch_array();
        
        return array(
            "tilt" => floatval($mounting['tilt']),
            "azimuth" => floatval($mounting['azimuth']),
            "elevation" => floatval($mounting['elevation'])
        );
    }

    private function get_tracking($id) {
        $result = $this->mysqli->query("SELECT * FROM solar_tracking WHERE id = '$id'");
        if ($result->num_rows < 1) {
            return false;
        }
        $tracking = $result->fetch_array();
        
        return array(
            "axis" => intval($tracking['axis']),
            "axis_height" => floatval($tracking['axis_height']),
            "tilt_max" => floatval($tracking['tilt_max']),
            "backtrack" => boolval($tracking['backtrack'])
        );
    }

    private function parse($result) {
        $configs = $this->decode($result);
        $configs['rows'] = $this->get_rows($configs['id']);
        $configs['mounting'] = $this->get_mounting($configs['id']);
        $configs['tracking'] = $this->get_tracking($configs['id']);
        
        return $configs;
    }

    private function decode($configs) {
        return array(
            'id' => intval($configs['id']),
            'userid' => intval($configs['userid']),
            'type' => strval($configs['type']),
            'orientation' => Orientation::get_str($configs['orientation'])
        );
    }

    public function update($configs, $fields) {
        $fields = json_decode(stripslashes($fields), true);
        
        //$this->update_integer($configs['id'], 'configs', $fields, 'strid', 1, CONFIGS_STRID_MAX);
        
        $this->update_string($configs['id'], 'configs', $fields, 'type');
        
        $this->update_orientation($configs['id'], $fields);
        
        $this->update_rows($configs, $fields);
        $this->update_mounting($configs, $fields);
        $this->update_tracking($configs, $fields);
        
        return $this->get($configs['id']);
    }

    private function update_rows($configs, $fields) {
        if (!isset($fields['rows'])) {
            return;
        }
        $rows = $fields['rows'];
        
        $this->update_integer($configs['id'], 'rows', $rows, 'count', 1, PHP_INT_MAX);
        $this->update_double($configs['id'], 'rows', $rows, 'pitch', 0, CONFIGS_PITCH_MAX);
        $this->update_integer($configs['id'], 'rows', $rows, 'modules', 1, PHP_INT_MAX);
        $this->update_integer($configs['id'], 'rows', $rows, 'stack', 1, PHP_INT_MAX);
        $this->update_double($configs['id'], 'rows', $rows, 'gap_x', 0, PHP_INT_MAX);
        $this->update_double($configs['id'], 'rows', $rows, 'gap_y', 0, PHP_INT_MAX);
        $this->update_double($configs['id'], 'rows', $rows, 'pos_x', 0, PHP_INT_MAX);
        $this->update_double($configs['id'], 'rows', $rows, 'pos_y', 0, PHP_INT_MAX);
    }

    private function update_mounting($configs, $fields) {
        if (!isset($fields['mounting'])) {
            return;
        }
        $mounting = $fields['mounting'];
        
        if (!$configs['mounting']) {
            if (!isset($mounting['tilt']) || !is_numeric($mounting['tilt']) ||
                !isset($mounting['azimuth']) || !is_numeric($mounting['azimuth']) ||
                !isset($mounting['elevation']) || !is_numeric($mounting['elevation'])) {
                
                throw new SolarException("The mounting configuration is invalid");
            }
            $this->mysqli->query("DELETE FROM solar_tracking WHERE `id` = '".$configs['id']."'");
            
            $this->create_mounting($configs['id'], $mounting['tilt'], $mounting['azimuth'], $mounting['elevation']);
        }
        else {
            $this->update_double($configs['id'], 'mounting', $mounting, 'tilt', 0, CONFIGS_TILT_MAX);
            $this->update_double($configs['id'], 'mounting', $mounting, 'azimuth', 0, CONFIGS_ANGLE_MAX);
            $this->update_double($configs['id'], 'mounting', $mounting, 'elevation', 0, CONFIGS_ELEVATION_MAX);
        }
    }

    private function update_tracking($configs, $fields) {
        if (!isset($fields['tracking'])) {
            return;
        }
        $tracking = $fields['tracking'];
        
        if (!$configs['tracking']) {
            if (!isset($tracking['axis_height']) || !is_numeric($tracking['axis_height']) ||
                !isset($tracking['tilt_max']) || !is_numeric($tracking['tilt_max']) ||
                !isset($tracking['backtrack'])) {
                
                throw new SolarException("The tracking configuration is invalid");
            }
            $tracking['axis'] = 1;
            
            $this->mysqli->query("DELETE FROM solar_mounting WHERE `id` = '".$configs['id']."'");
            
            $this->create_tracking($configs['id'], $tracking['axis'], $tracking['axis_height'], $tracking['tilt_max'], $tracking['backtrack']);
        }
        else {
            $this->update_double($configs['id'], 'tracking', $tracking, 'axis_height', 0, CONFIGS_ELEVATION_MAX);
            $this->update_double($configs['id'], 'tracking', $tracking, 'tilt_max', 0, CONFIGS_ANGLE_MAX);
            $this->update_boolean($configs['id'], 'tracking', $tracking, 'backtrack');
        }
    }

    private function update_boolean($id, $database, $fields, $field) {
        if (!isset($fields[$field])) {
            return;
        }
        $this->update_database($id, $database, $field, $fields[$field] ? true : false, 'i');
    }

    private function update_integer($id, $database, $fields, $field, $min, $max) {
        $this->update_number($id, $database, $fields, $field, $min, $max, 'i');
    }

    private function update_double($id, $database, $fields, $field, $min, $max) {
        $this->update_number($id, $database, $fields, $field, $min, $max, 'd');
    }

    private function update_number($id, $database, $fields, $field, $min, $max, $type) {
        if (!isset($fields[$field])) {
            return;
        }
        $value = $fields[$field];
        if ($value == 'null') {
            $value = null;
        }
        else if (!is_numeric($value) || $value < $min || $value > $max) {
            throw new SolarException("The configs $field is invalid: $value");
        }
        $this->update_database($id, $database, $field, $value, $type);
    }

    private function update_string($id, $database, $fields, $field, $json=false) {
        if (!isset($fields[$field])) {
            return;
        }
        $value = $fields[$field];
        if ($json) {
            $value = json_encode($value);
        }
        $this->update_database($id, $database, $field, $value, 's');
    }

    private function update_orientation($id, $fields) {
        if (!isset($fields['orientation'])) {
            return;
        }
        $value = Orientation::get_code($fields['orientation']);
        $this->update_database($id, 'configs', 'orientation', $value, 'i');
    }

    private function update_database($id, $database, $field, $value, $type) {
        if ($stmt = $this->mysqli->prepare("UPDATE solar_$database SET $field = ? WHERE id = ?")) {
            $stmt->bind_param($type."i", $value, $id);
            if ($stmt->execute() === false) {
                $stmt->close();
                throw new SolarException("Error while update $field of configs#$id");
            }
            $stmt->close();
        }
        else {
            throw new SolarException("Error while setting up database update");
        }
    }

    public function delete($id) {
        $this->mysqli->query("DELETE FROM solar_configs WHERE `id` = '$id'");
        
        $this->mysqli->query("DELETE FROM solar_rows WHERE `id` = '$id'");
        $this->mysqli->query("DELETE FROM solar_mounting WHERE `id` = '$id'");
        $this->mysqli->query("DELETE FROM solar_tracking WHERE `id` = '$id'");
        
        return array('success'=>true, 'message'=>'Configurations successfully deleted');
    }

}

abstract class Orientation {
    const PORTRAIT = 0;
    const LANDSCAPE = 1;

    static public function get_str($code) {
        switch ($code) {
        case null:
        case Orientation::PORTRAIT:
            return 'portrait';
        case Orientation::LANDSCAPE:
            return 'landscape';
        default:
            throw new SolarException("Invalid orientation code: $code");
        }
    }

    static public function get_code($str) {
        switch (strtoupper($str)) {
            case 'PORTRAIT':
                return Orientation::PORTRAIT;
            case 'LANDSCAPE':
                return Orientation::LANDSCAPE;
            default:
                throw new SolarException("Invalid orientation: $str");
        }
    }

    static public function get_all () {
        return array(
            Orientation::PORTRAIT,
            Orientation::LANDSCAPE
        );
    }

    static public function is_valid($orientation) {
        $code = is_numeric($orientation) ? $orientation : Orientation::get_code($orientation);
        return in_array($code, Orientation::get_all());
    }
}
