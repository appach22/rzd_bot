function get_time_t(el)
{
    var d = el.val().split(".");
    return Date.UTC(d[2], d[1] - 1, d[0]) / 1000;
}

function trim(str) { return str.replace(/^\s\s*/, '').replace(/\s\s*$/, ''); }

function validate_text(obj)
{
    if(obj.val() == "")
        return false;
    return true;
}

function validate_places()
{
    if(!validate_text($("#sourceField")))
    {
        jAlert("warning", "Выберите станцию отправления.", "Предупреждение");
        return false;
    }

    if(!validate_text($("#destinationField")))
    {
        jAlert("warning", "Выберите станцию назначения.", "Предупреждение");
        return false;
    }

    return true;
}

function validate_dates()
{
    var one_shot = false;
    var min_date = 0;
    var max_date = 0;

    $(".dateField").each(function() {
        if(validate_text($(this)))
        {
            one_shot = true;

            var f_date = get_time_t($(this));

            if(!min_date) min_date = f_date;
            if(!max_date) min_date = f_date;

            if(f_date > max_date)
                max_date = f_date;
            else if(f_date < min_date)
                min_date = f_date;
        }
    });

    if(!one_shot)
    {
        jAlert("warning", "Выберите дату отправления.", "Предупреждение");
        return false;
    }

    if((max_date - min_date) > 172800)
    {
        jAlert("error", "Интервал между крайними датами не должен превышать 3 дня!", "Ошибка");
        return false;
    }

    return true;
}

function validate_trains()
{
    var one_shot = false;

    for(var i = 1; i < 4; i++)
    {
        var el_d = $(".d" + i + "f");
        if(validate_text(el_d))
        {
            var one_shot = false;

            for(var j = 1; j < 4; j++)
            {
                if(validate_text($(".d" + i + "t" + j + "f")))
                    one_shot = true;
            }
            if(!one_shot)
            {
                jAlert("error", "Укажите номер поезда для " + el_d.val() + "!", "Ошибка");
                return false;
            }
        }
    }

    return true;
}

function validate_email(obj)
{
    return /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/.test(obj.val());
}

function validate_all_emails()
{
    var one_shot = false;
    var ret = true;

    // validate emails
    $(".emailField").each(function() {
        if(validate_text($(this)))
        {
            one_shot = true;

            if(!validate_email($(this)))
            {
                $(this).addClass("fieldError");
                jAlert("error", "e-mail \"" + $(this).val() + "\" введен неверно!", "Ошибка");
                ret = false;
                return false;
            }
            else
            {
                if($(this).hasClass("fieldError"))
                    $(this).removeClass("fieldError");
            }
        }
    });

    if(!one_shot)
    {
        jAlert("warning", "Заполните поле e-mail.", "Предупреждение");
        return false;
    }

    return ret;
}

function validate_int(obj)
{
    return /^[0-9]+$/.test(obj.val());
}

function validate_places()
{
    var ret = true;

    if(validate_text($("#placesFrom")) && !validate_text($("#placesTo")))
        $("#placesTo").val("120");
    if(validate_text($("#placesTo")) && !validate_text($("#placesFrom")))
        $("#placesFrom").val("1");

    if(validate_text($("#placesFrom")))
    {
        var from = parseInt($("#placesFrom").val(), 10) || 0;
        if(from < 1 || from > 120)
            ret = false;
    }
    if(validate_text($("#placesTo")))
    {
        var to = parseInt($("#placesTo").val(), 10) || 0;
        if(to < 1 || to > 120)
            ret = false;
    }

    if(!ret)
        jAlert("warning", "Диапазон номеров должен быть 1-120.", "Предупреждение");

    return ret;
}

