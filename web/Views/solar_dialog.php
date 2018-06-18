<?php
    global $path;
?>

<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/Views/solar_dialog.js"></script>

<style>
    /* For Firefox */
    input[type='number'] {
        -moz-appearance:textfield;
    }

    /* Webkit browsers like Safari and Chrome */
    input[type=number]::-webkit-inner-spin-button,
    input[type=number]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }

    .module-body tr:hover > td {
        background-color: #44b3e2;
    }

    .module-selected {
        background-color: #209ed3;
        color: #fff;
    }

    .modal-adjust {
        width: 60%; left:20%; /* (100%-width)/2 */
        margin-left: auto; margin-right: auto;
        overflow-y: hidden;
    }

    .modal-adjust .modal-body {
        max-height: none;
        overflow-y: hidden;
    }

    .system-info .tooltip-inner {
        max-width: 500px;
    }

    .sidebar-wrapper {
        position: absolute;
        margin-top: -15px;
        margin-left: -15px;
        max-height: none;
        height: 100%;
        width: 250px;
        overflow-y: auto;
        background-color: #eee;
        z-index: 1000;
    }

    .content-wrapper {
        position: absolute;
        right: 15px;
        left: 15px;
        height: 100%;
        max-height: none;
        overflow-y: auto;
    }

    .content-wrapper .divider {
        *width: 100%;
        height: 1px;
        margin: 9px 1px;
        *margin: -5px 0 5px;
        overflow: hidden;
        background-color: #e5e5e5;
        border-bottom: 1px solid #ffffff;
    }

    #system-location th, 
    #module-orientation th, 
    #module-count th {
        text-align: left;
        font-weight: normal;
        color: #888;
    }
    #system-location td:nth-of-type(1) { width:109px; text-align:left; }
    #system-location td:nth-of-type(2) { width:109px; text-align:left; }
    #system-location td:nth-of-type(3) { width:107px; text-align:left; }
    #system-location td:nth-of-type(4) { width:14px; text-align:center; }

    #system-modules-table td:nth-of-type(1) { width:20%; }
    #system-modules-table th:nth-of-type(4), td:nth-of-type(4) { width:5%; text-align:right; }
    #system-modules-table td:nth-of-type(5) { width:14px; text-align:center; }
    #system-modules-table td:nth-of-type(6) { width:14px; text-align:center; }

    #system-init-modal table td { text-align: left; }

    #system-init-feeds table td:nth-of-type(1) { width:14px; text-align:center; }
    #system-init-feeds table td:nth-of-type(2) { width:5%; }
    #system-init-feeds table td:nth-of-type(3) { width:15%; }
    #system-init-feeds table td:nth-of-type(4) { width:25%; }

    #system-init-inputs table td:nth-of-type(1) { width:14px; text-align:center; }
    #system-init-inputs table td:nth-of-type(2) { width:5%; }
    #system-init-inputs table td:nth-of-type(3) { width:5%; }
    #system-init-inputs table td:nth-of-type(4) { width:10%; }
    #system-init-inputs table td:nth-of-type(5) { width:25%; }
    
    #module-orientation td:nth-of-type(1), #module-count td:nth-of-type(1) { width:117px; text-align:left; }
    #module-orientation td:nth-of-type(2), #module-count td:nth-of-type(2) { width:107px; text-align:left; }
    #module-orientation td:nth-of-type(3), #module-count td:nth-of-type(3) { width:14px; text-align:center; }
    
    #module-modal {
        width: 60%; left:20%; /* (100%-width)/2 */
    }
    
    #module-content {
        margin-top: -15px;
    }
</style>

