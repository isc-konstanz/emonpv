<?php
    global $path;
?>
<link rel="stylesheet" href="<?php echo $path; ?>Modules/solar/libs/leaflet/leaflet.css"/>
<link rel="stylesheet" href="<?php echo $path; ?>Modules/solar/libs/leaflet/search/leaflet-search.min.css"/>

<div id="system-config-modal" class="modal hide keyboard" tabindex="-1" role="dialog" aria-labelledby="system-config-modal" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="system-config-label"></h3>
    </div>
    <div class="modal-body">
    	<p id="" class="description">
    		<?php echo _('Placeholder for a short description of this dialog and what to do here.'); ?>
		</p>
		
        <div class="settings">
            <div>
            	<div>
                	<select id="system-model" class="select-large select-default" type="text" required>
                	    <option value='' hidden='true' selected><?php echo _('Select simulation model'); ?></option>
                	    <option value='mobidig'>MoBiDiG</option>
                	    <option value='pvlib'>Pvlib</option>
                	</select>
            	</div>
                <div id="system-model-tooltip" style="display: none;" data-toggle="tooltip" data-placement="bottom">
                    <svg class="icon icon-info">
                        <use xlink:href="#icon-question" />
                    </svg>
                </div>
        	</div>
        </div>
        <div class="settings">
            <div class="settings-header">
        		<div>
        			<span class="title"><?php echo _('Name'); ?></span>
                    <span id="system-name-tooltip" data-toggle="tooltip" data-placement="right"
                    		title="The name should work as a unique identifier for the system to be able to distinguish different systems. 
                    				Additionally, an optional description may be added to provide descriptive comments regarding the specific system.">
                        <svg class="icon icon-info">
                            <use xlink:href="#icon-question" />
                        </svg>
                    </span>
    			</div>
            </div>
            <div>
                <div>
                	<input id="system-name" class="input-large" type="text" 
                			pattern="[a-zA-Z\x7f-\xff0-9-_. ]+" required />
        		</div>
                <div>
                    <input id="system-description" class="input-large" type="text" style="display: none;"
                    		pattern="[a-zA-Z\x7f-\xff0-9-_. ]+" placeholder="<?php echo _('Description'); ?>" />
                </div>
                <div>
                    <svg id="system-description-icon" class="icon icon-action" title="<?php echo _('Add description'); ?>">
                        <use xlink:href="#icon-plus" />
                    </svg>
                </div>
            </div>
        </div>
        <div class="divider"></div>
        
        <div class="settings" style="padding-left: 0;">
        	<div class="settings-collapse">
                <div class="settings-title fill">
                    <svg id="settings-collapse-icon" class="icon icon-collapse">
                        <use xlink:href="#icon-chevron-right" />
                    </svg>
                    <span type="text"><?php echo _('Location'); ?></span>
                    <span id="system-location-tooltip" data-toggle="tooltip" data-placement="right"
                    		title="Advanced configurations for the geographic coordinates <b>longitude</b> and <b>latitude</b>. 
                					Additionally, the optional altitude and albedo of the solar system may be specified.">
                        <svg class="icon icon-info">
                            <use xlink:href="#icon-question" />
                        </svg>
                    </span>
                </div>
                <div>
                    <svg id="system-location-icon" class="icon icon-advanced">
                        <use xlink:href="#icon-cog" />
                    </svg>
                </div>
        	</div>
        </div>
        <div id="system-location" style="display: none;">
            <div class="settings">
                <div class="settings-header">
                    <div><span><?php echo _('Latitude'); ?></span></div>
                    <div><span><?php echo _('Longitude'); ?></span></div>
                    <div><span class="advanced" style="display: none;"><?php echo _('Altitude'); ?></span></div>
                    <div><span class="advanced" style="display: none;"><?php echo _('Albedo'); ?></span></div>
                    <div></div>
                </div>
                <div>
                    <div><input id="system-latitude" class="input-small" type="number" step="0.00001" required></div>
                    <div><input id="system-longitude" class="input-small" type="number" step="0.00001" required></div>
                    <div><input id="system-altitude" class="input-small advanced" type="number" step="0.1" style="display: none;"></div>
                    <div><input id="system-albedo" class="input-small advanced" type="number" step="0.01" style="display: none;"></div>
                    <div class="fill">
                        <svg id="system-coordinates-icon" class="icon icon-action" title="<?php echo _('Edit altitude and albedo'); ?>">
                            <use xlink:href="#icon-plus" />
                        </svg>
                    </div>
                </div>
            </div>
        </div>
        <div id="system-map" class="system-map"></div>
    </div>
    <div class="modal-footer">
        <button id="system-config-cancel" class="btn btn-plain btn-default" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="system-config-delete" class="btn btn-plain btn-danger" style="display: none; cursor: pointer;"><i class="icon-trash icon-white"></i> <?php echo _('Delete'); ?></button>
        <button id="system-config-save" class="btn btn-plain btn-primary" disabled><?php echo _('Save'); ?></button>
    </div>
    <div id="system-config-loader" class="ajax-loader" style="display: none;"></div>
</div>

<div id="system-delete-modal" class="modal hide" tabindex="-1" role="dialog" aria-labelledby="system-delete-label" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="system-delete-label"></h3>
    </div>
    <div id="system-delete-body" class="modal-body">
        <p>
            <?php echo _('Deleting a solar system is permanent.'); ?>
        </p>
        <p style="color: #999;">
            <?php echo _('This is a placeholder to explain what happens when a system is deleted.'); ?>
        </p>
        <p>
            <?php echo _('Are you sure you want to proceed?'); ?>
        </p>
        <div id="system-delete-loader" class="ajax-loader" style="display: none;"></div>
    </div>
    <div class="modal-footer">
        <button id="system-delete-cancel" class="btn" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="system-delete-confirm" class="btn btn-primary"><?php echo _('Delete permanently'); ?></button>
    </div>
</div>

<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/libs/leaflet/leaflet.js"></script>
<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/libs/leaflet/search/leaflet-search.src.js"></script>
<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/dialogs/solar_system.js"></script>