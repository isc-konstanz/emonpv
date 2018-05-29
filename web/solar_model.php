<?php
/*
 Released under the GNU Affero General Public License.
 See COPYRIGHT.txt and LICENSE.txt.
 
 Device module contributed by Nuno Chaveiro nchaveiro(at)gmail.com 2015
 ---------------------------------------------------------------------
 Sponsored by http://archimetrics.co.uk/
 */

// no direct access
defined('EMONCMS_EXEC') or die('Restricted access');

class Solar {
    
    const DEFAULT_DIR = "/opt/pvforecast/";
    const DEFAULT_NODE = "pvforecast";
    const DEFAULT_TAG = "forecast";

    public $mysqli;
    public $redis;
    private $log;

    public function __construct($mysqli, $redis) {
        $this->mysqli = $mysqli;
        $this->redis = $redis;
        $this->log = new EmonLogger(__FILE__);
    }

    public function create($userid, $name, $description, $location, $modules) {
        $userid = intval($userid);
        $name = preg_replace('/[^\p{L}_\p{N}\s-:]/u', '', $name);
        
        if (isset($description)) {
            $description = preg_replace('/[^\p{L}_\p{N}\s-:]/u', '', $description);
        }
        else {
            $description = '';
        }
        
        if (!isset($location)) {
            return array('success'=>false, 'message'=>"The systems location needs to be specified");
        }
        $location = (array) json_decode(stripslashes($location));
        
        if (!isset($location['longitude']) || !isset($location['latitude']) || !isset($location['altitude'])) {
            return array('success'=>false, 'message'=>"The systems location specification is incomplete");
        }
        
        if (isset($modules)) {
            $modules = (array) json_decode(stripslashes($modules));
        }
        else {
            $modules = array();
        }
        
        if (!$this->exists_name($userid, $name)) {
            $stmt = $this->mysqli->prepare("INSERT INTO solar_system (userid,name,description,longitude,latitude,altitude) VALUES (?,?,?,?,?,?)");
            $stmt->bind_param("issddd",$userid,$name,$description,$location['longitude'],$location['latitude'],$location['altitude']);
            $result = $stmt->execute();
            $stmt->close();
            if (!$result) return array('success'=>false, 'message'=>_("Error creating system"));
            
            $systemid = $this->mysqli->insert_id;
            if ($systemid > 0) {
                foreach ($modules as $module) {
                    $this->create_module($userid, $systemid, (array) $module);
                }
//                 if ($this->redis) {
//                     $this->load_list_to_redis($userid);
//                 }
                return array('success'=>true, 'id'=>$systemid, 'message'=>"System successfully created");;
            }
            return array('success'=>false, 'message'=>"SQL returned invalid system id insertion");
        }
        return array('success'=>false, 'message'=>'System with that name already exists');
    }

    private function create_module($userid, $systemid, $module) {
        $stmt = $this->mysqli->prepare("INSERT INTO solar_modules (systemid,inverter,type,tilt,azimuth,albedo,strings,modules) VALUES (?,?,?,?,?,?,?,?)");
        $stmt->bind_param("issdddii",$systemid,$module['inverter'],$module['type'],$module['tilt'],$module['azimuth'],$module['albedo'],$module['strings'],$module['modules']);
        
        $result = $stmt->execute();
        $stmt->close();
        if (!$result) return array('success'=>false, 'message'=>_("Error creating module"));
        
        $moduleid = $this->mysqli->insert_id;
        if ($moduleid > 0) {
            return array('success'=>true, 'id'=>$moduleid, 'message'=>"Module successfully created");;
        }
        return array('success'=>false, 'message'=>"SQL returned invalid module id insertion");
    }

    public function init($userid, $id, $template) {
        $userid = intval($userid);
        $id = intval($id);
        
        if (isset($template)) {
            $template = (array) json_decode(stripslashes($template));
        }
        else {
            $result = $this->prepare($userid, $id);
            if (isset($result["success"]) && !$result["success"]) {
                return $result;
            }
            $template = $result;
        }
        
        if (isset($template['feeds'])) {
            $feeds = $template['feeds'];
            $this->create_feeds($userid, $feeds);
        }
        else {
            $feeds = [];
        }
        
        if (isset($template['inputs'])) {
            $inputs = $template['inputs'];
            $this->create_inputs($userid, $inputs);
            $this->create_input_processes($userid, $feeds, $inputs);
        }
        else {
            $inputs = [];
        }
        
        return array('success'=>true, 'message'=>'System initialized');
    }

