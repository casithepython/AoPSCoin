// ==UserScript==
// @name         AoPSCoin
// @namespace    http://tampermonkey.net/
// @version      v1.1
// @description  Client-side code for AoPSCoin. If you have questions please contact casi or check out our support forum at https://artofproblemsolving.com/community/c1219179.
// @author       casi
// @match        https://artofproblemsolving.com/*
// @grant        none
// @run-at document-start
// ==/UserScript==


setTimeout(function() {
    'use strict'; // Default from tampermonkey
    // COOKIES
    function getCookie(cname) {
        var name = cname + "=";
        var decodedCookie = decodeURIComponent(document.cookie);
        var ca = decodedCookie.split(';');
        for(var i = 0; i <ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) == ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) == 0) {
                return c.substring(name.length, c.length);
            }
        }
        return "";
    }

    // TIME SECTION //
    function elapsedTime (time) { // This is for less than or equal to 6 hours ago
        if (time <= 60000) {return ("a few seconds ago")} // For less than a minute
        else if (time <= 3540000) { // For 1 minute - 59 minutes
            let minutes = Math.round(time/60000) // Get the number of minutes
            if (minutes == 1) {return ("1 minute ago")} // 1 minute since the English Language won't let me plug it into the other formula
            else {return (minutes.toString() + " minutes ago")} // x minutes ago
        }
        else { // For any other time given (1 hour - 6 hours)
            let hours = Math.round(time/3600000); // Get the number of hours
            if (hours == 1) {return ("1 hour ago")} // 1 hour in the singular
            else {return (hours.toString() + " hours ago")}; // x hours ago
        }
    }
    function meridian (hour, minute) { // For AM and PM
        minute = minute.toString();
        if (minute.length == 1) {minute = "0" + minute} // Turns 9:5 into 9:05
        if (hour == 0) {return ("12:" + minute + " AM")} // 12 AM
        else if (hour < 12) {return (hour.toString() + ":" + minute + " AM")} // 1 AM - 11 AM
        else if (hour == 12) {return ("12:" + minute + " PM")} // 12 PM
        else {return((hour-12).toString() + ":" + minute + " PM")} // 1 PM - 11 PM
    }
    function dateFormat (time) { // NOTE: This takes anything, Dates, times, milliseconds since 1970, etc.
        var months = ["January","February","March","April","May","June","July","August","September","October","November","December"] // Month list, this is global
        // Format date
        let now = new Date()
        let date = new Date(time)
        let day = date.getDate()
        let month = months[date.getMonth()]
        let year = date.getFullYear()
        let hour = date.getHours()
        let minute = date.getMinutes()
        let theday;
        //Print based on today, yesterday, or else
        if (day == now.getDate()) {theday = "Today"} // Check if the date posted was today
        else if (day == (now.getDate() - 1)) {theday = "Yesterday"} // Check if the date posted was yesterday
        else {theday = (month + " " + day + ", " + year)} // Otherwise, format as July 4, 1776
        return (theday + " at " + meridian(hour,minute)) // e.g. July 4, 1776 at 9:30 AM
    }
    function formatTime (date) { // Master function for the time formatting
        let nowDate = new Date(); // Get the date now
        let thenDate = new Date(date + " GMT+0"); // Make the input into a date
        // Get time since now and the posting time
        let then = thenDate.getTime()//+(thenDate.getTimezoneOffset()*60);
        let now = nowDate.getTime();
        let timeElapsed = now - then;

        if (timeElapsed <= 21600000) {return (elapsedTime (timeElapsed))} // If it's less than or equal to 6 hours, use the elapsed time module
        else {return dateFormat(thenDate)} // Otherwise, just post the date sent
    }

    // TRANSACTION SECTION //
    function submitNewTransaction() {
        alert("Successfully transferred!")
    }
    function checkTransactionUIError() { // Checks for errors in the transactionUI before submitting
        // There has to be a username submitted and verified by AoPS
        if ($(".cmty-itemlist-username").length <= 0) {
            alert("User invalid")
            return false;
        }
        let amount = $(".cmty-subject-input")[0].value
        // Number must be a positive integer. Make sure to run these checks at the back end too in case people modify the code
        if(Math.floor(amount) == amount && $.isNumeric(amount) && amount > 0) {}
        else {
            alert("Amount invalid")
            return false;
        }
        return true;
    }
    function transactionUI() { // Setting up the transaction UI
        // Use the PM template by creating a new private conversation
        new AoPS.Community.Views.NewPrivateConversation({
            model: AoPS.Feed.community_master.fetchCategory(1),
            master: AoPS.Feed.community_master
        })
        // Set up the button and override all existing functions
        $("body > div.aops-modal-wrapper > div > div > div > div > div > div:nth-child(2) > div > input.cmty-submit-button.btn.btn-primary").on("click",function (e) { // Just onclick, I don't want right-clicks triggering it
            e.stopPropagation() // This makes the button completely dead
            if(checkTransactionUIError()) { // First run a check to make sure everything is acceptable.
                AoPS.Community.Views.throwLoaderBlockingMessage("Please wait")
                // Button code:
                // Submit a new transaction, which is submitNewTransaction(to,from,amount,notes)
                // to = $(this)[0].innerText.slice(0,-2)
                // from = myUsername (we took this from the bootstrap data at the beginning, it's AoPS.bootstrap_data.my-profile.username
                // amount = parseInt($(".cmty-subject-input")[0].value), which takes the value from the amount input and turns it into an integer
                // notes = $(".cmty-post-textarea")[0].value

                // This needs to be fixed for security
                let toUsers = []
                $("body > div.aops-modal-wrapper > div > div > div > div > div > div.cmty-posting-top > div.cmty-private-recipients > div > div").each(function(){
                    toUsers.push($(this)[0].innerText.slice(0,-2))
                })
                let amount = parseInt($(".cmty-subject-input")[0].value)
                let notes = $(".cmty-post-textarea")[0].value
                let raw = JSON.stringify({"token":get_token(),"toUsers":toUsers,"amount":amount,"notes":notes});
                let myHeaders = new Headers();
                myHeaders.append("Content-Type", "application/json");
                let requestOptions = {
                    method: 'POST',
                    headers: myHeaders,
                    body: raw,
                    redirect: 'follow'
                };

                fetch("https://quantlaw.com/transfer", requestOptions)
                    .then(response => response.text())
                    .then(result => handle_result(result))
                    .catch(error => handle_result("An error occurred. Please contact casi." + error));

            }
        });
        $(document).on("keydown", function(e) {
            var key_pressed = e.which || e.keyCode;
            if (key_pressed === 13 && (e.ctrlKey || e.metaKey)) {
                console.log("pressed")
                e.stopPropagation()
            }
        });
        // Formatting
        $(".cmty-tags-line").remove() // No tags (maybe future feature)
        $(".cmty-bbcode-buttons").remove() // No buttons (maybe future feature)
        $(".cmty-posting-preview-bar").remove() // No preview bar (will reimplement when buttons are implemented)
        $(".cmty-post-preview").hide() //Remove preview
        $(".cmty-posting-subject-line .cmty-heading-text").text("Amount") // Rename "Subject" to "Amount"
        $(".cmty-post-textarea").attr("placeholder","Notes") // Add a notes placeholder so users know what it is*/
    }
    function handle_result(result) {
        AoPS.Ui.Modal.closeAllModals(); // Close the window
        alert(result)
    }
    // FEED HEADER SECTION //
    function setFeedHeader () {
        var myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");

        var raw = JSON.stringify({"token":get_token(),"user_id":AoPS.session.user_id});

        var requestOptions = {
            method: 'POST',
            headers: myHeaders,
            body: raw,
            redirect: 'follow'
        };

        fetch("https://quantlaw.com/get_user", requestOptions)
            .then(response => response.json())
            .then(result => formatHeader(result))
            .catch(error => console.log('error', error));
    }

    function formatHeader(userdata) {
        let balance = userdata.balance
        let isValid = userdata.isValid == 1
        let feedHeader = $("#feed-aopscoin-tab .feed-subfeed-header") // Get the header
        feedHeader.html(`<span class="feed-subfeed-title">AoPSCoin</span>
<span class="feed-subfeed-header-right">
<span title="Start New Transaction" id="balance">`+balance.toString()+`</span>
<span title="Start New Transaction" id="new-transaction" class="aops-font">V</span>
<span title="Close feed" class="aops-font feed-close">J</span>
</span>`); // Add HTML
        if (isValid == false) {
            $("#balance").css("color","red") //Balance is if invalid
        }
        else {
            $("#balance").css("color","#fff") // This way we auto-update the validate setting every time the feed is opened, not just on reload.
        }
        $("#feed-aopscoin-tab #new-transaction").mousedown(function () { // Override the other functions with mousedown
            transactionUI() // When clicked, open up the UI
        });
    }

    // FEED TOPICS SECTION //
    function setFeedTopics() { // The AJAX call for getting the feed topics.
        var myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");

        var raw = JSON.stringify({"token":get_token(),"user_id":AoPS.session.user_id});

        var requestOptions = {
            method: 'POST',
            headers: myHeaders,
            body: raw,
            redirect: 'follow'
        };

        fetch("https://quantlaw.com/get_transactions", requestOptions)
            .then(response => response.json())
            .then(result => formatFeedTopics(result))
            .catch(error => console.log('AoPSCoin error', error));
    }

    function formatFeedTopics (transactions) { // Function for formatting and constructing feed. This takes a list of objects {name:"",amount:"",reason:"",timestamp: Date(),notes:""}
        let feedList = $("#feed-aopscoin-tab .aops-scroll-content") // This is where the feed content will go
        feedList.text("") // Clear the existing feed to get rid of previous loads and the No More Topics text AoPS adds
        transactions.sort(function(a, b) {var dateA = new Date(a.transferTime), dateB = new Date(b.transferTime);return dateA - dateB;}); // Function I found online to sort the transactions by date
        transactions.sort().reverse() // Sort the transactions by date from newest to oldest
        var transaction;
        for (transaction of transactions) { // Go through all the transactions
            // Set up the variables for simplicity
            let name = transaction.name
            let amount = transaction.amount
            let time = formatTime(transaction.transferTime)
            let notes = transaction.notes
            // Some formatting to show whether the transaction was sent or received
            if (transaction.received) {name = ("From " + name)}
            else {name = ("To " + name)}
            // Add the HTML with the variables added
            feedList.append(`<div class="cmty-topic-cell aopscoin-cell" data-amount="${amount}" data-name="${name}" data-time="${time}" data-notes="${escape(notes)}"title="${amount}">
<div class="cmty-topic-cell-left"><div class="cmty-color-main cmty-topic-cell-jump-to-bottom" style="color: rgb(53, 108, 181);"></div>
<div class="cmty-color-main cmty-topic-cell-goto-unread" style="color: rgb(53, 108, 181);">
<div title="Jump to first unread" class="aops-font">h&nbsp;</div></div>
<div class="cmty-topic-cell-second-row"><span class="cmty-color-main cmty-topic-cell-username" data-hj-suppress="" data-hj-masked="" style="color: rgb(53, 108, 181);">` + name + `</span>  &nbsp; </span><span style="float:right;margin-right: 3px;margin-left: 3px;font-family:AoPS;font-style:normal;box-sizing: border-box;color: rgb(53, 108, 181);">y</span> <span class="aopscoin-amount" style="float:right;margin-left:4px;color: rgb(53, 108, 181);">` + amount + `
<span class="cmty-topic-cell-watchers"></span></div>
<div class="cmty-topic-cell-subtitle"><div class="cmty-topic-cell-subtitle-left">
<span class="aops-font">N</span>
<span class="cmty-topic-cell-time cmty-reply-time">` + time + `</span></div></div>
<div class="cmty-topic-cell-post">` + notes + `
</div>
</div></div>`);
        }
        $(".cmty-topic-cell.aopscoin-cell").click(function () {
            let name = $(this)[0].dataset.name
            let amount = $(this)[0].dataset.amount
            let notes = $(this)[0].dataset.notes
            let time = $(this)[0].dataset.time

            AoPS.Ui.Modal.showMessage(`<div class="cmty-post-wrapper">
<div class="cmty-post-tr">
<div class="cmty-post-left cmty-no-phone">
<div data-hj-suppress="" data-hj-masked="" class="cmty-post-username   "><p data-cmty="" title="`+name+`">`+name+`</p></div>


</div><div class="cmty-post-middle aopscoin-post-middle">

<div class="cmty-post-top-inline cmty-post-top-data">

<div class="cmty-post-top">
<a title="Amount" class="cmty-post-number">`+amount+`</a>
<a title="Amount" class="cmty-post-number aops-font">y</a>

<span class="cmty-post-date">`+time+`</span>


</div>
</div>
<div class="cmty-post-body"><div class="cmty-post-html"><div></div>${unescape(notes)}</div>


</div>
</div>
</div>
</div>`)
            $(".aopscoin-post-middle").css("border-right","none")
        })
    }
    function constructFeed () {
        AoPS.Feed.constructFeed()
        AoPS.Feed.feed_view.aopscoin_subfeed = AoPS.Feed.feed_view.addSubfeed({
            header_text: "AoPSCoin", // The header for inside the feed
            id: "feed-aopscoin-tab", // HTML ID
            title: "AoPSCoin", // Title for hovering over the button
            icon_letter: "y", // I'm using the impossible cube logo for now
            category: new AoPS.Community.Models.CategoryWithTopics({ // Create the category so the feed can open when we click the cube icon.
                master: AoPS.Feed.feed_view.community_master, // We're using the CategoryFeedTopics, because it won't keep loading new posts like CategoryGlobal
            }),
            master: AoPS.Feed.feed_view.community_master // The master was created on the constructFeed()
        });
        if ($("[id=feed-wrapper]").length == 2) {
            $("#feed-wrapper").remove()
        }
    }
    // RUN SECTION //
    function get_token () {
        return getCookie("AoPSCoin") //Get their token that's saved
    }
    if (document.getElementById('admin-panel')==null){
        $($('.menubar-label.resources .dropdown-category')[0]).prepend('<a href="https://artofproblemsolving.com/aopscoin" id="admin-panel">AoPSCoin Advanced</a>');
    }

    if (window.location.href=='https://artofproblemsolving.com/aopscoin'){
        $('#main-column-standard')[0].innerHTML=(`<div class="modal fade" id="tokenModal" tabindex="-1" role="dialog" aria-labelledby="tokenModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="tokenModalLabel">AoPSCoin Advanced</h5>
            </div>
            <div class="modal-body">
<label style="align:left">Enter token below. Alternatively, log out.</label>
                <form id="token-update-form">
                    <div class="form-group">
                        <input type="text" class="form-control" id="login-token" aria-describedby="emailHelp" placeholder="Current token: ${get_token()}" required="true">
                    </div>
                    <button type="submit" id="token-update-button" class="btn btn-primary">Update Token</button>
<button type="button" class="btn btn-primary" id="logout-button">Logout</button>
                </form>
            </div>
        </div>
    </div>
</div>`)
        function set_new_token(token) {
            document.cookie = "AoPSCoin=" + token + "; expires=1 Jan 3000 12:00:00 UTC;" // Add the token as a cookie
            window.location = "https://artofproblemsolving.com/"
        }
        $("#token-update-form").submit(function (e) {
            e.preventDefault()
            let inputs = $("#token-update-form :input").toArray()
            let token = inputs[0].value
            set_new_token(token)
        })
        $("#logout-button").click(function () {
            set_new_token("")
        })
    }
    if (get_token()) { //If the user is authenticated
        constructFeed()
        // Feed update refresh (400 milliseconds)
        setInterval(function () {
            setFeedHeader()
            setFeedTopics()
        },1000)
    }
    else { // If the user is not authenticated
        if (AoPS.session.logged_in) { // If they are logged in, we have to log them out
            $("#feed-tabs").append('<div id="feed-aopscoin-tab" class="feed-tab aops-font" title="AoPSCoin">y</div>') // Add in the tab
            $("#feed-aopscoin-tab").click(function () { // When the tab is opened
                // Set up the alert
                alert("You need to authenticate your AoPSCoin. You will be logged out and then you must log in again.")
                $(".aops-modal-buttons.aops-modal-footer").children(".aops-modal-btn")[0].innerText = "Authenticate"
                $(".aops-modal-buttons.aops-modal-footer").children(".aops-modal-btn").on("click",AoPS.login.logout) // Logout on click
            });
        }
        else { // If the user is logged out
            $("#login-button").off("click") // Get rid of the existing login function for the login button
            $("#login-button").mousedown(function (e) { // When the login button is clicked
                e.preventDefault(); // IDK if this is necessary

                // Get all the data from the form
                let username = $("#login-username")[0].value
                let password = $("#login-password")[0].value
                // Set up the settings for the request
                var settings = {
                    "url": "https://quantlaw.com/login",
                    "method": "POST",
                    "timeout": 0,
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "data": JSON.stringify({"username":username,"password":password}),
                };

                $.ajax(settings).done(function (response) { // When the request is done
                    document.cookie = "AoPSCoin=" + response.token + "; expires=1 Jan 3000 12:00:00 UTC;" // Add the token as a cookie

                    AoPS.login.login() // Login
                });
            })
        }
    }
},4000); // Run 4 seconds after initial load, I haven't found a way to automate this
