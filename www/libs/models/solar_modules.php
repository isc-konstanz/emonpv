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

class SolarModules {
    private $log;

    private $redis;
    private $mysqli;

    public function __construct($mysqli, $redis) {
        $this->log = new EmonLogger(__FILE__);
        $this->redis = $redis;
        $this->mysqli = $mysqli;
    }

    private function exist($id) {
        if ($this->redis) {
            if ($this->redis->exists("solar:modules#$id")) {
                return true;
            }
            return false;
        }
        $result = $this->mysqli->query("SELECT id FROM solar_modules WHERE id = '$id'");
        if ($result->num_rows>0) {
            //             if ($this->redis) {
            //                 $this->cache($system);
            //             }
            return true;
        }
        return false;
    }

    public function create($invid, $strid, $count, $geometry, $tracking, $type, $number, $settings) {
        $invid = intval($invid);
        $strid = intval($strid);
        
        if (empty($geometry)) {
            throw new SolarException("The systems geometry needs to be specified");
        }
        $geometry = json_decode(stripslashes($geometry), true);
        
        if (!isset($geometry['pitch']) || !is_numeric($geometry['pitch']) || 
            !isset($geometry['elevation']) || !is_numeric($geometry['elevation']) || 
            !isset($geometry['azimuth']) || !is_numeric($geometry['azimuth']) || 
            !isset($geometry['tilt']) || !is_numeric($geometry['tilt'])) {
            
            throw new SolarException("The modules geometrical specification is invalid");
        }
        
        $tracking = json_decode(stripslashes($tracking), true);
        if (empty($tracking)) {
            $tracking = null;
        }
        
        $count = intval($count);
        $number = intval($number);
        if (!empty($type)) {
            $type = preg_replace('/[^\/\|\,\w\s\-\:]/','', $type);
            // TODO: check if module exists
        }
        else {
            $type = null;
        }
        $settings = json_decode(stripslashes($settings), true);
        if (empty($settings)) {
            $settings = null;
        }
        
        $stmt = $this->mysqli->prepare("INSERT INTO solar_modules (invid,strid,count,pitch,elevation,azimuth,tilt,type,number,settings,tracking) VALUES (?,?,?,?,?,?,?,?,?,?,?)");
        $stmt->bind_param("iiiddddsiss",$invid,$strid,$count,$geometry['pitch'],$geometry['elevation'],$geometry['azimuth'],$geometry['tilt'],$type,$number,$settings,$tracking);
        $stmt->execute();
        $stmt->close();
        
        $id = $this->mysqli->insert_id;
        if ($id < 1) {
            throw new SolarException("Unable to create modules");
        }
        $variant = array(
            'id' => $id,
            'invid' => $invid,
            'strid' => $strid,
            'count' => $count,
            'pitch' => $geometry['pitch'],
            'elevation' => $geometry['elevation'],
            'azimuth' => $geometry['azimuth'],
            'tilt' => $geometry['tilt'],
            'type' => $type,
            'number' => $number,
            'settings' => empty(!$settings) ? json_encode($settings) : null,
            'tracking' => empty(!$tracking) ? json_encode($tracking) : null
        );
        if ($this->redis) {
            $this->add_redis($invid, $variant);
        }
        return $this->parse($variant);
    }

    public function get_list($invid) {
        if ($this->redis) {
            $modules = $this->get_list_redis($invid);
        } else {
            $modules = $this->get_list_mysql($invid);
        }
        usort($modules, function($v1, $v2) {
            if($v1['count'] == $v2['count']) {
                if($v1['number'] == $v2['number']) {
                    return $v1['number'] - $v2['number'];
                }
                return strcmp($v1['type'], $v2['type']);
            }
            return $v1['count'] - $v2['count'];
        });
        return $modules;
    }

    private function get_list_mysql($invid) {
        $invid = intval($invid);
        
        $modules = array();
        $result = $this->mysqli->query("SELECT * FROM solar_modules WHERE invid='$invid'");
        while ($variant = $result->fetch_array()) {
            $modules[] = $this->parse($variant);
        }
        return $modules;
    }

    private function get_list_redis($invid) {
        $modules = array();
        if ($this->redis->exists("solar:inverter#$invid:modules")) {
            foreach ($this->redis->sMembers("solar:inverter#$invid:modules") as $id) {
                $modules[] = $this->get_redis($id);
            }
        }
        else {
            $result = $this->mysqli->query("SELECT * FROM solar_modules WHERE invid='$invid'");
            while ($variant = $result->fetch_array()) {
                $this->add_redis($invid, $variant);
                $modules[] = $this->parse($variant);
            }
        }
        return $modules;
    }

    public function get($id) {
        $id = intval($id);
        if (!$this->exist($id)) {
            throw new SolarException("Modules for id $id does not exist");
        }
        if ($this->redis) {
            // Get from redis cache
            $modules = $this->get_redis($id);
        }
        else {
            // Get from mysql db
            $result = $this->mysqli->query("SELECT * FROM solar_modules WHERE id = '$id'");
            $modules = $this->parse($result->fetch_array());
        }
        return $modules;
    }

    private function get_redis($id) {
        return $this->parse((array) $this->redis->hGetAll("solar:modules#$id"));
    }

