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

    public function __construct() {
        $this->log = new EmonLogger(__FILE__);
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

}
