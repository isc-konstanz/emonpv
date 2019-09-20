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

    private $modules;

    public function __construct($mysqli, $redis) {
        $this->log = new EmonLogger(__FILE__);
        $this->redis = $redis;
        $this->mysqli = $mysqli;
        
        $this->modules = new SolarModules($mysqli, $redis);
    }

    private function exist($id) {
        if ($this->redis) {
            if ($this->redis->exists("solar:inverter#$id")) {
                return true;
            }
            return false;
        }
        $result = $this->mysqli->query("SELECT id FROM solar_inverter WHERE id = '$id'");
        if ($result->num_rows>0) {
//             if ($this->redis) {
//                 $this->cache($system);
//             }
            return true;
        }
        return false;
    }

    public function create($sysid, $type=null, $settings=null) {
        $sysid = intval($sysid);
        
        if (!empty($type)) {
            $type = preg_replace('/[^\/\|\,\w\s\-\:]/','', $type);
            // TODO: check if inverter exists
        }
        else {
            $type = null;
        }
        if (empty($settings)) {
            $settings = null;
        }
        
        $stmt = $this->mysqli->prepare("INSERT INTO solar_inverter (sysid,type,settings) VALUES (?,?,?)");
        $stmt->bind_param("iss",$sysid,$type,$settings);
        $stmt->execute();
        $stmt->close();
        
        $id = $this->mysqli->insert_id;
        if ($id < 1) {
            throw new SolarException("Unable to create inverter");
        }
        $inverter = array(
            'id' => $id,
            'sysid' => $sysid,
            'count' => 1,
            'type' => $type,
            'settings' => empty(!$settings) ? json_encode($settings) : null
        );
        if ($this->redis) {
            $this->add_redis($inverter);
        }
        $modules = array($this->modules->create($id));
        
        return $this->parse($inverter, $modules);
    }

    public function get_list($sysid) {
        if ($this->redis) {
            $inverters =  $this->get_list_redis($sysid);
        } else {
            $inverters =  $this->get_list_mysql($sysid);
        }
        usort($inverters, function($i1, $i2) {
            if($i1['count'] == $i2['count']) {
                return strcmp($i1['name'], $i2['name']);
            }
            return $i1['count'] - $i2['count'];
        });
        return $inverters;
    }

    private function get_list_mysql($sysid) {
        $sysid = intval($sysid);
        
        $inverters = array();
        $result = $this->mysqli->query("SELECT * FROM solar_inverter WHERE sysid='$sysid'");
        while ($inverter = $result->fetch_array()) {
            $inverters[] = $this->parse($inverter);
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
            $inverters = $this->get_list_mysql($userid);
            foreach($inverters as $inverter) {
                $this->add_redis($inverter);
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

    private function parse($inverter, $modules=null) {
        if ($modules == null) {
            $modules = $this->modules->get_list($inverter['id']);
        }
        return $this->decode($inverter, $modules);
    }

    private function decode($inverter, $modules) {
        if (empty($inverter['settings'])) {
            $settings = null;
        }
        else {
            $settings = json_decode($inverter['settings'], true);
        }
        return array(
            'id' => $inverter['id'],
            'sysid' => $inverter['sysid'],
            'count' => $inverter['count'],
            'type' => $inverter['type'],
            'settings' => $settings,
            'modules' => $modules
        );
    }

    public function delete($id) {
        $id = intval($id);
        if (!$this->exist($id)) {
            throw new SolarException("Inverter for id $id does not exist");
        }
        foreach($this->modules->get_list($id) as $modules) {
            $this->modules->delete($modules['id']);
        }
        
        $this->mysqli->query("DELETE FROM solar_inverter WHERE `id` = '$id'");
        if ($this->redis) {
            $this->delete_redis($id);
        }
        return array('success'=>true, 'message'=>'System successfully deleted');
    }

    private function delete_redis($id) {
        $sysid = $this->redis->hget("solar:inverter#$id",'sysid');
        $this->redis->del("solar:inverter#$id");
        $this->redis->srem("solar:system#$sysid:inverters", $id);
    }

}
