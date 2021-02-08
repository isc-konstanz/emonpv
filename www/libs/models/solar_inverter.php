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

class SolarInverter {
    private $log;

    private $redis;
    private $mysqli;

    public $configs;

    public function __construct($mysqli, $redis, $configs) {
        $this->log = new EmonLogger(__FILE__);
        $this->redis = $redis;
        $this->mysqli = $mysqli;
        $this->configs = $configs;
    }

    private function exist($id) {
        if ($this->redis) {
            if ($this->redis->exists("solar:inverter#$id")) {
                return true;
            }
            return false;
        }
        $result = $this->mysqli->query("SELECT * FROM solar_inverter WHERE id = '$id'");
        if ($result->num_rows>0) {
            if ($this->redis) {
                while ($inverter = $result->fetch_array()) {
                    $this->add_redis($inverter);
                }
            }
            return true;
        }
        return false;
    }

    public function create($sysid, $count=null, $model=null) {
        $sysid = intval($sysid);
        
        if (!empty($model)) {
            $model = json_decode(stripslashes($model), true);
        }
        if (empty($model)) {
            $type = null;
        }
        else if (!is_string($model)) {
            $type = 'custom';
        }
        else {
            $type = preg_replace('/[^\/\|\,\w\s\-\:]/','', $model);
            // TODO: check if module exists
        }
        if (isset($count) && !is_numeric($count)) {
            throw new SolarException("The inverter count is invalid");
        }
        
        $stmt = $this->mysqli->prepare("INSERT INTO solar_inverter (sysid,count,type) VALUES (?,?,?)");
        $stmt->bind_param("iis",$sysid,$count,$type);
        $stmt->execute();
        $stmt->close();
        
        $id = $this->mysqli->insert_id;
        if ($id < 1) {
            throw new SolarException("Unable to create inverter");
        }
        $inverter = array(
            'id' => $id,
            'sysid' => $sysid,
            'type' => $type,
            'count' => $count
        );
        if ($this->redis) {
            $this->add_redis($inverter);
        }
        if (substr($type, 0, 6) === 'custom') {
            $this->write_parameters($inverter, $model);
        }
        return $this->parse($inverter);
    }

    public function get_configs($invid) {
        $configs = array();
        
        $results = $this->mysqli->query("SELECT * FROM solar_refs WHERE invid='$invid' ORDER BY `order` ASC");
        while ($result = $results->fetch_array()) {
            $id = $result['cfgid'];
            $config = $this->configs->get($id);
            $config = array_merge(array(
                'id'=>intval($id),
                'invid'=>intval($invid),
                'strid'=>intval($result['strid']),
                'order'=>intval($result['order']),
                'count'=>isset($result['count']) ? intval($result['count']) : null
                
            ), array_slice($config, 2));
            
            $configs[] = $config;
        }
        return $configs;
    }

    public function get_list($sysid) {
        if ($this->redis) {
            $inverters =  $this->get_list_redis($sysid);
        } else {
            $inverters =  $this->get_list_mysql($sysid);
        }
        usort($inverters, function($i1, $i2) {
            if($i1['count'] == $i2['count']) {
                return strcmp($i1['type'], $i2['type']);
            }
            return $i1['count'] - $i2['count'];
        });
        return $inverters;
    }

    private function get_list_mysql($sysid) {
        $sysid = intval($sysid);
        
        $inverters = array();
        $results = $this->mysqli->query("SELECT * FROM solar_inverter WHERE sysid='$sysid'");
        while ($result = $results->fetch_array()) {
            $inverter = $this->parse($result);
            $inverters[] = $inverter;
        }
        return $inverters;
    }

