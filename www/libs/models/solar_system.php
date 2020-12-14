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
        $location_file = false;
        $location = json_decode(stripslashes($location), true);
        
        if (!empty($location['file'])) {
            $location_file = $this->get_meteo_file($location);
        }
        else {
            //TODO: configure location name from frontend
            $location['name'] = $name;
        }
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
        $system_dir = $this->create_system_dirs($system);
        
        if ($location_file) {
            $location_name = str_replace(' ', '_', $location['name']);
            move_uploaded_file($location_file["tmp_name"], "$system_dir/weather/$location_name.csv");
        }
        
        $inverters = (is_string($inverters) && !is_numeric($inverters) && $inverters === 'true') || boolval($inverters);
        if ($inverters) {
            $inverters = array();
            $inverters[] = $this->inverter->create($id);
        }
        return $this->parse($system, $location, $inverters);
    }

    private function create_system_dirs($system) {
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
        if (!file_exists($system_dir."/weather")) {
            mkdir($system_dir."/weather");
            chmod($system_dir."/weather", 0775);
        }
        return $system_dir;
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
                $order = $configs['order'];
                $configs_file = $system_dir."/conf/configs$order.cfg";
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
                
                $configs_dir = $system_dir."/conf/configs$order.d";
                if (!file_exists($configs_dir)) {
                    mkdir($configs_dir);
                }
                if (substr($configs['type'], 0, 6) !== 'custom') {
                    require_once("Modules/solar/libs/models/solar_module.php");
                    $module = new SolarModule($this->mysqli);
                    $module_json = $module->get($configs['type']);
                    $module_configs = $configs_dir."/module.cfg";
                    $this->delete_file($module_configs);
                    foreach ($module_json as $key=>$val) {
                        file_put_contents($module_configs, "$key = $val".PHP_EOL, FILE_APPEND);
                    }
                }
                
                $model_file = $configs_dir."/model.cfg";
                $this->delete_file($model_file);
                file_put_contents($model_file, "[Optical]".PHP_EOL, FILE_APPEND);
                file_put_contents($model_file, "    rows = $rows_count".PHP_EOL, FILE_APPEND);
                file_put_contents($model_file, "    row_modules = $rows_modules".PHP_EOL, FILE_APPEND);
                
                if (isset($row['pos_x'])) {
                    file_put_contents($model_file, "    pos_x = ".$row['pos_x'].PHP_EOL, FILE_APPEND);
                }
                if (isset($row['pos_y'])) {
                    file_put_contents($model_file, "    pos_y = ".$row['pos_y'].PHP_EOL, FILE_APPEND);
                }
                
                // Losses section
                $losses = $configs['losses'];
                if ($losses !== false) {
                    file_put_contents($model_file, PHP_EOL.
                            "[Losses]".PHP_EOL, FILE_APPEND);
                    
                    if (isset($losses['constant'])) {
                        file_put_contents($model_file, "    mu_c = ".$losses['constant'].PHP_EOL, FILE_APPEND);
                    }
                    if (isset($losses['wind'])) {
                        file_put_contents($model_file, "    mu_v = ".$losses['wind'].PHP_EOL, FILE_APPEND);
                    }
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
        $weather_file = str_replace('\\', '/', "weather/$weather_name");
        //$weather_file = str_replace('\\', '/', $this->get_user_dir($system['userid']))."/weather/$weather_name";
        
        if (file_exists("$system_dir/$weather_file.csv")) {
            $weather_configs = str_replace('type = EPW', 'type = TMY', $weather_configs);
        }
        $weather_configs = str_replace('file = weather.csv', "file = $weather_file.csv", $weather_configs);
        $weather_configs = str_replace('file = weather.epw', "file = $weather_file.epw", $weather_configs);
        
        file_put_contents($system_dir.'/conf/weather.cfg', $weather_configs);
    }

    public function add_configs($system, $inverter, $string, $configs) {
        $order = count($this->get_configs($system['id']))+1;
        
        $stmt = $this->mysqli->prepare("INSERT INTO solar_refs (`sysid`,`invid`,`strid`,`cfgid`,`order`) VALUES (?,?,?,?,?)");
        $stmt->bind_param("iiiii", $system['id'], $inverter['id'], $string, $configs['id'], $order);
        $stmt->execute();
        $stmt->close();
        
        if (substr($configs['type'], 0, 6) === 'custom') {
            require_once("Modules/solar/libs/models/solar_module.php");
            $module = new SolarModule($this->mysqli);
            $module->write_parameters($configs, $configs['module']);
        }
        return array_merge(array(
            'id'=>intval($configs['id']),
            'sysid'=>intval($system['id']),
            'invid'=>intval($inverter['id']),
            'strid'=>intval($string),
            'order'=>intval($order),
            'count'=>1
            
        ), array_slice($configs, 2));
    }

    public function remove_configs($system, $cfgid) {
        $system_name = str_replace(' ', '_', $system['name']);
        $system_dir = $this->get_system_dir($system);
        
        $results = $this->mysqli->query("SELECT `order` FROM solar_refs WHERE `sysid` = '".$system['id']."' AND `cfgid` = '".$cfgid."'");
        while ($result = $results->fetch_array()) {
            $order = $result['order'];
            $this->mysqli->query("DELETE FROM solar_refs WHERE `sysid` = '".$system['id']."' AND `cfgid` = '".$cfgid."'");
            $this->delete_file("$system_dir/results/results_$order.csv");
            $this->delete_file("$system_dir/results/results.csv");
            $this->delete_file("$system_dir/results.csv");
            $this->delete_file("$system_dir/results.csv");
            $this->delete_file("$system_dir/conf/configs$order.cfg");
            $this->delete_file("$system_dir/conf/configs$order.d");
            
            $this->reorder_configs($system);
            return true;
        }
        return false;
    }

    public function reorder_configs($system) {
        $configs = $this->get_configs($system['id']);
        if (count($configs) < 1) {
            return;
        }
        $count = 1;
        foreach ($configs as $cfg) {
            $order = $cfg['order'];
            if ($order != $count) {
                if ($stmt = $this->mysqli->prepare("UPDATE solar_refs SET `order` = ? WHERE `cfgid` = ?")) {
                    $stmt->bind_param("ii", $count, $cfg['id']);
                    if ($stmt->execute() === false) {
                        $stmt->close();
                        throw new SolarException("Error while updating configuration order of system$id");
                    }
                    $stmt->close();
                }
                $this->rename_configs($system, $order, $count);
            }
            $count += 1;
        }
    }

    private function rename_configs($system, $old, $new) {
        $system_name = str_replace(' ', '_', $system['name']);
        $system_dir = $this->get_system_dir($system);
        
        if (file_exists("$system_dir/conf/configs$old.cfg")) {
            rename("$system_dir/conf/configs$old.cfg", "$system_dir/conf/configs$new.cfg");
        }
        if (file_exists("$system_dir/conf/configs$old.d")) {
            rename("$system_dir/conf/configs$old.d", "$system_dir/conf/configs$new.d");
        }
        if (file_exists("$system_dir/results/$system_name"."_$old.csv")) {
            rename("$system_dir/results/$system_name"."_$old.csv",
                   "$system_dir/results/$system_name"."_$new.csv");
        }
    }

    public function get_configs($id) {
        $configs = array();
        
        $results = $this->mysqli->query("SELECT * FROM solar_refs WHERE `sysid` = '$id' ORDER BY `order` ASC");
        while ($result = $results->fetch_array()) {
            $cfgid = $result['cfgid'];
            $config = $this->configs->get($cfgid);
            $config = array_merge(array(
                'id'=>intval($cfgid),
                'sysid'=>intval($id),
                'order'=>intval($result['order']),
                'count'=>intval($result['count'])
                
            ), array_slice($config, 2));
            
            $configs[] = $config;
        }
        return $configs;
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

    private function get_meteo_file(&$location) {
        if (empty($_FILES['TMY3'])) {
            throw new SolarException("Location meteorological data file not submitted");
        }
        $location_file = $_FILES['TMY3'];
        if (pathinfo($location_file['name'], PATHINFO_EXTENSION) !== 'csv') {
            throw new SolarException("Location meteorological data file type invalid");
        }
        $tmy = fopen($location_file['tmp_name'], 'r');
        $tmy_header = explode(',', fgets($tmy)); fclose($tmy);
        
        if (count($tmy_header) < 7 || !is_string($tmy_header[1]) ||
            !is_numeric($tmy_header[4])|| !is_numeric($tmy_header[5])|| !is_numeric($tmy_header[6])) {
            
            throw new SolarException("Location meteorological data file format invalid");
        }
        $location['name'] = $tmy_header[1];
        $location['latitude'] = $tmy_header[4];
        $location['longitude'] = $tmy_header[5];
        $location['altitude'] = $tmy_header[6];
        
        return $location_file;
    }

    public function run($system) {
        $system_dir = $this->create_system_dirs($system);
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
        $this->delete_file("$system_dir/results");
        $this->delete_file("$system_dir/results.csv");
        
        if (!$this->redis) {
            file_put_contents($results_json, json_encode(array(
                'status'=>'error', 
                'message'=>'Unable to start simulation on this system', 
                'error'=>'Error'
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
        else {
            $results['status'] = 'created';
        }
        if ($results['status'] == 'success') {
            $files = array();
            foreach (glob("$results_dir/results/*.csv", GLOB_BRACE) as $file) {
                $files[] = basename($file);
            }
            $results['files'] = $files;
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
        
        return str_replace('\\', '/', $user_dir)."user$userid";
    }

    public function export($system) {
        $system_dir = $this->get_system_dir($system);
        $system_name = str_replace(' ', '_', $system['name']);
        $system_zip = "$system_dir/$system_name.zip";
        
        $this->delete_file($system_zip);
        
        $zip = new ZipArchive();
        if (!$zip->open($system_zip, ZIPARCHIVE::CREATE)) {
            throw new SolarException("Unable to create ZIP Archive");
        }
        $it = new RecursiveDirectoryIterator($system_dir, RecursiveDirectoryIterator::SKIP_DOTS);
        $files = new RecursiveIteratorIterator($it, RecursiveIteratorIterator::CHILD_FIRST);
        foreach ($files as $file) {
            $path = str_replace('\\', '/', $file->getRealPath());
            if ($file->isDir()) {
                $zip->addEmptyDir(str_replace($system_dir.'/', '', $path).'/');
            }
            else if (pathinfo($path, PATHINFO_EXTENSION) != 'zip') {
                $zip->addFromString(str_replace($system_dir.'/', '', $path), file_get_contents($path));
            }
        }
        $zip->close();
        
        $this->export_file($system_zip);
    }

    public static function export_file($file, $file_name=null) {
        if (!file_exists($file)) {
            throw new SolarException("Unable to find file: ".$file);
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
        $system_results = "$system_dir/results.xlsx";
        if (file_exists($system_results)) {
            $system_file = str_replace(' ', '_', $system['name']).".xlsx";
        }
        else {
            $system_results = "$system_dir/results.csv";
            $system_file = str_replace(' ', '_', $system['name']).".csv";
        }
        $this->export_file($system_results, $system_file);
    }

    public function export_config_results($system, $configs) {
        $results_name = '';
        $result = $this->mysqli->query("SELECT `order` FROM solar_refs WHERE `sysid` = '".$system['id']."' AND `cfgid` = '".$configs['id']."'");
        while ($r = $result->fetch_array()) {
            $results_name .= '_'.$r['order'];
        }
        $results_file = SolarSystem::get_system_dir($system)."/results/results$results_name.csv";
        
        SolarSystem::export_file($results_file, str_replace(' ', '_', $system['name'])."$results_name.csv");
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
        }
        $system['inverters'] = $inverters;
        
        if (!$inverters) {
            // TODO: Add system standalone configs
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
        if (isset($fields['albedo']) || isset($fields['latitude']) || isset($fields['longitude']) || isset($fields['altitude']) ||
                !empty($fields['file'])) {
            
            $system_dir = $this->get_system_dir($system);
            
            $location = $this->location->get($system['location']['id']);
            $location_name = str_replace(' ', '_', $location['name']);
            $location_path = "$system_dir/weather/$location_name";
            if (file_exists($location_path)) unlink("$location_path.csv");
            if (file_exists($location_path)) unlink("$location_path.epw");
            
            if (!empty($fields['file'])) {
                $location_file = $this->get_meteo_file($fields);
                move_uploaded_file($location_file["tmp_name"], "$location_path.csv");
            }
            $this->location->update($location, $fields);
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
        $this->delete_file($this->get_system_dir($system));
        
        return array('success'=>true, 'message'=>'System successfully deleted');
    }

    private function delete_file($path) {
        if (!file_exists($path)) {
            return;
        }
        if (is_file($path)) {
            unlink($path);
        }
        else if (is_dir($path)) {
            $it = new RecursiveDirectoryIterator($path, RecursiveDirectoryIterator::SKIP_DOTS);
            $files = new RecursiveIteratorIterator($it, RecursiveIteratorIterator::CHILD_FIRST);
            $empty = true;
            foreach($files as $file) {
                if ($file->isWritable()) {
                    if ($file->isDir()) {
                        // TODO: Remove this when permissions are fixed
                        if (iterator_count($it->getChildren()) === 0) {
                            rmdir($file->getRealPath());
                        }
                    }
                    else {
                        unlink($file->getRealPath());
                    }
                }
                else {
                    $empty = false;
                }
            }
            if ($empty) {
                rmdir($path);
            }
        }
    }

    private function delete_redis($id) {
        $userid = $this->redis->hget("solar:system#$id",'userid');
        $this->redis->del("solar:system#$id");
        $this->redis->srem("solar:user#$userid:systems", $id);
    }

}
