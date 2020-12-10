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
        <h3><?php echo _('Solar projects'); ?></h3>
        <span id="api-help" style="float:right"><a href="api"><?php echo _('Solar projects API Help'); ?></a></span>
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
                                    <li><a @click.prevent.stop="solar_inverter.newConfig(system)"><?php echo _("Add Inverter"); ?></a></li>
                                    <li><a @click.prevent.stop="solar_system.openConfig(system)"><?php echo _("Edit System"); ?></a></li>
                                    <li><a @click.prevent.stop="solar_system.openDeletion(system)"><?php echo _("Delete System"); ?></a></li>
                                    <li><a @click.prevent.stop="solar.system.export(system.id)"><?php echo _("Export System"); ?></a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div :id="'system'+sysid" class="system-body collapse" :class="{ 'in': !isCollapsed(sysid) }">
                        <transition name="slide">
                            <div v-if="system.results.progressBarShow" class="system-progress progress progress-striped" :class="system.results.progressBarClass">
                                <div class="bar" :style="{ width: system.results.progressBarWidth }"></div>
                            </div>
                        </transition>
                        <div class="inverter system-item" v-for="inverter in system.inverters" :data-id="inverter.id">
                            <!--  div class="count">
                                <input :style="'width:'+(1+inverter.count.length)+'ch;'" type="number" min="1" step="1" required disabled
                                       :value="inverter.count" v-on:input="setCount($event, inverter, 'inverter')"></input>
                            </div -->
                            <div style="min-width: 24px;"></div>
                            <div class="clipart" title="<?php echo _("Edit inverter"); ?>" @click="!hasConfigs(inverter) ? solar_inverter.openConfig(system, inverter.id) : null" :disabled="hasConfigs(inverter) ? 'disabled' : null">
                                <img src="<?php echo $path; ?>Modules/solar/images/inverter-mono.png"></img>
                            </div>
                            <div class="inverter-body">
                                <div>
                                    <div class="modules inverter-item" v-for="configs in inverter.configs" :data-id="configs.id">
                                        <!-- div class="count">
                                            <input :style="'width:'+(1+configs.rows.count.length)+'ch;'" style="margin-left:0!important" type="number" min="1" step="1" required 
                                                   :value="configs.rows.count" v-on:input="setCount($event, configs, 'configs')"></input>
                                        </div>
                                        <div class="description"><span>x</span></div>
                                        <div class="count">
                                            <input :style="'width:'+(1+configs.rows.modules.length)+'ch;'" type="number" min="1" step="1" required 
                                                   :value="configs.rows.modules" v-on:input="setCount($event, configs, 'configs')"></input>
                                        </div -->
                                        <div class="count"><span>{{getCount(configs)}}</span></div>
                                        <div class="name"><span>{{getModule(configs.type).Manufacturer}}</span></div>
                                        <div class="description"><span>{{getModule(configs.type).Name}}</span></div>
                                        <div class="grow"></div>
                                        <div class="action" v-if="hasResults(system, configs)" @click="solar.configs.download(configs.id, system.id)">
                                            <svg class="icon icon-action">
                                                <title><?php echo _("Download results"); ?></title>
                                                <use xlink:href="#icon-download-small"></use>
                                            </svg>
                                        </div>
                            			<div class="action" v-else></div>
                                        <div class="action" disabled>
                                            <svg class="icon icon-action">
                                                <title><?php echo _("Duplicate configurations"); ?></title>
                                                <use xlink:href="#icon-content_copy" />
                                            </svg>
                                        </div>
                                        <div class="action" @click="solar_configs.openConfig(inverter, configs.id, configs.type)">
                                            <svg class="icon icon-action">
                                                <title><?php echo _("Edit configurations"); ?></title>
                                                <use xlink:href="#icon-wrench" />
                                            </svg>
                                        </div>
                                        <div class="action" @click="solar_configs.openDeletion(inverter, configs.id)">
                                            <svg class="icon icon-action">
                                                <title><?php echo _("Delete configurations"); ?></title>
                                                <use xlink:href="#icon-bin" />
                                            </svg>
                                        </div>
                                    </div>
                                    <div class="inverter-item new" title="<?php echo _("Add configurations"); ?>" @click="solar_configs.newConfig(inverter)">
                                        <div>
                                            <button type="button" class="btn btn-plain btn-small btn-circle">
                                                <svg class="icon">
                                                    <use xlink:href="#icon-plus" />
                                                </svg>
                                            </button>
                                        </div>
                                        <!-- div></div>
                                        <div></div -->
                                        <div></div>
                                        <div></div>
                                        <div class="grow"></div>
                                        <div></div>
                                        <div></div>
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
                        <transition name="fade">
                            <div v-if="isSuccess(system)" class="results">
                                <div class="title">
                                    <div><span><?php echo "Energy yield";?></span>&nbsp;<span style="color:#c6c6c6; font-weight:normal">(DC)</span></div>
                                    <div><span><?php echo "Specific yield";?></span>&nbsp;<span style="color:#c6c6c6; font-weight:normal">(DC)</span></div>
                                    <div class="fill"></div>
                                    <div><span><?php echo "Bifacial gain";?></span></div>
                                </div>
                                <div class="value">
                                    <div><span>{{getEnergy(system.results.yield_energy)}}</span>&nbsp;<span class="unit">{{getEnergyUnit(system.results.yield_energy)}}</span></div>
                                    <div><span>{{getNumber(system.results.yield_specific)}}</span>&nbsp;<span class="unit"><?php echo "kWh/kWp";?></span></div>
                                    <div class="fill"></div>
                                    <div><span>{{getNumber(system.results.gain_bifacial, 1)}}</span>&nbsp;<span class="unit"><?php echo "%";?></span></div>
                                </div>
                            </div>
                            <div v-else-if="isError(system)" class="alert alert-error results-error">
                                <div class="message" data-toggle="collapse" data-target="#results-trace">
                                    <span>{{system.results.error}}: </span><span>{{system.results.message}}</span>
                                </div>
                                <div id="results-trace" class="collapse trace" v-html="system.results.trace"></div>
                            </div>
                        </transition>
                        <button :id="'system'+sysid+'-download'" title="Download results" :disabled="!isSuccess(system)" @click="solar.system.download(system.id)"
                                 class="system-download btn btn-plain btn-primary btn-right-results pull-right" :class="{ 'btn-right-hide' : isNew(system) }">
                            <svg class="icon">
                                <use xlink:href="#icon-download"></use>
                            </svg>&nbsp;
                            <?php echo _('Download'); ?>
                        </button>
                        <button :id="'system'+sysid+'-run'" class="system-run btn btn-plain pull-right" 
                                :class="[ isNew(system) ? 'btn-primary btn-right-results' : 'btn-default' ]" :disabled="!isConfigured(system) || isRunning(system) ? 'disabled' : null" 
                                @click="run(system)">
                            <?php echo _('Start'); ?>
                        </button>
                    </div>
                </div>
            </template>
            <div class="alert" v-else>
                <h3 class="alert-heading mt-0"><?php echo _('No projects created'); ?></h3>
                <p>
                    <?php echo _('Welcome to <em>solar simulations</em>, powered by <b>ISC Konstanz e.V.</b>.'); ?><br>
                    <?php echo _('Here, you can '); ?><a href="#" @click="solar_system.newConfig">create</a><?php echo _(' several simulation projects and quickly compare summarized results.'); ?><br>
                    <br>
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
<?php require "Modules/solar/dialogs/solar_configs.php"; ?>

<script>
var modules = <?php echo json_encode($modules); ?>;
</script>
<script src="<?php echo $path; ?>Lib/moment.min.js"></script>
<script src="<?php echo $path; ?>Lib/misc/gettext.js?v=<?php echo $v; ?>"></script>
<script src="<?php echo $path; ?>Lib/user_locale.js?v=<?php echo $v; ?>"></script>
<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/views/solar.js"></script>
<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/views/solar_view.js?v=<?php echo $v; ?>"></script>
