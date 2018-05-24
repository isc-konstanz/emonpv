<?php
    global $path;
?>

<script type="text/javascript" src="<?php echo $path; ?>Modules/solar/Views/solar.js"></script>

<style>
    .block-bound {
      background-color: rgb(68,179,226);
    }

    .block-content {
        background-color:#fff;
        color:#333;
        padding:10px;
    }

    .block-title {
        padding: 10px;
        float:left;
        color: grey;
        font-weight: bold;
    }

    .thing {
        margin-bottom:10px;
        border: 1px solid #aaa;
    }

    .thing-info {
        background-color: #ddd;
        cursor: pointer;
    }

    .thing-configure {
        float:right;
        padding:10px;
        width:30px;
        text-align:center;
        color:#666;
        border-left: 1px solid #eee;
    }

    .thing-configure:hover {
        background-color:#eaeaea;
    }

    .thing-list {
        padding: 0px 5px 5px 5px;
        background-color: #ddd;
    }

    .thing-list-item {
        margin-bottom: 12px;
    }

    .item-list {
        background-color: #f0f0f0;
        border-bottom: 1px solid #fff;
        border-item-left: 2px solid #f0f0f0;
        height: 41px;
    }

    .item {
        color: grey;
        padding-top: 5px;
    }

    .item-name {
        text-align: right;
        font-weight: bold;
        width: 80%;
    }

    .item-input {
        text-align: right;
        font-weight: bold;
        width: 1%;
    }

    .item-input .text {
        color: dimgrey;
        margin-right: 8px;
    }

    .item-left {
        text-align: right;
    }

    .item-right {
        text-align: left;
        width: 5%;
    }

    input.number {
        margin-bottom: 2px;
        margin-right: 8px;
        text-align: right;
        width: 55px;
        color: grey;
        background-color: white;
    }

    input.number[disabled] {
        background-color: #eee;
    }
</style>

<div>
    <div id="api-help-header" style="float:right;"><a href="api"><?php echo _('Solar Systems Help'); ?></a></div>
    <div id="local-header"><h2><?php echo _('Solar Systems'); ?></h2></div>

    <div id="system-list"></div>

    <div id="system-none" class="alert alert-block hide" style="margin-top: 20px">
        <h4 class="alert-heading"><?php echo _('No Solar Systems configured'); ?></h4>
        <p>
            <?php echo _('Solar Systems may consist of several photovoltaic installations, for which power forecasts will be generated.'); ?><br>
            <?php echo _('The systems power forecast may be constantly improved through live measurements, where one separate power meterering point is linked to a configured Solar System. This corresponds e.g. to several module installations of different orientations on a building roof, connected to one single inverter. You may want the next link as a guide for generating your request: '); ?><a href="api"><?php echo _('Solar Systems API helper'); ?></a>
        </p>
       </div>
    <div id="system-loader" class="ajax-loader"></div>
</div>

<script>

const INTERVAL = 10000;
var path = "<?php echo $path; ?>";

var systems = {};

function update() {
    solar.list(function(result) {
        if (result.length != 0) {
            $("#system-none").hide();
            $("#local-header").show();
            $("#api-help-header").show();
            if (updater) {
                draw();
            }
        }
        else {
            $("#system-none").show();
            $("#local-header").hide();
            $("#api-help-header").hide();
        }
        $('#system-loader').hide();
    });
}

update();

var updater;
function updaterStart() {
    clearInterval(updater);
    updater = null;
    if (INTERVAL > 0) updater = setInterval(update, INTERVAL);
}
function updaterStop() {
    clearInterval(updater);
    updater = null;
}
updaterStart();

//---------------------------------------------------------------------------------------------
// Draw systems
//---------------------------------------------------------------------------------------------
function draw() {
    var list = "";
    
    $("#system-list").html(list);
}

// --------------------------------------------------------------------------------------------
// Events
// --------------------------------------------------------------------------------------------
</script>