<?php

$schema['solar_system'] = array(
    'id' => array('type' => 'int(11)', 'Null'=>false, 'Key'=>'PRI', 'Extra'=>'auto_increment'),
    'userid' => array('type' => 'int(11)'),
    'name' => array('type' => 'text'),
    'description' => array('type' => 'text','default'=>''),
    'latitude' => array('type' => 'double(8,5)'),
    'longitude' => array('type' => 'double(8,5)'),
    'altitude' => array('type' => 'double')
);

$schema['solar_modules'] = array(
    'id' => array('type' => 'int(11)', 'Null'=>false, 'Key'=>'PRI', 'Extra'=>'auto_increment'),
    'systemid' => array('type' => 'int(11)'),
    'name' => array('type' => 'text'),
    'type' => array('type' => 'text'),
    'inverter' => array('type' => 'text'),
    'tilt' => array('type' => 'double'),
    'azimuth' => array('type' => 'double'),
    'albedo' => array('type' => 'double'),
    'modules_per_string' => array('type' => 'int(11)'),
    'strings_per_inverter' => array('type' => 'int(11)')
);
