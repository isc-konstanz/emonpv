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

    public function create($sysid, $type=null) {
        $sysid = intval($sysid);
        
        if (!empty($type)) {
            $type = preg_replace('/[^\/\|\,\w\s\-\:]/','', $type);
            // TODO: check if inverter exists
        }
        else {
            $type = null;
        }
        
        $stmt = $this->mysqli->prepare("INSERT INTO solar_inverter (sysid,type) VALUES (?,?)");
        $stmt->bind_param("is",$sysid,$type);
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
            'count' => 1
        );
        if ($this->redis) {
            $this->add_redis($inverter);
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

    private function parse($inverter, $configs=array()) {
        if ($configs == null) {
            $configs = $this->get_configs($inverter['id']);
        }
        return array(
            'id' => intval($inverter['id']),
            'sysid' => intval($inverter['sysid']),
            'count' => isset($inverter['count']) ? intval($inverter['count']) : null,
            'type' => strval($inverter['type']),
            'configs' => $configs
        );
    }

    public function update($inverter, $fields) {
        $fields = json_decode(stripslashes($fields), true);
        
        if (isset($fields['count'])) {
            $count = $fields['count'];
            
            if (empty($count) || !is_numeric($count) || $count < 1) {
                throw new SolarException("The inverter count is invalid: $count");
            }
            if ($stmt = $this->mysqli->prepare("UPDATE solar_inverter SET count = ? WHERE id = ?")) {
                $stmt->bind_param("ii", $count, $inverter['id']);
                if ($stmt->execute() === false) {
                    $stmt->close();
                    throw new SolarException("Error while update count of inverter#".$inverter['id']);
                }
                $stmt->close();
                
                if ($this->redis) {
                    $this->redis->hset("solar:inverter#".$inverter['id'], 'count', $count);
                }
            }
            else {
                throw new SolarException("Error while setting up database update");
            }
        }
        return array('success'=>true, 'message'=>'Inverter successfully updated');
    }

    public function delete($inverter, $force_delete=false) {
        $result = $this->mysqli->query("SELECT `id` FROM solar_inverter WHERE sysid = '".$inverter['sysid']."'");
        if ($result->num_rows <= 1 && !$force_delete) {
            return array('success'=>false, 'message'=>'Unable to delete last inverter of system.');
        }
        // TODO: verify if configs are not used of any system
        foreach ($this->get_configs($inverter['id']) as $configs) {
            $this->configs->delete($configs['id']);
        }
        $this->mysqli->query("DELETE FROM solar_inverter_configs WHERE `invid` = '".$inverter['id']."'");
        
        $this->mysqli->query("DELETE FROM solar_inverter WHERE `id` = '".$inverter['id']."'");
        if ($this->redis) {
            $this->delete_redis($inverter['id']);
        }
        return array('success'=>true, 'message'=>'Inverter successfully deleted');
    }

    private function delete_redis($id) {
        $sysid = $this->redis->hget("solar:inverter#$id",'sysid');
        $this->redis->del("solar:inverter#$id");
        $this->redis->srem("solar:system#$sysid:inverters", $id);
    }

    public function get_parameters($configs) {
        $parameters = array();
        foreach ($this->get_parameter_dirs($configs) as $dir) {
            $file = $dir."/inverter.cfg";
            if (file_exists($file)) {
                $parameter_file = parse_ini_file($file, false, INI_SCANNER_TYPED);
                foreach ($parameter_file as $key => $value) {
                    $parameters[$key] = $value;
                }
            }
        }
        return $parameters;
    }

    public function write_parameters($configs, $parameters) {
        foreach ($this->get_parameter_dirs($configs) as $dir) {
            if (!file_exists($dir)) {
                mkdir($dir, 0755, true);
            }
            $file = $dir."/inverter.cfg";
            $this->delete_file($file);
            foreach ($parameters as $key=>$val) {
                if ($val !== '') {
                    file_put_contents($file, "$key = $val".PHP_EOL, FILE_APPEND);
                }
            }
        }
    }

    public function delete_parameters($configs) {
        foreach ($this->get_parameter_dirs($configs) as $dir) {
            $this->delete_file($dir."/inverter.cfg");
        }
    }

    private function get_parameter_dirs($configs) {
        $user_id = $configs['userid'];
        $user_dir = SolarSystem::get_user_dir($user_id);
        $dirs = array();
        
        if (isset($configs['sysid'])) {
            $dirs[] = $this->get_parameter_dir($configs, $user_dir);
        }
        else {
            $results = $this->mysqli->query("SELECT * FROM solar_refs WHERE `cfgid` = '".$configs['id']."' ORDER BY `order` ASC");
            while ($result = $results->fetch_array()) {
                $dirs[] = $this->get_parameter_dir($result, $user_dir);
            }
        }
        return $dirs;
    }

    private function get_parameter_dir($configs, $user_dir) {
        $system = array('id' => intval($configs['sysid']));
        $system_dir = SolarSystem::get_system_dir($system, $user_dir);
        
        return $system_dir."/conf/configs".intval($configs['order']).".d";
    }

    private function delete_file($path) {
        if (!file_exists($path)) {
            return;
        }
        if (is_file($path)) {
            unlink($path);
        }
    }

}