    private function create_feeds($userid, &$feeds) {
        global $feed_settings;
        
        require_once "Modules/feed/feed_model.php";
        $feed = new Feed($this->mysqli, $this->redis, $feed_settings);
        
        for ($i = 0; $i < count($feeds); $i++) {
            if (!is_array($feeds[$i])) {
                $feeds[$i] = (array) $feeds[$i];
            }
            
            if ($feeds[$i]['action'] === 'create') {
                $options = array();
                if (isset($fd['interval'])) {
                    $options['interval'] = $feeds[$i]['interval'];
                }
                
                $result = $feed->create($userid, $feeds[$i]['tag'], $feeds[$i]['name'], intval($feeds[$i]['type']), intval($feeds[$i]['engine']), $options);
                if($result["success"] === true) {
                    // Assign the created input id to the inputs array
                    $feeds[$i]['id'] = $result["feedid"];
                }
            }
        }
    }

    private function create_inputs($userid, &$inputs) {
        require_once "Modules/input/input_model.php";
        $input = new Input($this->mysqli, $this->redis, null);
        
        for ($i = 0; $i < count($inputs); $i++) {
            if (!is_array($inputs[$i])) {
                $inputs[$i] = (array) $inputs[$i];
            }
            
            if ($inputs[$i]['action'] === 'create') {
                $inputid = $input->create_input($userid, $inputs[$i]['node'], $inputs[$i]['name']);
                if($input->exists($inputid)) {
                    $input->set_fields($inputid, '{"description":"'.$inputs[$i]['description'].'"}');
                    
                    // Assign the created input id to the inputs array
                    $inputs[$i]['id'] = $inputid;
                }
            }
        }
    }

    private function create_input_processes($userid, $feeds, $inputs) {
        global $user, $feed_settings;
        
        require_once "Modules/feed/feed_model.php";
        $feed = new Feed($this->mysqli, $this->redis, $feed_settings);
        
        require_once "Modules/input/input_model.php";
        $input = new Input($this->mysqli, $this->redis, $feed);
        
        require_once "Modules/process/process_model.php";
        $process = new Process($this->mysqli, $input, $feed, $user->get_timezone($userid));
        $process_list = $process->get_process_list(); // emoncms supported processes
        
        for ($i = 0; $i < count($inputs); $i++) {
            if ($inputs[$i]['action'] !== 'none') {
                if (isset($inputs[$i]['id']) && isset($inputs[$i]['processList'])) {
                    $processes = array();
                    foreach($inputs[$i]['processList'] as $process) {
                        $processes[] = $this->parse_process($feeds, $inputs, (array) $process);
                    }
                    if (count($processes) > 0) {
                        $input->set_processlist($userid, $inputs[$i]['id'], implode(",", $processes), $process_list);
                    }
                }
            }
        }
    }

    private function parse_process($feeds, $inputs, $process) {
        $arguments = (array) $process['arguments'];
        if (isset($arguments['value'])) {
            $value = $arguments['value'];
        }
        else if ($arguments['type'] === ProcessArg::NONE) {
            $value = 0;
        }
        
        if ($arguments['type'] === ProcessArg::VALUE) {
        }
        else if ($arguments['type'] === ProcessArg::INPUTID) {
            foreach ($inputs as $input) {
                if ($input['name'] == $value) {
                    if (isset($input['id']) && $input['id'] > 0) {
                        $value = $input['id'];
                    }
                }
            }
        }
        else if ($arguments['type'] === ProcessArg::FEEDID) {
            foreach ($feeds as $feed) {
                if ($feed['name'] == $value) {
                    if (isset($feed['id']) && $feed['id'] > 0) {
                        $value = $feed['id'];
                    }
                }
            }
        }
        else if ($arguments['type'] === ProcessArg::NONE) {
            $value = "";
        }
        else if ($arguments['type'] === ProcessArg::TEXT) {
        }
        else if ($arguments['type'] === ProcessArg::SCHEDULEID) {
            //not supporte for now
        }
        return $process['process'].":".$value;
    }

    public function prepare($userid, $id) {
        $userid = intval($userid);
        $id = intval($id);
        
        $system = $this->get($id);
        $name = strtolower($system['name']);
        
        $feeds = $this->prepare_feeds($userid, $name, $system['modules']);
        $inputs = $this->prepare_inputs($userid, $feeds);
        
        return array('success'=>true, 'feeds'=>$feeds, 'inputs'=>$inputs);
    }

