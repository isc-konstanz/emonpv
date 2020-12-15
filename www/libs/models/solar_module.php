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

class SolarModule {

    private $log;

    private $mysqli;

    public function __construct($mysqli) {
        $this->log = new EmonLogger(__FILE__);
        $this->mysqli = $mysqli;
    }

    public function get_list_meta() {
        $meta = array();
        
        $dir = $this->get_dir();
        foreach (glob($dir.'/*.json') as $file) {
            $meta[basename($file, ".json")] = (array) json_decode(file_get_contents($file), true);
        }
        ksort($meta);
        
        return $meta;
    }

    public function get_list() {
        $list = array();
        
        $dir = $this->get_dir();
        foreach (new DirectoryIterator($dir) as $modules) {
            if ($modules->isDir() && !$modules->isDot()) {
                $it = new RecursiveDirectoryIterator($modules->getPathname());
                foreach (new RecursiveIteratorIterator($it) as $file) {
                    if (file_exists($file) && $file->getExtension() == "json") {
                        $type = substr(pathinfo($file, PATHINFO_DIRNAME), strlen($dir)).'/'.pathinfo($file, PATHINFO_modelNAME);
                        $list[$type] = (array) json_decode(file_get_contents($file->getPathname()), true);
                    }
                }
            }
        }
        return $list;
    }

    public function get($type) {
        $dir = $this->get_dir();
        $file = $dir.$type.'.json';
        
        if (file_exists($file)) {
            return (array) json_decode(file_get_contents($file), true);
        }
        return array("success"=>false, "message"=>"Module for type ".$type." does not exist");
    }

    private function get_dir() {
        global $settings;
        if (!empty($settings['solar']['libs_dir'])) {
            $models_dir = $settings['solar']['libs_dir'];
        }
        else {
            $models_dir = SolarSystem::LIBS_DIR;
        }
        if (substr($models_dir, -1) !== "/") {
            $models_dir .= "/";
        }
        return $models_dir."modules/";
    }

    public function get_parameters($configs) {
        $parameters = array();
        foreach ($this->get_parameter_dirs($configs) as $dir) {
            $file = $dir."/module.cfg";
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
            $file = $dir."/module.cfg";
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
            $this->delete_file($dir."/module.cfg");
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
