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
                            <div class="description"><span>{{system.description}}</span></div>
                            <div class='grow'></div>
                            <div class="menu dropdown action" @click.prevent>
                                <svg class="dropdown-toggle icon icon-menu" data-toggle="dropdown">
                                    <use xlink:href="#icon-dots-vertical" />
                                </svg>
                                <ul class="dropdown-menu pull-right">
                                    <li><a @click.prevent.stop="solar_system.openExport(system)" disabled><?php echo _("Export results"); ?></a></li>
                                    <li><a @click.prevent.stop="solar_inverter.newConfig(system)"><?php echo _("Add Inverter"); ?></a></li>
                                    <li><a @click.prevent.stop="solar_system.openConfig(system)"><?php echo _("Edit System"); ?></a></li>
                                    <li><a @click.prevent.stop="solar_system.openDelete(system)"><?php echo _("Delete System"); ?></a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div :id="'system'+sysid" class="system-body collapse" :class="{ 'in': !isCollapsed(sysid) }">
                        <div class="inverter system-item" v-for="inverter in system.inverters" :data-id="inverter.id">
                            <div class="count"><input type="number" min="1" step="1" required :value="inverter.count" v-on:input="setCount"></input></div>
                            <div class="clipart" title="<?php echo _("Edit inverter"); ?>" @click="solar_inverter.openConfig(system, inverter.id)">
                                <img src="<?php echo $path; ?>Modules/solar/images/inverter-mono.png"></img>
                            </div>
                            <div class="inverter-body">
                                <div>
                                    <div class="modules inverter-item" v-for="module in inverter.modules" :data-id="module.id">
                                        <div class="count"><input type="number" min="1" step="1" required :value="module.count" v-on:input="setCount"></input></div>
                                        <div class="name"><span>{{(module.type)}}</span></div>
                                        <div class="grow"></div>
                                        <div class="action" @click="solar_modules.openDeletion(inverter, module.id)">
                                            <svg class="icon icon-action">
                                                <use xlink:href="#icon-bin" />
                                            </svg>
                                        </div>
                                        <div class="action" @click="solar_modules.openConfig(inverter, module.id)">
                                            <svg class="icon icon-action">
                                                <use xlink:href="#icon-wrench" />
                                            </svg>
                                        </div>
                                    </div>
                                    <div class="inverter-item new" title="<?php echo _("Add modules"); ?>" @click="solar_modules.newConfig(inverter)">
                                        <div>
                                            <button type="button" class="btn btn-plain btn-small btn-circle">
                                                <svg class="icon">
                                                    <use xlink:href="#icon-plus" />
                                                </svg>
                                            </button>
                                        </div>
                                        <div></div>
                                        <div class="grow"></div>
                                        <div></div>
                                        <div></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="inverter-add" title="<?php echo _("Add inverter"); ?>" @click="solar_inverter.newConfig(system)">
                            <button type="button" class="btn btn-plain btn-small btn-circle">
                                <svg class="icon">
                                    <use xlink:href="#icon-plus" />
                                </svg>
                            </button>
                            <div class="divider"></div>
                        </div>
                        <div :id="'system'+sysid+'-results'" class="alert alert-comment" style="display:none; margin: 10px 38px 0px;">
                            <?php echo _('Placeholder for the simulation results and visualization.'); ?>
                        </div>
                        <button :id="'system'+sysid+'-run'" class="system-run btn btn-primary btn-plain pull-right" @click="run(system)"><?php echo _('Start'); ?></button>
                    </div>
                </div>
            </template>
            <div class="alert" v-else>
                <h3 class="alert-heading mt-0"><?php echo _('No inputs created'); ?></h3>
                <p>
                    <?php echo _('This is a placeholder to explain what this is and what to do.'); ?><br>
                    <?php echo _('You may want the next link as a guide for generating your request: '); ?><a href="api"><?php echo _('Solar system API helper'); ?></a>
                </p>
            </div>
            <div id="solar-footer">
                <div class="system-new">
                    <div class="divider"></div>
                    <button id="system-new" title="New solar system" type="button" class="btn btn-plain btn-light btn-circle" @click="solar_system.newConfig">
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
<?php require "Modules/solar/dialogs/solar_inverter.php"; ?>
<?php require "Modules/solar/dialogs/solar_modules.php"; ?>

<script src="<?php echo $path; ?>Lib/moment.min.js"></script>
<script src="<?php echo $path; ?>Lib/misc/gettext.js?v=<?php echo $v; ?>"></script>
<script src="<?php echo $path; ?>Lib/user_locale.js?v=<?php echo $v; ?>"></script>
<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/views/solar.js"></script>
<script>
var path = "<?php echo $path; ?>";

</script>
<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/views/solar_view.js?v=<?php echo $v; ?>"></script>
