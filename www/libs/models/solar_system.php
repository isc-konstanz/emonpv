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

    const ROOT_DIR = "/opt/emonpv/";
    const LIBS_DIR = "/opt/emonpv/libs/";
    const DATA_DIR = "/var/opt/emonpv/";

    private $log;

    private $redis;
    private $mysqli;

    public $inverter;
    public $configs;

    public function __construct($mysqli, $redis, $configs) {
        $this->log = new EmonLogger(__FILE__);
        $this->redis = $redis;
        $this->mysqli = $mysqli;
        
        require_once("Modules/solar/libs/models/solar_location.php");
        $this->location = new SolarLocation($mysqli, $redis);
        $this->inverter = new SolarInverter($mysqli, $redis, $configs);
        $this->configs = $configs;
        
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
        $result = $this->mysqli->query("SELECT * FROM solar_system WHERE id = '$id'");
        if ($result->num_rows>0) {
            if ($this->redis) {
                while ($system = $result->fetch_array()) {
                    $this->add_redis($system);
                }
            }
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

    public function create($userid, $model, $name, $description, $location, $inverters) {
        $userid = intval($userid);
        $name = trim($name);
        
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
        else {
            $description = trim($description);
        }
        if (preg_replace('/[^\p{N}\p{L}\-\_\.\s]/u', '', $description) != $description) {
            throw new SolarException("System description only contain a-z A-Z 0-9 - _ . and space or language specific characters");
        }
        
        if (empty($location)) {
            throw new SolarException("The locations location needs to be specified");
        }
        $location = json_decode(stripslashes($location), true);
        
        //TODO: configure location name from frontend
        $location['name'] = $name;
        $location = $this->location->create($userid, $location);
        $locid = $location['id'];
        
        $stmt = $this->mysqli->prepare("INSERT INTO solar_system (userid,locid,name,description,model) VALUES (?,?,?,?,?)");
        $stmt->bind_param("iisss", $userid, $locid, $name, $description, $model);
        $stmt->execute();
        $stmt->close();
        
        $id = $this->mysqli->insert_id;
        if ($id < 1) {
            throw new SolarException("Unable to create system");
        }
        $system = array(
            'id' => $id,
            'userid' => $userid,
            'locid' => $locid,
            'model' => $model,
            'name' => $name,
            'description' => $description
        );
        if ($this->redis) {
            $this->add_redis($system);
        }
        
        $inverters = (is_string($inverters) && !is_numeric($inverters) && $inverters === 'true') || boolval($inverters);
        if ($inverters) {
            $inverters = array();
            $inverters[] = $this->inverter->create($id);
        }
        return $this->parse($system, $location, $inverters);
    }

    private function create_system_config($system, $system_dir) {
        $system_defaults = $this->get_config_dir()."/system.default.cfg";
        if (!file_exists($system_defaults)) {
            throw new SolarException("System default configs do not exist: ".$system_defaults);
        }
        $system_configs = file_get_contents($system_defaults);
        $system_configs = str_replace('name = <name>', 'name = '.$system['name'], $system_configs);
        
        $system_configs = str_replace('latitude = <lat>', 'latitude = '.$system['location']['latitude'], $system_configs);
        $system_configs = str_replace('longitude = <lon>', 'longitude = '.$system['location']['longitude'], $system_configs);
        if (!empty($system['location']['altitude'])) {
            $system_configs = str_replace(';altitude = <alt>', 'altitude = '.$system['location']['altitude'], $system_configs);
        }
        
        file_put_contents($system_dir.'/conf/system.cfg', $system_configs);
    }

    private function create_module_config($system, $system_dir) {
        $configs_defaults = $this->get_config_dir()."/configs.default.cfg";
        if (!file_exists($configs_defaults)) {
            throw new SolarException("Modules default configs do not exist: ".$configs_defaults);
        }
        foreach (glob("$system_dir/conf/configs*") as $configs_file) {
            if (is_dir($configs_file)) {
                foreach (glob("$configs_file/*") as $configs_override) {
                    if (is_file($configs_override)) {
                        unlink($configs_override);
                    }
                }
                rmdir($configs_file);
            }
            else if (is_file($configs_file)) {
                unlink($configs_file);
            }
        }
        
        foreach ($system['inverters'] as $inverter) {
            $configs_ids = array();
            $inverter_strings = array();
            foreach ($inverter['configs'] as $configs) {
                if (!array_key_exists($configs['strid'], $inverter_strings)) {
                    $inverter_strings[$configs['strid']] = array();
                }
                $inverter_strings[$configs['strid']][] = $configs['id'];
                $configs_ids[] = intval($configs['id']);
            }
            $configs_id_min = min($configs_ids);
            
            foreach ($inverter['configs'] as $configs) {
                $configs_id = $configs['id']; //- $configs_id_min + 1;
                $configs_file = $system_dir."/conf/configs$configs_id.cfg";
                $configs_configs = file_get_contents($configs_defaults);
                
                if (!empty($system['location']['albedo'])) {
                    $configs_configs = str_replace(';albedo = <albedo>', 'albedo = '.$system['location']['albedo'], $configs_configs);
                }
                
                // Inverter section
                $configs_configs = preg_replace('/'.preg_quote('count = <count>', '/').'/', 'count = '.$inverter['count'], $configs_configs, 1);
                $configs_configs = str_replace('strings = <count>', 'strings = '.count($inverter_strings), $configs_configs);
                
                
                // Modules section
                //$modules_configs = str_replace(';type = <type>', 'type = '.$configs['type'], $configs_configs);
                $configs_configs = str_replace(';orientation = <orientation>', 'orientation = '.$configs['orientation'], $configs_configs);
                
                $rows = $configs['rows'];
                $rows_count = $rows['count'];
                $rows_modules = $rows['modules'];
                
                $configs_count = $rows_count
                               * $rows_modules;
                if (!empty($rows['stack'])) {
                    $configs_count *= $rows['stack'];
                    
                    $configs_configs = str_replace(';stack = <count>', 'stack = '.$rows['stack'], $configs_configs);
                }
                $configs_configs = str_replace('pitch = <pitch>', 'pitch = '.$rows['pitch'], $configs_configs);
                $configs_configs = preg_replace('/'.preg_quote(';count = <count>', '/').'/', 'count = '.$configs_count, $configs_configs, 1);
                
                if (isset($rows['gap_x'])) {
                    $configs_configs = str_replace(';gap_x = <gap>', 'gap_x = '.$rows['gap_x'], $configs_configs);
                }
                if (isset($rows['gap_y'])) {
                    $configs_configs = str_replace(';gap_y = <gap>', 'gap_y = '.$rows['gap_y'], $configs_configs);
                }
                
                // Mounting section
                $mounting = $configs['mounting'];
                if ($mounting !== false) {
                    $configs_configs = str_replace(';tilt = <tilt>', 'tilt = '.$mounting['tilt'], $configs_configs);
                    $configs_configs = str_replace(';azimuth = <azimuth>', 'azimuth = '.$mounting['azimuth'], $configs_configs);
                    $configs_configs = str_replace(';elevation = <height>', 'elevation = '.$mounting['elevation'], $configs_configs);
                }
                
                // Tracking section
                $tracking = $configs['tracking'];
                if ($tracking !== false) {
                    $configs_configs = str_replace('enabled = <tracking>', 'enabled = true', $configs_configs);
                    
                    $configs_configs = str_replace(';backtrack = <backtrack>', 'backtrack = '.($tracking['backtrack'] ? 'true' : 'false'), $configs_configs);
                    $configs_configs = str_replace(';axis_height = <height>', 'axis_height = '.$tracking['axis_height'], $configs_configs);
                    $configs_configs = str_replace(';tilt_max = <tilt>', 'tilt_max = '.$tracking['tilt_max'], $configs_configs);
                }
                else {
                    $configs_configs = str_replace('enabled = <tracking>', 'enabled = false', $configs_configs);
                }
                
                file_put_contents($configs_file, $configs_configs);
                
                $configs_dir = $system_dir."/conf/configs$configs_id.d";
                if (!file_exists($configs_dir)) {
                    mkdir($configs_dir);
                }
                require_once("Modules/solar/libs/models/solar_module.php");
                $module = new SolarModule();
                $module_json = $module->get($configs['type']);
                $module_configs = "";
                foreach ($module_json as $key=>$val) {
                    file_put_contents($configs_dir."/module.cfg", "$key = $val".PHP_EOL, FILE_APPEND);
                }
                
                $model_file = $configs_dir."/model.cfg";
                file_put_contents($model_file, "[Optical]".PHP_EOL, FILE_APPEND);
                file_put_contents($model_file, "rows = $rows_count".PHP_EOL, FILE_APPEND);
                file_put_contents($model_file, "row_modules = $rows_modules".PHP_EOL, FILE_APPEND);
                
                if (isset($row['pos_x'])) {
                    file_put_contents($model_file, "pos_x = ".$row['pos_x'].PHP_EOL, FILE_APPEND);
                }
                if (isset($row['pos_y'])) {
                    file_put_contents($model_file, "pos_y = ".$row['pos_y'].PHP_EOL, FILE_APPEND);
                }
            }
        }
    }

    private function create_model_config($system, $system_dir) {
        $model_defaults = $this->get_config_dir()."/model.default.cfg";
        if (!file_exists($model_defaults)) {
            throw new SolarException("Model default configs do not exist: ".$model_defaults);
        }
        $model_configs = file_get_contents($model_defaults);
        $model_configs = str_replace('type = RayTracing', 'type = ViewFactor', $model_configs); // TODO: replace with $system['model']
        
        // FIXME: Remove this
        $model_configs = str_replace(';threading = True', 'threading = False', $model_configs);
        
        file_put_contents($system_dir.'/conf/model.cfg', $model_configs);
    }

    private function create_weather_config($system, $system_dir) {
        $weather_defaults = $this->get_config_dir()."/weather.default.cfg";
        if (!file_exists($weather_defaults)) {
            throw new SolarException("Weather default configs do not exist: ".$weather_defaults);
        }
        $weather_configs = file_get_contents($weather_defaults);
        $weather_configs = str_replace(';year = <year>', 'year = '.(date('Y')+1), $weather_configs);
        
        $weather_name = str_replace(' ', '_', $system['location']['name']);
        $weather_file = str_replace('\\', '/', $this->get_user_dir($system['userid']))."/weather/$weather_name";
        $weather_configs = str_replace('file = weather.epw', "file = $weather_file.epw", $weather_configs);
        $weather_configs = str_replace('file = weather.csv', "file = $weather_file.csv", $weather_configs);
        
        file_put_contents($system_dir.'/conf/weather.cfg', $weather_configs);
    }

    private function get_config_dir() {
        global $settings;
        if (!empty($settings['solar']['root_dir'])) {
            $config_dir = $settings['solar']['root_dir'];
        }
        else {
            $config_dir = SolarSystem::ROOT_DIR;
        }
        if (substr($config_dir, -1) !== "/") {
            $config_dir .= "/";
        }
        return $config_dir."conf";
    }

    public function run($system) {
        $user_dir = $this->get_user_dir($system['userid']);
        if (!file_exists($user_dir)) {
            mkdir($user_dir);
        }
        if (!file_exists($user_dir."/systems")) {
            mkdir($user_dir."/systems");
        }
        if (!file_exists($user_dir."/weather")) {
            mkdir($user_dir."/weather");
            chmod($user_dir."/weather", 0775);
        }
        
        $system_dir = $this->get_system_dir($system, $user_dir);
        if (!file_exists($system_dir)) {
            mkdir($system_dir);
            chmod($system_dir, 0775);
        }
        if (!file_exists($system_dir."/conf")) {
            mkdir($system_dir."/conf");
        }
        $results_json = "$system_dir/results.json";
        
        $this->create_system_config($system, $system_dir);
        $this->create_module_config($system, $system_dir);
        $this->create_model_config($system, $system_dir);
        $this->create_weather_config($system, $system_dir);
        
        global $settings;
        if (!empty($settings['solar']['python'])) {
            $python = $settings['solar']['python'];
        }
        else {
            $python = 'python';
        }
        if (!empty($settings['solar']['script'])) {
            $script = $settings['solar']['script'];
        }
        else {
            $script = 'emonpv';
        }
        if (!realpath($script)) {
            if (!empty($settings['solar']['root_dir'])) {
                $root_dir = $settings['solar']['root_dir'];
            }
            else {
                $root_dir = SolarSystem::ROOT_DIR;
            }
            if (substr($root_dir, -1) !== "/") {
                $root_dir .= "/";
            }
            $script = $root_dir."bin/".$script;
        }
        
        if (!$this->redis) {
            file_put_contents($results_json, json_encode(array(
                'status'=>'error', 
                'message'=>'Unable to start simulation on this system'
            )));
            throw new SolarException("Unable to start simulation on this system");
        }
        file_put_contents($results_json, json_encode(array(
            'status'=>'running',
            'progress'=>0
        )));
        chmod($results_json, 0664);
        
        $log = $settings['log']['location']."/emonpv.log";
        $this->redis->rpush("service-runner", "$python $script --data-directory=\"$system_dir\">$log");
        
        return array('success'=>true, 'message'=>'System simulation successfully started');
    }

    private function get_results($system) {
        $results = array();
        
        $results_dir = $this->get_system_dir($system);
        $results_json = "$results_dir/results.json";
        //$results_file = "$system_dir/results/".str_replace(' ', '_', $system['name']).".csv";
        
        //TODO: fetch run informations and check status
        if (file_exists($results_json)) {
            $results = json_decode(file_get_contents($results_json), true);
            
            if (json_last_error() != 0) {
                $results['status'] = 'error';
                $results['message'] = "Error reading $results_json: ".json_last_error_msg();
            }
            else if (isset($results['trace'])) {
                $trace = $results['trace'];
                $trace = str_replace("\n", "<br>", $trace);
                $trace = str_replace(" ", "&nbsp", $trace);
                
                $results['trace'] = $trace;
            }
        }
        else if (file_exists($results_dir)) {
            $results['status'] = 'running';
            $results['progress'] = 0;
        }
        else {
            $results['status'] = 'created';
        }
        return $results;
    }

    public static function get_system_dir($system, $user_dir=null) {
        if ($user_dir == null) {
            $user_dir = SolarSystem::get_user_dir($system['userid']);
        }
        return "$user_dir/systems/system".$system['id'];
    }

    public static function get_user_dir($userid) {
        global $settings;
        if (!empty($settings['solar']['data_dir'])) {
            $user_dir = $settings['solar']['data_dir'];
        }
        else {
            $user_dir = SolarSystem::DATA_DIR;
        }
        if (substr($user_dir, -1) !== "/") {
            $user_dir .= "/";
        }
        //TODO: Think about creating this dir with salted hash?
        
        return $user_dir."user$userid";
    }

    public static function export_file($file, $file_name=null) {
        if (!file_exists($file)) {
            throw new SolarException("Unable to find results CSV: ".$file);
        }
        if (empty($file_name)) {
            $file_name = basename($file);
        }
        
        header('Content-Description: File Transfer');
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="'.$file_name.'"');
        header('Content-Length: '.filesize($file));
        header('Expires: 0');
        
        // There is no need for the browser to cache the output
        header("Cache-Control: no-cache, no-store, must-revalidate");
        header("Pragma: no-cache");
        
        readfile($file);
        exit;
    }

    public function export_results($system) {
        $system_dir = $this->get_system_dir($system);
        $system_results = "$system_dir/results.csv";
        $system_name = str_replace(' ', '_', $system['name']).".csv";
        
        $this->export_file($system_results, $system_name);
    }

    public function export_configs($id, $configs) {
        $system = $this->get($id);
        $system_dir = SolarSystem::get_system_dir($system);
        
        $configs_count = 1;
        $configs_list = array();
        if ($system['inverters'] !== false) {
            foreach ($system['inverters'] as $inverter) {
                $configs_list = array_merge($inverter['configs'], $configs_list);
            }
        }
        else {
            $configs_list = $system['configs'];
        }
        foreach ($configs_list as $c) {
            if ($configs['id'] == $c['id']) {
                break;
            }
            $configs_count++;
        }
        $configs_results = "$system_dir/results/".str_replace(' ', '_', $system['name'])."_".$configs['id'].".csv";
        SolarSystem::export_file($configs_results, str_replace(' ', '_', $system['name'])."_$configs_count.csv");
    }

    public function get_list($userid) {
        if ($this->redis) {
            $systems = $this->get_list_redis($userid);
        } else {
            $systems = $this->get_list_mysql($userid);
        }
        usort($systems, function($s1, $s2) {
            return strcmp($s1['name'], $s2['name']);
        });
        return $systems;
    }

    private function get_list_mysql($userid) {
        $userid = intval($userid);
        
        $systems = array();
        $result = $this->mysqli->query("SELECT * FROM solar_system WHERE userid='$userid' ORDER BY name asc");
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
            $result = $this->mysqli->query("SELECT * FROM solar_system WHERE userid='$userid' ORDER BY name asc");
            while ($system = $result->fetch_array()) {
                $this->add_redis($system);
                $systems[] = $this->parse($system);
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

    private function parse($result, $location=null, $inverters=null) {
        $system = array(
            'id' => intval($result['id']),
            'userid' => intval($result['userid']),
            'model' => $result['model'],
            'name' => $result['name'],
            'description' => isset($result['description']) ? $result['description'] : ''
        );
        if ($location == null) {
            $location = $this->location->get($result['locid']);
        }
        $system['location'] = $location;
        
        if ($inverters == null) {
            $inverters = $this->inverter->get_list($result['id']);
            //foreach ($inverters as &$inverter) {
            //    unset($inverter['sysid']);
            //}
        }
        $system['inverters'] = $inverters;
        
        if (!$inverters) {
            // TODO: Add configs
        }
        $system['results'] = $this->get_results($result);
        
        return $system;
    }

    public function update($system, $fields) {
        $id = intval($system['id']);
        $fields = json_decode(stripslashes($fields), true);
        
        if (isset($fields['model'])) {
            $model = $fields['model'];
            
            require_once("Modules/solar/libs/sim_model.php");
            if (!SimulationModel::is_valid($model)) {
                throw new SolarException("Invalid simulation model: ".$model);
            }
            $this->update_field($id, 's', 'model', $model);
        }
        
        if (isset($fields['name'])) {
            $name = trim($fields['name']);
            
            if (preg_replace('/[^\p{N}\p{L}\-\_\.\s]/u', '', $name) != $name) {
                throw new SolarException("System name only contain a-z A-Z 0-9 - _ . and space or language specific characters");
            }
            else if ($this->exists_name($system['userid'], $name)) {
                throw new SolarException("System name already exists: $name");
            }
            $this->update_field($id, 's', 'name', $name);
        }
        if (isset($fields['description'])) {
            $description = trim($fields['description']);
            
            if (preg_replace('/[^\p{N}\p{L}\-\_\.\s]/u', '', $description) != $description) {
                throw new SolarException("System description only contain a-z A-Z 0-9 - _ . and space or language specific characters");
            }
            $this->update_field($id, 's', 'description', $description);
        }
        
        // TODO: Remove this when locations are managed on their own
        if (isset($fields['latitude']) || isset($fields['longitude']) || isset($fields['albedo']) ||
                array_key_exists('altitude', $fields)) {
            
            $this->location->update(
                $this->location->get($system['location']['id']), $fields);
        }
        return array('success'=>true, 'message'=>'System successfully updated');
    }

    private function update_field($id, $type, $field, $value) {
        if ($stmt = $this->mysqli->prepare("UPDATE solar_system SET $field = ? WHERE id = ?")) {
            $stmt->bind_param($type."i", $value, $id);
            if ($stmt->execute() === false) {
                $stmt->close();
                throw new SolarException("Error while update $field of system#$id");
            }
            $stmt->close();
            
            if ($this->redis) {
                $this->redis->hset("solar:system#$id", $field, $value);
            }
        }
        else {
            throw new SolarException("Error while setting up database update");
        }
    }

    public function delete($system) {
        foreach($this->inverter->get_list($system['id']) as $inverter) {
            $this->inverter->delete($inverter, true);
        }
        $this->location->delete($system['location']['id']);
        
        $this->mysqli->query("DELETE FROM solar_system WHERE `id` = '".$system['id']."'");
        if ($this->redis) {
            $this->delete_redis($system['id']);
        }
        return array('success'=>true, 'message'=>'System successfully deleted');
    }

    private function delete_redis($id) {
        $userid = $this->redis->hget("solar:system#$id",'userid');
        $this->redis->del("solar:system#$id");
        $this->redis->srem("solar:user#$userid:systems", $id);
    }

}
