<?php global $path, $session, $user; ?>
<style>
  a.anchor{display: block; position: relative; top: -50px; visibility: hidden;}
</style>

<h2><?php echo _('Device API'); ?></h2>
<h3><?php echo _('Apikey authentication'); ?></h3>
<p><?php echo _('If you want to call any of the following actions when your not logged in you have this options to authenticate with the API key:'); ?></p>
<ul><li><?php echo _('Append on the URL of your request: &apikey=APIKEY'); ?></li>
<li><?php echo _('Use POST parameter: "apikey=APIKEY"'); ?></li>
<li><?php echo _('Add the HTTP header: "Authorization: Bearer APIKEY"'); ?></li></ul>
<p><b><?php echo _('Read only:'); ?></b><br>
<input type="text" style="width:255px" readonly="readonly" value="<?php echo $user->get_apikey_read($session['userid']); ?>" />
</p>
<p><b><?php echo _('Read & Write:'); ?></b><br>
<input type="text" style="width:255px" readonly="readonly" value="<?php echo $user->get_apikey_write($session['userid']); ?>" />
</p>

<h3><?php echo _('Available HTML URLs'); ?></h3>
<table class="table">
    <tr><td><?php echo _('The system list view'); ?></td><td><a href="<?php echo $path; ?>solar/view"><?php echo $path; ?>solar/view</a></td></tr>
    <tr><td><?php echo _('This page'); ?></td><td><a href="<?php echo $path; ?>solar/api"><?php echo $path; ?>solar/api</a></td></tr>
</table>

<h3><?php echo _('Available JSON commands'); ?></h3>
<p><?php echo _('To use the json api the request url needs to include <b>.json</b>'); ?></p>

<p><b><?php echo _('Solar System actions'); ?></b></p>
<table class="table">
    <tr><td><?php echo _('Create a system'); ?></td><td><a href="<?php echo $path; ?>solar/create.json?name=Roof&location={%22longitude%22:47.67158,%22latitude%22:9.15218,%22altitude%22:403}"><?php echo $path; ?>solar/create.json?name=Roof&location={"longitude":47.67158,"latitude":9.15218,"altitude":403}</a></td></tr>
    <tr><td><?php echo _('Initialize a system'); ?></td><td><a href="<?php echo $path; ?>solar/init.json?id=1"><?php echo $path; ?>solar/init.json?id=1</a></td></tr>
    <tr><td><?php echo _('Prepare system initialization'); ?></td><td><a href="<?php echo $path; ?>solar/prepare.json?id=1"><?php echo $path; ?>solar/prepare.json?id=1</a></td></tr>
    <tr><td><?php echo _('List systems'); ?></td><td><a href="<?php echo $path; ?>solar/list.json"><?php echo $path; ?>solar/list.json</a></td></tr>
    <tr><td><?php echo _('Get system details'); ?></td><td><a href="<?php echo $path; ?>solar/get.json?id=1"><?php echo $path; ?>solar/get.json?id=1</a></td></tr>
    <tr><td><?php echo _('Update system'); ?></td><td><a href="<?php echo $path; ?>solar/set.json?id=1&fields={%22name%22:%22Facade%22,%22description%22:%22East%22}"><?php echo $path; ?>solar/set.json?id=1&fields={"name":"Facade","description":"East"}</a></td></tr>
    <tr><td><?php echo _('Delete system'); ?></td><td><a href="<?php echo $path; ?>solar/delete.json?id=1"><?php echo $path; ?>solar/delete.json?id=1</a></td></tr>
</table>

<p><b><?php echo _('Solar Module actions'); ?></b></p>
<table class="table">
    <tr><td><?php echo _('List module meta info'); ?></td><td><a href="<?php echo $path; ?>solar/module/meta.json"><?php echo $path; ?>solar/module/meta.json</a></td></tr>
    <tr><td><?php echo _('List module details'); ?></td><td><a href="<?php echo $path; ?>solar/module/list.json"><?php echo $path; ?>solar/module/list.json</a></td></tr>
    <tr><td><?php echo _('Get module details'); ?></td><td><a href="<?php echo $path; ?>solar/module/get.json?type=example"><?php echo $path; ?>solar/module/get.json?type=example</a></td></tr>
</table>