    private function prepare_feeds($userid, $name, $modules) {
        $feeds = array();
        $feeds[] = $this->prepare_feed($userid, $name.'_forecast');
        
        $length = count($modules);
        if ($length > 1) {
            for ($i = 1; $i <= $length; $i++) {
                $feeds[] = $this->prepare_feed($userid, $name.$i.'_forecast');
            }
        }
        return $feeds;
    }

    private function prepare_feed($userid, $name) {
        global $feed_settings;
        
        require_once "Modules/feed/feed_model.php";
        $feed = new Feed($this->mysqli, $this->redis, $feed_settings);
        
        $feedid = $feed->exists_tag_name($userid, self::DEFAULT_TAG, $name);
        if ($feedid == false) {
            $feedid = -1;
            $action = 'create';
        }
        else {
            $action = 'none';
        }
        return array(
            'id'=>$feedid,
            'name'=>$name,
            'tag'=>self::DEFAULT_TAG,
            'type'=>DataType::REALTIME,
            'engine'=>Engine::MYSQL,
            'action'=>$action
        );
    }

    private function prepare_inputs($userid, $feeds) {
        global $user, $feed_settings;
        
        require_once "Modules/feed/feed_model.php";
        $feed = new Feed($this->mysqli, $this->redis, $feed_settings);
        
        require_once "Modules/input/input_model.php";
        $input = new Input($this->mysqli, $this->redis, $feed);
        
        require_once "Modules/process/process_model.php";
        $process = new Process($this->mysqli, $input, $feed, $user->get_timezone($userid));
        $process_list = $process->get_process_list(); // emoncms supported processes
        
        $inputs = array();
        foreach ($feeds as $f) {
            $name = substr($f['name'], 0, strrpos($f['name'], '_'));
            
            $inputid = $input->exists_nodeid_name($userid, self::DEFAULT_NODE, $name);
            if ($inputid == false) {
                $action = 'create';
                $inputid = -1;
            }
            else {
                $action = 'none';
            }
            $processes = array();
            $processes[] = array(
                'name'=>'Log to Feed',
                'process'=>1,
                'arguments'=>array(
                    'type'=>ProcessArg::FEEDID,
                    'value'=>$f['name']
                )
            );
            
            if ($inputid >= 0 && $f['id'] >= 0) {
                $process_list = '1:'.$f['id'];
                $process_input = $input->get_processlist($inputid);
                if (!isset($processes['success'])) {
                    if ($process_input == '') {
                        $action = 'set';
                    }
                    else if ($process_input != $process_list) {
                        $action = 'override';
                    }
                }
                else {
                    if ($process_input == '') {
                        $action = 'set';
                    }
                    else {
                        $action = 'override';
                    }
                }
            }
            
            $inputs[] = array(
                'id'=>$inputid,
                'name'=>$name,
                'node'=>self::DEFAULT_NODE,
                'description'=>$name." forecast",
                'processList'=>$processes,
                'action'=>$action
            );
        }
        return $inputs;
    }

    public function exist($id) {
        $id = intval($id);
        
        static $system_exists_cache = array(); // Array to hold the cache
        if (isset($system_exists_cache[$id])) {
            return $system_exists_cache[$id]; // Retrieve from static cache
        }
        else {
            $exists = false;
//             if ($this->redis) {
//                 if (!$this->redis->exists("solar:$id")) {
//                     if ($this->load_feed_to_redis($id)) {
//                         $exists = true;
//                     }
//                 }
//                 else {
//                     $exists = true;
//                 }
//             }
//             else {
                $result = $this->mysqli->query("SELECT id FROM solar_system WHERE id='$id'");
                if ($result->num_rows>0) $exists = true;
//             }
            $system_exists_cache[$id] = $exists; // Cache it
        }
        return $exists;
    }

    private function exists_name($userid, $name) {
        $userid = intval($userid);
        $name = preg_replace('/[^\p{L}_\p{N}\s-:]/u','', $name);
        
        $stmt = $this->mysqli->prepare("SELECT id FROM solar_system WHERE userid=? AND name=?");
        $stmt->bind_param("is", $userid, $name);
        $stmt->execute();
        $stmt->bind_result($id);
        $result = $stmt->fetch();
        $stmt->close();
        
        if ($result && $id > 0) return $id; else return false;
    }

    public function get_list($userid) {
//         if ($this->redis) {
//             return $this->get_list_redis($userid);
//         } else {
            return $this->get_list_mysql($userid);
//         }
    }

