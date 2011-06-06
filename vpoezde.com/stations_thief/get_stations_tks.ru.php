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

$page = 1;
$html = get_page("www.tks.ru", "/db/rwstation?page=$page");

while(stripos($html, "<tr class=\"alt1\">") || stripos($html, "<tr class=\"alt2\">"))
{
    $page_content = $html;
    $alt = 2;
    
    while(stripos($page_content, "<tr class=\"alt1\">") || stripos($page_content, "<tr class=\"alt2\">"))
    {
        $start = stripos($page_content, "<tr class=\"alt$alt\">");
        $page_content = substr($page_content, $start);
        
        $tr_content = Array();
        
        for($i = 0; $i < 5; $i++)
        {
            if($i < 2)
            {
                $td_start = "target=\"_blank\">";
                $td_end = "</a></td>";
            }
            else
            {
                $td_start = "<td>";
                $td_end = "</td>";
            }
            
            $td_start_p = stripos($page_content, $td_start);
            $page_content = substr($page_content, $td_start_p + strlen($td_start));
            $td_end_p = stripos($page_content, $td_end);
            $tr_content[] = substr($page_content, 0, $td_end_p); // value
            $page_content = substr($page_content, $td_end_p);
        }
        
        // print_r($tr_content); echo "<br>";
        
        mysql_query("INSERT INTO `stations_tks.ru` (code, station, trainway, trainway_branch, customs) VALUES('".mysql_escape_string($tr_content[0])."', '".mysql_escape_string($tr_content[1])."', '".mysql_escape_string($tr_content[2])."', '".mysql_escape_string($tr_content[3])."', '".mysql_escape_string($tr_content[4])."')") or die(mysql_error()); 
        
        $alt = ($alt == 2) ? 1 : 2;
    }

    ++$page;
    $html = get_page("www.tks.ru", "/db/rwstation?page=$page");
}

mysql_close();

?>