<div id="system-modal" class="modal hide keyboard modal-adjust" tabindex="-1" role="dialog" aria-labelledby="system-modal-label" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="system-modal-label"><?php echo _('Configure Solar System'); ?></h3>
    </div>
    <div id="system-body" class="modal-body">
        <div id="system-content" class="content-wrapper" style="max-width:1280px">
            
            <label><b><?php echo _('Name'); ?></b></label>
            <input id="system-name" class="input-large" type="text" required>
            <span id="system-name-tooltip" data-toggle="tooltip" data-placement="bottom">
                <i class="icon-info-sign" style="vertical-align:top; margin-top:8px; margin-left:2px; cursor:pointer;"></i>
            </span>
            
            <label><b><?php echo _('Description'); ?></b></label>
            <input id="system-description" class="input-large" type="text">
            <span id="system-description-tooltip" data-toggle="tooltip" data-placement="bottom">
                <i class="icon-info-sign" style="vertical-align:top; margin-top:8px; margin-left:2px; cursor:pointer;"></i>
            </span>
            
            <div class="divider"></div>
            
            <label><b><?php echo _('Location'); ?></b></label>
            <table id="system-location">
                <tr>
                    <th><?php echo _('Latitude'); ?></th>
                    <th><?php echo _('Longitude'); ?></th>
                    <th><?php echo _('Altitude'); ?></th>
                    <th></th>
                </tr>
				<tr>
					<td><input id="system-latitude" class="input-small" type="number" step="0.00001" required></td>
					<td><input id="system-longitude" class="input-small" type="number" step="0.00001" required></td>
					<td><input id="system-altitude" class="input-small" type="number" required></td>
					<td>
                        <span id="system-location-tooltip" data-toggle="tooltip" data-placement="bottom">
                            <i class="icon-info-sign" style="margin-bottom:12px; cursor:pointer;"></i>
                        </span>
                    </td>
				</tr>
            </table>
            
            <label><b><?php echo _('Modules'); ?></b></label>
            <table id="system-modules-table" class="table table-hover"></table>
            <div id="system-modules-none" class="alert" style="display:none"><?php echo _('You have no modules configured'); ?></div>
            
            <button id="system-modules-add" class="btn btn-small" >&nbsp;<i class="icon-plus-sign" ></i>&nbsp;<?php echo _('Add modules'); ?></button>
        </div>
    </div>
    <div class="modal-footer">
        <button id="system-cancel" class="btn" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="system-delete" class="btn btn-danger" style="cursor:pointer"><i class="icon-trash icon-white"></i> <?php echo _('Delete'); ?></button>
        <button id="system-init" class="btn btn-primary"><i class="icon-refresh icon-white"></i> <?php echo _('Initialize'); ?></button>
        <button id="system-save" class="btn btn-primary"><?php echo _('Save'); ?></button>
    </div>
</div>

<div id="system-init-modal" class="modal hide keyboard modal-adjust" tabindex="-1" role="dialog" aria-labelledby="system-init-modal-label" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="system-init-modal-label"><?php echo _('Initialize Solar System'); ?></h3>
    </div>
    <div id="system-init-body"  class="modal-body">
        <div id="system-init-content" class="content-wrapper" style="max-width:1280px">
            <p><?php echo _('Initializing a system will automaticaly configure inputs and associated feeds.'); ?><br>
                <b><?php echo _('Warning: '); ?></b><?php echo _('Process lists with dependencies to deselected feeds or inputs will be skipped as a whole'); ?>
            </p>
            
            <div id="system-init-feeds" style="display:none">
                <label><b><?php echo _('Feeds'); ?></b></label>
                <table class="table table-hover">
                    <tr>
                        <th></th>
                        <th></th>
                        <th><?php echo _('Tag'); ?></th>
                        <th><?php echo _('Name'); ?></th>
                        <th><?php echo _('Process list'); ?></th>
                    </tr>
                    <tbody id="system-init-feeds-table"></tbody>
                </table>
            </div>
            
            <div id="system-init-inputs" style="display:none">
                <label><b><?php echo _('Inputs'); ?></b></label>
                <table class="table table-hover">
                    <tr>
                        <th></th>
                        <th></th>
                        <th><?php echo _('Node'); ?></th>
                        <th><?php echo _('Key'); ?></th>
                        <th><?php echo _('Name'); ?></th>
                        <th><?php echo _('Process list'); ?></th>
                    </tr>
                    <tbody id="system-init-inputs-table"></tbody>
                </table>
            </div>
        </div>
    </div>
    <div class="modal-footer">
        <button id="system-init-cancel" class="btn" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="system-init-confirm" class="btn btn-primary"><?php echo _('Initialize'); ?></button>
    </div>
</div>

<div id="system-delete-modal" class="modal hide" tabindex="-1" role="dialog" aria-labelledby="system-delete-modal-label" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="system-delete-modal-label"><?php echo _('Delete Solar System'); ?></h3>
    </div>
    <div class="modal-body">
        <p><?php echo _('Deleting a system is permanent and no further forecasts will be calculated.'); ?>
           <br><br>
           <?php echo _('Inputs and Feeds that this system uses are not deleted and all historic data is kept. To remove them, delete them manualy afterwards.'); ?>
           <br><br>
           <?php echo _('Are you sure you want to delete?'); ?>
        </p>
    </div>
    <div class="modal-footer">
        <button class="btn" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="system-delete-confirm" class="btn btn-primary"><?php echo _('Delete permanently'); ?></button>
    </div>
</div>

