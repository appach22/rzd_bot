$(function() {

var trainFocused = null;

$(".dateField").datepicker({dateFormat: "yy-mm-dd", changeMonth: true, changeYear: true});

// FAQ
$("#topFAQ").accordion({collapsible: true, active: false, autoHeight: false});

// helper
$(".settings-helper").cluetip({
    splitTitle: "|",
    showTitle: false,
    leftOffset: -435,
    width: 400,
    cluetipClass: "def"
});

// autocomplete
var setAutocomplete = function(el) {
if(el == 1 || el == 3)
{
    $("#sourceField").autocomplete({
        source: "stations.php",
        minLength: 2
    });
}
if(el == 2 || el == 3)
{
    $("#destinationField").autocomplete({
        source: "stations.php",
        minLength: 2
    });
}
}; setAutocomplete(3);

// masked phones
$(".cellField").mask({mask: "+7 (###) ###-##-##"});

// select country
$("#countryField").change(function() {
    $(".cellField").mask("destroy");
    $(".cellField").val("");

    switch($(this).val())
    {
        case "0":
            $(".cellField").mask({mask: "+7 (###) ###-##-##"});
            break;
        case "1":
            $(".cellField").mask({mask: "+38 (###) ###-##-##"});
            break;
        default:
            break;
    }
});

// stop dialog
$("#stopDialog").dialog({
    modal: true,
    width: "25em",
    autoOpen: false,
    resizable: false,
    close: function(ev, ui) {
        ;
    },
    open: function(ev, ui) {
        $("#stopRequest").val("");
        $("#stopEmail").val("");
    },
    buttons: {
        "Ок": function() {
            if(!validate_text($("#stopRequest")) || !validate_text($("#stopEmail")))
            {
                jAlert("warning", "Заполните все поля.", "Предупреждение");
                return false;
            }

            if(!validate_int($("#stopRequest")))
            {
                jAlert("error", "Номер заявки введен неверно!", "Ошибка");
                return false;
            }

            if(!validate_email($("#stopEmail")))
            {
                jAlert("error", "e-mail введен неверно!", "Ошибка");
                return false;
            }

            $("#loadingDialog").dialog("open");

            $.jsonRPC.request("stop", {
                params: [parseInt($("#stopRequest").val(), 10), $("#stopEmail").val()],
                success: function(result) {
                    $("#loadingDialog").dialog("close");
                    var res = result["result"];
                    switch(res["code"])
                    {
                        case 0:
                            jAlert("success", "Отслеживание успешно остановлено!", "Уведомление");
                            break;
                        case 1:
                            jAlert("error", "Ошибка обращения к базе данных!", "Ошибка");
                            break;
                        case 2:
                            jAlert("error", "Неверный номер отслеживания!", "Ошибка");
                            break;
                        case 3:
                            jAlert("error", "Введен ошибочный e-mail!", "Ошибка");
                            break;
                        case 4:
                            jAlert("error", "Отслеживание уже остановлено!", "Ошибка");
                            break;
                        case 5:
                            jAlert("error", "Системная ошибка при остановке отслеживания!", "Ошибка");
                            break;
                        default:
                            jAlert("error", "Неизвестная ошибка при остановке отслеживания!", "Ошибка");
                            break;
                    }
                    $("#stopDialog").dialog("close");
                },
                error: function(result) {
                    $("#loadingDialog").dialog("close");
                    // TODO: Возвращать текст ошибки
                    jAlert("error", "Ошибка при отправке запроса!", "Ошибка");
                }
            });
        },
        "Отмена": function() {
            $(this).dialog("close");
        }
    }
});

// trains dialog
$("#trainsDialog").dialog({
    modal: true,
    width: "65em",
    height: 300,
    autoOpen: false,
    resizable: false,
    close: function(ev, ui) {
        ;
    },
    open: function(ev, ui) {
        $("#trainsDialogTbl").html('<tr><td height="80"></td></tr>' +
                                   '<tr><td align="center">загрузка списка...</td></tr>' +
                                   '<tr><td height="10"></td></tr>' +
                                   '<tr><td align="center"><img src="static/img/loader.gif" border="0" alt="" /></td></tr>');

        var thisDate = parseInt(get_time_t($("." + trainFocused.closest("tr").closest("td").closest("tr").attr("id") + "f")), 10);

        $("#trainsDialog").dialog("option", "title", "Список поездов по маршруту " + $("#sourceField").val() + " - " + $("#destinationField").val() + " на ");

        $.jsonRPC.request("getTrainsList", {
            params: [$("#sourceField").val(), $("#destinationField").val(), thisDate],
            success: function(result) {
                var res = result["result"];
                var ret_html = '<tr>' +
                               '<td></td><td width="15"></td>' +
                               '<td align="center"><b>Поезд</b></td><td width="15"></td>' +
                               '<td align="center"><b>Маршрут</b></td><td width="15"></td>' +
                               '<td align="center"><b>Отправление</b></td><td width="15"></td>' +
                               '<td align="center"><b>Прибытие</b></td><td width="15"></td>' +
                               '<td align="center"><b>В пути</b></td><td width="15"></td>' +
                               '<td align="center"><b>Тип</b></td><td></td>' +
                               '</tr><tr><td height="5"></td></tr>';
                switch(res["code"])
                {
                    case 0:
                        if (res["trains"].length == 0)
                        {
                            $("#trainsDialog").dialog("close");
                            trainFocused.val("");
                            jAlert("error", "Поезда в указанную дату не найдены!", "Ошибка");
                            break;
                        }
                        for(i in res["trains"])
                        {
                            var train = res["trains"][i];
                            var tr = trim((train["train"]))
                            var num = tr.split(" ");
                            var route = trim(tr.slice(tr.indexOf(" ")))
                            ret_html += '<tr>' +
                                        '<td><input type="radio" name="trainListEl" class="trainListEl" value="' + num[0] + '"></td><td></td>' +
                                        '<td align="center">' + num[0] + '</td><td></td>' +
                                        '<td>' + route + '</td><td></td>' +
                                        '<td align="center">' + train["departure"] + '</td><td></td>' +
                                        '<td>' + train["arrival"] + '</td><td></td>' +
                                        '<td align="center">' + train["onway"] + '</td><td></td>' +
                                        '<td align="center">' + train["vip"] + '</td><td></td>' +
                                        '</tr>';
                        }
                        break;
                    case 1:
                        $("#trainsDialog").dialog("close");
                        trainFocused.val("");
                        jAlert("error", "Ошибка при отправке запроса: " + res["HTTPError"], "Ошибка");
                        break;
                    case 2:
                        $("#trainsDialog").dialog("close");
                        trainFocused.val("");
                        jAlert("error", "Ошибка системы Express-3: " + res["ExpressError"], "Ошибка");
                        break;
                    case 3:
                        $("#trainsDialog").dialog("close");
                        trainFocused.val("");
                        input_to_select(res);
                        jAlert("warning", "Уточните название станции", "Предупреждение");
                        break;
                    case 4:
                        $("#trainsDialog").dialog("close");
                        trainFocused.val("");
                        jAlert("error", res["Station"] + ": " + res["StationError"], "Ошибка");
                        break;
                    default:
                        break;
                }
                $("#trainsDialogTbl").html(ret_html);
            },
            error: function(result) {
                $("#trainsDialog").dialog("close");
                // TODO: Возвращать текст ошибки
                jAlert("error", "Ошибка при отправке запроса!", "Ошибка");
            }
        });
    },
    buttons: {
        "Отмена": function() {
            $(this).dialog("close");
        }
    }
});

$(".trainListEl").live("change", function() {
    trainFocused.val($(this).val());
    $("#trainsDialog").dialog("close");
});

// loading dialog
$("#loadingDialog").dialog({
    modal: true,
    width: 200,
    height: 70,
    autoOpen: false,
    resizable: false,
    dialogClass: "noTitleStuff"
});

// bind to stations reset
$(".station1rst").click(function() {
    select_to_input($(this), "sourceField");
    setAutocomplete(1);
});

$(".station2rst").click(function() {
    select_to_input($(this), "destinationField");
    setAutocomplete(2);
});

// bind to plus & minus
$(".trainMinus").click(function() {
    var theID = $(this).closest("tr").attr("id");
    $("." + theID).addClass("disabledField");
    $("." + theID + "f").val("");
});

$(".trainPlus").click(function() {
    var theID = $(this).closest("tr").closest("td").closest("tr").attr("id");
    for(var i = 2; i < 4; i++)
    {
        var item = "." + theID + "t" + i;
        if($(item).hasClass("disabledField"))
        {
            $(item).removeClass("disabledField");
            break;
        }
    }
});

$(".dateMinus").click(function() {
    var theID = $(this).closest("tr").closest("td").closest("tr").attr("id");
    $("." + theID).addClass("disabledField");
    $("." + theID + "f").val("");
    for(var i = 1; i < 4; i++)
    {
        $("." + theID + "t" + i + "f").val("");
        if(i > 1)
            $("." + theID + "t" + i).addClass("disabledField");
    }
});

$(".datePlus").click(function() {
    for(var i = 2; i < 4; i++)
    {
        var item = ".d" + i;
        if($(item).hasClass("disabledField"))
        {
            $(item).removeClass("disabledField");
            break;
        }
    }
});

$(".emailMinus").click(function() {
    var theID = $(this).closest("tr").closest("td").closest("tr").attr("id");
    $("." + theID).addClass("disabledField");
    $("." + theID + "f").val("");
});

$(".emailPlus").click(function() {
    for(var i = 2; i < 4; i++)
    {
        var item = ".e" + i;
        if($(item).hasClass("disabledField"))
        {
            $(item).removeClass("disabledField");
            break;
        }
    }
});

// bind to trains
$(".trainField").focus(function() {
    var thisDate = validate_text($("." + $(this).closest("tr").closest("td").closest("tr").attr("id") + "f"));
    if(!validate_text($("#sourceField")) || !validate_text($("#destinationField")) || !thisDate)
    {
        jAlert("error", "Поля \"Станция отправления\", \"Станция назначения\" и \"Дата\" должны быть заполнены!", "Ошибка");
        return false;
    }
    trainFocused = $(this);
    $("#trainsDialog").dialog("open");
});

// go-go-go
$("#submitStart").click(function() {
    if(!validate_places())
        return false;
    if(!validate_dates())
        return false;
    if(!validate_trains())
        return false;
    if(!validate_places())
        return false;
    if(!validate_all_emails())
        return false;

    take_and_send_start();
});

$("#submitStop").click(function() {
    $("#stopDialog").dialog("open");
});

});