    private function add_redis($invid, $modules) {
        $this->redis->sAdd("solar:inverter#$invid:modules", $modules['id']);
        $this->redis->hMSet("solar:modules#".$modules['id'], $modules);
    }

    private function parse($modules) {
        return $this->decode($modules);
    }

    private function decode($modules) {
        if (empty($modules['settings'])) {
            $settings = null;
        }
        else {
            $settings = json_decode($modules['settings'], true);
        }
        if (empty($modules['tracking'])) {
            $tracking = null;
        }
        else {
            $tracking = json_decode($modules['tracking'], true);
        }
        return array(
            'id' => $modules['id'],
            'invid' => $modules['invid'],
            'strid' => $modules['strid'],
            'count' => $modules['count'],
            'geometry' => array(
                'pitch' => $modules['pitch'],
                'elevation' => $modules['elevation'],
                'azimuth' => $modules['azimuth'],
                'tilt' => $modules['tilt']
            ),
            'tracking' => $tracking,
            'type' => $modules['type'],
            'number' => $modules['number'],
            'settings' => $settings
        );
    }

//     public function get_models_meta() {
//         $meta = array();
        
//         $dir = $this->get_module_dir();
//         foreach (glob($dir.'/*.json') as $file) {
//             $meta[basename($file, ".json")] = (array) json_decode(file_get_contents($file), true);
//         }
//         ksort($meta);
        
//         return $meta;
//     }

//     public function get_models_list() {
//         $list = array();
        
//         $dir = $this->get_models_dir();
//         foreach (new DirectoryIterator($dir) as $modules) {
//             if ($modules->isDir() && !$modules->isDot()) {
//                 $it = new RecursiveDirectoryIterator($modules->getPathname());
//                 foreach (new RecursiveIteratorIterator($it) as $file) {
//                     if (file_exists($file) && $file->getExtension() == "json") {
//                         $type = substr(pathinfo($file, PATHINFO_DIRNAME), strlen($dir)).'/'.pathinfo($file, PATHINFO_FILENAME);
//                         $list[$type] = (array) json_decode(file_get_contents($file->getPathname()), true);
//                     }
//                 }
//             }
//         }
//         return $list;
//     }

//     public function get_models($type) {
//         $dir = $this->get_models_dir();
//         $file = $dir.$type.'.json';
        
//         if (file_exists($file)) {
//             return (array) json_decode(file_get_contents($file), true);
//         }
//         return array("success"=>false, "message"=>"Module for type ".$type." does not exist");
//     }

//     private function get_models_dir() {
//         global $settings;
//         if (!empty($settings['pvforecast']['dir'])) {
//             $models_dir = $settings['pvforecast']['dir'];
//         }
//         else {
//             $models_dir = SolarSystem::DEFAULT_DIR;
//         }
//         if (substr($models_dir, -1) !== "/") {
//             $models_dir .= "/";
//         }
//         return $models_dir."lib/modules/";
//     }

    public function update($id, $fields) {
        $id = intval($id);
        if (!$this->exist($id)) {
            throw new SolarException("Modules for id $id does not exist");
        }
        $fields = json_decode(stripslashes($fields), true);
        
        if (isset($fields['count'])) {
            $count = $fields['count'];
            
            if (empty($count) || !is_numeric($count) || $count < 1) {
                throw new SolarException("The modules count is invalid: $count");
            }
            if ($stmt = $this->mysqli->prepare("UPDATE solar_modules SET count = ? WHERE id = ?")) {
                $stmt->bind_param("ii", $count, $id);
                if ($stmt->execute() === false) {
                    $stmt->close();
                    throw new SolarException("Error while update count of modules#$id");
                }
                $stmt->close();
                
                if ($this->redis) {
                    $this->redis->hset("solar:modules#$id", 'count', $count);
                }
            }
            else {
                throw new SolarException("Error while setting up database update");
            }
        }
        if (isset($fields['number'])) {
            $number = $fields['number'];
            
            if (empty($number) || !is_numeric($number) || $number < 1) {
                throw new SolarException("The modules number is invalid: $number");
            }
            if ($stmt = $this->mysqli->prepare("UPDATE solar_modules SET number = ? WHERE id = ?")) {
                $stmt->bind_param("ii", $number, $id);
                if ($stmt->execute() === false) {
                    $stmt->close();
                    throw new SolarException("Error while update number of modules#$id");
                }
                $stmt->close();
                
                if ($this->redis) {
                    $this->redis->hset("solar:modules#$id", 'number', $number);
                }
            }
            else {
                throw new SolarException("Error while setting up database update");
            }
        }
        return array('success'=>true, 'message'=>'Modules successfully updated');
    }

    public function delete($id) {
        $id = intval($id);
        if (!$this->exist($id)) {
            throw new SolarException("Modules for id $id does not exist");
        }
        
        $this->mysqli->query("DELETE FROM solar_modules WHERE `id` = '$id'");
        if ($this->redis) {
            $this->delete_redis($id);
        }
        return array('success'=>true, 'message'=>'Modules successfully deleted');
    }

    private function delete_redis($id) {
        $invid = $this->redis->hget("solar:modules#$id",'invid');
        $this->redis->del("solar:modules#$id");
        $this->redis->srem("solar:inverter#$invid:modules", $id);
    }

}