function take_and_send_start()
{
    var route_from = null;
    var route_to = null;
    var trains = new Array();
    var emails = new Array();
    var sms = new Array();

    $("#loadingDialog").dialog("open");

    if($("#sourceField").is(":text"))
        route_from = $("#sourceField").val();
    else
        route_from = $("#sourceField :selected").val();

    if($("#destinationField").is(":text"))
        route_to = $("#destinationField").val();
    else
        route_to = $("#destinationField :selected").val();

    for(var i = 1; i < 4; i++)
    {
        var el_d = $(".d" + i + "f");
        if(validate_text(el_d))
        {
            var thisDate = parseInt(get_time_t(el_d), 10);
            var el_t = $(".d" + i + "t1f");
            if(validate_text(el_t))
            {
                var numbers = el_t.val().split(", ");
                for (var j = 0; j < numbers.length; j++)
                    trains.push(new Array(thisDate, numbers[j]));
            }
        }
    }

    $(".emailField").each(function() {
        if(validate_text($(this)))
            emails.push($(this).val());
    });

    $(".cellField").each(function() {
        if(validate_text($(this)))
        {
            var prefix = "7";
            switch($("#countryField").val())
            {
                case "0":
                    prefix = "7";
                    break;
                case "1":
                    prefix = "38";
                    break;
                default:
                    break;
            }
            sms.push(parseInt(prefix + $(this).mask("value"), 10));
        }
    });

    var car_type = 0;
    if ($("#car_lux").attr('checked'))
        car_type |= 8;
    if ($("#car_kupe").attr('checked'))
        car_type |= 4;
    if ($("#car_platz").attr('checked'))
        car_type |= 2;
    if ($("#car_sit").attr('checked'))
        car_type |= 1;
    if (car_type == 0)
    {
        $("#loadingDialog").dialog("close");
        jAlert("warning", "Выберите тип вагона.", "Предупреждение");
        return;
    }


    $.jsonRPC.request("start", {
        params: [{"route_from": route_from, "route_to": route_to,
                 "trains": trains, "car_type": car_type,
                 "range": [validate_text($("#placesFrom")) ?
                                                           parseInt($("#placesFrom").val(), 10) : 1,
                           validate_text($("#placesTo")) ?
                                                           parseInt($("#placesTo").val(), 10) : 120
                          ],
                 "parity": $("#highPlaces").attr("checked") ? $("#lowPlaces").attr("checked") ? 3 : 2 : $("#lowPlaces").attr("checked") ? 1 : 3, // удачной отладки
                 "emails": emails, "sms": sms
        }],
        success: function(result) {
            $("#loadingDialog").dialog("close");
            var res = result["result"];
            switch(res["code"])
            {
                case 0:
                    jAlert("success", "Заявка принята в работу!", "Уведомление");
                    break;
                case 1:
                    jAlert("error", "Ошибка при отправке запроса: " + res["HTTPError"], "Ошибка");
                    break;
                case 2:
                    jAlert("error", "Ошибка системы Express-3: " + res["ExpressError"], "Ошибка");
                    break;
                case 3:
                    input_to_select(res);
                    jAlert("warning", "Уточните название станции", "Предупреждение");
                    break;
                case 4:
                    jAlert("error", res["Station"] + ": " + res["StationError"], "Ошибка");
                    break;
                default:
                    jAlert("error", "Произошла неизвестная ошибка!", "Ошибка");
                    break;
            }
        },
        error: function(result) {
            $("#loadingDialog").dialog("close");
            // TODO: Возвращать текст ошибки
            jAlert("error", "Ошибка при отправке запроса!", "Ошибка");
        }
    });
}

function input_to_select(res)
{
    var targetField = "sourceField";

    if($(".station" + res["StationNum"] + "rst").hasClass("disabledField"))
        $(".station" + res["StationNum"] + "rst").removeClass("disabledField");

    if(1 == res["StationNum"])
        targetField = "sourceField";
    else if(2 == res["StationNum"])
        targetField = "destinationField";

    $("#" + targetField).after('<select id="' + targetField + '" class="long-field-sl"></select>').remove();
    $("#" + targetField).empty();

    for(i in res["StationOptions"])
    {
        var station = res["StationOptions"][i];
        $("#" + targetField).append($('<option value="' + station[0] + '">' + station[1] + '</option>'));
    }
}

function select_to_input(el, targetField)
{
    var val = $("#" + targetField + " :selected").text().split(" (")[0];
    $(el).addClass("disabledField");
    $("#" + targetField).after('<input type="text" id="' + targetField + '" class="long-field" />').remove();
    $("#" + targetField).val(val);
}
