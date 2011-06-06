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

$abc = Array("À", "Á", "Â", "Ã", "Ä", "Å", "Æ", "Ç", "È", "É", "Ê", "Ë", "Ì", "Í", "Î", "Ï", "Ğ", "Ñ", "Ò", "Ó", "Ô", "Õ", "Ö", "×", "Ø", "Ù", "Ú", "Û", "Ü", "İ", "Ş", "ß");

foreach($abc as $let)
{
    $html = get_page("www.t4you.ru", "/stations.aspx?firstsymb=$let");
    $page_content = $html;
    
    $page_content = substr($page_content, stripos($page_content, "<table width=\"450\" border=\"0\" cellpadding=\"3\" cellspacing=\"1\">"));
    $page_content = substr($page_content, stripos($page_content, "</tr>") + strlen("</tr>"));

    while(stripos($page_content, "<a href=\"javascript:a"))
    {
        $tr_content = Array();
        
        for($i = 0; $i < 3; $i++)
        {
            $page_content = substr($page_content, stripos($page_content, "<td bgcolor=\"#FFFFFF\" align=\"center\">") + strlen("<td bgcolor=\"#FFFFFF\" align=\"center\">"));

            if($i == 0)
            {
                $page_content = substr($page_content, stripos($page_content, "')\">") + strlen("')\">"));
                $tr_content[] = substr($page_content, 0, stripos($page_content, "</a>")); // value
            }
            else
                $tr_content[] = substr($page_content, 0, stripos($page_content, "</td>")); // value

            $page_content = substr($page_content, stripos($page_content, "</td>"));
        }
        
        // print_r($tr_content); echo "<br>";
        
        mysql_query("INSERT INTO `stations_t4you.ru` (trainway_name, station_code, station_name) VALUES('".mysql_escape_string($tr_content[1])."', '".mysql_escape_string($tr_content[2])."', '".mysql_escape_string($tr_content[0])."')") or die(mysql_error()); 
    }
}

mysql_close();

?>