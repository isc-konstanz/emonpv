<?php
    global $path;
?>

<div id="inverter-config-modal" class="modal modal-adjust hide keyboard" tabindex="-1" role="dialog" aria-labelledby="inverter-config-modal" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="inverter-config-label"></h3>
    </div>
    <div id="inverter-config" class="modal-body">
        <div id="inverter-config-content" class="modal-content">
            <p class="description">
                <?php echo _('Inverters each specify the AC conversion for one or several strings of modules, connected to the DC inputs.'); ?>
                <br style="margin-bottom: 6px;">
                <?php echo _('Each inverter revolves around a specified <em>inverter model</em>, either from a selection of prepared available inverters, or entered manually from datasheet values.'); ?>
            </p>
            <div class="settings">
                <div class="settings-header">
                    <div>
                        <span class="title"><?php echo _('Count'); ?></span>
                        <span id="inverter-count-tooltip" data-toggle="tooltip" data-placement="right" 
                                title="">
                            <svg class="icon icon-info">
                                <use xlink:href="#icon-question" />
                            </svg>
                        </span>
                    </div>
                </div>
                <div>
                    <div><input id="inverter-count" class="input-small" type="number" step="1" min="1" required /></div>
                </div>
            </div>
            <div class="divider"></div>
            
            <div id="inverter-param-header" class="inverter-settings settings" style="padding-left: 0;">
                <div>
                    <div class="settings-title settings-collapse fill" style="margin-right:8px; marign-bottom:20px">
                        <svg id="inverter-advanced-icon" class="icon icon-collapse">
                            <use xlink:href="#icon-chevron-down" />
                        </svg>
                        <span type="text"><?php echo _('Model'); ?></span>
                        <span id="inverter-settings-tooltip" data-toggle="tooltip" data-placement="right"
                                title="Inverters represent to concrete models, specified by values as available in manufacturer <b>datasheets</b>.<br>
                                       By enabling the <b>advanced</b> configurations, parameters may be entered manually.">
                            <svg class="icon icon-info">
                                <use xlink:href="#icon-question" />
                            </svg>
                        </span>
                    </div>
                    <!-- div>
                        <span class="description" type="text" style="margin-right:12px;"><?php echo _('Advanced'); ?></span>
                    </div>
                    <div id="inverter-advanced-mode" class="checkbox checkbox-slider--b-flat checkbox-slider-info">
                        <label style="margin:0px"><input type="checkbox"><span></span></input></label>
                    </div -->
                </div>
            </div>
            <div id="inverter-param-advanced" class="collapse in">
                <div class="settings">
                    <div class="settings-header">
                        <div>
                            <span><?php echo _('Nominal power'); ?></span><span class="required asterisk">&ast;</span>
                            <span class="unit">[kW]</span>
                        </div>
                    </div>
                    <div>
                        <div><input id="inverter-param-power" class="input-small" type="number" step="0.001" min="0" placeholder="[kW]" required /></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="modal-footer">
        <span class="required pull-left"><span class="asterisk">&ast;</span><span class="description"><?php echo _('Required fields'); ?></span></span>
        <button id="inverter-config-cancel" class="btn btn-plain btn-default" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="inverter-config-delete" class="btn btn-plain btn-danger" style="display: none; cursor: pointer;"><i class="icon-trash icon-white"></i> <?php echo _('Delete'); ?></button>
        <button id="inverter-config-save" class="btn btn-plain btn-primary" disabled><?php echo _('Save'); ?></button>
    </div>
    <div id="inverter-config-loader" class="ajax-loader" style="display: none;"></div>
</div>

<div id="inverter-delete-modal" class="modal hide" tabindex="-1" role="dialog" aria-labelledby="inverter-delete-label" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="inverter-delete-label"></h3>
    </div>
    <div id="inverter-delete-body" class="modal-body delete">
        <div class="alert alert-error">
            <h4 class="alert-heading"><?php echo _('Deleting an inverter is permanent.'); ?></h4>
            <p><?php echo _('Are you sure you want to proceed?'); ?></p>
        </div>
        <p style="color: #999; margin: 10px 14px;">
            <?php echo _('Deleting a inverter will remove all corresponding configuration variants, including simulated results.'); ?><br>
            <?php echo _('Make sure you saved all files you need.'); ?>
        </p>
        <div id="inverter-delete-loader" class="ajax-loader" style="display: none;"></div>
    </div>
    <div class="modal-footer">
        <button id="inverter-delete-cancel" class="btn btn-plain btn-default" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="inverter-delete-confirm" class="btn btn-plain btn-danger"><i class="icon-trash icon-white"></i> <?php echo _('Delete'); ?></button>
    </div>
</div>

<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/dialogs/solar_inverter.js"></script>
<script>
    $(window).resize(function() {
        solar_inverter.adjustConfig();
    });
</script>
