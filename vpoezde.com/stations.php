<?php

header("Content-type: application/json; charset=utf-8");
header("Cache-Control: no-cache, must-revalidate");
header("Expires: Mon, 26 Jul 1997 05:00:00 GMT");

$r_host = "rzdtickets\.ru";
$r_host2 = "vpoezde\.com";
// $r_host = "gpio\.ru";
// $r_host2 = "localhost";

$sql_host = "localhost";
$sql_user = "rzdbot";
$sql_pass = "rzdtickets22";
$sql_db = "rzdtickets.ru";

$response = Array();
$pair = Array();

if(!empty($_GET["term"]) && (preg_match("/^http\:\/\/(www\.)?".$r_host."/i", strtolower(@$_SERVER["HTTP_REFERER"]))
                         || preg_match("/^http\:\/\/(www\.)?".$r_host2."/i", strtolower(@$_SERVER["HTTP_REFERER"]))))
{

    mysql_connect($sql_host, $sql_user, $sql_pass) or die(mysql_error());
    mysql_select_db($sql_db) or die(mysql_error());

    $search = @$_GET["term"];
//    $search = iconv("utf-8", "cp1251", $search);
    $search = mysql_real_escape_string($search)."%";

    $result = mysql_query("SELECT * FROM `stations_t4you.ru` WHERE `station_name` LIKE '$search' LIMIT 0, 10") or die(mysql_error());

    while($row = mysql_fetch_array($result, MYSQL_ASSOC))
    {
        $s_name = $row["station_name"];
//        $s_name = iconv("cp1251", "utf-8", $s_name);

        $s_code = $row["station_code"];

        $t_name = $row["trainway_name"];
//        $t_name = iconv("cp1251", "utf-8", $t_name);

        $pair["label"] = $s_name." (".$s_code."), ".$t_name;
        $pair["value"] = $s_name;

        array_push($response, $pair);
    }

    mysql_close();
}

echo json_encode($response);

?>
