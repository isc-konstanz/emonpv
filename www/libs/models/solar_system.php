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

class SolarSystem {

    public const DEFAULT_DIR = "/var/opt/pvforecast/";

    private $log;

    private $redis;
    private $mysqli;

    public $inverter;

    public function __construct($mysqli, $redis) {
        $this->log = new EmonLogger(__FILE__);
        $this->redis = $redis;
        $this->mysqli = $mysqli;
        
        $this->inverter = new SolarInverter($mysqli, $redis);
        
//         global $feed_settings;
//         require_once "Modules/feed/feed_model.php";
//         $this->feed = new Feed($mysqli, $redis, $feed_settings);
    }

    private function exist($id) {
        if ($this->redis) {
            if ($this->redis->exists("solar:system#$id")) {
                return true;
            }
            return false;
        }
        $result = $this->mysqli->query("SELECT id FROM solar_system WHERE id = '$id'");
        if ($result->num_rows>0) {
            //             if ($this->redis) {
            //                 $this->cache($system);
            //             }
            return true;
        }
        return false;
    }

    private function exists_name($userid, $name) {
        $userid = intval($userid);
        $id = -1;
        
        $stmt = $this->mysqli->prepare("SELECT id FROM solar_system WHERE userid=? AND name=?");
        $stmt->bind_param("is", $userid, $name);
        $stmt->execute();
        $stmt->bind_result($id);
        $result = $stmt->fetch();
        $stmt->close();
        
        if ($result && $id > 0) return $id; else return false;
    }

    public function create($userid, $model, $name, $description, $location) {
        $userid = intval($userid);
        $time = time();
        
        require_once("Modules/solar/libs/sim_model.php");
        if (!SimulationModel::is_valid($model)) {
            throw new SolarException("Invalid simulation model: ".$model);
        }
        if (preg_replace('/[^\p{N}\p{L}\-\_\.\s]/u', '', $name) != $name) {
            throw new SolarException("System name only contain a-z A-Z 0-9 - _ . and space or language specific characters");
        }
        else if ($this->exists_name($userid, $name)) {
            throw new SolarException("System name already exists: $name");
        }
        if (!isset($description)) {
            $description = '';
        }
        else if (preg_replace('/[^\p{N}\p{L}\-\_\.\s]/u', '', $description) != $description) {
            throw new SolarException("System description only contain a-z A-Z 0-9 - _ . and space or language specific characters");
        }
        
        if (empty($location)) {
            throw new SolarException("The systems location needs to be specified");
        }
        $location = json_decode(stripslashes($location), true);
        
        if (empty($location['latitude']) || empty($location['longitude']) ||
                !is_numeric($location['latitude']) || !is_numeric($location['longitude'])) {
                    
            throw new SolarException("The systems location specification is incomplete or invalid");
        }
        
        if (empty($location['altitude'])) {
            $location['altitude'] = null;
        }
        else if (!is_numeric($location['altitude'])) {
            throw new SolarException("The systems location specification is incomplete or invalid");
        }
        if (empty($location['albedo'])) {
            $location['albedo'] = null;
        }
        else if (!is_numeric($location['albedo'])) {
            throw new SolarException("The systems location specification is incomplete or invalid");
        }
        
        $stmt = $this->mysqli->prepare("INSERT INTO solar_system (userid,time_cr,model,name,description,latitude,longitude,altitude,albedo) VALUES (?,?,?,?,?,?,?,?,?)");
        $stmt->bind_param("iisssdddd",$userid,$time,$model,$name,$description,$location['latitude'],$location['longitude'],$location['altitude'],$location['albedo']);
        $stmt->execute();
        $stmt->close();
        
        $id = $this->mysqli->insert_id;
        if ($id < 1) {
            throw new SolarException("Unable to create system");
        }
        $system = array(
            'id' => $id,
            'userid' => $userid,
            'time_cr' =>  $time,
            'time_rn' => null,
            'forecast' => false,
            'model' => $model,
            'name' => $name,
            'description' => $description,
            'latitude' => $location['latitude'],
            'longitude' => $location['longitude'],
            'altitude' => $location['altitude'],
            'albedo' => $location['albedo']
        );
        if ($this->redis) {
            $this->add_redis($system);
        }
        $inverters = array($this->inverter->create($id));
        
        return $this->parse($system, $inverters);
    }

