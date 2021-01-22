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
            <p class="description">
                <?php echo _('Configuration variants each specify an optical simulation, generating DC power output for a single module.'); ?>
                <br style="margin-bottom: 6px;">
                <?php echo _('Each variant revolves around a specified <em>module model</em>, either from a selection of prepared available modules, or entered manually from datasheet values.'); ?>
            </p>
            <div id="module-tracking-header" class="settings" style="padding-left: 0; margin-top: 10px;">
                <div class="settings-title settings-collapse fill">
                    <svg id="module-tracking-icon" class="icon icon-collapse">
                        <use xlink:href="#icon-chevron-right" />
                    </svg>
                    <span type="text">
                        <?php echo _('Tracking'); ?>
                    </span>
                    <span id="module-tracking-tooltip" data-toggle="tooltip" data-placement="right"
                            title="Configures the <b>horizontal single axis tracking</b>, with the axis in north-south direction.<br>
                                   If not enabled, fixed tilt mounting applies."
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
            <div id="module-mounting-settings" class="collapse in">
                <div class="divider"></div>
                
                <div class="settings-title" style="padding-left: 18px;">
                    <span type="text"> <?php echo _('Mounting'); ?></span>
                    <span id="module-mounting-tooltip" data-toggle="tooltip" data-placement="right"
                            title="The <b>fixed tilt</b> mounting, specifyimg the <b>azimuth</b> and <b>elevation</b> from ground up to the lower edge of lower module.<br>
                                   The azimuth is configured from north, applied for both hemispheres.">
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
            <div id="module-losses-settings" class="collapse">
                <div class="settings-title settings-collapse" style="padding-top: 10px;">
                    <svg id="module-losses-icon" class="icon icon-collapse" data-show=false>
                        <use xlink:href="#icon-chevron-right" />
                    </svg>
                    <span type="text"> <?php echo _('Losses'); ?></span>
                    <span id="module-losses-tooltip" data-toggle="tooltip" data-placement="right"
                            title="Thermal loss parameters for the <b>Faiman model</b>.">
                        <svg class="icon icon-info">
                            <use xlink:href="#icon-question" />
                        </svg>
                    </span>
                </div>
                <div id="module-losses" class="collapse">
                    <div class="settings">
                        <div class="settings-header">
                            <div>
                                <span type="text" style="font-size: 15px"><?php echo _('Constant'); ?></span><br>
                                <span>&mu;<sub>c</sub></span>
                                <span class="unit">[W/m<sup>2</sup>*K]</span>
                            </div>
                            <div>
                                <span type="text" style="font-size: 15px"><?php echo _('Wind'); ?></span><br>
                                <span>&mu;<sub>v</sub></span>
                                <span class="unit">[W/m<sup>2</sup>*K/m/s]</span>
                            </div>
                        </div>
                        <div>
                            <div><input id="module-loss-constant" class="input-small" type="number" step=any placeholder="31" /></div>
                            <div><input id="module-loss-wind" class="input-small" type="number" step=any placeholder="0" /></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="divider"></div>
            
            <div id="module-rows-settings" class="settings">
                <div class="settings-title">
                    <span type="text"> <?php echo _('Rows'); ?></span>
                </div>
                <div class="settings-header">
                    <div>
                        <span><?php echo _('Number'); ?><span style="color: #aaa; font-size: 12px"><?php echo _(' of rows'); ?></span><span class="required asterisk">&ast;</span>
                    </div>
                    <div>
                        <span><?php echo _('Pitch'); ?><span style="color: #aaa; font-size: 12px"><?php echo _(' row to row'); ?></span></span><span class="required asterisk">&ast;</span>
                        <span class="unit">[m]</span>
                    </div>
                </div>
                <div>
                    <div><input id="module-rows" class="input-small" type="number" step="1" min="1" required /></div>
                    <div><input id="module-pitch" class="input-small" type="number" step="0.01" min="0.01" placeholder="[m]" required /></div>
                </div>
            </div>
            <div id="module-row-settings" class="settings">
                <div class="settings-header">
                    <div>
                        <span><?php echo _('Modules'); ?><span style="color: #aaa; font-size: 12px"><?php echo _(' per row'); ?></span><span class="required asterisk">&ast;</span></span>
                    </div>
                    <div>
                        <span class="advanced" style="display: none;"><?php echo _('Stacked'); ?><span style="font-size: 12px"><?php echo _(' modules'); ?></span></span>
                    </div>
                    <div>
                        <span class="advanced" style="display: none;"><?php echo _('Stack gap'); ?></span>
                    </div>
                    <div></div>
                </div>
                <div>
                    <div><input id="module-count" class="input-small" type="number" step="1" min="1" required /></div>
                    <div><input id="module-stack" class="input-small advanced" type="number" step="1" min="1" max="9" style="display: none;" /></div>
                    <div><input id="module-stack-gap" class="input-small advanced" type="number" min="0" step="0.1" placeholder="[m]" style="display: none;"></div>
                    <div class="fill">
                        <svg id="module-row-icon" class="icon icon-action" title="<?php echo _('Edit module stack gap'); ?>">
                            <use xlink:href="#icon-plus" />
                        </svg>
                    </div>
                </div>
            </div>
            <div class="settings">
                <div class="settings-header">
                    <div>
                        <span><?php echo _('Orientation'); ?></span><span class="required asterisk">&ast;</span>
                    </div>
                </div>
                <div>
                    <div>
                        <select id="module-orientation" class="input-medium" type="text" style="width: 120px;" required>
                            <option value='PORTRAIT'>Portrait</option>
                            <option value='LANDSCAPE'>Landscape</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="divider"></div>
            
            <div id="module-param-header" class="module-settings settings" style="padding-left: 0;">
                <div>
                    <div class="settings-title settings-collapse fill" style="margin-right:8px; marign-bottom:20px">
                        <svg id="module-advanced-icon" class="icon icon-collapse">
                            <use xlink:href="#icon-chevron-right" />
                        </svg>
                        <span type="text"><?php echo _('Module'); ?></span>
                        <span id="module-settings-tooltip" data-toggle="tooltip" data-placement="right"
                                title="Modules represent to concrete models, specified by values as available in manufacturer <b>datasheets</b>.<br>
                                       By enabling the <b>advanced</b> configurations, parameters may be entered manually.">
                            <svg class="icon icon-info">
                                <use xlink:href="#icon-question" />
                            </svg>
                        </span>
                    </div>
                    <div>
                        <span class="description" type="text" style="margin-right:12px;"><?php echo _('Advanced'); ?></span>
                    </div>
                    <div id="module-advanced-mode" class="checkbox checkbox-slider--b-flat checkbox-slider-info">
                        <label style="margin:0px"><input type="checkbox"><span></span></input></label>
                    </div>
                </div>
            </div>
            <div id="module-param-advanced" class="collapse">
                <div class="settings">
                    <div class="settings-header">
                        <div>
                            <span><?php echo _('Length'); ?></span><span class="required asterisk">&ast;</span>
                            <span class="unit">[m]</span>
                        </div>
                        <div>
                            <span><?php echo _('Width'); ?></span><span class="required asterisk">&ast;</span>
                            <span class="unit">[m]</span>
                        </div>
                        <div>
                            <span><?php echo _('Cells'); ?><span style="font-size: 12px"><?php echo _(' in series'); ?></span></span>
                            <span class="required asterisk">&ast;</span>
                        </div>
                    </div>
                    <div>
                        <div><input id="module-param-length" class="input-small" type="number" step="0.001" min="0" placeholder="[m]" required /></div>
                        <div><input id="module-param-width" class="input-small" type="number" step="0.001" min="0" placeholder="[m]" required /></div>
                        <div><input id="module-param-cells" class="input-small" type="number" step="1" min="1"required /></div>
                    </div>
                </div>
                <div id="module-bifi-settings" class="settings">
                    <div class="settings-header">
                        <div style="width: 116px">
                            <span><?php echo _('Bifaciality'); ?></span><span class="required asterisk">&ast;</span></span>
                        </div>
                        <div>
                            <span class="advanced" style="display: none;"><?php echo _('Factor'); ?></span>
                            <span class="advanced unit" style="display: none; letter-spacing:1px">[0,1]</span>
                        </div>
                    </div>
                    <div>
                        <div>
                            <div id="module-bifi-select" class='checkbox checkbox-slider--b-flat checkbox-slider-info'>
                                <label><input type='checkbox'><span></span></input></label>
                            </div>
                        </div>
                        <div>
                            <input id="module-bifi-factor" class="input-small advanced" type="number" step="0.01" min="0" max="1" style="display: none;" />
                        </div>
                    </div>
                    <div class="settings-header">
                        <div class="header">
                            <span type="text"><?php echo _('Surface'); ?></span><span class="required asterisk">&ast;</span>
                            <span type="text" class="advanced pull-right" style="display:none; font-size: 14px; padding-right: 8px;">(Front)</span>
                        </div>
                        <div>
                            <select id="module-surface-front" class="input-large" type="text" required>
                                <option value='Glass-AR' selected>Glass (Anti-reflective)</option>
                                <option value='Glass'>Glass</option>
                            </select>
                        </div>
                    </div>
                    <div class="settings-header advanced" style="display: none;">
                        <div class="header">
                            <span type="text" class="advanced pull-right" style="display:none; font-size: 14px; padding-right: 8px;">(Back)</span>
                        </div>
                        <div>
                            <select id="module-surface-back" class="input-large" type="text" required>
                                <option value='Glass-AR'>Glass (Anti-reflective)</option>
                                <option value='Glass' selected>Glass</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div id="module-tech-settings" class="settings">
                    <div class="settings-header">
                        <div></div>
                        <div></div>
                        <div style="padding-right: 0px;">
                            <span class="advanced" style="display: none;"><?php echo _('Ideality factor'); ?></span>
                        </div>
                    </div>
                    <div>
                        <div class="header" style="width: 116px;">
                            <span><?php echo _('Technology'); ?></span><span class="required asterisk">&ast;</span>
                        </div>
                        <div>
                            <select id="module-technology" class="input-large" type="text" style="margin-right: 12px;" required>
                                <option value='Mono-c-Si'>Monocrystalline silicon</option>
                                <option value='Multi-c-Si'>Multicrystalline silicon</option>
                            </select>
                        </div>
                        <div><input id="module-ideality-factor" class="input-small advanced" type="number" step="any" min="0" style="display: none;" /></div>
                        <div>
                            <svg id="module-tech-icon" class="icon icon-action" title="<?php echo _('Edit diode ideality factor'); ?>">
                                <use xlink:href="#icon-plus" />
                            </svg>
                        </div>
                    </div>
                </div>
                <div class="settings-header" style="padding-top: 18px; padding-left: 18px;">
                    <span type="text" style="font-weight: bold;"><?php echo _('Electrical'); ?></span>
                    <span type="text" style="font-size: 12px;"><?php echo _(' at STC'); ?></span>
                    <span id="module-params-tooltip" data-toggle="tooltip" data-placement="right"
                            title="<b>I/V parameters</b> measured at STC under front side illumination.<br>
                                   &mu;<sub>mpp</sub> and &alpha;<sub>sc</sub> are temperature coefficients for P<sub>mpp</sub> and I<sub>sc</sub>">
                        <svg class="icon icon-info">
                            <use xlink:href="#icon-question" />
                        </svg>
                    </span>
                </div>
                <div class="settings">
                    <div class="settings-header">
                        <div>
                            <span>V<sub>mpp</sub></span><span class="required asterisk">&ast;</span>
                            <span class="unit">[V]</span>
                        </div>
                        <div>
                            <span>I<sub>mpp</sub></span><span class="required asterisk">&ast;</span>
                            <span class="unit">[A]</span>
                        </div>
                        <div>
                            <span>&mu;<sub>mpp</sub></span><span class="required asterisk">&ast;</span>
                            <span class="unit">[%/&deg;C]</span>
                        </div>
                    </div>
                    <div>
                        <div><input id="module-param-vmpp" class="input-small" type="number" step="0.001" min="0" placeholder="[V]" required /></div>
                        <div><input id="module-param-impp" class="input-small" type="number" step="0.001" min="0" placeholder="[A]" required /></div>
                        <div><input id="module-param-mu-p" class="input-small" type="number" step="any" required /></div>
                    </div>
                    <div class="settings-header">
                        <div>
                            <span>V<sub>oc</sub></span><span class="required asterisk">&ast;</span>
                            <span class="unit">[V]</span>
                        </div>
                        <div>
                            <span>I<sub>sc</sub></span><span class="required asterisk">&ast;</span>
                            <span class="unit">[A]</span>
                        </div>
                        <div>
                            <span>&alpha;<sub>sc</sub></span><span class="required asterisk">&ast;</span>
                            <span class="unit">[%/&deg;C]</span>
                        </div>
                    </div>
                    <div>
                        <div><input id="module-param-voc" class="input-small" type="number" step="0.001" min="0" placeholder="[V]" required /></div>
                        <div><input id="module-param-isc" class="input-small" type="number" step="0.001" min="0" placeholder="[A]" required /></div>
                        <div><input id="module-param-alpha-sc" class="input-small" type="number" step="any" required /></div>
                    </div>
                </div>
            </div>
            <div id="module-param-settings" class="module-info collapse in">
                <div class="settings">
                    <div class="settings-header">
                        <div class="header" style="padding-right: 30px;">
                            <span><?php echo _('Type'); ?></span><span class="required asterisk">&ast;</span>
                        </div>
                        <div>
                            <div class="name">
                                <span id="module-model-manufacturer">
                                    <?php echo _('Select a module type'); ?>
                                </span>
                                <svg class="icon icon-action" onclick="solar_configs.showSidebar()">
                                    <title><?php echo _("Edit module type"); ?></title>
                                    <use xlink:href="#icon-wrench" />
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
            <?php echo _('Deleting a configuration variant will not remove any results, up until the project will be simulated again.'); ?><br>
            <?php echo _('Make sure you saved all files you need.'); ?>
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