    private function get_list_redis($sysid) {
        $inverters = array();
        if ($this->redis->exists("solar:system#$sysid:inverters")) {
            foreach ($this->redis->sMembers("solar:system#$sysid:inverters") as $id) {
                $inverters[] = $this->get_redis($id);
            }
        }
        else {
            $result = $this->mysqli->query("SELECT * FROM solar_inverter WHERE sysid='$sysid'");
            while ($inverter = $result->fetch_array()) {
                $this->add_redis($inverter);
                $inverters[] = $this->parse($inverter);
            }
        }
        return $inverters;
    }

    public function get($id) {
        $id = intval($id);
        if (!$this->exist($id)) {
            throw new SolarException("Inverter for id $id does not exist");
        }
        if ($this->redis) {
            // Get from redis cache
            $inverter = $this->get_redis($id);
        }
        else {
            // Get from mysql db
            $result = $this->mysqli->query("SELECT * FROM solar_inverter WHERE id = '$id'");
            $inverter = $this->parse($result->fetch_array());
        }
        return $inverter;
    }

    private function get_redis($id) {
        return $this->parse((array) $this->redis->hGetAll("solar:inverter#$id"));
    }

    private function add_redis($inverter) {
        $this->redis->sAdd("solar:system#".$inverter['sysid'].":inverters", $inverter['id']);
        $this->redis->hMSet("solar:inverter#".$inverter['id'], $inverter);
    }

    private function parse($result, $configs=array()) {
        $inverter = array(
                'id' => intval($result['id']),
                'sysid' => intval($result['sysid']),
                'count' => !empty($result['count']) ? intval($result['count']) : null,
                'type' => $result['type']
        );
        if (!empty($result['type']) && 
                substr($inverter['type'], 0, 6) === 'custom') {
            $inverter['model'] = $this->get_parameters($inverter);
        }
        if ($configs == null) {
            $configs = $this->get_configs($result['id']);
        }
        $inverter['configs'] = $configs;
        
        return $inverter;
    }

    public function update($inverter, $fields) {
        $fields = json_decode(stripslashes($fields), true);
        
        $this->update_integer($inverter['id'], 'inverter', $fields, 'count', 1, PHP_INT_MAX);
        
        $this->update_module($inverter, $fields);
        $this->update_string($inverter['id'], 'inverter', $fields, 'type');
        
        return $this->get($inverter['id']);
    }

    private function update_module($inverter, $fields) {
        if (!empty($fields['type'])) {
            if (substr($fields['type'], 0, 6) !== "custom") {
                if (substr($inverter['type'], 0, 6) === "custom") {
                    $this->delete_parameters($inverter);
                }
                $this->update_string($inverter['id'], 'configs', $fields, 'type');
                return;
            }
            else {
                if (empty($fields['model'])) {
                    throw new SolarException("The model configuration is invalid");
                }
                $this->update_string($inverter['id'], 'inverter', $fields, 'type');
            }
        }
        if (!isset($fields['model'])) {
            return;
        }
        
        $params = $this->get_parameters($inverter);
        foreach ($fields['model'] as $key=>$val) {
            $params[$key] = $val;
        }
        $this->write_parameters($inverter, $params);
    }

    private function update_integer($id, $database, $fields, $field, $min, $max) {
        $this->update_number($id, $database, $fields, $field, $min, $max, 'i');
    }

    private function update_number($id, $database, $fields, $field, $min, $max, $type) {
        if (!array_key_exists($field, $fields)) {
            return;
        }
        $value = $fields[$field];
        
        if ($value && (!is_numeric($value) || $value < $min || $value > $max)) {
            throw new SolarException("The configs $field is invalid: $value");
        }
        $this->update_database($id, $database, $field, $value, $type);
    }

    private function update_string($id, $database, $fields, $field, $json=false) {
        if (!array_key_exists($field, $fields)) {
            return;
        }
        $value = $fields[$field];
        
        if ($json) {
            $value = json_encode($value);
        }
        $this->update_database($id, $database, $field, $value, 's');
    }

