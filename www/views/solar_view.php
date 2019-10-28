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
                    <div class="system-header" :class="{ 'collapsed': isCollapsed(sysid) }" data-toggle="collapse" :data-target="'#system'+sysid" 
                            @click="toggleCollapse(event, sysid)">
                        
                        <div class="system-item">
                            <div class="system-collapse">
                                <svg :id="'system'+sysid+'-icon'" class="icon icon-collapse">
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
                                    <li><a @click.prevent.stop="solar_system.openExport(system)" disabled><?php echo _("Export results"); ?></a></li>
                                    <li><a @click.prevent.stop="solar_system.openConfig(system)"><?php echo _("Settings"); ?></a></li>
                                    <li><a @click.prevent.stop="solar_system.openDelete(system)"><?php echo _("Delete"); ?></a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div :id="'system'+sysid" class="system-body collapse" :class="{ 'in': !isCollapsed(sysid) }">
                        <div class="inverter system-item" v-for="inverter in system.inverters" :data-id="inverter.id">
                            <div class="count"><input type="number" min="1" step="1" required :value="inverter.count" v-on:input="setCount"></input></div>
                            <div class="clipart"><img src="<?php echo $path; ?>Modules/solar/images/inverter-mono.png"></img></div>
                            <div class="modules">
                                <div>
                                    <div class="inverter-item" v-for="module in inverter.modules" :data-id="module.id">
                            			<div class="count"><input type="number" min="1" step="1" required :value="module.count" v-on:input="setCount"></input></div>
                            			<div class="name"><span>{{(module.type != null ? module.type : "")}}</span></div>
                                        <div class='grow'></div>
                                    </div>
                                </div>
                                <div class="system-add">
                                    <button title="Add inverter" type="button" class="btn btn-plain btn-small btn-circle" @click="solar_inverter.addModules(inverter)">
                                        <svg class="icon">
                                            <use xlink:href="#icon-plus" />
                                        </svg>
                                    </button>
                            		<div class="divider"></div>
                                </div>
                            </div>
                        </div>
                        <div class="system-add">
                            <button title="Add inverter" type="button" class="btn btn-plain btn-small btn-circle" @click="solar_system.addInverter(system)">
                                <svg class="icon">
                                    <use xlink:href="#icon-plus" />
                                </svg>
                            </button>
                    		<div class="divider" style="margin-right:40px;"></div>
                        </div>
                        <button :id="'system'+sysid+'-run'" class="system-run btn btn-plain btn-default pull-right"><?php echo _('Start'); ?></button>
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
