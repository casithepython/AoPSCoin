function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
function get_token() {
    return getCookie("AoPSCoin") //Get their token that's saved
}
function set_token(token) {
    document.cookie = "AoPSCoin=" + token + "; expires=1 Jan 3000 12:00:00 UTC;" // Add the token as a cookie
    window.location = "https://artofproblemsolving.com/community"
}
$("#tokenModal").modal('show')
$("#login-token").attr("placeholder",get_token())
$("#token-update-form").submit(function(e) {
    e.preventDefault()
    let inputs = $("#token-update-form :input").toArray()
    let token = inputs[0].value
    set_token(token)
})
$("#logout-button").click(function() {
    set_token("")
})
