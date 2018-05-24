<?php

    $domain = "messages";
    bindtextdomain($domain, "Modules/solar/locale");
    bind_textdomain_codeset($domain, 'UTF-8');

    $menu_dropdown_config[] = array(
            'name'=> dgettext($domain, "Solar Systems"),
            'icon'=>'icon-th-large',
            'path'=>"solar/view" ,
            'session'=>"write",
            'order' => 44
    );
