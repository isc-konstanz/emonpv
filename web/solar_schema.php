<?php

$schema['solar_system'] = array(
    'id' => array('type' => 'int(11)', 'Null'=>false, 'Key'=>'PRI', 'Extra'=>'auto_increment'),
    'userid' => array('type' => 'int(11)'),
    'name' => array('type' => 'text'),
    'description' => array('type' => 'text','default'=>'')
);

$schema['solar_modules'] = array(
    'id' => array('type' => 'int(11)', 'Null'=>false, 'Key'=>'PRI', 'Extra'=>'auto_increment'),
    'userid' => array('type' => 'int(11)'),
    'systemid' => array('type' => 'int(11)'),
    'method' => array('type' => 'varchar(32)'),
    'type' => array('type' => 'text'),
    'count' => array('type' => 'int(11)'),
    'longitude' => array('type' => 'float'),
    'latitude' => array('type' => 'float'),
    'tilt' => array('type' => 'float'),
    'azimuth' => array('type' => 'float'),
    'albedo' => array('type' => 'float')
);
