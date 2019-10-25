<?php
    global $path;
    $v = 1;
?>

<svg aria-hidden="true" style="position: absolute; width: 0; height: 0; overflow: hidden;" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<?php
$svgs = new AppendIterator();
$svgs->append(new DirectoryIterator(dirname(__FILE__, 2)."/icons"));
$svgs->append(new DirectoryIterator(dirname(__FILE__, 2)."/images"));
foreach ($svgs as $svg) {
    if (!$svg->isDot() && !$svg->isDir() && $svg->getExtension() == 'svg') {
        require $svg->getPathname();
    }
}
?>
</svg>

<link href="<?php echo $path; ?>Modules/solar/views/solar.css" rel="stylesheet"/>
<script src="<?php echo $path; ?>Lib/vue.min.js"></script>

<div class="solar-container position-relative">
    <div id="solar-header" class="d-flex justify-content-between align-items-center">
        <h3><?php echo _('Solar systems'); ?></h3>
        <span id="api-help" style="float:right"><a href="api"><?php echo _('Solar system API Help'); ?></a></span>
    </div>

    <div id="solar-view" v-cloak>
        <template v-if="loaded">
            <template v-if="systemCount > 0">
                <div class="system" v-for="(system, sysid) in systems" :data-id="sysid">
                    <div class="system-header" :class="{ 'collapsed': isCollapsed(sysid) }" data-toggle="collapse" :data-target="'#solar-system'+sysid" 
                            @click="toggleCollapse(event, sysid)">
                        
                        <div class="system-item">
                            <div class="system-collapse">
                                <svg :id="'solar-system'+sysid+'-icon'" class="icon icon-collapse">
                                    <use xlink:href="#icon-chevron-down" v-if="isCollapsed(sysid)"></use>
                                    <use xlink:href="#icon-chevron-up" v-else></use>
                                </svg>
                            </div>
                            <div class="name"><span>{{system.name+(system.description.length>0 ? ":" : "")}}</span></div>
                            <div class="desc"><span>{{system.description}}</span></div>
                            <div class='grow'></div>
                            <div class="menu dropdown action" @click.prevent>
                                <svg class="dropdown-toggle icon icon-menu" data-toggle="dropdown">" +
                                    <use xlink:href="#icon-dots-vertical" />" +
                                </svg>
                                <ul class="dropdown-menu pull-right">
                                    <li><a class="system-config" @click.prevent.stop="solar_system.openConfig(system)"><?php echo _("Edit system"); ?></a></li>
                                    <li><a class="system-export" @click.prevent.stop="solar_system.openExport(system)" disabled><?php echo _("Export results"); ?></a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div :id="'solar-system'+sysid" class="system-body collapse" :class="{ 'in': !isCollapsed(sysid) }">
                        <div class="system-item">
                            <div class="solar-inverter-img" style="width:175px; padding:10px 30px;">
                                <img src="<?php echo $path; ?>Modules/solar/images/inverter-mono.png"></img>
                            </div>
                        </div>
                    </div>
                </div>
            </template>
            <div id="solar-footer">
                <div class="system-new">
                    <div class="divider"></div>
                    <button id="system-new" title="New solar system" type="button" class="btn btn-plain btn-light btn-circle" @click="solar_system.newSystem">
                        <svg class="icon">
                            <use xlink:href="#icon-plus" />
                        </svg>
                    </button>
                    <div class="divider"></div>
                </div>
            </div>
        </template>
        <div id="solar-loader" class="ajax-loader" v-else></div>
    </div>
</div>

<?php require "Modules/solar/dialogs/solar_system.php"; ?>

<script src="<?php echo $path; ?>Lib/moment.min.js"></script>
<script src="<?php echo $path; ?>Lib/misc/gettext.js?v=<?php echo $v; ?>"></script>
<script src="<?php echo $path; ?>Lib/user_locale.js?v=<?php echo $v; ?>"></script>
<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/views/solar.js"></script>
<script>
var path = "<?php echo $path; ?>";

</script>
<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/views/solar_view.js?v=<?php echo $v; ?>"></script>
