<?php
    global $path;
?>

<link href="<?php echo $path; ?>Modules/solar/libs/misc/titatoggle-dist-min.css" rel="stylesheet">

<div id="module-config-modal" class="modal modal-adjust hide keyboard" tabindex="-1" role="dialog" aria-labelledby="module-config-label" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="module-config-label"></h3>
    </div>
    <div id="module-config" class="modal-body">
        <div id="module-config-sidebar" class="modal-sidebar">
            <div style="overflow-x: hidden; width:100%">
                <div id="module-sidebar-modules" class="accordion"></div>
            </div>
        </div>
        <div id="module-config-content" class="modal-content">
            <p id="module-config-description" class="description">
                <?php echo _('Placeholder for a short description of this dialog and what to do here.'); ?>
            </p>
            
            <div class="settings" style="padding-left: 0; margin-top: 10px;">
                <div class="settings-title fill">
                    <svg id="module-tracking-icon" class="icon icon-collapse">
                        <use xlink:href="#icon-chevron-right" />
                    </svg>
                    <span type="text">
                        <?php echo _('Tracking'); ?>
                    </span>
                    <span id="module-tracking-tooltip" data-toggle="tooltip" data-placement="right"
                            title="Placeholder description of tracking configurations."
                            style="margin-right: 18px">
                        <svg class="icon icon-info">
                            <use xlink:href="#icon-question" />
                        </svg>
                    </span>
                    <div id="module-tracking" class='checkbox checkbox-slider--b-flat checkbox-slider-info'>
                        <label><input type='checkbox' value=false><span></span></input></label>
                    </div>
                </div>
            </div>
            <div id="module-tracking-settings" class="collapse">
                <div class="settings">
                    <div class="settings-header">
                        <div>
                            <span><?php echo _('Axis height'); ?></span><span class="required asterisk">&ast;</span>
                            <span class="unit">[m]</span>
                        </div>
                        <div>
                            <span><?php echo _('Tilt maximum'); ?></span><span class="required asterisk">&ast;</span>
                            <span class="unit" style="letter-spacing:2px">[&deg;]</span>
                        </div>
                    </div>
                    <div>
                        <div><input id="module-axis-height" class="input-small" type="number" step="0.01" min="0" placeholder="[m]" required /></div>
                        <div><input id="module-tilt-max" class="input-small" type="number" step="0.1" min="0" max="359.9" placeholder="[ &deg; ]" required /></div>
                    </div>
                    <div>
                        <div class="header" style="padding-top: 10px;">
                            <span><?php echo _('Backtracking'); ?></span>
                        </div>
                        <div style="padding-top: 10px;">
                            <div id="module-backtrack" class='checkbox checkbox-slider--b-flat checkbox-slider-info'>
                                <label><input type='checkbox'><span></span></input></label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="module-mounting-settings" class="collapse">
                <div class="divider"></div>
                
                <div class="settings-title" style="padding-left: 18px;">
                    <span type="text"> <?php echo _('Mounting'); ?></span>
                    <span id="module-mounting-tooltip" data-toggle="tooltip" data-placement="right"
                            title="Placeholder description of mounting configurations.">
                        <svg class="icon icon-info">
                            <use xlink:href="#icon-question" />
                        </svg>
                    </span>
                </div>
                <div class="settings">
                    <div class="settings-header">
                        <div>
                            <span><?php echo _('Elevation'); ?></span><span class="required asterisk">&ast;</span>
                            <span class="unit">[m]</span>
                        </div>
                        <div>
                            <span><?php echo _('Azimuth'); ?></span><span class="required asterisk">&ast;</span>
                            <span class="unit" style="letter-spacing:2px">[&deg;]</span>
                        </div>
                        <div>
                            <span><?php echo _('Tilt'); ?></span><span class="required asterisk">&ast;</span>
                            <span class="unit" style="letter-spacing:2px">[&deg;]</span>
                        </div>
                    </div>
                    <div>
                        <div><input id="module-elevation" class="input-small" type="number" step="0.01" min="0" placeholder="[m]" required /></div>
                        <div><input id="module-azimuth" class="input-small" type="number" step="0.1" min="0" max="359.9" placeholder="[ &deg; ]" required /></div>
                        <div><input id="module-tilt" class="input-small" type="number" step="0.1" min="0" max="90" placeholder="[ &deg; ]" required /></div>
                    </div>
                </div>
            </div>
            <div class="divider"></div>
            
            <div id="module-rows-settings" class="settings">
                <div class="settings-title">
                    <span type="text"> <?php echo _('Rows'); ?></span>
                    <span id="module-rows-tooltip" data-toggle="tooltip" data-placement="right"
                            title="Placeholder description of the row count and pitch in meters.">
                        <svg class="icon icon-info">
                            <use xlink:href="#icon-question" />
                        </svg>
                    </span>
                </div>
                <div class="settings-header">
                    <div>
                        <span><?php echo _('Count'); ?></span><span class="required asterisk">&ast;</span>
                    </div>
                    <div>
                        <span><?php echo _('Pitch'); ?></span><span class="required asterisk">&ast;</span>
                        <span class="unit">[m]</span>
                    </div>
                </div>
                <div>
                    <div><input id="module-rows" class="input-small" type="number" step="1" min="1" placeholder="1" required /></div>
                    <div><input id="module-pitch" class="input-small" type="number" step="0.01" min="0.01" placeholder="[m]" required /></div>
                </div>
            </div>
            <div id="module-row-settings" class="settings">
                <div class="settings-header">
                    <div>
                        <span><?php echo _('Modules'); ?></span><span class="required asterisk">&ast;</span>
                    </div>
                    <div>
                        <span><?php echo _('Stack'); ?></span><span class="required asterisk">&ast;</span>
                    </div>
                    <div>
                        <span class="advanced" style="display: none;"><?php echo _('Gap'); ?></span>
                    </div>
                    <div></div>
                </div>
                <div>
                    <div><input id="module-count" class="input-small" type="number" step="1" min="1" placeholder="1" required /></div>
                    <div><input id="module-stack" class="input-small" type="number" step="1" min="1" max="9" required /></div>
                    <div><input id="module-gap" class="input-small advanced" type="number" min="0" step="0.1" placeholder="[m]" style="display: none;"></div>
                    <div class="fill">
                        <svg id="module-row-icon" class="icon icon-action" title="<?php echo _('Edit module stack gap'); ?>">
                            <use xlink:href="#icon-plus" />
                        </svg>
                    </div>
                </div>
            </div>
            <div class="divider"></div>
            
            <div class="module-settings settings" style="padding-left: 0;">
                <div>
                    <div class="settings-title" style="margin-right:8px; marign-bottom:20px">
                        <svg id="module-advanced-icon" class="icon icon-collapse">
                            <use xlink:href="#icon-chevron-right" />
                        </svg>
                        <span type="text">
                            <?php echo _('Module'); ?>
                        </span>
                        <span id="module-settings-tooltip" data-toggle="tooltip" data-placement="right"
                                title="Placeholder">
                            <svg class="icon icon-info">
                                <use xlink:href="#icon-question" />
                            </svg>
                        </span>
                    </div>
                    <div class="fill"></div>
                    <div>
                        <span class="description" type="text" style="margin-right:12px;"><?php echo _('Advanced'); ?></span>
                    </div>
                    <div id="module-advanced-mode" class="checkbox checkbox-slider--b-flat checkbox-slider-info">
                        <label style="margin:0px"><input type="checkbox" disabled><span style="cursor:not-allowed;"></span></input></label>
                    </div>
                </div>
                <div class="modules-info">
                    <div class="header">
                        <span><?php echo _('Orientation'); ?></span><span class="required asterisk">&ast;</span>
                    </div>
                    <div>
                        <select id="module-orientation" class="input-medium" type="text" style="width: 145px" required>
                            <option value='PORTRAIT'>Portrait</option>
                            <option value='LANDSCAPE'>Landscape</option>
                        </select>
                    </div>
                    <div></div>
                    <div></div>
                </div>
            </div>
            <div class="module-advanced settings" style="padding-top: 16px;">
                <div>
                    <div class="header" style="padding-right: 52px;">
                        <span><?php echo _('Type'); ?></span><span class="required asterisk">&ast;</span>
                    </div>
                    <div>
                        <div class="name">
                            <span id="module-model-manufacturer">
                                <?php echo _('Select a module type'); ?>
                            </span>
                            <svg class="icon icon-action" onclick="solar_configs.showSidebar()">
                                <title><?php echo _("Edit module type"); ?></title>
                                <use xlink:href="#icon-cog" />
                            </svg>
                        </div>
                    </div>
                </div>
                <div>
                    <div></div>
                    <div>
                        <div id="module-model-type" class="name"></div>
                        <p id="module-model-description" class="description"></p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="modal-footer">
        <span class="required pull-left"><span class="asterisk">&ast;</span><span class="description"><?php echo _('Required fields'); ?></span></span>
        <button id="module-config-cancel" class="btn btn-plain btn-default" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="module-config-delete" class="btn btn-plain btn-danger" style="cursor:pointer"><i class="icon-trash icon-white"></i> <?php echo _('Delete'); ?></button>
        <button id="module-config-save" class="btn btn-plain btn-primary"><?php echo _('Save'); ?></button>
    </div>
    <div id="module-config-loader" class="ajax-loader" style="display: none;"></div>
</div>

<div id="module-delete-modal" class="modal hide" tabindex="-1" role="dialog" aria-labelledby="module-delete-label" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="module-delete-label"></h3>
    </div>
    <div id="module-delete-body" class="modal-body delete">
        <div class="alert alert-error">
            <h4 class="alert-heading"><?php echo _('Deleting module configurations is permanent.'); ?></h4>
            <p><?php echo _('Are you sure you want to proceed?'); ?></p>
        </div>
        <p style="color: #999; margin: 10px 14px;">
            <?php echo _('This is a placeholder to explain what happens when module configurations are being deleted.'); ?>
        </p>
        <div id="module-delete-loader" class="ajax-loader" style="display: none;"></div>
    </div>
    <div class="modal-footer">
        <button id="module-delete-cancel" class="btn btn-plain btn-default" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="module-delete-confirm" class="btn btn-plain btn-danger"><i class="icon-trash icon-white"></i> <?php echo _('Delete'); ?></button>
    </div>
</div>

<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/dialogs/solar_configs.js"></script>
<script>
    $(window).resize(function() {
        solar_configs.adjustConfig();
    });
</script>