<div id="module-modal" class="modal hide keyboard modal-adjust" tabindex="-1" role="dialog" aria-labelledby="module-modal-label" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="module-modal-label"><?php echo _('Configure Solar Module'); ?></h3>
    </div>
    <div id="module-body" class="modal-body">
        <div id="module-sidebar" class="sidebar-wrapper">
            <div style="padding-left:10px;">
                <div id="module-sidebar-close" style="float:right; cursor:pointer; padding:10px;"><i class="icon-remove"></i></div>
                <h3><?php echo _('Modules'); ?></h3>
            </div>
            <div style="overflow-x: hidden; background-color:#f3f3f3; width:100%">
                <table id="module-table" class="table"></table>
            </div>
        </div>
        
        <div id="module-content" class="content-wrapper" style="max-width:1280px">
            
            <h3><?php echo _('Configuration'); ?></h3>
            
            <div id="navigation" style="padding-bottom:5px;">
                <button class="btn" id="module-sidebar-open"><i class="icon-list"></i></button>
            </div>
            
            <label><b><?php echo _('Key'); ?></b></label>
            <input id="module-name" class="input-large" type="text" required>
            <span id="module-name-tooltip" data-toggle="tooltip" data-placement="bottom">
                <i class="icon-info-sign" style="vertical-align:top; margin-top:8px; margin-left:2px; cursor:pointer;"></i>
            </span>
            
            <p id="module-description"></p>
            <div class="divider"></div>
            
            <label><b><?php echo _('Count'); ?></b></label>
            <table id="module-count">
                <tr>
                    <th><?php echo _('Strings'); ?></th>
                    <th><?php echo _('Modules'); ?></th>
                    <th></th>
                </tr>
				<tr>
					<td><input id="module-strings" class="input-small" type="number" step="1" min="1" placeholder="1" required></td>
					<td><input id="module-number" class="input-small" type="number" step="1" min="1" placeholder="1" required></td>
					<td>
                        <span id="module-count-tooltip" data-toggle="tooltip" data-placement="bottom">
                            <i class="icon-info-sign" style="margin-bottom:12px; cursor:pointer;"></i>
                        </span>
                    </td>
				</tr>
            </table>
            
            <label><b><?php echo _('Orientation'); ?></b></label>
            <table id="module-orientation">
                <tr>
                    <th><?php echo _('Tilt'); ?></th>
                    <th><?php echo _('Azimuth'); ?></th>
                    <th></th>
                </tr>
				<tr>
					<td><input id="module-tilt" class="input-small" type="number" step="0.1" min="0" max="90" placeholder="30" required></td>
					<td><input id="module-azimuth" class="input-small" type="number" step="0.1" min="0" max="359.9" placeholder="180" required></td>
					<td>
                        <span id="module-orientation-tooltip" data-toggle="tooltip" data-placement="bottom">
                            <i class="icon-info-sign" style="margin-bottom:12px; cursor:pointer;"></i>
                        </span>
                    </td>
				</tr>
            </table>
            
            <label><b><?php echo _('Albedo'); ?></b></label>
            <select id="module-albedo" class="input-medium">
                <option value="0.18"><?php echo _('Urban'); ?></option>
                <option value="0.20"><?php echo _('Grass'); ?></option>
                <option value="0.17"><?php echo _('Soil'); ?></option>
                <option value="0.40"><?php echo _('Sand'); ?></option>
                <option value="0.65"><?php echo _('Snow'); ?></option>
                <option value="0.12"><?php echo _('Asphalt'); ?></option>
                <option value="0.30"><?php echo _('Concrete'); ?></option>
                <option value="0.85"><?php echo _('Aluminum'); ?></option>
                <option value="0.74"><?php echo _('Copper'); ?></option>
                <option value="0.35"><?php echo _('Steel'); ?></option>
                <option value="0.06"><?php echo _('Sea'); ?></option>
            </select>
            <span id="module-albedo-tooltip" data-toggle="tooltip" data-placement="bottom">
                <i class="icon-info-sign" style="vertical-align:top; margin-top:8px; margin-left:2px; cursor:pointer;"></i>
            </span>
        </div>
    </div>
    <div class="modal-footer">
        <button id="module-cancel" class="btn" data-dismiss="modal" aria-hidden="true"><?php echo _('Cancel'); ?></button>
        <button id="module-delete" class="btn btn-danger" style="cursor:pointer"><i class="icon-trash icon-white"></i> <?php echo _('Delete'); ?></button>
        <button id="module-save" class="btn btn-primary"><?php echo _('Save'); ?></button>
    </div>
</div>

<script>
    $(window).resize(function() {
        dialog.adjustModal();
    });
</script>