    private function update_database($id, $database, $field, $value, $type) {
        if ($stmt = $this->mysqli->prepare("UPDATE solar_$database SET $field = ? WHERE id = ?")) {
            $stmt->bind_param($type."i", $value, $id);
            if ($stmt->execute() === false) {
                $stmt->close();
                throw new SolarException("Error while update $field of configs#$id");
            }
            $stmt->close();
            
            if ($this->redis) {
                $this->redis->hset("solar:inverter#$id", $field, $value);
            }
        }
        else {
            throw new SolarException("Error while setting up database update");
        }
    }

    public function delete($inverter, $force_delete=false) {
        $result = $this->mysqli->query("SELECT `id` FROM solar_inverter WHERE sysid = '".$inverter['sysid']."'");
        if ($result->num_rows <= 1 && !$force_delete) {
            return array('success'=>false, 'message'=>'Unable to delete last inverter of system.');
        }
        $this->delete_parameters($inverter);
        $this->delete_configs($inverter);
        
        $this->mysqli->query("DELETE FROM solar_inverter WHERE `id` = '".$inverter['id']."'");
        if ($this->redis) {
            $this->delete_redis($inverter['id']);
        }
        return array('success'=>true, 'message'=>'Inverter successfully deleted');
    }

    private function delete_configs($inverter) {
        $results = $this->mysqli->query("SELECT id, userid FROM solar_system WHERE id = '".$inverter['sysid']."'");
        $system = $results->fetch_array();
        $system_dir = SolarSystem::get_system_dir($system);
        
        $results = $this->mysqli->query("SELECT * FROM solar_refs WHERE `invid` = '".$inverter['id']."' ORDER BY `order` ASC");
        while ($result = $results->fetch_array()) {
            $order = $result['order'];
            $this->delete_file("$system_dir/results/results_$order.csv");
            $this->delete_file("$system_dir/conf/configs$order.cfg");
            $this->delete_file("$system_dir/conf/configs$order.d");
        }
        $this->delete_file("$system_dir/results/results.csv");
        $this->delete_file("$system_dir/results.csv");
        $this->delete_file("$system_dir/results.xlsx");
        $this->mysqli->query("DELETE FROM solar_refs WHERE `invid` = '".$inverter['id']."'");
    }

    private function delete_redis($id) {
        $sysid = $this->redis->hget("solar:inverter#$id",'sysid');
        $this->redis->del("solar:inverter#$id");
        $this->redis->srem("solar:system#$sysid:inverters", $id);
    }

    public function get_parameters($inverter) {
        $parameters = array();
        $parameters_file = $this->get_parameter_file($inverter);
        if (file_exists($parameters_file)) {
            $parameters_data = parse_ini_file($parameters_file, false, INI_SCANNER_TYPED);
            foreach ($parameters_data as $key => $value) {
                $parameters[$key] = $value;
            }
        }
        return $parameters;
    }

    public function write_parameters($inverter, $parameters=array()) {
        $dir = $this->get_parameter_dir($inverter);
        if (!file_exists($dir)) {
            mkdir($dir, 0755, true);
        }
        $file = $this->get_parameter_file($inverter, $dir);
        $this->delete_file($file);
        foreach ($parameters as $key=>$val) {
            if ($val !== '') {
                file_put_contents($file, "$key = $val".PHP_EOL, FILE_APPEND);
            }
        }
    }

    public function delete_parameters($inverter) {
        $this->delete_file($this->get_parameter_file($inverter));
    }

    private function get_parameter_file($inverter, $dir=null) {
        if ($dir == null) {
            $dir = $this->get_parameter_dir($inverter);
        }
        $id = $inverter['id'];
        
        return "$dir/inverter$id.cfg";
    }

    private function get_parameter_dir($inverter) {
        $results = $this->mysqli->query("SELECT id, userid FROM solar_system WHERE id = '".$inverter['sysid']."'");
        $system = $results->fetch_array();
        $system_dir = SolarSystem::get_system_dir($system);
        
        return "$system_dir/conf/.inv";
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

}
