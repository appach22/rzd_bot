$(function() {

// rpc
$.jsonRPC.setup({
    endPoint: "wsgi/"
});

// set datepicker lang
$.datepicker.setDefaults($.datepicker.regional["ru"]);

// buttons
$("button").addClass("ui-state-default ui-corner-all").hover(
        function() { $(this).addClass("ui-state-hover"); },
        function() { $(this).removeClass("ui-state-hover"); });
$("button").focus(function() { $(this).addClass("ui-state-hover"); });
$("button").blur(function() { $(this).removeClass("ui-state-hover"); });

// cleanup
$(".long-field").each(function() {
    $(this).val("");
});

$(".short-field").each(function() {
    $(this).val("");
});

// govnokontakt
try {
    VK.Widgets.Group("govnovk_groups", {mode: 1, width: "200", height: "290"}, 22031480);
} catch(e) {}

});
