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
    const VIEW_FACTOR = "ViewFactor";
    const RAY_TRACING = "RayTracing";

    static public function get_all () {
        return array(
            SimulationModel::VIEW_FACTOR,
            SimulationModel::RAY_TRACING
        );
    }

    static public function is_valid($model) {
        return in_array($model, SimulationModel::get_all());
    }
}
