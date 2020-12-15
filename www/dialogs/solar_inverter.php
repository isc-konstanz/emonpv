<?php
    global $path;
?>

<div id="inverter-config-modal" class="modal hide keyboard" tabindex="-1" role="dialog" aria-labelledby="inverter-config-modal" aria-hidden="true" data-backdrop="static">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="inverter-config-label"></h3>
    </div>
    <div class="modal-body">
        <div class="alert alert-error">
            <?php echo _('Creating additional inverters is currently not supported.'); ?>
        </div>
    </div>
    <div class="modal-footer">
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
