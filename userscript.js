
$(".btn-run").first().on("click",get_output);
function get_output () {
  var output = $(".active-out").first().text();
  alert(output);
};