    private function get_list_mysql($userid) {
        $userid = intval($userid);
        
        $systems = array();
        $sysresult = $this->mysqli->query("SELECT `id`,`userid`,`name`,`description`,`longitude`,`latitude`,`altitude` FROM solar_system WHERE userid='$userid' ORDER BY name asc");
        while ($system = (array) $sysresult->fetch_object()) {
            $systemid = intval($system['id']);
            $modules = array();
            $modresult = $this->mysqli->query("SELECT `id`,`inverter`,`type`,`tilt`,`azimuth`,`albedo`,`strings`,`modules` FROM solar_modules WHERE systemid='$systemid'");
            while ($module = (array) $modresult->fetch_object()) $modules[] = $module;
            
            $system['modules'] = $modules;
            $systems[] = $system;
        }
        return $systems;
    }

    public function get_config() {
        $systems = array();
        $sysresult = $this->mysqli->query("SELECT `id`,`userid`,`name`,`description`,`longitude`,`latitude`,`altitude` FROM solar_system ORDER BY name asc");
        while ($system = (array) $sysresult->fetch_object()) {
            // TODO: Return devicekeys instead of the potent writekey
            global $user;
            $apikey = $user->get_apikey_read($system['userid']);
            
            $systemid = intval($system['id']);
            $modules = array();
            $modresult = $this->mysqli->query("SELECT `inverter`,`type`,`tilt`,`azimuth`,`albedo`,`strings`,`modules` FROM solar_modules WHERE systemid='$systemid'");
            while ($module = (array) $modresult->fetch_object()) {$type = $module['type'];
                list($model, $manufacturer, $modelnumber) = explode('/', $type);
                unset($module['type']);
                
                $modules[] = array_merge(array('model'=>$model), $module, $this->get_module($type));
            }
            
            $system['apikey'] = $apikey;
            $system['modules'] = $modules;
            $systems[] = $system;
        }
        return $systems;
    }

    public function get($id) {
        $id = intval($id);
        
//         if ($this->redis) {
//             // Get from redis cache
//             $system = (array) $this->redis->hGetAll("solar:$id");
//         }
//         else {
            // Get from mysql db
            $result = $this->mysqli->query("SELECT `id`,`userid`,`name`,`description`,`longitude`,`latitude`,`altitude` FROM solar_system WHERE id = '$id'");
            $system = (array) $result->fetch_object();
            
            $modules = array();
            $result = $this->mysqli->query("SELECT `id`,`inverter`,`type`,`tilt`,`azimuth`,`albedo`,`strings`,`modules` FROM solar_modules WHERE systemid='$id'");
            while ($module = (array) $result->fetch_object()) {
                $type = $module['type'];
                list($method, $manufacturer, $model) = explode('/', $type);
                unset($module['id'], $module['userid'], $module['systemid'], $module['type']);
                
                $modules[] = array_merge(array('method'=>$method), $module, $this->get_module($type));
            }
            $system['modules'] = $modules;
            //         }
        return $system;
    }

    public function get_module_meta() {
        $meta = array();
        
        $dir = $this->get_module_dir();
        $it = new DirectoryIterator($dir);
        foreach ($it as $file) {
            if (file_exists($file->getPathname()) && $file->getExtension() == "json") {
                $method = strtolower(basename($file->getBasename('.json')));
                $meta[$method] = (array) json_decode(file_get_contents($file->getPathname()));;
            }
        }
        return $meta;
    }

    public function get_module_list() {
        $list = array();
        
        $dir = $this->get_module_dir();
        foreach (new DirectoryIterator($dir) as $modules) {
            if ($modules->isDir() && !$modules->isDot()) {
                $it = new RecursiveDirectoryIterator($modules->getPathname());
                foreach (new RecursiveIteratorIterator($it) as $file) {
                    if (file_exists($file) && $file->getExtension() == "json") {
                        $type = substr(pathinfo($file, PATHINFO_DIRNAME), strlen($dir)).'/'.pathinfo($file, PATHINFO_FILENAME);
                        $list[$type] = (array) json_decode(file_get_contents($file->getPathname()));
                    }
                }
            }
        }
        return $list;
    }

    public function get_module($type) {
        $dir = $this->get_module_dir();
        $file = $dir.$type.'.json';
        
        if (file_exists($file)) {
            return (array) json_decode(file_get_contents($file));
        }
        return array("success"=>false, "message"=>"Module for type ".$type." does not exist");
    }

    private function get_module_dir() {
        global $module_dir;
        if (isset($module_dir) && $module_dir !== "") {
            $module_dir = $module_dir;
        }
        else {
            $module_dir = self::DEFAULT_DIR;
        }
        if (substr($module_dir, -1) !== "/") {
            $module_dir .= "/";
        }
        return $module_dir."lib/modules/";
    }

