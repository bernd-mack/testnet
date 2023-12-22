<?PHP
header('Content-Type: application/json');

if (strtolower($_GET['state']) == "enabled") {
    $jsonData = file_get_contents('listmasternodes_enabled.json');
    if ($_GET['count'] == "True") {
        $data = json_decode($jsonData,true);
        $output['ENABLED'] = 0;
        foreach ($data as $value) { if ($value["state"] == "ENABLED"){ $output['ENABLED'] = $output['ENABLED']+1; } }
        echo json_encode($output);
        }
    else { echo $jsonData; }
}

else if (strtolower($_GET['state']) == "pre_enabled") {
    $jsonData = file_get_contents('listmasternodes_pre_enabled.json');
    if ($_GET['count'] == "True") {
        $data = json_decode($jsonData,true);
        $output['PRE_ENABLED'] = 0;
        foreach ($data as $value) { if ($value["state"] == "PRE_ENABLED"){ $output['PRE_ENABLED'] = $output['PRE_ENABLED']+1; } }
        echo json_encode($output);
        }
    else { echo $jsonData; }
}

else if (strtolower($_GET['state']) == "pre_resigned") {
    $jsonData = file_get_contents('listmasternodes_pre_resigned.json');
    if ($_GET['count'] == "True") {
        $data = json_decode($jsonData,true);
        $output['PRE_RESIGNED'] = 0;
        foreach ($data as $value) { if ($value["state"] == "PRE_RESIGNED"){ $output['PRE_RESIGNED'] = $output['PRE_RESIGNED']+1; } }
        echo json_encode($output);
        }
    else { echo $jsonData; }
}

else if (strtolower($_GET['state']) == "resigned") {
    $jsonData = file_get_contents('listmasternodes_resigned.json');
    if ($_GET['count'] == "True") {
        $data = json_decode($jsonData,true);
        $output['RESIGNED'] = 0;
        foreach ($data as $value) { if ($value["state"] == "RESIGNED"){ $output['RESIGNED'] = $output['RESIGNED']+1; } }
        echo json_encode($output);
        }
    else {echo $jsonData;}
}

else if (strtolower($_GET['state']) == "transferring") {
    $jsonData = file_get_contents('listmasternodes_transferring.json');
    if ($_GET['count'] == "True") {
        $data = json_decode($jsonData,true);
        $output['TRANSFERRING'] = 0;
        foreach ($data as $value) { if ($value["state"] == "TRANSFERRING"){ $output['TRANSFERRING'] = $output['TRANSFERRING']+1; } }
        echo json_encode($output);
        }
    else {echo $jsonData;}
}

else {
    $jsonData = file_get_contents('listmasternodes.json');
    if ($_GET['count'] == "True") {
        $data = json_decode($jsonData,true);
        $output['ENABLED'] = 0;
        $output['PRE_ENABLED'] = 0;
        $output['RESIGNED'] = 0;
        $output['PRE_RESIGNED'] = 0;
        $output['TRANSFERRING'] = 0;
        foreach ($data as $value) {
            if      ($value["state"] == "ENABLED")      { $output['ENABLED'] = $output['ENABLED']+1; }
            else if ($value["state"] == "PRE_ENABLED")  { $output['PRE_ENABLED'] = $output['PRE_ENABLED']+1; }
            else if ($value["state"] == "RESIGNED")     { $output['RESIGNED'] = $output['RESIGNED']+1; }
            else if ($value["state"] == "PRE_RESIGNED") { $output['PRE_RESIGNED'] = $output['PRE_RESIGNED']+1; }
            else if ($value["state"] == "TRANSFERRING") { $output['TRANSFERRING'] = $output['TRANSFERRING']+1; }}
        echo json_encode($output);}
    else {echo $jsonData;}
}
?>
