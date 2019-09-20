<?php
/*
 All Emoncms code is released under the GNU Affero General Public License.
 See COPYRIGHT.txt and LICENSE.txt.
 
 ---------------------------------------------------------------------
 Emoncms - open source energy visualisation
 Part of the OpenEnergyMonitor project:
 http://openenergymonitor.org
 
 */

abstract class SimulationModel {
    const PVLIB = "pvlib";
    const MOBIDIG = "mobidig";

    static public function get_all () {
        return array(
            SimulationModel::PVLIB,
            SimulationModel::MOBIDIG
        );
    }

    static public function is_valid($model) {
        return in_array($model, SimulationModel::get_all());
    }
}
