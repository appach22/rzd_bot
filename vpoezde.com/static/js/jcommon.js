function get_time_t(el)
{
    var d = el.val().split("-");
    return Date.UTC(d[0], d[1] - 1, d[2]) / 1000;
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

function take_and_send_start()
{
    var trains = new Array();
    var emails = new Array();
    var sms = new Array();

    $("#loadingDialog").dialog("open");

    for(var i = 1; i < 4; i++)
    {
        var el_d = $(".d" + i + "f");
        if(validate_text(el_d))
        {
            var thisDate = parseInt(get_time_t(el_d), 10);
            for(var j = 1; j < 4; j++)
            {
                var el_t = $(".d" + i + "t" + j + "f");
                if(validate_text(el_t) || j == 1)
                    trains.push(new Array(thisDate, el_t.val()));
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

    $.jsonRPC.request("start", {
        params: [{"route_from": $("#sourceField").val(), "route_to": $("#destinationField").val(),
                 "trains": trains, "car_type": parseInt($("#wagonField").val(), 10),
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
                    //TODO: здесь переделать input в select
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
