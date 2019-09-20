<?php
    global $path;
    $v = 1;
?>

<link href="<?php echo $path; ?>Modules/solar/views/solar.css" rel="stylesheet"/>
<link href="<?php echo $path; ?>Modules/solar/libs/groupjs/groups.css" rel="stylesheet"/>

<svg aria-hidden="true" style="position: absolute; width: 0; height: 0; overflow: hidden;" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<?php
$icons = new DirectoryIterator(dirname(__FILE__, 2)."/icons");
foreach ($icons as $icon) {
    if (!$icon->isDot() && !$icon->isDir() && $icon->getExtension() == 'svg') {
        require $icon->getPathname();
    }
}
?>
</svg>

<div class="solar-container">
    <div id="solar-header" class="hide">
        <span id="api-help" style="float:right"><a href="api"><?php echo _('Solar system API Help'); ?></a></span>
        <h3><?php echo _('Solar systems'); ?></h3>
    </div>
    <div id="solar-none" class="alert alert-block hide" style="margin-top:12px">
        <h4 class="alert-heading"><?php echo _('No Systems configured'); ?></h4>
        <p>
            <?php echo _('This is a placeholder to explain what this is and what to do.'); ?><br>
            <?php echo _('You may want the next link as a guide for generating your request: '); ?><a href="api"><?php echo _('Solar system API helper'); ?></a>
        </p>
    </div>
    <div id="solar-actions" class="hide"></div>
    <div id="solar-systems"></div>

    <div id="solar-footer" class="hide">
        <div class="system-new">
            <div class="divider"></div>
            <button id="system-new" title="New solar system" type="button" class="btn btn-plain btn-light btn-circle">
                <svg class="icon">
                    <use xlink:href="#icon-plus" />
                </svg>
        	</button>
            <div class="divider"></div>
        </div>
    </div>
    <div id="solar-loader" class="ajax-loader"></div>
</div>

<?php require "Modules/solar/dialogs/solar_system.php"; ?>

<script type="text/javascript" src="<?php echo $path; ?>Lib/user_locale.js"></script>
<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/libs/groupjs/groups.js"></script>
<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/views/solar.js"></script>
<script>
var path = "<?php echo $path; ?>";

groups.actions = {
	'select': true,
    'delete': {
        'title':'<?php echo _("Delete Selected"); ?>',
        'class':'action',
        'icon':'icon-trash',
        'event':'deleteSelected',
        'hide':true
    }
};
groups.header = {
    'name': {'class':'name'},
    'description': {'class':'description'},
};
groups.init($('#solar-actions'));

</script>
<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/views/solar_view.js?v=<?php echo $v; ?>"></script>
