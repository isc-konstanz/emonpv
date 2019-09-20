<?php

$schema['solar_system'] = array(
    'id' => array('type' => 'INT(11)', 'Null'=>false, 'Key'=>'PRI', 'Extra'=>'AUTO_INCREMENT'),
    'userid' => array('type' => 'INT(11)', 'Null'=>false),
    'time_cr' => array('type' => 'INT(10)', 'Null'=>false),
    'time_rn' => array('type' => 'INT(10)'),
    'forecast' => array('type' => 'TINYINT(1)', 'default'=>0),
    'model' => array('type' => 'VARCHAR(32)', 'Null'=>false),
    'name' => array('type' => 'TEXT', 'Null'=>false),
    'description' => array('type' => 'TEXT', 'default'=>0),
    'latitude' => array('type' => 'DOUBLE(8,5)', 'Null'=>false),
    'longitude' => array('type' => 'DOUBLE(8,5)', 'Null'=>false),
    'altitude' => array('type' => 'DOUBLE(5,2)'),
    'albedo' => array('type' => 'DOUBLE(3,2)')
);

$schema['solar_inverter'] = array(
    'id' => array('type' => 'INT(11)', 'Null'=>false, 'Key'=>'PRI', 'Extra'=>'AUTO_INCREMENT'),
    'sysid' => array('type' => 'INT(11)', 'Null'=>false),
    'count' => array('type' => 'INT(11)', 'default'=>1),
    'type' => array('type' => 'VARCHAR(64)'),
    'settings' => array('type' => 'TEXT')
);

$schema['solar_modules'] = array(
    'id' => array('type' => 'INT(11)', 'Null'=>false, 'Key'=>'PRI', 'Extra'=>'AUTO_INCREMENT'),
    'invid' => array('type' => 'INT(11)', 'Null'=>false),
    'strid' => array('type' => 'TINYINT(4)', 'default'=>1),
    'count' => array('type' => 'INT(11)', 'default'=>1),
    'azimuth' => array('type' => 'DOUBLE(5,2)'),
    'tilt' => array('type' => 'DOUBLE(5,2)'),
    'type' => array('type' => 'VARCHAR(64)'),
    'settings' => array('type' => 'TEXT'),
    'tracking' => array('type' => 'TEXT')
);