    public function set_fields($id, $fields) {
        $success = true;
        
        $id = intval($id);
        $fields = json_decode(stripslashes($fields));
        
        if (isset($fields->name)) {
            $result = $this->set_string($id, "name", $fields->name);
            if (!$result['success']) {
                return $result;
            }
        }
        if (isset($fields->description)) {
            $result = $this->set_string($id, "description", $fields->name);
            if (!$result['success']) {
                return $result;
            }
        }
        
        if (isset($fields->longitude)) {
            $result = $this->set_double($id, "longitude", $fields->longitude);
            if (!$result['success']) {
                return $result;
            }
        }
        if (isset($fields->latitude)) {
            $result = $this->set_double($id, "latitude", $fields->latitude);
            if (!$result['success']) {
                return $result;
            }
        }
        if (isset($fields->altitude)) {
            $result = $this->set_double($id, "altitude", $fields->altitude);
            if (!$result['success']) {
                return $result;
            }
        }
        
        if (isset($fields->modules)) {
            $result = $this->set_modules($id, $fields->modules);
            if (!$result['success']) {
                return $result;
            }
        }
        return array('success'=>true, 'message'=>'Fields successfully updated');
    }

    private function set_string($id, $key, $value) {
        if (preg_replace('/[^\p{N}\p{L}_\s-:]/u','', $value) != $value) {
            return array('success'=>false, 'message'=>"Invalid characters in system $key: $value");
        }
        
        $stmt = $this->mysqli->prepare("UPDATE solar_system SET ".$key." = ? WHERE id = ?");
        $stmt->bind_param("si",$value,$id);
        
        $result = $stmt->execute();
        $stmt->close();
        if (!$result) {
            return array('success'=>true, 'message'=>"Error updating field $key: $value");
        }
        
        if ($this->redis) {
            $this->redis->hSet("solar:".$id,$key,$value);
        }
        return array('success'=>true, 'message'=>"Successfully updated field $key: $value");
    }

    private function set_double($id, $key, $value) {
        $stmt = $this->mysqli->prepare("UPDATE solar_system SET ".$key." = ? WHERE id = ?");
        $stmt->bind_param("di",$value,$id);
        
        $result = $stmt->execute();
        $stmt->close();
        if (!$result) {
            return array('success'=>true, 'message'=>"Error updating field $key: $value");
        }
        
        if ($this->redis) {
            $this->redis->hSet("solar:".$id,$key,$value);
        }
        return array('success'=>true, 'message'=>"Successfully updated field $key: $value");
    }

    public function set_modules($id, $modules) {
        // TODO: Improve module updating process
        $this->mysqli->query("DELETE FROM solar_modules WHERE `systemid`='$id'");
        for ($i = 0; $i < count($modules); $i++) {
            $module = (array) $modules[$i];
//             if (isset($module['id'])) {
//                 $stmt = $this->mysqli->prepare("UPDATE solar_modules SET inverter=?,type=?,count=?,tilt=?,azimuth=?,albedo=? WHERE id=?");
//                 $stmt->bind_param("ssidddi",$module['inverter'],$module['type'],$module['count'],$module['tilt'],$module['azimuth'],$module['albedo'],$module['id']);
//
//                 $result = $stmt->execute();
//                 $stmt->close();
//                 if (!$result) {
//                     return array('success'=>true, 'message'=>"Error updating modules");
//                 }
//             }
//             else {
                $system = $this->get($id);
                $this->create_module($system['userid'], $id, $module);
//             }
        }
//         if ($this->redis) {
//             $this->redis->hSet("solar:".$id,"modules",json_encode($modules));
//         }
        return array('success'=>true, 'message'=>"Successfully updated modules");
    }

    public function delete($id) {
        $id = intval($id);
        
        $this->mysqli->query("DELETE FROM solar_system WHERE `id`='$id'");
        $this->mysqli->query("DELETE FROM solar_modules WHERE `systemid`='$id'");
        if (isset($system_exists_cache[$id])) { unset($system_exists_cache[$id]); } // Clear static cache
        
//         if ($this->redis) {
//             $result = $this->mysqli->query("SELECT userid FROM system WHERE `id` = '$id'");
//             $row = (array) $result->fetch_object();
//             if (isset($row['userid']) && $row['userid']) {
//                 $this->redis->delete("solar:$id");
//                 $this->load_list_to_redis($row['userid']);
//             }
//         }
        return array('success'=>true, 'message'=>'System successfully deleted');
    }
}
