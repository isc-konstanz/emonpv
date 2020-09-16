<?php

$schema['solar_system'] = array(
    'id' => array('type' => 'int(11)', 'Null'=>false, 'Key'=>'PRI', 'Extra'=>'auto_increment'),
    'userid' => array('type' => 'int(11)', 'Null'=>false),
    'locid' => array('type' => 'int(11)', 'Null'=>false),
    'model' => array('type' => 'varchar(32)', 'Null'=>false),
    'name' => array('type' => 'text', 'Null'=>false),
    'description' => array('type' => 'text')
);

$schema['solar_location'] = array(
    'id' => array('type' => 'int(11)', 'Null'=>false, 'Key'=>'PRI', 'Extra'=>'auto_increment'),
    'userid' => array('type' => 'int(11)', 'Null'=>false),
    'name' => array('type' => 'text', 'Null'=>false),
    'latitude' => array('type' => 'double(8,5)'),
    'longitude' => array('type' => 'double(8,5)'),
    'altitude' => array('type' => 'double(5,2)'),
    'albedo' => array('type' => 'double(3,2)'),
    'file' => array('type' => 'text')
);

$schema['solar_configs'] = array(
    'id' => array('type' => 'int(11)', 'Null'=>false, 'Key'=>'PRI', 'Extra'=>'auto_increment'),
    'userid' => array('type' => 'int(11)', 'Null'=>false),
    'type' => array('type' => 'varchar(64)'),
    'orientation' => array('type' => 'tinyint(1)')
);

$schema['solar_rows'] = array(
    'id' => array('type' => 'int(11)', 'Null'=>false),
    'count' => array('type' => 'int(11)', 'Null'=>false),
    'pitch' => array('type' => 'double(3,2)', 'Null'=>false),
    'modules' => array('type' => 'int(11)', 'Null'=>false),
    'stack' => array('type' => 'int(11)'),
    'gap_x' => array('type' => 'double(4,3)'),
    'gap_y' => array('type' => 'double(4,3)'),
    'pos_x' => array('type' => 'int(11)'),
    'pos_y' => array('type' => 'int(11)')
);

$schema['solar_mounting'] = array(
    'id' => array('type' => 'int(11)', 'Null'=>false),
    'tilt' => array('type' => 'double(5,2)'),
    'azimuth' => array('type' => 'double(5,2)'),
    'elevation' => array('type' => 'double(5,2)')
);

$schema['solar_tracking'] = array(
    'id' => array('type' => 'int(11)', 'Null'=>false),
    'axis' => array('type' => 'tinyint(1)'),
    'axis_height' => array('type' => 'double(5,2)'),
    'tilt_max' => array('type' => 'double(5,2)'),
    'backtrack' => array('type' => 'tinyint(1)')
);

$schema['solar_inverter'] = array(
    'id' => array('type' => 'int(11)', 'Null'=>false, 'Key'=>'PRI', 'Extra'=>'auto_increment'),
    'sysid' => array('type' => 'int(11)', 'Null'=>false),
    'type' => array('type' => 'varchar(64)'),
    'count' => array('type' => 'int(11)')
);

$schema['solar_inverter_configs'] = array(
    'invid' => array('type' => 'int(11)', 'Null'=>false),
    'strid' => array('type' => 'int(11)', 'Null'=>false),
    'cfgid' => array('type' => 'int(11)', 'Null'=>false),
    'count' => array('type' => 'int(11)')
);

$schema['solar_system_configs'] = array(
    'sysid' => array('type' => 'int(11)', 'Null'=>false),
    'cfgid' => array('type' => 'int(11)', 'Null'=>false)
);