    public function get_list($userid) {
        if ($this->redis) {
            $systems = $this->get_list_redis($userid);
        } else {
            $systems = $this->get_list_mysql($userid);
        }
        usort($systems, function($s1, $s2) {
            if($s1['time']['run'] == null || $s2['time']['run'] == null || $s1['time']['run'] == $s2['time']['run']) {
                if($s1['time']['create'] == $s2['time']['create']) {
                    return strcmp($s1['name'], $s2['name']);
                }
                return $s2['time']['create'] - $s1['time']['create'];
            }
            return $s2['time']['run'] - $s1['time']['run'];
        });
        return $systems;
    }

    private function get_list_mysql($userid) {
        $userid = intval($userid);
        
        $systems = array();
        $result = $this->mysqli->query("SELECT * FROM solar_system WHERE userid='$userid' ORDER BY time_rn,time_cr,name asc");
        while ($system = $result->fetch_array()) {
            $systems[] = $this->parse($system);
        }
        return $systems;
    }

    private function get_list_redis($userid) {
        $userid = intval($userid);
        
        $systems = array();
        if ($this->redis->exists("solar:user#$userid:systems")) {
            foreach ($this->redis->sMembers("solar:user#$userid:systems") as $id) {
                $systems[] = $this->get_redis($id);
            }
        }
        else {
            $systems = $this->get_list_mysql($userid);
            foreach($systems as $system) {
                $this->add_redis($system);
            }
        }
        return $systems;
    }

    public function get($id) {
        $id = intval($id);
        if (!$this->exist($id)) {
            throw new SolarException("System for id $id does not exist");
        }
        if ($this->redis) {
            // Get from redis cache
            return $this->get_redis($id);
        }
        else {
            // Get from mysql db
            $result = $this->mysqli->query("SELECT * FROM solar_system WHERE id = '$id'");
            return $this->parse($result->fetch_array());
        }
    }

    private function get_redis($id) {
        return $this->parse((array) $this->redis->hGetAll("solar:system#$id"));
    }

    private function add_redis($system) {
        $this->redis->sAdd("solar:user#".$system['userid'].":systems", $system['id']);
        $this->redis->hMSet("solar:system#".$system['id'], $system);
    }

    private function parse($system, $inverters=null) {
        // TODO: fetch runtime and possible other meta data
        
        if ($inverters == null) {
            $inverters = $this->inverter->get_list($system['id']);
        }
        return $this->decode($system, $inverters);
    }

    private function decode($system, $inverters) {
        return array(
            'id' => $system['id'],
            'userid' => $system['userid'],
            'time' => array(
                'create' => $system['time_cr'],
                'run' => $system['time_rn']
            ),
            'forecast' => $system['forecast'],
            'model' => $system['model'],
            'name' => $system['name'],
            'description' => $system['description'],
            'location' => array(
                'latitude' => $system['latitude'],
                'longitude' => $system['longitude'],
                'altitude' => $system['altitude'],
                'albedo' => $system['albedo']
            ),
            'inverters' => $inverters
        );
    }

    public function delete($id) {
        $id = intval($id);
        if (!$this->exist($id)) {
            throw new SolarException("System for id $id does not exist");
        }
        foreach($this->inverter->get_list($id) as $inverter) {
            $this->inverter->delete($inverter['id']);
        }
        
        $this->mysqli->query("DELETE FROM solar_system WHERE `id` = '$id'");
        if ($this->redis) {
            $this->delete_redis($id);
        }
        return array('success'=>true, 'message'=>'System successfully deleted');
    }

    private function delete_redis($id) {
        $userid = $this->redis->hget("solar:system#$id",'userid');
        $this->redis->del("solar:system#$id");
        $this->redis->srem("solar:user#$userid:systems", $id);
    }

}
