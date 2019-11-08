<?php
    global $path;
?>

<div id="modules-config-modal" class="modal modal-adjust hide keyboard" tabindex="-1" role="dialog" aria-labelledby="modules-config-label" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="modules-config-label"></h3>
    </div>
    <div id="modules-config" class="modal-body sidebar">
        <div id="modules-config-sidebar" class="modal-sidebar">
            <div style="overflow-x: hidden; width:100%">
                <div id="modules-sidebar-models" class="accordion"></div>
            </div>
        </div>
        <div id="modules-config-content" class="modal-content">
            <p id="modules-config-description" class="description">
                <?php echo _('Placeholder for a short description of this dialog and what to do here.'); ?>
            </p>
            
            <div class="settings">
                <div class="settings-header">
                    <div><span><?php echo _('Count'); ?></span></div>
                    <div>
                        <span><?php echo _('Pitch'); ?></span>
                        <span id="modules-pitch-tooltip" data-toggle="tooltip" data-placement="right"
                                title="Placeholder description of the row count and pitch in meters.">
                            <svg class="icon icon-info">
                                <use xlink:href="#icon-question" />
                            </svg>
                        </span>
                    </div>
                </div>
                <div>
                    <div><input id="modules-count" class="input-small" type="number" step="1" min="1" required /></div>
                    <div><input id="modules-pitch" class="input-small" type="number" step="0.01" min="0" placeholder="[m]" /></div>
                </div>
            </div>
            <div class="settings" style="margin-top: 20px;">
                <div class="settings-title fill">
                    <span type="text"><?php echo _('Geometry'); ?></span>
                    <span id="modules-geometry-tooltip" data-toggle="tooltip" data-placement="right"
                            title="The modules azimuth, the horizontal angle measured clockwise from north, and the tilt from horizontal.">
                        <svg class="icon icon-info">
                            <use xlink:href="#icon-question" />
                        </svg>
                    </span>
                </div>
            </div>
            <div class="settings">
                <div class="settings-header">
                    <div><span><?php echo _('Azimuth'); ?></span></div>
                    <div><span><?php echo _('Tilt'); ?></span></div>
                    <div><span><?php echo _('Elevation'); ?></span></div>
                </div>
                <div>
                    <div><input id="modules-azimuth" class="input-small" type="number" step="0.1" min="0" max="359.9" placeholder="[ &deg; ]" required /></div>
                    <div><input id="modules-tilt" class="input-small" type="number" step="0.1" min="0" max="90" placeholder="[ &deg; ]" required /></div>
                    <div><input id="modules-elevation" class="input-small" type="number" step="0.01" min="0" placeholder="[m]" /></div>
                </div>
            </div>
            <div class="divider"></div>
            
            <div class="modules-settings settings" style="padding-left: 0;">
                <div>
                    <div class="settings-title fill">
                        <svg id="settings-collapse-icon" class="icon icon-collapse">
                            <use xlink:href="#icon-chevron-right" />
                        </svg>
                        <span type="text"><?php echo _('Module'); ?></span>
                        <span id="modules-settings-tooltip" data-placement="right"
                                title="Placeholder">
                            <svg class="icon icon-info">
                                <use xlink:href="#icon-question" />
                            </svg>
                        </span>
                    </div>
                    <div class="menu dropdown action" @click.prevent>
                        <svg class="dropdown-toggle icon icon-advanced" data-toggle="dropdown">
                            <use xlink:href="#icon-dots-vertical" />
                        </svg>
                        <ul class="dropdown-menu pull-right">
                            <li><a @click.prevent.stop><?php echo _("Edit model"); ?></a></li>
                            <li><a @click.prevent.stop><?php echo _("Advanced settings"); ?></a></li>
                        </ul>
                    </div>
                </div>
            	<div>
            		<div style="padding: 10px 0 0 18px;">
                        <span id="modules-type" class="name"><?php echo _('Placeholder name'); ?></span>
                    	<p id="modules-description" class="description"><?php echo _('Placeholder description'); ?></p>
            		</div>
            	</div>
            </div>
        </div>
    </div>
    <div class="modal-footer">
        <button id="modules-config-cancel" class="btn btn-plain btn-default" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="modules-config-delete" class="btn btn-plain btn-danger" style="cursor:pointer"><i class="icon-trash icon-white"></i> <?php echo _('Delete'); ?></button>
        <button id="modules-config-save" class="btn btn-plain btn-primary"><?php echo _('Save'); ?></button>
    </div>
</div>

<div id="modules-delete-modal" class="modal hide" tabindex="-1" role="dialog" aria-labelledby="modules-delete-label" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="modules-delete-label"></h3>
    </div>
    <div id="modules-delete-body" class="modal-body delete">
        <div class="alert alert-error">
            <h4 class="alert-heading"><?php echo _('Deleting modules is permanent.'); ?></h4>
            <p><?php echo _('Are you sure you want to proceed?'); ?></p>
        </div>
        <p style="color: #999; margin: 10px 14px;">
            <?php echo _('This is a placeholder to explain what happens when modules are being deleted.'); ?>
        </p>
        <div id="modules-delete-loader" class="ajax-loader" style="display: none;"></div>
    </div>
    <div class="modal-footer">
        <button id="modules-delete-cancel" class="btn btn-plain btn-default" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="modules-delete-confirm" class="btn btn-plain btn-danger"><i class="icon-trash icon-white"></i> <?php echo _('Delete'); ?></button>
    </div>
</div>

<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/dialogs/solar_modules.js"></script>
