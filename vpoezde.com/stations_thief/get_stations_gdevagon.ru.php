<?php

mysql_connect("localhost", "rzdbot", "rzdbot3323322") or die(mysql_error());
mysql_select_db("rzdtickets.ru") or die(mysql_error());

function get_page($host, $page)
{
    $out = "";
    $fp = fsockopen("$host", 80, $errno, $errdesc);
    if(!$fp)
        die("Couldn't connect to $host:\nError: $errno\nDesc: $errdesc\n"); 
    $request = "GET $page HTTP/1.0\r\n";
    $request .= "Host: $host\r\n\r\n";
    fputs($fp, $request);
    while(!feof($fp))
        $out .= fgets($fp, 1024);
    fclose($fp);
    
    return $out;
}

$html = get_page("www.gdevagon.ru", "/scripts/info/way_info.php");

$page_content = $html;
$table_content = Array();

$page_content = substr($page_content, stripos($page_content, "<table class='infot'>"));
$page_content = substr($page_content, stripos($page_content, "</tr>") + strlen("</tr>"));

while(stripos($page_content, "Информация о дороге, контакты, список станций"))
{
    $tr_content = Array();

    for($i = 0; $i < 5; $i++)
    {
        if($i == 4)
            $td_start = "<td style='text-align : right;'>";
        else
            $td_start = "<td>";
        
        $page_content = substr($page_content, stripos($page_content, $td_start) + strlen($td_start));

        if($i == 2)
        {
            $page_content = substr($page_content, stripos($page_content, "title='Информация о дороге, контакты, список станций'>") + strlen("title='Информация о дороге, контакты, список станций'>"));
            $tr_content[] = substr($page_content, 0, stripos($page_content, "</a>")); // value
        }
        else
            $tr_content[] = substr($page_content, 0, stripos($page_content, "</td>")); // value

        $page_content = substr($page_content, stripos($page_content, "</td>"));
    }
    
    $table_content[] = $tr_content;
    // print_r($tr_content); echo "<br>";
}

// print_r($table_content);

foreach($table_content as $arr)
{
    $html = get_page("www.gdevagon.ru", "/scripts/info/way_info.php?page=0&ids=$arr[0]");
    $page_content = $html;
    $page = 0;

    while(stripos($page_content, "title='Информация о станции'"))
    {
        for($i = 0; $i < 2; $i++)
        {
            $page_content = substr($page_content, stripos($page_content, "<table class='infot'>"));
            $page_content = substr($page_content, stripos($page_content, "</tr>") + strlen("</tr>"));
        }

        while(stripos($page_content, "title='Информация о станции'"))
        {
            $tr_content = Array();

            for($i = 0; $i < 2; $i++)
            {           
                $page_content = substr($page_content, stripos($page_content, "<td>") + strlen("<td>"));

                if($i == 1)
                {
                    $page_content = substr($page_content, stripos($page_content, "title='Информация о станции'>") + strlen("title='Информация о станции'>"));
                    $tr_content[] = substr($page_content, 0, stripos($page_content, "</a>")); // value
                }
                else
                    $tr_content[] = substr($page_content, 0, stripos($page_content, "</td>")); // value

                $page_content = substr($page_content, stripos($page_content, "</td>"));
            }
            
            // print_r($tr_content); echo "<br>"; 
            
            mysql_query("INSERT INTO `stations_gdevagon.ru` (trainway_code, trainway_s_name, trainway_name, trainway_country, station_code, station_name) VALUES('".mysql_escape_string($arr[0])."', '".mysql_escape_string($arr[1])."', '".mysql_escape_string($arr[2])."', '".mysql_escape_string($arr[3])."', '".mysql_escape_string($tr_content[0])."', '".mysql_escape_string($tr_content[1])."')") or die(mysql_error()); 
        }
        
        ++$page;
        $html = get_page("www.gdevagon.ru", "/scripts/info/way_info.php?page=$page&ids=$arr[0]");
        $page_content = $html;
    }
}

mysql_close();

?>